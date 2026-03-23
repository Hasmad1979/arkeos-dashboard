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
    cols_to_keep = [c for c in ['Date', 'SN', 'Tech', 'Client'] if c in df.columns]
    df = df[cols_to_keep].copy()
    if 'Date' not in df.columns or 'SN' not in df.columns: return pd.DataFrame()
    df['Tech'] = df.get('Tech', pd.Series(['Inconnu']*len(df))).fillna('Inconnu').astype(str)
    df['Client'] = df.get('Client', pd.Series(['N/A']*len(df))).fillna('N/A').astype(str)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
    df = df.drop_duplicates(subset=['SN', 'Date']).reset_index(drop=True)
    df['Prev'] = df.groupby('SN')['Date'].shift(1)
    # Calcul du repeat : intervalle entre 0 et 22 jours
    df['R'] = (df['Date'] - df['Prev']).dt.days.apply(lambda x: 1 if pd.notna(x) and 0 <= x <= 22 else 0)
    return df

df = load_data_v2()

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
    
    # --- CALCULS ---
    total = len(final_df)
    reps = final_df['R'].sum()
    rdr = (reps / total * 100) if total > 0 else 0
    fttr = 100 - rdr

    # --- AFFICHAGE DES MÉTRIQUES ---
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interv. Totales", f"{total}")
    color_rdr = "#ef4444" if rdr > 20 else "#31333F"
    c2.markdown(f"**RDR %** \n <h2 style='color:{color_rdr}; font-weight:bold;'>{rdr:.1f}%</h2>", unsafe_allow_html=True)
    color_fttr = "#22c55e" if fttr > 60 else "#31333F"
    c3.markdown(f"**FTTR %** \n <h2 style='color:{color_fttr}; font-weight:bold;'>{fttr:.1f}%</h2>", unsafe_allow_html=True)
    c4.metric("Nb de Repeats", f"{int(reps)}")
    st.markdown("---")

    # --- GRAPHES TOP 10 ---
    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("🏆 Top 10 Actifs (SN) - Repeats")
        top_sn = final_df[final_df['R'] == 1]['SN'].value_counts().head(10).reset_index()
        top_sn.columns = ['SN', 'Repeats']
        st.plotly_chart(px.bar(top_sn, x='Repeats', y='SN', orientation='h', color_discrete_sequence=['#ef4444']), use_container_width=True)

    with col_right:
        st.subheader("🏢 Top 10 Clients - Repeats")
        top_cli = final_df[final_df['R'] == 1]['Client'].value_counts().head(10).reset_index()
        top_cli.columns = ['Client', 'Repeats']
        st.plotly_chart(px.bar(top_cli, x='Repeats', y='Client', orientation='h', color_discrete_sequence=['#3b82f6']), use_container_width=True)

    # --- TENDANCE ---
    st.subheader("📈 Trend RDR")
    if not final_df.empty:
        final_df['Mois_Label'] = final_df['Date'].dt.strftime('%Y-%m')
        chart_data = final_df.groupby('Mois_Label')['R'].mean().reset_index()
        chart_data['RDR %'] = chart_data['R'] * 100
        st.plotly_chart(px.line(chart_data, x='Mois_Label', y='RDR %', markers=True), use_container_width=True)

        # --- SECTION EXPORT (MODIFIÉE) ---
        st.sidebar.markdown("### 📊 Exports")
        
        # 1. Export COMPLET
        out_all = BytesIO()
        with pd.ExcelWriter(out_all, engine='xlsxwriter') as writer:
            final_df.to_excel(writer, index=False)
        st.sidebar.download_button("📥 Excel (All)", out_all.getvalue(), "Export_Complet.xlsx", use_container_width=True)

        # 2. Export REPEATS UNIQUEMENT (Les 17 cas)
        df_only_repeats = final_df[final_df['R'] == 1].copy()
        if not df_only_repeats.empty:
            out_reps = BytesIO()
            with pd.ExcelWriter(out_reps, engine='xlsxwriter') as writer:
                df_only_repeats.to_excel(writer, index=False)
            st.sidebar.download_button("🚨 Excel (Repeats Only)", out_reps.getvalue(), "Export_Repeats.xlsx", use_container_width=True, type="primary")
