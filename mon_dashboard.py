import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import BytesIO

st.set_page_config(layout="wide", page_title="Arkeos Dash")

@st.cache_data
def load_data_v2():
    f = "data_dynamics_brute.csv.csv.csv"
    if not os.path.exists(f): return pd.DataFrame()
    df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
    
    # --- DÉTECTION DES COLONNES (Ajout de WO) ---
    col_date, col_sn, col_tech, col_client, col_wo = None, None, None, None, None
    for c in df.columns:
        l = str(c).lower()
        if not col_date and any(x in l for x in ['date', 'créé']): col_date = c
        elif not col_sn and any(x in l for x in ['actif', 'asset', 'sn', 'série']): col_sn = c
        elif not col_tech and any(x in l for x in ['owner', 'propriétaire', 'tech']): col_tech = c
        elif not col_client and any(x in l for x in ['client', 'compte', 'customer']): col_client = c
        # Détection du numéro d'ordre / intervention
        elif not col_wo and any(x in l for x in ['ordre', 'wo', 'work order', 'numéro', 'id']): col_wo = c

    rename_dict = {}
    if col_date: rename_dict[col_date] = 'Date'
    if col_sn: rename_dict[col_sn] = 'SN'
    if col_tech: rename_dict[col_tech] = 'Tech'
    if col_client: rename_dict[col_client] = 'Client'
    if col_wo: rename_dict[col_wo] = 'WO'

    df = df.rename(columns=rename_dict)
    
    # On conserve les colonnes identifiées
    cols_to_keep = [c for c in ['Date', 'SN', 'Tech', 'Client', 'WO'] if c in df.columns]
    df = df[cols_to_keep].copy()
    
    if 'Date' not in df.columns or
