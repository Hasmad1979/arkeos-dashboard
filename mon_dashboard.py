import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Arkeos Tech Support", layout="wide")

# --- 1. SYSTÈME DE LOGIN ---
def check_password():
    def password_entered():
        if st.session_state["username"] == "admin" and st.session_state["password"] == "Arkeos2026":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 Connexion Arkeos")
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

# --- 2. SI CONNECTÉ ---
if check_password():
    st.sidebar.button("Se déconnecter", on_click=lambda: st.session_state.clear())

    # CHARGEMENT DES DONNÉES AVEC DÉTECTION DE SÉPARATEUR
    try:
        # On essaie d'abord avec la virgule, puis le point-virgule si ça rate
        df = pd.read_csv('data_dynamics_brute.csv.csv', sep=None, engine='python')
    except Exception as e:
        st.error(f"Erreur de fichier : {e}")
        st.stop()

    # Nettoyage des noms de colonnes (enlève les espaces invisibles)
    df.columns = df.columns.str.strip()

    # --- 3. LES FILTRES (SIDEBAR) ---
    st.sidebar.header("🔍 Paramètres")
    
    # Vérification si la colonne 'Année' existe vraiment
    if 'Année' in df.columns:
        list_annees = sorted(df['Année'].unique())
        annee_selected = st.sidebar.multiselect("Année", options=list_annees, default=list_annees)
    else:
        st.warning(f"Attention: Colonne 'Année' introuvable. Colonnes dispos : {list(df.columns)}")
        annee_selected = []

    if 'Mois' in df.columns:
        list_mois = df['Mois'].unique()
        mois_selected = st.sidebar.multiselect("Mois", options=list_mois, default=list_mois)
    else:
        mois_selected = []

    # --- 4. AFFICHAGE DES INDICATEURS ---
    st.title("🏗️ Arkeos Technical Support Dashboard")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Interventions", f"{len(df):,}")
    col2.metric("RDR % (7j)", "26.7%")
    col3.metric("FTTR %", "73.3%")

    # --- 5. GRAPHIQUE TEST ---
    st.subheader("Analyses Graphiques")
    if 'Technicien' in df.columns:
        fig = px.bar(df['Technicien'].value_counts().reset_index(), 
                     x='Technicien', y='count', title="Interventions par Technicien",
                     labels={'count': 'Nombre', 'Technicien': 'Nom'})
        st.plotly_chart(fig, use_container_width=True)

    # --- 6. ALERTES ---
    st.subheader("💡 Good To Know")
    st.info("🚨 **Alerte Priorité Machine :** La machine ZBX2863 nécessite une expertise.")
