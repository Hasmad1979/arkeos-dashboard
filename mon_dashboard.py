import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import plotly.express as px

# 1. CONFIGURATION
st.set_page_config(page_title="Arkeos Support Dashboard", layout="wide")

@st.cache_data
def load_data():
    file_name = "data_dynamics_brute.csv.csv" 
    if not os.path.exists(file_name):
        return None
    
    df = pd.read_csv(file_name)

    # Mapping basé sur vos colonnes réelles
    mapping = {
        "Numéro d'ordre de travail": "ID",
        "Propriétaire": "Technicien",
        "Type d'incident principal": "Panne",
        "Compte de service": "Compte",
        "Actif client principal de l'incident": "Actif_SN", # La colonne clé
        "Date de création": "Date_Debut",
        "Date de fin": "Date_Fin"
    }
    
    df = df.rename(columns=mapping)
    
    # Conversion et nettoyage
    df['Date_Debut'] = pd.to_datetime(df['Date_Debut'], errors='coerce')
    
    # Nettoyage des techniciens (on garde les noms, on vire les codes CC-WO)
    if 'Technicien' in df.columns:
        df = df[df['Technicien'].str.contains(' ', na=False)]
        df = df[~df['Technicien'].str.contains('CC-WO|WO-', na=False, case=False)]
    
    df = df.dropna(subset=['Date_Debut', 'Actif_SN'])

    # --- CALCUL REPEAT (7 JOURS OUVRES PAR ACTIF/SN) ---
    # On trie par machine (Actif_SN) pour suivre son historique propre
    df = df.sort_values(['Actif_SN', 'Date_Debut'])
    df['Date_Precedente'] = df.groupby('Actif_SN')['Date_Debut'].shift(1)
    
    def calc_working_days(row):
        if pd.isnull(row['Date_Precedente']): return np.nan
        try:
            return np.busday_count(row['Date_Precedente'].date(), row['Date_Debut'].date())
        except: return np.nan

    df['Jours_Ouvres_Diff'] = df.apply(calc_working_days, axis=1)
    
    # Marquage du Repeat si <= 7 jours ouvrés sur la MÊME machine
    df['Is_Repeat'] = df['Jours_Ouvres_Diff'].le(7).astype(int)
    
    # Temps
    df['Periode'] = df['Date_Debut'].dt.to_period('M').astype(str)
    df['Année'] = df['Date_Debut'].dt.year.astype(str)
    df['Mois_Nom'] = df['Date_Debut'].dt.strftime('%B')
    df['Mois_Num'] = df['Date_Debut'].dt.month
    
    return df

df_raw = load_data()

if df_raw is not None and not df_raw.empty:
    # --- FILTRES ---
    st.sidebar.header("🔍 Filtres")
    years = sorted(df_raw['Année'].unique(), reverse=True)
    selected_year = st.sidebar.multiselect("Année", options=years, default=years)
    
    mois_dispo = df_raw[df_raw['Année'].isin(selected_year)].sort_values('Mois_Num')['Mois_Nom'].unique()
    selected_month = st.sidebar.multiselect("Mois", options=list(mois_dispo), default=list(mois_dispo))
    
    tech_list = ["Tous"] + sorted(df_raw['Technicien'].unique().tolist())
    selected_tech = st.sidebar.selectbox("Technicien", options=tech_list)

    mask = (df_raw['Année'].isin(selected_year)) & (df_raw['Mois_Nom'].isin(selected_month))
    if selected_tech != "Tous":
        mask = mask & (df_raw['Technicien'] == selected_tech)
    
    df_f = df_raw[mask]

    # --- AFFICHAGE ---
    st.title("📊 Arkeos Support Dashboard")
    st.subheader("Analyse par Actif Client (SN)")
    
    total = len(df_f)
    repeats = df_f['Is_Repeat'].sum()
    rdr_rate = (repeats / total * 100) if total > 0 else 0
    fttr_rate = 100 - rdr_rate if total > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interventions", f"{total:,}")
    c2.metric("RDR % (7j/Actif)", f"{rdr_rate:.1f}%")
    c3.metric("FTTR %", f"{fttr_rate:.1f}%")
    c4.metric("Nb Repeats", f"{repeats:,}")

    st.markdown("---")

    # Nouveau graphique : Top Actifs à problèmes
    st.subheader("📠 Top 10 Actifs (Machines avec le plus de Repeats)")
    top_actifs = df_f[df_f['Is_Repeat']==1].groupby('Actif_SN').size().nlargest(10).reset_index(name='Nb')
    st.plotly_chart(px.bar(top_actifs, x='Nb', y='Actif_SN', orientation='h', color_discrete_sequence=['#E74C3C']), use_container_width=True)

    # Export
    buffer = io.BytesIO()
    df_f.to_excel(buffer, index=False)
    st.sidebar.download_button("📥 Export Excel", buffer.getvalue(), "reporting_par_actif.xlsx")

else:
    st.error("Erreur de chargement des données.")
