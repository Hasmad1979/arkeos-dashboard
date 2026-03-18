import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px

# 1. CONFIGURATION VISUELLE
st.set_page_config(page_title="Arkeos Technical Support", layout="wide")

st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #ffffff; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); border: 1px solid #edf2f7;
    }
    .main-title { font-size: 30px; font-weight: bold; color: #1a365d; }
    </style>
    """, unsafe_allow_html=True)

# 2. CHARGEMENT SÉCURISÉ
@st.cache_data
def load_data():
    # On teste le nom exact vu sur votre GitHub
    file_path = "data_dynamics_brute.csv.csv.csv"
    if not os.path.exists(file_path):
        return "introuvable"

    try:
        # Lecture avec détection automatique du séparateur
        df = pd.read_csv(file_path, sep=None, engine='python', encoding_errors='ignore')
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapping flexible pour éviter les KeyError
        mapping = {
            "Numéro de l'incident": "ID", "Incident Number": "ID",
            "Actifs du client": "SN", "Customer Asset": "SN",
            "Owner": "Technicien", "Propriétaire": "Technicien",
            "Créé le": "Date", "Created On": "Date",
            "Compte": "Client", "Account": "Client"
        }
        df = df.rename(columns=mapping)
        
        # Vérification des colonnes vitales
        if not {'SN', 'Date', 'Technicien'}.issubset(df.columns):
            return "colonnes_manquantes"

        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['SN', 'Date']).sort_values(['SN',
