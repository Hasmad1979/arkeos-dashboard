import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import BytesIO

# Configuration de la page
st.set_page_config(layout="wide", page_title="Arkeos Analytics Pro", page_icon="📟")

# Style CSS pour les cartes personnalisées
st.markdown("""
    <style>
    .metric-card {
        background-color: #1e2129;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #333;
        margin-bottom: 10px;
    }
    .metric-label { font-size: 14px; color: #a3a8b4; margin-bottom: 5px; }
    .metric-value { font-size: 28px; font-weight: bold; color: white; }
    .status-red { border-left: 5px solid #ff4b4b !important; }
    .status-green { border-left: 5px solid #00cc96 !important; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data_pro():
    f = "data_dynamics_brute.csv.csv.csv" #
    if not os.path.exists(f): return pd.DataFrame()
    
    df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
    
    # Identification unique pour éviter "duplicate keys"
    col_date, col_sn, col_tech, col_client = None, None, None, None
    for c in df.columns:
        l = str(c).lower()
        if not col_date and ('date' in l or 'créé' in l): col_date = c
        elif not col_sn and any(x in l for x in ['actif', 'asset', 'sn']): col_sn = c
        elif not col_tech and any(x in l for x in ['owner', 'propriétaire', 'tech']): col_tech = c
        elif not col_client and any(x in l for x in ['client', 'account', 'société']): col_client = c

    rename_dict = {col_date: 'Date', col_sn: 'SN', col_tech: 'Tech', col_client: 'Client'}
    df = df.rename(columns={k: v for k, v in rename_dict.items() if k is not None})
    
    # Filtrage colonnes essentielles
    df = df[[c for c in ['Date', 'SN', 'Tech', 'Client'] if c in df.columns]].copy()
    
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
    df = df.drop_duplicates(subset=['SN', 'Date']).reset_index(drop=True)
    
    # Calcul RDR
    df['Prev'] = df.groupby('SN')['Date'].shift(1)
    df['R'] = (df['Date'] - df['Prev']).dt.days.apply(lambda x: 1 if pd.notna(x) and 0 <= x <= 22 else 0)
    
    return df

df = load_data_pro()

if df.empty:
    st.error("Données introuvables. Vérifiez le fichier CSV.")
else:
    # --- Barre Latérale ---
    st.sidebar.image("https://via.placeholder.com/150x50?text=ARKEOS", use_container_width=True)
    years = sorted(df['Date'].dt.year.unique().tolist(), reverse=True)
    sel_yr = st.sidebar.multiselect("Période (Années)", years, default=years[:1])
    
    techs = sorted(df['Tech'].unique().tolist())
    sel_tk = st.sidebar.selectbox("Filtre Technicien", ["Tous"] + techs)
    
    mask = df['Date'].dt.year.isin(sel_yr)
    if sel_tk != "Tous": mask = mask & (df['Tech'] == sel_tk)
    f_df = df[mask].copy()

    # --- Header ---
    st.title("📟 Support Technical Performance")
    st.markdown(f"Analyse basée sur **{len(f_df):,}** interventions.")

    # --- KPIs avec Couleurs Dynamiques ---
    reps = f_df['R'].sum()
    rdr = (reps / len(f_df) * 100) if len(f_df) > 0 else 0
    fttr = 100 - rdr

    # Logique de couleur
    rdr_class = "status-red" if rdr > 20 else "status-green"
    fttr_class = "status-green" if fttr > 60 else "status-red"

    c1, c2
