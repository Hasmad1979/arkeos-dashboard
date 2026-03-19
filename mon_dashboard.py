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

# --- STYLE CSS PERSONNALISÉ (Look Professionnel) ---
st.markdown("""
    <style>
        .main { background-color: #f4f7f9; }
        [data-testid="stMetricValue"] { font-size: 24px; font-weight: bold; }
        .stMetric {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            border: 1px solid #eef2f6;
        }
        .plot-container {
            border-radius: 10px;
            background-color: white;
            padding: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        }
    </style>
""", unsafe_allow_html=True)

# --- CHARGEMENT ET TRAITEMENT DES DONNÉES ---
@st.cache_data
def load_and_clean_data():
    file_path = "data_dynamics_brute.csv.csv.csv"
    try:
        df = pd.read_csv(file_path, sep=None, engine='python', encoding_errors='ignore')
    except Exception:
        return pd.DataFrame()

    # Mapping intelligent des colonnes
    col_map = {
        'date': 'Date', 'créé': 'Date',
        'actif': 'SN', 'asset': 'SN', 'série': 'SN', 'sn': 'SN',
        'owner': 'Tech', 'propriétaire': 'Tech', 'tech': 'Tech',
        'client': 'Client', 'compte': 'Client', 'customer': 'Client'
    }
    
    rename_dict = {}
    for c in df.columns:
        low_c = str(c).lower()
        for key, val in col_map.items():
            if key in low_c:
                rename_dict[c] = val
                break
    
    df = df.rename(columns=rename_dict)
    
    # Validation des colonnes critiques
    required = ['Date', 'SN']
    if not all(col in df.columns for col in required):
        return pd.DataFrame()

    # Nettoyage
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
    df['Tech'] = df.get('Tech', 'Inconnu').fillna('Inconnu').astype(str)
    df['Client'] = df.get('Client', 'N/A').fillna('N/A').astype(str)
    
    # Calcul des Repeats (Logique métier : < 22 jours sur le même SN)
    df = df.drop_duplicates(subset=['SN', 'Date'])
    df['Prev_Date'] = df.groupby('SN')['Date'].shift(1)
    df['R'] = (df['Date'] - df['Prev_Date']).dt.days.apply(lambda x: 1 if 0 <= x <= 22 else 0)
    
    return df

df_raw = load_and_clean_data()

# --- INTERFACE PRINCIPALE ---
if df_raw.empty:
    st.error("⚠️ Erreur : Impossible de charger les données ou colonnes manquantes (Date/SN).")
else:
    # --- SIDEBAR (Filtres) ---
    st.sidebar.header("🎛️ Filtres")
    
    years = sorted(df_raw['Date'].dt.year.unique().tolist(), reverse=True)
    sel_yr = st.sidebar.multiselect("Années", years, default=years[:1])
    
    months = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", 
              "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    sel_mo = st.sidebar.multiselect("Mois", months, default=months)
    mo_idx = [months.index(m) + 1 for m in sel_mo]
    
    tech_list = ["Tous"] + sorted(df_raw['Tech'].unique().tolist())
    sel_tk = st.sidebar.selectbox("Technicien", tech_list)

    # Filtrage
    mask = (df_raw['Date'].dt.year.isin(sel_yr)) & (df_raw['Date'].dt.month.isin(mo_idx))
    if sel_tk != "Tous":
        mask &= (df_raw['Tech'] == sel_tk)
    
    df_filtered = df_raw[mask].copy()

    # --- HEADER ---
    st.title("📟 Arkeos Technical Dashboard")
    st.markdown(f"**Période :** {', '.join(map(str, sel_yr))} | **Filtre Tech :** {sel_tk}")

    # --- MÉTRIQUES (KPIs) ---
    total_interv = len(df_filtered)
    total_repeats = df_filtered['R'].sum()
    rdr = (total_repeats / total_interv * 100) if total_interv >
