import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px

st.set_page_config(page_title="Arkeos", layout="wide")

@st.cache_data
def load_data():
    f = "data_dynamics_brute.csv.csv.csv"
    if not os.path.exists(f): return "Fichier introuvable"
    try:
        df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapping automatique
        m = {"Numéro de l'incident": "ID", "Incident Number": "ID",
             "Actifs du client": "SN", "Customer Asset": "SN",
             "Créé le": "Date", "Created On": "Date", "Date": "Date"}
        df = df.rename(columns=m)

        # Force la détection de la date si le mapping échoue
        if 'Date' not in df.columns:
            for c in df.columns:
                if any(x in c.lower() for x in ['date', 'créé', 'created']):
                    df = df.rename(columns={c: 'Date'}); break

        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
        
        # Calcul RDR
        df['P'] = df.groupby('SN')['Date'].shift(1)
        def rdr(r):
            try:
                d = int(np.busday_count(r['P'].date(), r['Date'].date()))
                return 1 if 0 <= d <= 22 else 0
            except: return 0
        df['Is_R'] = df.apply(rdr, axis=1)
        return df
    except Exception as e: return f"Erreur: {e}"

d = load_data()
if isinstance(d, str):
    st.error(d)
else:
    st.title("📟 Arkeos Technical Dashboard")
    t, r = len(d), d['Is_R'].sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Interventions", f"{t}")
    c2.metric("Taux RDR", f"{(r/t*100):.1f}%" if t>0 else "0%")
    c3.metric("Nb
