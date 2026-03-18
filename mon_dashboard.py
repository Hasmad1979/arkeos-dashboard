import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px

# 1. CONFIGURATION ET STYLE PREMIUM
st.set_page_config(page_title="Arkeos Technical Support", layout="wide")

st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border: 1px solid #edf2f7;
        text-align: center;
    }
    .stAlert { border-radius: 12px; }
    .main-title { font-size: 34px; font-weight: bold; color: #1a365d; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    file_name = "data_dynamics_brute.csv.csv.csv"
    if not os.path.exists(file_name): return None
    try:
        df = pd.read_csv(file_name, sep=None, engine='python', encoding_errors='ignore')
        df.columns = [str(c).strip() for c in df.columns]
        
        mapping = {
            "Numéro de l'incident": "ID", "Incident Number": "ID",
            "Actifs du client": "SN", "Customer Asset": "SN",
            "Owner": "Technicien", "Propriétaire": "Technicien",
            "Créé le": "Date", "Created On": "Date",
            "Compte": "Client", "Account": "Client"
        }
        df = df.rename(columns=mapping)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['SN', 'Date']).sort_values(['SN', 'Date'])
        
        # Calcul du Repeat
        df['Date_Prev'] = df.groupby('SN')['Date'].shift(1)
        def calc_bus(row):
            if pd.isnull(row['Date_Prev']): return None
            try:
                d1, d2 = row['Date_Prev'].date(), row['Date'].date()
                return int(np.busday_count(d1, d2)) if d1 < d2 else 0
            except: return 0
        df['Is_Repeat'] = df.apply(lambda r: 1 if 0 <= (calc_bus(r) or 999) <= 22 else 0, axis=1)
        return df
    except: return None

df_raw = load_data()

if df_raw is not None:
    # --- SIDEBAR ---
    st.sidebar.title("🔍 Paramètres")
    
    years = sorted(df_raw['Date'].dt.year.unique(), reverse=True)
    sel_year = st.sidebar.multiselect("Année", years, default=[2026] if 2026 in years else [years[0]])
    
    noms_mois = {1:'January', 2:'February', 3:'March', 4:'April', 5:'May', 6:'June', 
                 7:'July', 8:'August', 9:'September', 10:'October', 11:'November', 12:'December'}
    df_raw['Mois_Nom'] = df_raw['Date'].dt.month.map(noms_mois)
    all_months = list(noms_mois.values())
    sel_months = st.sidebar.multiselect("Mois", all_months, default=["January", "February", "March"])
    
    techs = sorted(df_raw['Technicien'].astype(str).unique())
    sel_tech = st.sidebar.selectbox("Technicien", ["Tous"] + techs)

    # Filtrage
    mask = (df_raw['Date'].dt.year.isin(sel_year)) & (df_raw['Mois_Nom'].isin(sel_months))
    if sel_tech != "Tous":
        mask &= (df_raw['Technicien'] == sel_tech)
    df_f = df_raw[mask].copy()

    # --- AFFICHAGE ---
    st.markdown('<p class="main-title">📟 Arkeos Technical Support Dashboard</p>', unsafe_allow_html=True)
    
    total_int = len(df_f)
    nb_repeats = df_f['Is_Repeat'].sum()
    rdr_rate = (nb_repeats / total_int * 100) if total_int > 0 else 0

    k1, k2, k3, k4 = st.columns(4)
