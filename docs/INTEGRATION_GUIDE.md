# Integration Guide — handover to Glencore

This document outlines the path for Glencore IT / Responsible Sourcing to take this tool from a local prototype into Glencore's production systems.

## 1. What ships today

- A Python-based Streamlit web app (`app/streamlit_app.py`)
- Eight editable CSVs under `data/processed/` that drive the entire logic
- A scoring engine (`app/scoring.py`) that reads CSVs → returns Likelihood, Severity, Overall scores per (risk × commodity × country × process)
- Fetch scripts for public APIs (`scripts/`)

No database is required; the app is stateless and reads CSVs on each load.

## 2. Deployment options (ranked from simplest to most enterprise)

### Option A — Public Streamlit Community Cloud (free, good for external review)
1. Push the `glencore_env_risk_tool/` folder to a public GitHub repo.
2. Go to https://share.streamlit.io → New app → point to `app/streamlit_app.py`.
3. Public URL issued in ~2 min. Free tier fine for < 10 concurrent users.

**Not suitable for Glencore-confidential supplier lists.** Only safe for the public-data scoring tool as shipped.

### Option B — Private Streamlit hosted by Glencore
Package as a Docker container:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Deploy to Glencore's internal Kubernetes, Azure App Service, or equivalent. Put Glencore SSO in front of it (e.g., Azure AD).

### Option C — Port the logic into Glencore's existing DD platform
The scoring engine is ~300 lines of Python in one file (`app/scoring.py`). It can be translated into:

- **Power BI**: CSVs → Dataflows, scoring formulas → DAX measures
- **Python microservice** that Glencore's SCDD management platform calls via REST
- **SQL views** on Glencore's data warehouse (the scoring is linear combinations — trivial in SQL)

All the hard work (dataset choice, normalization rules, weights) is in the CSVs — those move as-is.

## 3. Connecting to Glencore's supplier master

The tool today takes a country + commodity + process and returns environmental risk. In production, Glencore likely wants to feed in a **supplier record** and get back a risk profile. Two touchpoints:

### Input side — onboarding form
The Glencore SCDD M&M procedure already has onboarding/transaction forms that capture:
- Supplier name, counterparty ID
- Product (commodity) and specification
- Country of mine/origin
- Country of transit
- Process stage (mining vs refining vs recycling)

Map those form fields into this tool's filter inputs. Result: automatic Tier-1 risk ranking per supplier on onboarding.

### Output side — auto-populating the SAQ
Each row the tool emits includes:
- `likely_supplier_types` → which SAQ section to prioritize
- `risk KPIs` (from `risks.csv`) → which specific questions to ask
- `cahra_flag` → triggers the CAHRA-specific sub-questionnaire already in Glencore's SCDD procedure

This maps directly into Glencore's SAQ builder: the tool's output can pre-select which of the standard SAQ modules get sent to a given supplier.

## 4. Data refresh cadence

| Dataset | Suggested refresh |
|---|---|
| Glencore CAHRA list | Annual (aligned with Glencore's own update cycle) |
| Yale EPI | Every 2 years (new release) |
| WRI Aqueduct | On each WRI release (roughly every 2–3 years) |
| Global Tailings Portal | Quarterly |
| WHO Ambient Air Quality | Annual |
| World Bank (CO₂, WGI) | Annual |
| IUCN Red List | Annual |
| INFORM Risk | Annual |
| Commodity producer rankings (USGS MCS) | Annual (January) |

Refresh is manual by running `scripts/02_fetch_external_data.py`. For production, put it on a monthly cron.

## 5. Glencore-specific customizations worth doing at handover

1. **Replace seed country indicators with Glencore's own country risk database** (if one exists). Keep the same column names.
2. **Add Glencore's supplier IDs as a dimension** — add a column in a supplier-facing CSV and let the tool filter by supplier.
3. **Extend the CAHRA flag** to include Glencore's Declined Party List (DPL) and Red Flag List. Add a `dpl_flag` column to `country_indicators.csv` or a new `suppliers.csv`.
4. **Add provincial/sub-national detail** for CAHRA countries where only some regions are flagged (Colombia, Mexico, Philippines, etc.). The Aqueduct province_baseline data has ~43k rows at sub-national level ready to go.
5. **Connect to the SAQ management platform** so that when the tool produces a CAHRA + High/Critical finding it auto-queues the relevant SAQ modules.
6. **Lock down public data sources with hash-stamped caches** so audit trails can reference exact dataset versions.

## 6. Security considerations

- No secrets in the repo today. Set `IUCN_TOKEN` via environment variable when running fetch scripts.
- When Glencore-confidential supplier data is added, move it out of the public CSV pattern into a secured database; only the app should have read access.
- Audit trail: add logging around `compute()` calls so every risk assessment is reproducible with the exact CSV version used.

## 7. Licensing / dataset attribution

The tool uses publicly-available datasets. Each dataset's license should be respected at deployment:

- WRI Aqueduct — CC BY 4.0
- Yale EPI — CC BY-NC 4.0 (non-commercial) — verify commercial use permitted under Glencore's licensing
- Global Tailings Portal — Creative Commons; attribution to Church of England Pensions Board / GRID-Arendal
- IUCN Red List — terms of use require attribution; commercial use requires agreement
- WHO AAQ — free for public use
- World Bank — CC BY 4.0
- WDPA — non-commercial use without fee; commercial use requires license

Include attributions in the deployed app footer. The current sidebar already has team attribution — extend that to dataset credits.

## 8. Point of contact

For questions about the tool's structure or methodology during handover, contact the NYU SPS Global Affairs team listed in the app's sidebar footer.
