import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px

st.set_page_config(page_title="Arkeos Support", layout="wide")

@st.cache_data
def load_data():
    f = "data_dynamics_brute.csv.csv.csv"
    if not os.path.exists(f): return "Fichier introuvable"
    try:
        df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapping et détection automatique des colonnes
        m = {"Numéro de l'incident": "ID", "Actifs du client": "SN", "Owner": "Tech", "Propriétaire": "Tech", "Créé le": "Date", "Created On": "Date"}
        df = df.rename(columns=m)
        
        for c in df.columns:
            if 'Date' not in df.columns and any(x in c.lower() for x in ['date', 'créé']): df = df.rename(columns={c: 'Date'})
            if 'SN' not in df.columns and any(x in c.lower() for x in ['actif', 'asset', 'sn']): df = df.rename(columns={c: 'SN'})
            if 'Tech' not in df.columns and any(x in c.lower() for x in ['owner', 'technicien']): df = df.rename(columns={c: 'Tech'})

        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
        df['Tech'] = df['Tech'].astype(str).replace('nan', 'Non spécifié')

        # Calcul RDR (Repeat 22 jours ouvrés)
        df['P'] = df.groupby('SN')['Date'].shift(1)
        def rdr(r):
            try:
                d = int(np.busday_count(r['P'].date(), r['Date'].date()))
                return 1 if 0 <= d <= 22 else 0
            except: return 0
        df['Is_R'] = df.apply(rdr, axis=1)
        return df
    except Exception as e: return f"Erreur: {e}"

df = load_data()
if isinstance(df, str):
    st.error(df)
else:
    st.title("📟 Arkeos Technical Dashboard")
    
    # --- FILTRES ---
    years = sorted(df['Date'].dt.year.unique().tolist(), reverse=True)
    sel_y = st.sidebar.multiselect("Année", years, default=years[:1])
    techs = sorted(df['Tech'].unique().tolist())
    sel_t = st.sidebar.selectbox("Technicien", ["Tous"] + techs)
