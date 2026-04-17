"""
Refresh soilgrids_country.csv from the ISRIC SoilGrids 2.0 REST API.

Source: https://soilgrids.org/ — ISRIC World Soil Information.
API docs: https://www.isric.org/explore/soilgrids/faq-soilgrids
Endpoint: https://rest.isric.org/soilgrids/v2.0/properties/query
License: CC BY 4.0.

For each country in country_centroids.csv, queries topsoil (0-5 cm) for:
  - phh2o (pH in H2O, scaled x10)
  - soc (soil organic carbon, dg/kg, divide by 10 for g/kg)
  - cec (cation exchange capacity, mmol(c)/kg, divide by 10 for cmol(+)/kg)

Derives soil_vulnerability_1_5 using the same formula documented in
METHODOLOGY.md. Overwrites soilgrids_country.csv.

Run: python scripts/07_fetch_soilgrids.py
"""
from pathlib import Path
import time

import pandas as pd
import requests

PROC = Path(__file__).parent.parent / "data" / "processed"
API = "https://rest.isric.org/soilgrids/v2.0/properties/query"
PROPS = ["phh2o", "soc", "cec"]


def vuln_ph(ph):
    return max(1.0, min(5.0, abs(ph - 7) * 1.3 + 1))

def vuln_soc(soc):
    for threshold, score in [(50, 1.0), (30, 2.0), (20, 3.0), (10, 4.0)]:
        if soc >= threshold: return score
    return 5.0

def vuln_cec(cec):
    for threshold, score in [(35, 1.0), (25, 2.0), (15, 3.0), (10, 4.0)]:
        if cec >= threshold: return score
    return 5.0


def query(lat, lon):
    params = [("lon", lon), ("lat", lat), ("depth", "0-5cm"), ("value", "mean")]
    params += [("property", p) for p in PROPS]
    r = requests.get(API, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()["properties"]["layers"]
    out = {}
    for layer in data:
        name = layer["name"]
        try:
            v = layer["depths"][0]["values"]["mean"]
        except (KeyError, IndexError, TypeError):
            v = None
        out[name] = v
    # Unit conversions (per SoilGrids 2.0 mapping units)
    if out.get("phh2o") is not None: out["phh2o"] /= 10     # -> pH
    if out.get("soc") is not None:   out["soc"] /= 10       # -> g/kg
    if out.get("cec") is not None:   out["cec"] /= 10       # -> cmol/kg
    return out


def main():
    centroids = pd.read_csv(PROC / "country_centroids.csv")
    names = dict(zip(pd.read_csv(PROC / "country_indicators.csv")["iso3"],
                     pd.read_csv(PROC / "country_indicators.csv")["country"]))
    rows = []
    for _, r in centroids.iterrows():
        iso = r["iso3"]
        print(f"  {iso}...", end=" ", flush=True)
        try:
            vals = query(r["lat"], r["lon"])
        except Exception as e:
            print(f"error: {e}")
            continue
        ph = vals.get("phh2o"); soc = vals.get("soc"); cec = vals.get("cec")
        if ph is None or soc is None or cec is None:
            print("no data")
            continue
        v = round((vuln_ph(ph) + vuln_soc(soc) + vuln_cec(cec)) / 3, 2)
        rows.append(dict(
            iso3=iso, country=names.get(iso, iso),
            soil_ph_0_5cm=round(ph, 2),
            soil_soc_g_per_kg=round(soc, 1),
            soil_cec_cmol_per_kg=round(cec, 1),
            soil_vulnerability_1_5=v,
            source_note="ISRIC SoilGrids 2.0 (0-5cm mean) via REST API",
        ))
        print(f"pH={ph:.2f} SOC={soc:.1f} CEC={cec:.1f} → v={v}")
        time.sleep(0.5)  # polite rate-limit
    if rows:
        pd.DataFrame(rows).sort_values("country").to_csv(PROC / "soilgrids_country.csv", index=False)
        print(f"\nWrote {len(rows)} countries → {PROC/'soilgrids_country.csv'}")


if __name__ == "__main__":
    main()
