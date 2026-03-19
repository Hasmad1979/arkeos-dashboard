import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import BytesIO

st.set_page_config(layout="wide", page_title="Arkeos Dash")

@st.cache_data
def load_data_v3():
    f = "data_dynamics_brute.csv.csv.csv"
    if not os.path.exists(f): return pd.DataFrame()
    df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
    
    # Détection dynamique
    col_date, col_sn, col_tech, col_client = None, None, None, None
    for c in df.columns:
        l = str(c).lower()
        if not col_date and any(x in l for x in ['date', 'créé']): col_date = c
        elif not col_sn and any(x in l for x in ['actif', 'asset', 'sn', 'série']): col_sn = c
        elif not col_tech and any(x in l for x in ['owner', 'propriétaire', 'tech']): col_tech = c
        elif not col_client and any(x in l for x in ['client', 'compte', 'customer']): col_client = c

    rename_dict = {col_date: 'Date', col_sn: 'SN', col_tech: 'Tech', col_client: 'Client'}
    df = df.rename(columns={k: v for k, v in rename_dict.items() if k})
    
    cols_to_keep = [c for c in ['Date', 'SN', 'Tech', 'Client'] if c in df.columns]
    df = df[cols_to_keep].copy()
    
    if 'Date' not in df.columns or 'SN' not in df.columns: return pd.DataFrame()
    
    df['Tech'] = df.get('Tech', pd.Series(['Inconnu']*len(df))).fillna('Inconnu').astype(str)
    df['Client'] = df.get('Client', pd.Series(['N/A']*len(df))).fillna('N/A').astype(str)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
    df = df.drop_duplicates(subset=['SN', 'Date']).reset_index(drop=True)
    
    # Calcul RDR (Repeats)
    df['Prev'] = df.groupby('SN')['Date'].shift(1)
    df['R'] = (df['Date'] - df['Prev']).dt.days.apply(lambda x: 1 if pd.notna(x) and 0 <= x <= 22 else 0)
    
    # Ajout du jour de la semaine pour l'analyse de productivité
    df['Jour'] = df['Date'].dt.day_name()
    return df

df = load_data_v3()

if df.empty:
    st.error("Données introuvables.")
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
    
    # --- METRIQUES PRINCIPALES ---
    total = len(final_df)
    reps = final_df['R'].sum()
    rdr = (reps / total * 100) if total > 0 else 0
    fttr = 100 - rdr

    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interv. Totales", f"{total}")
    
    color_rdr = "#ef4444" if rdr > 20 else "#31333F"
    c2.markdown(f"**RDR %** \n <h2 style='color:{color_rdr}; font-weight:bold;'>{rdr:.1f}%</h2>", unsafe_allow_html=True)
    
    color_fttr = "#22c55e" if fttr > 60 else "#31333F"
    c3.markdown(f"**FTTR %** \n <h2 style='color:{color_fttr}; font-weight:bold;'>{fttr:.1f}%</h2>", unsafe_allow_html=True)
    
    c4.metric("Nb de Repeats", f"{int(reps)}")
    st.markdown("---")

    # --- NOUVELLE SECTION : ANALYSE PRODUCTIVITÉ & TECH ---
    st.subheader("👨‍🔧 Performance des Techniciens")
    
    col_t1, col_t2 = st.columns(2)
    
    with col_t1:
        # Volume d'interventions par Technicien
        tech_volume = final_df['Tech'].value_counts().reset_index()
        tech_volume.columns = ['Technicien', 'Volume']
        fig_vol = px.bar(tech_volume.head(15), x='Volume', y='Technicien', orientation='h', 
                         title="Volume d'interv. par Technicien", color='Volume', color_continuous_scale='Blues')
        st.plotly_chart(fig_vol, use_container_width=True)

    with col_t2:
        # Taux de Repeat par Technicien (Qualité)
        tech_quality = final_df.groupby('Tech')['R'].mean().reset_index()
        tech_quality['RDR %'] = tech_quality['R'] * 100
        tech_quality = tech_quality.sort_values('RDR %', ascending=False)
        fig_qual = px.bar(tech_quality.head(15), x='RDR %', y='Tech', orientation='h',
                          title="Taux de Repeat par Tech (Qualité)", color='RDR %', color_continuous_scale='Reds')
        st.plotly_chart(fig_qual, use_container_width=True)

    # --- TOP CLIENTS & ACTIFS ---
    st.markdown("---")
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("🏆 Top 10 Actifs (SN) - Repeats")
        top_sn = final_df[final_df['R'] == 1]['SN'].value_counts().head(10).reset_index()
        st.plotly_chart(px.bar(top_sn, x='count', y='SN', orientation='h', color_discrete_sequence=['#ef4444']), use_container_width=True)

    with col_right:
        st.subheader("🏢 Top 10 Clients - Repeats")
        top_cli = final_df[final_df['R'] == 1]['Client'].value_counts().head(10).reset_index()
        st.plotly_chart(px.bar(top_cli, x='count', y='Client', orientation='h', color_discrete_sequence=['#3b82f6']), use_container_width=True)

    # --- EXPORT ---
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
        final_df.to_excel(writer, index=False)
    st.sidebar.download_button("📥 Télécharger Excel", out.getvalue(), "Arkeos_Full_Export.xlsx", use_container_width=True)
