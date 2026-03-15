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
    
    # Détection intelligente des colonnes selon vos captures Excel
    def find_col(keywords):
        for col in df.columns:
            if any(k.lower() in col.lower() for k in keywords):
                return col
        return None

    mapping = {
        find_col(["ordre", "trav"]): "ID",
        find_col(["actifs", "sn"]): "SN",
        find_col(["propriétaire"]): "Technicien",
        find_col(["création"]): "Date_Debut",
        find_col(["fin"]): "Date_Fin",
        find_col(["incident", "type"]): "Panne",
        find_col(["compte", "service"]): "Compte"
    }
    
    df = df.rename(columns={k: v for k, v in mapping.items() if k is not None})
    
    # Conversion des dates
    df['Date_Debut'] = pd.to_datetime(df['Date_Debut'], errors='coerce')
    df['Date_Fin'] = pd.to_datetime(df['Date_Fin'], errors='coerce')
    df = df.dropna(subset=['Date_Debut', 'Compte'])

    # --- CALCUL REPEAT DISPATCH (20 JOURS OUVRES) ---
    # On trie par Compte et Date
    df = df.sort_values(['Compte', 'Date_Debut'])
    
    # Calcul de la différence en jours ouvrés avec le ticket précédent du même compte
    df['Date_Precedente'] = df.groupby('Compte')['Date_Debut'].shift(1)
    
    def calc_working_days(row):
        if pd.isnull(row['Date_Precedente']):
            return np.nan
        # np.busday_count calcule les jours entre deux dates en excluant les weekends
        return np.busday_count(row['Date_Precedente'].date(), row['Date_Debut'].date())

    df['Jours_Ouvres_Diff'] = df.apply(calc_working_days, axis=1)
    
    # Un "Repeat" est un ticket sur le même compte en moins de 20 jours ouvrés
    df['Is_Repeat'] = df['Jours_Ouvres_Diff'].le(20).astype(int)
    # FTTR est l'inverse d'un Repeat
    df['Is_FTTR'] = (df['Is_Repeat'] == 0).astype(int)
    
    # Colonnes pour filtres
    df['Année'] = df['Date_Debut'].dt.year.astype(str)
    df['Mois'] = df['Date_Debut'].dt.month_name()
    
    return df

df_raw = load_data()

if df_raw is not None and not df_raw.empty:
    # --- FILTRES SIDEBAR ---
    st.sidebar.header("🔍 Filtres")
    selected_year = st.sidebar.multiselect("Année", options=sorted(df_raw['Année'].unique()), default=sorted(df_raw['Année'].unique()))
    selected_month = st.sidebar.multiselect("Mois", options=df_raw['Mois'].unique(), default=df_raw['Mois'].unique())
    
    tech_list = ["Tous"] + sorted(df_raw['Technicien'].dropna().unique().tolist())
    selected_tech = st.sidebar.selectbox("Technicien", options=tech_list)

    # Application des filtres
    mask = df_raw['Année'].isin(selected_year) & df_raw['Mois'].isin(selected_month)
    if selected_tech != "Tous":
        mask = mask & (df_raw['Technicien'] == selected_tech)
    
    df_f = df_raw[mask]

    # --- AFFICHAGE ---
    st.title("📊 Arkeos Support Dashboard")
    
    # Calcul des Métriques
    total = len(df_f)
    repeats = df_f['Is_Repeat'].sum()
    repeat_rate = (repeats / total * 100) if total > 0 else 0
    fttr_rate = 100 - repeat_rate if total > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interventions", f"{total:,}")
    c2.metric("Repeat Dispatch Rate", f"{repeat_rate:.1f}%")
    c3.metric("FTTR %", f"{fttr_rate:.1f}%")
    c4.metric("Délai Moyen", f"{(df_f['Is_Repeat'].count()):.0f} tickets")

    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🛠️ Top 10 Comptes (Repeats)")
        top_c = df_f[df_f['Is_Repeat']==1].groupby('Compte').size().nlargest(10).reset_index(name='Nb')
        st.plotly_chart(px.bar(top_c, x='Nb', y='Compte', orientation='h', color_discrete_sequence=['#E74C3C']), use_container_width=True)

    with col2:
        st.subheader("👨‍🔧 FTTR par Technicien (Top 10)")
        perf = df_f.groupby('Technicien')['Is_FTTR'].mean().nlargest(10) * 100
        perf = perf.reset_index(name='FTTR %')
        st.plotly_chart(px.bar(perf, x='FTTR %', y='Technicien', orientation='h', color_discrete_sequence=['#2ECC71']), use_container_width=True)

    # Bouton Export
    buffer = io.BytesIO()
    df_f.to_excel(buffer, index=False)
    st.sidebar.download_button("📥 Télécharger la sélection", buffer.getvalue(), "reporting_arkeos.xlsx")

else:
    st.error("Données introuvables. Vérifiez le fichier 'data_dynamics_brute.csv.csv'.")
