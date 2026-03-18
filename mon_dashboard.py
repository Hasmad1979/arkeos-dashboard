import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from io import BytesIO

st.set_page_config(layout="wide", page_title="Arkeos Dash")

# J'ai changé le nom de la fonction pour forcer Streamlit à vider son cache buggé
@st.cache_data
def load_data_v2():
    f = "data_dynamics_brute.csv.csv.csv"
    if not os.path.exists(f): return pd.DataFrame()
    
    # 1. Lecture
    df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
    
    # 2. LA VRAIE SOLUTION : On cherche les colonnes UNE SEULE FOIS
    col_date, col_sn, col_tech = None, None, None
    
    for c in df.columns:
        l = str(c).lower()
        if not col_date and any(x in l for x in ['date', 'créé']): col_date = c
        elif not col_sn and any(x in l for x in ['actif', 'asset', 'sn', 'série']): col_sn = c
        elif not col_tech and any(x in l for x in ['owner', 'propriétaire', 'tech']): col_tech = c

    # On renomme proprement sans créer de doublons
    rename_dict = {}
    if col_date: rename_dict[col_date] = 'Date'
    if col_sn: rename_dict[col_sn] = 'SN'
    if col_tech: rename_dict[col_tech] = 'Tech'
    
    df = df.rename(columns=rename_dict)
    
    # 3. ON SUPPRIME TOUT LE RESTE POUR NE PAS FAIRE CRASHER STREAMLIT
    cols_to_keep = [c for c in ['Date', 'SN', 'Tech'] if c in df.columns]
    df = df[cols_to_keep].copy()
    
    # Sécurité au cas où il manque une colonne
    if 'Date' not in df.columns or 'SN' not in df.columns:
        return pd.DataFrame() # Retourne un df vide au lieu de crasher
        
    df['Tech'] = df.get('Tech', pd.Series(['Inconnu']*len(df))).fillna('Inconnu').astype(str)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date', 'SN'])
    
    # Tri et nettoyage final
    df = df.sort_values('Date').drop_duplicates(subset=['SN', 'Date']).reset_index(drop=True)
    
    # 4. Calcul RDR
    df['Prev'] = df.groupby('SN')['Date'].shift(1)
    df['R'] = (df['Date'] - df['Prev']).dt.days.apply(lambda x: 1 if pd.notna(x) and 0 <= x <= 22 else 0)
    
    return df

# --- INTERFACE ---
df = load_data_v2()

if df.empty:
    st.error("Impossible de trouver les colonnes Date et SN dans le fichier. Vérifie le nom des colonnes du CSV.")
else:
    st.title("📟 Arkeos Technical Dashboard")
    
    years = sorted(df['Date'].dt.year.unique().tolist(), reverse=True)
    sel_yr = st.sidebar.multiselect("Années", years, default=years[:1])
    techs = sorted(df['Tech'].unique().tolist())
    sel_tk = st.sidebar.selectbox("Technicien", ["Tous"] + techs)
    
    mask = df['Date'].dt.year.isin(sel_yr)
    if sel_tk != "Tous": mask = mask & (df['Tech'] == sel_tk)
    
    final_df = df[mask].copy()
    
    total = len(final_df)
    reps = final_df['R'].sum()
    rdr = (reps / total * 100) if total > 0 else 0
    fttr = 100 - rdr
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interv.", f"{total}")
    c2.metric("RDR %", f"{rdr:.1f}%")
    c3.metric("FTTR %", f"{fttr:.1f}%")
    c4.metric("Repeats", f"{int(reps)}")

    st.subheader("📈 Tendance")
    if not final_df.empty:
        final_df['Mois'] = final_df['Date'].dt.strftime('%Y-%m')
        chart_data = final_df.groupby('Mois')['R'].mean().reset_index()
        chart_data['RDR %'] = chart_data['R'] * 100
        st.plotly_chart(px.bar(chart_data, x='Mois', y='RDR %'), use_container_width=True)

    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
        final_df.to_excel(writer, index=False)
    st.sidebar.download_button("📥 Excel", out.getvalue(), "Export.xlsx")
