import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import BytesIO

st.set_page_config(layout="wide", page_title="Arkeos")

@st.cache_data
def load():
    f = "data_dynamics_brute.csv.csv.csv"
    if not os.path.exists(f): return "Fichier introuvable"
    try:
        # Lecture sans aucune contrainte
        df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapping simple
        for c in df.columns:
            l = c.lower()
            if any(x in l for x in ['date', 'créé']): df=df.rename(columns={c:'D'})
            if any(x in l for x in ['actif', 'asset', 'sn']): df=df.rename(columns={c:'S'})
            if any(x in l for x in ['owner', 'propriétaire', 'tech']): df=df.rename(columns={c:'T'})
        
        # NETTOYAGE RADICAL POUR L'ERREUR 'DUPLICATE KEYS'
        # 1. On supprime les lignes totalement identiques
        df = df.drop_duplicates().reset_index(drop=True)
        
        # 2. Conversion Date
        df['D'] = pd.to_datetime(df['D'], errors='coerce')
        df = df.dropna(subset=['D', 'S'])
        
        # 3. On force l'unicité par SN et Date (on ne garde qu'une intervention par seconde)
        df = df.sort_values('D').drop_duplicates(subset=['S', 'D'], keep='first').reset_index(drop=True)
        
        df['T'] = df['T'].fillna('Inconnu').astype(str)
        
        # Calcul RDR
        df['P'] = df.groupby('S')['D'].shift(1)
        df['R'] = (df['D'] - df['P']).dt.days.apply(lambda x: 1 if (0 <= x <= 22) else 0)
        
        return df
    except Exception as e: return f"Erreur: {e}"

d = load()

if isinstance(d, str):
    st.error(d)
else:
    st.title("📟 Arkeos Technical Dashboard")
    
    # Filtres SideBar
    yr = sorted(d['D'].dt.year.unique().tolist(), reverse=True)
    sy = st.sidebar.multiselect("Années", yr, default=yr[:1])
    tc = sorted(d['T'].unique().tolist())
    st_v = st.sidebar.selectbox("Technicien", ["Tous"] + tc)
    
    # Filtrage
    df_f = d[d['D'].dt.year.isin(sy)].copy()
    if st_v != "Tous":
        df_f = df_f[df_f['T'] == st_v]
    
    # Métriques
    t, r = len(df_f), df_f['R'].sum()
    pr = (r/t*100) if t > 0 else 0
    pf = 100 - pr
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interv.", f"{t:,}")
    c2.metric("RDR %", f"{pr:.1f}%")
    c3.metric("FTTR %", f"{pf:.1f}%")
    c4.metric("Repeats", f"{int(r):,}")

    # Graphique en barres (beaucoup plus robuste que px.line pour les doublons)
    st.subheader("📈 Tendance Mensuelle")
    df_f['M'] = df_f['D'].dt.strftime('%Y-%m')
    res = df_f.groupby('M')['R'].mean().reset_index()
    res['RDR %'] = res['R'] * 100
    
    st.plotly_chart(px.bar(res, x='M', y='RDR %', color_discrete_sequence=['#00CC96']), use_container_width=True)

    # Bouton Excel
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
        df_f.to_excel(wr, index=False)
    st.download_button("📥 Télécharger Rapport Excel", out.getvalue(), "Export_Arkeos.xlsx")
