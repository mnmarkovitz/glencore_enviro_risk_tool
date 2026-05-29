# FAQ & Data Notes

Answers to common questions about the tool's data, coverage, and design choices. Read alongside `METHODOLOGY.md` (the scoring math) and `OVERVIEW_AND_HANDOVER.md` (how it was built and how to integrate/customize it).

---

## 1. Selection criteria for the underlying data

Every dataset in the tool had to meet **all five** of these criteria. This is why some otherwise-useful sources were left out.

1. **Public & free** — no paywall, no per-seat licence. So an analyst, an auditor, or a regulator can independently verify any score. (This excluded SEED Index, S&P/Verisk proprietary indices, etc.)
2. **Global country coverage** — usable for any sourcing country, not just one region. (This is why there is no noise-pollution country score — no global noise dataset exists; we use a NIOSH process baseline instead.)
3. **Authoritative & maintained** — published by a recognized scientific or governmental body that updates it on a known cycle (WRI, Yale, WHO, World Bank, USGS, UNEP, ISRIC, IUCN, EC JRC, NRGI, EJOLT).
4. **Quantitative & comparable** — a numeric indicator that can be normalized onto a 1–5 scale across countries. Narrative reports were used as context only, not as scores.
5. **Relevant to a specific environmental risk** — each dataset maps to at least one of the 13 risks (see `risks.csv` and the Data Sources sheet/tab).

When two datasets both qualified for the same risk, we preferred the one that is (a) most specific to mining/extractives and (b) most recently updated. Example: for soil pollution we blend ISRIC SoilGrids (physical soil mobility) with Yale EPI Heavy Metals (pollution burden), rather than either alone.

---

## 2. Why isn't Nigeria included?

Nigeria is **in the country dataset** (it carries full environmental indicators and a CAHRA flag), but it does **not appear as a top producer** of any of the commodities Glencore sources in the volumes the tool tracks.

The commodity → country lists come from **USGS Mineral Commodity Summaries 2024** (for metals) and **BP Statistical Review + IEA** (for coal and oil & gas), and we include each commodity's **top ~10 producer countries by global production share**. Nigeria is a significant **oil producer**, but on a *global production-share* basis it falls outside the top 10 for crude (it sits ~12th–15th depending on year), so it didn't make the oil & gas producer list.

**How to add it:** if Glencore sources from Nigeria (e.g., a specific oil or tin supplier), add a row to `data/processed/commodity_producers.csv`:

```
Oil and gas,Nigeria,NGA,11,3.0,USGS/IEA,N,
```

Because Nigeria already has full indicator data, it will immediately get scored across all risks and appear on the map (it already has a centroid). No other change needed.

---

## 3. Why don't some oil & gas producer countries show risk scores?

Three possible reasons, in order of likelihood:

1. **The app was asleep / showing a cached empty state.** Streamlit Community Cloud sleeps after inactivity; the first visit may briefly show no data. Fix: reload, and if hosted, reboot the app. (We also added a guard so empty filter combinations show a friendly message instead of blank cells.)
2. **Process applicability.** Oil & gas was added to the tool specifically for the **Marketing / trading & transport** process (per the project scope). For the **Mining / Refining / Smelting / Recycling** processes, many oil & gas rows are marked *not applicable* (`applies = N`) in `risk_process_matrix.csv`, so their Likelihood is capped low and they read as Low — not blank, but low. If you filter to only those processes you'll see few high scores for oil & gas.
3. **A genuinely missing indicator** for one risk in one country shows as `—` (em-dash), not zero. That single risk falls back to the process-intrinsic score; the country still has scores for every other risk.

As of the current data, **all 10 oil & gas producer countries** (USA, Saudi Arabia, Russia, Canada, China, Iraq, UAE, Brazil, Iran, Kuwait) have complete scores and map centroids. If a specific one looks blank, it's reason #1 — reboot the app.

---

## 4. How is "Recycling" defined?

In this tool, **Recycling** is the process stage covering **secondary / scrap-based metal recovery** — reprocessing end-of-life products, manufacturing scrap, slags, drosses, spent catalysts, and other secondary feedstocks back into usable metal.

**Scope captured by the risk-process matrix** (`risk_process_matrix.csv`, the `Recycling` rows):
- **Waste pollution: intensity 5/5** — secondary processing produces hazardous, highly variable waste streams; this is the dominant recycling risk in the tool.
- **Water pollution: 3/5** — leaching chemicals and wash water; risk of closed-loop failure.
- **Air pollution: 4/5** — secondary smelting fumes (e.g., lead, zinc recovery).
- **Soil pollution: 3/5** — stormwater runoff from scrap yards.
- **Water depletion / tailings / biodiversity / GHG / noise:** 2/5 each — primarily an industrial-facility footprint, lower than virgin mining.

**Treatment of mixed sources.** The tool scores recycling at the **country + commodity + process** level — it does **not** distinguish 100%-recycled feedstock from blended (recycled + primary) feedstock, because that distinction is a **supplier-specific attribute**, not a country-level one. This mirrors Glencore's own SCDD M&M procedure, where "100% recycled" is a *mitigating factor* assessed at the supplier level (Step 2A scoping), not a country-level input. In practice:
- Use the tool's **Recycling** scores to scope the Tier-1 desktop risk for any recycler in a given country.
- At Tier 2 (SAQ), confirm whether the material is 100% recycled or blended — per Glencore's procedure, a verified 100%-recycled supplier (with the LBMA precious-metals exception) can be treated as a mitigating factor and may fall out of scope for further SCDD.

If Glencore wants the tool to model 100%-recycled vs blended explicitly, that becomes a **supplier-level field** in the (confidential) `glencore_suppliers.csv` — see the customization guide in `OVERVIEW_AND_HANDOVER.md`.

---

## 5. Why might the Risk Matrix and the Ranked Table look different?

This was a real display quirk that has now been **fixed**. Here is what was happening and how it now behaves:

- The **Ranked Table** buckets each row by its own `Overall = Likelihood × Severity` value (1–4 Low, 5–9 Moderate, 10–14 High, 15–25 Critical). This is the authoritative count.
- The **5×5 Risk Matrix** places each row in a cell by its **rounded** Likelihood (x) and **rounded** Severity (y). A cell's L×S product (using the rounded centre values) can land in a *different* bucket than some of the individual rows inside it — because rounding 4.6 → 5 changes the product. That made the matrix's colour imply a different count than the table.

**The fix (now live):**
1. Above the matrix we now show **exact bucket-count tiles** (Low / Moderate / High / Critical), computed from each row's *own* Overall — these are guaranteed identical to the ranked table.
2. Each matrix cell is now coloured by the **majority bucket of the rows actually in it** (not by the rounded-centre product), and the number in the cell is the count of rows there.
3. A caption explains that cell rounding can place adjacent-bucket rows together, and that the tiles above are the authoritative totals.

So: for **Cobalt × Indonesia**, both the tiles and the ranked table now agree — Low 0, Moderate 9, High 47, Critical 7 (63 rows total). The matrix is a *positional* visualization; the tiles and table are the *exact* counts.

---

## 6. Lithium coverage (added)

Lithium is now in the tool as a USGS-Critical commodity. Producer countries (USGS MCS 2024 mine-production share): Australia, Chile, China, Argentina, Brazil, Zimbabwe, Portugal, Canada, United States. Portugal was added to the country dataset (indicators, centroid, soil) to support it.
