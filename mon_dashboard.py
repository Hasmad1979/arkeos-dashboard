import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import BytesIO

st.set_page_config(layout="wide", page_title="Arkeos Dash")

def load():
    f = "data_dynamics_brute.csv.csv.csv" #
    if not os.path.exists(f): return "Fichier introuvable"
    try:
        df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
        df.columns = [str(c).strip() for c in df.columns]
        
        # 1. Renommage simple
        for c in df.columns:
            l = c.lower()
            if any(x in l for x in ['date', 'créé']): df=df.rename(columns={c:'D'})
            if any(x in l for x in ['actif', 'asset', 'sn']): df=df.rename(columns={c:'S'})
            if any(x in l for x in ['owner', 'propriétaire', 'tech']): df=df.rename(columns={c:'T'})
        
        df['D'] = pd.to_datetime(df['D'], errors='coerce')
        df = df.dropna(subset=['D', 'S'])
        
        # --- LA SEULE CORRECTION QUI MARCHE ---
        # On regroupe par SN et Date et on prend la 1ère ligne. 
        # Cela élimine les "duplicate keys" AVANT le calcul du RDR.
        df = df.groupby(['S', 'D']).first().reset_index()
        df = df.sort_values(['S', 'D'])
        
        df['T'] = df['T'].fillna('Inconnu').astype(str)
        
        # 2. Calcul RDR (jours calendaires pour éviter les erreurs de busday)
        df['P'] = df.groupby('S')['D'].shift(1)
        df['Diff'] = (df['D'] - df['P']).dt.days
        df['R'] = df['Diff'].apply(lambda x: 1 if (0 <= x <= 22) else 0)
        
        return df
    except Exception as e: return f"Erreur: {e}"

d = load()
if isinstance(d, str):
    st.error(d)
else:
    st.title("📟 Arkeos Dashboard")
    
    # Filtres
    yr = sorted(d['D'].dt.year.unique().tolist(), reverse=True)
    sy = st.sidebar.multiselect("Années", yr, default=yr[:1])
    tc = sorted(d['T'].unique().tolist())
    st_v = st.sidebar.selectbox("Technicien", ["Tous"] + tc)
    
    df_f = d[d['D'].dt.year.isin(sy)].copy()
    if st_v != "Tous": df_f = df_f[df_f['T'] == st_v]
    
    # KPIs
    t, r = len(df_f), df_f['R'].sum()
    pr = (r/t*100) if t > 0 else 0
    pf = 100 - pr
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interv.", f"{t:,}")
    c2.metric("RDR %", f"{pr:.1f}%")
    c3.metric("FTTR %", f"{pf:.1f}%")
    c4.metric("Repeats", f"{int(r):,}")

    # Graphique Robuste
    st.subheader("📈 Tendance")
    # On agrège par jour pour être certain qu'il n'y ait pas de doublons pour Plotly
    ch_data = df_f.groupby(df_f['D'].dt.date)['R'].mean().reset_index()
    ch_data.columns = ['Date', 'Taux']
    st.plotly_chart(px.line(ch_data, x='Date', y='Taux', labels={'Taux':'RDR %'}), use_container_width=True)

    # Export Excel
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
        df_f.to_excel(wr, index=False)
    st.download_button("📥 Télécharger Excel", out.getvalue(), "Export_Arkeos.xlsx")
