import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import BytesIO

st.set_page_config(layout="wide", page_title="Arkeos Dash")

@st.cache_data
def load_data_fixed():
    f = "data_dynamics_brute.csv.csv.csv" #
    if not os.path.exists(f): return pd.DataFrame()
    
    df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
    
    # --- LA CORRECTION EST ICI ---
    # On assigne les colonnes UNE SEULE FOIS pour éviter les doublons de noms "Date"
    col_date, col_sn, col_tech, col_client = None, None, None, None
    
    for c in df.columns:
        l = str(c).lower()
        if not col_date and ('date' in l or 'créé' in l): col_date = c
        elif not col_sn and any(x in l for x in ['actif', 'asset', 'sn', 'série']): col_sn = c
        elif not col_tech and any(x in l for x in ['owner', 'propriétaire', 'tech']): col_tech = c
        elif not col_client and any(x in l for x in ['client', 'account', 'compte', 'société']): col_client = c

    rename_dict = {}
    if col_date: rename_dict[col_date] = 'Date'
    if col_sn: rename_dict[col_sn] = 'SN'
    if col_tech: rename_dict[col_tech] = 'Tech'
    if col_client: rename_dict[col_client] = 'Client'
    
    df = df.rename(columns=rename_dict)
    
    # On isole uniquement les bonnes colonnes
    cols = [c for c in ['Date', 'SN', 'Tech', 'Client'] if c in df.columns]
    df = df[cols].copy()
    
    if 'Date' not in df.columns or 'SN' not in df.columns:
        return pd.DataFrame()
        
    # La conversion marchera enfin car il n'y a qu'une seule colonne "Date"
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
    
    df = df.drop_duplicates(subset=['SN', 'Date']).reset_index(drop=True)
    
    df['Tech'] = df.get('Tech', pd.Series(['Inconnu']*len(df))).fillna('Inconnu').astype(str)
    
    # Calcul RDR
    df['Prev'] = df.groupby('SN')['Date'].shift(1)
    df['R'] = (df['Date'] - df['Prev']).dt.days.apply(lambda x: 1 if pd.notna(x) and 0 <= x <= 22 else 0)
    
    return df

df = load_data_fixed()

if df.empty:
    st.error("Fichier introuvable ou erreur de structure.")
else:
    # --- FILTRES ---
    years = sorted(df['Date'].dt.year.unique().tolist(), reverse=True)
    sel_yr = st.sidebar.multiselect("Années", years, default=years[:1])
    
    mask = df['Date'].dt.year.isin(sel_yr)
    f_df = df[mask].copy()
    
    st.title("📟 Arkeos Technical Dashboard")

    # --- KPIs ---
    t, r = len(f_df), f_df['R'].sum()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interv.", f"{t}")
    c2.metric("RDR %", f"{(r/t*100 if t>0 else 0):.1f}%")
    c3.metric("FTTR %", f"{(100-(r/t*100 if t>0 else 0)):.1f}%")
    c4.metric("Nb Repeats", f"{int(r)}")

    st.divider()

    # --- TOP 10 ACTIFS & CLIENTS ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("⚠️ Top 10 Actifs (Impact Repeat)")
        top_assets = f_df[f_df['R'] == 1]['SN'].value_counts().head(10).reset_index()
        top_assets.columns = ['SN', 'Nombre de Repeats']
        if not top_assets.empty:
            fig_asset = px.bar(top_assets, x='Nombre de Repeats', y='SN', orientation='h', 
                               color='Nombre de Repeats', color_continuous_scale='Reds')
            st.plotly_chart(fig_asset, use_container_width=True)
        else:
            st.write("Aucun repeat détecté.")

    with col_right:
        if 'Client' in f_df.columns:
            st.subheader("🏢 Top 10 Clients (Impact Repeat)")
