"""
Fetch / refresh the external public datasets that feed country_indicators.csv.

Each function is independent and writes to data/raw/. A merge step consolidates
everything into data/processed/country_indicators.csv. Some sources require a
free account token; set them in environment variables.

Required env vars (set what you have; missing ones skip that source):
  IUCN_TOKEN       - https://apiv3.iucnredlist.org/api/v3/token
  (All other sources are fully open.)

Usage:
  python scripts/02_fetch_external_data.py --source all
  python scripts/02_fetch_external_data.py --source worldbank
  python scripts/02_fetch_external_data.py --source iucn
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd
import requests

RAW = Path(__file__).parent.parent / "data" / "raw"
PROC = Path(__file__).parent.parent / "data" / "processed"
RAW.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------
# World Bank Open Data (no auth)
# ---------------------------------------------------------------
def fetch_worldbank():
    """CO2 per capita + Regulatory Quality + Gov Effectiveness."""
    indicators = {
        "EN.ATM.CO2E.PC": "wb_co2_t_per_capita",
        "RQ.EST":         "wb_wgi_regulatory_quality",
        "GE.EST":         "wb_wgi_gov_effectiveness",
    }
    out_frames = []
    for code, col in indicators.items():
        url = f"http://api.worldbank.org/v2/country/all/indicator/{code}?format=json&per_page=20000&date=2020:2024"
        print(f"Fetching {code}...")
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        data = r.json()[1]
        df = pd.DataFrame(data)
        df = df[df["value"].notna()]
        df = df.sort_values(["countryiso3code", "date"]).drop_duplicates("countryiso3code", keep="last")
        df = df[["countryiso3code", "value"]].rename(columns={"countryiso3code": "iso3", "value": col})
        out_frames.append(df)
    merged = out_frames[0]
    for f in out_frames[1:]:
        merged = merged.merge(f, on="iso3", how="outer")
    merged.to_csv(RAW / "worldbank.csv", index=False)
    print(f"  -> wrote {len(merged)} rows to data/raw/worldbank.csv")


# ---------------------------------------------------------------
# Yale EPI 2024
# ---------------------------------------------------------------
def fetch_epi():
    """
    EPI 2024 country scores.
    Download the 'epi2024results.csv' from https://epi.yale.edu/downloads and
    place in data/raw/. This function just validates its presence.
    """
    path = RAW / "epi2024results.csv"
    if not path.exists():
        print(f"[MANUAL] Download epi2024results.csv from https://epi.yale.edu/downloads "
              f"and place it at {path}")
        return
    df = pd.read_csv(path)
    print(f"EPI: {len(df)} rows, columns: {list(df.columns)[:10]}")


# ---------------------------------------------------------------
# IUCN Red List (requires free token)
# ---------------------------------------------------------------
def fetch_iucn():
    token = os.environ.get("IUCN_TOKEN")
    if not token:
        print("[SKIP] Set IUCN_TOKEN env var (request at https://apiv3.iucnredlist.org/api/v3/token)")
        return
    countries = pd.read_csv(PROC / "country_indicators.csv")["iso3"].tolist()
    rows = []
    for iso in countries:
        url = f"https://apiv3.iucnredlist.org/api/v3/country/getspecies/{iso}?token={token}"
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            print(f"  {iso}: HTTP {r.status_code}")
            continue
        data = r.json().get("result", [])
        threatened = sum(1 for s in data if s.get("category") in ("CR", "EN", "VU"))
        rows.append({"iso3": iso, "iucn_threatened_species": threatened})
        print(f"  {iso}: {threatened} threatened")
    pd.DataFrame(rows).to_csv(RAW / "iucn.csv", index=False)


# ---------------------------------------------------------------
# Global Tailings Portal (GRID-Arendal)
# ---------------------------------------------------------------
def fetch_tailings():
    """
    Global Tailings Portal — download the CSV from https://tailing.grida.no/data
    (login required, free). Place in data/raw/tailings_portal.csv.
    """
    path = RAW / "tailings_portal.csv"
    if not path.exists():
        print(f"[MANUAL] Download from https://tailing.grida.no/data (free account) to {path}")
        return
    df = pd.read_csv(path)
    agg = df.groupby("Country").agg(
        tsf_count=("Facility Name", "count"),
        tsf_max_very_high_or_extreme=("Consequence Classification",
                                       lambda s: int(any(str(v) in ("Very high", "Extreme") for v in s))),
    ).reset_index()
    agg.to_csv(RAW / "tailings_agg.csv", index=False)
    print(f"  -> {len(agg)} countries summarized")


# ---------------------------------------------------------------
# WHO Ambient Air Quality (PM2.5)
# ---------------------------------------------------------------
def fetch_who_pm25():
    """
    WHO AAQ database (annual mean PM2.5 by country).
    Download from https://www.who.int/data/gho/data/themes/air-pollution/who-air-quality-database
    and place in data/raw/who_aaq.csv.
    """
    path = RAW / "who_aaq.csv"
    if not path.exists():
        print(f"[MANUAL] Download WHO AAQ DB to {path}")
        return
    print(f"WHO AAQ: {sum(1 for _ in open(path))} rows")


# ---------------------------------------------------------------
# Global Forest Watch (WRI) — deforestation
# ---------------------------------------------------------------
def fetch_gfw():
    """
    GFW API requires an API key. Simpler: download country summaries from
    https://www.globalforestwatch.org/dashboards/global/ and place CSV at
    data/raw/gfw_country.csv.
    """
    path = RAW / "gfw_country.csv"
    if not path.exists():
        print(f"[MANUAL] Download GFW country summary to {path}")
        return
    print(f"GFW: {sum(1 for _ in open(path))} rows")


# ---------------------------------------------------------------
# WRI Aqueduct 4.0 API (UCW, CEP, bwd, etc.)
# ---------------------------------------------------------------
def fetch_aqueduct_api():
    """
    Fetch pollution indicators (UCW, CEP, bwd) at country level from Aqueduct 4.0 API.
    Endpoint: https://www.wri.org/applications/aqueduct/water-risk-atlas/#/api
    Note: this endpoint changes; check current docs.
    """
    print("[TODO] Aqueduct API endpoints rotate; consult WRI docs. Base file already includes bws, drr, rfr.")


# ---------------------------------------------------------------
# INFORM Risk Index (EC JRC)
# ---------------------------------------------------------------
def fetch_inform():
    """Open CSV from https://drmkc.jrc.ec.europa.eu/inform-index (public)."""
    url = "https://drmkc.jrc.ec.europa.eu/inform-index/Portals/0/InfoRM/2024/INFORM_Risk_2024_v065.xlsx"
    path = RAW / "inform_risk_2024.xlsx"
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        path.write_bytes(r.content)
        print(f"  -> wrote INFORM to {path}")
    except Exception as e:
        print(f"  skipped: {e}")


# ---------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------
SOURCES = {
    "worldbank": fetch_worldbank,
    "epi": fetch_epi,
    "iucn": fetch_iucn,
    "tailings": fetch_tailings,
    "who": fetch_who_pm25,
    "gfw": fetch_gfw,
    "aqueduct_api": fetch_aqueduct_api,
    "inform": fetch_inform,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="all", choices=["all"] + list(SOURCES))
    args = parser.parse_args()
    if args.source == "all":
        for name, fn in SOURCES.items():
            print(f"\n=== {name} ===")
            try:
                fn()
            except Exception as e:
                print(f"  ERROR: {e}")
    else:
        SOURCES[args.source]()


if __name__ == "__main__":
    main()
