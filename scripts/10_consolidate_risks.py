"""
One-time consolidation:
  1. Remove the priority/secondary distinction (drop `category` -> set all to "Risk").
  2. Merge improper_waste_disposal INTO waste_pollution (combine definition + KPIs +
     supplier types; take MAX intrinsic intensity per process).
  3. Delete displacement (mining-induced displacement and resettlement) — it is a
     human-rights risk, out of scope for this environmental tool.
"""
import pandas as pd
from pathlib import Path

PROC = Path(__file__).parent.parent / "data" / "processed"


def main():
    risks = pd.read_csv(PROC / "risks.csv")
    matrix = pd.read_csv(PROC / "risk_process_matrix.csv")
    rs = pd.read_csv(PROC / "risk_supplier_types.csv")

    # --- 1. Drop category column (treat all risks equally) ---
    if "category" in risks.columns:
        risks = risks.drop(columns=["category"])
    if "priority" in risks.columns:
        risks = risks.drop(columns=["priority"])

    # --- 2. Merge improper_waste_disposal INTO waste_pollution ---
    # Find existing waste_pollution row and improper_waste_disposal row
    if "improper_waste_disposal" in set(risks["risk_id"]):
        wp_idx = risks.index[risks["risk_id"] == "waste_pollution"][0]
        iwd = risks.loc[risks["risk_id"] == "improper_waste_disposal"].iloc[0]
        # Combine definitions
        risks.at[wp_idx, "definition"] = (
            risks.at[wp_idx, "definition"].rstrip(".") + ". "
            "Includes negligent, incorrect, or illegal discarding of solid, liquid or "
            "hazardous materials in unauthorised locations (formerly tracked as a separate "
            "'improper waste disposal' risk; merged into waste pollution as both share the "
            "same datasets, KPIs, and supplier types)."
        )
        # Combine KPIs (deduplicate naively)
        risks.at[wp_idx, "key_kpis"] = (
            risks.at[wp_idx, "key_kpis"] + " "
            "Environmental Incident Frequency Rate (EIFR; unauthorised releases / spills "
            "per million hours worked); regulatory compliance deviations (notices of "
            "violation per inspection); discharge quality variance vs permit thresholds."
        )
        # Drop improper_waste_disposal row
        risks = risks[risks["risk_id"] != "improper_waste_disposal"]

    # Merge process matrix: take MAX intrinsic_intensity per process across the two rows
    iwd_rows = matrix[matrix["risk_id"] == "improper_waste_disposal"].copy()
    if len(iwd_rows):
        for _, row in iwd_rows.iterrows():
            mask = (matrix["risk_id"] == "waste_pollution") & (matrix["process"] == row["process"])
            if mask.any():
                wp_intensity = matrix.loc[mask, "intrinsic_intensity_1_5"].iloc[0]
                if row["intrinsic_intensity_1_5"] > wp_intensity:
                    matrix.loc[mask, "intrinsic_intensity_1_5"] = row["intrinsic_intensity_1_5"]
                    matrix.loc[mask, "rationale"] = (
                        str(matrix.loc[mask, "rationale"].iloc[0]).rstrip(".") + " (also covers improper disposal)."
                    )
        matrix = matrix[matrix["risk_id"] != "improper_waste_disposal"]

    # Merge supplier types: union of unique types
    if "improper_waste_disposal" in set(rs["risk_id"]):
        wp_types = set(s.strip() for s in rs.loc[rs["risk_id"] == "waste_pollution",
                                                  "supplier_types"].iloc[0].split(";"))
        iwd_types = set(s.strip() for s in rs.loc[rs["risk_id"] == "improper_waste_disposal",
                                                   "supplier_types"].iloc[0].split(";"))
        merged = "; ".join(sorted(wp_types | iwd_types))
        rs.loc[rs["risk_id"] == "waste_pollution", "supplier_types"] = merged
        rs = rs[rs["risk_id"] != "improper_waste_disposal"]

    # --- 3. Drop displacement (human-rights risk, not environmental) ---
    risks = risks[risks["risk_id"] != "displacement"]
    matrix = matrix[matrix["risk_id"] != "displacement"]
    rs = rs[rs["risk_id"] != "displacement"]

    # Save
    risks.to_csv(PROC / "risks.csv", index=False)
    matrix.to_csv(PROC / "risk_process_matrix.csv", index=False)
    rs.to_csv(PROC / "risk_supplier_types.csv", index=False)
    print(f"Risks now: {len(risks)} (removed displacement; merged improper_waste_disposal into waste_pollution)")
    print(risks[["risk_id", "risk_type"]].to_string(index=False))


if __name__ == "__main__":
    main()
