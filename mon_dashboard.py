import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import datetime

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Arkeos Dashboard", page_icon="📊")

# --- STYLE CSS ---
st.markdown("""
    <style>
        .main { background-color: #f8f9fa; }
        div[data-testid="stMetric"] {
            background-color: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border: 1px solid #eef2f6;
        }
    </style>
""", unsafe_allow_html=True)

# --- FONCTION DE CHARGEMENT ---
@st.cache_data
def load_data():
    f = "data_dynamics_brute.csv.csv.csv"
    try:
        df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
    except:
        return pd.DataFrame()

    col_map = {
        'date': 'Date', 'créé': 'Date',
        'actif': 'SN', 'asset': 'SN', 'sn': 'SN',
        'owner': 'Tech', 'tech': 'Tech',
        'client': 'Client', 'customer': 'Client'
    }
    
    new_cols = {}
    for c in df.columns:
        low_c = str(c).lower()
        for key, val in col_map.items():
            if key in low_c:
                new_cols[c] = val
                break
    
    df = df.rename(columns=new_cols)
    
    if 'Date' not in df.columns or 'SN' not in df.columns:
        return pd.DataFrame()

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
    
    # Sécurisation des colonnes Tech et Client
    if 'Tech' not in
