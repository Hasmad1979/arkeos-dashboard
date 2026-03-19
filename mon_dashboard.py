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
    
    # Détection dynamique des colonnes
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
    
    # On garde les colonnes utiles
    cols_to_keep = [c for c in ['Date', 'SN', 'Tech', 'Client'] if c in df.columns]
    df = df[cols_to_keep].copy()
    
    if 'Date' not in df.columns or 'SN' not in df.columns: return pd.DataFrame()
    
    df['Tech'] = df.get('Tech', pd.Series(['Inconnu']*len(df))).fillna('Inconnu').astype(str)
    df['Client'] = df.get('Client', pd.Series(['N/A']*len(df))).fillna('N/A').astype(str)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
    
    # Calcul RDR (Intervention dans les 22 jours sur le même SN)
    df = df.drop_duplicates(subset=['SN', 'Date']).reset_index(drop=True)
    df['Prev'] = df.groupby('SN')['Date'].shift(1)
    df['R'] = (df['Date'] - df['Prev']).dt.days.apply(lambda x: 1 if pd.notna(x) and 0 <= x <= 22 else 0)
    
    return df

df = load_data_v2()

if df.empty:
    st.error("Données introuvables ou colonnes manquantes.")
else:
    st.title("📟 Arkeos Technical Dashboard")
    
    # --- FILTRES ---
    years = sorted(df['Date'].dt.year.unique().tolist(), reverse=True)
    sel_yr = st.sidebar.multiselect("Années", years, default=years[:1])
    
    noms_mois = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    sel_mo_names = st.sidebar.multiselect("Mois", noms_mois, default=noms_mois)
    mapping_mois = {nom: i+1 for i, nom in enumerate(noms_mois)}
    sel_mo_nums = [mapping_mois[m] for m in sel_mo_names]

    techs = sorted(df['Tech'].unique().tolist())
    sel_tk = st.sidebar.selectbox("Technicien", ["Tous"] + techs)
    
    mask = (df['Date'].dt.year.isin(sel_yr)) & (df['Date'].dt.month.isin(sel_mo_nums))
    if sel_tk != "Tous": mask = mask & (df['Tech'] == sel_tk)
    
    final_df = df[mask].copy()
    
    # --- METRIQUES ---
    total = len(final_df)
    reps = final_df['R'].sum()
    rdr = (reps / total * 100) if total > 0 else 0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interv. Totales", f"{total}")
    c2.metric("RDR %", f"{rdr:.1f}%")
    c3.metric("FTTR %", f"{100 - rdr:.1f}%")
    c4.metric("Nb de Repeats", f"{int(reps)}")

    st.markdown("---")

    # --- TOP 10 ANALYSE ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("🏆 Top 10 Actifs (SN) les plus impactés")
        # On compte le nombre de "Repeats" (R=1) par SN
        top_sn = final_df[final_df['R'] == 1]['SN'].value_counts().head(10).reset_index()
        top_sn.columns = ['SN', 'Nombre de Repeats']
        if not top_sn.empty:
            st.plotly_chart(px.bar(top_sn, x='Nombre de Repeats', y='SN', orientation='h', color_discrete_sequence=['#ef4444']), use_container_width=True)
        else:
            st.info("Aucun repeat détecté sur cette période.")

    with col_right:
        st.subheader("🏢 Top 10 Clients les plus impactés")
        if 'Client' in final_df.columns and final_df['Client'].nunique() > 1:
            top_cli = final_df[final_df['R'] == 1]['Client'].value_counts().head(10).reset_index()
            top_cli.columns = ['Client', 'Nombre de Repeats']
            if not top_cli.empty:
                st.plotly_chart(px.bar(top_cli, x='Nombre de Repeats', y='Client', orientation='h', color_discrete_sequence=['#3b82f6']), use_container_width=True)
            else:
                st.info("Aucun repeat client sur cette période.")
        else:
            st.warning("Colonne 'Client' non détectée ou vide.")

    # --- TENDANCE ---
    st.subheader("📈 Tendance Mensuelle du RDR %")
    if not final_df.empty:
        final_df['Mois_Label'] = final_df['Date'].dt.strftime('%Y-%m')
        chart_data = final_df.groupby('Mois_Label')['R'].mean().reset_index()
        chart_data['RDR %'] = chart_data['R'] * 100
        st.plotly_chart(px.line(chart_data, x='Mois_Label', y='RDR %', markers=True), use_container_width=True)
        
        # EXPORT
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
            final_df.to_excel(writer, index=False)
        st.sidebar.markdown("---")
        st.sidebar.download_button("📥 Télécharger Excel", out.getvalue(), "Arkeos_Export.xlsx", use_container_width=True)
