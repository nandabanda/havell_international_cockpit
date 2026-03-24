import streamlit as st

def render_premium_nav(active: str = ""):
    with st.sidebar:
        st.markdown(
            """
            <div style="
                padding:14px 14px 10px 14px;
                border:1px solid rgba(30,40,60,.10);
                border-radius:20px;
                background:linear-gradient(180deg, rgba(255,255,255,.96), rgba(248,244,236,.96));
                box-shadow:0 14px 34px rgba(15,23,42,.08);
                margin-bottom:14px;
            ">
                <div style="font-size:0.78rem; letter-spacing:.14em; color:#6b7280; text-transform:uppercase; font-weight:700;">
                    SYDIAI
                </div>
                <div style="font-size:1.35rem; font-weight:800; color:#111827; margin-top:4px;">
                    Havell International Cockpit
                </div>
                <div style="font-size:0.88rem; color:#475569; margin-top:6px; line-height:1.35rem;">
                    Unified international command layer across hunting, farming, profitability, supply and governance.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <style>
            section[data-testid="stSidebar"] .stPageLink a {
                background: linear-gradient(180deg, rgba(255,255,255,.94), rgba(248,244,236,.94));
                border: 1px solid rgba(30,40,60,.10);
                border-radius: 14px;
                padding: 8px 10px;
                margin: 4px 0;
                text-decoration: none !important;
                box-shadow: 0 6px 18px rgba(15,23,42,.05);
            }
            section[data-testid="stSidebar"] .stPageLink a:hover {
                border-color: rgba(31,75,153,.32);
                transform: translateY(-1px);
                box-shadow: 0 10px 22px rgba(15,23,42,.08);
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        def section_label(text):
            st.markdown(
                f"""
                <div style="
                    margin:12px 2px 6px 2px;
                    font-size:.78rem;
                    font-weight:800;
                    color:#6b7280;
                    letter-spacing:.12em;
                    text-transform:uppercase;
                ">{text}</div>
                """,
                unsafe_allow_html=True,
            )

        section_label("Control Tower")
        st.page_link("app.py", label="Command Centre", icon="🛰️")

        section_label("Hunting")
        st.page_link("pages/1_Hunting_Cockpit.py", label="Hunting Cockpit", icon="🎯")
        st.page_link("pages/1_1_Business_Development_Studio.py", label="Business Development Studio", icon="🧭")
        st.page_link("pages/1_2_Institutional_Revenue_Intelligence.py", label="Revenue Intelligence", icon="💰")
        st.page_link("pages/1_3_Institutional_Supply_Orchestration.py", label="Supply Orchestration", icon="📦")
        st.page_link("pages/1_4_Channel_Profitability_Studio.py", label="Channel Profitability", icon="📈")

        section_label("Farming")
        st.page_link("pages/2_1_Distributor_Development.py", label="Distributor Development", icon="🧩")
        st.page_link("pages/3_Farming_Cockpit.py", label="Farming Cockpit", icon="🌾")
        st.page_link("pages/3_1_Distributor_Revenue_Intelligence.py", label="Distributor Revenue Intelligence", icon="💵")
        st.page_link("pages/3_2_Distributor_Supply_Orchestration.py", label="Distributor Supply Orchestration", icon="🚚")
        st.page_link("pages/3_3_Distributor_Profitability_Studio.py", label="Distributor Profitability", icon="💼")

        section_label("Governance")
        st.page_link("pages/4_RGM_Guardrails.py", label="RGM Guardrails", icon="🛡️")
        st.page_link("pages/5_Supply_Sync.py", label="Supply Sync", icon="🔄")

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
