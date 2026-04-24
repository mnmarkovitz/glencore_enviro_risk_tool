"""
Export a simplified companion Excel workbook — "Quick Reference" for
Responsible Sourcing analysts who want the scored output without running
the full Streamlit tool.

Output: Quick_Reference.xlsx (in project root)

Sheets:
  1. README               - what this is, how to read it, when refreshed
  2. Country × Risk       - color-coded matrix (countries x 8 priority risks)
  3. Full Ranked Results  - every scored row with filter + color-coded bucket
  4. Data Sources         - every dataset cited, with URL

Run whenever the scoring inputs change:
    python scripts/08_export_quick_reference.py
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "app"))
from scoring import compute, _load  # noqa: E402

OUTPUT = ROOT / "Quick_Reference.xlsx"

# Bucket colors — match the Streamlit app exactly
BUCKET_FILLS = {
    "Low":      PatternFill("solid", start_color="FF4CAF50", end_color="FF4CAF50"),
    "Moderate": PatternFill("solid", start_color="FFFFC107", end_color="FFFFC107"),
    "High":     PatternFill("solid", start_color="FFFF9800", end_color="FFFF9800"),
    "Critical": PatternFill("solid", start_color="FFE53935", end_color="FFE53935"),
    "No data":  PatternFill("solid", start_color="FFBDBDBD", end_color="FFBDBDBD"),
}
HEADER_FILL = PatternFill("solid", start_color="FF00A9A5", end_color="FF00A9A5")  # Glencore teal
HEADER_FONT = Font(bold=True, color="FFFFFFFF")
BUCKET_FONT_LIGHT = Font(color="FFFFFFFF", bold=True)
BUCKET_FONT_DARK = Font(color="FF000000", bold=True)
THIN_BORDER = Border(*(Side(border_style="thin", color="FFCCCCCC"),) * 4)


def _bucket_of(overall):
    if pd.isna(overall): return "No data"
    if overall <= 4: return "Low"
    if overall <= 9: return "Moderate"
    if overall <= 14: return "High"
    return "Critical"


def _style_header(row):
    for cell in row:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = THIN_BORDER


def _autosize(ws, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


# -------------------------- sheet builders --------------------------

def sheet_readme(wb, risks, countries, producers, today):
    ws = wb.active
    ws.title = "README"
    ws["A1"] = "Environmental Risk — Quick Reference"
    ws["A1"].font = Font(bold=True, size=18, color="FF00A9A5")
    ws["A2"] = f"Generated: {today}   |   For: Glencore Group Responsible Sourcing team"
    ws["A2"].font = Font(italic=True, color="FF555555")

    ws["A4"] = "What this workbook is"
    ws["A4"].font = Font(bold=True, size=13)
    ws["A5"] = (
        "A precomputed snapshot of environmental risk scores for every commodity × country × "
        "mining process combination in the Glencore Responsible Sourcing team's tool. Use this "
        "Excel file for quick lookups when you don't need the full interactive Streamlit tool."
    )
    ws["A5"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[5].height = 60

    ws["A7"] = "How to read the scores"
    ws["A7"].font = Font(bold=True, size=13)
    ws["A8"] = "Overall = Likelihood × Severity, range 1–25. Cells are color-coded by bucket:"
    ws["A10"] = "Low";      ws["A10"].fill = BUCKET_FILLS["Low"];      ws["A10"].font = BUCKET_FONT_LIGHT
    ws["B10"] = "Overall 1–4"
    ws["A11"] = "Moderate"; ws["A11"].fill = BUCKET_FILLS["Moderate"]; ws["A11"].font = BUCKET_FONT_DARK
    ws["B11"] = "Overall 5–9"
    ws["A12"] = "High";     ws["A12"].fill = BUCKET_FILLS["High"];     ws["A12"].font = BUCKET_FONT_DARK
    ws["B12"] = "Overall 10–14"
    ws["A13"] = "Critical"; ws["A13"].fill = BUCKET_FILLS["Critical"]; ws["A13"].font = BUCKET_FONT_LIGHT
    ws["B13"] = "Overall 15–25"

    ws["A15"] = "Sheets"
    ws["A15"].font = Font(bold=True, size=13)
    ws["A16"] = "README"
    ws["B16"] = "This page."
    ws["A17"] = "Country × Risk"
    ws["B17"] = "Heatmap: max Overall risk score per country × each priority risk. Best for scanning exposure."
    ws["A18"] = "Full Ranked Results"
    ws["B18"] = "Every scored combination with sources. Use Excel's filter to slice."
    ws["A19"] = "Data Sources"
    ws["B19"] = "Hyperlinked list of every public dataset the scores come from."

    ws["A21"] = "Methodology (brief)"
    ws["A21"].font = Font(bold=True, size=13)
    ws["A22"] = "Likelihood = 0.4 × Process Intrinsic Risk + 0.6 × Country Hazard Score (both 1–5)"
    ws["A23"] = "Severity   = 0.5 × Ecological Sensitivity + 0.5 × Regulatory Strictness (both 1–5)"
    ws["A24"] = "Overall    = Likelihood × Severity"
    ws["A25"] = (
        "Full methodology, formulas, and normalization rules are in the Streamlit tool's "
        "Methodology tab and in docs/METHODOLOGY.md."
    )
    ws["A25"].alignment = Alignment(wrap_text=True)
    ws.row_dimensions[25].height = 40

    ws["A27"] = "Important caveats"
    ws["A27"].font = Font(bold=True, size=13)
    ws["A28"] = (
        "This workbook is a STATIC snapshot. It does not update automatically — re-run "
        "scripts/08_export_quick_reference.py whenever the CSVs change. The interactive Streamlit "
        "tool is the Source of Truth. For map visualization, supplier overlays, and drill-down, use "
        "the Streamlit tool — not this file.\n\n"
        "Cells showing '—' mean the underlying public dataset has NO value for that country and risk. "
        "Examples: Noise pollution has no global country-level dataset (hence all '—' in the Hazard "
        "columns for that risk), and UNESCO heritage-in-danger counts are zero for many countries. "
        "In those cases, Likelihood falls back to the Process Intrinsic Risk alone."
    )
    ws["A28"].alignment = Alignment(wrap_text=True)
    ws.row_dimensions[28].height = 140

    ws["A30"] = "Built for Glencore Responsible Sourcing by NYU SPS Global Affairs MS students:"
    ws["A30"].font = Font(italic=True)
    ws["A31"] = (
        "Marielle Markovitz, Maahi Gupta, Daniela Cano, Daniel Luis de Jesus, "
        "Lindsay Huba-Zhang, Zorana Ivanovich, Mohamad Rimawi"
    )
    ws["A31"].font = Font(italic=True, color="FF555555")

    _autosize(ws, [18, 80])


def sheet_country_risk(wb, df, risks):
    ws = wb.create_sheet("Country × Risk")
    priority_ids = risks[risks["category"] == "Priority"]["risk_id"].tolist()
    priority_labels = dict(zip(risks["risk_id"], risks["risk_type"]))

    # Build max Overall per country × risk (all commodities, all processes, applies==Y)
    df_y = df[df["applies"] == "Y"].copy()
    pivot = (
        df_y[df_y["risk_id"].isin(priority_ids)]
        .groupby(["country", "iso3", "cahra_flag", "risk_id"])["overall_1_25"]
        .max().unstack("risk_id")
    )
    # Reorder columns to match priority order
    pivot = pivot.reindex(columns=[rid for rid in priority_ids if rid in pivot.columns])
    # Sort countries by their worst Overall score descending
    pivot["_max"] = pivot.max(axis=1)
    pivot = pivot.sort_values("_max", ascending=False).drop(columns=["_max"])
    pivot = pivot.reset_index()

    # Header row
    headers = ["Country", "ISO", "CAHRA"] + [priority_labels[rid] for rid in pivot.columns[3:]]
    ws.append(headers)
    _style_header(ws[1])

    # Data rows
    for _, r in pivot.iterrows():
        row_data = [r["country"], r["iso3"], r["cahra_flag"]]
        row_data += [float(r[rid]) if pd.notna(r[rid]) else None for rid in pivot.columns[3:]]
        ws.append(row_data)
        row_idx = ws.max_row
        # CAHRA cell styling
        if r["cahra_flag"] == "Y":
            ws.cell(row=row_idx, column=3).fill = PatternFill("solid", start_color="FFFFD54F", end_color="FFFFD54F")
            ws.cell(row=row_idx, column=3).font = Font(bold=True)
        # Color each score cell
        for i in range(4, len(headers) + 1):
            val = ws.cell(row=row_idx, column=i).value
            if val is None: continue
            bucket = _bucket_of(val)
            ws.cell(row=row_idx, column=i).fill = BUCKET_FILLS[bucket]
            ws.cell(row=row_idx, column=i).font = BUCKET_FONT_LIGHT if bucket in ("Low", "Critical") else BUCKET_FONT_DARK
            ws.cell(row=row_idx, column=i).alignment = Alignment(horizontal="center")
            ws.cell(row=row_idx, column=i).number_format = "0.0"

    ws.freeze_panes = "D2"
    ws.auto_filter.ref = ws.dimensions
    _autosize(ws, [32, 6, 8] + [16] * (len(headers) - 3))


def sheet_full_table(wb, df):
    ws = wb.create_sheet("Full Ranked Results")
    df_y = df[df["applies"] == "Y"].copy()
    cols = [
        "risk_type", "commodity", "country", "cahra_flag", "process",
        "country_hazard_raw", "country_hazard_norm_1_5",
        "likelihood_1_5", "severity_1_5", "overall_1_25", "risk_bucket",
        "process_intrinsic_1_5",
        "ecological_sensitivity_1_5", "regulatory_strictness_1_5",
        "likely_supplier_types", "country_hazard_source",
    ]
    df_y = df_y[cols].sort_values("overall_1_25", ascending=False)
    df_y.columns = [
        "Risk", "Commodity", "Country", "CAHRA", "Process",
        "Hazard Raw (source units)", "Hazard Normalized (1-5)",
        "Likelihood (1-5)", "Severity (1-5)", "Overall (1-25)", "Bucket",
        "Process Intrinsic (1-5)",
        "Eco Sensitivity (1-5)", "Regulatory Strict. (1-5)",
        "Likely Supplier Types", "Country Hazard Source",
    ]

    # Header
    ws.append(df_y.columns.tolist())
    _style_header(ws[1])

    # Data
    for _, row in df_y.iterrows():
        cells = [("—" if pd.isna(v) else v) for v in row.tolist()]
        ws.append(cells)
        r = ws.max_row
        if row["CAHRA"] == "Y":
            ws.cell(row=r, column=4).fill = PatternFill("solid", start_color="FFFFD54F", end_color="FFFFD54F")
            ws.cell(row=r, column=4).font = Font(bold=True)
        bucket = row["Bucket"]
        ws.cell(row=r, column=11).fill = BUCKET_FILLS.get(bucket, PatternFill())
        ws.cell(row=r, column=11).font = BUCKET_FONT_LIGHT if bucket in ("Low", "Critical") else BUCKET_FONT_DARK
        # Number formats for numeric columns (skip cells that are the "—" placeholder)
        for c in [6, 7, 8, 9, 10, 12, 13, 14]:
            if isinstance(ws.cell(row=r, column=c).value, (int, float)):
                ws.cell(row=r, column=c).number_format = "0.00"

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    _autosize(ws, [40, 18, 32, 8, 14, 18, 18, 14, 14, 14, 10, 18, 16, 20, 50, 50])


def sheet_sources(wb, risks):
    ws = wb.create_sheet("Data Sources")
    ws.append(["Risk", "Likelihood dataset", "Indicator", "URL",
                "Severity dataset", "Indicator", "URL"])
    _style_header(ws[1])
    for _, r in risks.iterrows():
        ws.append([r["risk_type"],
                    r["likelihood_dataset"], r["likelihood_indicator"], r["likelihood_url"],
                    r["severity_dataset"], r["severity_indicator"], r["severity_url"]])
        # Make URLs clickable
        row = ws.max_row
        for col in [4, 7]:
            cell = ws.cell(row=row, column=col)
            if cell.value:
                cell.hyperlink = cell.value
                cell.font = Font(color="FF0366D6", underline="single")
    ws.freeze_panes = "A2"
    _autosize(ws, [40, 28, 44, 60, 28, 44, 60])


def main():
    risks, matrix, countries, producers, _noise, _w, _st = _load()
    today = date.today().isoformat()
    print(f"Computing scores for export... (today: {today})")
    df = compute()  # all commodities, countries, processes, risks
    print(f"  {len(df):,} rows scored.")

    wb = Workbook()
    sheet_readme(wb, risks, countries, producers, today)
    sheet_country_risk(wb, df, risks)
    sheet_full_table(wb, df)
    sheet_sources(wb, risks)
    wb.save(OUTPUT)
    print(f"✓ Wrote {OUTPUT.name}  ({OUTPUT.stat().st_size / 1024:.0f} KB)")
    print(f"  Location: {OUTPUT}")


if __name__ == "__main__":
    main()
