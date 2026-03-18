import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px

# 1. CONFIGURATION ET STYLE
st.set_page_config(page_title="Arkeos Technical Support", layout="wide")

st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #ffffff; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); border: 1px solid #edf2f7;
        text-align: center;
    }
    .main-title { font-size: 32px; font-weight: bold; color: #1a365d; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    # Nom du fichier vu sur votre GitHub
    file_path = "data_dynamics_brute.csv.csv.csv"
    
    if not os.path.exists(file_path):
        return "Fichier introuvable. Vérifiez le nom sur GitHub."

    try:
        # Lecture flexible (détection séparateur)
        df = pd.read_csv(file_path, sep=None, engine='python', encoding_errors='ignore')
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapping exhaustif pour Dynamics (Français et Anglais)
        mapping = {
            "Numéro de l'incident": "ID", "Incident Number": "ID",
            "Actifs du client": "SN", "Customer Asset": "SN",
            "Owner": "Technicien", "Propriétaire": "Technicien",
            "Créé le": "Date", "Created On": "Date",
            "Compte": "Client", "Account": "Client"
        }
        df = df.rename(columns=mapping)
        
        # Sécurité : Si 'Technicien' n'existe toujours pas, on utilise 'Inconnu'
        if 'Technicien' not in df.columns:
            df['Technicien'] = "Non spécifié"
            
        # Nettoyage des dates
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['SN', 'Date']).sort_values(['SN', 'Date'])
        
        # Calcul du Repeat (RDR 22j)
        df['Date_Prev'] = df.groupby('SN')['Date'].shift(1)
        
        def calc_repeat(row):
            if pd.isnull(row['Date_Prev']): return 0
            try:
                d1, d2 = row['Date_Prev'].date(), row['Date'].date()
                diff = int(np.busday_count(d1, d2)) if d1 < d2 else 0
                return 1 if 0 <= diff <= 22 else 0
            except: return 0
            
        df['Is_Repeat'] = df.apply(calc_repeat, axis=1)
        return df
    except Exception as e:
        return f"Erreur technique : {str(e)}"

# 3. LOGIQUE D'AFFICHAGE
data = load_data()

if isinstance(data, str):
    st.error(f"⚠️ {data}")
else:
    df = data
    st.markdown('<p class="main-title">📟 Arkeos Technical Support Dashboard</p>', unsafe_allow_html=True)
    
    # Sidebar Filters avec sécurité contre les colonnes manquantes
    st.sidebar.title("🔍 Paramètres")
    
    # Filtre Année
    years = sorted(df['Date'].dt.year.unique().tolist(), reverse=True)
    sel_year = st.sidebar.multiselect("Année", years, default=years[:1])
    
    # Filtre Technicien (Correction du KeyError)
    tech_list = sorted(df['Technicien'].unique().astype(str).tolist())
    sel_tech = st.sidebar.selectbox("Technicien", ["Tous"] + tech_list)

    # Application des filtres
    df_f = df[df['Date'].dt.year.isin(sel_year)].copy()
    if sel_tech != "Tous":
        df_f = df_f[df_f['Technicien'] == sel_tech]

    # --- AFFICHAGE DES KPIs ---
    total = len(df_f)
    nb_reps = df_f['Is_Repeat'].sum()
    rdr_rate = (nb_reps / total * 100) if total > 0 else 0

    k1, k2, k
