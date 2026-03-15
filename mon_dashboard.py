import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import plotly.express as px

# Configuration
st.set_page_config(page_title="Arkeos Support Dashboard", layout="wide")

@st.cache_data
def load_data():
    # Nom du fichier basé sur votre structure GitHub
    file_name = "data_dynamics_brute.csv.csv" 
    if not os.path.exists(file_name):
        return None
    
    df = pd.read_csv(file_name)
    
    # Détection des colonnes basée sur vos captures d'écran
    def find_col(keywords):
        for col in df.columns:
            if any(k.lower() in col.lower() for k in keywords):
                return col
        return None

    mapping = {
        find_col(["ordre", "trav"]): "ID",
        find_col(["actifs", "client", "sn", "produit"]): "SN",
        find_col(["propriétaire", "owner"]): "Technicien",
        find_col(["création"]): "Date_Debut",
        find_col(["fin"]): "Date_Fin",
        find_col(["incident", "type"]): "Panne",
        find_col(["compte", "service"]): "Compte"
    }
    
    df = df.rename(columns={k: v for k, v in mapping.items() if k is not None})
    
    # Sécurité pour le calcul des repeats
    if "SN" not in df.columns:
        df["SN"] = df["ID"] if "ID" in df.columns else "Inconnu"

    # Conversion des dates
    df['Date_Debut'] = pd.to_datetime(df['Date_Debut'], errors='coerce')
    df['Date_Fin'] = pd.to_datetime(df['Date_Fin'], errors='coerce')
    df = df.dropna(subset=['Date_Debut'])

    # Colonnes temporelles pour les filtres
    df['Année'] = df['Date_Debut'].dt.year.astype(str)
    df['Mois'] = df['Date_Debut'].dt.month_name()
    
    # --- CALCUL REPEAT & FTTR ---
    # Tri par équipement et date pour détecter les successions
    df = df.sort_values(['SN', 'Date_Debut'])
    # Repeat Dispatch : même SN dans un délai de 22 jours
    df['Is_Repeat'] = df.groupby('SN')['Date_Debut'].diff().dt.days.le(22).astype(int)
    # FTTR : Si ce n'est pas un repeat, c'est un First Time Fix
    df['Is_FTFT'] = (df['Is_Repeat'] == 0).astype(int)
    
    # Calcul durée
    df['Duree_Mins'] = (df['Date_Fin'] - df['Date_Debut']).dt.total_seconds() / 60
    df['Duree_Mins'] = df['Duree_Mins'].fillna(0).apply(lambda x: max(0, x))
    
    return df

df_raw = load_data()

if df_raw is not None and not df_raw.empty:
    # --- FILTRES ---
    st.sidebar.header("🔍 Filtres")
    selected_year = st.sidebar.multiselect("Année", options=sorted(df_raw['Année'].unique()), default=sorted(df_raw['Année'].unique()))
    selected_month = st.sidebar.multiselect("Mois", options=df_raw['Mois'].unique(), default=df_raw['Mois'].unique())
    
    tech_options = ["Tous"] + sorted(df_raw['Technicien'].dropna().unique().tolist())
    selected_tech = st.sidebar.selectbox("Technicien", options=tech_options)

    mask = df_raw['Année'].isin(selected_year) & df_raw['Mois'].isin(selected_month)
    if selected_tech != "Tous":
        mask = mask & (df_raw['Technicien'] == selected_tech)
    
    df_filtered = df_raw[mask]

    # --- AFFICHAGE ---
    st.title("📊 Arkeos Support Dashboard")
    
    # Calcul des métriques
    total_int = len(df_filtered)
    total_rep = df_filtered['Is_Repeat'].sum()
    repeat_rate = (total_rep / total_int * 100) if total_int > 0 else 0
    fttr_rate = 100 - repeat_rate if total_int > 0 else 0
    
    # Ligne 1 des KPI
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interventions", f"{total_int:,}")
    c2.metric("Repeat Dispatch Rate", f"{repeat_rate:.1f}%")
    c3.metric("FTTR %", f"{fttr_rate:.1f}%")
    c4.metric("Délai Moyen", f"{df_filtered['Duree_Mins'].mean():.1f} min")

    st.markdown("---")
    
    # Graphiques
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🛠️ Top 10 Pannes")
        top_p = df_filtered.groupby('Panne').size().nlargest(10).reset_index(name='Nb')
        st.plotly_chart(px.bar(top_p, x='Nb', y='Panne', orientation='h', color_discrete_sequence=['#4B8BBE']), use_container_width=True)

    with col2:
        st.subheader("👨‍🔧 FTTR par Technicien (Top 10)")
        # Moyenne du FTTR par technicien pour voir les plus performants
        tech_perf = df_filtered.groupby('Technicien')['Is_FTFT'].mean().nlargest(10) * 100
        tech_perf = tech_perf.reset_index(name='FTTR %')
        st.plotly_chart(px.bar(tech_perf, x='FTTR %', y='Technicien', orientation='h', color_discrete_sequence=['#2CA02C']), use_container_width=True)

    # Export
    buffer = io.BytesIO()
    df_filtered.to_excel(buffer, index=False)
    st.sidebar.download_button("📥 Télécharger Sélection", buffer.getvalue(), "data_filtree.xlsx")

else:
    st.error("Impossible de charger les données. Vérifiez le fichier CSV.")
