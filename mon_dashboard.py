import streamlit as st

# 1. CONFIGURATION DES COMPTES
# Tu peux ajouter autant de comptes que tu veux ici
USERS = {
    "admin": "Arkeos2026",
    "technicien1": "ArkeosTech01",
    "manager": "ArkeosManager",
    "invite": "ArkeosGuest"
}

def check_password():
    """Retourne True si l'utilisateur est connecté avec un compte valide."""
    
    # Initialisation de l'état de connexion
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["user_connected"] = None

    # Si déjà connecté, on ne réaffiche pas le formulaire
    if st.session_state["authenticated"]:
        return True

    # --- ÉCRAN DE CONNEXION ---
    st.title("🔐 Connexion Arkeos")
    
    username = st.text_input("Identifiant")
    password = st.text_input("Mot de passe", type="password")
    
    if st.button("Se connecter"):
        # On vérifie si l'identifiant existe et si le mot de passe correspond
        if username in USERS and password == USERS[username]:
            st.session_state["authenticated"] = True
            st.session_state["user_connected"] = username
            st.success(f"Bienvenue {username} !")
            st.rerun() # Redirige vers la page principale
        else:
            st.error("❌ Identifiant ou mot de passe incorrect")
    
    return False

# 2. LOGIQUE D'AFFICHAGE
if check_password():
    # --- ICI COMMENCE TA PAGE PRINCIPALE (DASHBOARD) ---
    
    # Bouton de déconnexion dans la barre latérale
    st.sidebar.write(f"Utilisateur : **{st.session_state['user_connected']}**")
    if st.sidebar.button("Se déconnecter"):
        st.session_state["authenticated"] = False
        st.session_state["user_connected"] = None
        st.rerun()

    # --- TON CODE DE DASHBOARD (REMETS TES FILTRES ET GRAPHIQUES ICI) ---
    st.title("🏗️ Arkeos Technical Support Dashboard")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Interventions", "2,700")
    col2.metric("RDR % (7j)", "26.7%")
    col3.metric("FTTR %", "73.3%")

    st.success(f"Accès accordé au compte : {st.session_state['user_connected']}")
    
    # Tu peux même personnaliser l'affichage selon le compte
    if st.session_state["user_connected"] == "admin":
        st.info("Mode Administrateur activé : Accès à tous les réglages.")
