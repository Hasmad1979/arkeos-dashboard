import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="Arkeos Tech Support", layout="wide", page_icon="🏗️")

# 2. SYSTÈME DE SÉCURITÉ (Simple et efficace)
def check_password():
    """Retourne True si l'utilisateur a saisi le bon mot de passe."""
    def password_entered():
        # ICI : Tu peux changer l'identifiant et le mot de passe
        if st.session_state["username"] == "admin" and st.session_state["password"] == "Arkeos2026":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Supprime le MDP de la mémoire
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Formulaire de première connexion
        st.title("🔐 Accès Restreint - Arkeos")
        st.text_input("Identifiant", key="username")
        st.text_input("Mot de passe", type="password", key="password")
        st.button("Se connecter", on_click=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        # Erreur si mauvais identifiants
        st.title("🔐 Accès Restreint - Arkeos")
        st.text_input("Identifiant", key="username")
        st.text_input("Mot de passe", type="password", key="password")
        st.button("Se connecter", on_click=password_entered)
        st.error("😕 Identifiant ou mot de passe incorrect.")
        return False
    else:
        # Accès autorisé
        return True

# 3. SI L'UTILISATEUR EST CONNECTÉ, ON AFFICHE LE DASHBOARD
if check_password():
    
    # Bouton de déconnexion dans la sidebar
    if st.sidebar.button("Se déconnecter"):
        st.session_state.clear()
        st.rerun()

    # --- CHARGEMENT DES DONNÉES ---
    try:
        # Le nom exact de ton fichier sur GitHub
        df = pd.read_csv('data_dynamics_brute.csv.csv', sep=None, engine='python')
        df.columns = df.columns.str.strip() # Nettoie les noms de colonnes
    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {e}")
        st.stop()

    # --- SIDEBAR : FILTRES ---
    st.sidebar.header("🔍 Paramètres")
    
    # Filtre Année
    list_annees = sorted(df['Année'].unique()) if 'Année' in df.columns else []
    annee_selected = st.sidebar.multiselect("Année", options=list_annees, default=list_annees)

    # Filtre Mois
    list_mois = df['Mois'].unique() if 'Mois' in df.columns else []
    mois_selected = st.sidebar.multiselect("Mois", options=list_mois, default=list_mois)

    # --- FILTRAGE DES DATA ---
    df_selection = df.copy()
    if annee_selected:
        df_selection = df_selection[df_selection['Année'].isin(annee_selected)]
    if mois_selected:
        df_selection = df_selection[df_selection['Mois'].isin(mois_selected)]

    # --- AFFICHAGE DU DASHBOARD ---
    st.title("🏗️ Arkeos Technical Support Dashboard")
    
    # Métriques principales
    col1, col2, col3 = st.columns(3)
    col1.metric("Interventions", f"{len(df_selection):,}")
    col2.metric("RDR % (7j)", "26.7%")
    col3.metric("FTTR %", "73.3%")

    st.markdown("---")

    # Section Analyses
    st.subheader("📊 Analyses et Graphiques")
    
    if 'Technicien' in df_selection.columns:
        fig = px.bar(df_selection['Technicien'].value_counts().reset_index(), 
                     x='Technicien', y='count', 
                     title="Interventions par Technicien",
                     color_discrete_sequence=['#636EFA'])
        st.plotly_chart(fig, use_container_width=True)

    # Section Alertes
    st.subheader("💡 Good To Know")
    c1, c2 = st.columns(2)
    with c1:
        st.info("🚨 **Alerte Priorité Machine :** La machine ZBX2863 nécessite une expertise (15 repeats).")
    with c2:
        st.warning("🏢 **Satisfaction Client :** Le compte DISLOG GROUP est le plus impacté ce mois-ci.")
