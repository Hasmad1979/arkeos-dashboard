import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="Arkeos Technical Dashboard", layout="wide")

@st.cache_data
def load_data():
    f = "data_dynamics_brute.csv.csv.csv"
    if not os.path.exists(f): return "Fichier introuvable sur GitHub"
    try:
        # Lecture avec détection automatique du séparateur
        df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapping automatique des colonnes vitales
        m = {
            "Numéro de l'incident": "ID", "Incident Number": "ID",
            "Actifs du client": "SN", "Customer Asset": "SN",
            "Owner": "Tech", "Propriétaire": "Tech",
            "Créé le": "Date", "Created On": "Date"
        }
        df = df.rename(columns=m)

        # Recherche de secours si les noms ne correspondent pas exactement
        for c in df.columns:
            if 'Date' not in df.columns and any(x in c.lower() for x in ['date', 'créé', 'created']):
                df = df.rename(columns={c: 'Date'})
            if 'SN' not in df.columns and any(x in c.lower() for x in ['actif', 'asset', 'serial', 'machine']):
                df = df.rename(columns={c: 'SN'})
            if 'Tech' not in df.columns and any(x in c.lower() for x in ['owner', 'propriétaire', 'technicien', 'agent']):
                df = df.rename(columns={c: 'Tech'})

        # Nettoyage et conversion
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
        if 'Tech' not in df.columns: df['Tech'] = "Non spécifié"
        
        # Conversion forcée en texte pour le filtre Technicien
        df['Tech'] = df['Tech'].astype(str).replace('nan', 'Non spécifié')

        # Calcul RDR (Repeats sous 22 jours ouvrés)
        df['P'] = df.groupby('SN')['Date'].shift(1)
        def calc_rdr(row):
            try:
                if pd.isnull(row['P']): return 0
                d = int(np.busday_count(row['P'].date(), row['Date'].date()))
                return 1 if 0 <= d <= 22 else 0
            except: return 0
        df['Is_R'] = df.apply(calc_rdr, axis=1)
        return df
    except Exception as e: return f"Erreur : {e}"

# 2. LOGIQUE D'AFFICHAGE
df = load_data()

if isinstance(df, str):
    st.error(df)
else:
    st.title("📟 Arkeos Technical Dashboard")

    # --- FILTRES SIDEBAR ---
    st.sidebar.header("Filtres")
    
    # Filtre Année
    years = sorted(df['Date'].dt.year.unique().tolist(), reverse=True)
    sel_year = st.sidebar.multiselect("Sélectionner l'Année", years, default=years[:1])
    
    # Filtre Technicien (Corrigé pour afficher les noms)
    tech_list = sorted(df['Tech'].unique().tolist())
    sel_tech = st.sidebar.selectbox("Sélectionner le Technicien", ["Tous"] + tech_list)

    # Application des filtres
    df_f = df[df['Date'].dt.year.isin(sel_year)].copy()
    if sel_tech != "Tous":
        df_f = df_f[df_f['Tech'] == sel_tech]

    # --- INDICATEURS (KPIs) ---
    t = len(df_f)
    r = df_f['Is_R'].sum()
    rdr_rate = (r / t * 100) if t > 0 else 0
    fttr_rate = 100 - rdr_rate

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Interventions", f"{t:,}")
    k2.metric("Taux RDR %", f"{rdr_rate:.1f}%")
    k3.metric("Taux FTTR %", f"{fttr_rate:.1f}%")
    k4.metric("Nb Repeats", f"{r:,}")

    # --- GRAPHIQUE ---
    st.subheader("📈 Tendance du Taux RDR %")
    trend = df_f.set_index('Date')['Is_R'].resample('ME').mean() * 100
    fig = px.area(trend, labels={'value': 'RDR %', 'Date': 'Mois'})
    st.plotly_chart(fig, use_container_width
