"""
Fetch Global Energy Monitor (GEM) asset trackers — coal mines + oil/gas extraction.

Source: https://globalenergymonitor.org/
Specific trackers used:
  - Global Coal Mine Tracker:            https://globalenergymonitor.org/projects/global-coal-mine-tracker/
  - Global Oil & Gas Extraction Tracker: https://globalenergymonitor.org/projects/global-oil-gas-extraction-tracker/
  - Global Iron Ore Mine Tracker:        https://globalenergymonitor.org/projects/global-iron-ore-mines-tracker/
  - Global Steel Plant Tracker:          https://globalenergymonitor.org/projects/global-steel-plant-tracker/
                                         (iron ore → steel value-chain context)

Data is FREE but requires a one-time sign-up to receive download links. Save the
downloaded XLSX files at:
  data/raw/gem_coal_mines.xlsx
  data/raw/gem_oil_gas_extraction.xlsx
  data/raw/gem_iron_ore_mines.xlsx
  data/raw/gem_steel_plants.xlsx

This script then trims and normalizes them to data/processed/gem_sites.csv with
columns: source_tracker, asset_name, commodity, country, iso3, lat, lon,
status, owner_operators.

GEM methodology: https://globalenergymonitor.org/projects/
License: CC BY 4.0 (attribution required).
"""
from pathlib import Path

import pandas as pd

RAW = Path(__file__).parent.parent / "data" / "raw"
PROC = Path(__file__).parent.parent / "data" / "processed"


def _load(path: Path, tracker: str, commodity: str):
    if not path.exists():
        print(f"  [SKIP] {path.name} not found. Download from globalenergymonitor.org first.")
        return pd.DataFrame()
    df = pd.read_excel(path)
    # GEM column names vary by tracker release; be defensive
    rename_map = {
        "Mine Name": "asset_name", "Plant Name": "asset_name",
        "Unit Name": "asset_name", "Project Name": "asset_name",
        "Country/Area": "country", "Country": "country",
        "Latitude": "lat", "Longitude": "lon",
        "Status": "status", "Owner": "owner_operators",
        "Operator": "owner_operators", "Parent": "owner_operators",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    keep = [c for c in ["asset_name", "country", "lat", "lon", "status", "owner_operators"]
            if c in df.columns]
    out = df[keep].copy()
    out["source_tracker"] = tracker
    out["commodity"] = commodity
    return out


def main():
    frames = [
        _load(RAW / "gem_coal_mines.xlsx", "Global Coal Mine Tracker", "Coal"),
        _load(RAW / "gem_oil_gas_extraction.xlsx", "Global Oil & Gas Extraction Tracker", "Oil and gas"),
        _load(RAW / "gem_iron_ore_mines.xlsx", "Global Iron Ore Mine Tracker", "Iron ore"),
        _load(RAW / "gem_steel_plants.xlsx", "Global Steel Plant Tracker", "Iron ore"),
    ]
    if not any(len(f) for f in frames):
        print("No GEM files present. Register at https://globalenergymonitor.org/ to download.")
        return
    out = pd.concat([f for f in frames if len(f)], ignore_index=True)
    out = out.dropna(subset=["lat", "lon"])
    out.to_csv(PROC / "gem_sites.csv", index=False)
    print(f"Saved {len(out):,} GEM sites → data/processed/gem_sites.csv")


if __name__ == "__main__":
    main()
