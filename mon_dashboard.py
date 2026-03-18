import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import BytesIO

# Configuration de la page
st.set_page_config(layout="wide", page_title="Arkeos Support Dashboard")

@st.cache_data
def load_data():
    # Nom exact de votre fichier d'après votre capture d'écran
    file_path = "data_dynamics_brute.csv.csv.csv"
    
    if not os.path.exists(file_path):
        return "Fichier introuvable. Vérifiez le nom du CSV."
    
    try:
        # Lecture robuste
        df = pd.read_csv(file_path, sep=None, engine='python', encoding_errors='ignore')
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapping automatique des colonnes
        for col in df.columns:
            c = col.lower()
            if any(x in c for x in ['date', 'créé']): df = df.rename(columns={col: 'Date'})
            if any(x in c for x in ['actif', 'asset', 'sn', 'série']): df = df.rename(columns={col: 'SN'})
            if any(x in c for x in ['owner', 'propriétaire', 'tech', 'agent']): df = df.rename(columns={col: 'Tech'})
        
        # Nettoyage des données
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date', 'SN'])
        
        # --- SOLUTION ANTI-ERREUR DUPLICATE KEYS ---
        # On supprime les doublons exacts (même machine à la même seconde)
        df = df.drop_duplicates(subset=['Date', 'SN']).sort_values('Date')
        
        df['Tech'] = df['Tech'].fillna('Inconnu').astype(str)
        
        # Calcul du RDR (Repeat sous 22 jours ouvrés)
        df['Prev_Date'] = df.groupby('SN')['Date'].shift(1)
        
        def check_repeat(row):
            if pd.isnull(row['Prev_Date']): return 0
            try:
                # Calcul jours ouvrés
                days = int(np.busday_count(row['Prev_Date'].date(), row['Date'].date()))
                return 1 if 0 <= days <= 22 else 0
            except: return 0
            
        df['Is_Repeat'] = df.apply(check_repeat, axis=1)
        return df
    except Exception as e:
        return f"Erreur de lecture : {e}"

# --- CHARGEMENT ---
data = load_data()

if isinstance(data, str):
    st.error(data)
else:
    st.title("📟 Arkeos Technical Dashboard")
    
    # --- BARRE LATÉRALE (FILTRES) ---
    st.sidebar.header("Filtres")
    
    years = sorted(data['Date'].dt.year.unique().tolist(), reverse=True)
    sel_year = st.sidebar.multiselect("Année", years, default=years[:1])
    
    techs = sorted(data['Tech'].unique().tolist())
    sel_tech = st.sidebar.selectbox("Technicien", ["Tous"] + techs)
    
    # Application des filtres
    df_f = data[data['Date'].dt.year.isin(sel_year)].copy()
    if sel_tech != "Tous":
        df_f = df_f[df_f['Tech'] == sel_tech]
    
    # --- CALCULS KPIs ---
    total_interv = len(df_f)
    repeats = df_f['Is_Repeat'].sum()
    rdr_rate = (repeats / total_interv * 100) if total_interv > 0 else 0
    fttr_rate = 100 - rdr_rate
    
    # Affichage des métriques
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interventions", f"{total_interv:,}")
    c2.metric("Taux RDR %", f"{rdr_rate:.1f}%")
    c3.metric("Taux FTTR %", f"{fttr_rate:.1f}%")
    c4.metric("Nb Repeats", f"{int(repeats):,}")

    # --- GRAPHIQUE (AGRÉGATION MENSUELLE POUR ÉVITER LES DOUBLONS) ---
    st.subheader("📈 Évolution Mensuelle de la Qualité")
    
    # On groupe par mois pour que le graphique soit propre et sans erreur
    chart_data = df_f.groupby(df_f['Date'].dt.to_period('M'))['Is_Repeat'].mean() * 100
    chart_data.index = chart_data.index.to_timestamp()
    
    fig = px.area(chart_data, labels={'value': 'RDR %', 'Date': 'Mois'}, color_discrete_sequence=['#FF4B4B'])
    st.plotly_chart(fig, use_container_width=True)

    # --- EXPORT EXCEL ---
    st.divider()
    st.subheader("📥 Export des données")
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_f.to_excel(writer, index=False, sheet_name='Sheet1')
    
    st.download_button(
        label="Télécharger le rapport filtré en Excel",
        data=output.getvalue(),
        file_name=f"Report_Arkeos_{sel_tech}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
