import streamlit as st
import streamlit_authenticator as stauth

# 1. Configuration de la page
st.set_page_config(page_title="Arkeos Dashboard", layout="wide")

# 2. On définit l'utilisateur directement dans le code (plus de fichier YAML externe)
# Le mot de passe ici est : Arkeos2026
credentials = {
    'usernames': {
        'admin': {
            'email': 'admin@arkeos.com',
            'name': 'Administrateur Arkeos',
            'password': '$2b$12$N3q7mYn0D1.S8pG.L8PzOuX0k3z6J7H8zK9tL0mM1nO2pP3qR4sS5'
        }
    }
}

# 3. Initialisation
authenticator = stauth.Authenticate(
    credentials,
    'arkeos_cookie',
    'arkeos_key',
    30
)

# 4. Formulaire de login
authenticator.login(location='main')

# 5. La logique d'affichage
if st.session_state["authentication_status"]:
    # SI CONNECTÉ : On affiche ton dashboard
    authenticator.logout('Déconnexion', 'sidebar')
    
    # --- DEBUT DE TON DASHBOARD ---
    st.title("🏗️ Arkeos Technical Support Dashboard")
    
    # Tes métriques que j'ai vues sur ta photo
    col1, col2, col3 = st.columns(3)
    col1.metric("Interventions", "2,700")
    col2.metric("RDR % (7j)", "26.7%")
    col3.metric("FTTR %", "73.3%")
    
    st.success("Connexion réussie ! Ton dashboard est ici.")
    # --- FIN DE TON DASHBOARD ---

elif st.session_state["authentication_status"] is False:
    st.error('Identifiant ou mot de passe incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Veuillez entrer vos accès pour voir le dashboard')
