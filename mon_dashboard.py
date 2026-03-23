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
    
    col_date, col_sn, col_tech, col_client, col_wo = None, None, None, None, None
    for c in df.columns:
        l = str(c).lower()
        if not col_date and any(x in l for x in ['date', 'créé']): col_date = c
        elif not col_sn and any(x in l for x in ['actif', 'asset', 'sn', 'série']): col_sn = c
        elif not col_tech and any(x in l for x in ['owner', 'propriétaire', 'tech']): col_tech = c
        elif not col_client and any(x in l for x in ['client', 'compte', 'customer']): col_client = c
        elif not col_wo and any(x in l for x in ['ordre', 'wo', 'work order', 'numéro', 'id']): col_wo = c

    rename_dict = {}
    if col_date: rename_dict[col_date] = 'Date'
    if col_sn: rename_dict[col_sn] = 'SN'
    if col_tech: rename_dict[col_tech] = 'Tech'
    if col_client: rename_dict[col_client] = 'Client'
    if col_wo: rename_dict[col_wo] = 'WO'

    df = df.rename(columns=rename_dict)
    cols_to_keep = [c for c in ['Date', 'SN', 'Tech', 'Client', 'WO'] if c in df.columns]
    df = df[cols_to_keep].copy()
    
    # --- LA LIGNE CORRIGÉE ICI ---
    if 'Date' not in df.columns or 'SN' not in df.columns:
        return pd.DataFrame()
    
    df['Tech'] = df.get('Tech', pd.Series(['Inconnu']*len(df))).fillna('Inconnu').astype(str)
    df['Client'] = df.get('Client', pd.Series(['N/A']*len(df))).fillna('N/A').astype(str)
    df['WO'] = df.get('WO', pd.Series(['-']*len(df))).fillna('-').astype(str)
    
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
    df = df.drop_duplicates(subset=['SN', 'Date']).reset_index(drop=True)
    
    df['Prev_Date'] = df.groupby('SN')['Date'].shift(1)
    df['Prev_WO'] = df.groupby('SN')['WO'].shift(1)
    df['R'] = (df['Date'] - df['Prev_Date']).dt.days.apply(lambda x: 1 if pd.notna(x) and 0 <= x <= 22 else 0)
    return df

# ... (reste du code identique)
