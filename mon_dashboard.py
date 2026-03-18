import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import BytesIO

# 1. Configuration de l'interface
st.set_page_config(layout="wide", page_title="Arkeos Support Quality")

@st.cache_data
def load_and_clean_data():
    # Nom du fichier d'après votre structure
    file_path = "data_dynamics_brute.csv.csv.csv"
    
    if not os.path.exists(file_path):
        return "Fichier introuvable. Vérifiez le nom dans GitHub."
    
    try:
        # Lecture flexible (détecte point-virgule ou virgule)
        df = pd.read_csv(file_path, sep=None, engine='python', encoding_errors='ignore')
        df.columns = [str(c).strip() for c in df.columns]
        
        # Identification des colonnes clés
        for col in df.columns:
            c = col.lower()
            if any(x in c for x in ['date', 'créé']): df = df.rename(columns={col: 'Date'})
            if any(x in c for x in ['actif', 'asset', 'sn']): df = df.rename(columns={col: 'SN'})
            if any(x in c for x in ['owner', 'propriétaire', 'tech']): df = df.rename(columns={col: 'Tech'})
        
        # Conversion Date
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date', 'SN'])
        
        # --- SOLUTION ANTI-ERREUR DUPLICATE KEYS ---
        # On ne garde qu'une intervention par jour par machine pour éliminer les doublons de secondes
        df['Jour'] = df['Date'].dt.date
        df = df.sort_values('Date').drop_duplicates(subset=['SN', 'Jour'], keep='first')
        df = df.reset_index(drop=True)
        
        df['Tech'] = df['Tech'].fillna('Inconnu').astype(str)
        
        # --- CALCUL RDR (Repeat < 22 jours) ---
        df['Prev_Date'] = df.groupby('SN')['Date'].shift(1)
        
        def calculate_rdr(row):
            if pd.isnull(row['Prev_Date']): return 0
            # Différence simple en jours calendaires (plus stable)
            diff = (row['Date'] - row['Prev_Date']).days
            return 1 if 0 <= diff <= 22 else 0
            
        df['Is_Repeat'] = df.apply(calculate_rdr, axis=1)
        return df
    except Exception as e:
        return f"Erreur lors de la lecture : {e}"

# --- CHARGEMENT ---
data = load_and_clean_data()

if isinstance(data, str):
    st.error(data)
else:
    st.title("📟 Arkeos Technical Dashboard")
    
    # --- FILTRES (SIDEBAR) ---
    st.sidebar.header("Paramètres")
    
    years = sorted(data['Date'].dt.year.unique().tolist(), reverse=True)
    selected_years = st.sidebar.multiselect("Année(s)", years, default=years[:1])
    
    techs = sorted(data['Tech'].unique().tolist())
    selected_tech = st.sidebar.selectbox("Technicien", ["Tous"] + techs)
    
    # Filtrage des données
    df_filtered = data[data['Date'].dt.year.isin(selected_years)].copy()
    if selected_tech != "Tous":
        df_filtered = df_filtered[df_filtered['Tech'] == selected_tech]
    
    # --- CALCUL KPIs ---
    total_calls = len(df_filtered)
    repeats = df_filtered['Is_Repeat'].sum()
    rdr_rate = (repeats / total_calls * 100) if total_calls > 0 else 0
    fttr_rate = 100 - rdr_rate
    
    # Affichage des métriques
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interventions", f"{total_calls:,}")
    c2.metric("Taux RDR %", f"{rdr_rate:.1f}%")
    c3.metric("Taux FTTR %", f"{fttr_rate:.1f}%")
    c4.metric("Nb Repeats", f"{int(repeats):,}")

    # --- GRAPHIQUE (AGRÉGATION MENSUELLE) ---
    st.subheader("📈 Évolution de la Qualité")
    # Agrégation manuelle pour éviter tout conflit d'index Plotly
    chart_df = df_filtered.copy()
    chart_df['Mois'] = chart_df['Date'].dt.strftime('%Y-%m')
    res_chart = chart_df.groupby('Mois')['Is_Repeat'].mean().reset_index()
    res_chart['RDR %'] = res_chart['Is_Repeat'] * 100
    
    fig = px.bar(res_chart, x='Mois', y='RDR %', color_discrete_sequence=['#00CC96'])
    st.plotly_chart(fig, use_container_width=True)

    # --- EXPORT EXCEL ---
    st.divider()
    st.subheader("📥 Exporter les données")
    
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_filtered.to_excel(writer, index=False, sheet_name='Dashboard_Data')
    
    st.download_button(
        label="Télécharger le rapport Excel",
        data=buffer.getvalue(),
        file_name=f"Rapport_Arkeos_{selected_tech}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
