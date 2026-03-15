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
    
    # Lecture du fichier
    df = pd.read_csv(file_name)
    
    # Détection intelligente des colonnes (évite les KeyError)
    def find_col(keywords):
        for col in df.columns:
            if any(k.lower() in col.lower() for k in keywords):
                return col
        return None

    # Mapping basé sur vos fichiers Excel
    mapping = {
        find_col(["ordre", "trav"]): "ID",
        find_col(["propriétaire", "owner"]): "Technicien",
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

    # --- CALCUL REPEAT DISPATCH (20 JOURS OUVRES HORS WEEKEND) ---
    df = df.sort_values(['Compte', 'Date_Debut'])
    df['Date_Precedente'] = df.groupby('Compte')['Date_Debut'].shift(1)
    
    def calc_working_days(row):
        if pd.isnull(row['Date_Precedente']):
            return np.nan
        try:
            # Calcule les jours ouvrés entre deux tickets
            return np.busday_count(row['Date_Precedente'].date(), row['Date_Debut'].date())
        except:
            return np.nan

    df['Jours_Ouvres_Diff'] = df.apply(calc_working_days, axis=1)
    
    # Un Repeat = même compte en <= 20 jours ouvrés
    df['Is_Repeat'] = df['Jours_Ouvres_Diff'].le(20).astype(int)
    
    # Données temporelles
    df['Année'] = df['Date_Debut'].dt.year.astype(str)
    df['Mois'] = df['Date_Debut'].dt.month_name()
    
    return df

df_raw = load_data()

if df_raw is not None and not df_raw.empty:
    # --- BARRE LATÉRALE : FILTRES ---
    st.sidebar.header("🔍 Filtres")
    selected_year = st.sidebar.multiselect("Année", options=sorted(df_raw['Année'].unique()), default=sorted(df_raw['Année'].unique()))
    selected_month = st.sidebar.multiselect("Mois", options=df_raw['Mois'].unique(), default=df_raw['Mois'].unique())
    
    tech_list = ["Tous"] + sorted(df_raw['Technicien'].dropna().unique().tolist())
    selected_tech = st.sidebar.selectbox("Technicien", options=tech_list)

    # Filtrage
    mask = df_raw['Année'].isin(selected_year) & df_raw['Mois'].isin(selected_month)
    if selected_tech != "Tous":
        mask = mask & (df_raw['Technicien'] == selected_tech)
    
    df_f = df_raw[mask]

    # --- DASHBOARD ---
    st.title("📊 Arkeos Support Dashboard")
    
    total = len(df_f)
    repeats = df_f['Is_Repeat'].sum()
    rdr_rate = (repeats / total * 100) if total > 0 else 0
    fttr_rate = 100 - rdr_rate if total > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interventions", f"{total:,}")
    c2.metric("Repeat Dispatch Rate", f"{rdr_rate:.1f}%")
    c3.metric("FTTR %", f"{fttr_rate:.1f}%")
    c4.metric("Volume Repeats", f"{repeats:,}")

    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🛠️ Top 10 Comptes (Repeats)")
        top_c = df_f[df_f['Is_Repeat']==1].groupby('Compte').size().nlargest(10).reset_index(name='Nb')
        st.plotly_chart(px.bar(top_c, x='Nb', y='Compte', orientation='h', color_discrete_sequence=['#E74C3C']), use_container_width=True)

    with col2:
        # --- NOUVEAU GRAPHIQUE RDR PAR TECHNICIEN ---
        st.subheader("👨‍🔧 Taux de Repeat par Technicien")
        # On calcule le taux de repeat par technicien (Moyenne de Is_Repeat)
        tech_rdr = df_f.groupby('Technicien')['Is_Repeat'].mean().reset_index()
        tech_rdr['RDR %'] = tech_rdr['Is_Repeat'] * 100
        # On affiche les 10 techniciens ayant le RDR le plus élevé
        top_rdr_tech = tech_rdr.nlargest(10, 'RDR %')
        st.plotly_chart(px.bar(top_rdr_tech, x='RDR %', y='Technicien', orientation='h', 
                               color_discrete_sequence=['#FFA500'], 
                               labels={'RDR %': 'Taux de Repeat (%)'}), use_container_width=True)

    # Export
    buffer = io.BytesIO()
    df_f.to_excel(buffer, index=False)
    st.sidebar.download_button("📥 Télécharger les données filtrées", buffer.getvalue(), "reporting_arkeos.xlsx")

else:
    st.error("Données introuvables. Vérifiez le format de votre fichier CSV.")
