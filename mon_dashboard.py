import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px

st.set_page_config(page_title="Arkeos Support", layout="wide")

@st.cache_data
def load_data():
    f = "data_dynamics_brute.csv.csv.csv"
    if not os.path.exists(f): return "Fichier CSV introuvable."
    try:
        df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapping et détection automatique intelligente
        for c in df.columns:
            cl = c.lower()
            if any(x in cl for x in ['date', 'créé', 'created']): df = df.rename(columns={c: 'Date'})
            if any(x in cl for x in ['actif', 'asset', 'sn', 'serial']): df = df.rename(columns={c: 'SN'})
            if any(x in cl for x in ['owner', 'propriétaire', 'technicien']): df = df.rename(columns={c: 'Tech'})

        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
        df['Tech'] = df['Tech'].fillna('Non spécifié').astype(str)

        # Calcul RDR (Repeats sous 22 jours ouvrés)
        df['P'] = df.groupby('SN')['Date'].shift(1)
        def calc(r):
            try:
                if pd.isnull(r['P']): return 0
                d = int(np.busday_count(r['P'].date(), r['Date'].date()))
                return 1 if 0 <= d <= 22 else 0
            except: return 0
        df['Is_R'] = df.apply(calc, axis=1)
        return df
    except Exception as e: return f"Erreur: {e}"

df = load_data()
if isinstance(df, str):
    st.error(df)
else:
    st.title("📟 Arkeos Technical Dashboard")
    
    # --- FILTRES ---
    years = sorted(df['Date'].dt.year.unique().tolist(), reverse=True)
    sel_y = st.sidebar.multiselect("Année", years, default=years[:1])
    techs = sorted(df['Tech'].unique().tolist())
    sel_t = st.sidebar.selectbox("Technicien", ["Tous"] + techs)

    df_f = df[df['Date'].dt.year.isin(sel_y)].copy()
    if sel_t != "Tous": df_f = df_f[df_f['Tech'] == sel_t]

    # --- KPIs ---
    t, r = len(df_f), df_f['Is_R'].sum()
    rate_r = (r/t*100) if t > 0 else 0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interventions", f"{t:,}")
    c2.metric("Taux RDR %", f"{rate_r:.1f}%")
    c3.metric("Taux FTTR %", f"{(100-rate_r):.1f}%")
    c4.metric("Nb
