import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px

# 1. STYLE ET VISUALISATION (Design original)
st.set_page_config(page_title="Arkeos Technical Support", layout="wide")

st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #ffffff; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); border: 1px solid #edf2f7;
        text-align: center;
    }
    .main-title { font-size: 32px; font-weight: bold; color: #1a365d; }
    .stAlert { border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    # Nom exact du fichier détecté sur votre GitHub
    file_path = "data_dynamics_brute.csv.csv.csv"
    
    if not os.path.exists(file_path):
        return f"Fichier '{file_path}' introuvable."

    try:
        # Lecture flexible pour les exports Dynamics
        df = pd.read_csv(file_path, sep=None, engine='python', encoding_errors='ignore')
        df.columns = [str(c).strip() for c in df.columns]
        
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
        
        # --- CALCUL DU REPEAT (RDR 22j) ---
        df['Date_Prev'] = df.groupby('SN')['Date'].shift(1)
        
        def calc_bus(row):
            if pd.isnull(row['Date_Prev']): return None
            try:
                d1, d2 = row['Date_Prev'].date(), row['Date'].date()
                return int(np.busday_count(d1, d2)) if d1 < d2 else 0
            except: return 0
            
        df['Is_Repeat'] = df.apply(lambda r: 1 if 0 <= (calc_bus(r) or 999) <= 22 else 0, axis=1)
        return df

    except Exception as e:
        # C'est ce bloc 'except' qui manquait et causait votre erreur
