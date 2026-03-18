import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import BytesIO

st.set_page_config(layout="wide", page_title="Arkeos Dashboard")

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
        # Nettoyage des doublons pour éviter les erreurs de graphique
        df = df.dropna(subset=['D', 'S']).drop_duplicates(subset=['D', 'S']).sort_values('D')
        df['T'] = df['T'].fillna('Inconnu').astype(str)
        
        # Calcul RDR (Repeats < 22 jours)
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
    sy = st.sidebar.multiselect("Année", yr, default=yr[:1])
    tc = sorted(d['T'].unique().tolist())
    sv = st.sidebar.selectbox("Technicien", ["Tous"] + tc)
    
    df_f = d[d['D'].dt.year.isin(sy)].copy()
    if sv != "Tous": df_f = df_f[df_f['T'] == sv]
    
    # --- KPIs ---
    t, r = len(df_f), df_f['R'].sum()
    pr = (r/t*100) if t > 0 else 0
    pf = 100 - pr
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interventions", f"{t:,}")
    c2.metric("Taux RDR %", f"{pr:.1f}%")
    c3.metric("Taux FTTR %", f"{pf:.1f}%")
    c4.metric("Nb Repeats", f"{int(r):,}")

    # --- GRAPHIQUE ANTI-ERREUR (AGRÉGATION MENSUELLE) ---
    st.subheader("📈 Tendance Mensuelle")
    # On crée une moyenne mensuelle pour éviter les "duplicate keys"
    df_m = df_f.copy()
    df_m['Mois'] = df_m['D'].dt.to_period('M').dt.to_timestamp()
    chart_res = df_m.groupby('Mois')['R'].mean().reset_index()
    chart_res['RDR %'] = chart_res['R'] * 100
    
    st.plotly_chart(px.area(chart_res, x='Mois', y='RDR %'), use_container_width=True)

    # --- EXPORT EXCEL ---
    st.divider()
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
        df_f.to_excel(wr, index=False, sheet_name='Data')
    st.download_button("📥 Télécharger l'export Excel", out.getvalue(), "Rapport_Arkeos.xlsx")
