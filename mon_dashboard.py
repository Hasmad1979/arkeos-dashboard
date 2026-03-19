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
    col_date, col_sn, col_tech = None, None, None
    for c in df.columns:
        l = str(c).lower()
        if not col_date and any(x in l for x in ['date', 'créé']): col_date = c
        elif not col_sn and any(x in l for x in ['actif', 'asset', 'sn', 'série']): col_sn = c
        elif not col_tech and any(x in l for x in ['owner', 'propriétaire', 'tech']): col_tech = c
    rename_dict = {}
    if col_date: rename_dict[col_date] = 'Date'
    if col_sn: rename_dict[col_sn] = 'SN'
    if col_tech: rename_dict[col_tech] = 'Tech'
    df = df.rename(columns=rename_dict)
    cols_to_keep = [c for c in ['Date', 'SN', 'Tech'] if c in df.columns]
    df = df[cols_to_keep].copy()
    if 'Date' not in df.columns or 'SN' not in df.columns: return pd.DataFrame()
    df['Tech'] = df.get('Tech', pd.Series(['Inconnu']*len(df))).fillna('Inconnu').astype(str)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date', 'SN'])
    df = df.sort_values('Date').drop_duplicates(subset=['SN', 'Date']).reset_index(drop=True)
    df['Prev'] = df.groupby('SN')['Date'].shift(1)
    df['R'] = (df['Date'] - df['Prev']).dt.days.apply(lambda x: 1 if pd.notna(x) and 0 <= x <= 22 else 0)
    return df

df = load_data_v2()

if df.empty:
    st.error("Erreur de chargement du fichier CSV.")
else:
    st.title("📟 Arkeos Technical Dashboard")
    
    # --- SECTION FILTRES (CORRIGÉE) ---
    years = sorted(df['Date'].dt.year.unique().tolist(), reverse=True)
    sel_yr = st.sidebar.multiselect("Années", years, default=years[:1])
    
    # Liste des mois en clair
    noms_mois = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    
    # LIGNE CRITIQUE : Écrite sur une seule ligne pour éviter les erreurs de syntaxe
    sel_mo_names = st.sidebar.multiselect("Mois", noms_mois, default=noms_mois)
    
    # Mapping rapide pour le filtrage numérique
    mapping_mois = {nom: i+1 for i, nom in enumerate(noms_mois)}
    sel_mo_nums = [mapping_mois[m] for m in sel_mo_names]

    techs = sorted(df['Tech'].unique().tolist())
    sel_tk = st.sidebar.selectbox("Technicien", ["Tous"] + techs)
    
    # --- FILTRAGE ---
    mask = (df['Date'].dt.year.isin(sel_yr)) & (df['Date'].dt.month.isin(sel_mo_nums))
    if sel_tk != "Tous":
        mask = mask & (df['Tech'] == sel_tk)
    
    final_df = df[mask].copy()
    
    # --- DASHBOARD ---
    total = len(final_df)
    reps = final_df['R'].sum()
    rdr = (reps / total * 100) if total > 0 else 0
    fttr = 100 - rdr
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interv.", f"{total}")
    c2.metric("RDR %", f"{rdr:.1f}%")
    c3.metric("FTTR %", f"{fttr:.1f}%")
    c4.metric("Repeats", f"{int(reps)}")

    if not final_df.empty:
        final_df['Mois_Label'] = final_df['Date'].dt.strftime('%Y-%m')
        chart_data = final_df.groupby('Mois_Label')['R'].mean().reset_index()
        chart_data['RDR %'] = chart_data['R'] * 100
        st.plotly_chart(px.bar(chart_data, x='Mois_Label', y='RDR %'), use_container_width=True)
        
        # Bouton Excel
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
            final_df.to_excel(writer, index=False)
        st.sidebar.download_button("📥 Excel", out.getvalue(), "Export.xlsx")
    else:
        st.warning("Aucune donnée disponible.")
