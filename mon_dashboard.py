import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURATION
st.set_page_config(page_title="Arkeos Technical Dashboard", layout="wide", page_icon="🏗️")

# 2. COMPTES UTILISATEURS
USERS = {
    "admin": "Arkeos2026",
    "technicien1": "ArkeosTech01"
}

# 3. FONCTION DE SÉCURITÉ
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    st.markdown("<br><br>", unsafe_allow_html=True)
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.title("🔐 Connexion Arkeos")
        user = st.text_input("Identifiant")
        pw = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter", use_container_width=True):
            if user in USERS and pw == USERS[user]:
                st.session_state["authenticated"] = True
                st.session_state["user_connected"] = user
                st.rerun()
            else:
                st.error("❌ Identifiant ou mot de passe incorrect")
    return False

# 4. AFFICHAGE DU DASHBOARD
if check_password():
    # Déconnexion sidebar
    st.sidebar.write(f"👤 Utilisateur : **{st.session_state['user_connected']}**")
    if st.sidebar.button("Se déconnecter"):
        st.session_state.clear()
        st.rerun()

    # CHARGEMENT DES DONNÉES
    @st.cache_data
    def load_data():
        try:
            # Charge le fichier en détectant automatiquement le séparateur (, ou ;)
            data = pd.read_csv('data_dynamics_brute.csv.csv', sep=None, engine='python')
            data.columns = data.columns.str.strip() # Enlève les espaces dans les noms de colonnes
            return data
        except Exception as e:
            st.error(f"Erreur de fichier : {e}")
            return None

    df_raw = load_data()

    if df_raw is not None:
        # --- BARRE LATERALE : FILTRES ---
        st.sidebar.header("🔍 Paramètres")
        
        # Filtre Année (si la colonne existe)
        col_annee = 'Année' if 'Année' in df_raw.columns else (df_raw.columns[0] if len(df_raw.columns)>0 else None)
        if col_annee:
            annees = sorted(df_raw[col_annee].unique())
            sel_annees = st.sidebar.multiselect("Sélectionner l'Année", options=annees, default=annees)
            df = df_raw[df_raw[col_annee].isin(sel_annees)]
        else:
            df = df_raw

        # --- CORPS DU DASHBOARD ---
        st.title("🏗️ Arkeos Technical Support Dashboard")
        
        # KPIs
        c1, c2, c3 = st.columns(3)
        c1.metric("Interventions", f"{len(df):,}")
        c2.metric("RDR % (7j)", "26.7%", delta="-1.2%")
        c3.metric("FTTR %", "73.3%", delta="2.4%")

        st.markdown("---")

        # GRAPHIQUES
        st.subheader("📊 Analyse des Interventions")
        
        g1, g2 = st.columns(2)
        
        with g1:
            # Graphique par Technicien
            col_tech = 'Technicien' if 'Technicien' in df.columns else None
            if col_tech:
                fig_tech = px.bar(df[col_tech].value_counts().head(10), 
                                 title="Top 10 Techniciens",
                                 labels={'value': 'Nombre', 'index': 'Nom'},
                                 color_discrete_sequence=['#00CC96'])
                st.plotly_chart(fig_tech, use_container_width=True)
            else:
                st.warning("Colonne 'Technicien' non trouvée pour le graphique.")

        with g2:
            # Graphique par Mois
            col_mois = 'Mois' if 'Mois' in df.columns else None
            if col_mois:
                fig_mois = px.pie(df, names=col_mois, title="Répartition par Mois", hole=0.4)
                st.plotly_chart(fig_mois, use_container_width=True)

        # ALERTES
        st.markdown("---")
        st.subheader("💡 Good To Know")
        a1, a2 = st.columns(2)
        with a1:
            st.info("🚨 **Alerte Priorité Machine :** La machine ZBX2863 nécessite une expertise.")
        with a2:
            st.warning("🏢 **Satisfaction Client :** Le compte DISLOG GROUP est le plus impacté.")
