import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# --- AUTHENTIFICATION ---
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Affichage de la boîte de connexion
name, authentication_status, username = authenticator.login('Connexion Arkeos', 'main')

if authentication_status:
    # --- TON CODE DASHBOARD COMMENCE ICI ---
    authenticator.logout('Déconnexion', 'sidebar')
    st.write(f'Bienvenue *{name}*')
    
    # C'est ici que tu appelles tes fonctions de mon_dashboard.py
    # ex: import mon_dashboard; mon_dashboard.display_metrics()
    
elif authentication_status == False:
    st.error('Identifiant ou mot de passe incorrect')
elif authentication_status == None:
    st.warning('Veuillez entrer vos accès')
