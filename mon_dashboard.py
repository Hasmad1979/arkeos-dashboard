import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import plotly.express as px

# 1. CONFIGURATION
st.set_page_config(page_title="Arkeos Technical Support Dashboard", layout="wide")

# --- STYLE CSS ---
st.markdown("""
    <style>
    [data-testid="stToolbar"] {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
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
    # Correction du nom de fichier selon vos captures GitHub
    file_name = "data_dynamics_brute.csv.csv" 
    if not os.path.exists(file_name):
        return None
    
    # Lecture avec détection automatique du séparateur
    df = pd.read_csv(file_name, sep=None, engine='python')
    
    # Nettoyage des noms de colonnes (enlève les espaces invisibles)
    df.columns = [str(c).strip() for c in df.columns]

    # Mapping basé sur votre export Dynamics
    mapping = {
        "Numéro de l'incident": "ID", 
        "Actifs du client": "SN", 
        "Owner": "Technicien", 
        "Créé le": "Date",
        "Type d'incident 2": "Panne" 
    }
    df = df.rename(columns=mapping)
    
    # Conversion date
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['SN', 'Date']).sort_values(['SN', 'Date'])
    
    # Calcul Repeat (22 jours ouvrés)
    df['Date_Prev'] = df.groupby('SN')['Date'].shift(1)
    
    def calc_bus(row):
        if pd.isnull(row['Date_Prev']): return None
        try:
            d1, d2 = row['Date_Prev'].date(), row['Date'].date()
            # np.busday_count compte les jours ouvrés
            return int(np.busday_count(d1, d2)) if d1 < d2 else 0
        except: return 0
        
    df['Ecart_Ouvres'] = df.apply(calc_bus, axis=1)
    df['Is_Repeat'] = ((df['Ecart_Ouvres'] >= 0) & (df['Ecart_Ouvres'] <= 22)).astype(int)
    return df

df_raw = load_data()

if df_raw is not None:
    noms_mois = {1:'Janvier', 2:'Février', 3:'Mars', 4:'Avril', 5:'Mai', 6:'Juin', 
                 7:'Juillet', 8:'Août', 9:'Septembre', 10:'Octobre', 11:'Novembre', 12:'Décembre'}

    # --- SIDEBAR FILTRES ---
    st.sidebar.title("🎮 Filtres")
    
    # Années
    years = sorted(df_raw['Date'].dt.year.unique(), reverse=True)
    sel_years = st.sidebar.multiselect("Années", years, default=years)
    
    # Mois
    df_raw['Mois_Num'] = df_raw['Date'].dt.month
