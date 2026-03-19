import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import BytesIO

# 1. Configuration de la page
st.set_page_config(layout="wide", page_title="Arkeos Dash")

@st.cache_data
def load_data_v2():
    # Remplacez par le nom exact de votre fichier sur GitHub ou en local
    f = "data_dynamics_brute.csv" 
    
    if not os.path.exists(f): 
        return pd.DataFrame()
    
    # Lecture du CSV
    df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
    
    # Détection des colonnes
    col_date, col_sn, col_tech, col_client = None, None, None, None
    for c in df.columns:
        l = str(c).lower()
        if not col_date and any(x in l for x in ['date', 'créé']): col_date = c
        elif not col_sn and any(x in l for x in ['actif', 'asset', 'sn', 'série']): col_sn = c
        elif not col_tech and any(x in l for x in ['owner', 'propriétaire', 'tech']): col_tech = c
        elif not col_client and any(x in l for x in ['client', 'compte', 'customer']): col_client = c

    rename_dict = {}
    if col_date: rename_dict[col_date] = 'Date'
    if col_sn: rename_dict[col_sn] = 'SN'
    if col_tech: rename_dict[col_tech] = 'Tech'
    if col_client: rename_dict[col_client] = 'Client'
    
    df = df.rename(columns=rename_dict)
    
    # Validation des colonnes critiques
    if 'Date' not in df.columns or 'SN' not in df.columns: 
        return pd.DataFrame()

    # Nettoyage
    df['Tech'] = df.get('Tech', pd.Series(['Inconnu']*len(df))).fillna('Inconnu').astype(str)
    df['Client'] = df.get('Client', pd.Series(['N/A']*len(df))).fillna('N/A').astype(str)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
    df = df.drop_duplicates(subset=['SN', 'Date']).reset_index(drop=True)

    # Calcul du Repeat (R) - Fenêtre de 22 jours
    df['Prev'] = df.groupby('SN')['Date'].shift(
