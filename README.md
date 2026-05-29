# Environmental Risk Identification & Assessment Tool

> Built for the Glencore Group Responsible Sourcing team
> in partnership with the **NYU SPS Center for Global Affairs Consulting Practicum**.

A risk-based desktop tool that scores environmental risks across Glencore's metals & minerals supply chain. Every score traces back to a public dataset; nothing is analyst opinion.

---

## What's in this repository

| Deliverable | Open it |
|---|---|
| 🌐 **Live tool** (filters, maps, heatmaps, drill-down) | [Streamlit app — public URL](https://nyu-cp-enviro-risk-tool.streamlit.app/) |
| 📊 **Excel companion** (15-sheet color-coded workbook, no setup) | [Quick_Reference.xlsx](Quick_Reference.xlsx) |
| 📘 **Handover document** (how built, how to integrate, how to update) | [docs/OVERVIEW_AND_HANDOVER.md](docs/OVERVIEW_AND_HANDOVER.md) |

---

## What the tool does

Pick any combination of **commodity, country, mining process** (Mining / Refining / Smelting / Recycling / Marketing) and **risk type**. The tool returns:

- A ranked table of environmental risks scored 1–25 (Likelihood × Severity), color-coded Low / Moderate / High / Critical
- A 5×5 Likelihood × Severity heatmap
- A satellite map of producer countries, Glencore-owned assets, and (optional) suppliers
- A drill-down panel showing the raw indicator value and the public-source URL behind every score
- Pre-loaded SAQ KPIs per risk that the Responsible Sourcing analyst can drop straight into Glencore's existing Step 2B questionnaire

---

## Frameworks aligned to

- **OECD** Due Diligence Guidance for Responsible Supply Chains of Minerals (3rd ed.) and **OECD Handbook on Environmental Due Diligence in Mineral Supply Chains** (2023)
- **Glencore SCDD Procedure — Metals & Minerals** (2024) — automates Step 2A + supports Steps 2B–3
- **RMI Supply Chain Due Diligence Plus Module** (April 2025)
- **UNDP** Human Rights Due Diligence and the Environment: A Practical Tool for Business
- Glencore's existing **saliency-based risk framework**

---

## Public datasets behind the scoring

WRI Aqueduct · Yale EPI 2024 · WHO Ambient Air Quality DB · IUCN Red List · UNEP-WCMC Protected Planet · Global Forest Watch · Global Tailings Portal · USGS Mineral Commodity Summaries · USGS MRDS · USGS Critical Minerals Atlas · Global Energy Monitor · ISRIC SoilGrids · World Bank WGI · **NRGI Resource Governance Index** · **EJ Atlas (Environmental Justice Atlas)** · INFORM Risk Index · UNESCO World Heritage · Glencore CAHRA List 2025

Full URLs and licences are listed in the **Data Sources** sheet of the Excel file and in `docs/OVERVIEW_AND_HANDOVER.md` Section 4.

---

## Run locally (technical, optional)

```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

Opens at http://localhost:8501.

For Docker / Glencore-hosted deploy: see [docs/OVERVIEW_AND_HANDOVER.md Section 5](docs/OVERVIEW_AND_HANDOVER.md).

---

## Project documentation

- **[docs/OVERVIEW_AND_HANDOVER.md](docs/OVERVIEW_AND_HANDOVER.md)** — primary handover document. How the tool was built, how to integrate into Glencore's systems, how to update the data, full file map, and a plain-English step-by-step walkthrough.
- **[docs/METHODOLOGY.md](docs/METHODOLOGY.md)** — exact scoring formulas, normalization rules, weight rationale.
- **[docs/USER_GUIDE.md](docs/USER_GUIDE.md)** — analyst-facing walkthrough; mirrored inside the live tool's "📖 User Guide" tab.
