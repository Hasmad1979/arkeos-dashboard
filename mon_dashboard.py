import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import BytesIO

st.set_page_config(layout="wide", page_title="Arkeos Dash")

@st.cache_data
def load_data():
    f = "data_dynamics_brute.csv"
    if not os.path.exists(f): return pd.DataFrame()
    df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
    # Mapping automatique simplifié
    ren = {}
    for c in df.columns:
        l = str(c).lower()
        if 'date' in l or 'créé' in l: ren[c] = 'Date'
        elif any(x in l for x in ['actif','asset','sn','série']): ren[c] = 'SN'
        elif any(x in l for x in ['owner','tech']): ren[c] = 'Tech'
        elif any(x in l for x in ['client','compte']): ren[c] = 'Client'
    df = df.rename(columns=ren)
    if 'Date' not in df.columns or 'SN' not in df.columns: return pd.DataFrame()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
    df['Tech'] = df.get('Tech', 'Inconnu').fillna('Inconnu').astype(str)
    df['Client'] = df.get('Client', 'N/A').fillna('N/A').astype(str)
    # Calcul RDR
    df['Prev'] = df.groupby('SN')['Date'].shift(1)
    df['R'] = (df['Date'] - df['Prev']).dt.days.apply(lambda x: 1 if (0 <= x <= 22) else 0)
    return df

df = load_data()

if df.empty:
    st.error("Fichier CSV introuvable ou colonnes 'Date'/'SN' absentes.")
else:
    st.title("📟 Arkeos Technical Dashboard")
    # --- FILTRES (LIGNES UNIQUES) ---
    years = sorted(df['Date'].dt.year.unique().tolist(), reverse=True)
    sel_yr = st.sidebar.multiselect("Années", years, default=years[:1])
    noms_mois = ["Janvier","Février","Mars","Avril","Mai","Juin","Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
    sel_mo_names = st.sidebar.multiselect("Mois", noms_mois, default=noms_mois)
    m_map = {n: i+1 for i, n in enumerate(noms_mois)}
    sel_mo_nums = [m_map[m] for m in sel_mo_names]
    t_list = sorted(df['Tech'].unique().tolist())
    sel_tk = st.sidebar.selectbox("Technicien", ["Tous"] + t_list)
    # --- FILTRAGE ---
    mask = (df['Date'].dt.year.isin(sel_yr)) & (df['Date'].dt.month.isin(sel_mo_nums))
    if sel_tk != "Tous": mask = mask & (df['Tech'] == sel_tk)
    f_df = df[mask].copy()
    # --- KPI ---
    tot = len(f_df)
    rep = int(f_df['R'].sum())
    rdr = (rep / tot * 100) if tot > 0 else 0
    fttr = 100 - rdr
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interv. Totales", f"{tot}")
    c2.markdown(f"**RDR %** <h2 style='color:{'#ef4444' if rdr > 20 else '#31333F'};'>{rdr:.1f}%</h2>", unsafe_allow_html=True)
    c3.markdown(f"**FTTR %** <h2 style='color:{'#22c55e' if fttr > 80 else '#31333F'};'>{fttr:.1f}%</h2>", unsafe_allow_html=True)
    c4.metric("Nb de Repeats", f"{rep}")
    # --- GRAPHIQUE TENDANCE ---
    st.subheader("📈 Tendance Mensuelle du RDR %")
    if not f_df.empty:
        f_df['Mois
