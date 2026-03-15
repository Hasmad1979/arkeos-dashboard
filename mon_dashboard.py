import streamlit as st

st.set_page_config(page_title="Arkeos Tech Support", layout="wide")

# Fonction de vérification simple
def check_password():
    def password_entered():
        if st.session_state["username"] == "admin" and st.session_state["password"] == "Arkeos2026":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # On ne garde pas le mot de passe en mémoire
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Affichage du formulaire de login
        st.title("Connexion Arkeos")
        st.text_input("Identifiant", key="username")
        st.text_input("Mot de passe", type="password", key="password")
        st.button("Se connecter", on_click=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        # Mauvais mot de passe
        st.text_input("Identifiant", key="username")
        st.text_input("Mot de passe", type="password", key="password")
        st.button("Se connecter", on_click=password_entered)
        st.error("😕 Identifiant ou mot de passe inconnu")
        return False
    else:
        # Mot de passe correct
        return True

if check_password():
    # --- TON DASHBOARD COMMENCE ICI ---
    st.sidebar.button("Se déconnecter", on_click=lambda: st.session_state.clear())
    
    st.title("🏗️ Arkeos Technical Support Dashboard")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Interventions", "2,700")
    col2.metric("RDR % (7j)", "26.7%")
    col3.metric("FTTR %", "73.3%")
    
    st.success("Accès sécurisé validé.")
    # Ajoute ici le reste de tes graphiques
