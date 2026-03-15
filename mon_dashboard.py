import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURATION
st.set_page_config(page_title="Arkeos Technical Dashboard", layout="wide", page_icon="🏗️")

# 2. COMPTES UTILISATEURS
USERS = {"admin": "Arkeos2026"}

# 3. SÉCURITÉ
def check_password():
    if st.session_state.get("authenticated"):
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

if check_password():
    # Sidebar
    st.sidebar.write(f"👤 : **{st.session_state['user_connected']}**")
    if st.sidebar.button("Se déconnecter"):
        st.session_state.clear()
        st.rerun()

    # 4. CHARGEMENT DES DONNÉES
    try:
        df = pd.read_csv('data_dynamics_brute.csv.csv', sep=None, engine='python')
        df.columns = df.columns.str.strip()
        
        # --- FILTRES (SIDEBAR) ---
        st.sidebar.header("🔍 Paramètres")
        
        # On cherche la colonne 'Année' ou on prend la première disponible
        col_annee = 'Année' if 'Année' in df.columns else None
        
        if col_annee:
            annees = sorted(df[col_annee].unique().tolist())
            sel_annees = st.sidebar.multiselect("Année", options=annees, default=annees)
            df = df[df[col_annee].isin(sel_annees)]
        
        # --- CORPS DU DASHBOARD ---
        st.title("🏗️ Arkeos Technical Support Dashboard")
        
        # KPIs
        c1, c2, c3 = st.columns(3)
        c1.metric("Interventions", f"{len(df):,}")
        c2.metric("RDR % (7j)", "26.7%")
        c3.metric("FTTR %", "73.3%")

        st.markdown("---")

        # GRAPHIQUES
        st.subheader("📊 Analyse des Interventions")
        g1, g2 = st.columns(2)
        
        with g1:
            if 'Technicien' in df.columns:
                fig_tech = px.bar(df['Technicien'].value_counts().head(10), title="Top 10 Techniciens")
                st.plotly_chart(fig_tech, use_container_width=True)
        
        with g2:
            if 'Mois' in df.columns:
                fig_mois = px.pie(df, names='Mois', title="Répartition mensuelle", hole=0.4)
                st.plotly_chart(fig_mois, use_container_width=True)

        st.info("💡 **Alerte :** La machine ZBX2863 nécessite une expertise.")

    except Exception as e:
        st.error(f"Erreur de chargement : Vérifiez que le fichier CSV est présent. (Détail : {e})")
