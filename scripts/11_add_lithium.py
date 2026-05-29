"""
Add Lithium to the analysis:
  1. Append lithium producer rows to commodity_producers.csv (USGS MCS 2024).
  2. Add Portugal (a top-10 lithium producer) to country_indicators.csv,
     country_centroids.csv, and soilgrids_country.csv (seed values).
Lithium is on the USGS 2022 Critical Minerals List -> critical_mineral = Y.
"""
import pandas as pd
from pathlib import Path

PROC = Path(__file__).parent.parent / "data" / "processed"
CRIT_URL = "https://www.usgs.gov/news/national-news-release/us-geological-survey-releases-2022-list-critical-minerals"

# --- 1. Lithium producers (USGS MCS 2024 mine-production shares) ---
LITHIUM = [
    ("Australia", "AUS", 1, 52.0), ("Chile", "CHL", 2, 25.0),
    ("China", "CHN", 3, 13.0), ("Argentina", "ARG", 4, 5.0),
    ("Brazil", "BRA", 5, 2.0), ("Zimbabwe", "ZWE", 6, 2.0),
    ("Portugal", "PRT", 7, 1.0), ("Canada", "CAN", 8, 0.8),
    ("United States", "USA", 9, 0.5),
]


def add_producers():
    prod = pd.read_csv(PROC / "commodity_producers.csv")
    if "Lithium" in set(prod.commodity):
        print("Lithium already present; skipping producers.")
        return
    rows = [dict(commodity="Lithium", country=c, iso3=i, producer_rank=r,
                 share_of_global_pct=s, source="USGS MCS 2024",
                 critical_mineral="Y", critical_source=f"USGS 2022 Critical Minerals List ({CRIT_URL})")
            for c, i, r, s in LITHIUM]
    prod = pd.concat([prod, pd.DataFrame(rows)], ignore_index=True)
    prod.to_csv(PROC / "commodity_producers.csv", index=False)
    print(f"Added {len(rows)} lithium producer rows.")


def add_portugal():
    ci = pd.read_csv(PROC / "country_indicators.csv")
    if "PRT" not in set(ci.iso3):
        prt = {
            "iso3": "PRT", "country": "Portugal",
            "epi_overall_2024": 62.0, "epi_ecosystem_vitality": 58.0,
            "epi_biodiversity_habitat": 60.0, "epi_air_quality": 70.0,
            "epi_waste_management": 65.0, "epi_heavy_metals": 68.0,
            "who_pm25_annual_ugm3": 9.5, "wb_co2_t_per_capita": 3.9,
            "gfw_tree_cover_loss_pct_2023": 0.30, "iucn_threatened_species": 90,
            "wdpa_protected_pct": 22.0, "tsf_count": 5, "tsf_max_very_high_or_extreme": 0,
            "wb_wgi_gov_effectiveness": 1.05, "wb_wgi_regulatory_quality": 0.95,
            "unesco_heritage_sites": 17, "unesco_heritage_in_danger": 0,
            "inform_risk_2024": 2.0, "basel_hazwaste_kt_per_yr": None,
            "source_note": "Seed values (EPI/WHO/WB). Refresh via scripts/02_fetch_external_data.py",
            "cahra_flag": "N", "cahra_regions": "",
            "nrgi_rgi_score_0_100": None, "ej_atlas_conflict_count": 15,
        }
        ci = pd.concat([ci, pd.DataFrame([prt])], ignore_index=True).sort_values("country")
        ci.to_csv(PROC / "country_indicators.csv", index=False)
        print("Added Portugal to country_indicators.csv")

    cen = pd.read_csv(PROC / "country_centroids.csv")
    if "PRT" not in set(cen.iso3):
        cen = pd.concat([cen, pd.DataFrame([{"iso3": "PRT", "lat": 39.40, "lon": -8.22}])],
                        ignore_index=True)
        cen.to_csv(PROC / "country_centroids.csv", index=False)
        print("Added Portugal to country_centroids.csv")

    soil = pd.read_csv(PROC / "soilgrids_country.csv")
    if "PRT" not in set(soil.iso3):
        # Mediterranean soils: slightly acidic, moderate SOC/CEC
        ph, socv, cec = 5.8, 20, 15
        v_ph = max(1.0, min(5.0, abs(ph - 7) * 1.3 + 1))
        v_soc = 3.0 if socv >= 20 else 4.0
        v_cec = 3.0 if cec >= 15 else 4.0
        vuln = round((v_ph + v_soc + v_cec) / 3, 2)
        soil = pd.concat([soil, pd.DataFrame([{
            "iso3": "PRT", "country": "Portugal", "soil_ph_0_5cm": ph,
            "soil_soc_g_per_kg": socv, "soil_cec_cmol_per_kg": cec,
            "soil_vulnerability_1_5": vuln,
            "source_note": "Seed estimate (Mediterranean soils). Refresh via scripts/07_fetch_soilgrids.py.",
        }])], ignore_index=True).sort_values("country")
        soil.to_csv(PROC / "soilgrids_country.csv", index=False)
        print(f"Added Portugal to soilgrids_country.csv (vulnerability {vuln})")


if __name__ == "__main__":
    add_producers()
    add_portugal()
    print("Done.")
