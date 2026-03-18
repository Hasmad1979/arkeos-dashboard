import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import BytesIO

st.set_page_config(layout="wide", page_title="Arkeos Support")

@st.cache_data
def load():
    f = "data_dynamics_brute.csv.csv.csv"
    if not os.path.exists(f): return "Fichier introuvable"
    try:
        # Lecture avec gestion des erreurs d'encodage
        df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
        df.columns = [str(c).strip() for c in df.columns]
        
        # Identification des colonnes clés
        for c in df.columns:
            l = c.lower()
            if any(x in l for x in ['date', 'créé']): df=df.rename(columns={c:'D'})
            if any(x in l for x in ['actif', 'asset', 'sn']): df=df.rename(columns={c:'S'})
            if any(x in l for x in ['owner', 'propriétaire', 'tech']): df=df.rename(columns={c:'T'})
        
        df['D'] = pd.to_datetime(df['D'], errors='coerce')
        
        # --- SOLUTION À L'ERREUR : SUPPRESSION DES DOUBLONS DE CLÉS ---
        # On ne garde qu'une seule entrée si la date et le SN sont identiques
        df = df.dropna(subset=['D', 'S']).drop_duplicates(subset=['D', 'S']).sort_values('D')
        
        df['T'] = df['T'].fillna('Inconnu').astype(str)
        
        # Calcul RDR (Repeat)
        df['P'] = df.groupby('S')['D'].shift(1)
        def r_c(r):
            try:
                if pd.isnull(r['P']): return 0
                diff = int(np.busday_count(r['P'].date(), r['D'].date()))
                return 1 if 0 <= diff <= 22 else 0
            except: return 0
        df['R'] = df.apply(r_c, axis=1)
        return df
    except Exception as e: return f"Erreur: {e}"

d = load()
if isinstance(d, str):
    st.error(d)
else:
    st.title("📟 Arkeos Technical Dashboard")
    
    # --- FILTRES ---
    yr = sorted(d['D'].dt.year.unique().tolist(), reverse=True)
    sy = st.sidebar.multiselect("Sélection Année", yr, default=yr[:1])
    tc = sorted(d['T'].unique().tolist())
    sv = st.sidebar.selectbox("Sélection Technicien", ["Tous"] + tc)
    
    # Application filtres
    df_f = d[d['D'].dt.year.isin(sy)].copy()
    if sv != "Tous": df_f = df_f[df_f['T'] == sv]
    
    # --- KPIs ---
    t, r = len(df_f), df_f['R'].sum()
    pr = (r/t*100) if t > 0 else 0
    pf = 100 - pr
    
    c1, c2, c3,
