import streamlit as st
import streamlit_authenticator as stauth

st.set_page_config(page_title="Arkeos Tech Support", layout="wide")

# On définit les utilisateurs directement ici
# Hash pour 'Arkeos2026'
credentials = {
    'usernames': {
        'admin': {
            'email': 'admin@arkeos.com',
            'name': 'Administrateur Arkeos',
            'password': '$2b$12$N3q7mYn0D1.S8pG.L8PzOuX0k3z6J7H8zK9tL0mM1nO2pP3qR4sS5'
        }
    }
}

# Initialisation
authenticator = stauth.Authenticate(
    credentials,
    'arkeos_auth_cookie',
    'arkeos_key',
    30
)

# Affichage Login
authenticator.login(location='main')

if st.session_state["authentication_status"]:
    authenticator.logout('Déconnexion', 'sidebar')
    st.title("Arkeos Technical Support Dashboard")
    st.success("Enfin connecté !")
    # COLLE LA SUITE DE TON CODE ICI (Graphes, metrics, etc.)

elif st.session_state["authentication_status"] is False:
    st.error('Identifiant ou mot de passe incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Veuillez entrer vos accès')
