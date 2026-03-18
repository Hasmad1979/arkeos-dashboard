import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import plotly.express as px

# 1. CONFIGURATION
st.set_page_config(page_title="Arkeos Dashboard", layout="wide")

# Masquer les menus Streamlit
st.markdown("<style>[data-testid='stToolbar'] {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>", unsafe_allow_html=True)

@st.cache_data
def load_data():
    file_name = "data_dynamics_brute.csv.csv"
    if not os.path.exists(file_name):
        return None
    
    # Lecture flexible
    df = pd.read_csv(file_name, sep=None, engine='python')
    df.columns = [str(c).strip() for c in df.columns]

    # Mapping ultra-flexible pour éviter les erreurs de colonnes
    mapping = {
        "Numéro de l'incident": "ID", "Incident Number": "ID",
        "Actifs du client": "SN", "Customer Asset": "SN",
        "Owner": "Technicien", "Propriétaire": "Technicien",
        "Créé le": "Date", "Created On": "Date",
        "Type d'incident 2": "Panne"
    }
    df = df.rename(columns=mapping)
    
    # Sécurité si une colonne manque
    if 'Technicien' not in df.columns: df['Technicien'] = "Non assigné"
    if 'SN' not in df.columns: return None

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['SN', 'Date']).sort_values(['SN', 'Date'])
    
    # Calcul Repeat (22 jours ouvrés)
    df['Date_Prev'] = df.groupby('SN')['Date'].shift(1)
    def calc_bus(row):
        if pd.isnull(row['Date_Prev']): return None
        try:
            d1, d2 = row['Date_Prev'].date(), row['Date'].date()
            return int(np.busday_count(d1, d2)) if d1 < d2 else 0
        except: return 0
    df['Ecart_Ouvres'] = df.apply(calc_bus, axis=1)
    df['Is_Repeat'] = ((df['Ecart_Ouvres'] >= 0) & (df['Ecart_Ouvres'] <= 22)).astype(int)
    return df

df_raw = load_data()

if df_raw is not None:
    st.sidebar.title("🎮 Filtres")
    
    # Filtre Année
    years = sorted(df_raw['Date'].dt.year.unique(), reverse=True)
    sel_years = st.sidebar.multiselect("Années", years, default=years)
    
    # Filtre Technicien
    techs = sorted(df_raw['Technicien'].unique().tolist())
    sel_techs = st.sidebar.multiselect("Techniciens", techs, default=techs)
    
    df_f = df_raw[(df_raw['Date'].dt.year.isin(sel_years)) & (df_raw['Technicien'].isin(sel_techs))]

    st.title("📊 Arkeos Technical Support")
    
    if not df_f.empty:
        # Affichage des KPIs
        c1, c2, c3 = st.columns(3)
        c1.metric("Interventions", f"{len(df_f):,}")
        c2.metric("Total Repeats", f"{df_f['Is_Repeat'].sum():,}")
        rate = (df_f['Is_Repeat'].sum() / len(df_f) * 100)
        c3.metric("Taux de Repeat", f"{rate:.1f}%")

        # Graphique
        st.subheader("📈 Évolution du Repeat")
        df_f['Mois'] = df_f['Date'].dt.strftime('%Y-%m')
        evol = df_f.groupby('Mois')['Is_Repeat'].mean().reset_index()
        fig = px.line(evol, x='Mois', y='Is_Repeat', title="Tendance mensuelle")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Aucune donnée avec ces filtres.")
else:
    st.error("Fichier de données introuvable. Vérifiez le nom sur GitHub.")
