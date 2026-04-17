"""
Merge raw datasets (from scripts/02_fetch_external_data.py) into
data/processed/country_indicators.csv.

Safe to re-run; it preserves any rows/countries the user has edited manually
by merging on iso3 and updating only non-null fetched values.
"""
from pathlib import Path
import pandas as pd

RAW = Path(__file__).parent.parent / "data" / "raw"
PROC = Path(__file__).parent.parent / "data" / "processed"


def _safe_read(path: Path) -> pd.DataFrame | None:
    return pd.read_csv(path) if path.exists() else None


def main():
    base = pd.read_csv(PROC / "country_indicators.csv")

    updates = []
    wb = _safe_read(RAW / "worldbank.csv")
    if wb is not None:
        updates.append(wb)
    iucn = _safe_read(RAW / "iucn.csv")
    if iucn is not None:
        updates.append(iucn)
    tailings = _safe_read(RAW / "tailings_agg.csv")
    if tailings is not None:
        updates.append(tailings.rename(columns={"Country": "country"}))

    for upd in updates:
        key = "iso3" if "iso3" in upd.columns else "country"
        for col in upd.columns:
            if col == key:
                continue
            base = base.merge(upd[[key, col]], on=key, how="left", suffixes=("", "_new"))
            new_col = f"{col}_new"
            if new_col in base.columns:
                base[col] = base[new_col].combine_first(base[col])
                base = base.drop(columns=[new_col])

    base.to_csv(PROC / "country_indicators.csv", index=False)
    print(f"Merged -> {PROC/'country_indicators.csv'} ({len(base)} rows)")


if __name__ == "__main__":
    main()
