import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Arkeos Tech Support", layout="wide")

# --- 1. SYSTÈME DE LOGIN (LA CLÉ) ---
def check_password():
    def password_entered():
        if st.session_state["username"] == "admin" and st.session_state["password"] == "Arkeos2026":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("Connexion Arkeos")
        st.text_input("Identifiant", key="username")
        st.text_input("Mot de passe", type="password", key="password")
        st.button("Se connecter", on_click=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Identifiant", key="username")
        st.text_input("Mot de passe", type="password", key="password")
        st.button("Se connecter", on_click=password_entered)
        st.error("😕 Identifiant ou mot de passe inconnu")
        return False
    return True

# --- 2. SI CONNECTÉ, ON RECONSTRUIT LE DASHBOARD ---
if check_password():
    st.sidebar.button("Se déconnecter", on_click=lambda: st.session_state.clear())

    # CHARGEMENT DES DONNÉES
    # Note : d'après tes fichiers, le nom est data_dynamics_brute.csv.csv
    try:
        df = pd.read_csv('data_dynamics_brute.csv.csv')
    except:
        st.error("Erreur : Le fichier de données est introuvable.")
        st.stop()

    # --- 3. LES FILTRES (SIDEBAR) ---
    st.sidebar.header("🔍 Paramètres")
    
    # Filtre Année
    list_annees = sorted(df['Année'].unique())
    annee_selected = st.sidebar.multiselect("Année", options=list_annees, default=list_annees)

    # Filtre Mois
    list_mois = df['Mois'].unique()
    mois_selected = st.sidebar.multiselect("Mois", options=list_mois, default=list_mois)

    # Filtre Technicien
    list_tech = ["Tous"] + list(df['Technicien'].unique())
    tech_selected = st.sidebar.selectbox("Technicien", options=list_tech)

    # APPLICATION DES FILTRES
    df_selection = df[(df['Année'].isin(annee_selected)) & (df['Mois'].isin(mois_selected))]
    if tech_selected != "Tous":
        df_selection = df_selection[df_selection['Technicien'] == tech_selected]

    # --- 4. AFFICHAGE DES INDICATEURS ---
    st.title("🏗️ Arkeos Technical Support Dashboard")
    
    col1, col2, col3 = st.columns(3)
    # Calcul dynamique basé sur tes données filtrées
    total_interv = len(df_selection)
    col1.metric("Interventions", f"{total_interv:,}")
    col2.metric("RDR % (7j)", "26.7%") # Tu peux remplacer par ton calcul
    col3.metric("FTTR %", "73.3%") # Tu peux remplacer par ton calcul

    # --- 5. ZONE DE GRAPHIQUES ---
    st.subheader("Analyses Graphiques")
    
    # Exemple de graphique (Répartition par Technicien)
    fig_tech = px.bar(df_selection.groupby('Technicien').size().reset_index(name='Nombre'), 
                     x='Technicien', y='Nombre', title="Interventions par Technicien")
    st.plotly_chart(fig_tech, use_container_width=True)

    # --- 6. ALERTES ---
    st.subheader("💡 Good To Know")
    col_a, col_b = st.columns(2)
    with col_a:
        st.info("🚨 **Alerte Priorité Machine :** La machine ZBX2863 nécessite une expertise.")
    with col_b:
        st.warning("🏢 **Alerte Satisfaction Client :** Le compte DISLOG GROUP est le plus impacté.")
