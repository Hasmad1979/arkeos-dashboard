import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Arkeos Dashboard", layout="wide")

# 1. CONNEXION (Simplifiée pour éviter les erreurs)
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
            st.error("Erreur d'identifiants")
    st.stop()

# 2. CHARGEMENT ET DIAGNOSTIC
try:
    df = pd.read_csv('data_dynamics_brute.csv.csv', sep=None, engine='python')
    # Nettoyage automatique des noms de colonnes
    df.columns = [str(c).strip() for c in df.columns]
    
    st.sidebar.write("### 🔍 Diagnostic Colonnes")
    st.sidebar.write(list(df.columns)) # Affiche la liste réelle des colonnes
    
    # 3. FILTRES INTELLIGENTS
    st.sidebar.header("Paramètres")
    
    # On cherche la colonne qui ressemble à "Année"
    col_cible = None
    for c in df.columns:
        if "ann" in c.lower() or "year" in c.lower():
            col_cible = c
            break
            
    if col_cible:
        options = sorted(df[col_cible].dropna().unique().tolist())
        sel = st.sidebar.multiselect(f"Filtrer {col_cible}", options, default=options)
        df = df[df[col_cible].isin(sel)]
    else:
        st.sidebar.error("❌ Aucune colonne 'Année' trouvée. Vérifie le diagnostic ci-dessus.")

    # 4. AFFICHAGE
    st.title("🏗️ Arkeos Technical Support Dashboard")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Interventions", f"{len(df):,}")
    c2.metric("RDR %", "26.7%")
    c3.metric("FTTR %", "73.3%")

    st.markdown("---")
    
    # GRAPHIQUE AUTOMATIQUE (Prend la première colonne de texte trouvée)
    st.subheader("📊 Analyse des Interventions")
    col_txt = df.select_dtypes(include=['object']).columns
    if len(col_txt) > 0:
        fig = px.bar(df[col_txt[0]].value_counts().head(10), title=f"Top 10 par {col_txt[0]}")
        st.plotly_chart(fig, use_container_width=True)

    st.info("💡 Alerte : La machine ZBX2863 nécessite une expertise.")

except Exception as e:
    st.error(f"Erreur : {e}")
