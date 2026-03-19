import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import BytesIO

st.set_page_config(layout="wide", page_title="Arkeos Dash")

@st.cache_data
def load_data_v4():
    f = "data_dynamics_brute.csv.csv.csv"
    if not os.path.exists(f): return pd.DataFrame()
    df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
    
    # Détection dynamique des colonnes
    col_date, col_sn, col_tech, col_client, col_duree = None, None, None, None, None
    for c in df.columns:
        l = str(c).lower()
        if not col_date and any(x in l for x in ['date', 'créé']): col_date = c
        elif not col_sn and any(x in l for x in ['actif', 'asset', 'sn', 'série']): col_sn = c
        elif not col_tech and any(x in l for x in ['owner', 'propriétaire', 'tech']): col_tech = c
        elif not col_client and any(x in l for x in ['client', 'compte']): col_client = c
        elif not col_duree and any(x in l for x in ['durée', 'duration', 'temps']): col_duree = c

    rename_dict = {col_date: 'Date', col_sn: 'SN', col_tech: 'Tech', col_client: 'Client', col_duree: 'Duree'}
    df = df.rename(columns={k: v for k, v in rename_dict.items() if k})
    
    if 'Date' not in df.columns or 'SN' not in df.columns: return pd.DataFrame()
    
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
    
    # Valeur par défaut pour la durée si absente (ex: 120 min)
    if 'Duree' not in df.columns: df['Duree'] = 120
    else: df['Duree'] = pd.to_numeric(df['Duree'], errors='coerce').fillna(120)

    # Calcul RDR (Repeats)
    df = df.drop_duplicates(subset=['SN', 'Date']).reset_index(drop=True)
    df['Prev'] = df.groupby('SN')['Date'].shift(1)
    df
