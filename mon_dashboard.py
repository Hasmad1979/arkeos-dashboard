import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px

# 1. CONFIGURATION ET STYLE PREMIUM (IMAGE 95BE44)
st.set_page_config(page_title="Arkeos Technical Support", layout="wide")

st.markdown("""
    <style>
    /* Style des cartes de métriques */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border: 1px solid #edf2f7;
        text-align: center;
    }
    /* Style des alertes Good To Know */
    .stAlert {
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    /* Titre principal */
    .main-title { 
        font-size: 34px; 
        font-weight: bold; 
        color: #1a365d; 
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    file_name = "data_dynamics_brute.csv.csv.csv"
    if not os.path.exists(file_name): return None
    try:
        # Lecture flexible pour Dynamics
        df = pd.read_csv(file_name, sep=None, engine='python', encoding_errors='ignore')
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapping des colonnes pour retrouver les données
        mapping = {
            "Numéro de l'incident": "ID", "Incident Number": "ID",
            "Actifs du client": "SN", "Customer Asset": "SN",
            "Owner": "Technicien", "Propriétaire": "Technicien",
            "Créé le": "Date", "Created On": "Date",
            "Compte": "Client", "Account": "Client"
        }
        df = df.rename(columns=mapping)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['SN', 'Date']).sort_values(['SN', 'Date'])
        
        # Calcul du Repeat (RDR)
        df['Date_Prev'] = df.groupby('SN')['Date'].shift(1)
        def calc_bus(row):
            if pd.isnull(row['Date_Prev']): return None
            try:
                d1, d2 = row['Date_Prev'].date(), row['Date'].date()
                return int(np.busday_count(d1, d2)) if d1 < d2 else
