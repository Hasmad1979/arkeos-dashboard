import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px

st.set_page_config(page_title="Arkeos Support", layout="wide")

@st.cache_data
def load_data():
    # On cherche le fichier avec son nom actuel sur votre GitHub
    file_path = "data_dynamics_brute.csv.csv.csv"
    if not os.path.exists(file_path):
        return "Fichier CSV introuvable sur GitHub."

    try:
        # Lecture du fichier
        df = pd.read_csv(file_path, sep=None, engine='python', encoding_errors='ignore')
        df.columns = [str(c).strip() for c in df.columns]
        
        # --- SOLUTION AU PROBLÈME 'DATE' ---
        # On cherche une colonne qui ressemble à une date ou un identifiant
        mapping = {
            "Numéro de l'incident": "ID", "Incident Number": "ID",
            "Actifs du client": "SN", "Customer Asset": "SN",
            "Créé le": "Date", "Created On": "Date", "Date": "Date",
            "Owner": "Tech", "Propriétaire": "Tech"
        }
        df = df.rename(columns=mapping)

        # Si 'Date' manque toujours, on prend la 1ère colonne qui contient 'Date' ou 'Créé'
        if 'Date' not in df.columns:
            for col in df.columns:
                if 'date' in col.lower() or 'créé' in col.lower() or 'created' in col.lower():
                    df = df.rename(columns={col: 'Date'})
                    break

        # Nettoyage final
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
        
        # Calcul Repeat (RDR 22j)
        df['Prev'] = df.groupby('SN')['Date'].shift(1)
        def check_r(r):
            try:
                if pd.isnull(r['Prev']): return 0
                d = int(np.busday_count(r['Prev'].date(), r['Date'].date()))
                return 1 if 0 <= d <= 22 else 0
            except: return 0
        df['Is_Repeat'] = df.apply(check_r, axis=1)
        return df

    except Exception as e:
        return f"Erreur de structure : {str(e)}"

# AFFICHAGE
data = load_data()
if isinstance(data, str):
    st.error(f
