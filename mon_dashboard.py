import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import BytesIO

st.set_page_config(layout="wide", page_title="Arkeos")

# 1. Chargement sans aucune indexation complexe
@st.cache_data
def load():
    f = "data_dynamics_brute.csv.csv.csv" # Nom du fichier
    if not os.path.exists(f): return "Fichier introuvable"
    try:
        df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
        # Nettoyage immédiat des noms de colonnes
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapping simple
        for c in df.columns:
            l = c.lower()
            if any(x in l for x in ['date', 'créé']): df=df.rename(columns={c:'D'})
            if any(x in l for x in ['actif', 'asset', 'sn']): df=df.rename(columns={c:'S'})
            if any(x in l for x in ['owner', 'propriétaire', 'tech']): df=df.rename(columns={c:'T'})
        
        df['D'] = pd.to_datetime(df['D'], errors='coerce')
        df = df.dropna(subset=['D', 'S'])
        
        # --- LA SOLUTION : ON COUPE TOUT LIEN ENTRE LES LIGNES ---
        df = df.sort_values('D').reset_index(drop=True)
        df['T'] = df['T'].fillna('Inconnu').astype(str)
        
        # Calcul RDR ligne par ligne (pas de pivot, pas d'index)
        df['P'] = df.groupby('S')['D'].shift(1)
        def r_c(r):
            if pd.isnull(r['P']): return 0
            try:
                # Différence simple en jours pour éviter np.busday_count si erreur
                diff = (r['D'] - r['P']).days
                return 1 if 0 <= diff <= 22 else 0
            except: return 0
        df['R'] = df.apply(r_c, axis=1)
        return df
    except Exception as e: return f"Erreur: {e}"

d = load()

if isinstance(d, str):
    st.error(d)
else:
    st.title("📟 Arkeos Dashboard")
    
    # Filtres Sidebar
    yr = sorted(d['D'].dt.year.unique().tolist(), reverse=True)
    sy = st.sidebar.multiselect("Années", yr, default=yr[:1])
    tc = sorted(d['T'].unique().tolist())
    st_v = st.sidebar.selectbox("Technicien", ["Tous"] + tc)
    
    # Filtrage manuel (copie propre)
    df_f = d[d['D'].dt.year.isin(sy)].copy()
    if st_v != "Tous":
        df_f = df_f[df_f['T'] == st_v]
    
    # Affichage des KPIs
    t, r = len(df_f), df_f['R'].sum()
    pr = (r/t*100) if t > 0 else 0
    pf = 100 - pr
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interv.", f"{t:,}")
    c2.metric("RDR %", f"{pr:.1f}%")
    c3.metric("FTTR %", f"{pf:.1f}%")
    c4.metric("Repeats", f"{int(r):,}")

    # Graphique en barres (plus robuste que les lignes face aux doublons)
    st.subheader("📈 Tendance Mensuelle")
    df_f['Mois'] = df_f['D'].dt.strftime('%Y-%m')
    chart_res = df_f.groupby('Mois')['R'].mean().reset_index()
    chart_res['RDR %'] = chart_res['R'] * 100
    
    fig = px.bar(chart_res, x='Mois', y='RDR %')
    st.plotly_chart(fig, use_container_width=True)

    # Export Excel simple
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
        df_f.to_excel(wr, index=False)
    st.sidebar.download_button("📥 Télécharger Excel", out.getvalue(), "Export_Arkeos.xlsx")
