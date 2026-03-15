import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import plotly.express as px
import plotly.graph_objects as go

# 1. Configuration de la page
st.set_page_config(page_title="Arkeos Technical Support Dashboard", layout="wide")

# --- STYLE CSS PERSONNALISÉ ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            /* Fond de la page gris très clair */
            .stApp { background-color: #f8f9fa; }
            /* Style des métriques */
            div[data-testid="stMetric"] {
                background-color: #ffffff;
                padding: 15px;
                border-radius: 10px;
                border-left: 5px solid #004a99;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

@st.cache_data
def load_data():
    file_name = "data_dynamics_brute.csv.csv"
    if not os.path.exists(file_name):
        return None
    df = pd.read_csv(file_name)
    df = df.rename(columns={"Numéro de l'incident": "ID", "Actifs du client": "SN", "Owner": "Technicien", "Créé le": "Date"})
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['SN', 'Date']).sort_values(['SN', 'Date'])
    
    # Calcul Repeat (22 jours ouvrés)
    df['Date_Prev'] = df.groupby('SN')['Date'].shift(1)
    def calc_bus(row):
        if pd.isnull(row['Date_Prev']): return None
        d1, d2 = row['Date_Prev'].date(), row['Date'].date()
        try:
            # np.busday_count exclusif sur la fin, on ajoute 0 ou 1 selon votre logique métier
            return int(np.busday_count(d1, d2)) if d1 < d2 else 0
        except:
            return 0

    df['Ecart_Ouvres'] = df.apply(calc_bus, axis=1)
    df['Is_Repeat'] = ((df['Ecart_Ouvres'] >= 0) & (df['Ecart_Ouvres'] <= 22)).astype(int)
    return df

df_raw = load_data()

if df_raw is not None:
    noms_mois = {1:'Janvier', 2:'Février', 3:'Mars', 4:'Avril', 5:'Mai', 6:'Juin', 
                 7:'Juillet', 8:'Août', 9:'Septembre', 10:'Octobre', 11:'Novembre', 12:'Décembre'}

    # --- SIDEBAR ---
    if os.path.exists("ark.png"):
        st.sidebar.image("ark.png", width=150)
    
    st.sidebar.title("🎮 Filtres")
    
    years = sorted(df_raw['Date'].dt.year.unique(), reverse=True)
    sel_years
