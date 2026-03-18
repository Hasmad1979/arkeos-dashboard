import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px

st.set_page_config(layout="wide", page_title="Arkeos Support")

@st.cache_data
def load():
    f = "data_dynamics_brute.csv.csv.csv"
    if not os.path.exists(f): return "Fichier introuvable"
    try:
        df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
        df.columns = [str(c).strip() for c in df.columns]
        # Détection auto des colonnes Date, SN et Tech
        for c in df.columns:
            l = c.lower()
            if any(x in l for x in ['date', 'créé']): df=df.rename(columns={c:'Date'})
            if any(x in l for x in ['actif', 'asset', 'sn', 'machine']): df=df.rename(columns={c:'SN'})
            if any(x in l for x in ['owner', 'propriétaire', 'tech', 'agent']): df=df.rename(columns={c:'Tech'})
        
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        # On supprime les doublons de temps pour éviter l'erreur 'duplicate keys'
        df = df.dropna(subset=['Date', 'SN']).drop_duplicates(subset=['Date', 'SN']).sort_values('Date')
        df['Tech'] = df['Tech'].fillna('Inconnu').astype(str)
        
        # Calcul RDR (Repeat sous 22 jours)
        df['P'] = df.groupby('SN')['Date'].shift(1)
        def r_c(r):
            try:
                if pd.isnull(r['P']): return 0
                d = int(np.busday_count(r['P'].date(), r['Date'].date()))
                return 1 if 0 <= d <= 22 else 0
            except: return 0
        df['R'] = df.apply(r_c, axis=1)
        return df
    except Exception as e: return f"Erreur: {e}"

d = load()
if isinstance(d, str):
    st.error(d)
else:
    st.title("📟 Arkeos Technical Dashboard")
    
    # --- FILTRES (SIDEBAR) ---
    yr = sorted(d['Date'].dt.year.unique().tolist(), reverse=True)
    sy = st.sidebar.multiselect("Sélectionner l'Année", yr, default=yr[:1])
    tc = sorted(d['Tech'].unique().tolist())
    st_v = st.sidebar.selectbox("Sélectionner le Technicien", ["Tous"] + tc)
    
    df = d[d['Date'].dt.year.isin(sy)].copy()
    if st_v != "Tous": df = df[df['Tech'] == st_v]
    
    # --- CALCULS KPIs ---
    t = len(df)
    r = df['R'].sum()
    pr = (r/t*100) if t > 0 else 0
    pf = 100 - pr # Taux FTTR
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interventions", f"{t:,}")
