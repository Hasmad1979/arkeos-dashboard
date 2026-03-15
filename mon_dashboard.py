import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import plotly.express as px

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="Arkeos Technical Support Dashboard", layout="wide")

# --- STYLE CSS ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { background-color: #f8f9fa; }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #004a99;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    # ATTENTION : Vérifiez bien que ce nom de fichier est identique sur GitHub
    file_name = "data_dynamics_brute.csv.csv" 
    
    if not os.path.exists(file_name):
        return None
        
    df = pd.read_csv(file_name)
    # Renommage des colonnes pour correspondre à votre logique
    df = df.rename(columns={
        "Numéro de l'incident": "ID", 
        "Actifs du client": "SN", 
        "Owner": "Technicien", 
        "Créé le": "Date"
    })
    
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['SN', 'Date']).sort_values(['SN', 'Date'])
    
    # Calcul Repeat (22 jours ouvrés)
    df['Date_Prev'] = df.groupby('SN')['Date'].shift(1)
    
    def calc_bus(row):
        if pd.isnull(row['Date_Prev']): return None
        d1, d2 = row['Date_Prev'].date(), row['Date'].date()
        try:
            return int(np.busday_count(d1, d2)) if d1 < d2 else 0
        except:
            return 0

    df['Ecart_Ouvres'] = df.apply(calc_bus, axis=1)
    df['Is_Repeat'] = ((df['Ecart_Ouvres'] >= 0) & (df['Ecart_Ouvres'] <= 22)).astype(int)
    return df

# --- CHARGEMENT ---
df_raw = load_data()

# --- BLOC PRINCIPAL (Sécurisé) ---
if df_raw is not None:
    noms_mois = {1:'Janvier', 2:'Février', 3:'Mars', 4:'Avril', 5:'Mai', 6:'Juin', 
                 7:'Juillet', 8:'Août', 9:'Septembre', 10:'Octobre', 11:'Novembre', 12:'Décembre'}

    # --- SIDEBAR ---
    if os.path.exists("ark.png"):
        st.sidebar.image("ark.png", width=150)
    
    st.sidebar.title("🎮 Filtres")
    
    # Création des listes pour les filtres
    years = sorted(df_raw['Date'].dt.year.unique(), reverse=True)
    sel_years = st.sidebar.multiselect("Années", years, default=years)
    
    df_raw['Mois_Num'] = df_raw['Date'].dt.month
    df_raw['Mois_Nom'] = df_raw['Mois_Num'].map(noms_mois)
    available_months = sorted(df_raw['Mois_Num'].unique())
    month_options = [noms_mois[m] for m in available_months]
    sel_months_names = st.sidebar.multiselect("Mois", month_options, default=month_options)
    
    techs = sorted(df_raw['Technicien'].astype(str).unique().tolist())
    sel_techs = st.sidebar.multiselect("Techniciens", techs, default=techs)
    
    # Application des filtres
    df_f = df_raw[
        (df_raw['Date'].dt.year.isin(sel_years)) & 
        (df_raw['Mois_Nom'].isin(sel_months_names)) &
        (df_raw['Technicien'].isin(sel_techs))
    ].copy()

    # --- DASHBOARD VISUEL ---
    st.title("📊 Arkeos Technical Support Dashboard")
    st.markdown("---")

    if not df_f.empty:
        # 1. KPI
        total_int = len(df_f)
        total_rep = df_f['Is_Repeat'].sum()
        repeat_rate = (total_rep / total_int * 100) if total_int > 0 else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Interventions", f"{total_int:,}")
        c2.metric("Total Repeats", f"{total_rep:,}")
        c3.metric("Taux de Repeat", f"{repeat_rate:.1f}%", delta_color="inverse")

        # 2. ÉVOLUTION MENSUELLE
        st.write("")
        with st.container(border=True):
            st.subheader("📈 Évolution Mensuelle du Taux de Repeat")
            evol = df_f.groupby('Mois_Num')['Is_Repeat'].mean() * 100
            evol = evol.reset_index()
            evol['Mois_Label'] = evol['Mois_Num'].map(lambda x: noms_mois[x])

            fig_evol = px.line(evol, x='Mois_Label', y='Is_Repeat', markers=True, text=[f"{v:.1f}%
