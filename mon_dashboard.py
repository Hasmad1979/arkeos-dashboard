import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import BytesIO
import streamlit_authenticator as stauth

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(layout="wide", page_title="Arkeos Dash")

# --- 1. CONFIGURATION DE L'AUTHENTIFICATION ---
config = {
    'usernames': {
        'admin': {
            'name': 'Administrateur Arkeos',
            'password': '$2b$12$6pXk0/5L2JvWn7L6f5E.e.8YQvI5UuV.6M1/6Wp6F5/vW8R6H5W' # admin123
        }
    }
}

authenticator = stauth.Authenticate(
    config,
    "arkeos_session", 
    "signature_key_123", 
    cookie_expiry_days=1
)

# --- CORRECTION ICI POUR LA NOUVELLE VERSION ---
authenticator.login(location='main')

# --- 2. LOGIQUE D'ACCÈS ---
if st.session_state["authentication_status"] == False:
    st.error("L'identifiant ou le mot de passe est incorrect.")

elif st.session_state["authentication_status"] == None:
    st.info("Veuillez vous connecter pour accéder au tableau de bord.")

elif st.session_state["authentication_status"]:
    # Bouton de déconnexion
    authenticator.logout('Déconnexion', 'sidebar')
    
    # Récupération du nom pour l'affichage
    nom_utilisateur = st.session_state["name"]

    # --- 3. LE RESTE DE VOTRE CODE ---
    @st.cache_data
    def load_data_v2():
        f = "data_dynamics_brute.csv.csv.csv"
        if not os.path.exists(f): return pd.DataFrame()
        df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
        
        col_date, col_sn, col_tech, col_client = None, None, None, None
        for c in df.columns:
            l = str(c).lower()
            if not col_date and any(x in l for x in ['date', 'créé']): col_date = c
            elif not col_sn and any(x in l for x in ['actif', 'asset', 'sn', 'série']): col_sn = c
            elif not col_tech and any(x in l for x in ['owner', 'propriétaire', 'tech']): col_tech = c
            elif not col_client and any(x in l for x in ['client', 'compte', 'customer']): col_client = c
        
        rename_dict = {}
        if col_date: rename_dict[col_date] = 'Date'
        if col_sn: rename_dict[col_sn] = 'SN'
        if col_tech: rename_dict[col_tech] = 'Tech'
        if col_client: rename_dict[col_client] = 'Client'
        
        df = df.rename(columns=rename_dict)
        cols_to_keep = [c for c in ['Date', 'SN', 'Tech', 'Client'] if c in df.columns]
        df = df[cols_to_keep].copy()
        
        if 'Date' not in df.columns or 'SN' not in df.columns: return pd.DataFrame()
        
        df['Tech'] = df.get('Tech', pd.Series(['Inconnu']*len(df))).fillna('Inconnu').astype(str)
        df['Client'] = df.get('Client', pd.Series(['N/A']*len(df))).fillna('N/A').astype(str)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
        df = df.drop_duplicates(subset=['SN', 'Date']).reset_index(drop=True)
        df['Prev'] = df.groupby('SN')['Date'].shift(1)
        df['R'] = (df['Date'] - df['Prev']).dt.days.apply(lambda x: 1 if pd.notna(x) and 0 <= x <= 22 else 0)
        return df

    df = load_data_v2()

    if df.empty:
        st.error("Données introuvables. Vérifiez le fichier CSV.")
    else:
        st.title("📟 Arkeos Technical Dashboard")
        st.sidebar.write(f"Utilisateur : **{nom_utilisateur}**")
        
        # ... (Gardez le reste de votre code de filtres et graphiques ici) ...
        # (Le reste du code que vous aviez précédemment reste identique)
