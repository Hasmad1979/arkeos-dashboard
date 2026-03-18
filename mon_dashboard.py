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
        df = df.dropna(subset=['Date', 'SN']).drop_duplicates(subset=['Date', 'SN']).sort_values('Date')
        df['Tech'] = df['Tech'].fillna('Inconnu').astype(str)
        df['P'] = df.groupby('SN')['Date'].shift(1)
        def r_c(r):
            try:
                d = int(np.busday_count(r['P'].date(), r['Date'].date()))
                return 1 if 0 <= d <= 22 else 0
            except: return 0
        df['R'] = df.apply(r_c, axis=1)
        return df
    except Exception as e: return f"Erreur: {e}"

d = load()
if isinstance(d, str): st.error(d)
else:
    st.title("📟 Arkeos Dashboard")
    yr = sorted(d['Date'].dt.year.unique().tolist(), reverse=True)
    sy = st.sidebar.multiselect("Année", yr, default=yr[:1])
    tc = sorted(d['Tech'].unique().tolist())
    st = st.sidebar.selectbox("Tech", ["Tous"] + tc)
    df = d[d['Date'].dt.year.isin(sy)].copy()
    if st != "Tous": df = df[df['Tech'] == st]
    t, r = len(df), df['R'].sum()
    p = (r/t*100) if t > 0 else 0
    c1, c2, c3, c4 = d.columns if False else d.columns, d.columns, d.columns, d.columns # Ignorer
    k1, k2, k3, k4 = d.iloc[0,0] if False else st.columns(4)
    k1.metric("Interv", f"{t}")
    k2.metric("RDR %", f"{p:.1f}%")
    k3.metric("FTTR %", f"{(100-
