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
│   └── 09_add_nrgi_ej_atlas.py
├── docs/
│   ├── OVERVIEW_AND_HANDOVER.md  (this file — single entry point)
│   ├── METHODOLOGY.md            (full scoring rules)
│   └── USER_GUIDE.md             (analyst-facing walkthrough)
├── .streamlit/config.toml        (turquoise theme)
├── Dockerfile + docker-compose.yml  (one-command deploy)
├── requirements.txt              (pinned Python dependencies)
├── Quick_Reference.xlsx          (15-sheet Excel companion)
└── (no other top-level deliverable files)
```

---

## 8. Step by step — how this was built (plain-English version)

If a stakeholder ever asks "where did this come from?", here is the simplest possible walkthrough.

### Step 1 — pick the risks
We started from Glencore's existing saliency-based environmental risk framework and the OECD Handbook on Environmental Due Diligence in Mineral Supply Chains (2023), which list the categories: water pollution, water depletion, tailings, biodiversity (species and ecosystems), noise, air, soil, hazardous waste, and so on. We have **13 environmental risks** in total, all treated equally (no priority/secondary distinction).

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

## 9. Data selection criteria — why these datasets

Every dataset in the tool had to pass five tests, in priority order:

1. **Public and free.** No paywalled or subscription data (this is why the SEED Index was excluded). The tool's value proposition is that any score can be re-derived by anyone.
2. **Global country coverage.** The dataset must score most countries on a comparable scale, so cross-country comparison is valid. (This is why noise pollution has no country layer — no global dataset exists; only the NIOSH process baseline.)
3. **Authoritative / institutional.** Produced by a recognised body — UN agency, World Bank, USGS, WRI, Yale, IUCN, ISRIC, EC JRC, or an OECD-aligned initiative. No crowd-sourced or unverifiable sources.
4. **Directly relevant to the specific risk.** Each risk is mapped to the dataset that most precisely measures it (Aqueduct for water stress; IUCN for species; SoilGrids for soil chemistry), not a generic proxy, wherever one exists.
5. **Refreshable.** The dataset is updated on a known cadence and can be re-pulled (see Section 6), so the tool does not decay.

Where no single dataset satisfies tests 2 + 4 (e.g., regulatory governance), the tool **blends several** so no one source dominates — Regulatory Strictness combines World Bank WGI, Yale EPI, NRGI Resource Governance Index, and the EJ Atlas conflict count.

## 10. Scope notes and known coverage gaps

### How "recycling" is defined
In this tool, **Recycling** means secondary recovery of metals from end-of-life or scrap feedstock — re-smelting and re-refining of recovered material rather than virgin ore. Its process-intensity scores (`risk_process_matrix.csv`) reflect that recycling:
- still runs high-temperature furnaces and chemical leaching (so air, waste, and water-pollution intensities remain material — often 4–5/5);
- generates **hazardous secondary waste streams** of highly variable quality (waste-pollution intensity 5/5);
- does **not** generate tailings or cause direct habitat loss the way mining does (those intensities drop to 1–2).

**Treatment of mixed sources:** the tool scores recycling as a *process type*, not a feedstock-purity claim. It does not distinguish 100%-recycled from blended (recycled + primary) feedstock — that distinction is handled in Glencore's SCDD procedure itself (Step 2: a supplier of 100% recycled material with no precious-metal blending can be out of scope, whereas blended material is treated as primary). The tool flags the *environmental* risks of the recycling process; the *feedstock-purity / chain-of-custody* question is a separate due-diligence determination made in the SAQ.

### Countries, producers, and "transit / sourcing jurisdiction" mode (e.g., Nigeria)
The commodity filter is driven by `commodity_producers.csv`, which lists the **USGS top-~10 producer countries** for each commodity. A country appears *under a commodity* only if it is a top-tier global producer of it.

**Nigeria** and ~35 other countries (mostly CAHRA jurisdictions) are in the country database — fully scored, CAHRA-flagged — but are **not top-10 producers of any tracked commodity**. They therefore don't surface in a commodity-filtered producer list. To make these analysable, the **country dropdown lists every country in the database** (producers first, then non-producers labelled as transit jurisdictions). Selecting a non-producer country scores it in **transit / sourcing-jurisdiction mode**: every risk × process is evaluated from the country's own environmental + governance hazard and the process-intrinsic risk, with the commodity shown as "(transit / sourcing jurisdiction)." This supports OECD "red-flag location of mineral origin or transit" screening.

To instead treat such a country as a *producer* of a specific commodity, add a row to `commodity_producers.csv` (commodity, country, iso3, rank, share) — its scores compute immediately because its indicator data already exists.

### Oil & gas country scores
All 10 oil & gas producer countries in the tool (US, Saudi Arabia, Russia, Canada, China, Iraq, UAE, Brazil, Iran, Kuwait) are **fully scored** — every risk × process combination returns an Overall score. If a particular *cell* shows "—" it is the **raw hazard column** for a risk that has no global country dataset (e.g., noise pollution) or no data for that country (e.g., a desert state with no Aqueduct flood category). In those cases the Likelihood still computes from the process-intrinsic score, and the Overall is still produced. "—" in a raw-indicator cell never means the row is unscored; it means that one public input is unavailable and the fallback rule applied (see `docs/METHODOLOGY.md`, "Missing data").

## 11. Customizing the app

Everything an analyst would want to change lives in CSVs under `data/processed/` — no Python required. Common customizations:

| I want to… | Edit this file | Notes |
|---|---|---|
| Add a commodity | `commodity_producers.csv` | Add rows (commodity, country, iso3, rank, share, source, critical flag). Producer countries must exist in `country_indicators.csv`. |
| Add a country | `country_indicators.csv` (+ `country_centroids.csv` for the map, `soilgrids_country.csv` for soil) | Fill any indicators you have; blanks fall back gracefully. |
| Add / edit a risk | `risks.csv` (+ a row per process in `risk_process_matrix.csv`, + a row in `risk_supplier_types.csv`) | Map the risk to its public likelihood + severity datasets. |
| Change how a process drives a risk | `risk_process_matrix.csv` | Edit the 1–5 `intrinsic_intensity` and the rationale. |
| Re-weight the formula | `scoring_weights.csv` | Change the 0.4/0.6 (likelihood) or 0.5/0.5 (severity) split, or the bucket thresholds. |
| Re-map supplier types to risks | `risk_supplier_types.csv` | Drives the "Supplier type (high risk categories)" column. |
| Add Glencore-owned assets to the map | `glencore_assets.csv` | Public assets only. Cite `source_url` per row. |
| Add confidential suppliers to the map | `glencore_suppliers.csv` | Git-ignored; stays local/confidential. |

To change the **app's behavior or look** (tabs, colors, charts) edit `app/streamlit_app.py`; the scoring logic is isolated in `app/scoring.py`. After any change: rerun the app (or push to trigger a Streamlit Cloud rebuild) and rebuild the Excel with `python scripts/08_export_quick_reference.py`.

## 12. Where to ask questions

| Question | Where to look |
|---|---|
| What does this score mean? | Drill-down panel of the Streamlit tool, or `Full Ranked Results` sheet in the Excel |
| Is this dataset trustworthy? | `Data Sources` sheet in the Excel; every URL listed |
| What's the math? | `Methodology + Scoring Weights` sheet in the Excel; `docs/METHODOLOGY.md` |
| Why these datasets? | Section 9 of this document |
| How is recycling defined? Why is country X (e.g. Nigeria) missing? | Sections 10 & 11 of this document |
| How do I customize the tool? | Section 11 of this document |
| How do I deploy this on our infrastructure? | Section 5 of this document |
| How does this fit our SCDD procedure? | `Supplier Engagement Tiers` sheet in the Excel; `docs/USER_GUIDE.md` |
