# Scoring methodology

## Purpose and scope

This tool identifies **outward environmental impacts** — harms that operations along a mining / trading supply chain (mining, refining, smelting, recycling, marketing) could cause to the natural environment, and that could trigger **penalties, fines, enforcement action, or reputational damage** on the operator.

The tool does **not** assess climate change risks *to* the company (physical or transition risk), which is the reverse direction of materiality.

## Why a published-data-only scoring system

We deliberately avoid analyst-assigned Likelihood and Severity scores because:

- They are not reproducible.
- They embed individual biases that vary across teams and review cycles.
- They make it hard to defend a conclusion to an auditor or regulator.

Every number in this tool is traceable to a named public dataset with a URL and a clear normalization rule. Users see both the **raw external indicator** and the **normalized 1–5 interpretation** side by side.

## Core formulas

All scores are on a **1–5** scale where **5 = worst** (highest risk / highest impact / highest penalty exposure).

```
Likelihood = w_P × Process_Intrinsic_Risk  +  w_C × Country_Hazard_Score      (1–5)
Severity   = w_E × Ecological_Sensitivity  +  w_R × Regulatory_Strictness     (1–5)
Overall    = Likelihood × Severity                                              (1–25)
```

Default weights (editable in `scoring_weights.csv`):

| Weight | Value | Rationale |
|---|---|---|
| `w_P` (process) | 0.4 | Process intrinsically drives risk (e.g., tailings are a mining-only risk). |
| `w_C` (country) | 0.6 | Country-level hazard determines where that process risk actually materializes. |
| `w_E` (ecology) | 0.5 | Half of severity is ecological consequence. |
| `w_R` (regulatory) | 0.5 | Half of severity is penalty/reputational consequence. |

### Likelihood components

**Process Intrinsic Risk (1–5)** — from `risk_process_matrix.csv`. Based on ENCORE-style materiality ratings and IFC EHS Guidelines for mining, smelting, and refining. Captures differences such as:
- Tailings: Mining 5 / Refining 2 / Marketing 1
- SO₂ air pollution: Smelting 5 / Mining 4 / Marketing 2
- Biodiversity habitat loss: Mining 5 / Recycling 2

**Country Hazard Score (1–5)** — derived per-risk from the specific public dataset mapped in `risks.csv`:

| Risk | Likelihood source | Normalization |
|---|---|---|
| Water depletion | WRI Aqueduct BWS (0–4) | category + 1 |
| Water pollution | Aqueduct BWS + EPI Waste Management | mean of two normalized values |
| Tailings | GTP TSF count + consequence flag | quintile + bump for VH/Extreme |
| Waste pollution | EPI Waste Management (inverted) | global quintiles |
| Biodiversity species | IUCN threatened species count | global quintiles |
| Biodiversity ecosystems | GFW tree cover loss % | global quintiles |
| Air pollution | WHO PM2.5 annual mean | WHO IT thresholds (<10→1, <25→2, <35→3, <50→4, ≥50→5) |
| Soil pollution | ISRIC SoilGrids pH + SOC + CEC → vulnerability 1–5, blended with EPI Heavy Metals | formula below + global quintiles |
| GHG emissions | World Bank CO₂ per capita | global quintiles |
| Health risks | WHO PM2.5 (proxy) | WHO IT thresholds |
| Displacement | WGI Gov. Effectiveness (inverted) | linear rescale |
| Physical instability | INFORM Risk Index | global quintiles |
| Cultural heritage | UNESCO sites-in-danger count | 1 + count (capped at 5) |
| Improper waste disposal | EPI Waste Management (inverted) | global quintiles |
| Noise pollution | (none – process-only) | country-invariant |

### Severity components

**Ecological Sensitivity (1–5)** — mean of:
- Yale EPI 2024 *Ecosystem Vitality* (inverted: `(100 − score)/20 + 1`)
- Protected Planet WDPA *% terrestrial area protected* (inverted: `max(1, 6 − pct/10)`)

**Regulatory Strictness (1–5)** — mean of:
- World Bank WGI *Regulatory Quality* (−2.5..2.5 → 1..5 linear)
- Yale EPI 2024 overall score (0..100 → 1..5 linear; proxy for enforcement capacity)

> **Design choice:** we treat *stronger regulatory regimes as producing higher Severity*, because the tool's purpose is to capture exposure to **penalties, fines, and enforcement action**. A rigorously enforced regime penalizes incidents harder. If your use case is pure ecological damage (not penalty exposure), edit `scoring_weights.csv` to lower `severity_regulatory_weight`.

## Overall score and buckets

```
Overall = Likelihood × Severity    (range 1–25)
```

| Range | Bucket |
|---|---|
| 1–4 | Low |
| 5–9 | Moderate |
| 10–14 | High |
| 15–25 | Critical |

Boundaries are in `scoring_weights.csv` and editable.

## Soil vulnerability — SoilGrids-derived

For the **soil_pollution** risk specifically, the country hazard score blends two datasets:

1. **Yale EPI Heavy Metals** (inverted, quintile-normalized) — captures country-level heavy-metal exposure history and industrial pollution burden.
2. **ISRIC SoilGrids 2.0** — a global 250 m soil-property grid. We sample topsoil (0–5 cm) pH, soil organic carbon (SOC), and cation exchange capacity (CEC) and compute:

```
vuln_pH   = clip( |pH − 7| × 1.3 + 1 , 1, 5 )     # neutral pH = least heavy-metal mobility
vuln_SOC  = 5 if SOC<10 g/kg; 4 if <20; 3 if <30; 2 if <50; 1 if ≥50
vuln_CEC  = 5 if CEC<10 cmol/kg; 4 if <15; 3 if <25; 2 if <35; 1 if ≥35

soil_vulnerability_1_5 = mean(vuln_pH, vuln_SOC, vuln_CEC)
```

**Why**: whether a spill or tailings seepage actually mobilizes heavy metals depends on the native soil. Acidic soils (low pH) + low organic carbon + low CEC = higher heavy-metal mobility and less natural buffering. Tropical acidic Oxisols (DRC, Madagascar, Indonesia) score higher vulnerability than temperate loams (Germany, Argentina, USA) or calcareous alkaline soils (Saudi Arabia, Kazakhstan).

Final country hazard for soil_pollution = mean of (normalized EPI Heavy Metals) and (SoilGrids vulnerability). When only one is available, that one is used alone.

## Non-applicable combinations

When `risk_process_matrix.csv` marks a risk × process cell as `applies = N` (e.g., tailings for Marketing), Likelihood is capped at **1.5** so the combination remains visible for auditability but is clearly deprioritized in the ranking.

## Missing data

- If a country-level indicator is missing, Likelihood falls back on `Process_Intrinsic_Risk` alone (weighted fully).
- If both Ecological Sensitivity and Regulatory Strictness are missing, Severity is `NaN` and the combination is marked **No data**.

## Global normalization notes

- **Aqueduct categorical indicators (bws, drr, rfr)** are already 0–4 — we simply add 1.
- **PM2.5** uses WHO Interim Target thresholds, not quintiles — this produces an absolute, health-anchored score rather than a relative ranking.
- **World Bank WGI** is linearly rescaled from −2.5..2.5 to 1..5.
- **Counts** (IUCN species, TSFs) and **0–100 scores** (EPI sub-indices) use **global quintiles** of the current `country_indicators.csv` sample — so expanding coverage to more countries will shift thresholds slightly.

## Source datasets

| Dataset | Covers | Link |
|---|---|---|
| WRI Aqueduct 4.0 | Water stress, drought, flood (bws, drr, rfr) | https://www.wri.org/applications/aqueduct |
| Yale EPI 2024 | Ecosystem Vitality, Waste Management, Heavy Metals, Air Quality, overall | https://epi.yale.edu |
| Global Tailings Portal | TSF count + consequence class per country | https://tailing.grida.no |
| IUCN Red List API | Threatened species counts per country | https://apiv3.iucnredlist.org |
| Protected Planet / WDPA | % national terrestrial area protected | https://www.protectedplanet.net |
| Global Forest Watch | Tree cover loss % per country per year | https://www.globalforestwatch.org |
| WHO Ambient Air Quality DB | PM2.5 annual mean | https://www.who.int/data/gho/data/themes/air-pollution |
| EC JRC EDGAR | SO₂, NOx national emissions | https://edgar.jrc.ec.europa.eu |
| World Bank WGI | Regulatory Quality, Government Effectiveness | https://www.worldbank.org/en/publication/worldwide-governance-indicators |
| World Bank Open Data | CO₂ per capita | https://data.worldbank.org |
| INFORM Risk Index (EC JRC) | Natural hazard exposure | https://drmkc.jrc.ec.europa.eu/inform-index |
| UNESCO World Heritage | Heritage sites & sites in danger | https://whc.unesco.org |
| UNEP Basel Convention | National hazardous waste generation | http://www.basel.int |
| NIOSH Mining Noise | dBA by mining activity (static) | https://www.cdc.gov/niosh/mining/topics/Noise.html |
| IFC EHS Guidelines | Base Metal Smelting/Refining sector noise + impact profiles | https://www.ifc.org/ehsguidelines |
| USGS Mineral Commodity Summaries | Top producers per commodity | https://pubs.usgs.gov/periodicals/mcs |

## Known limitations

- **Aqueduct UCW (Untreated Connected Wastewater) and CEP (Coastal Eutrophication Potential)** are not in the bundled ranking file. We proxy Water Pollution using BWS + EPI Waste until the Aqueduct API fetch is wired up (`scripts/02_fetch_external_data.py --source aqueduct_api`).
- **Noise pollution** has no global country-level dataset; we show only the process-baseline (NIOSH) and deliberately do not invent a score.
- **Seed country coverage** is ~43 top producers. Add countries by appending rows to `country_indicators.csv`.
- **Commodity coverage** matches USGS MCS 2024. Copper and oil/gas share figures are approximate and rounded.
