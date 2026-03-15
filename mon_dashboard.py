import streamlit as st
import pandas as pd
import plotly.express as px
import os
from PIL import Image

# 1. CONFIGURATION ET STYLE CSS CUSTOM
st.set_page_config(page_title="Arkeos Support Pro", layout="wide")

st.markdown("""
    <style>
    /* Style pour les cartes KPI cliquables */
    .kpi-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e0e6ed;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        transition: transform 0.2s, border-color 0.2s;
        cursor: pointer;
    }
    .kpi-card:hover {
        transform: translateY(-5px);
        border-color: #1E3A8A;
        background-color: #f8fbff;
    }
    .kpi-title { font-size: 16px; color: #64748b; font-weight: 500; }
    .kpi-value { font-size: 32px; color: #1E3A8A; font-weight: 700; margin: 10px 0; }
    .kpi-icon { font-size: 24px; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CHARGEMENT DES DONNÉES NETTOYÉES
@st.cache_data
def load_data():
    file_path = "data_dynamics_brute.csv.csv"
    if not os.path.exists(file_path): return None
    df = pd.read_csv(file_path)
    
    # Mapping et Nettoyage
    df = df.rename(columns={
        "Actif client principal de l'incident": "Actif_SN",
        "Propriétaire": "Technicien",
        "Date de création": "Date"
    })
    
    # Suppression des 'nan' et formatage texte
    df['Actif_SN'] = df['Actif_SN'].astype(str).str.replace(r'\.0$', '', regex=True)
    df = df[~df['Actif_SN'].isin(['nan', 'None', 'nan.0', ''])]
    
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    # Simulation de la logique RDR (Repeat dans les 7 jours)
    df = df.sort_values(['Actif_SN', 'Date'])
    df['Diff'] = df.groupby('Actif_SN')['Date'].diff().dt.days
    df['Is_Repeat'] = (df['Diff'] <= 7).astype(int)
    
    return df

df = load_data()

# 3. BARRE LATÉRALE (SIDEBAR)
if df is not None:
    with st.sidebar:
        if os.path.exists("download.png"):
            st.image("download.png", use_container_width=True) # Logo Arkeos
        
        st.markdown("---")
        st.header("🔍 Filtres")
        tech_list = ["Tous"] + sorted(df['Technicien'].unique().tolist())
        sel_tech = st.selectbox("Technicien", tech_list)

    # Application des filtres
    df_f = df if sel_tech == "Tous" else df[df['Technicien'] == sel_tech]

    # 4. CALCUL DES KPI
    total_int = len(df_f)
    nb_repeats = df_f['Is_Repeat'].sum()
    rdr_rate = (nb_repeats / total_int * 100) if total_int > 0 else 0
    fttr_rate = 100 - rdr_rate

    # 5. AFFICHAGE DES KPI PROFESSIONNELS
    st.title("📊 Arkeos Support Technique Dashboard")
    
    # Initialisation du choix de vue via session_state
    if 'view' not in st.session_state:
        st.session_state.view = "Global"

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button(f"📄 Total Interventions\n{total_int:,}", key="btn_total", use_container_width=True):
            st.session_state.view = "Global"
    
    with col2:
        # Couleur rouge pour le RDR (Alerte)
        if st.button(f"🔄 RDR % (Repeats)\n{rdr_rate:.1f}%", key="btn_rdr", use_container_width=True):
            st.session_state.view = "RDR"

    with col3:
        # Couleur verte pour le FTTR (Performance)
        if st.button(f"✅ FTTR %\n{fttr_rate:.1f}%", key="btn_fttr", use_container_width=True):
            st.session_state.view = "FTTR"

    with col4:
        st.button(f"⚠️ Nb Repeats\n{nb_repeats}", key="btn_nb", use_container_width=True)

    st.markdown("---")

    # 6. VUES DYNAMIQUES SELON LE CLIC
    if st.session_state.view == "RDR":
        st.subheader("🚨 Analyse approfondie des Repeats (RDR)")
        # On montre les actifs qui causent le plus de retours
        df_reps = df_f[df_f['Is_Repeat'] == 1]
        top_a = df_reps['Actif_SN'].value_counts().nlargest(10).reset_index()
        fig = px.bar(top_a, x='count', y='Actif_SN', orientation='h', title="Top 10 Actifs à Problèmes", color_discrete_sequence=['#E74C3C'])
        st.plotly_chart(fig, use_container_width=True)
        
    elif st.session_state.view == "FTTR":
        st.subheader("🏆 Excellence : Succès du premier coup (FTTR)")
        # On montre les techniciens avec le meilleur taux
        tech_perf = df_f.groupby('Technicien')['Is_Repeat'].mean().reset_index()
        tech_perf['FTTR'] = (1 - tech_perf['Is_Repeat']) * 100
        fig = px.bar(tech_perf.nlargest(10, 'FTTR'), x='FTTR', y='Technicien', orientation='h', title="Top 10 Techniciens Performants", color_discrete_sequence=['#2ECC71'])
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        # Vue globale par défaut
        st.subheader("📈 Tendance Générale")
        df_f['Semaine'] = df_f['Date'].dt.strftime('%Y-W%V')
        trend = df_f.groupby('Semaine').size().reset_index(name='Volume')
        fig = px.line(trend, x='Semaine', y='Volume', markers=True, title="Volume d'interventions hebdomadaire")
        st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Données introuvables. Vérifiez le fichier 'data_dynamics_brute.csv.csv'.")
