import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px

# 1. CONFIGURATION ET STYLE (RETOUR AU DESIGN ORIGINAL)
st.set_page_config(page_title="Arkeos Technical Support", layout="wide")

st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #f0f2f6;
    }
    .stAlert {
        border-radius: 10px;
        border-left: 5px solid #004a99;
    }
    .main-title { font-size: 32px; font-weight: bold; color: #1e293b; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    # Détection du fichier (on garde votre nom actuel sur GitHub)
    file_name = "data_dynamics_brute.csv.csv.csv"
    if not os.path.exists(file_name): return None

    try:
        # Lecture robuste
        df = pd.read_csv(file_name, sep=None, engine='python', encoding_errors='ignore')
        df.columns = [str(c).strip() for c in df.columns]

        # Mapping intelligent pour retrouver vos colonnes
        mapping = {
            "Numéro de l'incident": "ID", "Incident Number": "ID",
            "Actifs du client": "SN", "Customer Asset": "SN",
            "Owner": "Technicien", "Propriétaire": "Technicien",
            "Créé le": "Date", "Created On": "Date",
            "Compte": "Client", "Account": "Client"
        }
        df = df.rename(columns=mapping)
        
        # Nettoyage
        df['Date
