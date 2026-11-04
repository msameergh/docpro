"""Landing page UI for DocPro. Presentation only: no extraction or validation logic."""
import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {visibility: hidden; height: 0;}
header[data-testid="stHeader"] {background: transparent;}
/* the reopen-sidebar button lives inside the hidden toolbar, so show it again */
[data-testid="stExpandSidebarButton"] {visibility: visible;}

.dp-page .block-container, .block-container {max-width: 1200px;}
html, body, [class*="css"], .stApp {font-family: 'Inter', system-ui, sans-serif;}

/* ---------- landing ---------- */
.dp-stage {position: relative; border-radius: 28px; overflow: hidden; padding: 28px 40px 72px;
  background:
    radial-gradient(900px 420px at 15% -10%, rgba(99,102,241,.55), transparent 60%),
    radial-gradient(800px 420px at 90% 0%, rgba(14,165,233,.40), transparent 60%),
    radial-gradient(700px 380px at 50% 110%, rgba(168,85,247,.35), transparent 60%),
    #070B1A;
  color: #E6EAF5; border: 1px solid rgba(255,255,255,.08);}
.dp-stage::before {content: ""; position: absolute; inset: 0; pointer-events: none;
  background-image: linear-gradient(rgba(255,255,255,.04) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255,255,255,.04) 1px, transparent 1px);
  background-size: 48px 48px;
  -webkit-mask-image: radial-gradient(ellipse at 50% 30%, #000 20%, transparent 75%);
  mask-image: radial-gradient(ellipse at 50% 30%, #000 20%, transparent 75%);}
.dp-logo {display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 1.15rem; letter-spacing: -.02em; color: #fff;}
.dp-logo i {width: 28px; height: 28px; border-radius: 8px; display: inline-block;
  background: linear-gradient(135deg, #818CF8, #38BDF8); box-shadow: 0 0 24px rgba(129,140,248,.7);}
.dp-hero {position: relative; text-align: center; max-width: 860px; margin: 0 auto;}
.dp-pill {display: inline-flex; align-items: center; gap: 8px; padding: 6px 14px; border-radius: 999px; font-size: .8rem;
  color: #C7D2FE; background: rgba(99,102,241,.14); border: 1px solid rgba(129,140,248,.35);}
.dp-pill b {width: 7px; height: 7px; border-radius: 50%; background: #34D399; box-shadow: 0 0 10px #34D399;}
.dp-hero h1 {font-size: clamp(2.4rem, 6vw, 4.6rem); line-height: 1.04; letter-spacing: -.045em; font-weight: 800;
  margin: 22px 0 18px; padding: 0; color: #fff;}
.dp-grad {background: linear-gradient(90deg, #A5B4FC 0%, #7DD3FC 50%, #C4B5FD 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent; -webkit-text-fill-color: transparent;}
.dp-hero h1.dp-brand {font-size: clamp(3.6rem, 11vw, 7.5rem); margin: 56px 0 10px; display: flex; align-items: center;
  justify-content: center; gap: 22px;}
.dp-brand i {width: .5em; height: .5em; border-radius: .14em; display: inline-block;
  background: linear-gradient(135deg, #818CF8, #38BDF8); box-shadow: 0 0 40px rgba(129,140,248,.7);}
.dp-hero h2.dp-tag {font-size: clamp(1.1rem, 2.4vw, 1.6rem); font-weight: 600; letter-spacing: -.02em; margin: 0 0 20px; padding: 0; color: #fff;}
.dp-hero p {font-size: 1.15rem; line-height: 1.6; color: #A5B0CE; max-width: 640px; margin: 0 auto;}
.dp-stats {position: relative; display: flex; justify-content: center; gap: 56px; margin-top: 48px; flex-wrap: wrap;}
.dp-stats div {text-align: center;}
.dp-stats strong {display: block; font-size: 1.7rem; letter-spacing: -.03em; color: #fff;}
.dp-stats span {font-size: .8rem; color: #8590B0; text-transform: uppercase; letter-spacing: .12em;}

/* CTA form sits on the dark stage */
div[data-testid="stForm"] {border: 1px solid rgba(255,255,255,.12); background: rgba(255,255,255,.04);
  border-radius: 16px; padding: 18px 18px 8px; backdrop-filter: blur(8px);}
.dp-cta-wrap {margin-top: -44px; position: relative; z-index: 5;}
.stButton > button, .stFormSubmitButton > button {border-radius: 12px; font-weight: 600; padding: .65rem 1.2rem;
  background: linear-gradient(135deg, #6366F1, #0EA5E9); color: #fff; border: 0;
  box-shadow: 0 8px 24px rgba(99,102,241,.35); transition: transform .15s, box-shadow .15s;}
.stButton > button:hover, .stFormSubmitButton > button:hover {transform: translateY(-1px); color: #fff;
  box-shadow: 0 12px 30px rgba(99,102,241,.5);}

.stButton > button:disabled {opacity: .45; box-shadow: none; color: #fff;}

/* sections */
.dp-section {margin: 72px 0 8px; text-align: center;}
.dp-section small {color: #6366F1; font-weight: 600; letter-spacing: .14em; text-transform: uppercase; font-size: .75rem;}
.dp-section h2 {font-size: 2.1rem; letter-spacing: -.035em; margin: 10px 0 8px; font-weight: 700; padding: 0;}
.dp-section p {color: #6B7280; max-width: 560px; margin: 0 auto;}
.dp-grid {display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 18px; margin-top: 32px;}
.dp-three {grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));}
.dp-card {padding: 24px; border-radius: 18px; border: 1px solid rgba(128,128,150,.22);
  background: linear-gradient(180deg, rgba(99,102,241,.07), rgba(99,102,241,0)); transition: transform .2s, border-color .2s;}
.dp-card:hover {transform: translateY(-3px); border-color: rgba(99,102,241,.55);}
.dp-ico {width: 42px; height: 42px; border-radius: 12px; display: grid; place-items: center; font-size: 1.2rem; margin-bottom: 14px;
  background: linear-gradient(135deg, rgba(99,102,241,.25), rgba(14,165,233,.25));}
.dp-card h3 {font-size: 1.05rem; margin: 0 0 6px; padding: 0; letter-spacing: -.01em;}
.dp-card p {margin: 0; font-size: .92rem; line-height: 1.55; color: #6B7280;}
.dp-step {counter-increment: s;}
.dp-step .dp-ico::before {content: counter(s);font-weight: 700; color: #6366F1;}
.dp-steps {counter-reset: s;}
.dp-foot {margin-top: 64px; padding-top: 22px; border-top: 1px solid rgba(128,128,150,.22);
  display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; font-size: .82rem; color: #8B93A7;}

/* ---------- in-app banner ---------- */
.dp-bar {display: flex; align-items: center; justify-content: space-between; padding: 14px 20px; border-radius: 14px; margin-bottom: 18px;
  color: #fff; background: linear-gradient(120deg, #0B1022, #1E1B4B 60%, #1D4ED8);}
.dp-bar .dp-logo i {width: 22px; height: 22px; border-radius: 6px;}
.dp-bar span {font-size: .85rem; color: #A5B4FC;}

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
        '<h1 class="dp-brand"><i></i>DocPro</h1>'
        '<h2 class="dp-tag"><span class="dp-grad">Frontier Intelligence</span> for Documents Processing</h2>'
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
        '<div class="dp-bar"><div class="dp-logo"><i></i>DocPro</div>'
        "<span>Frontier Intelligence for Documents Processing</span></div>",
        unsafe_allow_html=True,
    )
