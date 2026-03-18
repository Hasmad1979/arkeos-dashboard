import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px

# 1. STYLE ET CONFIGURATION
st.set_page_config(page_title="Arkeos Dashboard", layout="wide")

st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #ffffff; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); border: 1px solid #edf2f7;
        text-align: center;
    }
    .main-title { font-size: 30px; font-weight: bold; color: #1a365d; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    file_path = "data_dynamics_brute.csv.csv.csv"
    if not os.path.exists(file_path):
        return "Fichier introuvable"

    try:
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
        
        # Calcul du Repeat
        df['Date_Prev'] = df.groupby('SN')['Date'].shift(1)
        
        def check_repeat(row):
            if pd.isnull(row['Date_Prev']): return 0
            try:
                d1, d2 = row['Date_Prev'].date(), row['Date'].date()
                diff = int(np.busday_count(d1, d2)) if d1 < d2 else 0
                return 1 if 0 <= diff <= 22 else 0
            except: return 0
            
        df['Is_Repeat'] = df.apply(check_repeat, axis=1)
        return df
    except Exception as e:
        return f"Erreur : {str(e)}"

# 3. INTERFACE
data = load_data()

if isinstance(data, str):
    st.error(f"⚠️ {data}")
else:
    st.markdown('<p class="main-title">📟 Arkeos Technical Support</p>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.header("Filtres")
    years = sorted(df['Date'].dt.year.unique(), reverse=True)
    sel_year = st
