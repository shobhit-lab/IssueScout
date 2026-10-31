"""IssueScout - AI first-contribution guide (Hacktoberfest 2026)

Run:   streamlit run app.py   (UI inspired by the Agnos Framer template)
Deps:  pip install streamlit requests pillow google-genai

Set your key once (recommended) instead of typing it each time:
    export GEMINI_API_KEY="your-key"        # macOS / Linux
    setx GEMINI_API_KEY "your-key"          # Windows
or put  GEMINI_API_KEY = "your-key"  in .streamlit/secrets.toml
"""
import html
import os
import re
import time

import requests
import streamlit as st
from PIL import Image, ImageOps
from google import genai

try:
    from google.genai import types
except Exception:  # very old SDKs
    types = None

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------
# Check the exact Gemma 4 model ID in Google AI Studio / the MLH Gemma page.
DEFAULT_MODEL = os.getenv("GEMMA_MODEL", "gemma-4-31b-it")
# If the primary model is unavailable / rate-limited, these are tried in order.
FALLBACK_MODELS = ["gemma-3-27b-it", "gemini-2.5-flash"]

LABELS = ["good first issue", "hacktoberfest", "help wanted", "documentation", "bug", "(any open issue)"]

st.set_page_config(page_title="IssueScout", page_icon="🧭", layout="wide",
                   initial_sidebar_state="expanded")


def _secret(name: str) -> str:
    try:
        return str(st.secrets.get(name, "") or "")
    except Exception:
        return ""


DEFAULT_KEY = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
               or _secret("GEMINI_API_KEY") or "")
DEFAULT_GH = os.getenv("GITHUB_TOKEN") or _secret("GITHUB_TOKEN") or ""


# --------------------------------------------------------------------------
# Theme (Agnos-inspired: warm light by default, one-click dark switch)
# --------------------------------------------------------------------------
st.session_state.setdefault("theme", "light")

THEMES = {
    "light": dict(bg="#F5F4F3", bg2="#FAF9F8", surface="#FFFFFF", surface2="#EEECEA", border="#E3E0DC",
                  text="#060612", muted="#69686E", accent="#FF6321", accent2="#0099FF",
                  link="#CF4E17", glow="rgba(255,99,33,.16)", ink="#060612", onink="#FFFFFF",
                  shadow="rgba(6,6,18,.22)"),
    "dark": dict(bg="#0A0A12", bg2="#0F0F19", surface="#14141F", surface2="#1D1D2B", border="#2A2A3A",
                 text="#F5F4F3", muted="#9A99A3", accent="#FF6321", accent2="#0099FF",
                 link="#FF8A57", glow="rgba(255,99,33,.20)", ink="#F5F4F3", onink="#060612",
                 shadow="rgba(0,0,0,.55)"),
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700;800&family=Geist+Mono:wght@500;600&display=swap');

@property --n   { syntax: '<integer>'; initial-value: 0; inherits: false; }
@property --ang { syntax: '<angle>';   initial-value: 0deg; inherits: false; }

:root { --bg:__bg__; --bg2:__bg2__; --surface:__surface__; --surface2:__surface2__; --border:__border__;
        --text:__text__; --muted:__muted__; --accent:__accent__; --accent2:__accent2__;
        --link:__link__; --glow:__glow__; --ink:__ink__; --onink:__onink__; --shadow:__shadow__;
        --radius:20px; --ease:cubic-bezier(.2,.8,.2,1); }

html, body, .stApp { background: var(--bg) !important; color: var(--text) !important;
                     font-family: 'Geist', system-ui, sans-serif !important; scroll-behavior: smooth; }
.stApp { background: radial-gradient(900px 480px at 85% -6%, var(--glow), transparent 70%),
                     radial-gradient(700px 420px at -4% 40%, rgba(0,153,255,.08), transparent 70%), var(--bg) !important; }
button, input, textarea, select { font-family: inherit !important; }

#MainMenu, footer, .stDeployButton { visibility: hidden; }
[data-testid="stHeader"] { background: transparent !important; }
.block-container { padding-top: 5.2rem; max-width: 1120px; }
::selection { background: var(--accent); color: #fff; }

/* ---------- keyframes ---------- */
@keyframes rise    { from { transform: translateY(112%); } }
@keyframes fadeUp  { from { opacity: 0; transform: translateY(26px); } }
@keyframes fadeIn  { from { opacity: 0; } }
@keyframes pop     { from { opacity: 0; transform: scale(.86); } }
@keyframes drop    { from { opacity: 0; transform: translate(-50%, -24px); } }
@keyframes spin    { to { transform: rotate(360deg); } }
@keyframes draw    { from { stroke-dashoffset: 1; } }
@keyframes count   { from { --n: 0; } }
@keyframes rot     { to { --ang: 360deg; } }
@keyframes bob     { 0%,100% { transform: translateY(0) rotate(var(--r)); }
                     50%     { transform: translateY(-14px) rotate(calc(var(--r) + 5deg)); } }
@keyframes ping    { 0% { transform: scale(.6); opacity: .9; } 80%,100% { transform: scale(3.2); opacity: 0; } }
@keyframes drift   { 0%,100% { transform: translate(0,0); } 50% { transform: translate(40px,-30px); } }
@keyframes marq    { to { transform: translateX(-50%); } }
@keyframes sheen   { 0% { transform: translateX(-130%) skewX(-20deg); } 55%,100% { transform: translateX(260%) skewX(-20deg); } }
@keyframes wobble  { 0%,100% { transform: rotate(-14deg); } 50% { transform: rotate(18deg); } }
@keyframes pulse   { 0%,100% { opacity: 1; } 50% { opacity: .55; } }
@keyframes scan    { to { transform: translateX(100%); } }

/* scroll-in helper: visible by default, animated on load, scroll-driven where supported */
.reveal { animation: fadeUp .9s var(--ease) both; animation-delay: calc(var(--d, 0) * 90ms); }
@supports (animation-timeline: view()) {
  .reveal { animation: fadeUp linear both; animation-delay: 0s;
            animation-timeline: view(); animation-range: entry 0% entry 42%; }
  .num    { animation: count linear both !important; animation-timeline: view() !important;
            animation-range: entry 8% cover 32% !important; }
}

/* ---------- streamlit text ---------- */
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span, [data-testid="stMarkdownContainer"] td,
[data-testid="stMarkdownContainer"] th { color: var(--text) !important; line-height: 1.65; }
[data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4 {
    color: var(--text) !important; font-family: 'Geist', sans-serif !important; letter-spacing: -.02em; }
[data-testid="stMarkdownContainer"] a, a { color: var(--link) !important; }
[data-testid="stMarkdownContainer"] code { background: var(--surface2) !important; color: var(--link) !important;
    border-radius: 6px; padding: .1rem .35rem; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * { color: var(--muted) !important; }
[data-testid="stWidgetLabel"] p, label p { color: var(--muted) !important; font-weight: 500; }

/* ---------- floating nav pill ---------- */
.nav { position: fixed; top: 14px; left: 50%; transform: translateX(-50%); z-index: 1000;
       display: flex; align-items: center; gap: .35rem; padding: .4rem .45rem .4rem .55rem;
       background: color-mix(in srgb, var(--surface) 82%, transparent);
       backdrop-filter: blur(14px) saturate(1.4); -webkit-backdrop-filter: blur(14px) saturate(1.4);
       border: 1px solid var(--border); border-radius: 16px;
       box-shadow: 0 12px 34px -14px var(--shadow); animation: drop .9s var(--ease) both; }
.nav .brand { display: flex; align-items: center; gap: .5rem; padding-right: .7rem; margin-right: .2rem;
              border-right: 1px solid var(--border); font-weight: 700; font-size: 1.05rem; letter-spacing: -.03em;
              color: var(--text) !important; text-decoration: none !important; }
.nav .brand svg { display: block; }
.nav .needle { transform-origin: 32px 32px; animation: wobble 5s ease-in-out infinite; }
.nav a.l { padding: .45rem .7rem; border-radius: 10px; font-size: .9rem; font-weight: 500;
           color: var(--muted) !important; text-decoration: none !important; transition: background .2s, color .2s; }
.nav a.l:hover { background: var(--surface2); color: var(--text) !important; }
.nav a.go { background: var(--ink); color: var(--onink) !important; text-decoration: none !important;
            padding: .5rem .95rem; border-radius: 11px; font-size: .9rem; font-weight: 600; margin-left: .35rem;
            transition: transform .2s var(--ease), box-shadow .2s; }
.nav a.go:hover { transform: translateY(-1px); box-shadow: 0 8px 18px -8px var(--shadow); }
@media (max-width: 640px) { .nav a.l { display: none; } }

/* ---------- hero ---------- */
.hero2 { position: relative; overflow: hidden; isolation: isolate; text-align: center;
         display: flex; flex-direction: column; align-items: center; justify-content: center;
         min-height: 620px; padding: 4.5rem 1.4rem 4rem; margin: .4rem 0 1.6rem;
         background: var(--bg2); border: 1px solid var(--border); border-radius: 34px;
         box-shadow: 0 30px 60px -40px var(--shadow); animation: pop 1s var(--ease) both; }
.hero2::after { content: ""; position: absolute; inset: 0; z-index: 1; pointer-events: none;
                background: radial-gradient(ellipse 46% 52% at 50% 50%, var(--bg2) 38%, transparent 100%); }
.hero2 > .in { position: relative; z-index: 2; }
.ring { position: absolute; left: 50%; top: 50%; width: var(--s); height: var(--s);
        margin: calc(var(--s) / -2) 0 0 calc(var(--s) / -2); border-radius: 50%; z-index: 0;
        border: 1.5px solid var(--border); box-shadow: inset 0 0 0 7px color-mix(in srgb, var(--surface2) 55%, transparent);
        animation: fadeIn 1.6s var(--ease) both; animation-delay: calc(var(--k) * 160ms); }
.sweep { position: absolute; left: 50%; top: 50%; width: 1240px; height: 1240px; margin: -620px 0 0 -620px;
         border-radius: 50%; z-index: 0; animation: spin 9s linear infinite;
         background: conic-gradient(from 0deg, transparent 0 300deg, var(--glow) 350deg, color-mix(in srgb, var(--accent) 38%, transparent) 360deg);
         -webkit-mask: radial-gradient(circle, transparent 0 20%, #000 38%, #000 52%, transparent 70%);
         mask: radial-gradient(circle, transparent 0 20%, #000 38%, #000 52%, transparent 70%); opacity: .8; }
.orb { position: absolute; z-index: 0; border-radius: 50%; filter: blur(70px); opacity: .5; animation: drift 14s ease-in-out infinite; }
.orb.a { width: 280px; height: 280px; background: var(--accent);  left: -60px; bottom: -80px; opacity: .22; }
.orb.b { width: 260px; height: 260px; background: var(--accent2); right: -50px; top: -70px; opacity: .2; animation-delay: -6s; }
.blip { position: absolute; z-index: 1; width: 9px; height: 9px; border-radius: 50%; background: var(--accent); }
.blip::after { content: ""; position: absolute; inset: 0; border-radius: 50%; background: var(--accent);
               animation: ping 3.2s ease-out infinite; animation-delay: var(--t, 0s); }
.tile { position: absolute; z-index: 2; width: 66px; height: 66px; border-radius: 19px; display: grid; place-items: center;
        background: var(--surface); border: 1px solid var(--border);
        box-shadow: 0 18px 32px -16px var(--shadow), inset 0 1px 0 rgba(255,255,255,.5);
        animation: bob 6.5s ease-in-out infinite; animation-delay: var(--t, 0s); }
.tile svg { stroke: var(--text); fill: none; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.tile.o svg { stroke: var(--accent); }
@media (max-width: 860px) { .tile, .blip { display: none; } .hero2 { min-height: 540px; border-radius: 26px; } }

.eyebrow, .eyebrow span { color: var(--text) !important; }
.eyebrow { display: inline-flex; align-items: center; gap: .45rem; padding: .28rem .7rem; border: 1px solid var(--border);
           background: var(--surface); border-radius: 7px; font-family: 'Geist Mono', monospace; font-size: .74rem; font-weight: 600;
           letter-spacing: .12em; text-transform: uppercase; color: var(--text); animation: fadeUp .8s var(--ease) both; }
.eyebrow i { color: var(--accent) !important; font-style: normal; }

.h1 { font-weight: 600; font-size: clamp(2.6rem, 6.6vw, 4.9rem); line-height: 1.02; letter-spacing: -.045em;
      margin: 1.25rem auto 0; max-width: 11.5em; color: var(--text); }
.h1 .w { display: inline-block; overflow: hidden; vertical-align: bottom; padding: 0 .04em .1em; margin: 0 -.04em; }
.h1 .w > span { display: inline-block; animation: rise 1s var(--ease) both; animation-delay: calc(var(--i) * 80ms + 250ms); }
.h1 .acc { position: relative; display: inline-block; color: var(--accent); }
.h1 .acc, .h1 .acc .w > span { color: var(--accent) !important; }
.h1, .h1 .w, .h1 .w > span, .h1 .acc { line-height: 1.04 !important; }
.h1 .acc svg { position: absolute; left: 0; bottom: -.14em; width: 100%; height: .3em; overflow: visible; }
.h1 .acc path { stroke: var(--accent); stroke-width: 4; fill: none; stroke-linecap: round; stroke-dasharray: 1; stroke-dashoffset: 0;
                animation: draw 1.1s var(--ease) both; animation-delay: 1.35s; }

.sub { max-width: 34rem; margin: 1.35rem auto 0; color: var(--muted) !important; font-size: 1.08rem; line-height: 1.6;
       animation: fadeUp .9s var(--ease) both; animation-delay: .9s; }
.ctas { display: flex; flex-wrap: wrap; gap: .7rem; justify-content: center; margin-top: 1.7rem;
        animation: fadeUp .9s var(--ease) both; animation-delay: 1.05s; }
a.btn, a.btn:visited { position: relative; overflow: hidden; display: inline-flex; align-items: center; gap: .5rem;
        padding: .8rem 1.35rem; border-radius: 12px; font-weight: 600; font-size: .98rem;
        text-decoration: none !important; transition: transform .25s var(--ease), box-shadow .25s; }
a.btn.p { background: var(--accent); color: #fff !important; box-shadow: 0 14px 28px -12px var(--accent); }
a.btn.d { background: var(--ink); color: var(--onink) !important; }
a.btn:hover { transform: translateY(-3px); }
a.btn.p::after { content: ""; position: absolute; top: 0; bottom: 0; width: 38%; background: rgba(255,255,255,.35);
                 animation: sheen 3.6s ease-in-out infinite; }
a.btn .ar { display: inline-block; transition: transform .25s var(--ease); }
a.btn:hover .ar { transform: translateX(4px); }
.note { margin-top: 1.1rem; font-size: .9rem; color: var(--accent) !important; font-weight: 500;
        animation: fadeUp .9s var(--ease) both; animation-delay: 1.2s; }

/* ---------- marquee ---------- */
.trust { margin: 2.2rem 0 .4rem; }
.trust .cap { display: flex; align-items: center; gap: 1rem; justify-content: center; text-align: center;
              font-family: 'Geist Mono', monospace; font-size: .72rem; letter-spacing: .14em; color: var(--muted); text-transform: uppercase; }
.trust .cap::before, .trust .cap::after { content: ""; flex: 1; border-top: 1.5px dashed var(--border); }
.trust .cap b, .trust .cap span { color: var(--muted) !important; }
.trust .cap b { color: var(--text) !important; }
.marq { overflow: hidden; margin-top: 1.1rem; -webkit-mask: linear-gradient(90deg, transparent, #000 12%, #000 88%, transparent);
        mask: linear-gradient(90deg, transparent, #000 12%, #000 88%, transparent); }
.marq .track { display: flex; width: max-content; gap: 2.8rem; animation: marq 32s linear infinite; }
.marq:hover .track { animation-play-state: paused; }
.marq .it { display: inline-flex; align-items: center; gap: .55rem; font-weight: 600; font-size: 1.12rem;
            letter-spacing: -.02em; color: var(--muted) !important; white-space: nowrap; transition: color .2s; }
.marq .it:hover { color: var(--text) !important; }
.marq .it i { width: 8px; height: 8px; border-radius: 2px; background: var(--accent); transform: rotate(45deg); display: inline-block; }

/* ---------- sections ---------- */
.sec { margin: 3.6rem 0 1.2rem; text-align: center; scroll-margin-top: 90px; }
.sec .h2 { font-weight: 600; font-size: clamp(1.8rem, 4vw, 2.7rem); line-height: 1.08; letter-spacing: -.04em;
           margin: .9rem auto 0; max-width: 17em; color: var(--text); }
.sec .h2 em { font-style: normal; color: var(--accent); }
.sec p.lead { color: var(--muted) !important; max-width: 32rem; margin: .8rem auto 0; }

.grid3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 1.6rem; }
@media (max-width: 820px) { .grid3, .vs { grid-template-columns: 1fr !important; } }

.stat { position: relative; overflow: hidden; padding: 1.6rem 1.5rem; border-radius: var(--radius);
        background: var(--surface); border: 1px solid var(--border);
        transition: transform .35s var(--ease), box-shadow .35s, border-color .35s; }
.stat:hover { transform: translateY(-6px); border-color: var(--accent); box-shadow: 0 26px 40px -26px var(--shadow); }
.stat::before { content: ""; position: absolute; width: 160px; height: 160px; right: -60px; top: -60px; border-radius: 50%;
                background: var(--glow); filter: blur(24px); transition: transform .5s var(--ease); }
.stat:hover::before { transform: scale(1.6); }
.stat .big { position: relative; font-size: clamp(2.8rem, 5vw, 3.9rem); font-weight: 600; letter-spacing: -.05em; line-height: 1; color: var(--text); }
.stat .big, .stat .big .num { line-height: 1 !important; }
.stat .big .num { counter-reset: n var(--n); animation: count 1.8s var(--ease) both; }
.stat .big .num::after { content: counter(n); }
.stat .big sup { font-size: .4em; color: var(--accent); margin-left: .12em; vertical-align: top; position: relative; top: .35em; font-weight: 600; }
.stat .lab { position: relative; margin-top: .65rem; color: var(--muted) !important; font-size: .96rem; line-height: 1.5; }

.step { position: relative; padding: 1.6rem 1.5rem 1.5rem; border-radius: var(--radius); background: var(--surface);
        border: 1px solid var(--border); overflow: hidden; transition: transform .35s var(--ease), box-shadow .35s; }
.step::after { content: ""; position: absolute; left: 0; top: 0; height: 3px; width: 100%; background: linear-gradient(90deg, var(--accent), var(--accent2));
               transform: scaleX(0); transform-origin: left; transition: transform .55s var(--ease); }
.step:hover { transform: translateY(-6px); box-shadow: 0 26px 40px -26px var(--shadow); }
.step:hover::after { transform: scaleX(1); }
.step .ix { font-family: 'Geist Mono', monospace; font-size: .8rem; font-weight: 600; letter-spacing: .1em; color: var(--accent) !important; }
.step .ic { width: 48px; height: 48px; border-radius: 14px; display: grid; place-items: center; margin: .9rem 0 1rem;
            background: var(--surface2); transition: transform .4s var(--ease), background .3s; }
.step:hover .ic { transform: rotate(-8deg) scale(1.08); background: var(--glow); }
.step .ic svg { stroke: var(--text); fill: none; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.step h4 { margin: 0 0 .35rem; font-size: 1.2rem; font-weight: 600; letter-spacing: -.02em; color: var(--text); }
.step p { margin: 0; color: var(--muted) !important; font-size: .96rem; line-height: 1.55; }

.vs { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1.6rem; text-align: left; }
.vs .c { padding: 1.7rem 1.6rem; border-radius: var(--radius); border: 1px solid var(--border); background: var(--surface); }
.vs .c.us { background: var(--ink); border-color: var(--ink); position: relative; overflow: hidden; }
.vs .c.us::before { content: ""; position: absolute; width: 260px; height: 260px; right: -90px; top: -90px; border-radius: 50%;
                    background: radial-gradient(circle, var(--accent), transparent 68%); opacity: .5; animation: drift 10s ease-in-out infinite; }
.vs .t { position: relative; font-family: 'Geist Mono', monospace; font-size: .74rem; letter-spacing: .12em; text-transform: uppercase;
         font-weight: 600; color: var(--muted); margin-bottom: 1rem; }
.vs .us .t { color: var(--accent) !important; }
.vs ul { list-style: none; margin: 0; padding: 0; position: relative; }
.vs li { display: flex; gap: .7rem; align-items: flex-start; padding: .62rem 0; font-size: 1rem; color: var(--text) !important;
         border-top: 1px dashed var(--border); }
.vs li:first-child { border-top: none; }
.vs .c:not(.us) li { color: var(--muted) !important; }
.vs .us li { color: var(--onink) !important; border-top-color: color-mix(in srgb, var(--onink) 16%, transparent); }
.vs li::before { flex: none; width: 22px; height: 22px; border-radius: 50%; display: grid; place-items: center; font-size: .75rem; font-weight: 700; margin-top: .05rem; }
.vs .c:not(.us) li::before { content: "✕"; background: var(--surface2); color: var(--muted); }
.vs .us li::before { content: "✓"; background: var(--accent); color: #fff; }
.vs .us li { opacity: 1; transition: transform .3s var(--ease); }
.vs .us li:hover { transform: translateX(6px); }

.foot { margin: 3.4rem 0 .6rem; padding-top: 1.3rem; border-top: 1px dashed var(--border); text-align: center; color: var(--muted) !important;
        font-size: .9rem; }
.foot b { color: var(--text) !important; }

/* ---------- inputs ---------- */
.stTextInput input, .stTextArea textarea, .stNumberInput input {
    background: var(--surface) !important; color: var(--text) !important;
    border: 1px solid var(--border) !important; border-radius: 12px !important; transition: border-color .2s, box-shadow .2s; }
.stTextInput input:focus, .stTextArea textarea:focus { border-color: var(--accent) !important;
    box-shadow: 0 0 0 4px var(--glow) !important; }
.stTextInput input::placeholder, .stTextArea textarea::placeholder { color: var(--muted) !important; opacity:.7; }
div[data-baseweb="select"] > div { background: var(--surface) !important; border: 1px solid var(--border) !important;
    border-radius: 12px !important; color: var(--text) !important; transition: border-color .2s; }
div[data-baseweb="select"] > div:hover { border-color: var(--accent) !important; }
div[data-baseweb="select"] * { color: var(--text) !important; }
div[data-baseweb="select"] svg { fill: var(--muted) !important; }
div[data-baseweb="popover"] > div, div[data-baseweb="popover"] ul, [role="listbox"] {
    background: var(--surface) !important; border-radius: 12px !important; }
div[data-baseweb="popover"] li, [role="option"] { background: var(--surface) !important; color: var(--text) !important; }
div[data-baseweb="popover"] li:hover, [role="option"]:hover, [role="option"][aria-selected="true"] {
    background: var(--surface2) !important; }
[data-testid="stCheckbox"] span { color: var(--text) !important; }

/* ---------- buttons ---------- */
.stButton > button, .stDownloadButton > button {
    position: relative; overflow: hidden; border-radius: 12px; border: 1px solid var(--ink); background: var(--ink);
    color: var(--onink) !important; font-weight: 600; padding: .6rem 1.2rem;
    transition: transform .25s var(--ease), box-shadow .25s, border-color .2s; }
.stButton > button p, .stDownloadButton > button p { color: var(--onink) !important; }
.stButton > button:hover, .stDownloadButton > button:hover { transform: translateY(-2px); box-shadow: 0 12px 22px -12px var(--shadow);
    border-color: var(--ink); color: var(--onink) !important; }
.stButton > button:active { transform: scale(.97); }
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] {
    background: var(--accent); border: none; color: #fff !important; box-shadow: 0 14px 26px -12px var(--accent); }
.stButton > button[kind="primary"] p, .stButton > button[data-testid="stBaseButton-primary"] p { color: #fff !important; }
.stButton > button[kind="primary"]::after, .stButton > button[data-testid="stBaseButton-primary"]::after {
    content: ""; position: absolute; top: 0; bottom: 0; width: 38%; background: rgba(255,255,255,.32);
    animation: sheen 3.8s ease-in-out infinite; pointer-events: none; }
.stButton > button:focus-visible { outline: 2px solid var(--accent2); outline-offset: 2px; }

/* floating theme switch, like Agnos' bottom-right pill */
.st-key-theme_btn { position: fixed !important; right: 22px; bottom: 22px; z-index: 1001; width: auto !important;
                    animation: fadeUp .9s var(--ease) both; animation-delay: 1.4s; }
.st-key-theme_btn button { background: var(--surface) !important; border: 1px solid var(--border) !important;
                           box-shadow: 0 14px 30px -14px var(--shadow); border-radius: 14px; padding: .5rem .95rem; }
.st-key-theme_btn button p { color: var(--text) !important; }

/* ---------- tabs: segmented pill ---------- */
[data-baseweb="tab-list"] { gap: .25rem; background: var(--surface2); padding: .3rem; border-radius: 14px;
    width: fit-content; max-width: 100%; border: 1px solid var(--border); }
[data-baseweb="tab"] { background: transparent !important; color: var(--muted) !important; font-weight: 600;
    padding: .5rem 1.05rem; border-radius: 10px; height: auto; transition: background .25s, color .25s, box-shadow .25s; }
[data-baseweb="tab"]:hover { color: var(--text) !important; }
[data-baseweb="tab"][aria-selected="true"] { color: var(--text) !important; background: var(--surface) !important;
    box-shadow: 0 6px 14px -8px var(--shadow); }
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none !important; }
[data-baseweb="tab-panel"] { animation: fadeUp .6s var(--ease) both; padding-top: 1.1rem; }

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] { background: var(--surface) !important; border-right: 1px solid var(--border); }
[data-testid="stSidebar"] * { color: var(--text); }
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { color: var(--muted) !important; }

/* ---------- containers, expanders, alerts, uploader, code ---------- */
[data-testid="stVerticalBlockBorderWrapper"], [data-testid="stExpander"] {
    border-color: var(--border) !important; border-radius: var(--radius) !important; }
[data-testid="stVerticalBlockBorderWrapper"] { background: var(--surface); animation: fadeUp .7s var(--ease) both; }
[data-testid="stExpander"] { background: var(--surface); transition: border-color .25s, box-shadow .25s; }
[data-testid="stExpander"]:hover { border-color: var(--accent) !important; }
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * { color: var(--text) !important; }
[data-testid="stAlert"] { background: var(--surface2) !important; border: 1px solid var(--border);
    border-radius: 14px; animation: fadeUp .5s var(--ease) both; }
[data-testid="stAlert"] * { color: var(--text) !important; }
[data-testid="stFileUploaderDropzone"] { background: var(--surface) !important; border: 1.5px dashed var(--border) !important;
    border-radius: var(--radius) !important; transition: border-color .25s, background .25s, transform .25s var(--ease); }
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--accent) !important; transform: translateY(-2px); }
[data-testid="stFileUploaderDropzone"] * { color: var(--muted) !important; }
[data-testid="stFileUploaderDropzone"] button { color: var(--text) !important; background: var(--surface2) !important;
    border: 1px solid var(--border) !important; }
[data-testid="stCode"] pre, pre { background: var(--surface2) !important; border-radius: 14px !important; }
[data-testid="stCode"] code { color: var(--text) !important; }
[data-testid="stImage"] img { border-radius: 16px; border: 1px solid var(--border); animation: pop .6s var(--ease) both; }
hr { border-color: var(--border) !important; }

/* loading state: pill with a scanning bar */
[data-testid="stSpinner"] { position: relative; overflow: hidden; width: fit-content; max-width: 100%;
    padding: .65rem 1.1rem; border: 1px solid var(--border); border-radius: 999px; background: var(--surface);
    animation: pulse 1.6s ease-in-out infinite; }
[data-testid="stSpinner"]::after { content: ""; position: absolute; inset: auto 0 0 -100%; height: 3px; width: 100%;
    background: linear-gradient(90deg, transparent, var(--accent), var(--accent2), transparent); animation: scan 1.3s linear infinite; }
[data-testid="stSpinner"] * { color: var(--muted) !important; }

/* ---------- issue card + chips ---------- */
.issue-card { position: relative; padding: 1.2rem 1.35rem; margin: .7rem 0 1rem; border-radius: var(--radius);
    border: 1.5px solid transparent;
    background: linear-gradient(var(--surface), var(--surface)) padding-box,
                conic-gradient(from var(--ang), var(--accent), var(--accent2), var(--border) 55%, var(--accent)) border-box;
    animation: rot 7s linear infinite, fadeUp .7s var(--ease) both; }
.issue-card h3 { font-family: 'Geist', sans-serif; font-weight: 600; letter-spacing: -.02em; margin: 0 0 .6rem; font-size: 1.3rem; color: var(--text); }
.chip { display: inline-block; background: var(--surface2); border: 1px solid var(--border); color: var(--muted);
    border-radius: 999px; padding: .14rem .7rem; font-size: .82rem; margin: 0 .35rem .35rem 0; transition: transform .2s var(--ease), border-color .2s; }
.chip:hover { transform: translateY(-2px); border-color: var(--accent); }
.empty { border: 1.5px dashed var(--border); border-radius: var(--radius); padding: 1.6rem; color: var(--muted);
    text-align: center; margin-top: .8rem; animation: fadeUp .6s var(--ease) both; }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; scroll-behavior: auto !important; }
}
/* header must not swallow clicks meant for the floating nav */
[data-testid="stHeader"] { pointer-events: none !important; }
[data-testid="stHeader"] button, [data-testid="stHeader"] a, [data-testid="stToolbar"],
[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapseButton"] { pointer-events: auto !important; }
.nav, .nav * { pointer-events: auto !important; }
.nav { z-index: 1000001 !important; }

/* inputs: style the BaseWeb wrappers too (they were staying dark in light theme) */
div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="textarea"] {
  background: var(--surface) !important; border-color: var(--border) !important; border-radius: 12px !important; }
div[data-baseweb="input"] > div, div[data-baseweb="base-input"] > div { background: transparent !important; }
div[data-baseweb="input"] button, div[data-baseweb="input"] svg { color: var(--muted) !important; fill: var(--muted) !important;
  background: transparent !important; }
div[data-baseweb="input"]:focus-within, div[data-baseweb="base-input"]:focus-within {
  border-color: var(--accent) !important; box-shadow: 0 0 0 4px var(--glow) !important; }
.stTextInput input { box-shadow: none !important; }
[data-testid="stTooltipIcon"] svg, [data-testid="stTooltipHoverTarget"] svg { color: var(--muted) !important; fill: var(--muted) !important; }

/* expander (Advanced) */
[data-testid="stExpander"] details, [data-testid="stExpander"] summary,
[data-testid="stExpanderDetails"] { background: var(--surface) !important; color: var(--text) !important; }
[data-testid="stExpander"] summary { border-radius: 14px; }
[data-testid="stExpander"] summary:hover { background: var(--surface2) !important; }
[data-testid="stExpander"] summary svg { fill: var(--text) !important; color: var(--text) !important; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] * { color: var(--muted) !important; }

/* sidebar arrows: always visible (Streamlit hides them unless hovered / while rerunning) */
[data-testid="stSidebarCollapseButton"], [data-testid="stSidebarCollapseButton"] *,
[data-testid="stExpandSidebarButton"], [data-testid="stExpandSidebarButton"] *,
[data-testid="stSidebarCollapsedControl"], [data-testid="stSidebarCollapsedControl"] *,
[data-testid="stSidebarHeader"] button {
  opacity: 1 !important; visibility: visible !important; }
[data-testid="stSidebarCollapsedControl"], [data-testid="stExpandSidebarButton"] { display: flex !important; }

/* aligned form controls: same height, bottoms lined up */
[data-testid="stHorizontalBlock"] { align-items: flex-end !important; }
div[data-baseweb="select"] > div, div[data-baseweb="input"], div[data-baseweb="base-input"] {
  min-height: 46px !important; box-sizing: border-box; align-items: center; }
div[data-baseweb="select"] > div { padding-left: .35rem; }
.stTextInput input { height: 46px; }
div[data-baseweb="select"] { width: 100% !important; }
div[data-baseweb="popover"] li, [role="option"] { text-align: left !important; }
[data-testid="stSelectbox"], [data-testid="stTextInput"] { margin-bottom: .4rem; }

/* sidebar expand arrow: make it clearly visible */
[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"] button,
[data-testid="stSidebarCollapseButton"] button { color: var(--accent) !important; }
[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"] button {
  background: var(--surface2) !important; border: 1px solid var(--accent) !important; border-radius: 10px !important; }
[data-testid="stExpandSidebarButton"] *, [data-testid="stSidebarCollapsedControl"] *,
[data-testid="stSidebarCollapseButton"] * { color: var(--accent) !important; fill: var(--accent) !important; }
[data-testid="stExpandSidebarButton"]:hover, [data-testid="stSidebarCollapsedControl"] button:hover {
  background: var(--accent) !important; }
[data-testid="stExpandSidebarButton"]:hover *, [data-testid="stSidebarCollapsedControl"] button:hover * {
  color: #fff !important; fill: #fff !important; }
/* page zoom */
html { zoom: 1.25; }
</style>
"""


def inject_css():
    css = CSS
    for k, v in THEMES[st.session_state["theme"]].items():
        css = css.replace(f"__{k}__", v)
    st.markdown(css, unsafe_allow_html=True)


def flip_theme():
    st.session_state["theme"] = "light" if st.session_state["theme"] == "dark" else "dark"


def H(s: str) -> str:
    """Flatten HTML so Streamlit's markdown parser never treats it as a code block."""
    return "\n".join(line.strip() for line in s.strip().splitlines() if line.strip())


inject_css()

# --------------------------------------------------------------------------
# Landing: nav, hero, marquee, stats, how-it-works, comparison
# --------------------------------------------------------------------------
LOGO = """<svg width="30" height="30" viewBox="0 0 64 64" fill="none" aria-hidden="true">
<circle cx="32" cy="32" r="28" stroke="var(--border)" stroke-width="4"/>
<g class="needle"><path d="M32 8 L40 32 L32 56 L24 32 Z" fill="var(--accent)"/><path d="M32 8 L40 32 L32 32 Z" fill="var(--accent2)"/></g>
<circle cx="32" cy="32" r="3.5" fill="var(--bg)"/></svg>"""

ICONS = {
    "branch": '<circle cx="6" cy="6" r="2.2"/><circle cx="6" cy="18" r="2.2"/><circle cx="18" cy="8" r="2.2"/><path d="M6 8.2v7.6M18 10.2c0 4-6 3-11 6.5"/>',
    "bug": '<rect x="8" y="9" width="8" height="10" rx="4"/><path d="M12 9V5M9 6l1.5 2M15 6l-1.5 2M4 13h4M16 13h4M5 19l3-2M19 19l-3-2"/>',
    "image": '<rect x="3" y="4" width="18" height="16" rx="3"/><circle cx="9" cy="10" r="1.6"/><path d="M4 18l5-5 4 4 3-3 4 4"/>',
    "pr": '<circle cx="6" cy="6" r="2.2"/><circle cx="6" cy="18" r="2.2"/><circle cx="18" cy="18" r="2.2"/><path d="M6 8.2v7.6M18 15.8V10a3 3 0 0 0-3-3h-3m2-2l-2 2 2 2"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>',
    "spark": '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5L18 18M18 6l-2.5 2.5M8.5 15.5L6 18"/>',
    "rocket": '<path d="M5 15c-1.5 1.5-2 5-2 5s3.5-.5 5-2M14 4c3-1 6-1 6-1s0 3-1 6l-6 6-5-5 6-6z"/><circle cx="15" cy="9" r="1.3"/>',
}


def icon(name: str, size: int = 28) -> str:
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24">{ICONS[name]}</svg>')


def headline() -> str:
    lines = [["Find", "your", "first", "issue."], ["Then", "ship", "it."]]
    out, i = [], 0
    for ln, words in enumerate(lines):
        for w in words:
            if w == "ship":
                out.append(
                    f'<span class="acc"><span class="w" style="--i:{i}"><span>{w}</span></span>'
                    '<svg viewBox="0 0 120 12" preserveAspectRatio="none" aria-hidden="true">'
                    '<path pathLength="1" d="M2 8 Q 20 0 40 6 T 80 6 T 118 4"/></svg></span> ')
            else:
                out.append(f'<span class="w" style="--i:{i}"><span>{w}</span></span> ')
            i += 1
        if ln == 0:
            out.append("<br>")
    return "".join(out)


NAV = f"""
<div class="nav">
<a class="brand" href="#top">{LOGO}IssueScout</a>
<a class="l" href="#how">How it works</a>
<a class="l" href="#tool">Try it</a>
<a class="go" href="#tool">Get started</a>
</div>
"""

HERO = f"""
<div id="top"></div>
<div class="hero2">
<div class="orb a"></div><div class="orb b"></div>
<div class="ring" style="--s:700px;--k:1"></div>
<div class="ring" style="--s:940px;--k:2"></div>
<div class="ring" style="--s:1180px;--k:3"></div>
<div class="ring" style="--s:1420px;--k:4"></div>
<div class="sweep"></div>
<span class="blip" style="left:19%;top:30%;--t:.2s"></span>
<span class="blip" style="left:82%;top:64%;--t:1.4s"></span>
<span class="blip" style="left:12%;top:70%;--t:2.3s"></span>
<span class="blip" style="left:88%;top:26%;--t:.9s"></span>
<div class="tile" style="left:6%;top:20%;--r:-8deg;--t:0s">{icon("branch")}</div>
<div class="tile o" style="right:6%;top:17%;--r:9deg;--t:-2s">{icon("bug")}</div>
<div class="tile o" style="left:10%;bottom:14%;--r:7deg;--t:-4s">{icon("image")}</div>
<div class="tile" style="right:9%;bottom:16%;--r:-6deg;--t:-1s">{icon("pr")}</div>
<div class="in">
<span class="eyebrow"><i>&rsaquo;</i> Hacktoberfest 2026 <i>&lsaquo;</i></span>
<div class="h1">{headline()}</div>
<p class="sub">IssueScout finds a beginner-friendly issue you can actually finish, then hands you a clear, step-by-step plan to ship it.</p>
<div class="ctas">
<a class="btn p" href="#tool">Start scouting <span class="ar">&rarr;</span></a>
<a class="btn d" href="#how">See how it works</a>
</div>
<div class="note">Free to use &middot; bring your own Gemini key</div>
</div>
</div>
"""

REPOS = ["pallets/flask", "django/django", "facebook/react", "microsoft/vscode", "rust-lang/rust",
         "vuejs/core", "tensorflow/tensorflow", "home-assistant/core", "nodejs/node", "kubernetes/kubernetes"]
_items = "".join(f'<span class="it"><i></i>{r}</span>' for r in REPOS)

TRUST = f"""
<div class="trust reveal">
<div class="cap"><span>Works with <b>any public</b> GitHub repo</span></div>
<div class="marq"><div class="track">{_items}{_items}</div></div>
</div>
"""

STATS = """
<div class="grid3">
<div class="stat reveal" style="--d:0"><div class="big"><span class="num" style="--n:30"></span><sup>+</sup></div>
<div class="lab">open issues pulled per search, filtered by label and assignee.</div></div>
<div class="stat reveal" style="--d:1"><div class="big"><span class="num" style="--n:300"></span><sup>files</sup></div>
<div class="lab">of the real repo tree mapped, so plans only point at files that exist.</div></div>
<div class="stat reveal" style="--d:2"><div class="big"><span class="num" style="--n:3"></span><sup>models</sup></div>
<div class="lab">in an automatic fallback chain, so a busy model never blocks you.</div></div>
</div>
"""

HOW = f"""
<div class="sec reveal" id="how">
<span class="eyebrow"><i>&rsaquo;</i> How it works <i>&lsaquo;</i></span>
<div class="h2">From &ldquo;where do I start?&rdquo; to <em>merged</em> in three moves</div>
<p class="lead">Each step is one tab below. Use them in order, or jump straight to the one you need.</p>
</div>
<div class="grid3">
<div class="step reveal" style="--d:0"><span class="ix">01</span><div class="ic">{icon("search")}</div>
<h4>Find an issue</h4><p>Paste a repo, pick a label, and choose from unassigned issues. Get a plain-English summary, difficulty and a plan.</p></div>
<div class="step reveal" style="--d:1"><span class="ix">02</span><div class="ic">{icon("image")}</div>
<h4>Decode the error</h4><p>Drop in a screenshot of a stack trace or UI bug and get the likely cause with step-by-step fixes.</p></div>
<div class="step reveal" style="--d:2"><span class="ix">03</span><div class="ic">{icon("rocket")}</div>
<h4>Write the PR</h4><p>Paste your git diff and receive a conventional commit message and a ready-to-post PR description.</p></div>
</div>
"""

VS = """
<div class="sec reveal" style="margin-top:3.8rem">
<span class="eyebrow"><i>&rsaquo;</i> Why IssueScout <i>&lsaquo;</i></span>
<div class="h2">Skip the guesswork that makes <em>first PRs</em> stall</div>
</div>
<div class="vs">
<div class="c reveal" style="--d:0"><div class="t">Browsing alone</div><ul>
<li>Scrolling hundreds of issues with no idea what&rsquo;s doable</li>
<li>Unclear which files to touch</li>
<li>Pasting errors into search and hoping</li>
<li>Staring at a blank PR description</li></ul></div>
<div class="c us reveal" style="--d:1"><div class="t">With IssueScout</div><ul>
<li>Label filters and unassigned-only results</li>
<li>Likely files picked from the real repo tree</li>
<li>Screenshots explained step by step</li>
<li>Commit message and PR text from your diff</li></ul></div>
</div>
"""

SECTION_TOOL = """
<div class="sec reveal" id="tool" style="margin-bottom:1.4rem">
<span class="eyebrow"><i>&rsaquo;</i> The toolkit <i>&lsaquo;</i></span>
<div class="h2">Pick a tool and <em>start scouting</em></div>
<p class="lead">Add your Gemini key in the sidebar, then try one of the three workflows.</p>
</div>
"""

# Make in-page anchor links (nav pill + hero buttons) actually scroll.
# Streamlit scrolls inside its own container, so plain #hash links don't work;
# this zero-height iframe installs one delegated click handler on the parent page.
import streamlit.components.v1 as components
components.html(
    """
<script>
(function () {
  const doc = window.parent.document;
  if (window.parent.__issuescoutNav) return;
  window.parent.__issuescoutNav = true;
  doc.addEventListener("click", function (e) {
    const a = e.target.closest && e.target.closest('a[href^="#"]');
    if (!a) return;
    const id = a.getAttribute("href").slice(1);
    const target = id === "top" ? null : doc.getElementById(id);
    if (id !== "top" && !target) return;
    e.preventDefault();
    e.stopPropagation();
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    } else {
      const m = doc.querySelector('[data-testid="stMain"], section.main, .main');
      if (m) m.scrollTo({ top: 0, behavior: "smooth" });
      window.parent.scrollTo({ top: 0, behavior: "smooth" });
    }
    try { window.parent.history.replaceState(null, "", "#" + id); } catch (_) {}
  }, true);
})();
</script>
""",
    height=0,
)

st.markdown(H(NAV), unsafe_allow_html=True)
st.markdown(H(HERO), unsafe_allow_html=True)
st.markdown(H(TRUST), unsafe_allow_html=True)
st.markdown(H(STATS), unsafe_allow_html=True)
st.markdown(H(HOW), unsafe_allow_html=True)
st.markdown(H(VS), unsafe_allow_html=True)
st.markdown(H(SECTION_TOOL), unsafe_allow_html=True)

# floating theme switch (pinned bottom-right via CSS)
st.button("🌙 Dark" if st.session_state["theme"] == "light" else "☀️ Light",
          on_click=flip_theme, key="theme_btn")

# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Keys")
    st.text_input("Gemini API key", type="password", value=DEFAULT_KEY, key="gemini_key")
    st.text_input("GitHub token (optional)", type="password", value=DEFAULT_GH, key="gh_token",
                  help="Raises GitHub's rate limit from 60 to 5,000 requests per hour.")
    st.markdown("Get a free Gemini key at [aistudio.google.com](https://aistudio.google.com).")
    with st.expander("Advanced"):
        st.text_input("Model ID", value=DEFAULT_MODEL, key="model_id",
                      help="If this model is unavailable, IssueScout falls back automatically.")
        st.caption("Fallbacks: " + ", ".join(FALLBACK_MODELS))

# --------------------------------------------------------------------------
# GitHub helpers
# --------------------------------------------------------------------------
class GHError(Exception):
    pass


def gh_headers(token: str):
    h = {"Accept": "application/vnd.github+json", "User-Agent": "IssueScout"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def gh_get(path: str, token: str, params=None):
    try:
        r = requests.get(f"https://api.github.com{path}", params=params,
                         headers=gh_headers(token), timeout=20)
    except requests.exceptions.RequestException:
        raise GHError("Couldn't reach GitHub. Check your connection and try again.")
    if r.status_code == 401:
        raise GHError("GitHub rejected your token. Clear it or paste a valid one.")
    if r.status_code == 404:
        raise GHError("Repository not found. Check the URL (private repos need a token).")
    if r.status_code in (403, 429):
        raise GHError("GitHub rate limit reached. Add a free GitHub token in the sidebar, or wait a few minutes.")
    if not r.ok:
        raise GHError(f"GitHub returned an error ({r.status_code}). Try again shortly.")
    try:
        return r.json()
    except ValueError:
        raise GHError("GitHub sent an unreadable response. Try again.")


def parse_repo(text: str):
    text = (text or "").strip()
    m = re.search(r"github\.com[/:]([^/\s]+)/([^/\s#?]+)", text)
    if not m:
        m = re.fullmatch(r"([\w.-]+)/([\w.-]+)", text)  # "owner/repo" shorthand
    if not m:
        return None, None
    return m.group(1), m.group(2).removesuffix(".git")


@st.cache_data(ttl=300, show_spinner=False)
def get_issues(owner: str, repo: str, label: str, token: str):
    params = {"state": "open", "per_page": 30}
    if label:
        params["labels"] = label
    data = gh_get(f"/repos/{owner}/{repo}/issues", token, params)
    if not isinstance(data, list):
        return []
    return [i for i in data if "pull_request" not in i]


NOISE_EXT = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2", ".ttf", ".lock",
             ".map", ".min.js", ".pdf", ".zip", ".mp4")


@st.cache_data(ttl=300, show_spinner=False)
def get_file_paths(owner: str, repo: str, token: str):
    """Best-effort list of repo files. Never raises: the plan still works without it."""
    try:
        data = gh_get(f"/repos/{owner}/{repo}/git/trees/HEAD", token, {"recursive": 1})
        tree = data.get("tree", []) if isinstance(data, dict) else []
    except GHError:
        return []
    paths = [t["path"] for t in tree if t.get("type") == "blob"
             and not t["path"].lower().endswith(NOISE_EXT)
             and not t["path"].startswith(("node_modules/", "vendor/", "dist/", "build/"))]
    return paths[:300]


# --------------------------------------------------------------------------
# AI helpers (retries, model fallback, friendly errors)
# --------------------------------------------------------------------------
class AIError(Exception):
    pass


RETRYABLE = ("429", "500", "502", "503", "504", "unavailable", "resource_exhausted",
             "deadline", "timed out", "timeout", "overloaded", "connection")
AUTH_BAD = ("api_key_invalid", "api key not valid", "permission_denied", "unauthenticated", "invalid api key")


@st.cache_resource(show_spinner=False)
def get_client(key: str):
    if types is not None:
        try:
            return genai.Client(api_key=key, http_options=types.HttpOptions(timeout=90_000))
        except Exception:
            pass
    return genai.Client(api_key=key)


def model_chain():
    primary = (st.session_state.get("model_id") or DEFAULT_MODEL).strip()
    chain = []
    for m in [primary] + FALLBACK_MODELS:
        if m and m not in chain:
            chain.append(m)
    return chain


def call_ai(contents):
    """Returns (text, model_used). Raises AIError with a human-readable message."""
    key = (st.session_state.get("gemini_key") or "").strip()
    if not key:
        raise AIError("Add your Gemini API key in the sidebar first.")
    try:
        client = get_client(key)
    except Exception as e:
        raise AIError(f"Couldn't start the AI client: {e}")

    last = "unknown error"
    for model in model_chain():
        for attempt in range(3):
            try:
                resp = client.models.generate_content(model=model, contents=contents)
                text = (getattr(resp, "text", None) or "").strip()
                if text:
                    return text, model
                last = "the model returned an empty answer (it may have been blocked by a safety filter)"
                break  # try next model
            except Exception as e:  # noqa: BLE001 - SDK raises many types
                msg = str(e)
                low = msg.lower()
                last = msg.splitlines()[0][:220]
                if any(k in low for k in AUTH_BAD):
                    raise AIError("Your Gemini API key was rejected. Check it in the sidebar.")
                if any(k in low for k in RETRYABLE):
                    time.sleep(1.5 * (2 ** attempt))
                    continue
                break  # not found / unsupported input / other: move to next model
    raise AIError(f"All models failed. Last error: {last}")


def run_ai(spinner_text: str, contents):
    """Wraps call_ai with spinner + error display. Returns result dict or None."""
    try:
        with st.spinner(spinner_text):
            text, model = call_ai(contents)
        return {"text": text, "model": model}
    except AIError as e:
        st.error(str(e))
    except Exception as e:  # last line of defence: the app never crashes
        st.error(f"Something unexpected happened: {e}")
    return None


def show_result(res, download_name=None):
    with st.container(border=True):
        st.markdown(res["text"])
    st.caption(f"Answered by {res['model']}")
    if download_name:
        st.download_button("Download as Markdown", res["text"], file_name=download_name, mime="text/markdown")


# --------------------------------------------------------------------------
# Tabs
# --------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["Find an issue", "Explain a screenshot", "Write a PR"])

# ---------- Tab 1: issues -> plan ----------
with tab1:
    c1, c2 = st.columns([3, 1])
    url = c1.text_input("GitHub repo", "https://github.com/pallets/flask",
                        placeholder="https://github.com/owner/repo or owner/repo")
    label = c2.selectbox("Label", LABELS, index=LABELS.index("(any open issue)"))

    if st.button("Find issues", type="primary"):
        owner, repo = parse_repo(url)
        if not owner:
            st.error("That doesn't look like a GitHub repo. Use https://github.com/owner/repo or owner/repo.")
        else:
            try:
                with st.spinner("Searching GitHub..."):
                    found = get_issues(owner, repo, "" if label.startswith("(") else label,
                                       st.session_state.get("gh_token", ""))
                st.session_state["issues"] = found
                st.session_state["repo"] = (owner, repo)
                st.session_state["searched"] = True
                st.session_state.pop("plan", None)
            except GHError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Something unexpected happened: {e}")

    issues = st.session_state.get("issues", [])
    only_free = st.checkbox("Only show unassigned issues", value=True) if issues else False
    if only_free:
        issues = [i for i in issues if not i.get("assignee") and not i.get("assignees")]

    if st.session_state.get("searched") and not issues:
        st.markdown('<div class="empty">No matching issues. Try another label, '
                    'choose "(any open issue)", or switch repos.</div>', unsafe_allow_html=True)

    if issues:
        by_title = {f"#{i['number']}  {i['title']}": i for i in issues}
        choice = st.selectbox("Pick an issue", list(by_title.keys()))
        issue = by_title[choice]

        chips = [f"{issue.get('comments', 0)} comments"]
        chips += [lb["name"] for lb in issue.get("labels", [])[:4] if isinstance(lb, dict)]
        author = (issue.get("user") or {}).get("login")
        if author:
            chips.append(f"opened by {author}")
        st.markdown(
            f'<div class="issue-card"><h3>{html.escape(issue["title"])}</h3>'
            + "".join(f'<span class="chip">{html.escape(str(c))}</span>' for c in chips)
            + f'<div style="margin-top:.4rem"><a href="{html.escape(issue["html_url"])}" target="_blank">'
              'Open on GitHub</a></div></div>',
            unsafe_allow_html=True)
        with st.expander("Read the issue"):
            st.markdown((issue.get("body") or "_No description provided._")[:3000])

        if st.button("Generate plan", type="primary"):
            owner, repo = st.session_state["repo"]
            paths = "\n".join(get_file_paths(owner, repo, st.session_state.get("gh_token", ""))) \
                or "(file list unavailable)"
            prompt = f"""You are a friendly open-source mentor helping a student make their first contribution.

Issue title: {issue['title']}
Issue body:
{(issue.get('body') or '')[:3000]}

Repository files:
{paths}

Respond in markdown with:
1. **Plain-English summary** (2-3 sentences)
2. **Difficulty** (Easy/Medium/Hard) and estimated time
3. **Files likely involved** (only from the list above)
4. **Step-by-step plan** (fork, branch, change, test, commit)
5. **Pitfalls** to watch for
"""
            res = run_ai("Gemma is reading the issue...", prompt)
            if res:
                res["issue"] = issue["number"]
                st.session_state["plan"] = res
                st.toast("Your plan is ready", icon="🧭")

        plan = st.session_state.get("plan")
        if plan and plan.get("issue") == issue["number"]:
            show_result(plan, f"plan-issue-{issue['number']}.md")

# ---------- Tab 2: multimodal ----------
def load_image(f) -> Image.Image:
    img = Image.open(f)
    img = ImageOps.exif_transpose(img)
    img.load()
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")
    img.thumbnail((1600, 1600))
    return img


with tab2:
    st.write("Upload a screenshot of an error, stack trace, or UI bug.")
    img_file = st.file_uploader("Screenshot", type=["png", "jpg", "jpeg", "webp"])
    note = st.text_input("What are you trying to do? (optional)")

    img = None
    if img_file:
        try:
            img = load_image(img_file)
            st.image(img, width=420)
        except Exception:
            st.error("That image couldn't be opened. Try a PNG or JPG.")

    if img is not None and st.button("Explain screenshot", type="primary"):
        prompt = ("Explain this screenshot to a beginner developer. Say what is wrong, "
                  "the most likely cause, and how to fix it step by step. "
                  f"Context: {note or 'none given'}")
        res = run_ai("Reading your screenshot...", [prompt, img])
        if res:
            st.session_state["shot"] = res
            st.toast("Screenshot explained", icon="🔍")

    if st.session_state.get("shot") and img is not None:
        show_result(st.session_state["shot"], "screenshot-explained.md")

# ---------- Tab 3: PR writer ----------
with tab3:
    st.write("Paste your `git diff` and get a commit message and PR description.")
    diff = st.text_area("git diff", height=260, placeholder="Paste the output of `git diff` here")
    issue_ref = st.text_input("Issue number (optional)", placeholder="123")

    if st.button("Write PR", type="primary"):
        if not diff.strip():
            st.warning("Paste a git diff first.")
        else:
            num = re.sub(r"\D", "", issue_ref or "")
            if len(diff) > 8000:
                st.info("Your diff is long, so only the first 8,000 characters were used.")
            prompt = f"""Write a conventional commit message and a GitHub pull request description
for this diff. Include: Summary, Changes, How to test{', and "Closes #' + num + '"' if num else ''}.
Keep it concise and professional.

DIFF:
{diff[:8000]}"""
            res = run_ai("Writing your PR...", prompt)
            if res:
                st.session_state["pr"] = res
                st.toast("PR description written", icon="🚀")

    if st.session_state.get("pr"):
        show_result(st.session_state["pr"], "pull-request.md")
        with st.expander("Copy-friendly version"):
            st.code(st.session_state["pr"]["text"], language="markdown")

# --------------------------------------------------------------------------
# Footer
# --------------------------------------------------------------------------
st.markdown(H("""
<div class="foot reveal"><b>IssueScout</b> &middot; Built for Hacktoberfest 2026 &middot; Powered by Gemma via the Gemini API</div>
"""), unsafe_allow_html=True)
