# Project Overview & Handover

A plain-language guide to what was built, how it works, how to integrate it into Glencore's systems, and how to keep it up to date — whether the user works in the live tool, the Excel workbook, or the underlying source files.

This document is the single starting point for anyone receiving the project. Read this first; everything else is reference.

---

## 1. What was delivered

Three things, in one project folder:

| Artifact | What it is | Who uses it |
|---|---|---|
| **Live Streamlit tool** | A web app at a permanent public URL. Filters, maps, heatmaps, drill-down. | Responsible Sourcing analysts |
| **`Quick_Reference.xlsx`** | 15-sheet Excel workbook with the same data, color-coded. No technical setup required. | Same analysts; offline use; sharing with non-technical stakeholders |
| **Source code repo** | Public GitHub repo containing every CSV, every Python file, every doc. The tool and Excel are both rebuilt from this. | Glencore IT during handover |

---

## 2. How the tool was built — in one paragraph

We took every public, audit-able dataset that says something about environmental risk in a country (water, air, soil, biodiversity, governance, tailings, mines), put each country's score into a single CSV table, multiplied that table by a small "process intensity" table that says how much each mining process drives each risk, and ran the result through a one-page formula that produces a 1–25 risk score per (commodity × country × process × risk) row. The Streamlit web app is just a friendly view over that table — filters, charts, maps. The Excel workbook is the same table exported with color coding, hyperlinks, and a few summary sheets.

---

## 3. Component architecture (visual)

```
┌──────────────────────────────────────────────────────────────────────────┐
│   PUBLIC DATASETS (refreshed periodically, all free)                     │
│   WRI Aqueduct · Yale EPI · WHO PM2.5 · IUCN Red List · WDPA · GFW       │
│   USGS MCS · USGS MRDS · USGS Critical Minerals Atlas · GEM · ISRIC      │
│   SoilGrids · World Bank WGI · NRGI Resource Governance Index · EJ       │
│   Atlas · INFORM Risk · UNESCO World Heritage · Glencore CAHRA List      │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│   data/processed/   (the editable middle layer — CSV files)              │
│   risks.csv · risk_process_matrix.csv · risk_supplier_types.csv          │
│   country_indicators.csv · soilgrids_country.csv ·                       │
│   aqueduct_country_scores.csv · commodity_producers.csv ·                │
│   country_centroids.csv · glencore_assets.csv · glencore_suppliers.csv   │
│   noise_process_baseline.csv · scoring_weights.csv · supplier_types.csv  │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│   app/scoring.py  (the formula engine, ~400 lines)                       │
│   • Reads every CSV above                                                │
│   • Joins them on iso3 / commodity / risk_id / process                   │
│   • Computes  Likelihood = 0.4 × process + 0.6 × country hazard          │
│              Severity   = 0.5 × eco sensitivity + 0.5 × regulatory       │
│              Overall    = Likelihood × Severity                          │
│   • Returns a long-form DataFrame with one row per combination           │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
       ┌──────────────────────┐          ┌────────────────────────────┐
       │  app/streamlit_app   │          │  scripts/08_export_quick   │
       │  .py                 │          │  _reference.py             │
       │  • the live web app  │          │  • exports the Excel       │
       │  • 9 tabs, filters,  │          │    workbook (15 sheets)    │
       │    maps, drill-down  │          │  • run on demand           │
       └──────────────────────┘          └────────────────────────────┘
                  │                                   │
                  ▼                                   ▼
       Public Streamlit URL                 Quick_Reference.xlsx
```

There is **no database**, **no server**, **no API to maintain**. The CSVs are the entire state.

---

## 4. How the scoring works (one page)

### Inputs

For each environmental risk (15 in total — water pollution, water depletion, tailings, biodiversity, etc.), we look up two things:

1. **Process Intrinsic Risk** (1–5): does this mining stage drive this risk? Tailings has Mining = 5, Marketing = 1. From `risk_process_matrix.csv`.
2. **Country Hazard Score** (1–5): what does the public data say about this country's exposure to this risk? Aqueduct's Baseline Water Stress for water depletion. IUCN species count for biodiversity. SoilGrids pH+SOC+CEC for soil pollution. From `country_indicators.csv` + a few other CSVs joined on `iso3`.

We also compute two country-level severity ingredients (these are shared across all risks):

3. **Ecological Sensitivity** (1–5): Yale EPI Ecosystem Vitality + Protected Planet WDPA % protected (both inverted)
4. **Regulatory Strictness** (1–5): blended from four governance datasets — World Bank WGI Regulatory Quality, Yale EPI overall, **NRGI Resource Governance Index**, and **EJ Atlas conflict count** (high counts reduce strictness because they signal contested or poorly enforced regimes).

### The formulas

```
Likelihood = 0.4 × Process Intrinsic + 0.6 × Country Hazard      →   1–5
Severity   = 0.5 × Ecological Sensitivity + 0.5 × Regulatory      →   1–5
Overall    = Likelihood × Severity                                →   1–25
```

Bucket: 1–4 Low · 5–9 Moderate · 10–14 High · 15–25 Critical.

The weights (0.4, 0.6, 0.5, 0.5) and bucket thresholds live in `scoring_weights.csv` and can be changed without touching code.

---

## 5. How to integrate into Glencore's systems

There are three integration paths. Pick whichever your IT team prefers — the underlying logic is the same in all three.

### Path A — keep the Streamlit tool, host it inside Glencore (recommended)

A `Dockerfile` and `docker-compose.yml` are in the repo. One command builds a container:

```bash
docker compose up -d
```

Deploy the resulting container to:
- Azure App Service (Glencore is on Azure)
- AWS ECS / Fargate
- An on-prem Linux box
- Glencore's internal Kubernetes

Put Glencore SSO (Azure AD / Okta) in front of the container. Now only Responsible Sourcing team members can access it.

The CSVs in `data/processed/` can be replaced with database tables (Glencore's counterparty master, supplier master, internal CAHRA list) by editing `app/scoring.py`'s `_load()` function — it currently does `pd.read_csv()`; swap each with `pd.read_sql()` against Glencore's data warehouse and the rest of the tool works unchanged.

### Path B — port the scoring engine into Glencore's BI stack

The scoring engine is one Python file (`app/scoring.py`, ~400 lines). It is linear algebra on small tables. It ports cleanly to:

- **Power BI**: import each CSV as a Dataflow, re-implement the formulas as DAX measures. The full math is in the README sheet of the Excel workbook + `docs/METHODOLOGY.md`.
- **Tableau**: same approach with calculated fields.
- **A Python microservice** that the existing SCDD management platform calls via REST. Wrap `compute()` in a Flask / FastAPI endpoint that accepts a supplier record and returns the scored rows.

### Path C — keep using the Streamlit tool + Excel as-is

If Glencore's IT team doesn't want to host anything, the team can:
- Keep using the existing public Streamlit URL (recommended only for prototyping — it's hosted on the project's free Streamlit Community Cloud account, which Glencore should eventually transfer or replace)
- Distribute the `Quick_Reference.xlsx` workbook by email or SharePoint
- Run the Streamlit tool locally on individual analysts' laptops via `streamlit run app/streamlit_app.py`

---

## 6. How to update the data and the tool

### Refreshing public datasets (quarterly)

Most external data refreshes are scripted under `scripts/`. The maintainer (one analyst on rotation) runs:

```bash
python scripts/02_fetch_external_data.py --source worldbank
python scripts/05_fetch_usgs_mrds.py
python scripts/06_fetch_gem.py
python scripts/07_fetch_soilgrids.py
```

Each script overwrites the relevant CSV in `data/raw/` and, for some, `data/processed/`. A few datasets require manual download from a website that needs free registration (Yale EPI, WHO Ambient Air Quality, Global Tailings Portal); paths and instructions are at the top of `scripts/02_fetch_external_data.py`.

### Annual updates

The Glencore CAHRA list is updated annually by Glencore's RS team. To reflect the new edition: open `country_indicators.csv` in Excel, edit the `cahra_flag` and `cahra_regions` columns, save. Same pattern for any Glencore-owned asset additions in `glencore_assets.csv`.

### Re-exporting the Excel workbook after any data change

```bash
python scripts/08_export_quick_reference.py
```

Takes about 5 seconds. Overwrites `Quick_Reference.xlsx`.

### Re-deploying after CSV or code changes

If the Streamlit tool is hosted on Streamlit Community Cloud or in a Docker container with a Git-pull deploy:

```bash
git add data/processed
git commit -m "Refresh quarterly indicators"
git push
```

Streamlit Cloud auto-rebuilds within ~60 seconds. Docker container picks up changes on the next pull or rebuild.

---

## 7. What sits where in the repo (file map)

```
glencore_enviro_risk_tool/
├── app/
│   ├── streamlit_app.py        Live web app (UI + filters + charts + maps)
│   └── scoring.py              The formula engine (~400 lines)
├── data/
│   ├── raw/                    External downloads (kept out of Git)
│   └── processed/              The 13 CSVs that drive everything
├── scripts/                    Refresh scripts (one per data source)
│   ├── 01_process_aqueduct.py
│   ├── 02_fetch_external_data.py
│   ├── 03_merge_to_indicators.py
│   ├── 04_add_cahra_countries.py
│   ├── 05_fetch_usgs_mrds.py
│   ├── 06_fetch_gem.py
│   ├── 07_fetch_soilgrids.py
│   ├── 08_export_quick_reference.py    (rebuilds the .xlsx)
│   ├── 09_add_nrgi_ej_atlas.py
│   ├── build_slides.py                  (rebuilds the class deck)
│   └── capture_screenshots.py
├── docs/
│   ├── OVERVIEW_AND_HANDOVER.md  (this file)
│   ├── METHODOLOGY.md            (full scoring rules)
│   ├── USER_GUIDE.md             (analyst-facing walkthrough)
│   ├── INTEGRATION_GUIDE.md      (Glencore IT integration paths)
│   └── HANDOVER.md               (extended IT handover playbook)
├── .streamlit/config.toml        (turquoise theme)
├── Dockerfile + docker-compose.yml  (one-command deploy)
├── requirements.txt              (pinned Python dependencies)
├── Quick_Reference.xlsx          (15-sheet Excel companion)
└── Glencore_Env_Risk_Tool_Deck.pptx  (class presentation)
```

---

## 8. Step by step — how this was built (plain-English version)

If a stakeholder ever asks "where did this come from?", here is the simplest possible walkthrough.

### Step 1 — pick the risks
We started from Glencore's existing saliency-based environmental risk framework and the OECD Handbook on Environmental Due Diligence in Mineral Supply Chains (2023), which list the categories: water pollution, water depletion, tailings, biodiversity (species and ecosystems), noise, air, soil, hazardous waste, and so on. We have 15 risks total, 8 prioritized.

### Step 2 — pick the public dataset that says how bad each risk is in each country
For each risk, we found the best free, audit-able dataset. Aqueduct for water. WHO for air. IUCN for species. SoilGrids for soil. Global Tailings Portal for tailings. Etc. The mapping is in `risks.csv`.

### Step 3 — say how much each mining stage drives each risk
A small editable table (`risk_process_matrix.csv`): tailings is a 5/5 risk for Mining, 1/5 for Marketing. Air pollution is 5/5 for Smelting, 4/5 for Mining. Etc. Based on ENCORE materiality ratings + IFC EHS Guidelines.

### Step 4 — build a country indicator table
One big CSV (`country_indicators.csv`) with one row per country and one column per indicator: Yale EPI, WHO PM2.5, World Bank governance, IUCN species count, NRGI Resource Governance, EJ Atlas conflict count, and so on.

### Step 5 — run the formula
For every (commodity × country × process × risk) combination — about 10,000 rows — multiply the process score by the country score with the published 0.4 / 0.6 weights, do the same for severity with 0.5 / 0.5, multiply L × S to get Overall, bucket it into Low/Moderate/High/Critical.

### Step 6 — show the result
Two views over the same table: a Streamlit web app (filters, charts, maps) and an Excel workbook (15 colour-coded sheets).

### Step 7 — add the supplier engagement workflow
Map every output row back to Glencore's existing SCDD Procedure for Metals & Minerals — specifically Steps 2A through 2G + 3 — so an analyst can see "Critical row at Tier 1 OSDR → escalate to Tier 2 SAQ" automatically.

That's the whole project.

---

## 9. Where to ask questions

| Question | Where to look |
|---|---|
| What does this score mean? | Drill-down panel of the Streamlit tool, or `Full Ranked Results` sheet in the Excel |
| Is this dataset trustworthy? | `Data Sources` sheet in the Excel; every URL listed |
| What's the math? | `Methodology + Scoring Weights` sheet in the Excel; `docs/METHODOLOGY.md` |
| How do I deploy this on our infrastructure? | This document, Section 5; `docs/INTEGRATION_GUIDE.md` for more detail |
| How does this fit our SCDD procedure? | `Supplier Engagement Tiers` sheet in the Excel; `docs/USER_GUIDE.md` |
