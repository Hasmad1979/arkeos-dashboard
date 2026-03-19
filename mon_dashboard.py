import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import BytesIO

st.set_page_config(layout="wide", page_title="Arkeos Dash")

@st.cache_data
def load_data_v2():
    f = "data_dynamics_brute.csv.csv.csv"
    if not os.path.exists(f): return pd.DataFrame()
    
    df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
    
    col_date, col_sn, col_tech = None, None, None
    for c in df.columns:
        l = str(c).lower()
        if not col_date and any(x in l for x in ['date', 'créé']): col_date = c
        elif not col_sn and any(x in l for x in ['actif', 'asset', 'sn', 'série']): col_sn = c
        elif not col_tech and any(x in l for x in ['owner', 'propriétaire', 'tech']): col_tech = c

    rename_dict = {}
    if col_date: rename_dict[col_date] = 'Date'
    if col_sn: rename_dict[col_sn] = 'SN'
    if col_tech: rename_dict[col_tech] = 'Tech'
    
    df = df.rename(columns=rename_dict)
    cols_to_keep = [c for c in ['Date', 'SN', 'Tech'] if c in df.columns]
    df = df[cols_to_keep].copy()
    
    if 'Date' not in df.columns or 'SN' not in df.columns:
        return pd.DataFrame()
        
    df['Tech'] = df.get('Tech', pd.Series(['Inconnu']*len(df))).fillna('Inconnu').astype(str)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date', 'SN'])
    
    df = df.sort_values('Date').drop_duplicates(subset=['SN', 'Date']).reset_index(drop=True)
    
    df['Prev'] = df.groupby('SN')['Date'].shift(1)
    df['R'] = (df['Date'] - df['Prev']).dt.days.apply(lambda x: 1 if pd.notna(x) and 0 <= x <= 22 else 0)
    
    return df

# --- INTERFACE ---
df = load_data_v2()

if df.empty:
    st.error("Impossible de trouver les données. Vérifie le fichier CSV.")
else:
    st.title("📟 Arkeos Technical Dashboard")
    
    # --- FILTRES SIDEBAR ---
    st.sidebar.header("Filtres")
    
    # 1. Filtre Années
    years = sorted(df['Date'].dt.year.unique().tolist(), reverse=True)
    sel_yr = st.sidebar.multiselect("Années", years, default=years[:1])
    
    # 2. Filtre Mois (Dynamique selon l'année)
    # On crée un dictionnaire pour mapper le nom du mois à son numéro
    months_choices = {
        1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril", 
        5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août", 
        9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
    }
    sel_mo_names = st.sidebar.multiselect("Mois",
