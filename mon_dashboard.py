import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import plotly.express as px
from PIL import Image

# 1. CONFIGURATION
st.set_page_config(page_title="Arkeos Support Pro", layout="wide")

# Style Professionnel
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

# 2. CHARGEMENT ET CALCULS
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
    
    # --- ACTION CORRECTIVE : Forcer l'Actif en texte pour éviter l'affichage scientifique ---
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

# 3. INTERFACE
if df_raw is not None:
    with st.sidebar:
        try:
            logo = Image.open('download.png') #
            st.image(logo, width=280) 
        except:
            st.title("ARKEOS")
        
        st.markdown("---")
        st.header("🔍 Filtres")
        
        years = sorted(df_raw['Année'].unique(), reverse=True)
        sel_year = st.multiselect("Année", options=years, default=years)
        
        months = ["January", "February", "March", "April", "May", "June", 
                  "July", "August", "September", "October", "November", "December"]
        available_months = [m for m in months if m in df_raw['Mois'].unique()]
        sel_month = st.multiselect("Mois", options=available_months, default=available_months)
        
        all_techs = df_raw['Technicien'].dropna().unique()
        clean_techs = sorted([t for t in all_techs if " " in str(t) and not str(t).startswith("CC-WO")])
        sel_tech = st.selectbox("Propriétaire (Technicien)", options=["Tous"] + clean_techs)

        # Export Excel corrigé
        st.markdown("---")
        buf = io.BytesIO()
        df_raw.to_excel(buf, index=False)
        st.download_button("📥 Export Excel", buf.getvalue(), "reporting_arkeos.xlsx")

    # 4. AFFICHAGE DES RÉSULTATS
    st.title("📊 Arkeos Support Technique Dashboard")
    
    mask = (df_raw['Année'].isin(sel_year)) & (df_raw['Mois'].isin(sel_month))
    if sel_tech != "Tous":
        mask = mask & (df_raw['Technicien'] == sel_tech)
    df_f = df_raw[mask]

    if not df_f.empty:
        # KPI Row
        total_int = len(df_f)
        repeats = df_f['Is_Repeat'].sum()
        rdr_rate = (repeats / total_int * 100) if total_int > 0 else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Interventions", f"{total_int:,}")
        c2.metric("RDR % (7j)", f"{rdr_rate:.1f}%")
        c3.metric("FTTR %", f"{100-rdr_rate:.1f}%")
        c4.metric("Nb Repeats", f"{repeats:,}")

        st.markdown("---")

        # GRAPHIQUE TENDANCE
        st.subheader("📈 Tendance RDR % par Semaine")
        trend = df_f.groupby('Semaine')['Is_Repeat'].mean().reset_index()
        trend['RDR %'] = (trend['Is_Repeat'] * 100).round(1)
        fig_trend = px.line(trend, x='Semaine', y='RDR %', text='RDR %', markers=True, color_discrete_sequence=['#1E3A8A'])
        fig_trend.update_traces(textposition="top center")
        st.plotly_chart(fig_trend, use_container_width=True)

        # ANALYSE ACTIFS (CORRIGÉ POUR AFFICHAGE TEXTE)
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("📠 Top 10 Actifs (Impact Repeats)")
            df_reps = df_f[df_f['Is_Repeat'] == 1]
            if not df_reps.empty:
                # Groupement strict par ID d'actif (Texte)
                top_a = df_reps.groupby('Actif_SN').size().nlargest(10).reset_index(name='Nb')
                fig_a = px.bar(top_a, x='Nb', y='Actif_SN', orientation='h', 
                               color_discrete_sequence=['#E74C3C'], text='Nb')
                # Force l'axe Y à traiter les valeurs comme des noms (catégories)
                fig_a.update_layout(yaxis={'type': 'category', 'categoryorder': 'total ascending'})
                st.plotly_chart(fig_a, use_container_width=True)
            else:
                st.info("Aucun repeat sur cette sélection.")
        
        with col_b:
            st.subheader("👨‍🔧 RDR % par Technicien")
            tech_perf = df_f.groupby('Technicien')['Is_Repeat'].mean().reset_index()
            tech_perf['RDR %'] = (tech_perf['Is_Repeat'] * 100).round(1)
            top_t = tech_perf.nlargest(10, 'RDR %')
            fig_t = px.bar(top_t, x='RDR %', y='Technicien', orientation='h', 
                           color_discrete_sequence=['#FFA500'], text='RDR %')
            fig_t.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_t, use_container_width=True)

else:
    st.error("Données introuvables. Vérifiez le fichier source.")
