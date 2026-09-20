# coding: utf-8
"""
AeroCPI + AeroGuide — Official SIH 2026 6-Slide Pitch Deck Generator
Team: BuzzCodeX | Problem Statement: SIH26056 | Theme: Smart Automation

Generates high-fidelity 16:9 widescreen PowerPoint deck preserving official SIH structure,
mint/light background aesthetic, large serif headers, infographic cards, and real prototype screenshots.
"""

import os
import sys
import qrcode
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# -------------------------------------------------------------
# Color Palette Constants
# -------------------------------------------------------------
BG_MINT = RGBColor(244, 251, 247)         # #F4FBF7 - Light mint/aqua background
CARD_BG = RGBColor(255, 255, 255)         # #FFFFFF - Pure white card surface
CARD_BORDER = RGBColor(209, 231, 221)     # #D1E7DD - Soft mint border
NAVY_PRIMARY = RGBColor(11, 37, 69)       # #0B2545 - Official SIH Deep Navy
NAVY_DARK = RGBColor(15, 23, 42)          # #0F172A - Slate 900
TEXT_MUTED = RGBColor(71, 85, 105)        # #475569 - Slate 600
TEXT_DIM = RGBColor(100, 116, 139)        # #64748B - Slate 500

GREEN_ACCENT = RGBColor(5, 150, 105)      # #059669 - Emerald Green
GREEN_LIGHT = RGBColor(209, 250, 229)     # #D1FAE5 - Mint Badge BG
ORANGE_ACCENT = RGBColor(217, 119, 6)     # #D97706 - Amber Saffron
ORANGE_LIGHT = RGBColor(254, 243, 199)    # #FEF3C7 - Amber Badge BG
PURPLE_ACCENT = RGBColor(99, 102, 241)    # #6366F1 - Indigo Violet
PURPLE_LIGHT = RGBColor(238, 242, 255)    # #EEF2FF - Purple Badge BG
BLUE_ACCENT = RGBColor(2, 132, 199)       # #0284C7 - Cyan Sky
RED_ACCENT = RGBColor(225, 29, 72)        # #E11D48 - Rose Red
RED_LIGHT = RGBColor(255, 228, 230)       # #FFE4E6 - Red Badge BG

FONT_SERIF = "Georgia"
FONT_SANS = "Calibri"
FONT_MONO = "Consolas"

# -------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------
def create_qr(data: str, filename: str) -> str:
    """Generates a clean QR code image and returns its path."""
    os.makedirs("scratch_qr", exist_ok=True)
    path = os.path.join("scratch_qr", filename)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0B2545", back_color="#FFFFFF")
    img.save(path)
    return path

def add_header(slide, title_text: str, subtitle_text: str = None, category_badge: str = "SIH26056 · SMART AUTOMATION"):
    """Adds standard SIH 2026 header across content slides."""
    # Top SIH Bar background
    top_bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(0), Inches(0), Inches(13.333), Inches(0.42)
    )
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = NAVY_PRIMARY
    top_bar.line.fill.background()

    tb = top_bar.text_frame
    tb.word_wrap = True
    tb.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tb.paragraphs[0]
    p.text = "SMART INDIA HACKATHON 2026  |  TEAM BUZZCODEX  |  PROBLEM STATEMENT ID: SIH26056  |  THEME: SMART AUTOMATION"
    p.font.name = FONT_SANS
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.alignment = PP_ALIGN.CENTER

    # Slide Title Box
    title_box = slide.shapes.add_textbox(Inches(0.6), Inches(0.55), Inches(9.5), Inches(0.85))
    tf = title_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p_title = tf.paragraphs[0]
    p_title.text = title_text
    p_title.font.name = FONT_SERIF
    p_title.font.size = Pt(21)
    p_title.font.bold = True
    p_title.font.color.rgb = NAVY_PRIMARY

    if subtitle_text:
        p_sub = tf.add_paragraph()
        p_sub.text = subtitle_text
        p_sub.font.name = FONT_SANS
        p_sub.font.size = Pt(10.5)
        p_sub.font.color.rgb = TEXT_MUTED
        p_sub.space_before = Pt(2)

    # Right Badge Box
    badge_box = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(10.2), Inches(0.55), Inches(2.533), Inches(0.42)
    )
    badge_box.fill.solid()
    badge_box.fill.fore_color.rgb = GREEN_LIGHT
    badge_box.line.color.rgb = GREEN_ACCENT
    badge_box.line.width = Pt(1)
    
    b_tf = badge_box.text_frame
    b_tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    bp = b_tf.paragraphs[0]
    bp.text = category_badge
    bp.font.name = FONT_SANS
    bp.font.size = Pt(9.5)
    bp.font.bold = True
    bp.font.color.rgb = GREEN_ACCENT
    bp.alignment = PP_ALIGN.CENTER

def add_card(slide, left: float, top: float, width: float, height: float, bg_color=CARD_BG, border_color=CARD_BORDER, border_width=1):
    """Adds a soft rounded card container."""
    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    if border_color:
        card.line.color.rgb = border_color
        card.line.width = Pt(border_width)
    else:
        card.line.fill.background()
    return card

def add_footer_statement(slide, statement: str, left: float = 0.6, top: float = 6.9, width: float = 12.133, height: float = 0.38):
    """Adds standardized bottom take-away banner."""
    bar = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY_PRIMARY
    bar.line.fill.background()
    
    tf = bar.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = statement
    p.font.name = FONT_SANS
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.alignment = PP_ALIGN.CENTER

# -------------------------------------------------------------
# Main Deck Builder
# -------------------------------------------------------------
def build_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Generate QR Codes
    qr_mospi = create_qr("https://mospi.gov.in", "qr_mospi.png")
    qr_dgca = create_qr("https://www.dgca.gov.in", "qr_dgca.png")
    qr_sih = create_qr("https://sih.gov.in", "qr_sih.png")
    qr_audit = create_qr("https://github.com/priyanshu5ingh/AeroCPI", "qr_audit.png")

    # =========================================================
    # SLIDE 1: TITLE / PROBLEM
    # =========================================================
    slide1 = prs.slides.add_slide(blank_layout)
    bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = BG_MINT
    bg1.line.fill.background()

    # Top SIH Header Banner
    s1_top = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(0.48))
    s1_top.fill.solid()
    s1_top.fill.fore_color.rgb = NAVY_PRIMARY
    s1_top.line.fill.background()
    s1_tb = s1_top.text_frame
    s1_tb.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = s1_tb.paragraphs[0]
    p.text = "SMART INDIA HACKATHON 2026  ·  GOVERNMENT OF INDIA  ·  MINISTRY OF EDUCATION & AICTE"
    p.font.name = FONT_SANS
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)
    p.alignment = PP_ALIGN.CENTER

    # Main Hero Title Box (Center Left)
    hero_card = add_card(slide1, 0.6, 0.75, 12.133, 3.4, CARD_BG, CARD_BORDER)
    
    tb = slide1.shapes.add_textbox(Inches(0.9), Inches(0.95), Inches(11.5), Inches(3.0)).text_frame
    tb.word_wrap = True

    # Badges row
    p_meta = tb.paragraphs[0]
    p_meta.text = "PROBLEM STATEMENT ID: SIH26056  |  THEME: SMART AUTOMATION  |  CATEGORY: SOFTWARE"
    p_meta.font.name = FONT_SANS
    p_meta.font.size = Pt(11)
    p_meta.font.bold = True
    p_meta.font.color.rgb = GREEN_ACCENT

    # Main Title
    p_title = tb.add_paragraph()
    p_title.text = "REAL-TIME AIRFARE PRICE INDEX FOR INDIA"
    p_title.font.name = FONT_SERIF
    p_title.font.size = Pt(32)
    p_title.font.bold = True
    p_title.font.color.rgb = NAVY_PRIMARY
    p_title.space_before = Pt(8)

    # Subtitle
    p_sub = tb.add_paragraph()
    p_sub.text = "AeroCPI  +  AeroGuide"
    p_sub.font.name = FONT_SERIF
    p_sub.font.size = Pt(20)
    p_sub.font.bold = True
    p_sub.font.color.rgb = ORANGE_ACCENT
    p_sub.space_before = Pt(4)

    # Tagline
    p_tag = tb.add_paragraph()
    p_tag.text = "MEASURE THE MARKET.  EXPLAIN THE MOVEMENT.  GUIDE THE DECISION."
    p_tag.font.name = FONT_SANS
    p_tag.font.size = Pt(13)
    p_tag.font.bold = True
    p_tag.font.color.rgb = NAVY_DARK
    p_tag.space_before = Pt(8)

    # Team & Status
    p_team = tb.add_paragraph()
    p_team.text = "Developed by Team BuzzCodeX  |  36K+ Persisted Observations  |  140 Tier-1 Panel Cells  |  3 Live Ingestion Paths"
    p_team.font.name = FONT_SANS
    p_team.font.size = Pt(10.5)
    p_team.font.color.rgb = TEXT_MUTED
    p_team.space_before = Pt(6)

    # 3 Summary Foundation Cards
    card_w = 3.84
    gap = 0.3
    
    # Foundation Card 1
    add_card(slide1, 0.6, 4.35, card_w, 2.35, CARD_BG, CARD_BORDER)
    tb1 = slide1.shapes.add_textbox(Inches(0.8), Inches(4.5), Inches(3.44), Inches(2.05)).text_frame
    tb1.word_wrap = True
    p = tb1.paragraphs[0]
    p.text = "01 THE MARKET CHALLENGE"
    p.font.name = FONT_SANS
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ORANGE_ACCENT
    
    p = tb1.add_paragraph()
    p.text = "• 150M+ domestic air travellers face extreme price volatility across routes, carriers, and horizons.\n• Standard CPI captures lagged physical goods; airfares change continuously by minute and seat class.\n• Lack of high-frequency price indices leaves policymakers and travellers without real-time signals."
    p.font.name = FONT_SANS
    p.font.size = Pt(9.5)
    p.font.color.rgb = TEXT_MUTED
    p.space_before = Pt(4)

    # Foundation Card 2
    add_card(slide1, 0.6 + card_w + gap, 4.35, card_w, 2.35, CARD_BG, CARD_BORDER)
    tb2 = slide1.shapes.add_textbox(Inches(0.8 + card_w + gap), Inches(4.5), Inches(3.44), Inches(2.05)).text_frame
    tb2.word_wrap = True
    p = tb2.paragraphs[0]
    p.text = "02 DUAL-LAYER SOLUTION"
    p.font.name = FONT_SANS
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = GREEN_ACCENT
    
    p = tb2.add_paragraph()
    p.text = "• AeroCPI: Experimental economic airfare index using DGCA passenger weights & Jevons geometric aggregation.\n• AeroGuide: Consumer intelligence layer delivering explainable BOOK / WAIT / WATCH fare decisions.\n• 5A Log-Linear Econometric Decomposition: Carrier, Horizon, DOW, Seasonality, Route."
    p.font.name = FONT_SANS
    p.font.size = Pt(9.5)
    p.font.color.rgb = TEXT_MUTED
    p.space_before = Pt(4)

    # Foundation Card 3
    add_card(slide1, 0.6 + (card_w + gap)*2, 4.35, card_w, 2.35, CARD_BG, CARD_BORDER)
    tb3 = slide1.shapes.add_textbox(Inches(0.8 + (card_w + gap)*2), Inches(4.5), Inches(3.44), Inches(2.05)).text_frame
    tb3.word_wrap = True
    p = tb3.paragraphs[0]
    p.text = "03 SCIENTIFIC DISCIPLINE"
    p.font.name = FONT_SANS
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = PURPLE_ACCENT
    
    p = tb3.add_paragraph()
    p.text = "• Multi-Source Ingestion: Google Flights, EaseMyTrip Scrapy, Duffel API pilot.\n• Evidence-Gated ML Gate: Forecasting strictly locked (0/7 pairs) until longitudinal depth is proven.\n• Immutable Cryptographic Provenance: Every quote tied to SHA-256 raw HTML/JSON capture."
    p.font.name = FONT_SANS
    p.font.size = Pt(9.5)
    p.font.color.rgb = TEXT_MUTED
    p.space_before = Pt(4)

    # Disclaimer banner at very bottom
    add_footer_statement(
        slide1,
        "METHODOLOGY BOUNDARY: AeroCPI is an independent prototype measurement system for SIH 2026. It is not official MoSPI CPI.",
        0.6, 6.85, 12.133, 0.4
    )

    # =========================================================
    # SLIDE 2: PROPOSED SOLUTION
    # =========================================================
    slide2 = prs.slides.add_slide(blank_layout)
    bg2 = slide2.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg2.fill.solid()
    bg2.fill.fore_color.rgb = BG_MINT
    bg2.line.fill.background()

    add_header(
        slide2,
        "AEROCPI + AEROGUIDE: PROPOSED SOLUTION",
        "FROM BASIC SCRAPING TO AN AUDITABLE MEASUREMENT & CONSUMER INTELLIGENCE PLATFORM",
        "CORE INNOVATION"
    )

    # Left Column: Problem
    add_card(slide2, 0.6, 1.45, 3.4, 4.3, CARD_BG, CARD_BORDER)
    tb_prob = slide2.shapes.add_textbox(Inches(0.75), Inches(1.6), Inches(3.1), Inches(4.0)).text_frame
    tb_prob.word_wrap = True
    
    p = tb_prob.paragraphs[0]
    p.text = "THE PROBLEM WE SOLVED"
    p.font.name = FONT_SANS
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ORANGE_ACCENT

    p = tb_prob.add_paragraph()
    p.text = "01 Multi-Dimensional Volatility"
    p.font.name = FONT_SANS
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY
    p.space_before = Pt(8)

    p = tb_prob.add_paragraph()
    p.text = "Airfares vary simultaneously across route distance, airline carrier, departure date, booking lead time (T+1 to T+60), and booking platform."
    p.font.name = FONT_SANS
    p.font.size = Pt(9)
    p.font.color.rgb = TEXT_MUTED

    p = tb_prob.add_paragraph()
    p.text = "02 Cross-Source Market Dispersion"
    p.font.name = FONT_SANS
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY
    p.space_before = Pt(8)

    p = tb_prob.add_paragraph()
    p.text = "Different sources show materially different fare distributions (e.g. Google Flights vs EaseMyTrip median spread of 5.45%). A single source skews reality."
    p.font.name = FONT_SANS
    p.font.size = Pt(9)
    p.font.color.rgb = TEXT_MUTED

    p = tb_prob.add_paragraph()
    p.text = "03 The Need for Trust & Auditability"
    p.font.name = FONT_SANS
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY
    p.space_before = Pt(8)

    p = tb_prob.add_paragraph()
    p.text = "Travellers and researchers distrust opaque algorithms. Every decision must be mathematically comparable, explainable, and provable."
    p.font.name = FONT_SANS
    p.font.size = Pt(9)
    p.font.color.rgb = TEXT_MUTED

    # Center Column: Transformation Pipeline
    add_card(slide2, 4.15, 1.45, 3.6, 4.3, CARD_BG, CARD_BORDER)
    tb_pipe = slide2.shapes.add_textbox(Inches(4.3), Inches(1.6), Inches(3.3), Inches(4.0)).text_frame
    tb_pipe.word_wrap = True

    p = tb_pipe.paragraphs[0]
    p.text = "MEASUREMENT PIPELINE"
    p.font.name = FONT_SANS
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = GREEN_ACCENT

    pipeline_steps = [
        ("OBSERVE", "Multi-source extraction (Google, EaseMyTrip, Duffel)", GREEN_ACCENT),
        ("NORMALIZE", "Standardized 10-field canonical quote schema", BLUE_ACCENT),
        ("MEASURE", "Jevons geometric index + DGCA passenger weights", PURPLE_ACCENT),
        ("COMPARE", "Cross-source agreement lab & fare dispersion", ORANGE_ACCENT),
        ("GUIDE", "Explainable BOOK / WAIT / WATCH policy engine", GREEN_ACCENT),
        ("VERIFY", "SHA-256 provenance & calculation manifests", NAVY_PRIMARY),
    ]

    for title, desc, col in pipeline_steps:
        p = tb_pipe.add_paragraph()
        p.text = f"➔ {title}"
        p.font.name = FONT_SANS
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = col
        p.space_before = Pt(5)

        p = tb_pipe.add_paragraph()
        p.text = desc
        p.font.name = FONT_SANS
        p.font.size = Pt(8.5)
        p.font.color.rgb = TEXT_MUTED

    # Right Column: Real AeroGuide Prototype Screenshot Hero
    add_card(slide2, 7.9, 1.45, 4.833, 4.3, CARD_BG, CARD_BORDER)
    tb_hero = slide2.shapes.add_textbox(Inches(8.05), Inches(1.55), Inches(4.5), Inches(0.4)).text_frame
    p = tb_hero.paragraphs[0]
    p.text = "AEROGUIDE CONSUMER INTELLIGENCE LAYER"
    p.font.name = FONT_SANS
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = PURPLE_ACCENT

    guide_img_path = os.path.abspath("ssnew/01_GUIDE.png")
    if os.path.exists(guide_img_path):
        slide2.shapes.add_picture(
            guide_img_path,
            Inches(8.05), Inches(1.95), Inches(4.533), Inches(3.65)
        )

    # Bottom 3 Visual Pillars
    pillar_w = 3.84
    
    add_card(slide2, 0.6, 5.9, pillar_w, 0.85, CARD_BG, CARD_BORDER)
    p_tb1 = slide2.shapes.add_textbox(Inches(0.75), Inches(5.95), Inches(3.5), Inches(0.75)).text_frame
    p_tb1.word_wrap = True
    p = p_tb1.paragraphs[0]
    p.text = "🟢 1. MEASURE"
    p.font.name = FONT_SANS
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = GREEN_ACCENT
    p = p_tb1.add_paragraph()
    p.text = "National airfare movement across 10 trunk routes using DGCA passenger weighting."
    p.font.name = FONT_SANS
    p.font.size = Pt(8.5)
    p.font.color.rgb = TEXT_MUTED

    add_card(slide2, 0.6 + pillar_w + gap, 5.9, pillar_w, 0.85, CARD_BG, CARD_BORDER)
    p_tb2 = slide2.shapes.add_textbox(Inches(0.75 + pillar_w + gap), Inches(5.95), Inches(3.5), Inches(0.75)).text_frame
    p_tb2.word_wrap = True
    p = p_tb2.paragraphs[0]
    p.text = "🔵 2. EXPLAIN"
    p.font.name = FONT_SANS
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT
    p = p_tb2.add_paragraph()
    p.text = "Route & source pricing drivers decomposed via 5A log-linear attribution."
    p.font.name = FONT_SANS
    p.font.size = Pt(8.5)
    p.font.color.rgb = TEXT_MUTED

    add_card(slide2, 0.6 + (pillar_w + gap)*2, 5.9, pillar_w, 0.85, CARD_BG, CARD_BORDER)
    p_tb3 = slide2.shapes.add_textbox(Inches(0.75 + (pillar_w + gap)*2), Inches(5.95), Inches(3.5), Inches(0.75)).text_frame
    p_tb3.word_wrap = True
    p = p_tb3.paragraphs[0]
    p.text = "🟣 3. VERIFY"
    p.font.name = FONT_SANS
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = PURPLE_ACCENT
    p = p_tb3.add_paragraph()
    p.text = "SHA-256 provenance hashes & evidence-gated forecasting safeguards."
    p.font.name = FONT_SANS
    p.font.size = Pt(8.5)
    p.font.color.rgb = TEXT_MUTED

    add_footer_statement(
        slide2,
        "CORE DISTINCTION: We did not stop at scraping. We engineered a national measurement layer AND an auditable consumer decision engine.",
        0.6, 6.85, 12.133, 0.4
    )

    # =========================================================
    # SLIDE 3: TECHNICAL APPROACH
    # =========================================================
    slide3 = prs.slides.add_slide(blank_layout)
    bg3 = slide3.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg3.fill.solid()
    bg3.fill.fore_color.rgb = BG_MINT
    bg3.line.fill.background()

    add_header(
        slide3,
        "TECHNICAL APPROACH",
        "MULTI-SOURCE INGESTION ➔ CANONICAL OBSERVATION ➔ JEVONS INDEX ➔ EVIDENCE-GATED DECISIONS",
        "ARCHITECTURE"
    )

    # 6 Horizontal Architecture Stages
    stages = [
        ("01 SOURCE COLLECTION", "• Google Flights (Live)\n• EaseMyTrip (Scrapy)\n• Duffel API (Pilot)\n• NDC Partner Adapters", GREEN_ACCENT),
        ("02 CANONICAL SCHEMA", "• Route & Travel Date\n• Search Timestamp\n• Airline & Cabin\n• Base, Tax, Total Fare\n• Stops, Duration, APW", BLUE_ACCENT),
        ("03 QUALITY & PROVENANCE", "• Deduplication filter\n• Comparability rules\n• SHA-256 raw capture\n• Quote fingerprinting\n• Anomaly thresholds", PURPLE_ACCENT),
        ("04 INDEX ENGINE", "• 10 DGCA trunk routes\n• Jevons geometric mean\n• AeroCPI Headline\n• 5A Log-Linear model\n• Advance Horizon APW", ORANGE_ACCENT),
        ("05 AEROGUIDE ENGINE", "• Cross-Source Spread\n• Airline Intelligence\n• Flexible Dates Matrix\n• Decision Policy Engine\n• 11-Node Decision Trace", GREEN_ACCENT),
        ("06 AUDIT & EVIDENCE", "• Manifests\n• Reproducibility CLI\n• ML Gate: LOCKED\n• 301 backend tests\n• Immutable audit trail", NAVY_PRIMARY),
    ]

    st_w = 1.9
    st_gap = 0.14
    for i, (title, content, col) in enumerate(stages):
        left_pos = 0.6 + i * (st_w + st_gap)
        add_card(slide3, left_pos, 1.45, st_w, 2.7, CARD_BG, CARD_BORDER)
        
        strip = slide3.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left_pos), Inches(1.45), Inches(st_w), Inches(0.35))
        strip.fill.solid()
        strip.fill.fore_color.rgb = col
        strip.line.fill.background()
        st_p = strip.text_frame.paragraphs[0]
        st_p.text = title
        st_p.font.name = FONT_SANS
        st_p.font.size = Pt(8.5)
        st_p.font.bold = True
        st_p.font.color.rgb = RGBColor(255, 255, 255)
        st_p.alignment = PP_ALIGN.CENTER
        strip.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE

        tb = slide3.shapes.add_textbox(Inches(left_pos + 0.08), Inches(1.85), Inches(st_w - 0.16), Inches(2.2)).text_frame
        tb.word_wrap = True
        p = tb.paragraphs[0]
        p.text = content
        p.font.name = FONT_SANS
        p.font.size = Pt(8)
        p.font.color.rgb = NAVY_DARK
        p.space_before = Pt(2)

    # Lower Section: Real Screenshot & Math
    add_card(slide3, 0.6, 4.3, 5.9, 2.45, CARD_BG, CARD_BORDER)
    tb_sc = slide3.shapes.add_textbox(Inches(0.75), Inches(4.4), Inches(5.6), Inches(0.3)).text_frame
    p = tb_sc.paragraphs[0]
    p.text = "EVIDENCE: CROSS-SOURCE AGREEMENT & DECISION TRACE"
    p.font.name = FONT_SANS
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY

    trace_img_path = os.path.abspath("ssnew/05_SOURCE_AGREEMENT.png")
    if os.path.exists(trace_img_path):
        slide3.shapes.add_picture(
            trace_img_path,
            Inches(0.75), Inches(4.75), Inches(5.6), Inches(1.9)
        )

    # Right Card: Mathematical Formulation & Real Tech Stack
    add_card(slide3, 6.8, 4.3, 5.933, 2.45, CARD_BG, CARD_BORDER)
    tb_math = slide3.shapes.add_textbox(Inches(7.0), Inches(4.4), Inches(5.5), Inches(2.25)).text_frame
    tb_math.word_wrap = True
    
    p = tb_math.paragraphs[0]
    p.text = "MATHEMATICAL FORMULATION (JEVONS INDEX)"
    p.font.name = FONT_SANS
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = ORANGE_ACCENT

    p = tb_math.add_paragraph()
    p.text = "I_h = 100 · exp( Σ w_r · ln( J_{r,h} / 100 ) )"
    p.font.name = FONT_MONO
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY
    p.space_before = Pt(4)

    p = tb_math.add_paragraph()
    p.text = "Where w_r is DGCA annual route passenger share, and J_{r,h} is the geometric mean of observed fares for route r at advance purchase horizon h."
    p.font.name = FONT_SANS
    p.font.size = Pt(8.5)
    p.font.color.rgb = TEXT_MUTED
    p.space_before = Pt(2)

    p = tb_math.add_paragraph()
    p.text = "PRODUCTION TECH STACK & ENGINE INTEGRITY"
    p.font.name = FONT_SANS
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = GREEN_ACCENT
    p.space_before = Pt(6)

    p = tb_math.add_paragraph()
    p.text = "• Backend: Python 3.13, FastAPI (Async), SQLAlchemy 2.0, SQLite / PostgreSQL\n• Ingestion: Scrapy Crawler Layer, Playwright Browser Engine, REST API Client\n• Frontend: React 18, TypeScript, Tailwind CSS, Lucide Icons, Vitest (25/25 passed)\n• Test Suite: 301/301 Pytest Verified (Pre-4B Hardening & Provenance Audits)"
    p.font.name = FONT_SANS
    p.font.size = Pt(8)
    p.font.color.rgb = NAVY_DARK
    p.space_before = Pt(2)

    add_footer_statement(
        slide3,
        "ONE CANONICAL OBSERVATION MODEL  ·  MULTIPLE ACQUISITION PATHS  ·  ONE AUDITABLE MEASUREMENT CHAIN",
        0.6, 6.85, 12.133, 0.4
    )

    # =========================================================
    # SLIDE 4: FEASIBILITY & VIABILITY
    # =========================================================
    slide4 = prs.slides.add_slide(blank_layout)
    bg4 = slide4.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg4.fill.solid()
    bg4.fill.fore_color.rgb = BG_MINT
    bg4.line.fill.background()

    add_header(
        slide4,
        "FEASIBILITY & VIABILITY",
        "EMPIRICAL PROOF, OPERATIONAL STABILITY, RISK MITIGATIONS & SUSTAINABILITY MODEL",
        "VERIFIED METRICS"
    )

    # Left: Why It Is Buildable
    add_card(slide4, 0.6, 1.45, 3.6, 4.3, CARD_BG, CARD_BORDER)
    tb_b = slide4.shapes.add_textbox(Inches(0.75), Inches(1.6), Inches(3.3), Inches(4.0)).text_frame
    tb_b.word_wrap = True
    p = tb_b.paragraphs[0]
    p.text = "WHY IT IS BUILDABLE & ROBUST"
    p.font.name = FONT_SANS
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = GREEN_ACCENT

    buildable_checks = [
        ("✓ Multiple Ingestion Paths", "Web Scraping, Scrapy Spiders & REST APIs operational"),
        ("✓ Canonical Normalization", "10-field strict typing eliminates parser divergence"),
        ("✓ Source-Isolated Architecture", "Failure in one scraper never degrades other sources"),
        ("✓ Automated Daily Collection", "OS Task Scheduler runs daily batch pipelines"),
        ("✓ Cryptographic Provenance", "SHA-256 payload fingerprints on every raw observation"),
        ("✓ Frozen Methodology", "Mathematical index calculation is versioned & static"),
        ("✓ Evidence-Gated ML", "Forecast lock prevents false or unscientific signals"),
    ]
    for chk, desc in buildable_checks:
        p = tb_b.add_paragraph()
        p.text = chk
        p.font.name = FONT_SANS
        p.font.size = Pt(9)
        p.font.bold = True
        p.font.color.rgb = NAVY_PRIMARY
        p.space_before = Pt(4)
        p = tb_b.add_paragraph()
        p.text = desc
        p.font.name = FONT_SANS
        p.font.size = Pt(8)
        p.font.color.rgb = TEXT_MUTED

    # Middle: Real Current Evidence
    add_card(slide4, 4.4, 1.45, 4.0, 4.3, CARD_BG, CARD_BORDER)
    tb_e = slide4.shapes.add_textbox(Inches(4.55), Inches(1.6), Inches(3.7), Inches(4.0)).text_frame
    tb_e.word_wrap = True
    p = tb_e.paragraphs[0]
    p.text = "REAL CURRENT EMPIRICAL EVIDENCE"
    p.font.name = FONT_SANS
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = BLUE_ACCENT

    evidence_metrics = [
        ("36K+ Persisted Observations", "Real multi-source airfare quotes stored in database"),
        ("140 Tier-1 Panel Cells", "10 routes × 14 departure dates tracked longitudinally"),
        ("100% Multi-Source Coverage", "All 140 panel cells have ≥2 independently observed sources"),
        ("3 Observed Sources in Pilot", "Google Flights (Live), EaseMyTrip (Scrapy), Duffel (Pilot)"),
        ("0.98% Median Diff (DEL-BOM)", "High agreement between Google Flights & Duffel"),
        ("5.45% Median Spread", "Moderate dispersion between Google Flights & EaseMyTrip"),
    ]
    for met, desc in evidence_metrics:
        p = tb_e.add_paragraph()
        p.text = f"● {met}"
        p.font.name = FONT_SANS
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = NAVY_PRIMARY
        p.space_before = Pt(4)
        p = tb_e.add_paragraph()
        p.text = desc
        p.font.name = FONT_SANS
        p.font.size = Pt(8)
        p.font.color.rgb = TEXT_MUTED

    p = tb_e.add_paragraph()
    p.text = "🔒 ML FORECAST GATE: LOCKED"
    p.font.name = FONT_SANS
    p.font.size = Pt(9)
    p.font.bold = True
    p.font.color.rgb = RED_ACCENT
    p.space_before = Pt(8)
    p = tb_e.add_paragraph()
    p.text = "0/7 required 7-day longitudinal target pairs recorded. Forecast model locked by scientific safeguard."
    p.font.name = FONT_SANS
    p.font.size = Pt(8)
    p.font.color.rgb = TEXT_MUTED

    # Right: Risks & Mitigations
    add_card(slide4, 8.6, 1.45, 4.133, 4.3, CARD_BG, CARD_BORDER)
    tb_r = slide4.shapes.add_textbox(Inches(8.75), Inches(1.6), Inches(3.8), Inches(4.0)).text_frame
    tb_r.word_wrap = True
    p = tb_r.paragraphs[0]
    p.text = "RISKS ➔ ARCHITECTURAL MITIGATIONS"
    p.font.name = FONT_SANS
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = ORANGE_ACCENT

    risks = [
        ("Website UI Changes", "Modular adapters + Scrapy/Playwright decoupling"),
        ("Dynamic Carrier Pricing", "Fixed standard specifications (Economy, Direct Trunk)"),
        ("Source Disagreement", "Cross-Source Agreement Lab measuring spread"),
        ("Data Quality Anomaly", "Strict 10-point validation rules & fingerprinting"),
        ("Insufficient Temporal Depth", "Evidence-gated AI locks forecasting automatically"),
        ("Channel Access Restrictions", "Permission-aware collection + NDC direct API roadmap"),
    ]
    for r, m in risks:
        p = tb_r.add_paragraph()
        p.text = f"• {r}"
        p.font.name = FONT_SANS
        p.font.size = Pt(8.5)
        p.font.bold = True
        p.font.color.rgb = NAVY_PRIMARY
        p.space_before = Pt(4)
        p = tb_r.add_paragraph()
        p.text = f"  ➔ Mitigation: {m}"
        p.font.name = FONT_SANS
        p.font.size = Pt(8)
        p.font.color.rgb = GREEN_ACCENT

    # Bottom Sustainability Strip
    add_card(slide4, 0.6, 5.9, 12.133, 0.85, CARD_BG, CARD_BORDER)
    tb_s = slide4.shapes.add_textbox(Inches(0.8), Inches(5.95), Inches(11.7), Inches(0.75)).text_frame
    tb_s.word_wrap = True
    p = tb_s.paragraphs[0]
    p.text = "POTENTIAL SUSTAINABILITY & INSTITUTIONAL MODEL"
    p.font.name = FONT_SANS
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = PURPLE_ACCENT
    p = tb_s.add_paragraph()
    p.text = "Freemium Consumer Airfare Guide (AeroGuide)  ➔  Enterprise & OTA Market Analytics  ➔  Government / MoSPI Policy Dashboards  ➔  Academic Research API"
    p.font.name = FONT_SANS
    p.font.size = Pt(9)
    p.font.bold = True
    p.font.color.rgb = NAVY_DARK
    p.space_before = Pt(2)

    add_footer_statement(
        slide4,
        "HIGH SCALABILITY: Horizontally expandable across 100+ domestic airports, global NDC APIs, and hourly collection intervals.",
        0.6, 6.85, 12.133, 0.4
    )

    # =========================================================
    # SLIDE 5: IMPACT & BENEFITS
    # =========================================================
    slide5 = prs.slides.add_slide(blank_layout)
    bg5 = slide5.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg5.fill.solid()
    bg5.fill.fore_color.rgb = BG_MINT
    bg5.line.fill.background()

    add_header(
        slide5,
        "IMPACT & BENEFITS",
        "DELIVERING TANGIBLE VALUE TO POLICYMAKERS, TRAVELLERS & RESEARCHERS",
        "STAKEHOLDER VALUE"
    )

    stakeholders = [
        ("01 POLICY / STATISTICAL AGENCIES", GREEN_ACCENT, [
            "High-Frequency Measurement: Daily airfare indices supplementing lagged monthly CPI reports.",
            "Standardized Route Basket: DGCA passenger-weighted city pairs reflect actual mobility demand.",
            "Econometric 5A Attribution: Decomposes fare movements into carrier, horizon, and seasonal drivers.",
            "Audit Trail: Complete calculation manifests ready for institutional verification."
        ]),
        ("02 TRAVELLERS & CONSUMERS", BLUE_ACCENT, [
            "Real-Time Fare Context: Instant visibility into whether current fare (₹10,495) is elevated vs baseline.",
            "Cross-Source Spread: Unbiased comparison between Google Flights, EaseMyTrip, and API feeds.",
            "Nearby Alternative Dates: Calendar fare matrices showing cheapest departure windows.",
            "Actionable Advice: Clear BOOK / WAIT / WATCH guidance backed by 11-node decision trace."
        ]),
        ("03 RESEARCH & AVIATION INDUSTRY", PURPLE_ACCENT, [
            "Multi-Source Dataset: Canonical observations covering trunk corridors across multiple lead horizons.",
            "Market Dispersion Analysis: Measures yield management divergence between low-cost and full-service carriers.",
            "Longitudinal Panel Studies: Foundation for academic research in transportation pricing elasticity.",
            "Open Architecture: Modular Scrapy & API schemas enabling broader aviation study."
        ]),
    ]

    for i, (title, col, bullets) in enumerate(stakeholders):
        left_pos = 0.6 + i * (3.84 + 0.3)
        add_card(slide5, left_pos, 1.45, 3.84, 2.7, CARD_BG, CARD_BORDER)
        
        strip = slide5.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left_pos), Inches(1.45), Inches(3.84), Inches(0.35))
        strip.fill.solid()
        strip.fill.fore_color.rgb = col
        strip.line.fill.background()
        st_p = strip.text_frame.paragraphs[0]
        st_p.text = title
        st_p.font.name = FONT_SANS
        st_p.font.size = Pt(9)
        st_p.font.bold = True
        st_p.font.color.rgb = RGBColor(255, 255, 255)
        st_p.alignment = PP_ALIGN.CENTER
        strip.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE

        tb = slide5.shapes.add_textbox(Inches(left_pos + 0.12), Inches(1.85), Inches(3.6), Inches(2.2)).text_frame
        tb.word_wrap = True
        for b_idx, bullet in enumerate(bullets):
            p = tb.paragraphs[0] if b_idx == 0 else tb.add_paragraph()
            p.text = f"• {bullet}"
            p.font.name = FONT_SANS
            p.font.size = Pt(8.5)
            p.font.color.rgb = NAVY_DARK
            p.space_before = Pt(3)

    # Lower Section: UI Visual Anchor (Left: Guide, Right: Market)
    add_card(slide5, 0.6, 4.3, 5.9, 2.45, CARD_BG, CARD_BORDER)
    tb_g = slide5.shapes.add_textbox(Inches(0.75), Inches(4.4), Inches(5.6), Inches(0.3)).text_frame
    p = tb_g.paragraphs[0]
    p.text = "AEROGUIDE: CONSUMER DECISION HERO (BLR ➔ DEL · WATCH FARE)"
    p.font.name = FONT_SANS
    p.font.size = Pt(9)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY

    guide_mini = os.path.abspath("ssnew/01_GUIDE.png")
    if os.path.exists(guide_mini):
        slide5.shapes.add_picture(
            guide_mini,
            Inches(0.75), Inches(4.75), Inches(5.6), Inches(1.9)
        )

    add_card(slide5, 6.8, 4.3, 5.933, 2.45, CARD_BG, CARD_BORDER)
    tb_m = slide5.shapes.add_textbox(Inches(6.95), Inches(4.4), Inches(5.6), Inches(0.3)).text_frame
    p = tb_m.paragraphs[0]
    p.text = "AEROCPI: NATIONAL HEADLINE INDEX (96.21 · 5A ATTRIBUTION)"
    p.font.name = FONT_SANS
    p.font.size = Pt(9)
    p.font.bold = True
    p.font.color.rgb = ORANGE_ACCENT

    market_mini = os.path.abspath("ssnew/03_MARKET.png")
    if os.path.exists(market_mini):
        slide5.shapes.add_picture(
            market_mini,
            Inches(6.95), Inches(4.75), Inches(5.6), Inches(1.9)
        )

    add_footer_statement(
        slide5,
        "OBSERVE  ➔  UNDERSTAND  ➔  DECIDE  ➔  VERIFY  |  NOT JUST THE PRICE: THE SIGNAL, THE REASON, THE EVIDENCE.",
        0.6, 6.85, 12.133, 0.4
    )

    # =========================================================
    # SLIDE 6: RESEARCH & REFERENCES
    # =========================================================
    slide6 = prs.slides.add_slide(blank_layout)
    bg6 = slide6.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg6.fill.solid()
    bg6.fill.fore_color.rgb = BG_MINT
    bg6.line.fill.background()

    add_header(
        slide6,
        "RESEARCH & REFERENCES",
        "INSTITUTIONAL GROUNDING, METHODOLOGICAL PRECEDENTS & AUDIT PROVENANCE",
        "CREDIBILITY & AUDIT"
    )

    ref_top = [
        ("01 MoSPI / PIB (Government of India)", qr_mospi, "https://mospi.gov.in", "• Consumer Price Index (Base 2012=100) framework.\n• Transport & Communication subgroup CPI weights.\n• High-frequency experimental airfare measurement context.", GREEN_ACCENT),
        ("02 DGCA (Ministry of Civil Aviation)", qr_dgca, "https://www.dgca.gov.in", "• Monthly Domestic City-Pair Passenger Traffic Reports.\n• Route volume weights (w_r) derived from annual traffic.\n• Top 10 domestic trunk corridor basket definition.", BLUE_ACCENT),
        ("03 SIH 2026 (Ministry of Education)", qr_sih, "https://sih.gov.in", "• Problem Statement SIH26056: Real-time Airfare Price Index.\n• Theme: Smart Automation | Category: Software.\n• Team BuzzCodeX official prototype submission.", PURPLE_ACCENT),
    ]

    for i, (title, qr_img, url, desc, col) in enumerate(ref_top):
        left_pos = 0.6 + i * (3.84 + 0.3)
        add_card(slide6, left_pos, 1.45, 3.84, 2.35, CARD_BG, CARD_BORDER)
        
        strip = slide6.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left_pos), Inches(1.45), Inches(3.84), Inches(0.32))
        strip.fill.solid()
        strip.fill.fore_color.rgb = col
        strip.line.fill.background()
        st_p = strip.text_frame.paragraphs[0]
        st_p.text = title
        st_p.font.name = FONT_SANS
        st_p.font.size = Pt(8.5)
        st_p.font.bold = True
        st_p.font.color.rgb = RGBColor(255, 255, 255)
        st_p.alignment = PP_ALIGN.CENTER
        strip.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE

        if os.path.exists(qr_img):
            slide6.shapes.add_picture(
                qr_img,
                Inches(left_pos + 0.15), Inches(1.85), Inches(0.95), Inches(0.95)
            )

        tb = slide6.shapes.add_textbox(Inches(left_pos + 1.18), Inches(1.82), Inches(2.55), Inches(1.9)).text_frame
        tb.word_wrap = True
        p = tb.paragraphs[0]
        p.text = desc
        p.font.name = FONT_SANS
        p.font.size = Pt(8)
        p.font.color.rgb = NAVY_DARK

        p = tb.add_paragraph()
        p.text = url
        p.font.name = FONT_MONO
        p.font.size = Pt(7.5)
        p.font.bold = True
        p.font.color.rgb = col
        p.space_before = Pt(2)

    # 04 BLS / International Precedents
    add_card(slide6, 0.6, 3.95, 3.84, 2.75, CARD_BG, CARD_BORDER)
    strip4 = slide6.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(3.95), Inches(3.84), Inches(0.32))
    strip4.fill.solid()
    strip4.fill.fore_color.rgb = ORANGE_ACCENT
    strip4.line.fill.background()
    st_p4 = strip4.text_frame.paragraphs[0]
    st_p4.text = "04 METHODOLOGICAL PRECEDENTS"
    st_p4.font.name = FONT_SANS
    st_p4.font.size = Pt(8.5)
    st_p4.font.bold = True
    st_p4.font.color.rgb = RGBColor(255, 255, 255)
    st_p4.alignment = PP_ALIGN.CENTER
    strip4.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE

    tb4 = slide6.shapes.add_textbox(Inches(0.75), Inches(4.35), Inches(3.54), Inches(2.25)).text_frame
    tb4.word_wrap = True
    p = tb4.paragraphs[0]
    p.text = "• U.S. Bureau of Labor Statistics (BLS): Airline Fare Index sampling methodology across advance horizons.\n• Jevons Elementary Geometric Formula: Standard axiomatic price index formula mitigating substitution bias.\n• APW Sampling Set: Horizon analysis across {1, 7, 15, 30, 45, 60} days."
    p.font.name = FONT_SANS
    p.font.size = Pt(8)
    p.font.color.rgb = NAVY_DARK
    p.space_before = Pt(2)

    # 05 AeroCPI Internal Evidence
    add_card(slide6, 0.6 + 3.84 + 0.3, 3.95, 3.84, 2.75, CARD_BG, CARD_BORDER)
    strip5 = slide6.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6 + 3.84 + 0.3), Inches(3.95), Inches(3.84), Inches(0.32))
    strip5.fill.solid()
    strip5.fill.fore_color.rgb = NAVY_PRIMARY
    strip5.line.fill.background()
    st_p5 = strip5.text_frame.paragraphs[0]
    st_p5.text = "05 AEROCPI AUDIT EVIDENCE"
    st_p5.font.name = FONT_SANS
    st_p5.font.size = Pt(8.5)
    st_p5.font.bold = True
    st_p5.font.color.rgb = RGBColor(255, 255, 255)
    st_p5.alignment = PP_ALIGN.CENTER
    strip5.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE

    if os.path.exists(qr_audit):
        slide6.shapes.add_picture(
            qr_audit,
            Inches(0.6 + 3.84 + 0.3 + 0.15), Inches(4.35), Inches(0.95), Inches(0.95)
        )

    tb5 = slide6.shapes.add_textbox(Inches(0.6 + 3.84 + 0.3 + 1.18), Inches(4.35), Inches(2.55), Inches(2.25)).text_frame
    tb5.word_wrap = True
    p = tb5.paragraphs[0]
    p.text = "• 301/301 Pytest Verification Suite.\n• 25/25 Vitest UI Component Tests.\n• SHA-256 Provenance Hashes.\n• Immutable JSON Calculation Manifests.\n• Reproducibility Engine CLI."
    p.font.name = FONT_SANS
    p.font.size = Pt(8)
    p.font.color.rgb = NAVY_DARK

    # Right Card: Prominent Methodology Boundary
    add_card(slide6, 0.6 + (3.84 + 0.3)*2, 3.95, 3.84, 2.75, CARD_BG, CARD_BORDER)
    strip_b = slide6.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6 + (3.84 + 0.3)*2), Inches(3.95), Inches(3.84), Inches(0.32))
    strip_b.fill.solid()
    strip_b.fill.fore_color.rgb = RED_ACCENT
    strip_b.line.fill.background()
    st_pb = strip_b.text_frame.paragraphs[0]
    st_pb.text = "METHODOLOGICAL BOUNDARY & AUDIT RULE"
    st_pb.font.name = FONT_SANS
    st_pb.font.size = Pt(8.5)
    st_pb.font.bold = True
    st_pb.font.color.rgb = RGBColor(255, 255, 255)
    st_pb.alignment = PP_ALIGN.CENTER
    strip_b.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE

    tb_b = slide6.shapes.add_textbox(Inches(0.6 + (3.84 + 0.3)*2 + 0.15), Inches(4.35), Inches(3.54), Inches(2.25)).text_frame
    tb_b.word_wrap = True
    p = tb_b.paragraphs[0]
    p.text = "AeroCPI is an independent experimental measurement system developed for SIH 2026. It is NOT official CPI and does not replace official MoSPI statistics."
    p.font.name = FONT_SANS
    p.font.size = Pt(8.5)
    p.font.bold = True
    p.font.color.rgb = NAVY_PRIMARY
    p.space_before = Pt(2)

    p = tb_b.add_paragraph()
    p.text = "CORE AUDIT PRINCIPLE:"
    p.font.name = FONT_SANS
    p.font.size = Pt(8.5)
    p.font.bold = True
    p.font.color.rgb = RED_ACCENT
    p.space_before = Pt(6)

    p = tb_b.add_paragraph()
    p.text = "Never fabricate missing evidence. If longitudinal depth is insufficient, ML forecasting is strictly locked with clear disclosure."
    p.font.name = FONT_SANS
    p.font.size = Pt(8)
    p.font.color.rgb = TEXT_MUTED
    p.space_before = Pt(2)

    add_footer_statement(
        slide6,
        "AUDIT PRINCIPLE: NEVER FABRICATE MISSING EVIDENCE  |  OFFICIAL SIH 2026 SUBMISSION  |  TEAM BUZZCODEX",
        0.6, 6.85, 12.133, 0.4
    )

    # Save presentation
    output_pptx = "AeroCPI_SIH2026_Pitch_Deck.pptx"
    prs.save(output_pptx)
    print(f"[SUCCESS] Official SIH 2026 6-Slide Pitch Deck saved to: {output_pptx}")
    return output_pptx

if __name__ == "__main__":
    build_deck()
