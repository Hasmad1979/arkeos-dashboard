import streamlit as st
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="Arkeos", layout="wide")

@st.cache_data
def load_data():
    f = "data_dynamics_brute.csv.csv.csv"
    if not os.path.exists(f): return "Fichier introuvable"
    try:
        df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
        df.columns = [str(c).strip() for c in df.columns]
        # Mapping automatique des colonnes vitales
        m = {"Numéro de l'incident": "ID", "Incident Number": "ID",
             "Actifs du client": "SN", "Customer Asset": "SN"}
        df = df.rename(columns=m)
        # Trouve la colonne Date automatiquement
        for c in df.columns:
            if any(x in c.lower() for x in ['date', 'créé', 'created']):
                df = df.rename(columns={c: 'Date'}); break
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
        # Calcul RDR 22j
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
    st.title("📟 Arkeos Dashboard")
    t, r = len(df), df['Is_R'].sum()
    k1, k2, k3 = st.columns(3)
    k1.metric("Interventions", f"{t}")
    k2.metric("RDR %", f"{(r/t*100):.1f}%" if t>0 else "0%")
    k3.metric("Repeats", f"{r}")
    # Graphique ultra-simple pour éviter les coupures
    st.line_chart(df.set_index('Date')['Is_R'].resample('ME').mean())
