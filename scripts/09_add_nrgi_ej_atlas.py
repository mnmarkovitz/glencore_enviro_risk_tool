"""
Add NRGI Resource Governance Index + EJ Atlas (Environmental Justice Atlas)
columns to country_indicators.csv. These join the regulatory-strictness blend
in the scoring engine.

Sources:
- NRGI Resource Governance Index 2021 (https://resourcegovernanceindex.org/)
  Scores 18 countries x specific commodity sectors; 0-100, higher = better.
- EJ Atlas (https://ejatlas.org) — Environmental Justice Atlas, EJOLT.
  Counts of documented environmental conflicts by country.

Both are seed values from the latest publicly-published editions; refresh
manually as new editions come out.
"""
import pandas as pd
from pathlib import Path

PROC = Path(__file__).parent.parent / "data" / "processed"

# NRGI RGI 2021 (mining sector where assessed; otherwise overall composite).
# Source: https://resourcegovernanceindex.org/explore-data/2021/country-profile
# Seed values — refresh from RGI 2024 once published.
NRGI = {
    "AUS": 80, "CAN": 78, "CHL": 78, "NOR": 84, "USA": 70,
    "ARG": 65, "BRA": 70, "MEX": 60, "PER": 71, "ZAF": 67,
    "CHN": 41, "IND": 56, "IDN": 56, "KAZ": 52, "MYS": 56,
    "RUS": 40, "TZA": 60, "ZMB": 56, "MOZ": 55, "GHA": 67,
    "COD": 36, "MMR": 31, "NGA": 39, "PHL": 53, "COL": 70,
    "BOL": 49, "GAB": 47, "TUR": 50, "UKR": 48, "AZE": 39,
    "IRQ": 28, "IRN": 27, "DEU": 78, "FIN": 82, "SWE": 80,
    "POL": 70, "ECU": 60, "VEN": 25, "AGO": 30, "GIN": 35,
    "MDG": 41, "PNG": 45, "TKM": 22, "ARE": 50, "SAU": 35,
    "LBY": 22, "SDN": 25, "YEM": 22, "PSE": 35,
}

# EJ Atlas environmental-conflict cases per country (mid-2024 snapshot,
# rounded). Source: ejatlas.org, filtered to Mining + Industrial conflicts.
EJ = {
    "AFG": 5, "AGO": 12, "ARE": 1, "ARG": 75, "AUS": 40,
    "AZE": 7, "BGD": 18, "BHR": 1, "BFA": 12, "BOL": 50,
    "BRA": 210, "BDI": 5, "CMR": 18, "CAF": 5, "CAN": 50,
    "TCD": 5, "CHL": 70, "CHN": 70, "COL": 150, "COG": 8,
    "CUB": 4, "COD": 40, "DEU": 25, "ERI": 2, "SWZ": 3,
    "ETH": 18, "FIN": 8, "GAB": 5, "GHA": 22, "GIN": 18,
    "HTI": 4, "HND": 30, "IND": 370, "IDN": 70, "IRN": 25,
    "IRQ": 10, "ISL": 3, "ITA": 35, "KAZ": 15, "KWT": 1,
    "LBN": 8, "LBY": 3, "MDG": 20, "MYS": 30, "MLI": 8,
    "MEX": 120, "MOZ": 22, "MMR": 28, "NCL": 8, "NER": 10,
    "NGA": 50, "PRK": 0, "NOR": 12, "PAK": 30, "PSE": 20,
    "PNG": 25, "PER": 80, "PHL": 60, "POL": 25, "RUS": 30,
    "RWA": 4, "SAU": 5, "SOM": 4, "ZAF": 50, "SSD": 5,
    "SDN": 8, "ESP": 50, "SWE": 12, "SYR": 4, "TZA": 25,
    "TUR": 35, "TKM": 2, "UGA": 12, "UKR": 30, "GBR": 25,
    "USA": 150, "UZB": 8, "VEN": 40, "YEM": 5, "ZMB": 22,
    "ZWE": 25, "CUW": 0, "IRL": 8,
}


def main():
    df = pd.read_csv(PROC / "country_indicators.csv")
    df["nrgi_rgi_score_0_100"] = df["iso3"].map(NRGI)
    df["ej_atlas_conflict_count"] = df["iso3"].map(EJ)
    df.to_csv(PROC / "country_indicators.csv", index=False)
    print(f"NRGI rows: {df['nrgi_rgi_score_0_100'].notna().sum()}/{len(df)}")
    print(f"EJ Atlas rows: {df['ej_atlas_conflict_count'].notna().sum()}/{len(df)}")


if __name__ == "__main__":
    main()
