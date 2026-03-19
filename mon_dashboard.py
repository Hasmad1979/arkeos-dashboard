import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import BytesIO

st.set_page_config(layout="wide", page_title="Arkeos Dash")

@st.cache_data
def load_data_v2():
    f = "data_dynamics_brute.csv"
    if not os.path.exists(f): return pd.DataFrame()
    
    df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
    
    # Mapping des colonnes
    cols = {c: c.lower() for c in df.columns}
    rename_dict = {}
    for c, l in cols.items():
        if 'date' in l or 'créé' in l: rename_dict[c] = 'Date'
        elif any(x in l for x in ['actif', 'asset', 'sn', 'série']): rename_dict[c] = 'SN'
        elif any(x in l for x in ['owner', 'propriétaire', 'tech']): rename_dict[c] = 'Tech'
        elif any(x in l for x in ['client', 'compte', 'customer']): rename_dict[c] = 'Client'
    
    df = df.rename(columns=rename_dict)
    if 'Date' not in df.columns or 'SN' not in df.columns: return pd.DataFrame()

    # Nettoyage
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
    df['Tech'] = df.get('Tech', 'Inconnu').fillna('Inconnu').astype(str)
    df['Client'] = df.get('Client', 'N/A').fillna('N/A').astype(str)

    # CALCUL RDR (Ligne simplifiée pour éviter SyntaxError)
    df['Prev'] = df.groupby('SN')['Date'].shift(1)
    df['Diff'] = (df['Date'] - df['Prev']).dt.days
    df['R'] = df['Diff'].apply(lambda x: 1 if (pd.notna(x) and 0 <= x <= 22) else 0)
    
    return df

df = load_data_v2()

if df.empty:
    st.error("Fichier CSV non trouvé ou colonnes invalides.")
else:
    st.title("📟 Arkeos Technical Dashboard")
    
    # --- FILTRES ---
    years = sorted(df['Date'].dt.year.unique().tolist(), reverse=True)
    sel_yr =
