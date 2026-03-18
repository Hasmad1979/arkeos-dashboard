import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import BytesIO

st.set_page_config(layout="wide", page_title="Arkeos Dash Pro", page_icon="📟")

# --- STYLE CSS POUR LES KPI ---
st.markdown("""
    <style>
    .metric-card { background-color: #1e2129; padding: 20px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #333; }
    .metric-label { font-size: 14px; color: #a3a8b4; }
    .metric-value { font-size: 24px; font-weight: bold; color: white; }
    .status-red { border-left: 5px solid #ff4b4b !important; }
    .status-green { border-left: 5px solid #00cc96 !important; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    f = "data_dynamics_brute.csv.csv.csv" #
    if not os.path.exists(f): return pd.DataFrame()
    df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
    
    col_date, col_sn, col_tech, col_client = None, None, None, None
    for c in df.columns:
        l = str(c).lower()
        if not col_date and ('date' in l or 'créé' in l): col_date = c
        elif not col_sn and any(x in l for x in ['actif', 'asset', 'sn']): col_sn = c
        elif not col_tech and any(x in l for x in ['owner', 'propriétaire', 'tech']): col_tech = c
        elif not col_client and any(x in l for x in ['client', 'account', 'société']): col_client = c

    df = df.rename(columns={col_date:'Date', col_sn:'SN', col_tech:'Tech', col_client:'Client'})
    df = df[[c for c in ['Date', 'SN', 'Tech', 'Client'] if c in df.columns]].copy()
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
    df = df.drop_duplicates(subset=['SN', 'Date']).reset_index(drop=True)
    
    df['Prev'] = df.groupby('SN')['Date'].shift(1)
    df['R'] = (df['Date'] - df['Prev']).dt.days.apply(lambda x: 1 if pd.notna(x) and 0 <= x <= 22 else 0)
    return df

df = load_data()

if not df.empty:
    st.title("📟 Support Technical Performance")
    
    # Filtres
    years = sorted(df['Date'].dt.year.unique().tolist(), reverse=True)
    sel_yr = st.sidebar.multiselect("Années", years, default=years[:1])
    f_df = df[df['Date'].dt.year.isin(sel_yr)].copy()
    
    # Calculs
    total = len(f_df)
    reps = f_df['R'].sum()
    rdr = (reps / total * 100) if total > 0 else 0
    fttr = 100 - rdr

    # --- AFFICHAGE DES KPI (CORRIGÉ) ---
    rdr_class = "status-red" if rdr > 20 else "status-green"
    fttr_class = "status-green" if fttr > 60 else "status-red"

    # On définit bien les colonnes Streamlit ici
    c1, c2, c3, c4 = st.columns(4) 
    
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Interv.</div><div class="metric-value">{total}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card {rdr_class}"><div class="metric-label">RDR %</div><div class="metric-value">{rdr:.1f}%</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card {fttr_class}"><div class="metric-label">FTTR %</div><div class="metric-value">{fttr:.1f}%</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Repeats</div><div class="metric-value">{int(reps)}</div></div>', unsafe_allow_html=True)

    st.divider()

    # --- TOP 10 ---
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("⚠️ Top 10 Actifs")
        top_a = f_df[f_df['R']==1]['SN'].value_counts().head(10).reset_index()
        st.plotly_chart(px.bar(top_a, x='count', y='SN', orientation='h', color_discrete_sequence=['#ff4b4b']), use_container_width=True)
    with col_b:
        st.subheader("🏢 Top 10 Clients")
        if 'Client' in f_df.columns:
            top_c = f_df[f_df['R']==1]['Client'].value_counts().head(10).reset_index()
            st.plotly_chart(px.bar(top_c, x='count', y='Client', orientation='h', color_discrete_sequence=['#00cc96']), use_container_width=True)

    # Export
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
        f_df.to_excel(wr, index=False)
    st.sidebar.download_button("📥 Excel", out.getvalue(), "Rapport.xlsx")
else:
    st.error("Données vides ou erreur de lecture.")
