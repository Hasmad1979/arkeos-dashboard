import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import plotly.express as px

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="Arkeos Support Dashboard", layout="wide")

@st.cache_data
def load_data():
    file_name = "data_dynamics_brute.csv.csv" 
    if not os.path.exists(file_name):
        return None
    
    # Lecture du fichier mis à jour
    df = pd.read_csv(file_name)
    
    # Système de détection automatique des colonnes
    def find_col(keywords):
        for col in df.columns:
            if any(k.lower() in col.lower() for k in keywords):
                return col
        return None

    mapping = {
        find_col(["ordre", "trav"]): "ID",
        find_col(["actifs", "client", "sn"]): "Actif", # Focus sur la machine/SN
        find_col(["propriétaire", "owner"]): "Technicien",
        find_col(["création"]): "Date_Debut",
        find_col(["fin"]): "Date_Fin",
        find_col(["compte", "service"]): "Compte"
    }
    
    df = df.rename(columns={k: v for k, v in mapping.items() if k is not None})
    
    # Nettoyage et conversion des dates
    df['Date_Debut'] = pd.to_datetime(df['Date_Debut'], errors='coerce')
    df = df.dropna(subset=['Date_Debut', 'Actif'])

    # --- CALCUL REPEAT DISPATCH (20 JOURS OUVRES PAR ACTIF CLIENT) ---
    # Tri par Actif (SN) et Date
    df = df.sort_values(['Actif', 'Date_Debut'])
    df['Date_Precedente'] = df.groupby('Actif')['Date_Debut'].shift(1)
    
    def calc_working_days(row):
        if pd.isnull(row['Date_Precedente']): return np.nan
        try:
            # np.busday_count calcule l'écart en excluant les samedis et dimanches
            return np.busday_count(row['Date_Precedente'].date(), row['Date_Debut'].date())
        except: return np.nan

    df['Jours_Ouvres_Diff'] = df.apply(calc_working_days, axis=1)
    
    # Un Repeat = même actif réparé à nouveau en <= 20 jours ouvrés
    df['Is_Repeat'] = df['Jours_Ouvres_Diff'].le(20).astype(int)
    
    # Dimensions temporelles pour les graphiques et filtres
    df['Periode'] = df['Date_Debut'].dt.to_period('M').astype(str)
    df['Année'] = df['Date_Debut'].dt.year.astype(str)
    df['Mois_Nom'] = df['Date_Debut'].dt.strftime('%B')
    df['Mois_Num'] = df['Date_Debut'].dt.month
    
    return df

df_raw = load_data()

if df_raw is not None and not df_raw.empty:
    # --- BARRE LATÉRALE : FILTRES ---
    st.sidebar.header("🔍 Filtres")
    
    years = sorted(df_raw['Année'].unique(), reverse=True)
    selected_year = st.sidebar.multiselect("Année", options=years, default=years)
    
    mois_dispo = df_raw[df_raw['Année'].isin(selected_year)].sort_values('Mois_Num')['Mois_Nom'].unique()
    selected_month = st.sidebar.multiselect("Mois", options=list(mois_dispo), default=list(mois_dispo))
    
    tech_list = ["Tous"] + sorted(df_raw['Technicien'].dropna().unique().tolist())
    selected_tech = st.sidebar.selectbox("Technicien", options=tech_list)

    # Application des filtres
    mask = (df_raw['Année'].isin(selected_year)) & (df_raw['Mois_Nom'].isin(selected_month))
    if selected_tech != "Tous":
        mask = mask & (df_raw['Technicien'] == selected_tech)
    
    df_f = df_raw[mask]

    # --- HEADER KPI ---
    st.title("📊 Arkeos Support Dashboard")
    st.markdown("### Analyse de Performance par Actif Client")
    
    total = len(df_f)
    repeats = df_f['Is_Repeat'].sum()
    rdr_rate = (repeats / total * 100) if total > 0 else 0
    fttr_rate = 100 - rdr_rate if total > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interventions", f"{total:,}")
    c2.metric("Repeat Rate (RDR %)", f"{rdr_rate:.1f}%")
    c3.metric("FTTR %", f"{fttr_rate:.1f}%")
    c4.metric("Volume Repeats", f"{repeats:,}")

    st.markdown("---")

    # --- TREND CHART : ÉVOLUTION MENSUELLE ---
    st.subheader("📈 Tendance Mensuelle du RDR % (Actifs)")
    trend_data = df_f.groupby('Periode')['Is_Repeat'].mean().reset_index()
    trend_data['RDR %'] = trend_data['Is_Repeat'] * 100
    
    fig_trend = px.line(trend_data, x='Periode', y='RDR %', markers=True, 
                        color_discrete_sequence=['#FF4B4B'], 
                        labels={'Periode': 'Mois', 'RDR %': 'Taux de Repeat (%)'})
    fig_trend.update_layout(yaxis_range=[0, trend_data['RDR %'].max() + 10])
    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("---")
    
    # --- GRAPHIQUES DE DÉTAILS ---
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📠 Top 10 Actifs (Les plus problématiques)")
        top_a = df_f[df_f['Is_Repeat']==1].groupby('Actif').size().nlargest(10).reset_index(name='Nb_Repeats')
        st.plotly_chart(px.bar(top_a, x='Nb_Repeats', y='Actif', orientation='h', 
                               color_discrete_sequence=['#E74C3C']), use_container_width=True)

    with col2:
        st.subheader("👨‍🔧 RDR % par Technicien (Top 10)")
        tech_rdr = df_f.groupby('Technicien')['Is_Repeat'].mean().reset_index()
        tech_rdr['RDR %'] = tech_rdr['Is_Repeat'] * 100
        st.plotly_chart(px.bar(tech_rdr.nlargest(10, 'RDR %'), x='RDR %', y='Technicien', 
                               orientation='h', color_discrete_sequence=['#FFA500']), use_container_width=True)

    # EXPORT EXCEL
    buffer = io.BytesIO()
    df_f.to_excel(buffer, index=False)
    st.sidebar.download_button("📥 Télécharger Rapport Excel", buffer.getvalue(), "reporting_rdr_arkeos.xlsx")

else:
    st.error("Données introuvables. Vérifiez que le fichier 'data_dynamics_brute.csv.csv' est bien présent sur GitHub.")
