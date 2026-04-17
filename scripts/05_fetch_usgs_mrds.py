"""
Fetch USGS MRDS (Mineral Resources Data System) — global mineral-site database.

Source: https://mrdata.usgs.gov/mrds/
Full CSV download: https://mrdata.usgs.gov/mrds/mrds-csv.zip (~35 MB zipped, ~150 MB extracted)

Output: data/raw/mrds.csv (full dump), data/processed/mrds_sites.csv (trimmed,
filtered to commodities Glencore sources, with lat/lon and status).

Note: MRDS is a PUBLIC, global inventory of known mineral occurrences. It is NOT
Glencore-specific — the overlay on the tool's map layer is labeled "All known
mines in region (USGS MRDS)" so users don't confuse it with Glencore's portfolio.

USGS also maintains the Critical Minerals Atlas (https://apps.usgs.gov/critical-minerals/)
which focuses on the 2022 Critical Minerals List. The flag is already encoded
in commodity_producers.csv:critical_mineral.
"""
import io
import zipfile
from pathlib import Path

import pandas as pd
import requests

RAW = Path(__file__).parent.parent / "data" / "raw"
PROC = Path(__file__).parent.parent / "data" / "processed"
RAW.mkdir(parents=True, exist_ok=True)

URL = "https://mrdata.usgs.gov/mrds/mrds-csv.zip"

# Keywords in MRDS commod1/commod2/commod3 columns that map to our commodities
COMMOD_MAP = {
    "Aluminum":      ["ALUMINUM", "BAUXITE"],
    "Iron ore":      ["IRON"],
    "Zinc":          ["ZINC"],
    "Lead":          ["LEAD"],
    "Nickel":        ["NICKEL"],
    "Cobalt":        ["COBALT"],
    "Copper":        ["COPPER"],
    "Gold":          ["GOLD"],
    "Silver":        ["SILVER"],
    "Platinum":      ["PLATINUM", "PALLADIUM", "PGM"],
    "Ferrovanadium": ["VANADIUM"],
    "Manganese alloys": ["MANGANESE"],
    "Ferrochrome":   ["CHROMIUM", "CHROMITE"],
    "Coal":          ["COAL"],
}


def main():
    zip_path = RAW / "mrds.zip"
    if not zip_path.exists():
        print(f"Downloading {URL} (~35 MB) ...")
        r = requests.get(URL, timeout=120, stream=True)
        r.raise_for_status()
        zip_path.write_bytes(r.content)
    with zipfile.ZipFile(zip_path) as z:
        csv_name = next(n for n in z.namelist() if n.lower().endswith("mrds.csv"))
        with z.open(csv_name) as f:
            df = pd.read_csv(f, low_memory=False)
    print(f"MRDS rows: {len(df):,}")
    df = df.dropna(subset=["latitude", "longitude"])
    # Attach commodity label from commod1/commod2/commod3
    commod_cols = [c for c in ["commod1", "commod2", "commod3"] if c in df.columns]
    def _match(row):
        text = " ".join(str(row[c]).upper() for c in commod_cols if pd.notna(row[c]))
        for label, kws in COMMOD_MAP.items():
            if any(k in text for k in kws):
                return label
        return None
    df["commodity"] = df.apply(_match, axis=1)
    df = df.dropna(subset=["commodity"])

    keep = ["site_name", "commodity", "latitude", "longitude", "country", "state",
            "dev_stat", "prod_size"]
    keep = [c for c in keep if c in df.columns]
    out = df[keep].copy()
    out.to_csv(PROC / "mrds_sites.csv", index=False)
    print(f"Saved {len(out):,} commodity-matched sites → data/processed/mrds_sites.csv")


if __name__ == "__main__":
    main()
