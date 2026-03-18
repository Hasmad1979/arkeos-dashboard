import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import plotly.express as px

# 1. CONFIGURATION
st.set_page_config(page_title="Arkeos Dashboard", layout="wide")

st.markdown("""
    <style>
    [data-testid="stToolbar"] {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .stApp { background-color: #f8f9fa; }
    div[data-testid="stMetric"] {
        background-color: #ffffff; padding: 15px; border-radius: 10px;
        border-left: 5px solid #004a99; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    # On teste les deux noms de fichiers possibles vus sur votre GitHub
    for f in ["data_dynamics_brute.csv.csv", "data_dynamics_brute.csv.csv.csv"]:
        if os.path.exists(f):
            df = pd.read_csv(f, sep=None, engine='python')
            
            # Nettoyage automatique des noms de colonnes
            df.columns = [str(c).strip() for c in df.columns]

            # Mapping flexible pour éviter la KeyError
            mapping = {
                "Numéro de l'incident": "ID", "Incident Number": "ID",
                "Actifs du client": "SN", "Customer Asset": "SN",
                "Owner": "Technicien", "Propriétaire": "Technicien",
                "Créé le": "Date", "Created On": "Date",
                "Type d'incident 2": "Panne"
            }
            df = df.rename(columns=mapping)
            
            # Vérification de sécurité : si 'Technicien' manque, on utilise 'Owner' ou une colonne vide
            if 'Technicien' not in df.columns:
                df['Technicien'] = "Inconnu"

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
    return None

df_raw = load_data()
