import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import plotly.express as px
from PIL import Image

# 1. CONFIGURATION ET STYLE
st.set_page_config(page_title="Arkeos Support Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetricValue"] { font-size: 28px; color: #1E3A8A; font-weight: bold; }
    div[data-testid="metric-container"] {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #eef2f6;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. CHARGEMENT ET NETTOYAGE
@st.cache_data
def load_data():
    file_name = "data_dynamics_brute.csv.csv" 
    if not os.path.exists(file_name):
        return None
    
    df = pd.read_csv(file_name)

    mapping = {
        "Numéro d'ordre de travail": "ID",
        "Propriétaire": "Technicien",
        "Type d'incident principal": "Panne",
        "Compte de service": "Compte",
        "Actif client principal de l'incident": "Actif_SN",
        "Date de création": "Date_Debut"
    }
    df = df.rename(columns=mapping)
    
    # CORRECTION : On force l'Actif en texte pour éviter l'affichage "34.8M"
    df['Actif_SN'] = df['Actif_SN'].astype(str).str.replace('.0', '', regex=False)
    
    df['Date_Debut'] = pd.to_datetime(df['Date_Debut'], errors='coerce')
    df = df.dropna(subset=['Date_Debut', 'Actif_SN'])

    # CALCUL REPEAT (7 JOURS OUVRES)
    df = df.sort_values(['Actif_SN', 'Date_Debut'])
    df['Date_Precedente'] = df.groupby('Actif_SN')['Date_Debut'].shift(1)
    
    def calc_working_days(row):
        if pd.isnull(row['Date_Precedente']): return np.nan
        try:
            return np.busday_count(row['Date_Precedente'].date(), row['Date_Debut'].date())
        except: return np.nan

    df['Jours_Ouvres_Diff'] = df.apply(calc_working_days, axis=1)
    df['Is_Repeat'] = df['Jours_Ouvres_Diff'].le(7).astype(int)
    
    df['Année'] = df['Date_Debut'].dt.year.astype(str)
    df['Mois'] = df['Date_Debut'].dt.strftime('%B')
    df['Semaine'] = df['Date_Debut'].dt.strftime('%Y-W%V')
    
    return df

df_raw = load_data()

# 3. INTERFACE LATÉRALE (LOGO & FILTRES)
if df_raw is not None:
    with st.sidebar:
        try:
            # Utilisation du fichier download.png présent dans vos dossiers
            logo = Image.open('download.png')
            st.image(logo, use_container_width=True) 
        except:
            st.title("ARKEOS")
        
        st.markdown("---")
        st.header("🔍 Filtres")
        
        years = sorted(df_raw['Année'].unique(), reverse=True)
        sel_year = st.multiselect("Année", options=years, default=years)
        
        all_techs = df_raw['Technicien'].dropna().unique()
        clean_techs = sorted([t for t in all_techs if " " in str(t) and not str(t).startswith("CC-WO")])
        sel_tech = st.selectbox("Technicien", options=["Tous"] + clean_techs)

        st.markdown("---")
        buf = io.BytesIO()
        df_raw.to_excel(buf, index=False)
        st.download_button("📥 Export Excel", buf.getvalue(), "reporting_arkeos.xlsx")

    # 4. DASHBOARD PRINCIPAL
    st.title("📊 Arkeos Support Technique Dashboard")
    
    mask = df_raw['Année'].isin(sel_year)
    if sel_tech != "Tous":
        mask = mask & (df_raw['Technicien'] == sel_tech)
    df_f = df_raw[mask]

    if not df_f.empty:
        # KPI
        c1, c2, c3, c4 = st.columns(4)
        total = len(df_f)
        reps = df_f['Is_Repeat'].sum()
        rdr = (reps / total * 100) if total > 0 else 0
        
        c1.metric("Interventions", f"{total:,}")
        c2.metric("RDR % (7j)", f"{rdr:.1f}%")
        c3.metric("FTTR %", f"{100-rdr:.1f}%")
        c4.metric("Nb Repeats", f"{reps:,}")

        st.markdown("---")

        # TENDANCE HEBDO
        st.subheader("📈 Tendance RDR % par Semaine")
        trend = df_f.groupby('Semaine')['Is_Repeat'].mean().reset_index()
        trend['RDR %'] = (trend['Is_Repeat'] * 100).round(1)
        fig_trend = px.line(trend, x='Semaine', y='RDR %', markers=True, color_discrete_sequence=['#1E3A8A'])
        st.plotly_chart(fig_trend, use_container_width=True)

        # ANALYSE PAR ACTIF (CORRIGÉE)
        st.subheader("📠 Top 10 Actifs (Impact Repeats)")
        df_reps = df_f[df_f['Is_Repeat'] == 1]
        if not df_reps.empty:
            top_a = df_reps.groupby('Actif_SN').size().nlargest(10).reset_index(name='Nb')
            fig_a = px.bar(top_a, x='Nb', y='Actif_SN', orientation='h', 
                           color_discrete_sequence=['#E74C3C'], text='Nb')
            # On force l'affichage catégorique pour voir les vrais numéros de série
            fig_a.update_layout(yaxis={'type': 'category', 'categoryorder': 'total ascending'})
            st.plotly_chart(fig_a, use_container_width=True)
        
    else:
        st.warning("Aucune donnée pour ces filtres.")
else:
    st.error("Fichier de données introuvable.")
