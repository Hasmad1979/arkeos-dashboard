import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuration (Toujours en premier)
st.set_page_config(page_title="Arkeos Dashboard", layout="wide")

# 2. Gestion des comptes
USERS = {
    "admin": "Arkeos2026",
    "technicien1": "ArkeosTech01"
}

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    st.title("🔐 Connexion Arkeos")
    user = st.text_input("Identifiant")
    pw = st.text_input("Mot de passe", type="password")
    
    if st.button("Se connecter"):
        if user in USERS and pw == USERS[user]:
            st.session_state["authenticated"] = True
            st.session_state["user_connected"] = user
            st.rerun()
        else:
            st.error("Identifiant ou mot de passe incorrect")
    return False

# 3. Affichage après connexion
if check_password():
    # Barre latérale
    st.sidebar.write(f"Utilisateur : **{st.session_state['user_connected']}**")
    if st.sidebar.button("Se déconnecter"):
        st.session_state["authenticated"] = False
        st.rerun()

    # --- CHARGEMENT DES DONNÉES ---
    # Remplace par le nom exact de ton fichier CSV
    try:
        df = pd.read_csv('data_dynamics_brute.csv.csv', sep=None, engine='python')
        df.columns = df.columns.str.strip()
    except Exception as e:
        st.error(f"Erreur de données : {e}")
        st.stop()

    # --- TES FILTRES (SideBar) ---
    st.sidebar.header("🔍 Paramètres")
    if 'Année' in df.columns:
        list_annees = sorted(df['Année'].unique())
        annee_selected = st.sidebar.multiselect("Année", options=list_annees, default=list_annees)
        df = df[df['Année'].isin(annee_selected)]

    # --- TON DASHBOARD ---
    st.title("🏗️ Arkeos Technical Support Dashboard")
    
    # Tes métriques
    col1, col2, col3 = st.columns(3)
    col1.metric("Interventions", f"{len(df):,}")
    col2.metric("RDR % (7j)", "26.7%")
    col3.metric("FTTR %", "73.3%")

    # --- TES GRAPHIQUES ---
    st.subheader("📊 Analyse des Interventions")
    
    if 'Technicien' in df.columns:
        fig = px.bar(df['Technicien'].value_counts().reset_index(), 
                     x='Technicien', y='count', title="Top Techniciens")
        st.plotly_chart(fig, use_container_width=True)

    # --- TES ALERTES ---
    st.info("💡 **Alerte :** La machine ZBX2863 nécessite une expertise.")
