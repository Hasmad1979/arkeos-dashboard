import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import BytesIO

st.set_page_config(layout="wide", page_title="Arkeos Dash")

@st.cache_data
def load_data():
    f = "data_dynamics_brute.csv.csv.csv"
    if not os.path.exists(f): return "Fichier introuvable"
    try:
        # 1. Chargement sans aucune fioriture
        df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
        df.columns = [str(c).strip() for c in df.columns]
        
        # 2. Mapping ultra-simplifié
        for c in df.columns:
            l = c.lower()
            if any(x in l for x in ['date', 'créé']): df=df.rename(columns={c:'Date'})
            if any(x in l for x in ['actif', 'asset', 'sn']): df=df.rename(columns={c:'SN'})
            if any(x in l for x in ['owner', 'propriétaire', 'tech']): df=df.rename(columns={c:'Tech'})
        
        # 3. SUPPRESSION RADICALE DES DOUBLONS
        # On ne garde qu'une seule ligne si SN et Date sont identiques
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date', 'SN'])
        df = df.drop_duplicates(subset=['SN', 'Date']).sort_values('Date').reset_index(drop=True)
        
        # 4. Calcul RDR sans utiliser de fonctions complexes
        df['Tech'] = df['Tech'].fillna('Inconnu').astype(str)
        df['Prev'] = df.groupby('SN')['Date'].shift(1)
        
        # Calcul simple de la différence en jours
        df['Days'] = (df['Date'] - df['Prev']).dt.days
        df['R'] = df['Days'].apply(lambda x: 1 if (0 <= x <= 22) else 0)
        
        return df
    except Exception as e:
        return f"Erreur système : {e}"

df = load_data()

if isinstance(df, str):
    st.error(df)
else:
    st.title("📟 Arkeos Technical Dashboard")
    
    # --- FILTRES ---
    years = sorted(df['Date'].dt.year.unique().tolist(), reverse=True)
    sel_yr = st.sidebar.multiselect("Années", years, default=years[:1])
    techs = sorted(df['Tech'].unique().tolist())
    sel_tk = st.sidebar.selectbox("Technicien", ["Tous"] + techs)
    
    # Filtrage manuel pour éviter les erreurs d'assemblage
    mask = df['Date'].dt.year.isin(sel_yr)
    if sel_tk != "Tous":
        mask = mask & (df['Tech'] == sel_tk)
    
    final_df = df[mask].copy().reset_index(drop=True)
    
    # --- KPIs ---
    total = len(final_df)
    reps = final_df['R'].sum()
    rdr = (reps / total * 100) if total > 0 else 0
    fttr = 100 - rdr
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interv.", f"{total}")
    c2.metric("RDR %", f"{rdr:.1f}%")
    c3.metric("FTTR %", f"{fttr:.1f}%")
    c4.metric("Repeats", f"{int(reps)}")

    # --- GRAPHIQUE BARRES (Le plus robuste) ---
    st.subheader("📈 Tendance de la Qualité")
    final_df['Mois'] = final_df['Date'].dt.strftime('%Y-%m')
    # Agrégation manuelle pour éviter le crash de Plotly
    chart_data = final_df.groupby('Mois')['R'].mean().reset_index()
    chart_data['RDR %'] = chart_data['R'] * 100
    
    st.plotly_chart(px.bar(chart_data, x='Mois', y='RDR %'), use_container_width=True)

    # --- EXPORT EXCEL ---
    st.divider()
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        final_df.to_excel(writer, index=False)
    st.download_button("📥 Télécharger Rapport Excel", output.getvalue(), "Export_Arkeos.xlsx")
