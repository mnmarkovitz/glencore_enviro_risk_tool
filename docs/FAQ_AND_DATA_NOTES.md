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

## 2. Why isn't Nigeria in the country dropdown? (Now fixed)

**What was happening.** The tool scores **commodity supply chains** — the unit of analysis is (commodity × country × process × risk). The country dropdown was built only from **producer** countries (the USGS / BP / IEA top-~10-producer lists). Nigeria — and **35 other countries** that we added purely to carry the CAHRA flag and country context — are in the dataset but are **not top producers of any tracked commodity**, so they never appeared in the dropdown and couldn't be scored.

The 36 affected countries are almost all CAHRA jurisdictions: Afghanistan, Angola, Azerbaijan, Bangladesh, Burkina Faso, Burundi, Cameroon, CAR, Chad, Eritrea, Eswatini, Ethiopia, Guinea, Haiti, Honduras, Lebanon, Libya, Mali, Mozambique, Myanmar, Niger, **Nigeria**, North Korea, Pakistan, Palestine, Republic of the Congo, Rwanda, Somalia, South Sudan, Sudan, Syria, Tanzania, Turkmenistan, Uganda, Venezuela, Yemen.

**The fix (now live).** The dropdown now lists **every country in the dataset**: producer countries first (surfaced by the selected commodity), then all other countries — explicitly labelled as "non-producer / transit jurisdictions." When you select one of these, the tool scores it in **transit / sourcing-jurisdiction mode**: every risk × process is evaluated using that country's own environmental + governance hazard and the process-intrinsic risk, with the commodity shown as "(transit / sourcing jurisdiction)." This directly supports OECD **"red-flag location of mineral origin or transit"** screening — exactly the CAHRA use case.

So Nigeria now appears in the dropdown and returns a full risk profile. If instead you want Nigeria treated as a *producer* of a specific commodity (e.g., a tin or oil supplier), add one row to `data/processed/commodity_producers.csv`:

```
Oil and gas,Nigeria,NGA,11,3.0,USGS/IEA,N,
```

---

## 3. Why don't some oil & gas producer countries show risk scores?

First, the current state: **all 10 oil & gas producer countries** — USA, Saudi Arabia, Russia, Canada, China, Iraq, UAE, Brazil, Iran, Kuwait — have **complete scores** across all 13 risks and all 5 processes (63 rows each), and all have map centroids. There are no genuinely missing oil & gas countries today. So if a row or a map pin looks blank, it is one of the following display effects, not missing data:

**(a) The app was asleep or showing a cached empty state.** Streamlit Community Cloud puts an app to sleep after a period of inactivity. The first visitor may momentarily see an empty page or stale content before it wakes. Reload the page; if you administer it, reboot the app (see Q on rebooting). We also added a guard so an empty filter combination shows a friendly "no data for this combination" message instead of blank cells.

**(b) Process applicability — the most common reason a value looks low or empty.** Per the project scope, oil & gas was brought into the tool primarily for the **Marketing / trading & transport** stage (Glencore markets crude and products; it is not, in this tool, modelled as an upstream oil *miner*/*smelter*). In `risk_process_matrix.csv`, several oil & gas-relevant risks are therefore weighted toward Marketing and Mining (extraction), while **Smelting and Recycling are marked not-applicable** (`applies = N`) for hydrocarbon value chains. Non-applicable combinations are deliberately **capped at a low Likelihood** and, unless you tick "Show non-applicable process combos" in the sidebar, are **hidden entirely**. So if you filter Oil & gas to the Smelting or Recycling process, you will correctly see little or nothing — that is by design, not a data gap.

**(c) A single missing indicator** shows as `—` (em-dash), never as a zero. Example: if a country has no value for one specific dataset (say, no Global Tailings Portal entry), only that one risk's *raw* hazard cell shows `—`; that risk still gets a Likelihood from the process-intrinsic fallback, and every other risk for that country is unaffected.

**How to confirm a country is fully scored:** filter to it in "Full Ranked Results" (Excel) or the ranked table (app) with "Show non-applicable process combos" ticked — you'll see all 13 risks × 5 processes = 65 rows (a few may be capped-low non-applicable). Nothing should be blank in the Likelihood / Severity / Overall columns.

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

### Recycling — more detail (worked example)

**What "Recycling" is and isn't in this tool.**
- **It IS:** secondary metal recovery — taking material that has already been a product (end-of-life batteries, electronics, catalytic converters, manufacturing offcuts, drosses, slags, spent industrial catalysts) and reprocessing it back into usable metal. This is a distinct process stage from Mining (digging ore), Refining/Smelting (turning ore into metal), and Marketing (trading/transport).
- **It IS NOT:** a "green" or zero-risk stage. Recycling still uses furnaces, acids, and solvents and produces hazardous residues — the tool deliberately scores it as a real environmental risk, not a clean alternative.

**Why the risk profile looks the way it does.** Recycling's single highest-intensity risk in the tool is **Waste pollution (5/5)**. The reason: to recover a small fraction of valuable metal you process large volumes of low-grade secondary material with strong chemicals, generating highly variable and often hazardous secondary waste (filter cakes, leachates, furnace dusts). Air pollution (4/5) follows — secondary smelting of, e.g., lead-acid batteries emits metal fumes. Water pollution (3/5) and soil pollution (3/5) come from leaching chemicals, wash water, and scrap-yard runoff. The "footprint" risks (water depletion, tailings, biodiversity, GHG, noise) are lower (2/5) because recycling sits in existing industrial zones rather than opening new land — which is recycling's genuine environmental advantage over virgin mining, and the tool reflects that.

**Worked example.** Filter the tool to **Cobalt → (any country) → Recycling**. You will see Waste pollution and Air pollution rise toward the top of the ranked list, while Tailings and Biodiversity sit low — the opposite shape to the same commodity under the **Mining** process, where Tailings and Biodiversity dominate. That contrast is the point: the tool shows that *shifting a supply chain from primary to secondary sourcing changes the risk profile, it doesn't remove it.*

**The mixed-source question, in practice.** Glencore's SCDD M&M procedure treats "100% recycled" as a Step-2A **mitigating factor** that can take a supplier out of scope for further due diligence (with a stated exception for precious-metals feed to LBMA-brand assets). The tool can't verify that claim from public country data — recycled-vs-blended is a property of the *specific shipment and supplier*, not the country. So the recommended workflow is:
1. Use the tool's **Recycling** scores for the Tier-1 desktop screen of any recycler in a given country.
2. At Tier 2 (SAQ), require evidence of the 100%-recycled claim (chain-of-custody, mass-balance, facility type from KYC).
3. If verified, apply Glencore's mitigating-factor rule; if blended with primary material, treat it like primary sourcing and keep the mining/refining risks in scope.

To hard-code this distinction, add a `recycled_pct` or `feedstock_type` column to the confidential `glencore_suppliers.csv` and branch the SAQ logic on it — see `OVERVIEW_AND_HANDOVER.md` §11.

---

## 5. Rebooting the app vs. re-running it — what's the difference?

These are two different actions with different effects:

| | **Reboot app** (from share.streamlit.io / "Manage app") | **Rerun** (the "Rerun" / "R" button inside the running app) |
|---|---|---|
| What it does | Tears the app's container down and rebuilds it from scratch, **pulling the latest code and data from GitHub** | Re-executes the Python script **as it currently is**, on the already-running container |
| Picks up new commits you pushed to GitHub? | **Yes** — this is how new code/data versions go live | **No** — it runs whatever code the container already has in memory |
| Clears cached data (`@st.cache_data`)? | Yes (fresh container) | Only if you also choose "Clear cache"; a plain rerun keeps the cache |
| Speed | ~1–2 minutes (full rebuild) | Instant |
| When to use | After we push changes to the repo; if the app is stuck/asleep/erroring | While using the app, to re-render after changing a filter or to recover from a transient UI glitch |

**Rule of thumb:** if you want **the latest version we built**, you must **Reboot** (or push a commit, which auto-triggers a rebuild on Streamlit Cloud). A "Rerun" inside the app will *not* show new features — it just refreshes the current version's screen. After a reboot, also hard-refresh your browser (Cmd+Shift+R / Ctrl+Shift+R) to clear the browser's own cache.

---

## 6. Why did the Risk Matrix and the Ranked Table show different counts? (Redesigned)

The original matrix was a **5×5 grid of counts**, and it caused exactly the confusion you flagged: it showed two numbers that didn't reconcile.

- The **ranked table** has one row per **risk × process** combination. For a single commodity + country that is 13 risks × 5 processes ≈ 63 rows — so "7 Critical" there meant 7 *risk-process combinations*.
- The old **grid** rounded Likelihood and Severity to whole numbers to place each combination in a cell, then counted them — but the same risk appearing under 5 processes was counted up to 5 times, and rounding pushed combinations into cells whose centre implied a different bucket. Two different "numbers of critical risks" with no obvious reconciliation.

**The redesign (now live): the matrix is now a scatter plot, one dot per environmental risk.**

- We collapse process duplicates: each environmental risk is plotted **once**, at its **worst-scoring process** (highest Overall). So for one commodity + country you see at most 13 dots — the actual environmental risks, no repeats.
- Each dot sits at its **exact** Likelihood (x) and Severity (y) — no rounding — and is **coloured by its true bucket** (Overall = L × S). Position and colour therefore always agree.
- Dotted curves mark the Low / Moderate / High / Critical boundaries (the lines where L × S = 4, 9, 14).
- The count tiles above the chart now read, e.g., "13 risks plotted: Low 2 · Moderate 4 · High 5 · Critical 2" — and that sums to the number of dots.
- Hovering a dot shows the risk name, the commodity/country, and which process drove its worst score.

**Why the matrix count and the ranked-table row count still differ — and that's correct:** the matrix counts **distinct environmental risks** (deduplicated to the worst process); the ranked table lists **every risk × process combination**. They are answering two different questions ("how many risks?" vs "how many risk-process line items?"). The caption under the matrix states this explicitly so it is no longer confusing. If you want the table to match the matrix, filter the table to a single process.

---

## 7. Lithium coverage (added)

Lithium is now in the tool as a USGS-Critical commodity. Producer countries (USGS MCS 2024 mine-production share): Australia, Chile, China, Argentina, Brazil, Zimbabwe, Portugal, Canada, United States. Portugal was added to the country dataset (indicators, centroid, soil) to support it.
