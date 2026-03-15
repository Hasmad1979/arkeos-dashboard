import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURATION
st.set_page_config(page_title="Arkeos Technical Dashboard", layout="wide", page_icon="🏗️")

# 2. COMPTES UTILISATEURS
USERS = {"admin": "Arkeos2026"}

# 3. SÉCURITÉ
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
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
    st.stop() # Arrête l'exécution ici si pas connecté

# 4. AFFICHAGE APRÈS CONNEXION
st.sidebar.write(f"👤 : **{st.session_state['user_connected']}**")
if st.sidebar.button("Se déconnecter"):
    st.session_state.clear()
    st.rerun()

# 5. CHARGEMENT ET NETTOYAGE DES DONNÉES
try:
    # Lecture flexible (détecte , ou ;)
    df = pd.read_csv('data_dynamics_brute.csv.csv', sep=None, engine='python')
    # Nettoyage CRITIQUE des colonnes (enlève espaces et caractères invisibles)
    df.columns = [str(c).strip() for c in df.columns]
    
    # --- FILTRES DYNAMIQUES ---
    st.sidebar.header("🔍 Paramètres")
    
    # On cherche une colonne qui contient "Année" (insensible à la casse)
    col_annee = next((c for c in df.columns if "ann" in c.lower()), None)
    
    if col_annee:
        annees = sorted(df[col_annee].dropna().unique().tolist())
        sel_annees = st.sidebar.multiselect("Filtrer par Année", options=annees, default=annees)
        df = df[df[col_annee].isin(sel_annees)]
    else:
        st.sidebar.warning("Colonne 'Année' non détectée.")

    # --- AFFICHAGE DU DASHBOARD ---
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
        col_tech = next((c for c in df.columns if "tech" in c.lower()), None)
        if col_tech:
            fig_tech = px.bar(df[col_tech].value_counts().head(10), 
                             title="Top 10 Techniciens",
                             labels={'value': 'Interventions', 'index': 'Technicien'})
            st.plotly_chart(fig_tech, use_container_width=True)
    
    with g2:
        col_mois = next((c for c in df.columns if "mois" in c.lower()), None)
        if col_mois:
            fig_mois = px.pie(df, names=col_mois, title="Répartition par Mois", hole=0.4)
            st.plotly_chart(fig_mois, use_container_width=True)

    st.info("💡 **Alerte :** La machine ZBX2863 nécessite une expertise.")

except Exception as e:
    st.error(f"Erreur technique : {e}")
    st.info("Conseil : Vérifiez que le fichier 'data_dynamics_brute.csv.csv' est bien sur GitHub.")
