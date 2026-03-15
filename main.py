import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# 1. Chargement de la config
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# 2. Création de l'objet authentificateur
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

# 3. Affichage du formulaire de login
name, authentication_status, username = authenticator.login('Login', 'main')

# 4. Vérification du statut
if authentication_status:
    # --- ICI TU METS TOUT TON CODE ACTUEL DU DASHBOARD ---
    authenticator.logout('Déconnexion', 'sidebar')
    st.write(f'Bienvenue *{name}*')
    st.title('Arkeos Technical Support Dashboard')
    # ... le reste de tes graphiques ...

elif authentication_status == False:
    st.error('Identifiant ou mot de passe incorrect')
elif authentication_status == None:
    st.warning('Veuillez entrer votre identifiant et mot de passe')
