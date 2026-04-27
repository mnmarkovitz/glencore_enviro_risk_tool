"""
Build a 9-slide PPTX deck for the graduate-level class presentation.
Speaker = 2 people, 5 min each. Geopolitics-of-energy lens.
Output: Glencore_Env_Risk_Tool_Deck.pptx (uploadable to Google Slides).
"""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from copy import deepcopy

ROOT = Path(__file__).parent.parent
ASSETS = ROOT / "docs" / "slide_assets"
OUT = ROOT / "Glencore_Env_Risk_Tool_Deck.pptx"

# --- Glencore palette ---
TEAL = RGBColor(0x00, 0xA9, 0xA5)
DEEP = RGBColor(0x00, 0x5F, 0x73)
LIGHT = RGBColor(0xE0, 0xF2, 0xF1)
TEXT_DARK = RGBColor(0x1A, 0x1A, 0x1A)
TEXT_GREY = RGBColor(0x55, 0x55, 0x55)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ORANGE = RGBColor(0xFF, 0x98, 0x00)
RED = RGBColor(0xE5, 0x39, 0x35)
GREEN = RGBColor(0x4C, 0xAF, 0x50)
AMBER = RGBColor(0xFF, 0xC1, 0x07)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
SW, SH = prs.slide_width, prs.slide_height
BLANK = prs.slide_layouts[6]


def add_rect(slide, x, y, w, h, fill, line=None):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    s.fill.solid(); s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
    s.shadow.inherit = False
    return s


def add_text(slide, x, y, w, h, text, size=18, color=TEXT_DARK, bold=False,
              align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, italic=False,
              font="Calibri"):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.05)
    para = tf.paragraphs[0]
    para.alignment = align
    run = para.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.italic = italic
    run.font.name = font
    return tb


def add_bullets(slide, x, y, w, h, items, size=14, color=TEXT_DARK,
                 line_spacing=1.18):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = PP_ALIGN.LEFT
        para.line_spacing = line_spacing
        bold = False
        text = item
        if isinstance(item, tuple):
            text, bold = item
        run = para.add_run()
        run.text = "• " + text
        run.font.size = Pt(size)
        run.font.color.rgb = color
        run.font.bold = bold
        run.font.name = "Calibri"
    return tb


def add_header(slide, title, subtitle=None):
    """Top accent bar + title."""
    add_rect(slide, 0, 0, SW, Inches(0.15), TEAL)
    add_text(slide, Inches(0.5), Inches(0.25), Inches(12.3), Inches(0.6),
              title, size=26, color=DEEP, bold=True)
    if subtitle:
        add_text(slide, Inches(0.5), Inches(0.85), Inches(12.3), Inches(0.4),
                  subtitle, size=14, color=TEXT_GREY, italic=True)


def add_footer(slide, page_num, total):
    add_text(slide, Inches(0.5), Inches(7.05), Inches(8), Inches(0.35),
              "Glencore Environmental Risk Tool — NYU SPS MS Global Affairs",
              size=9, color=TEXT_GREY, italic=True)
    add_text(slide, Inches(11.5), Inches(7.05), Inches(1.3), Inches(0.35),
              f"{page_num} / {total}", size=9, color=TEXT_GREY,
              align=PP_ALIGN.RIGHT)


def add_speaker_notes(slide, notes):
    slide.notes_slide.notes_text_frame.text = notes


# ========================================================================
# Slide 1 — Title
# ========================================================================
s = prs.slides.add_slide(BLANK)
# Full teal background
add_rect(s, 0, 0, SW, SH, DEEP)
add_rect(s, 0, Inches(2.5), SW, Inches(2.5), TEAL)
add_text(s, Inches(0.5), Inches(2.7), Inches(12.3), Inches(0.6),
          "ENVIRONMENTAL RISK IDENTIFICATION & ASSESSMENT TOOL",
          size=16, color=WHITE, bold=True)
add_text(s, Inches(0.5), Inches(3.3), Inches(12.3), Inches(1.6),
          "For Glencore's Group Responsible Sourcing team",
          size=40, color=WHITE, bold=True)
add_text(s, Inches(0.5), Inches(5.0), Inches(12.3), Inches(0.5),
          "A geopolitics-of-energy lens on critical-mineral supply chains",
          size=18, color=LIGHT, italic=True)
add_text(s, Inches(0.5), Inches(6.2), Inches(12.3), Inches(0.4),
          "NYU School of Professional Studies  |  MS Global Affairs  |  Spring 2026",
          size=12, color=LIGHT)
add_text(s, Inches(0.5), Inches(6.55), Inches(12.3), Inches(0.4),
          "Marielle Markovitz · Maahi Gupta · Daniela Cano · Daniel Luis de Jesus · "
          "Lindsay Huba-Zhang · Zorana Ivanovich · Mohamad Rimawi",
          size=10, color=LIGHT, italic=True)
add_speaker_notes(s,
    "[Speaker 1, 30 sec] Welcome. We're presenting an environmental risk "
    "identification tool we built for the Glencore Responsible Sourcing team. "
    "Our framing is the geopolitics of the energy transition — the minerals "
    "we need for batteries and grids are concentrated in jurisdictions where "
    "environmental due diligence is hardest. We'll walk through the scope, "
    "the geopolitical context, the tool itself, a case study, and how it "
    "fits Glencore's existing workflow.")


# ========================================================================
# Slide 2 — Scope of Work
# ========================================================================
s = prs.slides.add_slide(BLANK)
add_header(s, "Scope of Work",
            "What Glencore asked for · How we framed our response")
# Two columns
add_text(s, Inches(0.5), Inches(1.5), Inches(6.0), Inches(0.4),
          "Mandate", size=16, color=DEEP, bold=True)
add_bullets(s, Inches(0.5), Inches(1.95), Inches(6.0), Inches(4.5), [
    ("A pivot-style decision tool for Glencore's Group Responsible Sourcing "
     "team to support OECD-aligned Tier 1 due diligence", True),
    "Cover the value chain end-to-end: mining → refining → smelting → "
    "recycling → marketing",
    "Quantify outward environmental risks (penalties, fines, reputation) — "
    "not climate-on-company risks",
    "Prioritise: water, waste, tailings, biodiversity, noise, air, soil",
    "Editable by non-technical analysts — Excel/Sheets-friendly",
    "Built on free, audit-able public data only",
], size=12)

add_text(s, Inches(7.0), Inches(1.5), Inches(5.8), Inches(0.4),
          "Frameworks aligned to", size=16, color=DEEP, bold=True)
add_bullets(s, Inches(7.0), Inches(1.95), Inches(5.8), Inches(4.5), [
    ("OECD Due Diligence Guidance for Responsible Supply Chains of Minerals "
     "(3rd ed., 2016)", True),
    "Glencore SCDD Procedure — Metals & Minerals (2024) — automates Step 2A "
    "(Supplier/product scoping) and 2B/2C",
    "EU CSRD + CSDDD reporting expectations",
    "RMI Supply Chain Due Diligence Plus Module (April 2025)",
    "ENCORE materiality + IFC EHS Guidelines for process-level intensity",
], size=12)
# Cite footer
add_text(s, Inches(0.5), Inches(6.55), Inches(12.3), Inches(0.35),
          "Sources: OECD DDG (oecd.org/daf/inv/mne/mining.htm); "
          "Glencore SCDD Procedure for Metals & Minerals; RMI (responsiblemineralsinitiative.org).",
          size=9, color=TEXT_GREY, italic=True)
add_footer(s, 2, 9)
add_speaker_notes(s,
    "[Speaker 1, 1 min] Glencore engaged us to build a Tier 1 desktop "
    "research tool for environmental risk in their metals and minerals "
    "supply chain. The mandate had a few hard constraints: it had to "
    "automate the early steps of their existing OECD-aligned due "
    "diligence procedure — specifically Step 2A and 2B; it had to be "
    "non-technical so any RS analyst could use it; and every score had "
    "to come from a public, audit-able source so it could survive a "
    "CSRD or CSDDD review. We aligned our scoring methodology to ENCORE "
    "materiality and the IFC EHS Guidelines for process-level intensity. "
    "I'll now hand to [Speaker 2] for the geopolitical framing.")


# ========================================================================
# Slide 3 — Geopolitics framing
# ========================================================================
s = prs.slides.add_slide(BLANK)
add_header(s, "Why this matters now",
            "The energy transition is mineral-intensive — and supply is concentrated")
# Big stat callouts
def stat(slide, x, y, big, label, color=TEAL):
    add_rect(slide, x, y, Inches(3.1), Inches(2.0), color)
    add_text(slide, x, y + Inches(0.2), Inches(3.1), Inches(0.9), big,
              size=44, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, x, y + Inches(1.15), Inches(3.1), Inches(0.8), label,
              size=11, color=WHITE, align=PP_ALIGN.CENTER)

stat(s, Inches(0.5), Inches(1.55), "4–6×",
      "IEA: critical-mineral demand growth by 2040 under net-zero scenarios", DEEP)
stat(s, Inches(3.7), Inches(1.55), "74%",
      "Cobalt — DRC share of 2023 global production (USGS MCS 2024)", TEAL)
stat(s, Inches(6.9), Inches(1.55), "48%",
      "Nickel — Indonesia share of 2023 global production", TEAL)
stat(s, Inches(10.1), Inches(1.55), "72%",
      "Platinum — South Africa share of 2023 global production", DEEP)

# Text block
add_text(s, Inches(0.5), Inches(3.85), Inches(12.3), Inches(0.4),
          "Two trends collide", size=16, color=DEEP, bold=True)
add_bullets(s, Inches(0.5), Inches(4.3), Inches(12.3), Inches(2.0), [
    ("(a) The energy transition runs through critical minerals.", True),
    "Cobalt + nickel for batteries · copper for grid · REEs for wind turbines · "
    "platinum for fuel cells. The IEA estimates 4–6× demand growth by 2040.",
    ("(b) Production is concentrated — and concentration overlaps with "
     "high-risk jurisdictions.", True),
    "The US 2022 Critical Minerals List, the EU Critical Raw Materials Act (2024), "
    "and the IRA all flag the same supply-concentration risk. For an operator "
    "like Glencore, that is the operational reality, not an abstraction.",
], size=12)

add_text(s, Inches(0.5), Inches(6.55), Inches(12.3), Inches(0.35),
          "Sources: IEA Critical Minerals Outlook 2024 (iea.org); "
          "USGS Mineral Commodity Summaries 2024 (pubs.usgs.gov/periodicals/mcs2024); "
          "USGS 2022 Critical Minerals List; EU Critical Raw Materials Act 2024.",
          size=9, color=TEXT_GREY, italic=True)
add_footer(s, 3, 9)
add_speaker_notes(s,
    "[Speaker 2, 1 min 30] The energy transition isn't just a story about "
    "renewable electricity — it's a mineral story. The IEA forecasts 4 to 6 "
    "times demand growth for cobalt, nickel, copper, and rare earths by 2040 "
    "under a net-zero scenario. But supply is highly concentrated: 74 percent "
    "of cobalt comes from the DRC, almost half of nickel from Indonesia, "
    "72 percent of platinum from South Africa. And here's the critical "
    "geopolitical insight — the US 2022 Critical Minerals List, the EU's "
    "Critical Raw Materials Act, and the Inflation Reduction Act are all "
    "responding to the same problem: every Western government is now treating "
    "supply-chain concentration as a national-security risk. For an operator "
    "like Glencore, that's not a thought experiment — it's where they actually "
    "buy and sell every day.")


# ========================================================================
# Slide 4 — Supply concentration meets CAHRA
# ========================================================================
s = prs.slides.add_slide(BLANK)
add_header(s, "The CAHRA × Critical Minerals overlap",
            "Where the energy transition's supply chain meets Glencore's high-risk list")

# Build a small table of overlap evidence
table_data = [
    ("Commodity", "Top producer", "Share", "CAHRA", "Critical?"),
    ("Cobalt", "DRC", "74%", "All regions", "Yes"),
    ("Nickel", "Indonesia", "48%", "All regions", "Yes"),
    ("Platinum", "South Africa", "72%", "—", "Yes"),
    ("Manganese alloys", "South Africa / Gabon", "36% + 23%", "—", "Yes"),
    ("Ferrochrome", "South Africa", "44%", "—", "Yes"),
    ("Aluminum", "China (smelting)", "59%", "Xinjiang", "Yes"),
    ("Zinc", "China", "33%", "Xinjiang", "Yes"),
    ("Copper", "Chile / Peru / DRC", "23 + 10 + 13%", "DRC: All regions", "—"),
]
# Manual table
left = Inches(0.5); top = Inches(1.5); col_w = [Inches(2.4), Inches(3.0),
    Inches(2.0), Inches(2.8), Inches(1.8)]
total_w = sum(c for c in col_w)
row_h = Inches(0.42)
for r_i, row in enumerate(table_data):
    is_header = r_i == 0
    x = left
    for c_i, val in enumerate(row):
        cell = add_rect(s, x, top + row_h * r_i, col_w[c_i], row_h,
                         DEEP if is_header else (LIGHT if r_i % 2 == 1 else WHITE),
                         line=DEEP if is_header else TEXT_GREY)
        add_text(s, x, top + row_h * r_i, col_w[c_i], row_h, val,
                  size=12, color=WHITE if is_header else TEXT_DARK,
                  bold=is_header, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        x += col_w[c_i]

# Insight callout
add_rect(s, Inches(0.5), Inches(5.4), Inches(12.3), Inches(1.0), TEAL)
add_text(s, Inches(0.7), Inches(5.55), Inches(11.9), Inches(0.7),
          "Of the 8 USGS-Critical Minerals in Glencore's portfolio, every single one has a top-3 "
          "producer that touches the CAHRA list. The energy transition cannot be decoupled from "
          "high-risk jurisdictions — managing environmental risk in those countries is non-optional.",
          size=13, color=WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE)

add_text(s, Inches(0.5), Inches(6.55), Inches(12.3), Inches(0.35),
          "Sources: USGS MCS 2024; USGS 2022 Critical Minerals List "
          "(usgs.gov/news/national-news-release/us-geological-survey-releases-2022-list-critical-minerals); "
          "Glencore CAHRA List 2025 (updated 27.02.2025).",
          size=9, color=TEXT_GREY, italic=True)
add_footer(s, 4, 9)
add_speaker_notes(s,
    "[Speaker 2, 1 min 30] If we map Glencore's CAHRA list against the US "
    "2022 Critical Minerals List, the overlap is striking. Cobalt — 74 percent "
    "DRC, all of which is CAHRA-flagged. Nickel — 48 percent Indonesia, "
    "all CAHRA. Platinum — 72 percent South Africa. Aluminum smelting — "
    "59 percent China, with Xinjiang flagged. The point isn't that any "
    "specific country is bad; it's that the geographic concentration of "
    "energy-transition minerals systematically pushes Western buyers into "
    "jurisdictions where environmental governance is weak or contested. "
    "That's the operational gap our tool addresses. Now I'll hand to "
    "[Speaker 1] for the tool itself.")


# ========================================================================
# Slide 5 — The tool overview (screenshot)
# ========================================================================
s = prs.slides.add_slide(BLANK)
add_header(s, "The tool",
            "Pivot-style filter → ranked risks · Likelihood × Severity heatmap · drill-down audit trail")

# Add screenshot (left half)
img = ASSETS / "01_dashboard.png"
if img.exists():
    s.shapes.add_picture(str(img), Inches(0.4), Inches(1.3), height=Inches(5.5))

# Right side commentary
add_text(s, Inches(8.0), Inches(1.4), Inches(4.9), Inches(0.4),
          "What it does", size=16, color=DEEP, bold=True)
add_bullets(s, Inches(8.0), Inches(1.85), Inches(4.9), Inches(4.5), [
    "Filters: commodity, country, process, risk type — top producers surfaced first",
    "8 priority risks (15 total) scored as Likelihood × Severity = Overall (1–25)",
    "Bucketed Low / Moderate / High / Critical with consistent palette across "
    "the table, heatmap, choropleth, and Excel companion",
    "Drill-down panel exposes raw indicator + source URL for every score → "
    "auditable for CSRD / CSDDD",
    "8 tabs: Dashboard · Map · Comparative Analysis · Risk Library · "
    "SCDD Tiers · User Guide · Methodology · Data Sources",
], size=11)
add_text(s, Inches(0.5), Inches(6.6), Inches(12.3), Inches(0.3),
          "Live tool: streamlit.app  ·  Repo: github.com/mnmarkovitz/glencore_enviro_risk_tool",
          size=9, color=TEXT_GREY, italic=True)
add_footer(s, 5, 9)
add_speaker_notes(s,
    "[Speaker 1, 1 min] This is the tool. An analyst opens it, picks a "
    "commodity in the sidebar — let's say cobalt — and the country "
    "dropdown automatically prioritizes the top producers from the USGS "
    "Mineral Commodity Summaries. They pick a process — mining, refining, "
    "smelting, recycling, or marketing — and they get back a ranked table "
    "of every environmental risk that applies, plus a 5-by-5 Likelihood-"
    "by-Severity heatmap. Click any row and you see the raw indicator value "
    "with its source URL, so an audit can trace every number back to its "
    "public data point.")


# ========================================================================
# Slide 6 — Methodology
# ========================================================================
s = prs.slides.add_slide(BLANK)
add_header(s, "Methodology",
            "Reproducible scoring from public datasets · No analyst gut-feel")

# Formulas
add_rect(s, Inches(0.5), Inches(1.5), Inches(8.5), Inches(2.5), LIGHT)
add_text(s, Inches(0.7), Inches(1.65), Inches(8.1), Inches(0.4),
          "Two formulas", size=14, color=DEEP, bold=True)
add_text(s, Inches(0.7), Inches(2.1), Inches(8.1), Inches(0.5),
          "Likelihood = 0.4 × Process Intrinsic + 0.6 × Country Hazard    →   1–5",
          size=14, color=TEXT_DARK, font="Consolas")
add_text(s, Inches(0.7), Inches(2.55), Inches(8.1), Inches(0.5),
          "Severity   = 0.5 × Ecological Sensitivity + 0.5 × Regulatory Strict.   →   1–5",
          size=14, color=TEXT_DARK, font="Consolas")
add_text(s, Inches(0.7), Inches(3.05), Inches(8.1), Inches(0.5),
          "Overall    = Likelihood × Severity              →   1–25",
          size=14, color=TEXT_DARK, font="Consolas")
add_text(s, Inches(0.7), Inches(3.55), Inches(8.1), Inches(0.4),
          "Buckets: 1–4 Low · 5–9 Moderate · 10–14 High · 15–25 Critical",
          size=11, color=TEXT_GREY, italic=True)

# Bucket strip
def pill(slide, x, y, w, h, label, color):
    add_rect(slide, x, y, w, h, color)
    add_text(slide, x, y, w, h, label, size=11, color=WHITE, bold=True,
              align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

pill(s, Inches(9.3), Inches(1.5), Inches(0.85), Inches(0.35), "Low", GREEN)
pill(s, Inches(10.2), Inches(1.5), Inches(0.85), Inches(0.35), "Moderate", AMBER)
pill(s, Inches(11.1), Inches(1.5), Inches(0.85), Inches(0.35), "High", ORANGE)
pill(s, Inches(12.0), Inches(1.5), Inches(0.85), Inches(0.35), "Critical", RED)

# Why these weights
add_text(s, Inches(0.5), Inches(4.3), Inches(12.3), Inches(0.4),
          "Why country weight > process weight (0.6 vs 0.4)?",
          size=14, color=DEEP, bold=True)
add_text(s, Inches(0.5), Inches(4.7), Inches(12.3), Inches(1.0),
          "Process determines whether a risk is possible at all (no tailings in trading), but country "
          "context determines whether a capable process actually causes harm. Two copper mines — Chile's "
          "Atacama and Zambia's Copperbelt — have the same Process Intrinsic score for water depletion "
          "(5), but very different realized risk: Aqueduct rates Atacama 5 (Extremely High) vs Zambia 2.",
          size=12, color=TEXT_DARK)

# Data sources strip
add_text(s, Inches(0.5), Inches(5.7), Inches(12.3), Inches(0.4),
          "Public datasets feeding the scores",
          size=14, color=DEEP, bold=True)
add_text(s, Inches(0.5), Inches(6.05), Inches(12.3), Inches(0.5),
          "WRI Aqueduct · Yale EPI 2024 · WHO PM2.5 DB · IUCN Red List · WDPA · Global Forest Watch · "
          "Global Tailings Portal · USGS MRDS · USGS Critical Minerals Atlas · Global Energy Monitor · "
          "ISRIC SoilGrids · World Bank WGI · INFORM Risk · Glencore CAHRA List 2025",
          size=10, color=TEXT_GREY, italic=True)

add_text(s, Inches(0.5), Inches(6.55), Inches(12.3), Inches(0.35),
          "All weights and bucket thresholds editable in scoring_weights.csv. "
          "Full methodology: github.com/mnmarkovitz/glencore_enviro_risk_tool/blob/main/docs/METHODOLOGY.md",
          size=9, color=TEXT_GREY, italic=True)
add_footer(s, 6, 9)
add_speaker_notes(s,
    "[Speaker 1, 1 min] Two formulas. Likelihood is 40 percent process "
    "intensity — does the process even cause this risk — and 60 percent "
    "country hazard, drawn from a specific public dataset for each risk: "
    "Aqueduct for water, IUCN for species, GFW for deforestation, "
    "SoilGrids for soil, and so on. Severity is half ecological sensitivity, "
    "half regulatory strictness — because the tool measures penalty exposure, "
    "not pure ecological damage. Overall is L times S, bucketed into Low, "
    "Moderate, High, and Critical. Importantly, every single weight is in an "
    "editable CSV — Glencore can change the balance whenever they want without "
    "touching code. I'll hand to [Speaker 2] for the case study.")


# ========================================================================
# Slide 7 — Case study: DRC × Cobalt × Mining
# ========================================================================
s = prs.slides.add_slide(BLANK)
add_header(s, "Case study — DRC × Cobalt × Mining",
            "How a Glencore Responsible Sourcing analyst uses the tool in practice")

# Map screenshot left
img = ASSETS / "02_map.png"
if img.exists():
    s.shapes.add_picture(str(img), Inches(0.4), Inches(1.3), height=Inches(3.5))

# Text right
add_text(s, Inches(0.5), Inches(4.95), Inches(12.3), Inches(0.4),
          "What the tool surfaces (filter: Cobalt + DRC + Mining)",
          size=14, color=DEEP, bold=True)
add_bullets(s, Inches(0.5), Inches(5.35), Inches(6.0), Inches(1.7), [
    "🚩 CAHRA flag (All regions) → automatic Tier 1 → Tier 2 escalation",
    "Tailings — Critical (TSF count + GISTM consequence class)",
    "Soil pollution — Critical (acidic Oxisols + EPI Heavy Metals)",
    "Biodiversity loss — Critical (590 IUCN-listed species; high deforestation)",
], size=11)
add_bullets(s, Inches(7.0), Inches(5.35), Inches(5.8), Inches(1.7), [
    "Each row's drill-down shows raw + normalized scores with source URL",
    "Risk Library tab pre-loads SAQ KPIs (e.g. tailings GISTM conformance %, "
    "seepage rate) → directly into Glencore's Step 2B questionnaire",
    "Likely supplier types ranked: Earth moving · Hazardous chemicals · "
    "Waste disposal — narrows the SAQ scope",
], size=11)

add_text(s, Inches(0.5), Inches(6.55), Inches(12.3), Inches(0.35),
          "Sources: USGS MCS 2024; Glencore CAHRA List 2025; ISRIC SoilGrids 2.0; "
          "Yale EPI 2024; IUCN Red List API; Global Forest Watch.",
          size=9, color=TEXT_GREY, italic=True)
add_footer(s, 7, 9)
add_speaker_notes(s,
    "[Speaker 2, 2 min] Concrete case study. Suppose an analyst gets a "
    "request to onboard a new cobalt supplier from the DRC. They open "
    "the tool, filter to Cobalt — DRC — Mining. Immediately three things "
    "happen. First, the CAHRA flag fires, automatically pushing this "
    "supplier from Tier 1 to Tier 2 of Glencore's SCDD procedure — that's "
    "non-discretionary. Second, the ranked table shows three Critical "
    "risks: tailings, soil pollution, and biodiversity loss. Each is "
    "audit-able — tailings comes from the Global Tailings Portal, soil "
    "pollution from ISRIC SoilGrids — DRC has highly acidic tropical "
    "soils that mobilize heavy metals — and biodiversity from IUCN Red "
    "List counts. Third, and this is the most operationally useful part: "
    "the Risk Library tab pre-loads the SAQ KPIs the analyst should ask "
    "the supplier — GISTM conformance, seepage rate in liters per day, "
    "heavy-metal soil concentrations. It also surfaces the likely "
    "supplier-type categories: earth moving, hazardous-chemical supplier, "
    "waste disposal. This collapses what was a multi-day desk-research "
    "exercise into about 10 minutes — and every number is auditable.")


# ========================================================================
# Slide 8 — Integration with Glencore SCDD workflow
# ========================================================================
s = prs.slides.add_slide(BLANK)
add_header(s, "Where this fits — Glencore's SCDD Tiers",
            "Tool automates Tier 1, scopes Tier 2, accelerates Tiers 3–4")

tiers = [
    ("Tier 1", "OSDR — desktop research", GREEN,
     "AUTOMATED by tool",
     "Step 2A: scoping",
     "Public data: Aqueduct, EPI, IUCN, WDPA, GTP, SoilGrids, GEM, USGS MRDS"),
    ("Tier 2", "SAQ — Supplier Questionnaire", TEAL,
     "Tool scopes the SAQ",
     "Step 2B & 2C",
     "Tool's Risk Library + KPI list → directly into the SAQ template"),
    ("Tier 3", "Onsite / OGA — On-the-ground assessment", ORANGE,
     "Tool ranks priorities",
     "Step 3.1.5",
     "Critical-bucket rows define the onsite agenda; sampling priorities"),
    ("Tier 4", "CAP — Corrective Action Plan", RED,
     "Tool identifies milestones",
     "Step 3.1.7",
     "KPIs become CAP milestones; ongoing monitoring tracks improvement"),
]
left = Inches(0.5); top = Inches(1.45); h = Inches(1.18); gap = Inches(0.08)
for i, (tier, name, color, role, step, content) in enumerate(tiers):
    y = top + (h + gap) * i
    add_rect(s, left, y, Inches(1.5), h, color)
    add_text(s, left, y, Inches(1.5), Inches(0.45), tier,
              size=18, color=WHITE, bold=True, align=PP_ALIGN.CENTER,
              anchor=MSO_ANCHOR.MIDDLE)
    add_text(s, left, y + Inches(0.5), Inches(1.5), Inches(0.6), role,
              size=10, color=WHITE, align=PP_ALIGN.CENTER, italic=True)
    # Right side
    add_rect(s, left + Inches(1.55), y, Inches(11.1), h, LIGHT if i % 2 == 0 else WHITE)
    add_text(s, left + Inches(1.7), y + Inches(0.05), Inches(8), Inches(0.4),
              name, size=14, color=DEEP, bold=True)
    add_text(s, left + Inches(9.3), y + Inches(0.05), Inches(3.1), Inches(0.4),
              step, size=11, color=TEXT_GREY, italic=True, align=PP_ALIGN.RIGHT)
    add_text(s, left + Inches(1.7), y + Inches(0.45), Inches(10.7), Inches(0.7),
              content, size=11, color=TEXT_DARK)

add_text(s, Inches(0.5), Inches(6.55), Inches(12.3), Inches(0.35),
          "Sources: Glencore SCDD Procedure for Metals & Minerals (2024); "
          "OECD DDG (3rd ed.); RMI Supply Chain DD Plus Module (April 2025).",
          size=9, color=TEXT_GREY, italic=True)
add_footer(s, 8, 9)
add_speaker_notes(s,
    "[Speaker 2, 1 min] The tool sits cleanly inside Glencore's existing "
    "SCDD workflow. Their procedure follows the OECD's five-step framework "
    "and breaks operational engagement into four tiers. Tier 1 is "
    "open-source desktop research — that's what we automate. Tier 2 is "
    "the supplier questionnaire — our Risk Library tab pre-populates the "
    "questions for that. Tier 3 is the onsite visit — our Critical-bucket "
    "rows tell the assessor where to focus. Tier 4 is the corrective "
    "action plan — our KPIs become CAP milestones. The point is: nothing "
    "in Glencore's existing process changes. The tool just makes the "
    "first three tiers faster and more reproducible.")


# ========================================================================
# Slide 9 — Roadmap, handover & references
# ========================================================================
s = prs.slides.add_slide(BLANK)
add_header(s, "Status & roadmap",
            "Handover-ready · public repo · permanent Streamlit URL")

# Two columns
add_text(s, Inches(0.5), Inches(1.5), Inches(6.0), Inches(0.4),
          "What's shipping today", size=15, color=DEEP, bold=True)
add_bullets(s, Inches(0.5), Inches(1.95), Inches(6.0), Inches(2.6), [
    "Public repo — github.com/mnmarkovitz/glencore_enviro_risk_tool",
    "Live Streamlit app — public URL via Streamlit Community Cloud",
    "18-sheet Excel companion (Quick_Reference.xlsx) for offline analysts",
    "Full handover playbook for Glencore IT (Dockerfile + docs/HANDOVER.md)",
    ".gitignore protects confidential supplier CSV from public push",
], size=11)

add_text(s, Inches(7.0), Inches(1.5), Inches(5.8), Inches(0.4),
          "Roadmap", size=15, color=DEEP, bold=True)
add_bullets(s, Inches(7.0), Inches(1.95), Inches(5.8), Inches(2.6), [
    "Glencore swaps in their counterparty database for the supplier layer",
    "Sub-national CAHRA region resolution (Aqueduct already at province level)",
    "Live Aqueduct API for water-pollution UCW + CEP indicators",
    "Translate scoring engine into Power BI / DAX for Glencore BI stack",
    "Annual data refresh cycle with automated CI",
], size=11)

# References
add_text(s, Inches(0.5), Inches(4.7), Inches(12.3), Inches(0.4),
          "Selected references",
          size=14, color=DEEP, bold=True)
refs = [
    "OECD (2016). Due Diligence Guidance for Responsible Supply Chains of Minerals from "
    "Conflict-Affected and High-Risk Areas, 3rd ed. oecd.org/daf/inv/mne/mining.htm",
    "IEA (2024). Global Critical Minerals Outlook 2024. iea.org",
    "USGS (2024). Mineral Commodity Summaries 2024. pubs.usgs.gov/periodicals/mcs2024",
    "USGS (2022). 2022 List of Critical Minerals. usgs.gov/news/national-news-release/"
    "us-geological-survey-releases-2022-list-critical-minerals",
    "Glencore (2024). Supply Chain Due Diligence Procedure — Metals and Minerals.",
    "Glencore (2025). CAHRA List 2025 (updated 27.02.2025).",
    "Yale EPI 2024 · WRI Aqueduct 4.0 · WHO Ambient Air Quality DB · IUCN Red List · "
    "WDPA · ISRIC SoilGrids · Global Energy Monitor · Global Tailings Portal · "
    "ENCORE · IFC EHS Guidelines · INFORM Risk Index 2024.",
]
add_bullets(s, Inches(0.5), Inches(5.05), Inches(12.3), Inches(2.0), refs, size=9.5)

add_footer(s, 9, 9)
add_speaker_notes(s,
    "[Speaker 1 closing, 30 sec] To wrap: the tool is on a public GitHub "
    "repo, deployed to a permanent Streamlit URL, ships with an 18-sheet "
    "Excel companion for analysts who don't want to run a web tool, and "
    "comes with a Docker container plus a written handover playbook for "
    "Glencore's IT team. Everything is editable in CSVs — no code skills "
    "required. We aimed to build something that survives the handover and "
    "stays useful as the geopolitical and energy-transition context keeps "
    "evolving. Happy to take questions.")


prs.save(OUT)
print(f"✓ Wrote {OUT.name}  ({OUT.stat().st_size / 1024:.0f} KB)")
print(f"  Location: {OUT}")
