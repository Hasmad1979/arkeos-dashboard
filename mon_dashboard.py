import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import BytesIO

st.set_page_config(layout="wide", page_title="Arkeos Dash")

@st.cache_data
def load_data_final():
    f = "data_dynamics_brute.csv.csv.csv"
    if not os.path.exists(f): return pd.DataFrame()
    df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
    
    # 1. Détection automatique des colonnes
    c_dt, c_sn, c_tk, c_cl, c_dr = None, None, None, None, None
    for c in df.columns:
        l = str(c).lower()
        if not c_dt and any(x in l for x in ["date", "créé"]): c_dt = c
        elif not c_sn and any(x in l for x in ["actif", "asset", "sn", "série"]): c_sn = c
        elif not c_tk and any(x in l for x in ["owner", "propriétaire", "tech"]): c_tk = c
        elif not c_cl and any(x in l for x in ["client", "compte"]): c_cl = c
        elif not c_dr and any(x in l for x in ["durée", "duration", "temps"]): c_dr = c

    # 2. Renommage et Nettoyage
    renames = {c_dt: "Date", c_sn: "SN", c_tk: "Tech", c_cl: "Client", c_dr: "Duree"}
    df = df.rename(columns={k: v for k, v in renames.items() if k})
    
    if "Date" not in df.columns or "SN" not in df.columns: return pd.DataFrame()
    
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date", "SN"]).sort_values("Date")
    
    # Gestion de la Durée pour le MTTR (défaut 120min si absent)
    df["Duree"] = pd.to_numeric(df.get("Duree", 120), errors="coerce").fillna(120)

    # 3. Calcul RDR (Repeats < 22 jours) - Version sécurisée sans erreur de syntaxe
    df = df.drop_duplicates(subset=["SN", "Date"]).reset_index(drop=True)
    df["Prev"] = df.groupby("SN")["Date"].shift(1)
    df["Days"] = (df["Date"] - df["Prev"]).dt.days
    df["R"] = np.where((df["Days"] >= 0) & (df["Days"] <= 22), 1, 0)
    
    return df

df = load_data_final()

if df.empty:
    st.error("Don
