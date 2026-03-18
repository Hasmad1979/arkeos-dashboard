import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px

st.set_page_config(layout="wide")

@st.cache_data
def load():
    f = "data_dynamics_brute.csv.csv.csv"
    if not os.path.exists(f): return "Fichier introuvable"
    try:
        df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
        df.columns = [str(c).strip() for c in df.columns]
        for c in df.columns:
            l = c.lower()
            if any(x in l for x in ['date', 'créé']): df=df.rename(columns={c:'Date'})
            if any(x in l for x in ['actif', 'asset', 'sn']): df=df.rename(columns={c:'SN'})
            if any(x in l for x in ['owner', 'propriétaire', 'tech']): df=df.rename(columns={c:'Tech'})
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
        
        # --- CORRECTION DU DOUBLON ---
        # On garde une seule ligne si tout est identique (même seconde, même SN)
        df = df.drop_duplicates(subset=['Date', 'SN'])
        
        df['Tech'] = df['Tech'].fillna('Inconnu').astype(str)
        df['P'] = df.groupby('SN')['Date'].shift(1)
        def rdr_c(r):
            try:
                d = int(np.busday_count(r['P'].date(), r['Date'].date()))
                return 1 if 0 <= d <= 22 else 0
            except: return 0
        df['R'] = df.apply(rdr_c, axis=1)
        return df
    except Exception as e: return f"Erreur: {e}"

d = load()
if isinstance(d, str): st.error(d)
else:
    st.title("📟 Arkeos Dashboard")
    yr = sorted(d['Date'].dt.year.unique().tolist(), reverse=True)
    s_y = st.sidebar.multiselect("Année", yr, default=yr[:1])
    tc = sorted(d['Tech'].unique().tolist())
    s_t = st.sidebar.selectbox("Technicien", ["Tous"] + tc)
    
    df = d[d['Date'].dt.year.isin(s_y)].copy()
    if s_t != "Tous": df = df[df['Tech'] == s_t]
    
    t, r = len(df), df['R'].sum()
    pct = (r/t*100) if t > 0 else 0
    c1, c2, c3, c4 = st.
