"""
One-time seed of soilgrids_country.csv from climate-zone-based estimates.
Replace with live fetch via scripts/07_fetch_soilgrids.py.
"""
import pandas as pd
from pathlib import Path

PROC = Path(__file__).parent.parent / "data" / "processed"

# (iso3, pH_0_5cm, SOC_g_per_kg, CEC_cmol_per_kg) - climate/soil-order estimates.
# pH, organic carbon, and cation exchange capacity drive heavy-metal mobility.
ROWS = [
    # Tropical humid (Oxisols/Ultisols - acidic, leached)
    ("COD", 5.0, 25, 10), ("COL", 5.2, 30, 12), ("IDN", 5.3, 30, 12),
    ("PHL", 5.5, 25, 12), ("BRA", 5.5, 25, 15), ("CMR", 5.3, 25, 12),
    ("GAB", 4.9, 40, 15), ("GHA", 5.5, 20, 10), ("MDG", 5.2, 20, 10),
    ("NGA", 5.4, 20, 12), ("VEN", 5.0, 25, 12), ("PNG", 5.2, 40, 20),
    ("AGO", 5.3, 22, 12), ("CAF", 5.0, 30, 15), ("COG", 5.1, 28, 14),
    ("MYS", 5.0, 40, 15), ("MMR", 5.5, 25, 15), ("GIN", 5.0, 35, 12),
    ("LBR", 5.0, 30, 12), ("SWZ", 5.8, 20, 15),
    # Tropical dry / savanna
    ("TZA", 6.0, 15, 15), ("UGA", 5.8, 20, 15), ("ETH", 6.5, 20, 25),
    ("ZMB", 5.5, 20, 12), ("ZWE", 5.8, 15, 15), ("MOZ", 5.5, 18, 12),
    ("MLI", 6.0, 8, 12), ("NER", 6.0, 6, 10), ("BFA", 6.0, 8, 12),
    ("TCD", 6.2, 8, 12), ("SDN", 7.5, 10, 20), ("BDI", 5.0, 25, 15),
    ("RWA", 5.0, 25, 15), ("SSD", 6.5, 15, 15), ("SOM", 7.8, 8, 20),
    ("ERI", 7.5, 10, 20),
    # Temperate continental
    ("ARG", 6.5, 30, 25), ("USA", 6.5, 30, 25), ("CAN", 6.0, 40, 20),
    ("AUS", 6.5, 20, 15), ("CHL", 6.5, 20, 20), ("CHN", 6.5, 20, 20),
    ("DEU", 6.5, 30, 25), ("POL", 6.2, 25, 22), ("RUS", 5.8, 40, 25),
    ("UKR", 6.8, 35, 30), ("KAZ", 7.2, 20, 25), ("TUR", 7.0, 18, 20),
    ("PER", 5.5, 30, 15), ("BOL", 6.5, 20, 20),
    # Boreal (acidic podzols, high SOC)
    ("FIN", 5.2, 60, 20), ("NOR", 5.0, 60, 20), ("SWE", 5.3, 55, 22),
    ("ISL", 5.2, 50, 25), ("PRK", 6.0, 25, 20),
    # Arid/desert (alkaline calcareous)
    ("SAU", 8.0, 5, 15), ("IRN", 7.8, 8, 20), ("IRQ", 7.8, 8, 20),
    ("LBY", 8.2, 5, 15), ("MEX", 7.0, 15, 20), ("ARE", 8.2, 5, 10),
    ("KWT", 8.2, 5, 10), ("BHR", 8.2, 5, 10), ("PAK", 7.5, 10, 20),
    ("YEM", 8.0, 5, 15), ("AZE", 7.5, 15, 25), ("TKM", 7.8, 8, 20),
    ("UZB", 7.5, 10, 25), ("SYR", 7.3, 12, 20),
    # Mediterranean / island / special
    ("LBN", 7.0, 15, 25), ("CUB", 6.0, 30, 20), ("HTI", 6.0, 20, 20),
    ("HND", 6.0, 25, 18), ("NCL", 5.5, 25, 15), ("BGD", 6.5, 18, 25),
    ("IND", 6.8, 15, 20), ("IRL", 5.5, 60, 25), ("GBR", 6.0, 45, 22),
    ("PSE", 7.3, 15, 20), ("AFG", 7.5, 10, 20),
]


def vuln_ph(ph):
    # Neutral pH ~ best (low heavy-metal mobility). Distance from 7 drives risk.
    return max(1.0, min(5.0, abs(ph - 7) * 1.3 + 1))


def vuln_soc(soc):
    # g/kg. Higher = more binding of contaminants.
    if soc >= 50: return 1.0
    if soc >= 30: return 2.0
    if soc >= 20: return 3.0
    if soc >= 10: return 4.0
    return 5.0


def vuln_cec(cec):
    # cmol(+)/kg. Higher = better buffering.
    if cec >= 35: return 1.0
    if cec >= 25: return 2.0
    if cec >= 15: return 3.0
    if cec >= 10: return 4.0
    return 5.0


# country name lookup from country_indicators.csv
idx = pd.read_csv(PROC / "country_indicators.csv")[["iso3", "country"]].drop_duplicates()
name = dict(zip(idx["iso3"], idx["country"]))

out = []
for iso, ph, soc, cec in ROWS:
    v = round((vuln_ph(ph) + vuln_soc(soc) + vuln_cec(cec)) / 3, 2)
    out.append(dict(
        iso3=iso, country=name.get(iso, iso),
        soil_ph_0_5cm=ph, soil_soc_g_per_kg=soc, soil_cec_cmol_per_kg=cec,
        soil_vulnerability_1_5=v,
        source_note="Seed estimate (climate/soil order). Refresh via scripts/07_fetch_soilgrids.py.",
    ))

df = pd.DataFrame(out).sort_values("country")
df.to_csv(PROC / "soilgrids_country.csv", index=False)
print(f"Wrote {len(df)} countries. Vulnerability summary:")
print(df["soil_vulnerability_1_5"].describe().round(2))
