# How to edit the tool in Excel / Google Sheets

All of the tool's logic lives in six CSV files under `data/processed/`. Edit them in Excel, Google Sheets, or a text editor — save — refresh the Streamlit tab. **No Python needed.**

## The six files you can edit

### 1. `risks.csv` — the catalog of risks

One row per environmental risk (15 rows shipped: 8 priority + 7 secondary).

| Column | Edit to... |
|---|---|
| `risk_id` | ID used internally — **don't rename** if you already have data referencing it |
| `risk_type` | Human-readable name shown in the UI |
| `category` | `Priority` or `Secondary` |
| `definition` | The tooltip / drill-down description |
| `key_kpis` | Measurable metrics (free text, shown in drill-down) |
| `likelihood_dataset` / `_indicator` / `_url` | The public dataset used to derive Likelihood |
| `severity_dataset` / `_indicator` / `_url` | The public dataset used to derive Severity |

**To add a new risk**: append a new row with a unique `risk_id`, then add matching rows in `risk_process_matrix.csv` for every process × this risk.

### 2. `risk_process_matrix.csv` — which processes each risk applies to

One row per `(risk_id, process)` pair. Intensity 1–5.

| Column | Edit to... |
|---|---|
| `risk_id` | Must match a `risks.csv` entry |
| `process` | One of Mining / Refining / Smelting / Recycling / Marketing |
| `applies` | `Y` or `N` — if `N`, Likelihood is capped at 1.5 |
| `intrinsic_intensity_1_5` | How intensely this process drives this risk (1–5) |
| `rationale` | Free text, shown on hover in future versions |

### 3. `commodity_producers.csv` — who produces what

One row per `(commodity, country)` pair, with producer rank.

| Column | Edit to... |
|---|---|
| `commodity` | Add new commodities by inserting rows here |
| `country` / `iso3` | Must match `country_indicators.csv` iso3 |
| `producer_rank` | 1 = largest; used to surface top producers first in the dropdown |
| `share_of_global_pct` | Informational; USGS MCS values |

### 4. `country_indicators.csv` — country-level raw indicators

The big table. One row per country.

| Column | Source |
|---|---|
| `epi_overall_2024`, `epi_ecosystem_vitality`, etc. | Yale EPI 2024 (0–100, higher = better) |
| `who_pm25_annual_ugm3` | WHO Ambient Air Quality DB |
| `wb_co2_t_per_capita` | World Bank |
| `iucn_threatened_species` | IUCN Red List count |
| `wdpa_protected_pct` | Protected Planet |
| `tsf_count`, `tsf_max_very_high_or_extreme` | Global Tailings Portal |
| `wb_wgi_gov_effectiveness`, `wb_wgi_regulatory_quality` | World Bank WGI (−2.5..2.5) |
| `gfw_tree_cover_loss_pct_2023` | Global Forest Watch |
| `inform_risk_2024` | INFORM Risk Index |
| `unesco_heritage_sites`, `unesco_heritage_in_danger` | UNESCO |
| `basel_hazwaste_kt_per_yr` | Basel Convention |

**To add a country**: append a row with the iso3 code and any values you have. Blank cells are OK — the scoring engine falls back on process intensity.

### 5. `scoring_weights.csv` — tune the formulas

| Parameter | Default | Effect |
|---|---|---|
| `likelihood_process_weight` | 0.4 | Raise this if you think process matters more than country context |
| `likelihood_country_weight` | 0.6 | Must sum to 1 with the above |
| `severity_eco_weight` | 0.5 | Raise this to emphasize ecological damage |
| `severity_regulatory_weight` | 0.5 | Raise this to emphasize penalty/fine exposure in strict regimes |
| `bucket_low_max`, `bucket_moderate_max`, etc. | 4 / 9 / 14 / 25 | Shift the Low/Moderate/High/Critical cutoffs |

### 6. `noise_process_baseline.csv` — NIOSH dBA by activity

Editable if you find updated NIOSH or IFC values.

## Typical edits

**"Our cobalt assessment needs to include Zambia"**  
→ Add a row in `commodity_producers.csv` (Cobalt, Zambia, ZMB, rank, %). Zambia is already in `country_indicators.csv` so it'll show up immediately.

**"We want to emphasize ecological damage over penalty exposure"**  
→ Edit `scoring_weights.csv`: `severity_eco_weight` 0.7, `severity_regulatory_weight` 0.3.

**"The tailings cell for Smelting should be 3, not 2"**  
→ Edit `risk_process_matrix.csv`, find the `(tailings, Smelting)` row, change intensity.

**"We want a new risk: mercury from artisanal refining"**  
→ Add a row in `risks.csv` with a new `risk_id`. Add five rows (one per process) in `risk_process_matrix.csv`. Assign a dataset + indicator for Likelihood (suggest UNEP Global Mercury Assessment).

## After editing

- **Streamlit app running?** Press `R` in the browser or `Ctrl-C` and re-run.
- **Something broken?** Check the terminal for Python traceback — usually a typo in a column name or a country whose iso3 doesn't match.
