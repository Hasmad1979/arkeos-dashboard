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
    df.columns = [str(c).strip() for c in df.columns]
    
    # Mapping des colonnes (Ajout du Client)
    col_map = {}
    for c in df.columns:
        l = c.lower()
        if 'date' in l or 'créé' in l: col_map[c] = 'Date'
        if any(x in l for x in ['actif', 'asset', 'sn', 'série']): col_map[c] = 'SN'
        if any(x in l for x in ['owner', 'propriétaire', 'tech']): col_map[c] = 'Tech'
        if any(x in l for x in ['client', 'account', 'compte', 'société']): col_map[c] = 'Client'

    df = df.rename(columns=col_map)
    
    # On ne garde que l'essentiel pour éviter les bugs d'index
    cols = [c for c in ['Date', 'SN', 'Tech', 'Client'] if c in df.columns]
    df = df[cols].copy()
    
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
    
    # Nettoyage des doublons de secondes
    df = df.drop_duplicates(subset=['SN', 'Date']).reset_index(drop=True)
    
    # Calcul RDR
    df['Prev'] = df.groupby('SN')['Date'].shift(1)
    df['R'] = (df['Date'] - df['Prev']).dt.days.apply(lambda x: 1 if pd.notna(x) and 0 <= x <= 22 else 0)
    
    return df

df = load_data_final()

if df.empty:
    st.error("Fichier introuvable ou colonnes manquantes.")
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
        # On filtre uniquement les lignes qui sont des "Repeats"
        top_assets = f_df[f_df['R'] == 1]['SN'].value_counts().head(10).reset_index()
        top_assets.columns = ['SN', 'Nombre de Repeats']
        if not top_assets.empty:
            fig_asset = px.bar(top_assets, x='Nombre de Repeats', y='SN', orientation='h', 
                               color='Nombre de Repeats', color_continuous_scale='Reds')
            st.plotly_chart(fig_asset, use_container_width=True)
        else:
            st.write("Aucun repeat détecté sur cette période.")

    with col_right:
        if 'Client' in f_df.columns:
            st.subheader("🏢 Top 10 Clients (Impact Repeat)")
            top_clients = f_df[f_df['R'] == 1]['Client'].value_counts().head(10).reset_index()
            top_clients.columns = ['Client', 'Nombre de Repeats']
            if not top_clients.empty:
                fig_client = px.bar(top_clients, x='Nombre de Repeats', y='Client', orientation='h',
                                    color='Nombre de Repeats', color_continuous_scale='Oranges')
                st.plotly_chart(fig_client, use_container_width=True)
            else:
                st.write("Aucun client impacté.")

    # --- TENDANCE MENSUELLE ---
    st.subheader("📈 Tendance Globale des Repeats")
    f_df['Mois'] = f_df['Date'].dt.strftime('%Y-%m')
    chart_data = f_df.groupby('Mois')['R'].sum().reset_index()
    st.plotly_chart(px.line(chart_data, x='Mois', y='R', markers=True), use_container_width=True)

    # Export
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
        f_df.to_excel(writer, index=False)
    st.sidebar.download_button("📥 Télécharger Excel", out.getvalue(), "Rapport_Top10.xlsx")
