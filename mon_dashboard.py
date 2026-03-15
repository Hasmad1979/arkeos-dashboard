import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import plotly.express as px
from PIL import Image

# --- 1. CONFIGURATION & THEME ---
st.set_page_config(page_title="Arkeos Performance Pro", layout="wide")

# Style CSS pour un look "Executive"
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetricValue"] { font-size: 28px; color: #1E3A8A; font-weight: bold; }
    div[data-testid="metric-container"] {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #eef2f6;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #f1f3f5;
        border-radius: 5px 5px 0 0;
        padding: 10px 20px;
    }
    .stTabs [data-baseweb="tab--active"] { background-color: #1E3A8A !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CHARGEMENT DES DONNÉES ---
@st.cache_data
def load_data():
    file_name = "data_dynamics_brute.csv.csv" 
    if not os.path.exists(file_name):
        return None
    
    df = pd.read_csv(file_name)

    mapping = {
        "Numéro d'ordre de travail": "ID",
        "Propriétaire": "Technicien",
        "Type d'incident principal": "Panne",
        "Compte de service": "Compte",
        "Actif client principal de l'incident": "Actif_SN",
        "Date de création": "Date_Debut"
    }
    
    df = df.rename(columns=mapping)
    df['Date_Debut'] = pd.to_datetime(df['Date_Debut'], errors='coerce')
    
    # On garde tout ce qui a un Actif et une Date (Inclus CC-WO)
    df = df.dropna(subset=['Date_Debut', 'Actif_SN'])

    # --- CALCUL REPEAT (7 JOURS OUVRES) ---
    df = df.sort_values(['Actif_SN', 'Date_Debut'])
    df['Date_Precedente'] = df.groupby('Actif_SN')['Date_Debut'].shift(1)
    
    def calc_working_days(row):
        if pd.isnull(row['Date_Precedente']): return np.nan
        try:
            return np.busday_count(row['Date_Precedente'].date(), row['Date_Debut'].date())
        except: return np.nan

    df['Jours_Ouvres_Diff'] = df.apply(calc_working_days, axis=1)
    df['Is_Repeat'] = df['Jours_Ouvres_Diff'].le(7).astype(int)
    
    # Temps
    df['Année'] = df['Date_Debut'].dt.year.astype(str)
    df['Mois_Nom'] = df['Date_Debut'].dt.strftime('%B')
    df['Semaine'] = df['Date_Debut'].dt.strftime('%Y-W%V')
    
    return df

df_raw = load_data()

# --- 3. LOGO & SIDEBAR ---
if df_raw is not None:
    with st.sidebar:
        try:
            logo = Image.open('download.png')
            st.image(logo, width=300) # Logo Agrandi
        except:
            st.write("🏛️ **ARKEOS SUPPORT**")
        
        st.markdown("---")
        st.header("🔍 FILTRES")
        
        years = sorted(df_raw['Année'].unique(), reverse=True)
        sel_year = st.sidebar.multiselect("Années", options=years, default=years)
        
        # Filtre Propriétaire propre
        all_techs = df_raw['Technicien'].dropna().unique()
        clean_techs = sorted([t for t in all_techs if " " in str(t) and not str(t).startswith("CC-WO")])
        sel_tech = st.sidebar.selectbox("Technicien", options=["Tous"] + clean_techs)

        # Application filtres
        mask = df_raw['Année'].isin(sel_year)
        if sel_tech != "Tous":
            mask = mask & (df_raw['Technicien'] == sel_tech)
        
        df_f = df_raw[mask]

    # --- 4. DASHBOARD CORPS ---
    st.title("📊 Dashboard Performance Technique")
    st.markdown(f"**Analyse :** {sel_tech} | **Période :** {', '.join(sel_year)}")

    # KPI Row
    total = len(df_f)
    reps = df_f['Is_Repeat'].sum()
    rdr = (reps / total * 100) if total > 0 else 0
    fttr = 100 - rdr if total > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Interventions", f"{total:,}")
    c2.metric("Taux RDR (7j)", f"{rdr:.1f}%", delta=f"{rdr:.1f}%", delta_color="inverse")
    c3.metric("Taux FTTR", f"{fttr:.1f}%")
    c4.metric("Nb de Repeats", f"{reps:,}")

    st.markdown("---")

    # Onglets pour la présentation
    t1, t2, t3 = st.tabs(["📈 Tendance Hebdo", "📠 Analyse Actifs", "🏢 Analyse Comptes"])

    with t1:
        st.subheader("Évolution du RDR % par Semaine")
        tw = df_f.groupby('Semaine')['Is_Repeat'].mean().reset_index()
        tw['RDR %'] = (tw['Is_Repeat'] * 100).round(1)
        fig_trend = px.line(tw, x='Semaine', y='RDR %', text='RDR %', markers=True, 
                            color_discrete_sequence=['#1E3A8A'])
        fig_trend.update_traces(textposition="top center")
        st.plotly_chart(fig_trend, use_container_width=True)

    with t2:
        col_m1, col_m2 = st.columns([2, 1])
        with col_m1:
            st.subheader("Top 10 Actifs (Machines critiques)")
            top
