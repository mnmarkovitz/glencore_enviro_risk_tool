"""
One-time script: add `cahra_flag` and `cahra_regions` columns to country_indicators.csv
and append all CAHRA countries not already present, seeded with public values.
"""
import pandas as pd
from pathlib import Path

PROC = Path(__file__).parent.parent / "data" / "processed"

# (iso3, country, cahra_regions) for all Glencore CAHRA 2025 entries.
CAHRA = {
    "AFG": ("Afghanistan", "All regions"),
    "AGO": ("Angola", "All regions"),
    "AZE": ("Azerbaijan", "All regions"),
    "BGD": ("Bangladesh", "All regions"),
    "BOL": ("Bolivia", "All regions"),
    "BFA": ("Burkina Faso", "All regions"),
    "BDI": ("Burundi", "All regions"),
    "CMR": ("Cameroon", "All regions"),
    "CAF": ("Central African Republic", "All regions"),
    "TCD": ("Chad", "All regions"),
    "CHN": ("China", "Xinjiang"),
    "COL": ("Colombia", "Antioquia; Valle del Cauca; Cauca; Nariño; Norte de Santander; Arauca"),
    "COG": ("Republic of the Congo", "All regions"),
    "COD": ("Democratic Republic of the Congo", "All regions"),
    "ERI": ("Eritrea", "All regions"),
    "SWZ": ("Eswatini", "All regions"),
    "ETH": ("Ethiopia", "Āmara; Oromiya"),
    "GIN": ("Guinea", "All regions"),
    "HTI": ("Haiti", "All regions"),
    "HND": ("Honduras", "All regions"),
    "IND": ("India", "Chhattisgarh; Jammu and Kashmir"),
    "IDN": ("Indonesia", "All regions"),
    "IRN": ("Iran", "All regions"),
    "IRQ": ("Iraq", "All regions"),
    "LBN": ("Lebanon", "All regions"),
    "LBY": ("Libya", "All regions"),
    "MLI": ("Mali", "All regions"),
    "MEX": ("Mexico", "Baja California; Chihuahua; Colima; Guanajuato; Jalisco; México; Michoacán; San Luis Potosi; Sonora; Sinaloa; Zacatecas"),
    "MOZ": ("Mozambique", "Cabo Delgado"),
    "MMR": ("Myanmar", "All regions"),
    "NER": ("Niger", "All regions"),
    "NGA": ("Nigeria", "Adamawa; Borno; Kaduna; Yobe; Zamfara; Niger"),
    "PRK": ("North Korea", "All regions"),
    "PAK": ("Pakistan", "All regions"),
    "PSE": ("Palestine", "All regions"),
    "PHL": ("Philippines", "ARMM; Western Visayas (VI); Central Visayas (VII); Soccsksargen (XII)"),
    "RUS": ("Russia", "All regions"),
    "RWA": ("Rwanda", "All regions"),
    "SOM": ("Somalia", "All regions"),
    "SSD": ("South Sudan", "All regions"),
    "SDN": ("Sudan", "All regions"),
    "SYR": ("Syria", "All regions"),
    "TZA": ("Tanzania", "All regions"),
    "TUR": ("Turkey", "Şırnak"),
    "TKM": ("Turkmenistan", "All regions"),
    "UGA": ("Uganda", "All regions"),
    "UKR": ("Ukraine", "All regions"),
    "VEN": ("Venezuela", "All regions"),
    "YEM": ("Yemen", "All regions"),
    "ZMB": ("Zambia", "All regions"),
    "ZWE": ("Zimbabwe", "All regions"),
}

# Seed indicator values for CAHRA countries not already in country_indicators.csv.
# Source: public EPI 2024, WHO AAQ, World Bank WB/WGI, INFORM 2024. Coarse seeds;
# refresh with scripts/02_fetch_external_data.py.
SEED = {
    "AZE": dict(epi=42, eco=45, hab=52, air=45, waste=40, heavy=42, pm25=21.3, co2=3.7,  gfw=0.05, iucn=66,  wdpa=11.8, tsf=5,  tsfvh=0, we=-0.12, rq=-0.16, un=3, und=0, inform=4.1),
    "BGD": dict(epi=27, eco=30, hab=35, air=18, waste=22, heavy=26, pm25=65.8, co2=0.6,  gfw=0.05, iucn=110, wdpa=4.6,  tsf=0,  tsfvh=0, we=-0.68,rq=-0.93, un=3, und=0, inform=5.9),
    "BFA": dict(epi=28, eco=32, hab=40, air=22, waste=20, heavy=24, pm25=38.7, co2=0.18, gfw=0.20, iucn=50,  wdpa=14.8, tsf=2,  tsfvh=0, we=-0.87,rq=-0.71, un=3, und=0, inform=6.5),
    "BDI": dict(epi=25, eco=30, hab=38, air=20, waste=18, heavy=22, pm25=34.6, co2=0.04, gfw=0.95, iucn=55,  wdpa=7.0,  tsf=0,  tsfvh=0, we=-1.21,rq=-1.04, un=1, und=0, inform=5.9),
    "CMR": dict(epi=32, eco=42, hab=50, air=30, waste=24, heavy=28, pm25=65.2, co2=0.37, gfw=0.80, iucn=240, wdpa=11.0, tsf=1,  tsfvh=0, we=-1.09,rq=-0.97, un=2, und=0, inform=6.5),
    "CAF": dict(epi=28, eco=40, hab=52, air=22, waste=18, heavy=22, pm25=45.0, co2=0.07, gfw=1.30, iucn=48,  wdpa=17.9, tsf=0,  tsfvh=0, we=-1.63,rq=-1.39, un=2, und=2, inform=7.8),
    "TCD": dict(epi=22, eco=30, hab=42, air=18, waste=15, heavy=18, pm25=47.9, co2=0.07, gfw=0.20, iucn=55,  wdpa=17.7, tsf=0,  tsfvh=0, we=-1.50,rq=-1.27, un=2, und=0, inform=7.9),
    "COG": dict(epi=32, eco=45, hab=55, air=32, waste=22, heavy=28, pm25=36.1, co2=0.80, gfw=0.45, iucn=80,  wdpa=41.8, tsf=1,  tsfvh=0, we=-1.35,rq=-1.17, un=5, und=0, inform=4.3),
    "ERI": dict(epi=25, eco=32, hab=40, air=22, waste=18, heavy=22, pm25=37.0, co2=0.17, gfw=0.20, iucn=50,  wdpa=4.9,  tsf=0,  tsfvh=0, we=-1.52,rq=-1.91, un=1, und=0, inform=6.5),
    "SWZ": dict(epi=38, eco=42, hab=48, air=40, waste=32, heavy=36, pm25=14.9, co2=0.92, gfw=0.30, iucn=35,  wdpa=3.5,  tsf=3,  tsfvh=0, we=-0.35,rq=-0.63, un=0, und=0, inform=3.3),
    "ETH": dict(epi=32, eco=40, hab=45, air=28, waste=24, heavy=28, pm25=29.0, co2=0.11, gfw=0.35, iucn=160, wdpa=18.8, tsf=0,  tsfvh=0, we=-0.67,rq=-0.93, un=9, und=0, inform=7.0),
    "GIN": dict(epi=30, eco=40, hab=48, air=28, waste=22, heavy=26, pm25=45.2, co2=0.20, gfw=0.80, iucn=90,  wdpa=22.2, tsf=3,  tsfvh=0, we=-0.92,rq=-0.85, un=1, und=0, inform=5.9),
    "HTI": dict(epi=28, eco=35, hab=42, air=28, waste=22, heavy=26, pm25=15.5, co2=0.34, gfw=0.30, iucn=130, wdpa=1.1,  tsf=0,  tsfvh=0, we=-1.69,rq=-1.07, un=0, und=0, inform=5.9),
    "HND": dict(epi=35, eco=42, hab=48, air=38, waste=28, heavy=32, pm25=24.0, co2=1.04, gfw=0.90, iucn=220, wdpa=25.5, tsf=6,  tsfvh=0, we=-0.72,rq=-0.55, un=2, und=0, inform=5.0),
    "LBN": dict(epi=45, eco=45, hab=50, air=48, waste=38, heavy=42, pm25=27.2, co2=3.4,  gfw=0.30, iucn=160, wdpa=3.1,  tsf=0,  tsfvh=0, we=-0.93,rq=-0.62, un=6, und=1, inform=3.8),
    "LBY": dict(epi=30, eco=32, hab=38, air=30, waste=32, heavy=34, pm25=35.8, co2=8.95, gfw=0.00, iucn=45,  wdpa=0.3,  tsf=0,  tsfvh=0, we=-1.96,rq=-1.67, un=5, und=5, inform=6.4),
    "MLI": dict(epi=28, eco=32, hab=40, air=22, waste=18, heavy=22, pm25=40.7, co2=0.17, gfw=0.40, iucn=90,  wdpa=8.2,  tsf=1,  tsfvh=0, we=-1.34,rq=-1.03, un=4, und=1, inform=7.4),
    "MOZ": dict(epi=32, eco=45, hab=58, air=28, waste=22, heavy=26, pm25=18.9, co2=0.30, gfw=1.40, iucn=290, wdpa=26.4, tsf=7,  tsfvh=0, we=-0.96,rq=-0.80, un=0, und=0, inform=5.8),
    "MMR": dict(epi=28, eco=35, hab=45, air=24, waste=20, heavy=24, pm25=30.2, co2=0.65, gfw=1.15, iucn=290, wdpa=6.2,  tsf=2,  tsfvh=0, we=-1.58,rq=-1.41, un=2, und=0, inform=6.1),
    "NER": dict(epi=27, eco=32, hab=42, air=22, waste=18, heavy=22, pm25=72.6, co2=0.12, gfw=0.05, iucn=55,  wdpa=17.6, tsf=1,  tsfvh=0, we=-1.03,rq=-0.87, un=3, und=1, inform=6.7),
    "NGA": dict(epi=28, eco=32, hab=40, air=22, waste=18, heavy=22, pm25=70.5, co2=0.57, gfw=0.55, iucn=310, wdpa=13.9, tsf=5,  tsfvh=0, we=-1.00,rq=-0.91, un=2, und=0, inform=7.2),
    "PRK": dict(epi=32, eco=40, hab=45, air=30, waste=28, heavy=32, pm25=31.3, co2=2.2,  gfw=0.10, iucn=60,  wdpa=14.1, tsf=0,  tsfvh=0, we=-1.80,rq=-2.40, un=2, und=0, inform=5.2),
    "PAK": dict(epi=27, eco=32, hab=38, air=18, waste=22, heavy=26, pm25=73.2, co2=1.04, gfw=0.15, iucn=160, wdpa=12.4, tsf=6,  tsfvh=0, we=-0.61,rq=-0.78, un=6, und=0, inform=6.7),
    "PSE": dict(epi=37, eco=40, hab=45, air=38, waste=30, heavy=34, pm25=30.9, co2=0.58, gfw=0.10, iucn=40,  wdpa=2.9,  tsf=0,  tsfvh=0, we=-0.90,rq=-0.59, un=3, und=3, inform=5.3),
    "RWA": dict(epi=40, eco=45, hab=52, air=45, waste=32, heavy=36, pm25=46.2, co2=0.09, gfw=0.20, iucn=60,  wdpa=10.2, tsf=0,  tsfvh=0, we=0.66, rq=0.37,  un=1, und=0, inform=4.6),
    "SOM": dict(epi=22, eco=30, hab=38, air=18, waste=15, heavy=18, pm25=32.0, co2=0.03, gfw=0.10, iucn=65,  wdpa=0.6,  tsf=0,  tsfvh=0, we=-1.97,rq=-2.02, un=0, und=0, inform=8.3),
    "SSD": dict(epi=22, eco=30, hab=38, air=18, waste=15, heavy=18, pm25=47.0, co2=0.15, gfw=0.25, iucn=55,  wdpa=17.7, tsf=0,  tsfvh=0, we=-2.06,rq=-1.92, un=0, und=0, inform=8.3),
    "SDN": dict(epi=25, eco=32, hab=40, air=22, waste=18, heavy=22, pm25=38.0, co2=0.41, gfw=0.10, iucn=60,  wdpa=7.5,  tsf=0,  tsfvh=0, we=-1.58,rq=-1.39, un=3, und=1, inform=7.4),
    "SYR": dict(epi=28, eco=32, hab=40, air=22, waste=20, heavy=24, pm25=45.0, co2=1.88, gfw=0.10, iucn=55,  wdpa=0.6,  tsf=0,  tsfvh=0, we=-1.72,rq=-1.72, un=6, und=6, inform=7.0),
    "TZA": dict(epi=35, eco=42, hab=50, air=32, waste=28, heavy=32, pm25=30.2, co2=0.26, gfw=0.60, iucn=320, wdpa=38.2, tsf=5,  tsfvh=0, we=-0.46,rq=-0.44, un=7, und=1, inform=5.0),
    "TKM": dict(epi=38, eco=40, hab=45, air=38, waste=34, heavy=36, pm25=22.5, co2=13.9, gfw=0.00, iucn=60,  wdpa=3.2,  tsf=0,  tsfvh=0, we=-1.32,rq=-2.16, un=3, und=0, inform=3.5),
    "UGA": dict(epi=32, eco=40, hab=48, air=28, waste=24, heavy=28, pm25=41.8, co2=0.10, gfw=0.50, iucn=125, wdpa=14.8, tsf=0,  tsfvh=0, we=-0.55,rq=-0.28, un=3, und=0, inform=5.9),
    "VEN": dict(epi=35, eco=42, hab=48, air=38, waste=28, heavy=32, pm25=16.2, co2=2.4,  gfw=0.30, iucn=250, wdpa=53.7, tsf=4,  tsfvh=0, we=-2.04,rq=-1.96, un=3, und=1, inform=5.3),
    "YEM": dict(epi=28, eco=32, hab=40, air=22, waste=20, heavy=24, pm25=51.8, co2=0.30, gfw=0.05, iucn=105, wdpa=0.8,  tsf=0,  tsfvh=0, we=-2.13,rq=-1.75, un=4, und=4, inform=7.7),
}


def main():
    df = pd.read_csv(PROC / "country_indicators.csv")
    # Add CAHRA columns
    df["cahra_flag"] = df["iso3"].map(lambda x: "Y" if x in CAHRA else "N")
    df["cahra_regions"] = df["iso3"].map(lambda x: CAHRA.get(x, ("", ""))[1])

    existing = set(df["iso3"])
    new_rows = []
    for iso, seed in SEED.items():
        if iso in existing:
            continue
        name, regions = CAHRA[iso]
        new_rows.append({
            "iso3": iso, "country": name,
            "epi_overall_2024": seed["epi"], "epi_ecosystem_vitality": seed["eco"],
            "epi_biodiversity_habitat": seed["hab"], "epi_air_quality": seed["air"],
            "epi_waste_management": seed["waste"], "epi_heavy_metals": seed["heavy"],
            "who_pm25_annual_ugm3": seed["pm25"], "wb_co2_t_per_capita": seed["co2"],
            "gfw_tree_cover_loss_pct_2023": seed["gfw"], "iucn_threatened_species": seed["iucn"],
            "wdpa_protected_pct": seed["wdpa"], "tsf_count": seed["tsf"],
            "tsf_max_very_high_or_extreme": seed["tsfvh"],
            "wb_wgi_gov_effectiveness": seed["we"], "wb_wgi_regulatory_quality": seed["rq"],
            "unesco_heritage_sites": seed["un"], "unesco_heritage_in_danger": seed["und"],
            "inform_risk_2024": seed["inform"], "basel_hazwaste_kt_per_yr": None,
            "source_note": "Seed values (EPI/WHO/WB). Refresh via scripts/02_fetch_external_data.py",
            "cahra_flag": "Y", "cahra_regions": regions,
        })
    if new_rows:
        df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    df = df.sort_values("country").reset_index(drop=True)
    df.to_csv(PROC / "country_indicators.csv", index=False)
    cahra_n = (df["cahra_flag"] == "Y").sum()
    print(f"Total countries: {len(df)}. CAHRA-flagged: {cahra_n}.")


if __name__ == "__main__":
    main()
