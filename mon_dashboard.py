import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import BytesIO

st.set_page_config(layout="wide", page_title="Arkeos Dash")

@st.cache_data
def load_data():
    f = "data_dynamics_brute.csv"
    if not os.path.exists(f): return pd.DataFrame()
    df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
    ren = {}
    for c in df.columns:
        l = str(c).lower()
        if 'date' in l or 'créé' in l: ren[c] = 'Date'
        elif any(x in l for x in ['actif','asset','sn','série']): ren[c] = 'SN'
        elif any(x in l for x in ['owner','tech']): ren[c] = 'Tech'
        elif any(x in l for x in ['client','compte']): ren[c] = 'Client'
    df = df.rename(columns=ren)
    if 'Date' not in df.columns or 'SN' not in df.columns: return pd.DataFrame()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
    df['Tech'] = df.get('Tech', 'Inconnu').fillna('Inconnu').astype(str)
    df['Client'] = df.get('Client', 'N/A').fillna('N/A').astype(str)
    df['Prev'] = df.groupby('SN')['Date'].shift(1)
    df['R'] = (df['Date']-df['Prev']).dt.days.apply(lambda x: 1 if (0<=x<=22) else 0)
    return df

df = load_data()

if df.empty:
    st.error("Fichier CSV introuvable ou colonnes 'Date'/'SN' absentes.")
else:
    st.title("📟 Arkeos Technical Dashboard")
    # Filtres ultra-courts pour éviter les coupures de ligne
    Y = sorted(df['Date'].dt.year.unique().tolist(), reverse=True)
    sY = st.sidebar.multiselect("Années", Y, default=Y[:1])
    M_N = ["Janvier","Février","Mars","Avril","Mai","Juin","Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
    sM = st.sidebar.multiselect("Mois", M_N, default=M_N)
    #
