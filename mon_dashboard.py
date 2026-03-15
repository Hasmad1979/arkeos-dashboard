import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# 1. Configuration de la page (DOIT être la première commande Streamlit)
st.set_page_config(page_title="Arkeos Dashboard", layout="wide")

# 2. Chargement du fichier de configuration
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# 3. Initialisation de l'authentificateur
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# 4. Affichage du formulaire de connexion
# La nouvelle version de la bibliothèque gère tout via le session_state
authenticator.login(location='main')

# 5. Vérification du statut d'authentification
if st.session_state["authentication_status"]:
    # --- UTILISATEUR CONNECTÉ ---
    
    # Bouton de déconnexion dans la barre latérale
    authenticator.logout('Déconnexion', 'sidebar')
    
    st.sidebar.write(f"Utilisateur : {st.session_state['name']}")
    
    # --- ICI : TON CODE DE DASHBOARD ACTUEL ---
    # (Tes titres, graphiques, filtres, etc.)
    st.title("🏗️ Arkeos Technical Support Dashboard")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Interventions", "2,700")
    col2.metric("RDR % (7j)", "26.7%")
    col3.metric("FTTR %", "73.3%")

    st.success("Accès sécurisé accordé.")

elif st.session_state["authentication_status"] is False:
    st.error('Identifiant ou mot de passe incorrect')

elif st.session_state["authentication_status"] is None:
    st.warning('Veuillez entrer votre nom d\'utilisateur et votre mot de passe')
