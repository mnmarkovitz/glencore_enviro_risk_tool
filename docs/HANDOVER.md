# Handover playbook — transferring the Environmental Risk Tool to Glencore

This document is for the Glencore team taking over ownership. It outlines everything needed to run, update, and host the tool independently of the NYU SPS team's personal accounts, laptops, or cloud services.

After following this playbook, the tool can be operated and maintained indefinitely by Glencore with **no dependency** on the original authors.

---

## 1. What you are receiving

A single folder containing:

```
glencore_enviro_risk_tool/
├── app/                    # Streamlit UI + scoring engine (Python, ~600 lines total)
├── data/processed/         # 10 editable CSVs — the entire logic
├── scripts/                # Refresh scripts for public datasets
├── docs/                   # METHODOLOGY.md, HOW_TO_EDIT.md, INTEGRATION_GUIDE.md, this file
├── .streamlit/             # UI theme config
├── .gitignore
├── Dockerfile              # Portable container
├── docker-compose.yml      # One-command run
├── requirements.txt        # Python dependencies (pinned)
└── README.md
```

No external databases, no hidden services, no API keys baked in. Every dataset the tool uses is either bundled as a CSV or fetched on demand from a public source (with fetch scripts in `scripts/`).

## 2. Handover checklist (Day 1 — Glencore IT)

### 2.1 Transfer source code to Glencore's Git

Choose one of:

**Option A — Import the GitHub repo into Glencore's GitHub / GitLab / Bitbucket:**
1. NYU team gives you the repo URL (currently `https://github.com/mnmarkovitz/glencore_enviro_risk_tool`)
2. Glencore IT uses their Git host's import function (GitHub: "Import a repository"; GitLab: "Import project"; Bitbucket: similar)
3. Point it at the public repo URL
4. Glencore now owns the code

**Option B — Zip + clean-room commit:**
1. NYU team delivers `glencore_enviro_risk_tool.zip` via secure channel
2. Glencore IT unzips, runs `git init`, creates first commit in Glencore's Git system
3. No traces of original authors' commit history

Either is fine — Option A preserves commit history (useful for audit), Option B is cleaner if Glencore prefers a fresh start.

### 2.2 Kill the NYU-hosted Streamlit Cloud deployment

1. NYU team signs into https://share.streamlit.io
2. Deletes the app or transfers it to Glencore's Streamlit account (Streamlit supports this via app settings → "Transfer ownership")
3. If deleted, Glencore redeploys from their own repo as below

### 2.3 Stand up Glencore's hosted instance (pick one)

#### Option 1 — Docker on Glencore infrastructure (recommended)

The repo contains a `Dockerfile` and `docker-compose.yml`. One command deploys the tool behind Glencore's firewall:

```bash
docker compose up -d
```

Deploy this container to:
- Azure App Service (Glencore uses Azure — a Web App for Containers takes <10 min to set up)
- AWS ECS / Fargate
- An internal Kubernetes cluster
- An on-prem Linux box

Put Glencore SSO (Azure AD / Okta) in front of it so only Responsible Sourcing team members can access.

#### Option 2 — Streamlit Community Cloud (Glencore's account)

1. Glencore creates a Streamlit Cloud account linked to a Glencore GitHub org
2. Import the repo
3. New app → point at `app/streamlit_app.py` → Deploy
4. Only suitable if Glencore is comfortable with a **public** URL (free tier). For private/SSO-gated, use Docker.

#### Option 3 — Port into Glencore's existing BI stack

The scoring engine is ~300 lines of Python. It's linear algebra on CSVs — trivially ported to:
- **Power BI**: import the CSVs as Dataflows, re-implement formulas as DAX measures (documented in `docs/METHODOLOGY.md`)
- **Tableau**: same approach
- **Internal Python microservice** called by an existing SCDD management platform

If Glencore prefers this route, `docs/INTEGRATION_GUIDE.md` section 3 has more detail.

### 2.4 Swap in Glencore's confidential data

Three CSVs should be replaced with Glencore's internal data on handover:

| Current file | Replace with |
|---|---|
| `data/processed/glencore_suppliers.csv` (empty template) | Glencore's counterparty master — all third-party suppliers with country, commodity, lat/lon, SCDD status |
| `data/processed/glencore_assets.csv` (39 public assets) | Complete, up-to-date list from Glencore's internal asset register |
| `data/processed/country_indicators.csv` CAHRA cells | Replace with the internal CAHRA list if Glencore maintains it outside the published annual edition |

All three files are already in `.gitignore` (or should be added there) so confidential data never reaches a public repo.

### 2.5 Set up data refresh cadence

The tool uses publicly-available datasets. Suggested refresh schedule, runnable as cron jobs:

| Source | Frequency | Script |
|---|---|---|
| Glencore CAHRA list | Annual (Feb update cycle) | Manual edit to `country_indicators.csv` |
| Yale EPI | Every 2 years on release | `scripts/02_fetch_external_data.py --source epi` + manual download |
| World Bank indicators | Annual | `scripts/02_fetch_external_data.py --source worldbank` |
| WRI Aqueduct | Every 2–3 years on release | `scripts/01_process_aqueduct.py` |
| Global Tailings Portal | Quarterly | `scripts/02_fetch_external_data.py --source tailings` |
| USGS Critical Minerals List | Every 3 years | Manual edit to `commodity_producers.csv` |
| USGS MRDS | Annual | `scripts/05_fetch_usgs_mrds.py` |
| Global Energy Monitor | Semi-annual | `scripts/06_fetch_gem.py` |
| ISRIC SoilGrids | Every 2 years | `scripts/07_fetch_soilgrids.py` |
| INFORM Risk | Annual | `scripts/02_fetch_external_data.py --source inform` |
| USGS MCS producer rankings | Annual (January release) | Manual edit to `commodity_producers.csv` |

Assign one Responsible Sourcing team member (or an intern on rotation) to run the refresh scripts quarterly and raise a PR with the new CSVs.

### 2.6 Governance — who can change what

Document who has write access to:

- **Risk taxonomy** (`risks.csv`, `risk_process_matrix.csv`, `risk_supplier_types.csv`) → Responsible Sourcing lead
- **Country indicators** (`country_indicators.csv`) → data refresh rotation
- **Supplier data** (`glencore_suppliers.csv`) → Responsible Sourcing team only
- **Scoring weights** (`scoring_weights.csv`) → Responsible Sourcing lead after stakeholder sign-off
- **App code** (`app/`) → requires developer review

Standard Git branch protection on `main` with required PR review is the minimum control.

## 3. Day-to-day operation (Responsible Sourcing team)

After handover, the team's normal workflow is:

1. Open `data/processed/*.csv` files in Excel or Google Sheets
2. Edit values (add a country, adjust a risk definition, update a supplier)
3. Save back to CSV
4. Commit + push through Glencore's standard Git workflow (or via a BI-team member)
5. The hosted Streamlit app (or Power BI report) picks up the changes automatically on rebuild

Training: walk through `docs/HOW_TO_EDIT.md` with the team once. ~30 minutes.

## 4. Adding a new supplier assessment

This is the most common operational task. From `docs/HOW_TO_EDIT.md`:

1. Open `glencore_suppliers.csv` (or Glencore's counterparty DB if this has been migrated)
2. Add a row: name, commodity, country (ISO-3), process type, lat/lon, SCDD status
3. Save. The tool's Map tab now shows the supplier and Risk Dashboard includes them in the ranked output when their country/commodity is filtered.

## 5. Support contract expectations

Once handed over:

- **No ongoing support from NYU SPS team is required.** The tool is self-contained.
- **Methodology questions** → refer to `docs/METHODOLOGY.md` (every formula, weight, and normalization rule documented)
- **Data source questions** → refer to the Data Sources tab in the app (every URL cited)
- **Code changes** → Glencore IT team or a vendor of their choice

If an NYU author is available for an optional 1-hour handover call, that is a courtesy — not a dependency.

## 6. Decommissioning NYU-side footprint

After Glencore confirms their environment is running, the NYU team should:

- [ ] Delete `https://github.com/mnmarkovitz/glencore_enviro_risk_tool` (or keep as a personal archive but unlinked from any Glencore URL)
- [ ] Remove the Streamlit Cloud deployment from their personal account
- [ ] Delete any local tunnel processes (`localhost.run` etc.)
- [ ] Shut down any local copies of `glencore_suppliers.csv` containing real Glencore data
- [ ] Confirm no credentials (API tokens for IUCN, OAuth tokens for GitHub, etc.) were ever committed to the repo

## 7. One-page summary for Glencore IT leadership

> **What:** A Python Streamlit web app (~1,000 LOC) + 10 editable CSVs for assessing outward environmental risk across the Glencore metals and minerals supply chain. All scoring uses publicly-available datasets (Aqueduct, EPI, WHO, World Bank, IUCN, WDPA, USGS, GEM, ISRIC SoilGrids, Basel, INFORM). Aligned with the OECD DDG 5-step framework and mapped explicitly to Glencore's SCDD M&M procedure steps 2A–3.
>
> **Deploy:** One Docker container, ~200 MB image, no external services required. Deployable on any cloud or on-prem Linux.
>
> **Run:** Stateless — CSVs are the logic. Editable in Excel/Sheets. No database required.
>
> **Effort to maintain:** ~4 hours/quarter to refresh external datasets + optional interface with internal counterparty DB.
>
> **Dependencies to retire:** NYU-hosted GitHub repo, Streamlit Community Cloud deployment, NYU authors' personal credentials. All three can be cut within an hour after Glencore's instance is up.

## 8. Questions Glencore should answer before day 1

- **Target hosting:** Azure App Service / ECS / internal K8s / Power BI?
- **Access control:** public URL, Glencore SSO, or IP-allowlist?
- **Confidential data owner:** which team owns `glencore_suppliers.csv`?
- **Refresh ownership:** which Responsible Sourcing team member runs the fetch scripts?
- **Change management:** is a Git PR workflow OK, or should CSV edits flow through a non-technical UI (e.g., a SharePoint list that syncs to the CSV)?

These answers determine the shape of Glencore's final deployment but do not block receiving the tool.
