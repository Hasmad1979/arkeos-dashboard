import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import BytesIO

# Configuration de la page
st.set_page_config(layout="wide", page_title="Arkeos Dash")

@st.cache_data
def load_data_v2():
    # Correction du nom de fichier (à adapter si nécessaire)
    f = "data_dynamics_brute.csv" 
    
    if not os.path.exists(f): 
        return pd.DataFrame()
    
    # Lecture flexible (gestion auto du séparateur et des erreurs d'encodage)
    df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
    
    # --- DETECTION AUTOMATIQUE DES COLONNES ---
    col_date, col_sn, col_tech, col_client = None, None, None, None
    for c in df.columns:
        l = str(c).lower()
        if not col_date and any(x in l for x in ['date', 'créé']): col_date = c
        elif not col_sn and any(x in l for x in ['actif', 'asset', 'sn', 'série']): col_sn = c
        elif not col_tech and any(x in l for x in ['owner', 'propriétaire', 'tech']): col_tech = c
        elif not col_client and any(x in l for x in ['client', 'compte', 'customer']): col_client = c

    rename_dict = {}
    if col_date: rename_dict[col_date] = 'Date'
    if col_sn: rename_dict[col_sn] = 'SN'
    if col_tech: rename_dict[col_tech] = 'Tech'
    if col_client: rename_dict[col_client] = 'Client'
    
    df = df.rename(columns=rename_dict)
    cols_to_keep = [c for c in ['Date', 'SN', 'Tech', 'Client'] if c in df.columns]
    df = df[cols_to_keep].copy()

    if 'Date' not in df.columns or 'SN' not in df.columns: 
        return pd.DataFrame()

    # Nettoyage et typage
    df['Tech'] = df.get('Tech', pd.Series(['Inconnu']*len(df))).fillna('Inconnu').astype(str)
    df['Client'] = df.get('Client', pd.Series(['N/A']*len(df))).fillna('N/A').astype(str)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
    df = df.drop_duplicates(subset=['SN', 'Date']).reset_index(drop=True)

    # --- CALCUL DU RDR (REPEAT REPAIR) ---
    # Un repeat est défini par une intervention sur le même SN sous 22 jours
    df['Prev'] = df.groupby('SN')['Date'].shift(1)
    df['R'] = (df['Date'] - df['Prev']).dt.days.apply(lambda x: 1 if pd.notna(x) and 0 <= x <= 22 else 0)
    
    return df

# Chargement des données
df = load_data_v2()

if df.empty:
    st.error("❌ Données introuvables. Vérifiez la présence du fichier CSV ou ses colonnes (Date, SN).")
else:
    st.title("📟 Arkeos Technical Dashboard")
    
    # --- BARRE LATÉRALE (FILTRES) ---
    st.sidebar.header("Filtres")
    years = sorted(df['Date'].dt.year.unique().tolist(), reverse=True)
    sel_yr = st.sidebar.multiselect("Années", years, default=years[:1])
    
    noms_mois = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", 
                 "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    sel_mo_names = st.sidebar.multiselect("Mois", noms_mois, default=noms_mois)
    mapping_mois = {nom: i+1 for i, nom in enumerate(noms_mois)}
    sel_mo_nums = [mapping_mois[m] for m in sel_mo_names]
    
    techs = sorted(df['Tech'].unique().tolist())
    sel_tk = st.sidebar.selectbox("Technicien", ["Tous"] + techs)
    
    # Application du filtre
    mask = (df['Date'].dt.year.isin(sel_yr)) & (df['Date'].dt.month.isin(sel_mo_nums))
    if sel_tk != "Tous": 
        mask = mask & (df['Tech'] == sel_tk)
    
    final_df = df[mask].copy()
    
    # --- CALCULS DES KPI ---
    total = len(final_df)
    reps = final_df['R'].sum()
    rdr = (re
