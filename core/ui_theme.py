import streamlit as st

IVORY_CSS = """
<style>
:root{
  --bg:#F6F2E9;          /* ivory background */
  --panel:#FBF8F2;       /* panel surface */
  --card:#FFFFFF;        /* card */
  --border:rgba(30,40,60,.10);
  --text:#111827;
  --muted:#475569;
  --accent:#1F4B99;      /* deep blue accent */
  --accent2:#0EA5A4;     /* teal accent */
  --shadow:0 10px 28px rgba(15,23,42,.08);
  --shadow2:0 18px 44px rgba(15,23,42,.10);
}

.stApp{
  background:
    radial-gradient(1000px 550px at 20% -10%, rgba(31,75,153,.10), transparent 60%),
    radial-gradient(900px 520px at 80% 0%, rgba(14,165,164,.08), transparent 55%),
    var(--bg);
  color: var(--text);
}

.block-container{ padding-top: 1.2rem; padding-bottom: 2.2rem; max-width: 1320px; }

h1,h2,h3,h4{ color: var(--text) !important; letter-spacing: .2px; }
p,li,span,div{ color: var(--text); }

.small-muted{ color: var(--muted) !important; font-size: .94rem; line-height: 1.35rem; }

.pill{
  display:inline-block;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: rgba(251,248,242,.85);
  color: var(--muted);
  font-size: .84rem;
  margin-right: 8px;
}

.section{
  border: 1px solid var(--border);
  background: rgba(251,248,242,.92);
  border-radius: 18px;
  padding: 14px 14px 12px 14px;
  box-shadow: var(--shadow);
  margin-bottom: 14px;
}

.section-title{ font-size: 1.08rem; font-weight: 760; }
.section-sub{ font-size: .92rem; color: var(--muted); margin-top: 4px; }

.kpi-grid{ display:grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
@media (max-width: 1100px){ .kpi-grid{ grid-template-columns: repeat(2, 1fr);} }
@media (max-width: 640px){ .kpi-grid{ grid-template-columns: repeat(1, 1fr);} }

.kpi-card{
  background: linear-gradient(180deg, rgba(255,255,255,.96), rgba(251,248,242,.96));
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 14px 14px 12px 14px;
  box-shadow: var(--shadow2);
  position: relative;
  overflow: hidden;
}

.kpi-title{ font-size: .80rem; color: var(--muted); text-transform: uppercase; letter-spacing: .06em; }
.kpi-value{ font-size: 1.62rem; font-weight: 820; margin-top: 4px; }
.kpi-help{ font-size: .92rem; color: var(--muted); margin-top: 8px; line-height: 1.30rem; }

.hrline{ height:1px; background: rgba(30,40,60,.10); margin: 12px 0 12px 0; }
</style>
"""

def apply_ivory():
    st.markdown(IVORY_CSS, unsafe_allow_html=True)

def pills(items):
    st.markdown("".join([f"<span class='pill'>{x}</span>" for x in items]), unsafe_allow_html=True)

def section(title: str, subtitle: str):
    st.markdown(
        f"<div class='section'><div class='section-title'>{title}</div>"
        f"<div class='section-sub'>{subtitle}</div></div>",
        unsafe_allow_html=True
    )

def kpi(title: str, value: str, help_line: str):
    st.markdown(
        f"<div class='kpi-card'><div class='kpi-title'>{title}</div>"
        f"<div class='kpi-value'>{value}</div>"
        f"<div class='kpi-help'>{help_line}</div></div>",
        unsafe_allow_html=True
    )
