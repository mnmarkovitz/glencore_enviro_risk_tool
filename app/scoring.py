"""
Normalized environmental risk scoring engine.

Inputs: CSVs in ../data/processed/ (editable in Excel).
Outputs: For each (risk, country, process, commodity) tuple, a Likelihood (1-5),
Severity (1-5), and Overall (L * S, 1-25) score, each with the raw indicator that
produced it.

Methodology (summary; full version in docs/METHODOLOGY.md):

Likelihood = 0.4 * Process_Intrinsic_Risk + 0.6 * Country_Hazard_Score
Severity   = 0.5 * Ecological_Sensitivity + 0.5 * Regulatory_Strictness
Overall    = Likelihood * Severity

All indicators are normalized to 1-5 (5 = worst). Raw values are preserved in the
output so the user can audit every normalized score against its public source.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np

DATA = Path(__file__).parent.parent / "data" / "processed"


def _load():
    risks = pd.read_csv(DATA / "risks.csv")
    matrix = pd.read_csv(DATA / "risk_process_matrix.csv")
    countries = pd.read_csv(DATA / "country_indicators.csv")
    aqueduct = pd.read_csv(DATA / "aqueduct_country_scores.csv")
    producers = pd.read_csv(DATA / "commodity_producers.csv")
    noise = pd.read_csv(DATA / "noise_process_baseline.csv")
    weights = pd.read_csv(DATA / "scoring_weights.csv").set_index("parameter")["value"].to_dict()
    supplier_types = pd.read_csv(DATA / "supplier_types.csv")
    risk_supplier = pd.read_csv(DATA / "risk_supplier_types.csv").set_index("risk_id")["supplier_types"].to_dict()
    # Attach per-risk supplier type list back to risks df for convenience
    risks["likely_supplier_types"] = risks["risk_id"].map(risk_supplier).fillna("")

    # Merge SoilGrids vulnerability if present
    soil_path = DATA / "soilgrids_country.csv"
    if soil_path.exists():
        soil = pd.read_csv(soil_path)[
            ["iso3", "soil_ph_0_5cm", "soil_soc_g_per_kg", "soil_cec_cmol_per_kg",
             "soil_vulnerability_1_5"]
        ]
        countries = countries.merge(soil, on="iso3", how="left")
    else:
        countries["soil_vulnerability_1_5"] = np.nan
    # Merge aqueduct into country_indicators on iso3
    countries = countries.merge(
        aqueduct.rename(columns={"gid_0": "iso3"})[
            ["iso3", "bws_cat_0_4", "drr_cat_0_4", "rfr_cat_0_4"]
        ],
        on="iso3",
        how="left",
    )
    # Aqueduct uses -9999 for no-data; treat as NaN
    for col in ["bws_cat_0_4", "drr_cat_0_4", "rfr_cat_0_4"]:
        countries[col] = countries[col].replace(-9999, np.nan)
    return risks, matrix, countries, producers, noise, weights, supplier_types


# ---- normalization helpers ------------------------------------------------

def _quintile(series: pd.Series, higher_is_worse: bool = True) -> pd.Series:
    """Map a numeric series to 1-5 by global quintiles (worst -> 5)."""
    s = series.dropna()
    if s.empty:
        return pd.Series(np.nan, index=series.index)
    try:
        q = pd.qcut(s, 5, labels=[1, 2, 3, 4, 5], duplicates="drop")
    except ValueError:
        # fallback when many duplicates
        q = pd.cut(s, 5, labels=[1, 2, 3, 4, 5])
    out = pd.Series(np.nan, index=series.index)
    out.loc[q.index] = q.astype(float)
    if not higher_is_worse:
        out = 6 - out
    return out


def _aq_to_1_5(cat: float) -> float:
    """Aqueduct category 0..4 -> 1..5."""
    if pd.isna(cat):
        return np.nan
    return float(cat) + 1


def _pm25_to_1_5(ugm3: float) -> float:
    """WHO AAQ PM2.5 annual mean -> 1..5 using WHO IT-1..IT-4 thresholds."""
    if pd.isna(ugm3):
        return np.nan
    for threshold, score in [(10, 1), (25, 2), (35, 3), (50, 4)]:
        if ugm3 < threshold:
            return score
    return 5


def _wgi_to_strictness(wgi: float) -> float:
    """WGI regulatory quality in [-2.5, 2.5] -> strictness 1..5 (higher = stricter)."""
    if pd.isna(wgi):
        return np.nan
    return max(1.0, min(5.0, (wgi + 2.5) / 5.0 * 4.0 + 1.0))


def _eco_sensitivity(row: pd.Series) -> float:
    """Blend EPI Ecosystem Vitality (inverted) + protected area coverage."""
    epi = row.get("epi_ecosystem_vitality")
    wdpa = row.get("wdpa_protected_pct")
    parts = []
    if pd.notna(epi):
        parts.append((100 - epi) / 20.0 + 1)  # 0 -> 6, 100 -> 1
    if pd.notna(wdpa):
        parts.append(max(1, min(5, 6 - wdpa / 10.0)))  # >50% -> 1, 0% -> 6
    if not parts:
        return np.nan
    return float(np.mean(parts))


def _regulatory_strictness(row: pd.Series) -> float:
    rq = row.get("wb_wgi_regulatory_quality")
    epi = row.get("epi_overall_2024")
    parts = []
    if pd.notna(rq):
        parts.append(_wgi_to_strictness(rq))
    if pd.notna(epi):
        parts.append(max(1, min(5, epi / 25.0 + 1)))  # 0 -> 1, 100 -> 5
    if not parts:
        return np.nan
    return float(np.mean(parts))


# ---- per-risk country hazard mapping --------------------------------------

def _country_hazard(risk_id: str, row: pd.Series,
                     quantile_maps: dict) -> tuple[Optional[float], Optional[float], str]:
    """Return (raw_value, normalized_1_5, source_note) for the country hazard driving
    the Likelihood of this risk.
    """
    if risk_id in ("water_depletion",):
        raw = row.get("bws_cat_0_4")
        return raw, _aq_to_1_5(raw), "Aqueduct BWS"
    if risk_id == "water_pollution":
        # Proxy: Aqueduct BWS (stress intensifies pollution concentration) combined with
        # EPI Waste Management (inverted). True Aqueduct UCW/CEP require API fetch.
        bws = _aq_to_1_5(row.get("bws_cat_0_4"))
        waste = quantile_maps["epi_waste"].get(row.name, np.nan)
        parts = [x for x in [bws, waste] if not pd.isna(x)]
        norm = float(np.mean(parts)) if parts else np.nan
        return row.get("bws_cat_0_4"), norm, "Aqueduct BWS + EPI Waste (proxy for UCW/CEP)"
    if risk_id == "tailings":
        tsf = row.get("tsf_count")
        sev_flag = row.get("tsf_max_very_high_or_extreme")
        if pd.isna(tsf):
            return np.nan, np.nan, "Global Tailings Portal"
        base = quantile_maps["tsf_count"].get(row.name, np.nan)
        # bump by consequence flag
        bump = 0.5 if sev_flag == 1 else (1.0 if (pd.notna(sev_flag) and sev_flag >= 2) else 0)
        return tsf, (None if pd.isna(base) else min(5.0, float(base) + bump)), "Global Tailings Portal TSF count"
    if risk_id == "waste_pollution":
        raw = row.get("epi_waste_management")
        return raw, quantile_maps["epi_waste"].get(row.name, np.nan), "Yale EPI Waste Management (inverted)"
    if risk_id == "biodiversity_species":
        raw = row.get("iucn_threatened_species")
        return raw, quantile_maps["iucn"].get(row.name, np.nan), "IUCN Red List threatened species count"
    if risk_id == "biodiversity_ecosystems":
        raw = row.get("gfw_tree_cover_loss_pct_2023")
        return raw, quantile_maps["gfw"].get(row.name, np.nan), "Global Forest Watch tree cover loss %"
    if risk_id == "noise_pollution":
        return np.nan, np.nan, "NIOSH process baseline (country-invariant)"
    if risk_id == "air_pollution":
        raw = row.get("who_pm25_annual_ugm3")
        return raw, _pm25_to_1_5(raw), "WHO AAQ PM2.5 annual mean"
    if risk_id == "soil_pollution":
        # Blend two datasets:
        #   (a) Yale EPI Heavy Metals (inverted) — historical/industrial contamination exposure
        #   (b) ISRIC SoilGrids-derived soil_vulnerability (pH + SOC + CEC) — how easily
        #       contamination mobilizes in local soils once released
        epi_norm = quantile_maps["epi_heavy"].get(row.name, np.nan)
        soil_vuln = row.get("soil_vulnerability_1_5")
        parts = [x for x in [epi_norm, soil_vuln] if not pd.isna(x)]
        if not parts:
            return np.nan, np.nan, "EPI Heavy Metals + ISRIC SoilGrids (no data)"
        norm = float(np.mean(parts))
        # raw: prefer soil_vulnerability numeric (so user sees a concrete soil metric)
        raw = soil_vuln if not pd.isna(soil_vuln) else row.get("epi_heavy_metals")
        src = ("ISRIC SoilGrids (pH+SOC+CEC vulnerability) + Yale EPI Heavy Metals (blend)"
               if (not pd.isna(soil_vuln) and not pd.isna(epi_norm))
               else ("ISRIC SoilGrids soil vulnerability" if not pd.isna(soil_vuln)
                     else "Yale EPI Heavy Metals (inverted)"))
        return raw, norm, src
    if risk_id == "ghg_emissions":
        raw = row.get("wb_co2_t_per_capita")
        return raw, quantile_maps["co2"].get(row.name, np.nan), "World Bank CO2 per capita"
    if risk_id == "health_risks":
        raw = row.get("who_pm25_annual_ugm3")
        return raw, _pm25_to_1_5(raw), "WHO AAQ PM2.5 (health proxy)"
    if risk_id == "displacement":
        raw = row.get("wb_wgi_gov_effectiveness")
        if pd.isna(raw):
            return np.nan, np.nan, "WGI Gov. Effectiveness (inverted)"
        return raw, max(1, min(5, (2.5 - raw) / 5.0 * 4.0 + 1.0)), "WGI Gov. Effectiveness (inverted)"
    if risk_id == "physical_instability":
        raw = row.get("inform_risk_2024")
        return raw, quantile_maps["inform"].get(row.name, np.nan), "INFORM Risk Index"
    if risk_id == "cultural_heritage":
        raw = row.get("unesco_heritage_in_danger")
        if pd.isna(raw):
            return np.nan, np.nan, "UNESCO Heritage Sites in Danger"
        return raw, max(1.0, min(5.0, 1.0 + float(raw))), "UNESCO Heritage Sites in Danger"
    if risk_id == "improper_waste_disposal":
        raw = row.get("epi_waste_management")
        return raw, quantile_maps["epi_waste"].get(row.name, np.nan), "Yale EPI Waste Management (inverted)"
    return np.nan, np.nan, "no source mapped"


# ---- main scoring ---------------------------------------------------------

@dataclass
class RiskScore:
    risk_id: str
    risk_type: str
    commodity: str
    country: str
    iso3: str
    cahra_flag: str
    cahra_regions: str
    process: str
    applies: str
    process_intrinsic_1_5: float
    country_hazard_raw: Optional[float]
    country_hazard_norm_1_5: Optional[float]
    country_hazard_source: str
    likelihood_1_5: Optional[float]
    ecological_sensitivity_1_5: Optional[float]
    regulatory_strictness_1_5: Optional[float]
    severity_1_5: Optional[float]
    overall_1_25: Optional[float]
    risk_bucket: str
    likely_supplier_types: str
    likelihood_dataset: str
    severity_dataset: str
    definition: str


BUCKETS = [(4, "Low"), (9, "Moderate"), (14, "High"), (25, "Critical")]

def _bucket(overall: Optional[float]) -> str:
    if overall is None or pd.isna(overall):
        return "No data"
    for upper, label in BUCKETS:
        if overall <= upper:
            return label
    return "Critical"


def compute(
    commodities: Optional[list[str]] = None,
    countries: Optional[list[str]] = None,
    processes: Optional[list[str]] = None,
    risk_ids: Optional[list[str]] = None,
) -> pd.DataFrame:
    risks, matrix, countries_df, producers, _, W, _st = _load()
    LPW = W.get("likelihood_process_weight", 0.4)
    LCW = W.get("likelihood_country_weight", 0.6)
    SEW = W.get("severity_eco_weight", 0.5)
    SRW = W.get("severity_regulatory_weight", 0.5)
    NA_CAP = W.get("non_applicable_likelihood_cap", 1.5)
    # pre-compute country-level quintile maps for global normalization
    qm = {
        "epi_waste": _quintile(countries_df["epi_waste_management"], higher_is_worse=False),
        "epi_heavy": _quintile(countries_df["epi_heavy_metals"], higher_is_worse=False),
        "tsf_count": _quintile(countries_df["tsf_count"], higher_is_worse=True),
        "iucn": _quintile(countries_df["iucn_threatened_species"], higher_is_worse=True),
        "gfw": _quintile(countries_df["gfw_tree_cover_loss_pct_2023"], higher_is_worse=True),
        "co2": _quintile(countries_df["wb_co2_t_per_capita"], higher_is_worse=True),
        "inform": _quintile(countries_df["inform_risk_2024"], higher_is_worse=True),
    }
    # use index alignment: quintile maps are dicts keyed by DataFrame index
    quintile_maps = {k: dict(zip(v.index, v.values)) for k, v in qm.items()}

    # filter universe
    producers_f = producers.copy()
    if commodities:
        producers_f = producers_f[producers_f["commodity"].isin(commodities)]
    if countries:
        producers_f = producers_f[producers_f["country"].isin(countries)]
    # commodity-country pairs to score
    pairs = producers_f[["commodity", "country", "iso3", "producer_rank", "share_of_global_pct"]].drop_duplicates()
    if countries and not commodities:
        # "any country" mode: cross with all commodities
        pass

    risks_f = risks.copy()
    if risk_ids:
        risks_f = risks_f[risks_f["risk_id"].isin(risk_ids)]
    matrix_f = matrix.copy()
    if processes:
        matrix_f = matrix_f[matrix_f["process"].isin(processes)]

    out = []
    country_by_iso = countries_df.set_index("iso3")
    for _, pr in pairs.iterrows():
        iso3 = pr["iso3"]
        if iso3 not in country_by_iso.index:
            continue
        country_row = country_by_iso.loc[iso3]
        # country_row might be a DataFrame if duplicates; keep first
        if isinstance(country_row, pd.DataFrame):
            country_row = country_row.iloc[0]
        eco = _eco_sensitivity(country_row)
        reg = _regulatory_strictness(country_row)
        for _, rk in risks_f.iterrows():
            r_id = rk["risk_id"]
            for _, mt in matrix_f[matrix_f["risk_id"] == r_id].iterrows():
                proc = mt["process"]
                applies = mt["applies"]
                pir = float(mt["intrinsic_intensity_1_5"])
                # resolve country-row index for quintile lookup
                country_idx = countries_df.index[countries_df["iso3"] == iso3][0]
                # Inject quintile lookup by index
                country_row_idx = country_row.copy()
                country_row_idx.name = country_idx
                raw, norm, src = _country_hazard(r_id, country_row_idx, quintile_maps)
                if pd.isna(norm):
                    likelihood = pir  # fallback: process-only likelihood
                else:
                    likelihood = LPW * pir + LCW * norm
                if applies == "N":
                    likelihood = min(likelihood, NA_CAP)
                severity = (
                    SEW * eco + SRW * reg if not (pd.isna(eco) or pd.isna(reg))
                    else (eco if not pd.isna(eco) else reg)
                )
                overall = (
                    likelihood * severity if (likelihood is not None and not pd.isna(likelihood) and not pd.isna(severity))
                    else np.nan
                )
                out.append(RiskScore(
                    risk_id=r_id,
                    risk_type=rk["risk_type"],
                    commodity=pr["commodity"],
                    country=pr["country"],
                    iso3=iso3,
                    cahra_flag=str(country_row.get("cahra_flag", "N")),
                    cahra_regions=str(country_row.get("cahra_regions", "") or ""),
                    process=proc,
                    applies=applies,
                    process_intrinsic_1_5=pir,
                    country_hazard_raw=None if pd.isna(raw) else float(raw),
                    country_hazard_norm_1_5=None if pd.isna(norm) else float(norm),
                    country_hazard_source=src,
                    likelihood_1_5=None if pd.isna(likelihood) else round(float(likelihood), 2),
                    ecological_sensitivity_1_5=None if pd.isna(eco) else round(float(eco), 2),
                    regulatory_strictness_1_5=None if pd.isna(reg) else round(float(reg), 2),
                    severity_1_5=None if pd.isna(severity) else round(float(severity), 2),
                    overall_1_25=None if pd.isna(overall) else round(float(overall), 2),
                    risk_bucket=_bucket(overall),
                    likely_supplier_types=str(rk.get("likely_supplier_types", "") or ""),
                    likelihood_dataset=rk["likelihood_dataset"],
                    severity_dataset=rk["severity_dataset"],
                    definition=rk["definition"],
                ).__dict__)
    # Always return a well-formed DataFrame — even when `out` is empty, include
    # every expected column so downstream code doesn't KeyError on empty filters.
    if out:
        return pd.DataFrame(out)
    expected_cols = list(RiskScore.__dataclass_fields__.keys())
    return pd.DataFrame(columns=expected_cols)


if __name__ == "__main__":
    df = compute(commodities=["Cobalt"])
    print(df.head(20).to_string())
    print(f"\nRows: {len(df)}")
