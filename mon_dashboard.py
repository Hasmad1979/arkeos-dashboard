import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import BytesIO

st.set_page_config(layout="wide", page_title="Arkeos Dash Pro", page_icon="📟")

# --- STYLE CSS POUR LES KPI PRO ---
st.markdown("""
    <style>
    .metric-card { background-color: #1e2129; padding: 20px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #333; }
    .metric-label { font-size: 14px; color: #a3a8b4; font-weight: bold; }
    .metric-value { font-size: 26px; font-weight: bold; color: white; }
    .status-red { border-left: 5px solid #ff4b4b !important; }
    .status-green { border-left: 5px solid #00cc96 !important; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data_v2():
    f = "data_dynamics_brute.csv.csv.csv" # Nom exact du fichier
    if not os.path.exists(f): return pd.DataFrame()
    
    df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
    
    # Identification des colonnes UNE SEULE FOIS (Anti-doublon)
    col_date, col_sn, col_tech, col_client = None, None, None, None
    for c in df.columns:
        l = str(c).lower()
        if not col_date and any(x in l for x in ['date', 'créé']): col_date = c
        elif not col_sn and any(x in l for x in ['actif', 'asset', 'sn', 'série']): col_sn = c
        elif not col_tech and any(x in l for x in ['owner', 'propriétaire', 'tech']): col_tech = c
        elif not col_client and any(x in l for x in ['client', 'account', 'société']): col_client = c

    rename_dict = {}
    if col_date: rename_dict[col_date] = 'Date'
    if col_sn: rename_dict[col_sn] = 'SN'
    if col_tech: rename_dict[col_tech] = 'Tech'
    if col_client: rename_dict[col_client] = 'Client'
    
    df = df.rename(columns=rename_dict)
    
    # Nettoyage strict
    cols_to_keep = [c for c in ['Date', 'SN', 'Tech', 'Client'] if c in df.columns]
    df = df[cols_to_keep].copy()
    
    if 'Date' not in df.columns or 'SN' not in df.columns:
        return pd.DataFrame()
        
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date', 'SN'])
    df = df.sort_values('Date').drop_duplicates(subset=['SN', 'Date']).reset_index(drop=True)
    
    df['Tech'] = df.get('Tech', pd.Series(['Inconnu']*len(df))).fillna('Inconnu').astype(str)
    
    # Calcul RDR
    df['Prev'] = df.groupby('SN')['Date'].shift(1)
    df['R'] = (df['Date'] - df['Prev']).dt.days.apply(lambda x: 1 if pd.notna(x) and 0 <= x <= 22 else 0)
    
    return df

# --- INTERFACE ---
df = load_data_v2()

if df.empty:
    st.error("Données introuvables ou colonnes Date/SN manquantes.")
else:
    st.title("📟 Arkeos Technical Dashboard")
    
    # Filtres
    years = sorted(df['Date'].dt.year.unique().tolist(), reverse=True)
    sel_yr = st.sidebar.multiselect("Années", years, default=years[:1])
    techs = sorted(df['Tech'].unique().tolist())
    sel_tk = st.sidebar.selectbox("Technicien", ["Tous"] + techs)
    
    mask = df['Date'].dt.year.isin(sel_yr)
    if sel_tk != "Tous": mask = mask & (df['Tech'] == sel_tk)
    
    final_df = df[mask].copy()
    
    # Calculs KPIs
    total = len(final_df)
    reps = final_df['R'].sum()
    rdr = (reps / total * 100) if total > 0 else 0
    fttr = 100 - rdr

    # --- AFFICHAGE KPI COULEURS (PRO) ---
    rdr_class = "status-red" if rdr > 20 else "status-green"
    fttr_class = "status-green" if fttr > 60 else "status-red"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Interv.</div><div class="metric-value">{total}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card {rdr_class}"><div class="metric-label">RDR % (>20%=⚠️)</div><div class="metric-value">{rdr:.1f}%</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card {fttr_class}"><div class="metric-label">FTTR % (<60%=⚠️)</div><div class="metric-value">{fttr:.1f}%</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Repeats</div><div class="metric-value">{int(reps)}</div></div>', unsafe_allow_html=True)

    st.divider()

    # --- TOP 10 ACTIFS & CLIENTS ---
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("⚠️ Top 10 Actifs (Impact RDR)")
        top_a = final_df[final_df['R'] == 1]['SN'].value_counts().head(10).reset_index()
        top_a.columns = ['SN', 'Repeats']
        st.plotly_chart(px.bar(top_a, x='Repeats', y='SN', orientation='h', color='Repeats', color_continuous_scale='Reds'), use_container_width=True)

    with col_b:
        st.subheader("🏢 Top 10 Clients Impactés")
        if 'Client' in final_df.columns:
            top_c = final_df[final_df['R'] == 1]['Client'].value_counts().head(10).reset_index()
            top_c.columns = ['Client', 'Repeats']
            st.plotly_chart(px.bar(top_c, x='Repeats', y='Client', orientation='h', color='Repeats', color_continuous_scale='Oranges'), use_container_width=True)
        else:
            st.info("Colonne Client non détectée.")

    # --- TENDANCE ---
    st.subheader("📈 Tendance Mensuelle")
    if not final_df.empty:
        final_df['Mois'] = final_df['Date'].dt.strftime('%Y-%m')
        chart_data = final_df
