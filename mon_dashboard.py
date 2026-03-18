import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io

# --- 1. CONFIGURATION ET DESIGN CORPORATE ---
# Toujours mettre set_page_config en TOUT PREMIER
st.set_page_config(page_title="Arkeos AI Dashboard", layout="wide")

# Masquer les éléments Streamlit par défaut
hide_st_style = """
            <style>
            [data-testid="stToolbar"] {visibility: hidden !important;}
            footer {visibility: hidden !important;}
            [data-testid="stFooter"] {display: none !important;}
            header {visibility: hidden !important;}
            .main { background-color: #F8FAFC; }
            .kpi-card {
                background-color: white; padding: 20px; border-radius: 12px;
                border: 1px solid #E2E8F0; text-align: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            }
            .insight-card {
                background-color: #EFF6FF; padding: 15px; border-radius: 10px;
                border-left: 5px solid #1E3A8A; margin-bottom: 20px;
            }
            .value-blue { color: #1E3A8A; font-weight: 800; font-size: 28px; }
            .value-red { color: #DC2626; font-weight: 800; font-size: 28px; }
            .value-green { color: #16A34A; font-weight: 800; font-size: 28px; }
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- 2. GESTION DE LA SÉCURITÉ ---
USERS = {
    "admin": "Arkeos2026",
    "technicien": "ArkeosTech2026"
}

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    st.markdown("<br><br>", unsafe_allow_html=True)
    col_l, col_c, col_r = st.columns([1, 1.5, 1])
    with col_c:
        st.title("🔐 Accès Arkeos")
        user = st.text_input("Identifiant")
        pw = st.text_input("Mot de
