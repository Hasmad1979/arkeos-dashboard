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
    file_name = "data_dynamics_brute.csv.csv" 
    if not os.path.exists(file_name):
        return None
    
    df = pd.read_csv(file_name)
    
    # Détection flexible des colonnes
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
    
    # Sécurité si SN absent (utilise ID par défaut)
    if "SN" not in df.columns:
        df["SN"] = df["ID"] if "ID" in df.columns else "Inconnu"

    # Conversion et préparation des dates
    df['Date_Debut'] = pd.to_datetime(df['Date_Debut'], errors='coerce')
    df['Date_Fin'] = pd.to_datetime(df['Date_Fin'], errors='coerce')
    df = df.dropna(subset=['Date_Debut'])

    # Ajout des colonnes pour les filtres
    df['Année'] = df['Date_Debut'].dt.year.astype(str)
    df['Mois'] = df['Date_Debut'].dt.month_name()
    
    # --- CALCUL REPEAT (Dispatch) ---
    # Un "Repeat" est défini ici comme une intervention sur le même SN sous 22 jours
    df = df.sort_values(['SN', 'Date_Debut'])
    df['Is_Repeat'] = df.groupby('SN')['Date_Debut'].diff().dt.days.le(22).astype(int)
    
    # Calcul durée en minutes
    df['Duree_Mins'] = (df['Date_Fin'] - df['Date_Debut']).dt.total_seconds() / 60
    df['Duree_Mins'] = df['Duree_Mins'].fillna(0).apply(lambda x: max(0, x))
    
    return df

df_raw = load_data()

if df_raw is not None and not df_raw.empty:
    # --- BARRE LATÉRALE : FILTRES ---
    st.sidebar.header("🔍 Filtres")
    
    selected_year = st.sidebar.multiselect("Année", options=sorted(df_raw['Année'].unique()), default=sorted(df_raw['Année'].unique()))
    selected_month = st.sidebar.multiselect("Mois", options=df_raw['Mois'].unique(), default=df_raw['Mois'].unique())
    
    tech_options = ["Tous"] + sorted(df_raw['Technicien'].dropna().unique().tolist())
    selected_tech = st.sidebar.selectbox("Technicien", options=tech_options)

    # Application des filtres
    mask = df_raw['Année'].isin(selected_year) & df_raw['Mois'].isin(selected_month)
    if selected_tech != "Tous":
        mask = mask & (df_raw['Technicien'] == selected_tech)
    
    df_filtered = df_raw[mask]

    # --- AFFICHAGE DASHBOARD ---
    st.title("📊 Arkeos Support Dashboard")
    
    # KPI
    total_int = len(df_filtered)
    total_rep = df_filtered['Is_Repeat'].sum()
    rate = (total_rep / total_int * 100) if total_int > 0 else 0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interventions", f"{total_int:,}")
    c2.metric("Taux Repeat", f"{rate:.1f}%")
    c3.metric("Run Time Total", f"{(df_filtered['Duree_Mins'].sum()/60):,.0f} h")
    c4.metric("Délai Moyen", f"{df_filtered['Duree_Mins'].mean():.1f} min")

    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🛠️ Top 10 Pannes")
        if 'Panne' in df_filtered.columns:
            top_p = df_filtered.groupby('Panne').size().nlargest(10).reset_index(name='Nb')
            st.plotly_chart(px.bar(top_p, x='Nb', y='Panne', orientation='h', color_discrete_sequence=['#4B8BBE']), use_container_width=True)

    with col2:
        st.subheader("👨‍🔧 Volume par Technicien")
        top_t = df_filtered.groupby('Technicien').size().nlargest(10).reset_index(name='Nb')
        st.plotly_chart(px.bar(top_t, x='Nb', y='Technicien', orientation='h', color_discrete_sequence=['#FF4B4B']), use_container_width=True)

    # Export des données filtrées
    buffer = io.BytesIO()
    df_filtered.to_excel(buffer, index=False)
    st.sidebar.download_button("📥 Télécharger Sélection (Excel)", buffer.getvalue(), "selection_arkeos.xlsx")

else:
    st.error("Données introuvables ou erreur de colonnes.")
