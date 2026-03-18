import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px

# 1. Configuration de la page
st.set_page_config(layout="wide", page_title="Arkeos Dashboard")

@st.cache_data
def load_data():
    f = "data_dynamics_brute.csv.csv.csv"
    if not os.path.exists(f):
        return "Erreur : Fichier de données introuvable."
    
    try:
        # Lecture avec détection automatique du séparateur
        df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
        df.columns = [str(c).strip() for c in df.columns]
        
        # Identification automatique des colonnes clés
        for c in df.columns:
            low = c.lower()
            if any(x in low for x in ['date', 'créé']): df = df.rename(columns={c: 'Date'})
            if any(x in low for x in ['actif', 'asset', 'sn', 'série']): df = df.rename(columns={c: 'SN'})
            if any(x in low for x in ['owner', 'propriétaire', 'tech', 'agent']): df = df.rename(columns={c: 'Tech'})
        
        # Nettoyage des dates et suppression des doublons techniques
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date', 'SN'])
        
        # --- SOLUTION À L'ERREUR DUPLICATE KEYS ---
        # On garde une seule entrée si un SN a deux lignes à la même seconde
        df = df.drop_duplicates(subset=['Date', 'SN']).sort_values('Date')
        
        df['Tech'] = df['Tech'].fillna('Non assigné').astype(str)
        
        # Calcul du RDR (Repeat sous 22 jours ouvrés)
        df['Prev_Date'] = df.groupby('SN')['Date'].shift(1)
        
        def calc_rdr(row):
            if pd.isnull(row['Prev_Date']): return 0
            try:
                # Calcul des jours ouvrés entre deux interventions
                diff = int(np.busday_count(row['Prev_Date'].date(), row['Date'].date()))
                return 1 if 0 <= diff <= 22 else 0
            except: return 0
            
        df['Is_Repeat'] = df.apply(calc_rdr, axis=1)
        return df
    except Exception as e:
        return f"Erreur lors de la lecture : {e}"

# 2. Chargement
data = load_data()

if isinstance(data, str):
    st.error(data)
else:
    st.title("📟 Arkeos Technical Dashboard")
    
    # --- BARRE LATÉRALE (FILTRES) ---
    st.sidebar.header("Filtres")
    years = sorted(data['Date'].dt.year.unique().tolist(), reverse=True)
    sel_years = st.sidebar.multiselect("Années", years, default=years[:1])
    
    techs = sorted(data['Tech'].unique().tolist())
    sel_tech = st.sidebar.selectbox("Technicien", ["Tous"] + techs)
    
    # Filtrage des données
    df_f = data[data['Date'].dt.year.isin(sel_years)].copy()
    if sel_tech != "Tous":
        df_f = df_f[df
