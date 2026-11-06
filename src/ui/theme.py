"""Nyaya.ai look and feel, inspired by Indian stamp paper: the pale green,
finely patterned paper that rent agreements and affidavits are printed on.

    apply_theme()       call once, right after st.set_page_config()
    hero(subtitle)      the stamp-paper header with the app name
    loader(text)        the scales-of-justice loading animation (returns a
                        placeholder; call .empty() on it when work is done)

Optional photo: put an image at assets/hero.jpg (for example a free photo
from Unsplash or Pexels) and it appears beside the title in the header. If
the file is missing, the header simply has no photo.
"""

import base64
from pathlib import Path

import streamlit as st

INK = "#1D2B45"        # ink navy: text and headings
PAPER = "#EAF0E6"      # stamp-paper green: page background
PAPER_DEEP = "#DCE6D6" # sidebar and quiet surfaces
SHEET = "#FBFCF8"      # white sheet: answers and cards
TAPE = "#A12B2F"       # court-file red tape: primary buttons, sparingly
BRASS = "#A8853F"      # brass of the scales: rules and the loader

HERO_IMAGE = Path("assets/hero.jpg")


def _svg_uri(svg):
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


# Guilloche band: overlapping waves, like the security border of stamp paper.
_GUILLOCHE = _svg_uri(
    """<svg xmlns='http://www.w3.org/2000/svg' width='120' height='36' viewBox='0 0 120 36'>
<g fill='none' stroke-width='0.8'>
<path d='M0 18 Q15 2 30 18 T60 18 T90 18 T120 18' stroke='#7E9C78'/>
<path d='M0 18 Q15 34 30 18 T60 18 T90 18 T120 18' stroke='#7E9C78'/>
<path d='M0 12 Q15 -2 30 12 T60 12 T90 12 T120 12' stroke='#A8853F' opacity='0.7'/>
<path d='M0 24 Q15 38 30 24 T60 24 T90 24 T120 24' stroke='#A8853F' opacity='0.7'/>
<path d='M-15 18 Q0 6 15 18 T45 18 T75 18 T105 18 T135 18' stroke='#9DB89A' opacity='0.8'/>
<path d='M-15 18 Q0 30 15 18 T45 18 T75 18 T105 18 T135 18' stroke='#9DB89A' opacity='0.8'/>
</g></svg>"""
)

# Faint fine-line texture for the whole page (barely visible, like paper).
_PAPER_LINES = _svg_uri(
    """<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160' viewBox='0 0 160 160'>
<g fill='none' stroke='#7E9C78' stroke-width='0.5' opacity='0.18'>
<path d='M0 40 Q40 20 80 40 T160 40'/><path d='M0 80 Q40 60 80 80 T160 80'/>
<path d='M0 120 Q40 100 80 120 T160 120'/><path d='M0 160 Q40 140 80 160 T160 160'/>
</g></svg>"""
)

# Original drawing of the scales of justice. The beam tips back and forth;
# each pan hangs from its end of the beam.
_SCALES = f"""
<svg class="ny-scales" viewBox="0 0 120 110" width="96" height="88" aria-hidden="true">
  <g stroke="{INK}" stroke-width="3" stroke-linecap="round" fill="none">
    <line x1="60" y1="18" x2="60" y2="92"/>
    <path d="M40 96 H80" stroke-width="5"/>
    <circle cx="60" cy="14" r="4" fill="{BRASS}" stroke="none"/>
  </g>
  <g class="ny-beam">
    <line x1="20" y1="24" x2="100" y2="24" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>
    <g class="ny-pan ny-pan-left">
      <path d="M20 24 L10 54 M20 24 L30 54" stroke="{BRASS}" stroke-width="1.5"/>
      <path d="M6 54 H34 A14 8 0 0 1 6 54 Z" fill="{BRASS}"/>
    </g>
    <g class="ny-pan ny-pan-right">
      <path d="M100 24 L90 54 M100 24 L110 54" stroke="{BRASS}" stroke-width="1.5"/>
      <path d="M86 54 H114 A14 8 0 0 1 86 54 Z" fill="{BRASS}"/>
    </g>
  </g>
</svg>
"""


def apply_theme():
    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Libre+Caslon+Text:wght@400;700&family=Mukta:wght@400;600&display=swap');

html, body, [class*="css"], .stMarkdown, .stTextInput, .stSelectbox, .stChatInput textarea {{
  font-family: 'Mukta', 'Noto Sans', 'Nirmala UI', sans-serif;
  color: {INK};
}}
[data-testid="stAppViewContainer"] {{
  background-color: {PAPER};
  background-image: url("{_PAPER_LINES}");
}}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stSidebar"] {{
  background-color: {PAPER_DEEP};
  border-right: 1px solid #C9D6C2;
}}
h1, h2, h3, .ny-title {{
  font-family: 'Libre Caslon Text', Georgia, serif;
  color: {INK};
  letter-spacing: 0;
}}
.block-container {{ max-width: 920px; }}

/* Header: a strip of stamp paper */
.ny-hero {{
  position: relative;
  border: 1px solid #C9D6C2;
  border-radius: 6px;
  background: {SHEET};
  overflow: hidden;
  margin-bottom: 1.2rem;
}}
.ny-band {{
  height: 36px;
  background-image: url("{_GUILLOCHE}");
  background-repeat: repeat-x;
  border-bottom: 1px solid #C9D6C2;
}}
.ny-hero-body {{ position: relative; padding: 1.1rem 1.4rem 1.2rem; }}
.ny-hero-body.ny-has-photo {{
  display: grid; grid-template-columns: 1fr 1.15fr; gap: 1.4rem; align-items: center;
}}
.ny-hero-photo {{
  /* !important: Streamlit's own img rules otherwise letterbox the photo */
  width: 100% !important; max-width: none !important; height: 210px !important;
  object-fit: cover !important; object-position: 60% 40%;
  border-radius: 4px; border: 1px solid #C9D6C2; display: block;
}}
@media (max-width: 720px) {{
  .ny-hero-body.ny-has-photo {{ grid-template-columns: 1fr; }}
  .ny-hero-photo {{ height: 170px !important; }}
}}
.ny-title {{ position: relative; font-size: 2.4rem; line-height: 1.1; margin: 0; font-weight: 700; }}
.ny-title .ny-dot {{ color: {TAPE}; }}
.ny-sub {{ position: relative; margin: .35rem 0 0; font-size: 1.05rem; color: #3C4A63; max-width: 60ch; }}

/* Answers read like a clean sheet */
[data-testid="stChatMessage"] {{
  background: {SHEET};
  border: 1px solid #D3DECD;
  border-radius: 6px;
  padding: .6rem .9rem;
}}
[data-testid="stExpander"] details {{
  background: {SHEET};
  border: 1px solid #D3DECD;
  border-radius: 6px;
}}

/* Chat box: a clean sheet, not an alarm */
[data-testid="stChatInput"] > div, [data-testid="stChatInput"] textarea {{
  background: {SHEET} !important;
}}
[data-testid="stChatInput"] > div {{ border: 1px solid #B9C8B2 !important; }}
[data-testid="stChatInput"] > div:focus-within {{ border-color: {BRASS} !important; }}

/* Primary actions in red tape; everything else stays quiet */
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {{
  background: {TAPE}; border-color: {TAPE}; color: #fff;
}}
.stButton > button[kind="primary"]:hover {{ background: #8A2227; border-color: #8A2227; }}
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible {{
  outline: 3px solid {BRASS}; outline-offset: 2px;
}}

/* Scales-of-justice loader */
.ny-loader {{
  display: flex; align-items: center; gap: 1rem;
  background: {SHEET};
  border: 1px solid #D3DECD; border-left: 4px solid {BRASS};
  border-radius: 6px; padding: .7rem 1rem; margin: .5rem 0;
}}
.ny-loader p {{ margin: 0; font-size: 1.05rem; }}
.ny-loader small {{ color: #56627A; }}
.ny-beam {{ transform-origin: 60px 24px; animation: ny-tip 2.4s ease-in-out infinite; }}
.ny-pan-left {{ transform-origin: 20px 24px; animation: ny-hang 2.4s ease-in-out infinite; }}
.ny-pan-right {{ transform-origin: 100px 24px; animation: ny-hang 2.4s ease-in-out infinite; }}
@keyframes ny-tip {{ 0%, 100% {{ transform: rotate(-9deg); }} 50% {{ transform: rotate(9deg); }} }}
@keyframes ny-hang {{ 0%, 100% {{ transform: rotate(9deg); }} 50% {{ transform: rotate(-9deg); }} }}
@media (prefers-reduced-motion: reduce) {{
  .ny-beam, .ny-pan-left, .ny-pan-right {{ animation: none; }}
}}
</style>
""",
        unsafe_allow_html=True,
    )


def hero(subtitle):
    text = (
        '<div><h1 class="ny-title">Nyaya<span class="ny-dot">.</span>ai</h1>'
        f'<p class="ny-sub">{subtitle}</p></div>'
    )
    photo, body_class = "", "ny-hero-body"
    if HERO_IMAGE.exists():
        data = base64.b64encode(HERO_IMAGE.read_bytes()).decode()
        photo = (
            f'<img class="ny-hero-photo" src="data:image/jpeg;base64,{data}" '
            'alt="A lawyer at his desk talking with two clients">'
        )
        body_class += " ny-has-photo"
    # One unindented line: Streamlit's Markdown treats indented HTML lines as a code block.
    html = (
        f'<div class="ny-hero"><div class="ny-band"></div><div class="{body_class}">'
        f'{text}{photo}</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def loader(text, note="Reading the law and checking every section I cite."):
    """Shows the scales of justice while work runs. Usage:
        box = loader("Weighing your case...")
        ... long work ...
        box.empty()
    """
    box = st.empty()
    scales = " ".join(line.strip() for line in _SCALES.splitlines())
    box.markdown(
        f'<div class="ny-loader" role="status" aria-live="polite">{scales}'
        f'<div><p>{text}</p><small>{note}</small></div></div>',
        unsafe_allow_html=True,
    )
    return box
