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
        for c in df.columns:
            l = c.lower()
            if any(x in l for x in ['date', 'créé']): df=df.rename(columns={c:'D'})
            if any(x in l for x in ['actif', 'asset', 'sn']): df=df.rename(columns={c:'S'})
            if any(x in l for x in ['owner', 'propriétaire', 'tech']): df=df.rename(columns={c:'T'})
        
        df['D'] = pd.to_datetime(df['D'], errors='coerce')
        # Nettoyage strict : on supprime les lignes vides et les doublons exacts
        df = df.dropna(subset=['D', 'S']).drop_duplicates(subset=['D', 'S']).sort_values('D')
        df['T'] = df['T'].fillna('Inconnu').astype(str)
        
        # Calcul Repeat (R)
        df['P'] = df.groupby('S')['D'].shift(1)
        def r_c(r):
            try:
                if pd.isnull(r['P']): return 0
                d = int(np.busday_count(r['P'].date(), r['D'].date()))
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
    
    # Filtres
    yr = sorted(d['D'].dt.year.unique().tolist(), reverse=True)
    sy = st.sidebar.multiselect("Année", yr, default=yr[:1])
    tc = sorted(d['T'].unique().tolist())
    sv = st.sidebar.selectbox("Technicien", ["Tous"] + tc)
    
    df = d[d['D'].dt.year.isin(sy)].copy()
    if sv != "Tous": df = df[df['T'] == sv]
    
    # KPIs
    t, r = len(df), df['R'].sum()
    pr = (r/t*100) if t > 0 else 0
    pf = 100 - pr
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interv.", f"{t:,}")
    c2.metric("RDR %", f"{pr:.1f}%")
    c3.metric("FTTR %", f"{pf:.1f}%")
    col4_val = int(r)
    c4.metric("Repeats", f"{col4_val:,}")

    # GRAPHIQUE ANTI-ERREUR (Agrégation par jour)
    st.subheader("📈 Tendance de la Qualité")
    # Cette ligne regroupe les données par jour pour éliminer les doublons de clés
    df_day = df.groupby(df['D'].dt.date)['R'].mean().reset_index()
    df_day['R'] = df_day['R'] * 100
    
    fig = px.line(df_day, x='D', y='R', labels={'R':'RDR %', 'D':'Date'})
    st.plotly_chart(fig, use_container_width=True)
