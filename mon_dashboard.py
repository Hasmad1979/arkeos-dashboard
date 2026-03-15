import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="Arkeos Technical Dashboard", layout="wide", page_icon="🏗️")

# 2. BASE DE DONNÉES DES UTILISATEURS
# Tu peux ajouter d'autres comptes ici : "identifiant": "mot de passe"
USERS = {
    "admin": "Arkeos2026",
    "technicien1": "ArkeosTech01",
    "manager": "ArkeosManager"
}

# 3. FONCTION DE CONNEXION
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    # Formulaire de Login
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

# 4. EXÉCUTION DU DASHBOARD SI CONNECTÉ
if check_password():
    
    # --- BARRE LATÉRALE (SIDEBAR) ---
    st.sidebar.image("https://www.streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.png", width=150) # Optionnel
    st.sidebar.write(f"👤 Utilisateur : **{st.session_state['user_connected']}**")
    
    if st.sidebar.button("Se déconnecter"):
        st.session_state["authenticated"] = False
        st.rerun()

    # --- CHARGEMENT DES DONNÉES ---
    @st.cache_data # Pour que le site soit plus rapide
    def load_data():
        try:
            # On détecte le séparateur automatiquement (, ou ;)
            data = pd.read_csv('data_dynamics_brute.csv.csv', sep=None, engine='python')
            data.columns = data.columns.str.strip() # Nettoyage des noms de colonnes
            return data
        except Exception as e:
            st.error(f"Erreur de chargement du fichier CSV : {e}")
            return None

    df_raw = load_data()

    if df_raw is not None:
        # --- FILTRES DANS LA SIDEBAR ---
        st.sidebar.header("🔍 Paramètres")
        
        # Filtre Année
        if 'Année' in df_raw.columns:
            years = sorted(df_raw['Année'].unique())
            selected_years = st.sidebar.multiselect("Année", options=years, default=years)
        else:
            selected_years = []

        # Filtre Mois
        if 'Mois' in df_raw.columns:
            months = df_raw['Mois'].unique()
            selected_months = st.sidebar.multiselect("Mois", options=months, default=months)
        else:
            selected_months = []

        # Application des filtres
        df = df_raw.copy()
        if selected_years:
            df = df[df['Année'].isin(selected_years)]
        if selected_months:
            df = df[df['Mois'].isin(selected_months)]

        # --- CORPS DU DASHBOARD ---
        st.title("🏗️ Arkeos Technical Support Dashboard")
        
        # Ligne 1 : Les KPIs
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Interventions", f"{len(df):,}")
        with col2:
            st.metric("RDR % (7j)", "26.7%", delta="-1.2%")
        with col3:
            st.metric("FTTR %", "73.3%", delta="2.4%")

        st.markdown("---")

        # Ligne 2 : Les Graphiques
        st.subheader("📊 Analyse des Interventions")
        
        c1, c2 = st.columns(2)

        with c1:
            if 'Technicien' in df.columns:
                tech_data = df['Technicien'].value_counts().reset_index().head(10)
                tech_data.columns = ['Nom', 'Nombre']
                fig_tech = px.bar(tech_data, x='Nom', y='Nombre', 
                                 title="Top 10 Techniciens",
                                 color='Nombre', color_continuous_scale='Viridis')
                st.plotly_chart(fig_tech, use_container_width=True)

        with c2:
            if 'Mois' in df.columns:
                # Ordre des mois pour le graphique
                order = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 
                         'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
                monthly_data = df['Mois'].value_counts().reindex(order).reset_index()
                monthly_data.columns = ['Mois', 'Total']
                fig_evo = px.line(monthly_data, x='Mois', y='Total', 
                                 title="Évolution Mensuelle", markers=True)
                st.plotly_chart(fig_evo, use_container_width=True)

        # Ligne 3 : Alertes et Infos
        st.markdown("---")
        st.subheader("💡 Good To Know")
        
        inf1, inf2 = st.columns(2)
        with inf1:
            st.info("🚨 **Alerte Priorité Machine :** La machine ZBX2863 nécessite une expertise (15 répétitions).")
        with inf2:
            st.warning("🏢 **Satisfaction Client :** Le compte DISLOG GROUP est le plus impacté cette période.")

    else:
        st.warning("Veuillez vérifier que le fichier 'data_dynamics_brute.csv.csv' est présent sur votre GitHub.")
