import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    layout="wide", 
    page_title="Arkeos Technical Dashboard v2",
    page_icon="📊"
)

# --- STYLE CSS (Look Professionnel) ---
st.markdown("""
    <style>
        .main { background-color: #f8f9fa; }
        [data-testid="stMetricValue"] { font-size: 26px; font-weight: 700; color: #1e293b; }
        .stMetric {
            background-color: #ffffff;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            border: 1px solid #e2e8f0;
        }
        div.stButton > button:first-child {
            background-color: #3b82f6;
            color: white;
            border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# --- CHARGEMENT DES DONNÉES ---
@st.cache_data
def load_data():
    f = "data_dynamics_brute.csv.csv.csv"
    try:
        # Lecture avec détection automatique du séparateur
        df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
        
        # Mapping des colonnes
        col_map = {
            'date': 'Date', 'créé': 'Date',
            'actif': 'SN', 'asset': 'SN', 'série': 'SN', 'sn': 'SN',
            'owner': 'Tech', 'propriétaire': 'Tech', 'tech': 'Tech',
            'client': 'Client', 'compte': 'Client', 'customer': 'Client'
        }
        
        new_cols = {}
        for c in df.columns:
            low_c = str(c).lower()
            for key, val in col_map.items():
                if key in low_c:
                    new_cols[c] = val
                    break
        
        df = df.rename(columns=new_cols)
