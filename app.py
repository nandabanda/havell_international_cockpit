import streamlit as st

st.set_page_config(
    page_title="SYDIAI Havell Cockpit",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
section[data-testid="stSidebarNav"] {display: none !important;}

</style>
""", unsafe_allow_html=True)
import streamlit as st
from core.ui_theme import apply_ivory
from core.nav_shell import render_premium_nav

st.set_page_config(
    page_title="Havell International Cockpit",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 🚫 Disable default multipage sidebar
st.sidebar.markdown(" ", unsafe_allow_html=True)

# 🎨 Apply theme
apply_ivory()

# 🚀 Render premium navigation
render_premium_nav("control_tower")

# 📊 Load Control Tower page
exec(open("pages/0_Control_Tower.py").read(), globals())
