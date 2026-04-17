"""
Process the WRI Aqueduct 4.0 country rankings Excel file into a clean wide-format CSV.

Input:  Aqueduct40_rankings_download_Y2023M07D05.xlsx
Output: data/processed/aqueduct_country_scores.csv

This file only contains bws (water stress), drr (drought risk), rfr (flood risk).
For pollution indicators (UCW, CEP), see scripts/02_fetch_aqueduct_api.py (TODO).
"""
import pandas as pd
from pathlib import Path

SRC = Path("/Users/mariellemarkovitz/Downloads/Aqueduct40_rankings_download_Y2023M07D05/Aqueduct40_rankings_download_Y2023M07D05.xlsx")
OUT = Path(__file__).parent.parent / "data" / "processed" / "aqueduct_country_scores.csv"

INDICATORS = {
    "bws": "Baseline Water Stress",
    "drr": "Drought Risk",
    "rfr": "Riverine Flood Risk",
}

def main():
    df = pd.read_excel(SRC, sheet_name="country_baseline")
    df = df[df["indicator_name"].isin(INDICATORS.keys())]
    # Prefer Tot, else One, else Pop (for rfr)
    pref = (
        df.assign(_rank=df["weight"].map({"Tot": 1, "One": 2, "Pop": 3}).fillna(99))
          .sort_values("_rank")
          .drop_duplicates(subset=["gid_0", "indicator_name"], keep="first")
    )
    wide = pref.pivot_table(
        index=["gid_0", "name_0", "un_region", "wb_region"],
        columns="indicator_name",
        values="cat",
        aggfunc="first",
    ).reset_index()
    wide.columns.name = None
    wide = wide.rename(columns={k: f"{k}_cat_0_4" for k in INDICATORS})
    wide.to_csv(OUT, index=False)
    print(f"Wrote {len(wide)} countries -> {OUT}")
    print(wide.head().to_string())

if __name__ == "__main__":
    main()
