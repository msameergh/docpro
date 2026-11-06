"""Landing page UI for DocPro. Presentation only: no extraction or validation logic."""
import base64
from pathlib import Path

import streamlit as st

LOGO_DIR = Path(__file__).parent / "Logo"
LOGO_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
              ".svg": "image/svg+xml", ".webp": "image/webp"}


def logo_mark() -> str:
    """HTML for the brand mark: the first image in the Logo folder, else the default gradient square."""
    try:
        files = sorted(f for f in LOGO_DIR.iterdir() if f.suffix.lower() in LOGO_TYPES)
        if files:
            data = base64.b64encode(files[0].read_bytes()).decode()
            return (f'<span class="dp-logo-img"><img alt="DocPro" '
                    f'src="data:{LOGO_TYPES[files[0].suffix.lower()]};base64,{data}"></span>')
    except OSError:
        pass
    return "<i></i>"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {--red: #ED2027; --red-d: #C8161D; --orange: #F58220; --yellow: #F5B700; --green: #6AB43E; --blue: #1E9BD7;
  --ink: #2A1416; --muted: #7A5F5C;}

#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {visibility: hidden; height: 0;}
header[data-testid="stHeader"] {background: transparent;}
/* the reopen-sidebar button lives inside the hidden toolbar, so show it again */
[data-testid="stExpandSidebarButton"] {visibility: visible;}

.dp-page .block-container, .block-container {max-width: 1200px;}
html, body, [class*="css"], .stApp {font-family: 'Inter', system-ui, sans-serif;}

/* ---------- landing ---------- */
.dp-stage {position: relative; border-radius: 28px; overflow: hidden; padding: 28px 40px 80px;
  background:
    radial-gradient(800px 380px at 10% -10%, rgba(237,32,39,.20), transparent 60%),
    radial-gradient(700px 380px at 95% 0%, rgba(245,130,32,.24), transparent 60%),
    radial-gradient(700px 320px at 50% 115%, rgba(255,194,14,.30), transparent 60%),
    radial-gradient(500px 260px at 0% 100%, rgba(106,180,62,.14), transparent 60%),
    radial-gradient(500px 260px at 100% 100%, rgba(30,155,215,.14), transparent 60%),
    #FFF8F4;
  color: var(--ink); border: 1px solid rgba(237,32,39,.14); box-shadow: 0 20px 60px rgba(237,32,39,.10);}
.dp-stage::after {content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 6px;
  background: linear-gradient(90deg, var(--green), var(--blue), var(--yellow), var(--orange), var(--red));}
.dp-stage::before {content: ""; position: absolute; inset: 0; pointer-events: none;
  background-image: linear-gradient(rgba(237,32,39,.05) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(237,32,39,.05) 1px, transparent 1px);
  background-size: 48px 48px;
  -webkit-mask-image: radial-gradient(ellipse at 50% 30%, #000 20%, transparent 75%);
  mask-image: radial-gradient(ellipse at 50% 30%, #000 20%, transparent 75%);}
.dp-logo {display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 1.15rem; letter-spacing: -.02em; color: var(--red-d);}
.dp-logo i {width: 28px; height: 28px; border-radius: 8px; display: inline-block;
  background: linear-gradient(135deg, var(--red), var(--orange)); box-shadow: 0 6px 18px rgba(237,32,39,.35);}
.dp-hero {position: relative; text-align: center; max-width: 860px; margin: 0 auto;}
.dp-grad {background: linear-gradient(90deg, var(--red) 0%, var(--orange) 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent; -webkit-text-fill-color: transparent;}
.dp-hero h1.dp-brand {font-size: clamp(3.6rem, 11vw, 7.5rem); line-height: 1.04; letter-spacing: -.045em; font-weight: 800;
  margin: 48px 0 10px; padding: 0; color: var(--red); display: flex; align-items: center; justify-content: center; gap: 22px;}
.dp-logo-img {display: inline-block; flex: none; height: 36px; aspect-ratio: 1; border-radius: 50%; overflow: hidden;
  background: #fff; box-shadow: 0 0 0 4px rgba(237,32,39,.12), 0 12px 32px rgba(237,32,39,.28);}
.dp-logo-img img {display: block; width: 100%; height: 100%; object-fit: cover; transform: scale(1.08);}
.dp-brand .dp-logo-img {height: .85em;}
.dp-bar .dp-logo-img {height: 38px; box-shadow: 0 0 0 2px rgba(237,32,39,.15);}
.dp-brand i {width: .5em; height: .5em; border-radius: .14em; display: inline-block;
  background: linear-gradient(135deg, var(--red), var(--orange)); box-shadow: 0 10px 30px rgba(237,32,39,.4);}
.dp-hero h2.dp-tag {font-size: clamp(1.1rem, 2.4vw, 1.6rem); font-weight: 600; letter-spacing: -.02em; margin: 0 0 20px; padding: 0; color: var(--ink);}
.dp-hero p {font-size: 1.15rem; line-height: 1.6; color: var(--muted); max-width: 640px; margin: 0 auto;}
.dp-stats {position: relative; display: flex; justify-content: center; gap: 56px; margin-top: 48px; flex-wrap: wrap;}
.dp-stats div {text-align: center;}
.dp-stats strong {display: block; font-size: 1.7rem; letter-spacing: -.03em; color: var(--ink);}
.dp-stats div:nth-child(1) strong {color: var(--red);} .dp-stats div:nth-child(2) strong {color: var(--orange);}
.dp-stats div:nth-child(3) strong {color: var(--green);}
.dp-stats span {font-size: .8rem; color: #A38A86; text-transform: uppercase; letter-spacing: .12em;}

/* CTA form */
div[data-testid="stForm"] {border: 1px solid rgba(237,32,39,.18); background: #fff;
  border-radius: 16px; padding: 18px 18px 8px; box-shadow: 0 12px 36px rgba(237,32,39,.12);}
.dp-cta-wrap {margin-top: -44px; position: relative; z-index: 5;}
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {border-radius: 12px; font-weight: 600; padding: .65rem 1.2rem;
  background: linear-gradient(135deg, var(--red), var(--orange)); color: #fff; border: 0;
  box-shadow: 0 8px 24px rgba(237,32,39,.30); transition: transform .15s, box-shadow .15s;}
.stButton > button:hover, .stFormSubmitButton > button:hover, .stDownloadButton > button:hover {transform: translateY(-1px); color: #fff;
  box-shadow: 0 12px 30px rgba(237,32,39,.45);}
.stButton > button:disabled {opacity: .45; box-shadow: none; color: #fff;}

/* sections: each card takes one colour from the logo */
.dp-section {margin: 72px 0 8px; text-align: center;}
.dp-section small {color: var(--red); font-weight: 700; letter-spacing: .14em; text-transform: uppercase; font-size: .75rem;}
.dp-section h2 {font-size: 2.1rem; letter-spacing: -.035em; margin: 10px 0 8px; font-weight: 700; padding: 0; color: var(--ink);}
.dp-section p {color: var(--muted); max-width: 560px; margin: 0 auto;}
.dp-grid {display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 18px; margin-top: 32px;}
.dp-three {grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));}
.dp-card {--c: var(--red); padding: 24px; border-radius: 18px; border: 1px solid color-mix(in srgb, var(--c) 22%, white);
  border-top: 4px solid var(--c); background: linear-gradient(180deg, color-mix(in srgb, var(--c) 8%, white), #fff);
  transition: transform .2s, box-shadow .2s;}
.dp-card:hover {transform: translateY(-3px); box-shadow: 0 14px 34px color-mix(in srgb, var(--c) 25%, transparent);}
.dp-card:nth-child(6n+2) {--c: var(--orange);} .dp-card:nth-child(6n+3) {--c: var(--yellow);}
.dp-card:nth-child(6n+4) {--c: var(--green);} .dp-card:nth-child(6n+5) {--c: var(--blue);}
.dp-ico {width: 42px; height: 42px; border-radius: 12px; display: grid; place-items: center; font-size: 1.2rem; margin-bottom: 14px;
  background: color-mix(in srgb, var(--c) 18%, white);}
.dp-card h3 {font-size: 1.05rem; margin: 0 0 6px; padding: 0; letter-spacing: -.01em; color: var(--ink);}
.dp-card p {margin: 0; font-size: .92rem; line-height: 1.55; color: var(--muted);}
.dp-step {counter-increment: s;}
.dp-step .dp-ico::before {content: counter(s); font-weight: 800; color: var(--c);}
.dp-steps {counter-reset: s;}
.dp-steps .dp-card:nth-child(4n+1) {--c: var(--green);} .dp-steps .dp-card:nth-child(4n+2) {--c: var(--blue);}
.dp-steps .dp-card:nth-child(4n+3) {--c: var(--orange);} .dp-steps .dp-card:nth-child(4n+4) {--c: var(--red);}
.dp-foot {margin-top: 64px; padding-top: 22px; border-top: 1px solid rgba(237,32,39,.14);
  display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; font-size: .82rem; color: #A38A86;}

/* ---------- in-app ---------- */
.dp-bar {position: relative; display: flex; align-items: center; justify-content: space-between; padding: 14px 20px 16px; border-radius: 14px;
  margin-bottom: 18px; overflow: hidden; border: 1px solid rgba(237,32,39,.16);
  background: linear-gradient(120deg, #FFF8F4, #FFEBDD 60%, #FFE0CC);}
.dp-bar::after {content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 4px;
  background: linear-gradient(90deg, var(--green), var(--blue), var(--yellow), var(--orange), var(--red));}
.dp-bar .dp-logo i {width: 22px; height: 22px; border-radius: 6px;}
.dp-bar span {font-size: .85rem; color: var(--muted); font-weight: 500;}
[data-testid="stMetric"] {border-left: 4px solid var(--red) !important;}
[data-testid="stMetric"]:nth-of-type(2n) {border-left-color: var(--orange) !important;}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) {background: #FFF4EC; border: 1px solid #FAD7C3; border-left: 4px solid var(--orange);}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) * {color: #5A2A22 !important;}
.block-container h1 {color: var(--ink);}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {color: var(--red-d);}

@media (max-width: 640px) {
  .dp-stage {padding: 20px 20px 56px;} .dp-stats {gap: 28px;}
}
</style>
"""

FEATURES = [
    ("⚡", "Instant extraction", "Drop in PDFs or photos. Vendors, totals, line items and packing rows are read in seconds."),
    ("🧠", "Frontier AI", "Advanced models tuned to return only what is on the page. Nothing invented."),
    ("🛡️", "Built-in verification", "Quantity x price, subtotals, tax, duplicates and weights are checked and flagged for review."),
    ("🔗", "Item master matching", "Packing descriptions are mapped to your item codes with confidence levels."),
    ("📊", "Export-ready Excel", "One click gives you a clean, formatted workbook for your team or ERP."),
    ("✍️", "Human in the loop", "Edit any cell, fix flagged rows, and see the checks update live."),
]

STEPS = [
    ("Upload", "Add invoices or packing lists as PDF or image."),
    ("Extract", "AI reads every field and line item."),
    ("Review", "Flagged issues are highlighted so you only check what matters."),
    ("Export", "Download a formatted Excel report."),
]


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def _cards(items, steps=False):
    cls = "dp-grid dp-steps" if steps else "dp-grid dp-three"
    cards = "".join(
        f'<div class="dp-card{" dp-step" if steps else ""}"><div class="dp-ico">{"" if steps else i[0]}</div>'
        f"<h3>{i[0] if steps else i[1]}</h3><p>{i[1] if steps else i[2]}</p></div>"
        for i in items
    )
    return f'<div class="{cls}">{cards}</div>'


def landing(needs_password: bool, check_password) -> bool:
    """Render the landing page. Returns True once the visitor may enter the workspace."""
    inject_css()
    st.markdown(
        '<div class="dp-stage">'
        '<div class="dp-hero">'
        '<h1 class="dp-brand">' + logo_mark() + 'DocPro</h1>'
        '<h2 class="dp-tag"><span class="dp-grad">Intelligent</span> Document Processing</h2>'
        "<p>DocPro turns invoices and packing lists into verified, export-ready data. "
        "Upload, review, and send to Excel in seconds.</p></div>"
        '<div class="dp-stats"><div><strong>Seconds</strong><span>Per document</span></div>'
        "<div><strong>Auto</strong><span>Consistency checks</span></div>"
        "<div><strong>1-click</strong><span>Excel export</span></div></div>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="dp-cta-wrap"></div>', unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.4, 1])
    entered = False
    with mid:
        with st.form("enter", border=True):
            pw = st.text_input("Password", type="password", placeholder="Enter access password",
                               label_visibility="collapsed") if needs_password else None
            go = st.form_submit_button("Unlock workspace" if needs_password else "Launch workspace",
                                       use_container_width=True)
        if go:
            if not needs_password or check_password(pw or ""):
                entered = True
            else:
                st.error("Incorrect password")

    st.markdown(
        '<div class="dp-section"><small>Platform</small><h2>Everything between the PDF and the spreadsheet</h2>'
        "<p>One focused workflow, from raw document to a reviewed, exported report.</p></div>"
        + _cards(FEATURES)
        + '<div class="dp-section"><small>How it works</small><h2>Four steps. Zero retyping.</h2></div>'
        + _cards(STEPS, steps=True)
        + '<div class="dp-foot"><span>© DocPro</span>'
        "</div>",
        unsafe_allow_html=True,
    )
    return entered


def app_bar():
    """Slim branded header shown above the workspace pages."""
    st.markdown(
        '<div class="dp-bar"><div class="dp-logo">' + logo_mark() + 'DocPro</div>'
        "<span>Intelligent Document Processing</span></div>",
        unsafe_allow_html=True,
    )
