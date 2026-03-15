import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import plotly.express as px

# 1. CONFIGURATION
st.set_page_config(page_title="Arkeos Support Dashboard", layout="wide")

@st.cache_data
def load_data():
    file_name = "data_dynamics_brute.csv.csv" 
    if not os.path.exists(file_name):
        return None
    
    df = pd.read_csv(file_name)

    # Mapping strict avec vos colonnes réelles
    mapping = {
        "Numéro d'ordre de travail": "ID",
        "Propriétaire": "Technicien",
        "Type d'incident principal": "Panne",
        "Compte de service": "Compte",
        "Actif client principal de l'incident": "SN",
        "Date de création": "Date_Debut",
        "Date de fin": "Date_Fin"
    }
    
    df = df.rename(columns=mapping)
    
    # Conversion des dates
    df['Date_Debut'] = pd.to_datetime(df['Date_Debut'], errors='coerce')
    df['Date_Fin'] = pd.to_datetime(df['Date_Fin'], errors='coerce')
    
    # --- NETTOYAGE DES TECHNICIENS ---
    if 'Technicien' in df.columns:
        # On garde les noms propres (avec espace) et on exclut les codes techniques
        df = df[df['Technicien'].str.contains(' ', na=False)]
        df = df[~df['Technicien'].str.contains('CC-WO|WO-', na=False, case=False)]
    
    df = df.dropna(subset=['Date_Debut', 'SN'])

    # --- CALCUL REPEAT (7 JOURS OUVRES PAR ACTIF) ---
    df = df.sort_values(['SN', 'Date_Debut'])
    df['Date_Precedente'] = df.groupby('SN')['Date_Debut'].shift(1)
    
    def calc_working_days(row):
        if pd.isnull(row['Date_Precedente']): return np.nan
        try:
            # np.busday_count calcule l'écart en excluant Samedi/Dimanche
            return np.busday_count(row['Date_Precedente'].date(), row['Date_Debut'].date())
        except: return np.nan

    df['Jours_Ouvres_Diff'] = df.apply(calc_working_days, axis=1)
    
    # --- MODIFICATION ICI : passage à 7 jours ---
    df['Is_Repeat'] = df['Jours_Ouvres_Diff'].le(7).astype(int)
    
    # Dimensions temporelles
    df['Periode'] = df['Date_Debut'].dt.to_period('M').astype(str)
    df['Année'] = df['Date_Debut'].dt.year.astype(str)
    df['Mois_Nom'] = df['Date_Debut'].dt.strftime('%B')
    df['Mois_Num'] = df['Date_Debut'].dt.month
    
    return df

df_raw = load_data()

if df_raw is not None and not df_raw.empty:
    # --- SIDEBAR : FILTRES ---
    st.sidebar.header("🔍 Filtres")
    
    years = sorted(df_raw['Année'].unique(), reverse=True)
    selected_year = st.sidebar.multiselect("Année", options=years, default=years)
    
    mois_dispo = df_raw[df_raw['Année'].isin(selected_year)].sort_values('Mois_Num')['Mois_Nom'].unique()
    selected_month = st.sidebar.multiselect("Mois", options=list(mois_dispo), default=list(mois_dispo))
    
    tech_list = ["Tous"] + sorted(df_raw['Technicien'].unique().tolist())
    selected_tech = st.sidebar.selectbox("Propriétaire (Technicien)", options=tech_list)

    # Filtrage
    mask = (df_raw['Année'].isin(selected_year)) & (df_raw['Mois_Nom'].isin(selected_month))
    if selected_tech != "Tous":
        mask = mask & (df_raw['Technicien'] == selected_tech)
    
    df_f = df_raw[mask]

    # --- DASHBOARD ---
    st.title("📊 Arkeos Performance Dashboard")
    st.markdown("### Analyse de Performance (Seuil : 7 jours ouvrés)")
    
    total = len(df_f)
    repeats = df_f['Is_Repeat'].sum()
    rdr_rate = (repeats / total * 100) if total > 0 else 0
    fttr_rate = 100 - rdr_rate if total > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interventions", f"{total:,}")
    c2.metric("RDR % (7j)", f"{rdr_rate:.1f}%")
    c3.metric("FTTR %", f"{fttr_rate:.1f}%")
    c4.metric("Nb Repeats", f"{repeats:,}")

    st.markdown("---")

    # Trend Chart
    st.subheader("📈 Évolution Mensuelle du RDR % (7 jours)")
    trend = df_f.groupby('Periode')['Is_Repeat'].mean().reset_index()
    trend['RDR %'] = trend['Is_Repeat'] * 100
    st.plotly_chart(px.line(trend, x='Periode', y='RDR %', markers=True, color_discrete_sequence=['#FF4B4B']), use_container_width=True)

    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🛠️ Top 10 Pannes (Repeats 7j)")
        top_p = df_f[df_f['Is_Repeat']==1].groupby('Panne').size().nlargest(10).reset_index(name='Nb')
        st.plotly_chart(px.bar(top_p, x='Nb', y='Panne', orientation='h'), use_container_width=True)

    with col2:
        st.subheader("👨‍🔧 RDR % par Technicien (Top 10)")
        tech_rdr = df_f.groupby('Technicien')['Is_Repeat'].mean().reset_index()
        tech_rdr['RDR %'] = tech_rdr['Is_Repeat'] * 100
        st.plotly_chart(px.bar(tech_rdr.nlargest(10, 'RDR %'), x='RDR %', y='Technicien', orientation='h', color_discrete_sequence=['#FFA500']), use_container_width=True)

    # EXPORT
    buffer = io.BytesIO()
    df_f.to_excel(buffer, index=False)
    st.sidebar.download_button("📥 Export Excel (Données filtrées)", buffer.getvalue(), "reporting_arkeos_7j.xlsx")

else:
    st.error("Données introuvables. Vérifiez le fichier sur GitHub.")
