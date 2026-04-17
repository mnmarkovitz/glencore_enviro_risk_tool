# Environmental Risk Identification & Assessment Tool

A contextual pivot tool for identifying, ranking and auditing environmental risks across a global commodity mining and trading supply chain. Every Likelihood and Severity score is derived from a **named public dataset**; nothing is subjective analyst input.

## What it does

Pick any combination of **commodity, country, process** (Mining / Refining / Smelting / Recycling / Marketing) and **risk type** (15 risks; 8 priority). The tool returns:

1. A **ranked risk table** (descending Overall = Likelihood × Severity) with both **raw indicator values** and **normalized 1–5 scores** so every number can be audited back to its source.
2. A **5 × 5 Likelihood × Severity heatmap**.
3. **Drill-down** per row: risk definition, the specific dataset used, and the raw + normalized scores.
4. A **Noise baseline** tab showing typical dBA by mining activity (NIOSH + IFC EHS).
5. **Methodology** and **Data Sources** tabs listing every input dataset with URL.

## Quick start

```bash
# Install
pip install -r requirements.txt

# Run the app
streamlit run app/streamlit_app.py
```

Opens at http://localhost:8501.

## Project layout

```
glencore_env_risk_tool/
├── app/
│   ├── streamlit_app.py      # UI (filters, heatmap, table, drill-down)
│   └── scoring.py            # Normalized scoring engine
├── data/
│   ├── raw/                  # Refreshable external datasets (see scripts/02_*)
│   └── processed/            # EDITABLE CSVs that drive the tool:
│       ├── risks.csv                    # 15 risks: definition, KPIs, source datasets
│       ├── risk_process_matrix.csv      # Risk × Process applicability (1–5)
│       ├── commodity_producers.csv      # USGS top producers per commodity
│       ├── country_indicators.csv       # Country-level raw indicators (EPI, PM2.5, etc.)
│       ├── aqueduct_country_scores.csv  # WRI Aqueduct 4.0 (bws, drr, rfr)
│       ├── noise_process_baseline.csv   # NIOSH dBA by mining activity
│       └── scoring_weights.csv          # Tunable weights (L = αP + βC, S = γE + δR)
├── scripts/
│   ├── 01_process_aqueduct.py
│   ├── 02_fetch_external_data.py        # Refresh external datasets
│   └── 03_merge_to_indicators.py        # Merge raw → processed
├── docs/
│   ├── METHODOLOGY.md
│   └── HOW_TO_EDIT.md
└── README.md
```

## Editing the tool

All of the tool's logic is in CSVs under `data/processed/`. Anyone can edit them in Excel, Google Sheets, or a text editor. Restart the app (`Ctrl-C` then re-run) or hit `R` in the Streamlit UI to pick up changes. See `docs/HOW_TO_EDIT.md`.

## Refreshing external data

```bash
# World Bank (public, no auth)
python scripts/02_fetch_external_data.py --source worldbank

# All sources (some require manual downloads)
python scripts/02_fetch_external_data.py --source all

# Merge fetched data into country_indicators.csv
python scripts/03_merge_to_indicators.py
```

Datasets requiring free account registration (download manually to `data/raw/`):
- **Yale EPI 2024** — https://epi.yale.edu/downloads
- **Global Tailings Portal** — https://tailing.grida.no/data
- **WHO Ambient Air Quality DB** — https://www.who.int/data/gho/data/themes/air-pollution
- **Global Forest Watch country summary** — https://www.globalforestwatch.org/dashboards/global/
- **IUCN Red List** — set `IUCN_TOKEN` env var after requesting at https://apiv3.iucnredlist.org

The tool ships with seed values for ~43 top mining/oil-producing countries from these sources, so it works out of the box.

## Scoring (one-liner)

```
Likelihood = 0.4 × Process_Intrinsic  +  0.6 × Country_Hazard        (1–5)
Severity   = 0.5 × Ecological_Sensitivity + 0.5 × Regulatory_Strictness (1–5)
Overall    = Likelihood × Severity                                    (1–25)
```

Buckets: 1–4 Low · 5–9 Moderate · 10–14 High · 15–25 Critical. Full method in `docs/METHODOLOGY.md`.

## Deploy publicly

Push this directory to a GitHub repo, then:

1. Go to https://share.streamlit.io
2. New app → point to `app/streamlit_app.py`
3. Free public URL.
