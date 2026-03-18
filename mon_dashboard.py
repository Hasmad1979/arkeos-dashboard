import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="Arkeos Dashboard", layout="wide")

@st.cache_data
def load_data():
    # Détection du fichier sur GitHub
    f = "data_dynamics_brute.csv.csv.csv"
    if not os.path.exists(f): return "Fichier introuvable"
    try:
        df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapping automatique des colonnes Dynamics
        m = {"Numéro de l'incident": "ID", "Incident Number": "ID",
             "Actifs du client": "SN", "Customer Asset": "SN",
             "Owner": "Tech", "Propriétaire": "Tech",
             "Créé le": "Date", "Created On": "Date"}
        df = df.rename(columns=m)

        # Recherche de secours pour la Date et le SN
        for c in df.columns:
            if 'Date' not in df.columns and any(x in c.lower() for x in ['date', 'créé', 'created']):
                df = df.rename(columns={c: 'Date'})
            if 'SN' not in df.columns and any(x in c.lower() for x in ['actif', 'asset', 'serial', 'machine']):
                df = df.rename(columns={c: 'SN'})

        # Nettoyage
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
        if 'Tech' not in df.columns: df['Tech'] = "Inconnu"

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
    except Exception as e: return f"Erreur: {e}"

# 2. LOGIQUE DU DASHBOARD
df = load_data()

if isinstance(df, str):
    st.error(df)
else:
    st.title("📟 Arkeos Technical Dashboard")

    # --- FILTRES SIDEBAR ---
    st.sidebar.header("Filtres")
    years = sorted(df['Date'].dt.year.unique(), reverse=True)
    sel_year = st.sidebar.multiselect("Sélectionner l'Année", years, default=years[:1])
    
    techs = sorted(df['Tech'].unique().astype(str).tolist())
    sel_tech = st.sidebar.selectbox("Sélectionner le Technicien", ["Tous"] + techs)

    # Application des filtres
    df_f = df[df['Date'].dt.year.isin(sel_year)].copy()
    if sel_tech != "Tous":
        df_f = df_f[df_f['Tech'] == sel_tech]

    # --- INDICATEURS (KPIs) ---
    t = len(df_f)
    r = df_f['Is_R'].sum()
    rdr_rate = (r/t*100) if t > 0 else 0
    fttr_rate = 100 - rdr_rate

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interventions", f"{t:,}")
    c2.metric("Taux RDR %", f"{rdr_rate:.1f}%")
    c3.metric("Taux FTTR %", f"{fttr_rate:.1f}%")
    c4.metric("Nb Repeats", f"{r:,}")

    # --- GRAPHIQUE ---
    st.subheader("📈 Tendance du Taux RDR % (Mensuel)")
    trend = df_f.set_index('Date')['Is_R'].resample('ME').mean() * 100
    fig = px.area(trend, labels={'value': 'RDR %', 'Date': 'Mois'}, 
                  color_discrete_sequence=['#1f77b4'])
    fig.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig, use_container_width=True)
