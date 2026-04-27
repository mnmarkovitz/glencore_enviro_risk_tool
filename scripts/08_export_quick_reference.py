"""
Export a comprehensive companion Excel workbook — "Quick Reference" for
Responsible Sourcing analysts who want the scored output without running
the full Streamlit tool.

Output: Quick_Reference.xlsx (in project root)

Sheets (mirrors the Streamlit tool's structure):
  1.  README                          - what this is + bucket legend + caveats
  2.  Country × Risk Heatmap          - color-coded matrix (countries × priority risks)
  3.  Full Ranked Results             - every scored row, filterable, color-coded
  4.  Risk Library                    - 15 risks with definition, KPIs, supplier types
  5.  Risk × Process Matrix           - intensity (1–5) of each process per risk
  6.  Commodity Producers             - USGS top producers + critical-mineral flag
  7.  CAHRA Country List              - Glencore CAHRA list 2025
  8.  Country Indicators              - all raw indicators per country
  9.  Soil Vulnerability (SoilGrids)  - pH, SOC, CEC, derived vulnerability
  10. Water Stress (Aqueduct)         - WRI Aqueduct 4.0 country scores
  11. Glencore-Owned Assets           - public industrial assets from annual report
  12. Supplier Types                  - Glencore supplier-type library
  13. Risk → Supplier Types           - mapping for SAQ scoping
  14. Noise Baseline                  - NIOSH dBA per mining activity
  15. Methodology                     - formulas, normalization, weights
  16. Supplier Engagement Tiers       - OSDR → SAQ → onsite → CAP
  17. Scoring Weights                 - editable weights table
  18. Data Sources                    - all hyperlinked citations

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


def _generic_table(wb, sheet_name, df, widths=None, hyperlink_cols=None, freeze="A2"):
    """Generic helper to drop a DataFrame onto a sheet with header styling."""
    ws = wb.create_sheet(sheet_name)
    ws.append(list(df.columns))
    _style_header(ws[1])
    for _, row in df.iterrows():
        ws.append([("" if pd.isna(v) else v) for v in row.tolist()])
        r = ws.max_row
        if hyperlink_cols:
            for c in hyperlink_cols:
                cell = ws.cell(row=r, column=c)
                if isinstance(cell.value, str) and cell.value.startswith("http"):
                    cell.hyperlink = cell.value
                    cell.font = Font(color="FF0366D6", underline="single")
    ws.freeze_panes = freeze
    ws.auto_filter.ref = ws.dimensions
    if widths:
        _autosize(ws, widths)
    return ws


def sheet_risk_library(wb, risks, matrix, risk_supplier):
    ws = wb.create_sheet("Risk Library")
    ws.append(["Risk", "Category", "Definition", "Key KPIs (for SAQ)",
                "Driving processes (intensity 1-5)", "Likely supplier types",
                "Likelihood dataset", "Severity dataset"])
    _style_header(ws[1])
    rs_map = dict(zip(risk_supplier["risk_id"], risk_supplier["supplier_types"])) \
        if "risk_id" in risk_supplier.columns else {}
    for _, r in risks.iterrows():
        proc_rows = matrix[(matrix["risk_id"] == r["risk_id"]) & (matrix["applies"] == "Y")] \
            .sort_values("intrinsic_intensity_1_5", ascending=False)
        proc_str = "; ".join(f"{p['process']}: {int(p['intrinsic_intensity_1_5'])}"
                              for _, p in proc_rows.iterrows())
        ws.append([
            r["risk_type"], r["category"], r["definition"], r["key_kpis"],
            proc_str,
            rs_map.get(r["risk_id"], r.get("likely_supplier_types", "")),
            r["likelihood_dataset"], r["severity_dataset"],
        ])
        # Wrap multi-line cells
        row_idx = ws.max_row
        for c in [3, 4, 5, 6]:
            ws.cell(row=row_idx, column=c).alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[row_idx].height = 90
    ws.freeze_panes = "A2"
    _autosize(ws, [32, 12, 60, 60, 40, 40, 28, 28])


def sheet_risk_process_matrix(wb, risks, matrix):
    ws = wb.create_sheet("Risk × Process Matrix")
    pivot = matrix.pivot(index="risk_id", columns="process",
                          values="intrinsic_intensity_1_5").fillna(0)
    # Reorder columns so processes follow value-chain order
    order = ["Mining", "Refining", "Smelting", "Recycling", "Marketing"]
    pivot = pivot.reindex(columns=[c for c in order if c in pivot.columns])
    # Replace risk_id with risk_type
    label_map = dict(zip(risks["risk_id"], risks["risk_type"]))
    pivot.index = pivot.index.map(label_map)
    pivot = pivot.reset_index().rename(columns={"risk_id": "Risk"})
    ws.append(list(pivot.columns))
    _style_header(ws[1])
    for _, r in pivot.iterrows():
        ws.append(r.tolist())
        row_idx = ws.max_row
        for col_i, val in enumerate(r.tolist()[1:], start=2):
            cell = ws.cell(row=row_idx, column=col_i)
            try:
                v = int(float(val))
            except (TypeError, ValueError):
                v = 0
            # 1-5 intensity color (low→high)
            colors = {0: "FFEEEEEE", 1: "FFC8E6C9", 2: "FFFFF59D",
                      3: "FFFFCC80", 4: "FFFF8A65", 5: "FFE53935"}
            cell.fill = PatternFill("solid", start_color=colors.get(v, "FFEEEEEE"),
                                     end_color=colors.get(v, "FFEEEEEE"))
            cell.alignment = Alignment(horizontal="center")
            cell.font = Font(bold=True, color="FFFFFFFF" if v >= 5 else "FF000000")
    ws.freeze_panes = "B2"
    _autosize(ws, [40] + [14] * (len(pivot.columns) - 1))


def sheet_commodity_producers(wb, producers):
    df = producers.copy()
    df.columns = ["Commodity", "Country", "ISO-3", "Rank", "Share % global",
                   "Source", "Critical Mineral", "Critical Source"]
    return _generic_table(wb, "Commodity Producers", df,
                           widths=[18, 30, 8, 8, 12, 28, 12, 60],
                           hyperlink_cols=[8])


def sheet_cahra_list(wb, countries):
    ws = wb.create_sheet("CAHRA Country List")
    cahra = countries[countries["cahra_flag"] == "Y"][["iso3", "country", "cahra_regions"]] \
        .sort_values("country")
    cahra.columns = ["ISO-3", "Country", "CAHRA regions"]
    ws.append(list(cahra.columns))
    _style_header(ws[1])
    for _, r in cahra.iterrows():
        ws.append(r.tolist())
        row_idx = ws.max_row
        ws.cell(row=row_idx, column=2).fill = PatternFill(
            "solid", start_color="FFFFD54F", end_color="FFFFD54F")
        ws.cell(row=row_idx, column=2).font = Font(bold=True)
    ws.freeze_panes = "A2"
    _autosize(ws, [8, 32, 60])
    # Note row at top
    ws.insert_rows(1)
    ws["A1"] = (f"Source: Glencore CAHRA List 2025 (updated 27.02.2025) — "
                 f"{len(cahra)} countries flagged as Conflict-Affected & High-Risk Areas")
    ws["A1"].font = Font(italic=True, color="FF555555", size=11)
    ws.merge_cells("A1:C1")


def sheet_country_indicators(wb, countries):
    df = countries.copy().sort_values("country")
    return _generic_table(wb, "Country Indicators", df,
                           widths=[6, 28] + [13] * (len(df.columns) - 2))


def sheet_soilgrids(wb):
    path = ROOT / "data" / "processed" / "soilgrids_country.csv"
    if not path.exists(): return
    df = pd.read_csv(path).sort_values("country")
    df.columns = ["ISO-3", "Country", "Topsoil pH (0-5cm)",
                   "Soil organic carbon (g/kg)", "Cation exchange capacity (cmol/kg)",
                   "Soil vulnerability (1-5)", "Source"]
    ws = _generic_table(wb, "Soil Vulnerability (SoilGrids)", df,
                         widths=[6, 28, 16, 18, 22, 18, 60])
    # Color the vulnerability column 1-5
    for r in range(2, ws.max_row + 1):
        v = ws.cell(row=r, column=6).value
        if isinstance(v, (int, float)):
            colors = {1: "FFC8E6C9", 2: "FFDCEDC8", 3: "FFFFF59D",
                      4: "FFFFCC80", 5: "FFFF8A65"}
            band = max(1, min(5, int(round(v))))
            ws.cell(row=r, column=6).fill = PatternFill(
                "solid", start_color=colors[band], end_color=colors[band])
            ws.cell(row=r, column=6).number_format = "0.00"
            ws.cell(row=r, column=6).alignment = Alignment(horizontal="center")
    # Note
    ws.insert_rows(1)
    ws["A1"] = ("Source: ISRIC SoilGrids 2.0 — https://soilgrids.org. "
                 "Vulnerability = mean of pH-distance, SOC-binding, CEC-buffering scores. "
                 "Higher = more mobile heavy metals.")
    ws["A1"].font = Font(italic=True, color="FF555555", size=11)
    ws.merge_cells("A1:G1")
    ws.row_dimensions[1].height = 30


def sheet_aqueduct(wb):
    path = ROOT / "data" / "processed" / "aqueduct_country_scores.csv"
    if not path.exists(): return
    df = pd.read_csv(path).sort_values("name_0")
    df.columns = ["ISO-3", "Country", "UN region", "WB region",
                   "BWS — Baseline Water Stress (0-4)",
                   "DRR — Drought Risk (0-4)",
                   "RFR — Riverine Flood Risk (0-4)"]
    df = df.replace(-9999, "")  # Aqueduct no-data sentinel
    return _generic_table(wb, "Water Stress (Aqueduct)", df,
                           widths=[6, 28, 14, 24, 22, 18, 22])


def sheet_glencore_assets(wb):
    path = ROOT / "data" / "processed" / "glencore_assets.csv"
    if not path.exists(): return
    df = pd.read_csv(path)
    df.columns = ["Asset", "Type", "Commodity", "Country", "ISO-3",
                   "Lat", "Lon", "Status", "Source URL"]
    return _generic_table(wb, "Glencore-Owned Assets", df,
                           widths=[34, 18, 28, 28, 6, 8, 8, 18, 50],
                           hyperlink_cols=[9])


def sheet_supplier_types(wb):
    path = ROOT / "data" / "processed" / "supplier_types.csv"
    if not path.exists(): return
    df = pd.read_csv(path)
    df.columns = ["Supplier type (high-risk category)",
                   "Possible environmental effect",
                   "Possible human-rights effect"]
    ws = _generic_table(wb, "Supplier Types", df, widths=[40, 60, 60])
    # Wrap text
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    for r in range(2, ws.max_row + 1):
        ws.row_dimensions[r].height = 60


def sheet_risk_supplier(wb, risks, risk_supplier):
    if "risk_id" not in risk_supplier.columns: return
    df = risk_supplier.merge(risks[["risk_id", "risk_type"]], on="risk_id", how="left")
    df = df[["risk_type", "supplier_types"]]
    df.columns = ["Risk", "Likely supplier types"]
    ws = _generic_table(wb, "Risk → Supplier Types", df, widths=[40, 80])
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    for r in range(2, ws.max_row + 1):
        ws.row_dimensions[r].height = 36


def sheet_noise(wb, noise):
    df = noise.copy()
    df.columns = ["Process", "Activity", "Typical dBA min", "Typical dBA max", "Source"]
    ws = _generic_table(wb, "Noise Baseline", df, widths=[14, 36, 16, 16, 60])
    # Color by max dBA
    for r in range(2, ws.max_row + 1):
        v = ws.cell(row=r, column=4).value
        if isinstance(v, (int, float)):
            color = "FFE53935" if v >= 105 else ("FFFF9800" if v >= 95 else
                     "FFFFC107" if v >= 85 else "FF4CAF50")
            ws.cell(row=r, column=4).fill = PatternFill("solid", start_color=color, end_color=color)
    ws.insert_rows(1)
    ws["A1"] = ("Source: NIOSH Mining Noise — https://www.cdc.gov/niosh/mining/topics/Noise.html"
                " + IFC EHS Guidelines (Base Metal Smelting & Refining). "
                "OSHA action level 85 dBA, PEL 90 dBA.")
    ws["A1"].font = Font(italic=True, color="FF555555", size=11)
    ws.merge_cells("A1:E1")
    ws.row_dimensions[1].height = 32


def sheet_methodology(wb, weights):
    ws = wb.create_sheet("Methodology")
    ws["A1"] = "Scoring methodology"
    ws["A1"].font = Font(bold=True, size=18, color="FF00A9A5")
    rows = [
        ("Likelihood", "0.4 × Process Intrinsic Risk  +  0.6 × Country Hazard Score    →   1–5"),
        ("Severity",   "0.5 × Ecological Sensitivity   +  0.5 × Regulatory Strictness    →   1–5"),
        ("Overall",    "Likelihood × Severity     →   1–25"),
        ("",            ""),
        ("Buckets",    "1–4 Low · 5–9 Moderate · 10–14 High · 15–25 Critical"),
    ]
    r = 3
    for label, formula in rows:
        ws.cell(row=r, column=1, value=label).font = Font(bold=True, color="FF005F73")
        ws.cell(row=r, column=2, value=formula)
        r += 1
    r += 2
    ws.cell(row=r, column=1, value="Why these weights?").font = Font(bold=True, size=14)
    r += 1
    ws.cell(row=r, column=1, value=(
        "Process type determines whether a risk is possible at all (e.g., tailings only happen at "
        "mines), but the country's regulatory + ecological context determines whether a capable "
        "process actually causes harm. Two copper mines — Chile vs Zambia — have the same Process "
        "Intrinsic Risk for water depletion (5) but very different realized risk because Chile's "
        "Atacama is extremely water-stressed (Aqueduct BWS = 5) while Zambia is moderate (BWS = 2). "
        "Country context therefore weighs more (0.6) than process (0.4). Stricter regulators raise "
        "Severity because the tool measures penalty exposure, not pure ecological damage."
    ))
    ws.cell(row=r, column=1).alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[r].height = 110
    r += 3
    ws.cell(row=r, column=1, value="Scoring weights (editable in scoring_weights.csv)").font = Font(bold=True, size=14)
    r += 1
    ws.cell(row=r, column=1, value="Parameter").fill = HEADER_FILL
    ws.cell(row=r, column=1).font = HEADER_FONT
    ws.cell(row=r, column=2, value="Value").fill = HEADER_FILL
    ws.cell(row=r, column=2).font = HEADER_FONT
    ws.cell(row=r, column=3, value="Description").fill = HEADER_FILL
    ws.cell(row=r, column=3).font = HEADER_FONT
    weights_path = ROOT / "data" / "processed" / "scoring_weights.csv"
    if weights_path.exists():
        wdf = pd.read_csv(weights_path)
        for _, w in wdf.iterrows():
            r += 1
            ws.cell(row=r, column=1, value=w["parameter"])
            ws.cell(row=r, column=2, value=float(w["value"]))
            ws.cell(row=r, column=3, value=w["description"])
            ws.cell(row=r, column=3).alignment = Alignment(wrap_text=True, vertical="top")
            ws.row_dimensions[r].height = 30
    _autosize(ws, [32, 12, 80])


def sheet_supplier_tiers(wb):
    ws = wb.create_sheet("Supplier Engagement Tiers")
    ws["A1"] = "Supplier Engagement Tiers — Glencore SCDD M&M Procedure"
    ws["A1"].font = Font(bold=True, size=18, color="FF00A9A5")
    ws["A2"] = ("Glencore's SCDD M&M Procedure follows the OECD Due Diligence Guidance (3rd ed.) "
                 "five-step framework. The tool automates Tier 1 (OSDR — Open-Source Desktop Research) "
                 "and feeds Tiers 2–4 with targeted questions and evidence requirements.")
    ws["A2"].alignment = Alignment(wrap_text=True)
    ws.row_dimensions[2].height = 40
    headers = ["Tier", "Name", "What it does", "SCDD step", "Inputs", "Outputs", "Escalation rule"]
    ws.append([])
    ws.append(headers)
    _style_header(ws[4])
    tiers = [
        ("Tier 1", "OSDR — Open-Source Desktop Research",
         "Automated by THIS tool. Tier-1 risk ranking from public datasets per "
         "(commodity × country × process). CAHRA flag, supplier-type cues, KPI list.",
         "Step 2A — Supplier/product scoping",
         "Aqueduct, Yale EPI, WHO AAQ, Global Tailings Portal, IUCN Red List, WDPA, GFW, "
         "World Bank WGI, EDGAR, NIOSH, ISRIC SoilGrids, GEM, CAHRA list, USGS MCS+CMA",
         "Likelihood × Severity per row + CAHRA flag + likely supplier types + KPI watchlist",
         "Overall ≥ 10 (High/Critical) OR CAHRA-flagged → escalate to Tier 2"),
        ("Tier 2", "SCDD Questionnaire (SAQ) + extended OSDR",
         "Supplier completes SAQ targeted at the risks the tool flagged. Adverse-news screening, "
         "beneficial-ownership check, certifications review (RMI/Copper Mark/LBMA).",
         "Step 2B — SAQ + Step 2C Risk assessment",
         "Supplier-completed SAQ, management system docs, public policies, third-party assurance",
         "Evidence of EMS, traceability documents, corrective-action history, certifications",
         "Gaps or inconsistencies → Tier 3. No issues + risks managed → Approve."),
        ("Tier 3", "Onsite visit / On-the-Ground Assessment (OGA)",
         "Trained assessor onsite. Water/air/soil sampling, worker + community interviews, "
         "physical inspection of TSFs, effluent, safety practices.",
         "Step 3.1.5 Onsite visit / 3.1.6 OGA",
         "Field team, lab partners, sampling protocols",
         "Firsthand evidence, signed nonconformances, verified material traceability",
         "Unresolved nonconformances → Tier 4 (CAP). Severe violations → reject."),
        ("Tier 4", "Corrective Action Plan (CAP) + monitoring",
         "Time-bound remediation plan jointly designed with supplier; ongoing monitoring.",
         "Step 3.1.7 CAPs + monitoring",
         "Supplier sign-off, milestones, evidence requirements, reporting cadence",
         "CAP document, monitoring reports, escalation triggers, re-assessment date",
         "CAP met → re-approve. CAP missed → reject 3P."),
    ]
    tier_colors = {"Tier 1": "FF4CAF50", "Tier 2": "FF1976D2",
                    "Tier 3": "FFFF9800", "Tier 4": "FFE53935"}
    for t in tiers:
        ws.append(list(t))
        r = ws.max_row
        ws.cell(row=r, column=1).fill = PatternFill("solid",
            start_color=tier_colors[t[0]], end_color=tier_colors[t[0]])
        ws.cell(row=r, column=1).font = Font(bold=True, color="FFFFFFFF")
        ws.cell(row=r, column=1).alignment = Alignment(horizontal="center", vertical="center")
        for c in range(2, 8):
            ws.cell(row=r, column=c).alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[r].height = 110
    _autosize(ws, [10, 28, 50, 36, 50, 50, 36])


def sheet_scoring_weights(wb):
    path = ROOT / "data" / "processed" / "scoring_weights.csv"
    if not path.exists(): return
    df = pd.read_csv(path)
    df.columns = ["Parameter", "Value", "Description"]
    return _generic_table(wb, "Scoring Weights", df, widths=[34, 12, 80])


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
    risks, matrix, countries, producers, noise, weights, _st = _load()
    risk_supplier = pd.read_csv(ROOT / "data" / "processed" / "risk_supplier_types.csv")
    today = date.today().isoformat()
    print(f"Computing scores for export... (today: {today})")
    df = compute()  # all commodities, countries, processes, risks
    print(f"  {len(df):,} rows scored.")

    wb = Workbook()
    sheet_readme(wb, risks, countries, producers, today)
    sheet_country_risk(wb, df, risks)
    sheet_full_table(wb, df)
    sheet_risk_library(wb, risks, matrix, risk_supplier)
    sheet_risk_process_matrix(wb, risks, matrix)
    sheet_commodity_producers(wb, producers)
    sheet_cahra_list(wb, countries)
    sheet_country_indicators(wb, countries)
    sheet_soilgrids(wb)
    sheet_aqueduct(wb)
    sheet_glencore_assets(wb)
    sheet_supplier_types(wb)
    sheet_risk_supplier(wb, risks, risk_supplier)
    sheet_noise(wb, noise)
    sheet_methodology(wb, weights)
    sheet_supplier_tiers(wb)
    sheet_scoring_weights(wb)
    sheet_sources(wb, risks)
    wb.save(OUTPUT)
    print(f"✓ Wrote {OUTPUT.name}  ({OUTPUT.stat().st_size / 1024:.0f} KB) — {len(wb.sheetnames)} sheets")
    print(f"  Location: {OUTPUT}")


if __name__ == "__main__":
    main()
