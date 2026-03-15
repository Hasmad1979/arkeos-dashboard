import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# CONFIGURATION DE LA PAGE (Doit être en premier)
st.set_page_config(page_title="Arkeos Tech Support", layout="wide")

# CHARGEMENT DE LA CONFIGURATION
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# INITIALISATION DE L'AUTHENTIFICATION
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# FORMULAIRE DE CONNEXION
# Note: La version récente utilise 'location'
authenticator.login(location='main')

# VERIFICATION DU STATUT
if st.session_state["authentication_status"]:
    # --- ESPACE CONNECTÉ ---
    authenticator.logout('Déconnexion', 'sidebar')
    st.sidebar.success(f"Connecté : {st.session_state['name']}")
    
    # --- TON DASHBOARD CI-DESSOUS ---
    st.title("Arkeos Technical Support Dashboard")
    
    # Tes indicateurs
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Interventions", "2,700")
    with col2:
        st.metric("RDR % (7j)", "26.7%")
    with col3:
        st.metric("FTTR %", "73.3%")

    # Ici tu peux ajouter tes graphiques et tes alertes
    st.info("Bienvenue dans votre interface sécurisée.")

elif st.session_state["authentication_status"] is False:
    st.error('Identifiant ou mot de passe incorrect')

elif st.session_state["authentication_status"] is None:
    st.warning('Veuillez entrer votre identifiant et mot de passe')
