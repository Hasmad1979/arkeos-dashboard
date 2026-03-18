import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io

# 1. Config de base
st.set_page_config(page_title="Arkeos AI Dashboard", layout="wide")

# 2. Sécurité
USERS = {"admin": "Arkeos2026", "technicien": "ArkeosTech2026"}

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if st.session_state["authenticated"]:
        return True

    st.title("🔐 Accès Arkeos")
    user = st.text_input("Identifiant")
    pw = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        if user in USERS and pw == USERS[user]:
            st.session_state["authenticated"] = True
            st.session_state["user_connected"] = user
            st.rerun()
        else:
            st.error("❌ Identifiant ou mot de passe incorrect")
    return False

# 3. Application
if check_password():
    st.sidebar.write(f"👤 Connecté : {st.session_state['user_connected']}")
    if st.sidebar.button("Déconnexion"):
        st.session_state["authenticated"] = False
        st.rerun()

    st.title("📠 Arkeos Dashboard")
    
    # Chargement des données
    file_path = "data_dynamics_brute.csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path, sep=None, engine='python')
        st.success(f"Données chargées : {len(df)} lignes.")
        st.write(df.head()) # Affiche les 5 premières lignes pour vérifier
    else:
        st.error(f"Fichier {file_path} introuvable sur GitHub.")
