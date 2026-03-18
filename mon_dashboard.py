import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import BytesIO

st.set_page_config(layout="wide", page_title="Arkeos Dashboard")

@st.cache_data
def load():
    f = "data_dynamics_brute.csv.csv.csv" # Nom du fichier
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
        df = df.dropna(subset=['D', 'S'])
        
        # --- RESET INDEX : LA SOLUTION FINALE ---
        df = df.sort_values('D').reset_index(drop=True) 
        df['T'] = df['T'].fillna('Inconnu').astype(str)
        
        # Calcul RDR
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
    
    # Filtres
    yr = sorted(d['D'].dt.year.unique().tolist(), reverse=True)
    sy = st.sidebar.multiselect("Année", yr, default=yr[:1])
    tc = sorted(d['T'].unique().tolist())
    sv = st.sidebar.selectbox("Technicien", ["Tous"] + tc)
    
    df_f = d[d['D'].dt.year.isin(sy)].copy()
    if sv != "Tous": df_f = df_f[df_f['T'] == sv]
    
    # KPIs
    t, r = len(df_f), df_f['R'].sum()
    pr = (r/t*100) if t > 0 else 0
    pf = 100 - pr
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interv.", f"{t:,}")
    c2.metric("RDR %", f"{pr:.1f}%")
    c3.metric("FTTR %", f"{pf:.1f}%")
    c4.metric("Repeats", f"{int(r):,}")

    # Graphique SÉCURISÉ
    st.subheader("📈 Tendance")
    # On utilise reset_index() ici aussi pour éviter l'erreur duplicate keys au moment du plot
    chart_data = df_f.groupby(df_f['D'].dt.date)['R'].mean().reset_index()
    chart_data.columns = ['Date', 'RDR']
    chart_data['RDR'] = chart_data['RDR'] * 100
    
    fig = px.line(chart_data, x='Date', y='RDR')
    st.plotly_chart(fig, use_container_width=True)

    # Export Excel
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
        df_f.to_excel(wr, index=False)
    st.sidebar.download_button("📥 Télécharger Excel", out.getvalue(), "Export.xlsx")
