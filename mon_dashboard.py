import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURATION
st.set_page_config(page_title="Arkeos Dashboard", layout="wide")

# 2. CONNEXION
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.title("🔐 Connexion Arkeos")
    u = st.text_input("Identifiant")
    p = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        if u == "admin" and p == "Arkeos2026":
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("Identifiant ou mot de passe incorrect")
    st.stop()

# 3. CHARGEMENT
try:
    df = pd.read_csv('data_dynamics_brute.csv.csv', sep=None, engine='python')
    df.columns = [str(c).strip() for c in df.columns]

    # Conversion de la colonne Date pour faire des filtres
    if "Date de création" in df.columns:
        df["Date de création"] = pd.to_datetime(df["Date de création"], errors='coerce')
        df["Année"] = df["Date de création"].dt.year.fillna(0).astype(int)

    # --- SIDEBAR : FILTRES ---
    st.sidebar.write(f"👤 : **admin**")
    if st.sidebar.button("Se déconnecter"):
        st.session_state.clear()
        st.rerun()

    st.sidebar.header("Paramètres")
    
    # Filtre Année (basé sur la date de création qu'on vient d'extraire)
    if "Année" in df.columns:
        annees = sorted([a for a in df["Année"].unique() if a > 0])
        sel_annees = st.sidebar.multiselect("Filtrer par Année", options=annees, default=annees)
        df = df[df["Année"].isin(sel_annees)]

    # Filtre Propriétaire (Tes techniciens)
    if "Propriétaire" in df.columns:
        pros = sorted(df["Propriétaire"].dropna().unique().tolist())
        sel_pros = st.sidebar.multiselect("Filtrer par Propriétaire", options=pros, default=pros[:5]) # Top 5 par défaut
        df = df[df["Propriétaire"].isin(sel_pros)]

    # --- AFFICHAGE ---
    st.title("🏗️ Arkeos Technical Support Dashboard")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Interventions", f"{len(df):,}")
    c2.metric("RDR %", "26.7%")
    c3.metric("FTTR %", "73.3%")

    st.markdown("---")
    
    # GRAPHIQUES
    st.subheader("📊 Analyse des Interventions")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        if "Propriétaire" in df.columns:
            fig_prop = px.bar(df["Propriétaire"].value_counts().head(10), 
                             title="Top 10 par Propriétaire",
                             labels={'value': 'Nombre', 'index': 'Propriétaire'},
                             color_discrete_sequence=['#007BFF'])
            st.plotly_chart(fig_prop, use_container_width=True)

    with col_b:
        if "Type d'incident principal" in df.columns:
            fig_type = px.pie(df, names="Type d'incident principal", 
                             title="Types d'Incidents", hole=0.4)
            st.plotly_chart(fig_type, use_container_width=True)

    st.info("💡 Alerte : La machine ZBX2863 nécessite une expertise.")

except Exception as e:
    st.error(f"Erreur technique : {e}")
