"""
Environmental Risk Identification & Assessment Tool
===================================================

Built for the Glencore Group Responsible Sourcing team in collaboration with
NYU SPS MS Global Affairs students:
Marielle Markovitz, Maahi Gupta, Daniela Cano, Daniel Luis de Jesus,
Lindsay Huba-Zhang, Zorana Ivanovich, Mohamad Rimawi.

A pivot-style decision tool for identifying and ranking outward environmental
risks across a global metals and minerals supply chain. Every Likelihood and
Severity score is derived from a named public dataset; raw indicator values and
normalized 1-5 scores are shown side by side for auditability.

Run:  streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).parent))
from scoring import compute, _load  # noqa: E402

DATA = Path(__file__).parent.parent / "data" / "processed"
DOCS = Path(__file__).parent.parent / "docs"

# ---- Glencore turquoise for UI chrome only ----
GLENCORE_TEAL = "#00A9A5"       # used for non-risk UI accents (e.g. CAHRA=No bars)
GLENCORE_DEEP = "#005F73"

# ---- Unified bucket colors (same palette everywhere: table pills, maps, charts, heatmap cells) ----
BUCKET_COLORS = {
    "Low":      "#4CAF50",   # green   — Overall 1–4
    "Moderate": "#FFC107",   # amber   — Overall 5–9
    "High":     "#FF9800",   # orange  — Overall 10–14
    "Critical": "#E53935",   # red     — Overall 15–25
    "No data":  "#BDBDBD",
}
# Discrete-banded continuous scale for 1–25 range. Each band maps to a bucket;
# sharp edges so a country's map color matches its bucket pill exactly.
RISK_SCALE = [
    [0.00, "#4CAF50"], [4/25, "#4CAF50"],   # Low (1–4)
    [4/25, "#FFC107"], [9/25, "#FFC107"],   # Moderate (5–9)
    [9/25, "#FF9800"], [14/25, "#FF9800"],  # High (10–14)
    [14/25, "#E53935"], [1.00, "#E53935"],  # Critical (15–25)
]
# Heatmap: same stops so every L×S cell is colored by its bucket
HEAT_SCALE = RISK_SCALE

st.set_page_config(
    page_title="Environmental Risk Tool - Glencore SCDD",
    layout="wide", page_icon="🌍",
)

# ---- load reference data (cached) ----
@st.cache_data
def load_ref():
    risks, matrix, countries, producers, noise, weights, supplier_types = _load()
    return risks, matrix, countries, producers, noise, weights, supplier_types

risks_df, matrix_df, countries_df, producers_df, noise_df, weights, supplier_types_df = load_ref()

@st.cache_data
def _load_centroids():
    return pd.read_csv(DATA / "country_centroids.csv")
COUNTRY_LATLON = _load_centroids()

# --- Mine-site layers: load if present (optional, layer togglable) ---
@st.cache_data
def _load_optional(name):
    p = DATA / name
    return pd.read_csv(p) if p.exists() else pd.DataFrame()

GLENCORE_ASSETS = _load_optional("glencore_assets.csv")
GLENCORE_SUPPLIERS = _load_optional("glencore_suppliers.csv")
MRDS_SITES = _load_optional("mrds_sites.csv")
GEM_SITES = _load_optional("gem_sites.csv")

# =================================================================
# Header
# =================================================================
st.title("Environmental Risk Identification & Assessment Tool")
st.caption(
    "Supporting the Glencore Group Responsible Sourcing team (Step 2A - OSDR / Risk Identification) "
    "with publicly-sourced country and process-level environmental risk scores for metals & minerals supply chains."
)

tab_dashboard, tab_map, tab_charts, tab_risklib, tab_tiers, tab_method, tab_sources, tab_noise = st.tabs([
    "🔍 Risk Dashboard",
    "🗺️ Map",
    "📈 More Charts",
    "📚 Risk Library",
    "🤝 Supplier Engagement Tiers",
    "📐 Methodology",
    "📊 Data Sources",
    "🔊 Noise Baseline",
])


# =================================================================
# Sidebar filters (shared across tabs)
# =================================================================
st.sidebar.header("🎯 Filters")

commodity_list = sorted(producers_df["commodity"].unique())
sel_commodities = st.sidebar.multiselect("Commodity", commodity_list, default=["Cobalt"])

# Surface top producers first for the selected commodity
if sel_commodities:
    top = (
        producers_df[producers_df["commodity"].isin(sel_commodities)]
        .sort_values(["commodity", "producer_rank"])["country"]
        .drop_duplicates().tolist()
    )
    others = sorted(set(producers_df["country"]) - set(top))
    country_options = top + others
else:
    country_options = sorted(producers_df["country"].unique())

sel_countries = st.sidebar.multiselect(
    "Country (top producers surfaced first)", country_options, default=[]
)

process_options = ["Mining", "Refining", "Smelting", "Recycling", "Marketing"]
sel_processes = st.sidebar.multiselect("Process", process_options, default=process_options)

risk_priority = st.sidebar.radio(
    "Risk set", ["Priority (8 risks)", "All risks (15)", "Custom"], index=0
)
if risk_priority == "Priority (8 risks)":
    sel_risk_ids = risks_df[risks_df["category"] == "Priority"]["risk_id"].tolist()
elif risk_priority == "All risks (15)":
    sel_risk_ids = risks_df["risk_id"].tolist()
else:
    sel_risk_ids = st.sidebar.multiselect(
        "Risk types", options=risks_df["risk_id"].tolist(),
        format_func=lambda x: risks_df.set_index("risk_id").loc[x, "risk_type"],
        default=risks_df["risk_id"].tolist(),
    )

min_overall = st.sidebar.slider("Minimum Overall score", 0.0, 25.0, 0.0, 0.5)
show_non_applicable = st.sidebar.checkbox("Show non-applicable process combos", value=False)
cahra_only = st.sidebar.checkbox("🚩 CAHRA countries only", value=False,
                                  help="Restrict output to countries on Glencore's CAHRA list (Conflict-Affected & High-Risk Areas)")
critical_only = st.sidebar.checkbox("⭐ Critical minerals only", value=False,
                                     help="Restrict to USGS 2022 Critical Minerals List: Aluminum, Zinc, Nickel, Cobalt, Platinum, Ferrovanadium, Manganese alloys, Ferrochrome")

with st.spinner("Scoring..."):
    df = compute(
        commodities=sel_commodities or None,
        countries=sel_countries or None,
        processes=sel_processes or None,
        risk_ids=sel_risk_ids or None,
    )
if not show_non_applicable:
    df = df[df["applies"] == "Y"]
if min_overall > 0:
    df = df[df["overall_1_25"].fillna(0) >= min_overall]
if cahra_only:
    df = df[df["cahra_flag"] == "Y"]
if critical_only:
    critical_commodities = set(producers_df[producers_df["critical_mineral"] == "Y"]["commodity"])
    df = df[df["commodity"].isin(critical_commodities)]


# =================================================================
# DASHBOARD
# =================================================================
with tab_dashboard:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Risk combinations", f"{len(df):,}")
    c2.metric("Critical", int((df["risk_bucket"] == "Critical").sum()))
    c3.metric("High", int((df["risk_bucket"] == "High").sum()))
    c4.metric("CAHRA rows", int((df["cahra_flag"] == "Y").sum()))
    c5.metric("Avg Overall", f"{df['overall_1_25'].mean():.2f}" if len(df) else "—")

    st.divider()
    st.subheader("Risk matrix (Likelihood × Severity)")
    if len(df) and df["likelihood_1_5"].notna().any():
        df_h = df.dropna(subset=["likelihood_1_5", "severity_1_5"]).copy()
        df_h["L_bin"] = df_h["likelihood_1_5"].round().clip(1, 5).astype(int)
        df_h["S_bin"] = df_h["severity_1_5"].round().clip(1, 5).astype(int)
        counts = (df_h.groupby(["S_bin", "L_bin"]).size()
                      .reset_index(name="count")
                      .pivot(index="S_bin", columns="L_bin", values="count")
                      .reindex(index=[5, 4, 3, 2, 1], columns=[1, 2, 3, 4, 5]).fillna(0))
        # Color each cell by its L*S bucket (not by count) so the palette matches
        # the rest of the tool. Count is shown as text inside the cell.
        def _bucket_of(L, S):
            v = L * S
            if v <= 4: return BUCKET_COLORS["Low"]
            if v <= 9: return BUCKET_COLORS["Moderate"]
            if v <= 14: return BUCKET_COLORS["High"]
            return BUCKET_COLORS["Critical"]
        fig = go.Figure()
        for yi, S in enumerate([5, 4, 3, 2, 1]):
            for xi, L in enumerate([1, 2, 3, 4, 5]):
                cnt = int(counts.loc[S, L]) if S in counts.index and L in counts.columns else 0
                fig.add_shape(type="rect", x0=L-0.5, x1=L+0.5, y0=S-0.5, y1=S+0.5,
                              fillcolor=_bucket_of(L, S), line=dict(color="white", width=2))
                fig.add_annotation(x=L, y=S, text=str(cnt), showarrow=False,
                                   font=dict(color="white" if L*S >= 10 else "#222",
                                             size=18, family="Arial Black"))
        fig.update_xaxes(range=[0.4, 5.6], tickvals=[1, 2, 3, 4, 5],
                         title="Likelihood (1 low, 5 high)")
        fig.update_yaxes(range=[0.4, 5.6], tickvals=[1, 2, 3, 4, 5],
                         title="Severity (1 low, 5 high)", scaleanchor="x", scaleratio=1)
        fig.update_layout(height=500, margin=dict(l=60, r=40, t=20, b=60),
                          plot_bgcolor="white", showlegend=False)
        # Legend strip
        legend_html = "".join(
            f"<span style='display:inline-block; width:14px; height:14px; background:{c}; "
            f"border-radius:3px; margin-right:4px; vertical-align:middle;'></span> "
            f"<span style='margin-right:18px;'>{name}</span>"
            for name, c in BUCKET_COLORS.items() if name != "No data"
        )
        st.markdown(legend_html, unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Cell color = risk bucket at that Likelihood × Severity position. "
                   "Number inside each cell = how many risk-country-process combinations fall there. "
                   "Worst = top-right. Same color palette as the ranked table, maps, and charts.")
    else:
        st.info("Add filters to see the heatmap.")

    st.divider()
    st.subheader("Ranked environmental risks")
    if len(df):
        display_cols = [
            "risk_type", "commodity", "country", "cahra_flag", "process",
            "country_hazard_raw", "country_hazard_norm_1_5",
            "process_intrinsic_1_5", "likelihood_1_5",
            "ecological_sensitivity_1_5", "regulatory_strictness_1_5", "severity_1_5",
            "overall_1_25", "risk_bucket", "likely_supplier_types",
            "country_hazard_source",
        ]
        df_sorted = df.sort_values("overall_1_25", ascending=False, na_position="last").reset_index(drop=True)
        df_sorted.index = df_sorted.index + 1
        df_sorted.index.name = "Rank"

        def _style_bucket(v):
            return f"background-color: {BUCKET_COLORS.get(v, '#EEE')}; color: white;"

        def _style_cahra(v):
            return "background-color: #FFD54F; font-weight: 600;" if v == "Y" else ""

        styled = (
            df_sorted[display_cols].style
            .applymap(_style_bucket, subset=["risk_bucket"])
            .applymap(_style_cahra, subset=["cahra_flag"])
            .format({
                "country_hazard_raw": "{:.2f}", "country_hazard_norm_1_5": "{:.2f}",
                "process_intrinsic_1_5": "{:.1f}", "likelihood_1_5": "{:.2f}",
                "ecological_sensitivity_1_5": "{:.2f}", "regulatory_strictness_1_5": "{:.2f}",
                "severity_1_5": "{:.2f}", "overall_1_25": "{:.2f}",
            }, na_rep="—")
        )
        st.dataframe(styled, height=500, use_container_width=True)

        csv = df_sorted.to_csv().encode("utf-8")
        st.download_button("⬇️ Download filtered results (CSV)", csv, "env_risk_results.csv", "text/csv")

        st.divider()
        st.subheader("Drill-down")
        pick = st.selectbox(
            "Select a row to see full context",
            options=df_sorted.index,
            format_func=lambda i: f"{df_sorted.loc[i,'risk_type']} — {df_sorted.loc[i,'commodity']} — "
                                  f"{df_sorted.loc[i,'country']} — {df_sorted.loc[i,'process']} "
                                  f"(Overall {df_sorted.loc[i,'overall_1_25']})",
        )
        row = df_sorted.loc[pick]
        colA, colB = st.columns([3, 2])
        with colA:
            cahra_badge = "🚩 **CAHRA country**" if row["cahra_flag"] == "Y" else ""
            st.markdown(f"### {row['risk_type']}  {cahra_badge}")
            st.markdown(f"**{row['commodity']} · {row['country']} · {row['process']}**")
            if row["cahra_flag"] == "Y" and row.get("cahra_regions"):
                st.warning(f"CAHRA regions: {row['cahra_regions']}")
            st.markdown(f"> {row['definition']}")
            st.markdown(
                f"**Likelihood source:** {row['country_hazard_source']}  \n"
                f"**Raw value:** `{row['country_hazard_raw']}`  \n"
                f"**Normalized (1–5):** `{row['country_hazard_norm_1_5']}`  \n"
                f"**Process intensity (1–5):** `{row['process_intrinsic_1_5']}`  \n"
                f"**Likelihood (1–5):** `{row['likelihood_1_5']}`"
            )
            st.markdown(
                f"**Severity source:** EPI Ecosystem Vitality + WDPA (eco) · WGI + EPI (regulatory)  \n"
                f"**Ecological sensitivity:** `{row['ecological_sensitivity_1_5']}`  \n"
                f"**Regulatory strictness:** `{row['regulatory_strictness_1_5']}`  \n"
                f"**Severity (1–5):** `{row['severity_1_5']}`  \n"
                f"**Overall (L × S):** `{row['overall_1_25']}`  ({row['risk_bucket']})"
            )
        with colB:
            rk = risks_df[risks_df["risk_id"] == row["risk_id"]].iloc[0]
            st.markdown("### Data sources")
            st.markdown(f"- **Likelihood:** [{rk['likelihood_dataset']}]({rk['likelihood_url']}) · {rk['likelihood_indicator']}")
            st.markdown(f"- **Severity:** [{rk['severity_dataset']}]({rk['severity_url']}) · {rk['severity_indicator']}")
            st.markdown("### Likely supplier types (from Glencore supplier type library)")
            for st_ in [x.strip() for x in (row.get("likely_supplier_types") or "").split(";") if x.strip()]:
                st.markdown(f"- {st_}")
            st.markdown("### KPIs to request in the SAQ")
            st.markdown(rk["key_kpis"])
    else:
        st.info("No results match the current filters.")


# =================================================================
# MAP
# =================================================================
with tab_map:
    st.subheader("Country choropleth — max Overall risk")
    if len(df) and df["overall_1_25"].notna().any():
        country_max = (
            df.groupby(["iso3", "country", "cahra_flag"])
              .agg(max_overall=("overall_1_25", "max"),
                   avg_overall=("overall_1_25", "mean"),
                   combos=("overall_1_25", "count"))
              .reset_index()
        )
        fig_c = px.choropleth(
            country_max, locations="iso3", color="max_overall",
            hover_name="country",
            hover_data={"iso3": False, "avg_overall": ":.2f",
                        "combos": True, "cahra_flag": True, "max_overall": ":.2f"},
            color_continuous_scale=RISK_SCALE,
            range_color=(1, 25),
            labels={"max_overall": "Max Overall (1–25)"},
        )
        fig_c.update_layout(height=520, margin=dict(l=0, r=0, t=0, b=0),
                            geo=dict(showframe=False, showcoastlines=True))
        st.plotly_chart(fig_c, use_container_width=True)
    else:
        st.info("No results — adjust filters.")

    st.subheader("Producer map — satellite imagery with layerable mine sites")
    st.caption(
        "Country centroids color-coded by max Overall risk. Toggle the layers below to overlay "
        "actual facility points from public registries (and, optionally, Glencore's internal supplier list)."
    )
    basemap = st.radio(
        "Base map", ["🛰️ Satellite (ESRI World Imagery)", "🗺️ Streets (OpenStreetMap)", "🌑 Carto Dark"],
        horizontal=True, index=0, key="basemap_choice",
    )
    st.markdown("**Map layers to overlay:**")
    lay1, lay2, lay3, lay4 = st.columns(4)
    show_glencore = lay1.checkbox("🏭 Glencore-owned assets",
                                   value=True, help="Public Glencore industrial assets from their annual report.")
    show_suppliers = lay2.checkbox("🤝 My suppliers (local CSV)",
                                    value=False, help=f"Editable list in data/processed/glencore_suppliers.csv. "
                                    f"Currently {len(GLENCORE_SUPPLIERS)} rows. Git-ignored — stays confidential.")
    show_gem = lay3.checkbox("⛽ GEM sites (coal / oil-gas / iron ore / steel)",
                              value=False, help=f"Global Energy Monitor trackers (coal mines, oil/gas extraction, "
                              f"iron-ore mines, steel plants). Currently "
                              f"{len(GEM_SITES)} rows — run scripts/06_fetch_gem.py to populate.")
    show_mrds = lay4.checkbox("⛏️ All known mines (USGS MRDS)",
                               value=False, help=f"USGS Mineral Resources Data System. Currently "
                               f"{len(MRDS_SITES)} rows — run scripts/05_fetch_usgs_mrds.py to populate.")
    if sel_commodities and len(df):
        prod = producers_df[producers_df["commodity"].isin(sel_commodities)]
        max_by_ctry = df.groupby(["iso3", "country"])["overall_1_25"].max().reset_index()
        merged = prod.merge(max_by_ctry, on=["iso3", "country"], how="left")
        merged = merged.merge(COUNTRY_LATLON, on="iso3", how="left")
        merged = merged.dropna(subset=["overall_1_25", "lat", "lon"])
        if len(merged):
            if basemap.startswith("🛰️"):
                mapbox_style = "white-bg"
                mapbox_layers = [{
                    "below": "traces",
                    "sourcetype": "raster",
                    "sourceattribution": "Tiles © Esri — Sources: Esri, Maxar, Earthstar Geographics",
                    "source": [
                        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                    ],
                }]
            elif basemap.startswith("🗺️"):
                mapbox_style = "open-street-map"
                mapbox_layers = []
            else:
                mapbox_style = "carto-darkmatter"
                mapbox_layers = []

            fig_p = go.Figure()
            # Base producer bubbles
            fig_p.add_trace(go.Scattermapbox(
                lat=merged["lat"], lon=merged["lon"],
                mode="markers",
                marker=dict(
                    size=merged["share_of_global_pct"].clip(3, 38),
                    color=merged["overall_1_25"],
                    colorscale=RISK_SCALE, cmin=1, cmax=25,
                    colorbar=dict(title="Overall (1–25)"),
                    opacity=0.85,
                ),
                text=[f"{c} ({cm})<br>Rank #{r} · {s:.1f}% · Overall {o:.2f}"
                      for c, cm, r, s, o in zip(merged["country"], merged["commodity"],
                                                  merged["producer_rank"],
                                                  merged["share_of_global_pct"],
                                                  merged["overall_1_25"])],
                hovertemplate="%{text}<extra>Top-producer bubble</extra>",
                name="Top producer (country centroid)",
            ))
            # Layer 2 — Glencore-owned assets
            if show_glencore and len(GLENCORE_ASSETS):
                ga = GLENCORE_ASSETS
                if sel_commodities:
                    ga = ga[ga["commodity"].str.contains("|".join(sel_commodities), case=False, na=False)]
                if len(ga):
                    fig_p.add_trace(go.Scattermapbox(
                        lat=ga["lat"], lon=ga["lon"], mode="markers",
                        marker=dict(size=14, color="#1E88E5", symbol="triangle",
                                    opacity=0.95),
                        text=[f"<b>{n}</b><br>{t} · {c}<br>{co} · {s}<br><a href='{u}'>{u}</a>"
                              for n, t, c, co, s, u in zip(ga["asset_name"], ga["asset_type"],
                                                             ga["commodity"], ga["country"],
                                                             ga["status"], ga["source_url"])],
                        hovertemplate="%{text}<extra>Glencore-owned</extra>",
                        name="🏭 Glencore asset (public)",
                    ))
            # Layer 3 — My suppliers (confidential, user-populated)
            if show_suppliers and len(GLENCORE_SUPPLIERS):
                sp = GLENCORE_SUPPLIERS.dropna(subset=["lat", "lon"])
                if sel_commodities:
                    sp = sp[sp["commodity"].isin(sel_commodities)]
                if len(sp):
                    fig_p.add_trace(go.Scattermapbox(
                        lat=sp["lat"], lon=sp["lon"], mode="markers",
                        marker=dict(size=12, color="#FFD600", symbol="circle", opacity=0.95),
                        text=[f"<b>{n}</b><br>{c} · {co}<br>Status: {s}"
                              for n, c, co, s in zip(sp["supplier_name"], sp["commodity"],
                                                      sp["country"], sp.get("status", sp["scdd_status"]))],
                        hovertemplate="%{text}<extra>Supplier (internal)</extra>",
                        name="🤝 Supplier (internal)",
                    ))
            # Layer 4 — GEM coal mines + oil/gas
            if show_gem and len(GEM_SITES):
                gm = GEM_SITES
                if sel_commodities:
                    gm = gm[gm["commodity"].isin(sel_commodities)]
                if len(gm):
                    fig_p.add_trace(go.Scattermapbox(
                        lat=gm["lat"], lon=gm["lon"], mode="markers",
                        marker=dict(size=6, color="#6A1B9A", opacity=0.7),
                        text=[f"<b>{n}</b><br>{c} · {co}<br>Status: {s}"
                              for n, c, co, s in zip(gm["asset_name"], gm["commodity"],
                                                      gm["country"], gm.get("status", ""))],
                        hovertemplate="%{text}<extra>GEM tracker</extra>",
                        name="⛽ GEM site",
                    ))
            # Layer 1 — USGS MRDS (all mines)
            if show_mrds and len(MRDS_SITES):
                ms = MRDS_SITES
                if sel_commodities:
                    ms = ms[ms["commodity"].isin(sel_commodities)]
                ms = ms.head(2000)  # perf cap
                if len(ms):
                    fig_p.add_trace(go.Scattermapbox(
                        lat=ms["latitude"], lon=ms["longitude"], mode="markers",
                        marker=dict(size=5, color="#757575", opacity=0.55),
                        text=[f"<b>{n}</b><br>{c} · {co}"
                              for n, c, co in zip(ms["site_name"], ms["commodity"], ms.get("country", ""))],
                        hovertemplate="%{text}<extra>USGS MRDS</extra>",
                        name="⛏️ USGS MRDS site",
                    ))
            fig_p.update_layout(
                mapbox_style=mapbox_style,
                mapbox_layers=mapbox_layers,
                mapbox_zoom=1.3,
                mapbox_center=dict(lat=20, lon=10),
                height=640, margin=dict(l=0, r=0, t=0, b=0),
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01,
                            bgcolor="rgba(255,255,255,0.85)"),
            )
            st.plotly_chart(fig_p, use_container_width=True)
            st.caption(
                "Sources: country bubbles derived from "
                "[USGS Mineral Commodity Summaries 2024](https://pubs.usgs.gov/periodicals/mcs2024). "
                "Glencore-owned assets: public [Glencore annual report + operations pages](https://www.glencore.com/what-we-do). "
                "Supplier layer: editable local CSV (git-ignored). "
                "GEM: [Global Energy Monitor](https://globalenergymonitor.org/). "
                "USGS MRDS: [mrdata.usgs.gov/mrds](https://mrdata.usgs.gov/mrds/). "
                "Base imagery: [ESRI World Imagery](https://www.arcgis.com/home/item.html?id=10df2279f9684e4a9f6a7f08febac2a9)."
            )
        else:
            st.info("No producer data for current filters.")
    else:
        st.info("Pick at least one commodity to see producer bubbles.")

    st.divider()
    st.subheader("🛰️ Live satellite & hydrology layers")
    st.markdown(
        "Use these live maps to verify and visualize risk at sub-national (basin / catchment / forest) level. "
        "These are external WRI and UNEP tools — they stay up to date."
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**WRI Aqueduct Water Risk Atlas**")
        st.link_button("Open Aqueduct (water stress)",
                       "https://www.wri.org/applications/aqueduct/water-risk-atlas/")
    with col2:
        st.markdown("**Global Forest Watch**")
        st.link_button("Open GFW (deforestation, fires)", "https://www.globalforestwatch.org/map/")
    with col3:
        st.markdown("**UNEP Protected Planet**")
        st.link_button("Open WDPA (protected areas)", "https://www.protectedplanet.net/en")
    col4, col5, col6 = st.columns(3)
    with col4:
        st.markdown("**Global Tailings Portal**")
        st.link_button("Open GTP", "https://tailing.grida.no/map")
    with col5:
        st.markdown("**Climate TRACE (facility GHG)**")
        st.link_button("Open Climate TRACE", "https://climatetrace.org/explore")
    with col6:
        st.markdown("**Delve ASM database**")
        st.link_button("Open Delve", "https://www.delvedatabase.org/data")


# =================================================================
# MORE CHARTS
# =================================================================
with tab_charts:
    if not len(df):
        st.info("Add filters on the left to populate charts.")
    else:
        # Top-N countries
        st.subheader("Top countries by average Overall risk")
        top_n = st.slider("How many countries?", 5, 30, 10, key="topn")
        ctry_avg = (df.groupby(["country", "cahra_flag"])
                      .agg(avg_overall=("overall_1_25", "mean"),
                           max_overall=("overall_1_25", "max"),
                           n_combos=("overall_1_25", "count")).reset_index()
                      .sort_values("avg_overall", ascending=False).head(top_n))
        fig_ctry = px.bar(
            ctry_avg.sort_values("avg_overall"), x="avg_overall", y="country",
            color="cahra_flag", orientation="h",
            color_discrete_map={"Y": "#E53935", "N": GLENCORE_TEAL},
            hover_data={"max_overall": ":.2f", "n_combos": True},
            labels={"avg_overall": "Average Overall (1–25)", "cahra_flag": "CAHRA"},
        )
        fig_ctry.update_layout(height=max(400, 28 * top_n))
        st.plotly_chart(fig_ctry, use_container_width=True)

        st.subheader("Risk type breakdown — average Overall score")
        risk_avg = (df.groupby("risk_type")
                      .agg(avg_overall=("overall_1_25", "mean"),
                           n=("overall_1_25", "count")).reset_index()
                      .sort_values("avg_overall", ascending=True))
        fig_risk = px.bar(risk_avg, x="avg_overall", y="risk_type", orientation="h",
                          color="avg_overall",
                          color_continuous_scale=RISK_SCALE,
                          range_color=(1, 25),
                          labels={"avg_overall": "Average Overall (1–25)", "risk_type": ""})
        fig_risk.update_layout(height=500, coloraxis_showscale=False)
        st.plotly_chart(fig_risk, use_container_width=True)

        st.subheader("Commodity × Country — max Overall risk")
        if df["commodity"].nunique() > 1 or df["country"].nunique() > 1:
            pivot = (df.groupby(["commodity", "country"])["overall_1_25"].max()
                       .unstack().fillna(0))
            fig_pv = px.imshow(pivot, aspect="auto",
                               color_continuous_scale=HEAT_SCALE,
                               range_color=(0, 25),
                               labels=dict(x="Country", y="Commodity", color="Max Overall"))
            fig_pv.update_layout(height=max(300, 40 * pivot.shape[0] + 100))
            st.plotly_chart(fig_pv, use_container_width=True)

        st.subheader("Sunburst — commodity → country → risk")
        st.caption("Click a slice to zoom in. Click the center to zoom back out. "
                   "Ring thickness shows the relative Overall score; color shows absolute severity.")
        if len(df) > 0:
            # If too many risk_types bloat the ring, let user collapse to risk category
            sb_depth = st.radio("Sunburst depth",
                                 ["Commodity → Country → Risk", "Commodity → Country", "Country → Risk"],
                                 horizontal=True, key="sb_depth")
            if sb_depth == "Commodity → Country → Risk":
                path = ["commodity", "country", "risk_type"]
            elif sb_depth == "Commodity → Country":
                path = ["commodity", "country"]
            else:
                path = ["country", "risk_type"]
            sb_df = df.dropna(subset=["overall_1_25"]).copy()
            fig_sb = px.sunburst(
                sb_df, path=path,
                values="overall_1_25", color="overall_1_25",
                color_continuous_scale=RISK_SCALE,
                range_color=(1, 25),
            )
            fig_sb.update_traces(insidetextorientation="radial",
                                 textfont_size=12)
            fig_sb.update_layout(height=850, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_sb, use_container_width=True)

        st.subheader("Process comparison — average Likelihood per risk")
        proc_risk = (df.groupby(["process", "risk_type"])["likelihood_1_5"].mean()
                       .reset_index())
        fig_pr = px.bar(proc_risk, x="risk_type", y="likelihood_1_5", color="process",
                        barmode="group",
                        labels={"likelihood_1_5": "Avg Likelihood (1–5)", "risk_type": ""})
        fig_pr.update_layout(height=500, xaxis_tickangle=-30)
        st.plotly_chart(fig_pr, use_container_width=True)


# =================================================================
# RISK LIBRARY
# =================================================================
with tab_risklib:
    st.markdown(
        "Interactive reference for the 15 environmental risks in the tool. "
        "Each risk card shows the definition, KPIs the SAQ should request, "
        "which mining processes drive the risk, and the likely supplier types involved."
    )
    PROCESS_ICONS = {
        "Mining": "⛏️", "Refining": "🧪", "Smelting": "🔥",
        "Recycling": "♻️", "Marketing": "🚢",
    }
    cat_filter = st.radio("Show", ["Priority (8)", "All (15)"], horizontal=True, index=0, key="risklib_cat")
    rl_df = risks_df if cat_filter == "All (15)" else risks_df[risks_df["category"] == "Priority"]

    for _, r in rl_df.iterrows():
        with st.expander(f"**{r['risk_type']}**  ·  {r['category']}", expanded=False):
            colx, coly = st.columns([3, 2])
            with colx:
                st.markdown(f"#### Definition\n> {r['definition']}")
                st.markdown("#### Measurable KPIs to request in SAQ")
                for kpi in [k.strip() for k in r["key_kpis"].split(";") if k.strip()]:
                    st.markdown(f"- {kpi}")
            with coly:
                st.markdown("#### Mining processes that drive this risk")
                process_rows = matrix_df[(matrix_df["risk_id"] == r["risk_id"]) & (matrix_df["applies"] == "Y")]
                process_rows = process_rows.sort_values("intrinsic_intensity_1_5", ascending=False)
                for _, p in process_rows.iterrows():
                    intensity = int(p["intrinsic_intensity_1_5"])
                    bars = "🔴" * intensity + "⚪" * (5 - intensity)
                    st.markdown(f"{PROCESS_ICONS.get(p['process'], '•')} **{p['process']}** {bars}  \n<sub>{p['rationale']}</sub>", unsafe_allow_html=True)
                st.markdown("#### Likely supplier types")
                for st_ in [x.strip() for x in (r.get("likely_supplier_types") or "").split(";") if x.strip()]:
                    st.markdown(f"- {st_}")
                st.markdown("#### Public data sources")
                st.markdown(f"- **Likelihood:** [{r['likelihood_dataset']}]({r['likelihood_url']}) — {r['likelihood_indicator']}")
                st.markdown(f"- **Severity:** [{r['severity_dataset']}]({r['severity_url']}) — {r['severity_indicator']}")


# =================================================================
# SUPPLIER ENGAGEMENT TIERS
# =================================================================
with tab_tiers:
    st.markdown(
        "### Where this tool fits in Glencore's SCDD for Metals & Minerals\n"
        "Glencore's SCDD M&M Procedure follows the **OECD Due Diligence Guidance** 5-step framework "
        "(this procedure covers steps 2 and 3). Most of the procedure's work happens through four "
        "engagement tiers with escalating cost and intrusiveness. This tool automates **Tier 1** "
        "(Open Source Desktop Research) and feeds **Tiers 2–3** with targeted questions and evidence."
    )

    tiers = [
        dict(
            tier="Tier 1", name="Open-Source Desktop Research (OSDR)",
            icon="🌐", color="#4CAF50",
            where="What this tool automates",
            inputs=("Aqueduct; EPI; WHO AAQ; Global Tailings Portal; IUCN; WDPA; GFW; WB WGI; "
                    "Climate TRACE; CAHRA list; USGS top producers"),
            outputs=("Likelihood × Severity per risk × country × process; CAHRA flag; "
                     "likely supplier types; KPI watchlist for SAQ"),
            scdd_step="Step 2A — Supplier/product scoping for SCDD",
            decision="If Overall ≥ 10 (High/Critical) or CAHRA-flagged → escalate to Tier 2",
        ),
        dict(
            tier="Tier 2", name="SCDD Questionnaire (SAQ) + extended OSDR",
            icon="📋", color="#2196F3",
            where="After Tier 1 flags the supplier as in-scope",
            inputs=("Supplier-completed SAQ; management system docs; publicly-available "
                    "policies/certifications; adverse-news screening; beneficial ownership"),
            outputs=("Evidence of environmental management systems; traceability documents; "
                     "corrective action history; third-party certifications (RMI/Copper Mark/LBMA)"),
            scdd_step="Step 2B — SCDD Questionnaire (SAQ) + Step 2C Risk assessment",
            decision="Gaps or inconsistencies → Tier 3. No issues + risks managed → Approve.",
        ),
        dict(
            tier="Tier 3", name="Onsite visit / On-the-ground Assessment (OGA)",
            icon="🏭", color="#FF9800",
            where="When SAQ/OSDR leave unresolved high-consequence risk",
            inputs=("Trained assessor onsite; water/air/soil sampling; interviews with workers & "
                    "community; inspection of TSFs, waste streams, effluent, safety practices"),
            outputs=("Firsthand evidence of conditions; signed nonconformances; verified material "
                     "traceability; photos and sampling data"),
            scdd_step="Step 3.1.5 Onsite visits / 3.1.6 On-the-ground assessments",
            decision="Unresolved nonconformances → design CAP (Tier 4). Severe violations → reject.",
        ),
        dict(
            tier="Tier 4", name="Corrective Action Plan (CAP) + monitoring",
            icon="🛠️", color="#E53935",
            where="When risks are real but supplier can remediate",
            inputs=("CAP jointly designed with supplier; milestones; evidence requirements; "
                    "reporting cadence"),
            outputs=("Timebound remediation plan; ongoing monitoring reports; escalation trigger "
                     "list; re-assessment date"),
            scdd_step="Step 3.1.7 CAPs + monitoring (in SCDD M&M procedure)",
            decision="CAP met → re-approve. CAP missed → reject 3P (per SCDD procedure).",
        ),
    ]

    for t in tiers:
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 4, 2])
            with c1:
                st.markdown(f"<div style='font-size:48px;'>{t['icon']}</div>", unsafe_allow_html=True)
                st.markdown(f"<span style='background:{t['color']};color:white;padding:4px 10px;border-radius:4px;font-weight:600;'>{t['tier']}</span>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"### {t['name']}")
                st.markdown(f"**Used:** {t['where']}  \n**Glencore SCDD step:** {t['scdd_step']}")
                st.markdown(f"**Inputs / evidence collected:**  \n{t['inputs']}")
                st.markdown(f"**Outputs:**  \n{t['outputs']}")
            with c3:
                st.markdown("**Escalation decision**")
                st.info(t["decision"])

    st.divider()
    st.subheader("How this tool auto-populates the SAQ (Tier 2)")
    st.markdown(
        "When Tier 1 flags a supplier as in-scope, the tool's **ranked risk table** identifies which "
        "risks matter for the specific commodity + country + process combination. The Responsible "
        "Sourcing analyst can then prioritize SAQ questions by:\n"
        "1. Focusing on KPIs listed in the **Risk Library** tab for each flagged risk\n"
        "2. Asking for evidence on the **Likely Supplier Types** column in the dashboard\n"
        "3. Cross-referencing **CAHRA regions** with the supplier's declared origin/transit countries\n\n"
        "This mirrors the SCDD M&M procedure's Step 2A → 2B → 2C workflow."
    )


# =================================================================
# METHODOLOGY
# =================================================================
with tab_method:
    st.markdown(
        """
### Scoring methodology

All scores on a **1–5** scale (5 = worst). Overall = Likelihood × Severity (1–25).

| Range | Bucket |
|---|---|
| 1–4  | Low |
| 5–9  | Moderate |
| 10–14 | High |
| 15–25 | Critical |

**Likelihood = 0.4 × Process Intrinsic Risk + 0.6 × Country Hazard Score**

- *Process Intrinsic Risk* (1–5): from `risk_process_matrix.csv`, derived from ENCORE materiality + IFC EHS Guidelines.
- *Country Hazard Score* (1–5): risk-specific public indicator normalized (see Data Sources tab).

**Severity = 0.5 × Ecological Sensitivity + 0.5 × Regulatory Strictness**

- *Ecological Sensitivity*: EPI Ecosystem Vitality (inv.) + WDPA protected area % (inv.)
- *Regulatory Strictness*: WB WGI Regulatory Quality + EPI overall. Stricter regime = higher penalty exposure.

All weights editable in `scoring_weights.csv`. Full detail in `docs/METHODOLOGY.md`.

### Alignment with Glencore SCDD M&M Procedure

| Glencore SCDD Step | What the tool provides |
|---|---|
| Step 2A — Supplier/product scoping | CAHRA flag + automatic risk ranking by commodity + country + process |
| Step 2B — SAQ issuance | KPI list per risk (in Risk Library) to target SAQ questions |
| Step 2C — Risk assessment | Raw indicator + normalized 1–5 for each risk; source + URL for cross-check |
| Step 3.1.7 — CAPs | Ranked risk list identifies where CAPs are most needed |

This tool operates at **OSDR** level (Tier 1). It does not replace the SAQ, onsite visit, or CAP process — it accelerates their targeting.
"""
    )


# =================================================================
# DATA SOURCES
# =================================================================
with tab_sources:
    st.markdown("### Master source list — every dataset and list used in this tool")
    st.markdown(
        """
#### Country-level risk indicators
- **[WRI Aqueduct 4.0](https://www.wri.org/applications/aqueduct/country-rankings/)** — Baseline Water Stress, Drought Risk, Riverine Flood Risk (189 countries). CC BY 4.0.
- **[Yale EPI 2024](https://epi.yale.edu)** — Ecosystem Vitality, Waste Management, Heavy Metals, Air Quality, Overall (180 countries). Attribution required.
- **[WHO Ambient Air Quality Database](https://www.who.int/data/gho/data/themes/air-pollution/who-air-quality-database)** — PM2.5 annual mean concentration.
- **[World Bank Open Data](https://data.worldbank.org/)** — CO₂ per capita (EN.ATM.CO2E.PC); **[World Bank WGI](https://www.worldbank.org/en/publication/worldwide-governance-indicators)** — Regulatory Quality, Government Effectiveness. CC BY 4.0.
- **[IUCN Red List API](https://apiv3.iucnredlist.org/)** — Threatened species counts by country. Free token required.
- **[Protected Planet / WDPA (UNEP-WCMC)](https://www.protectedplanet.net/en)** — % national terrestrial area protected.
- **[Global Forest Watch (WRI)](https://www.globalforestwatch.org/)** — Tree cover loss per country per year.
- **[EC JRC EDGAR](https://edgar.jrc.ec.europa.eu/)** — National SO₂ and NOx emissions inventories.
- **[Global Tailings Portal](https://tailing.grida.no/)** — ~1,900 tailings storage facilities (GRID-Arendal, Church of England Pensions Board).
- **[INFORM Risk Index (EC JRC)](https://drmkc.jrc.ec.europa.eu/inform-index)** — Natural hazard exposure.
- **[UNESCO World Heritage](https://whc.unesco.org)** — Heritage sites and sites in danger.
- **[UNEP Basel Convention](http://www.basel.int)** — National hazardous waste generation (kt/yr).
- **[NIOSH Mining Noise](https://www.cdc.gov/niosh/mining/topics/Noise.html)** + **[IFC EHS Guidelines (Base Metal Smelting & Refining)](https://www.ifc.org/ehsguidelines)** — dBA by mining activity.
- **[ISRIC SoilGrids 2.0](https://soilgrids.org/)** — Topsoil pH, organic carbon, cation exchange capacity at 250 m resolution. Used to compute soil vulnerability feeding the soil-pollution risk likelihood. CC BY 4.0. Refresh via `scripts/07_fetch_soilgrids.py`.

#### Commodity production and criticality
- **[USGS Mineral Commodity Summaries 2024](https://pubs.usgs.gov/periodicals/mcs2024)** — Top producer rankings per commodity (`commodity_producers.csv`).
- **[USGS 2022 Critical Minerals List](https://www.usgs.gov/news/national-news-release/us-geological-survey-releases-2022-list-critical-minerals)** — Critical-mineral flag (`critical_mineral` column).
- **[USGS Critical Minerals Atlas](https://apps.usgs.gov/critical-minerals/critical-minerals-atlas.html)** — Context for the 50 US-critical minerals.
- **[BP Statistical Review of World Energy 2024](https://www.energyinst.org/statistical-review)** + **[IEA](https://www.iea.org/)** — Coal and oil/gas production shares.

#### Mine-site registries (map layers)
- **[USGS Mineral Resources Data System (MRDS)](https://mrdata.usgs.gov/mrds/)** — ~300,000 global mineral sites (fetch via `scripts/05_fetch_usgs_mrds.py`). Labeled "All known mines" on the map — NOT Glencore-specific.
- **[Global Energy Monitor](https://globalenergymonitor.org/)** — Global [Coal Mine Tracker](https://globalenergymonitor.org/projects/global-coal-mine-tracker/), [Oil & Gas Extraction Tracker](https://globalenergymonitor.org/projects/global-oil-gas-extraction-tracker/), [Iron Ore Mine Tracker](https://globalenergymonitor.org/projects/global-iron-ore-mines-tracker/), [Steel Plant Tracker](https://globalenergymonitor.org/projects/global-steel-plant-tracker/) (fetch via `scripts/06_fetch_gem.py`). CC BY 4.0.
- **Glencore-owned industrial assets** — Manually curated from public [Glencore operations pages](https://www.glencore.com/what-we-do) and the [2023 Annual Report](https://www.glencore.com/publications/annual-report-2023) (`glencore_assets.csv`). Always verify against the latest annual report.
- **Confidential supplier CSV** — `glencore_suppliers.csv` is user-populated and **git-ignored**. Replace with Glencore's internal counterparty database on handover.

#### Governance / high-risk lists
- **[Glencore CAHRA List 2025](https://www.glencore.com/.rest/api/v1/documents/a5e42c35c81a2e5d3d91e7b8d8d06e0c/Glencore-CAHRA-List.pdf)** (updated 27.02.2025) — 50 high-risk countries / sub-regions driving the CAHRA flag.
- **[OECD Due Diligence Guidance for Responsible Supply Chains of Minerals](https://www.oecd.org/daf/inv/mne/mining.htm)** (3rd edition) — the 5-step framework Glencore's SCDD procedure follows.
- **[RMI Supply Chain Due Diligence Plus Module](https://www.responsiblemineralsinitiative.org/)** — due-diligence harmonization reference.

#### Map base imagery
- **[ESRI World Imagery](https://www.arcgis.com/home/item.html?id=10df2279f9684e4a9f6a7f08febac2a9)** — free satellite tiles (Esri, Maxar, Earthstar Geographics). Attribution required.
- **[OpenStreetMap](https://www.openstreetmap.org/copyright)** — ODbL, street base layer.
- **[Carto Dark Matter](https://carto.com/attributions)** — CC BY 3.0 dark basemap.

#### Live external tools (linked from the Map tab)
- **[WRI Aqueduct Water Risk Atlas (interactive)](https://www.wri.org/applications/aqueduct/water-risk-atlas/)**
- **[Global Forest Watch map](https://www.globalforestwatch.org/map/)**
- **[Protected Planet map](https://www.protectedplanet.net/en)**
- **[Global Tailings Portal map](https://tailing.grida.no/map)**
- **[Climate TRACE facility GHG](https://climatetrace.org/explore)**
- **[Delve ASM database](https://www.delvedatabase.org/data)**
"""
    )

    st.divider()
    st.markdown("### Risk → likelihood & severity dataset mapping")
    st.dataframe(
        risks_df[["risk_type", "category", "likelihood_dataset", "likelihood_indicator",
                  "likelihood_url", "severity_dataset", "severity_indicator", "severity_url"]],
        use_container_width=True, height=450,
    )

    st.markdown("### CAHRA-flagged countries in the tool")
    cahra_tbl = countries_df[countries_df["cahra_flag"] == "Y"][["iso3", "country", "cahra_regions"]].sort_values("country")
    st.dataframe(cahra_tbl, use_container_width=True, height=400)
    st.markdown(f"**{len(cahra_tbl)} CAHRA countries** from [Glencore CAHRA List 2025](https://www.glencore.com/) (updated 27.02.2025).")

    st.markdown("### Critical minerals flag")
    crit_list = producers_df[producers_df["critical_mineral"] == "Y"]["commodity"].unique().tolist()
    st.markdown("Source: [USGS 2022 Critical Minerals List](https://www.usgs.gov/news/national-news-release/us-geological-survey-releases-2022-list-critical-minerals). "
                f"**{len(crit_list)} of our tool's commodities are on the list**: {', '.join(crit_list)}.")

    st.markdown("### Supplier types")
    st.caption("Source: Glencore internal supplier-type library (used for SAQ prioritization).")
    st.dataframe(supplier_types_df, use_container_width=True)

    st.markdown("### Commodity → top producer countries")
    st.caption("Source: [USGS Mineral Commodity Summaries 2024](https://pubs.usgs.gov/periodicals/mcs2024); "
                "coal and oil/gas from [BP Statistical Review 2024](https://www.energyinst.org/statistical-review) + IEA.")
    st.dataframe(producers_df, use_container_width=True, height=350)

    st.markdown("### Glencore-owned industrial assets (public)")
    st.caption(f"{len(GLENCORE_ASSETS)} rows. Sources cited in each row's `source_url` column. "
                "Manually maintained — verify against the latest [Glencore annual report](https://www.glencore.com/publications/annual-report-2023) when updating.")
    if len(GLENCORE_ASSETS):
        st.dataframe(GLENCORE_ASSETS, use_container_width=True, height=350)


# =================================================================
# NOISE
# =================================================================
with tab_noise:
    st.markdown(
        "### Noise baseline by process and activity\n"
        "Source: NIOSH Mining Noise surveillance program + IFC EHS Guidelines. "
        "No global country-level dataset exists — site-level measurement required. "
        "Use this table as the baseline expectation for SAQ follow-up questions."
    )
    st.dataframe(noise_df, use_container_width=True)
    # Render as a range-bar chart (Gantt-style), grouped by process, with proper margin for labels
    ndf = noise_df.copy()
    ndf["mid"] = (ndf["typical_dba_min"] + ndf["typical_dba_max"]) / 2
    ndf["label"] = ndf["process"] + " — " + ndf["activity"]
    ndf = ndf.sort_values(["process", "typical_dba_max"], ascending=[True, True])
    def _bucket(v):
        if v >= 105: return "#E53935"  # red
        if v >= 95:  return "#FF9800"  # orange
        if v >= 85:  return "#FFC107"  # amber
        return "#4CAF50"               # green
    colors = [_bucket(v) for v in ndf["typical_dba_max"]]
    fig_n = go.Figure()
    fig_n.add_trace(go.Bar(
        y=ndf["label"],
        x=ndf["typical_dba_max"] - ndf["typical_dba_min"],
        base=ndf["typical_dba_min"],
        orientation="h",
        marker_color=colors,
        text=[f"{int(mn)}–{int(mx)} dBA" for mn, mx in zip(ndf["typical_dba_min"], ndf["typical_dba_max"])],
        textposition="outside",
        customdata=ndf[["process", "source_note"]].values,
        hovertemplate="<b>%{y}</b><br>Range: %{base:.0f}–%{x:.0f} dBA<br>Source: %{customdata[1]}<extra></extra>",
    ))
    fig_n.add_vline(x=85, line_dash="dash", line_color="#6C757D",
                    annotation_text="OSHA action (85 dBA)", annotation_position="top")
    fig_n.add_vline(x=90, line_dash="dash", line_color="#6C757D",
                    annotation_text="OSHA PEL (90 dBA)", annotation_position="bottom")
    fig_n.update_layout(
        showlegend=False,
        height=max(600, 30 * len(ndf) + 150),
        margin=dict(l=300, r=120, t=60, b=40),
        title="Typical noise exposure by activity (dBA)",
        xaxis_title="Decibels (dBA)",
        xaxis=dict(range=[70, 150]),
        yaxis=dict(automargin=True, title=""),
        bargap=0.25,
    )
    st.plotly_chart(fig_n, use_container_width=True)


# =================================================================
# Sidebar footer (attribution)
# =================================================================
st.sidebar.divider()
st.sidebar.markdown(
    """
**Built for the Glencore Group Responsible Sourcing team** in collaboration with NYU School of Professional Studies Master of Science in Global Affairs students:

- Marielle Markovitz
- Maahi Gupta
- Daniela Cano
- Daniel Luis de Jesus
- Lindsay Huba-Zhang
- Zorana Ivanovich
- Mohamad Rimawi

_Edit CSVs in `data/processed/` to update the tool — no code changes needed. See `docs/HOW_TO_EDIT.md`._
"""
)
