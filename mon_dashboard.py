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
# Note : Dans un environnement réel, utilisez des mots de passe hachés.
# 'admin123' haché ressemble à : $2b$12$6pXk0/5L2JvWn7L6f5E.e.8YQvI5UuV.6M1/6Wp6F5/vW8R6H5W
names = ["Administrateur Arkeos"]
usernames = ["admin"]
passwords = ["$2b$12$6pXk0/5L2JvWn7L6f5E.e.8YQvI5UuV.6M1/6Wp6F5/vW8R6H5W"] # Correspond à 'admin123'

authenticator = stauth.Authenticate(
    {'usernames': {usernames[0]: {'name': names[0], 'password': passwords[0]}}},
    "arkeos_session", 
    "signature_key_123", 
    cookie_expiry_days=1
)

# Affichage du formulaire (dans la zone principale)
name, authentication_status, username = authenticator.login('Connexion au Dashboard Arkeos', 'main')

# --- 2. LOGIQUE DE SÉCURITÉ ---
if authentication_status == False:
    st.error("L'identifiant ou le mot de passe est incorrect.")
elif authentication_status == None:
    st.info("Veuillez vous connecter pour accéder aux données techniques.")
elif authentication_status:
    
    # Bouton de déconnexion dans la barre latérale
    authenticator.logout('Déconnexion', 'sidebar')
    
    # --- 3. VOTRE CODE INITIAL (DÉBUT) ---
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
            elif not col_tech and any(x in l for x in ['owner', 'propri
