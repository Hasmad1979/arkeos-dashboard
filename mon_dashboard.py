import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import plotly.express as px
from PIL import Image # Nécessaire pour charger le logo

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="Arkeos Support Dashboard", layout="wide")

@st.cache_data
def load_data():
    file_name = "data_dynamics_brute.csv.csv" 
    if not os.path.exists(file_name):
        return None
    
    df = pd.read_csv(file_name)

    # Mapping strict selon vos colonnes réelles
    mapping = {
        "Numéro d'ordre de trav": "ID",
        "Propriétaire": "Technicien",
        "Type d'incident principal": "Panne",
        "Compte de service": "Compte",
        "Actif client principal de l'incident": "Actif_SN",
        "Date de création": "Date_Debut",
        "Date de fin": "Date_Fin"
    }
    
    df = df.rename(columns=mapping)
    df['Date_Debut'] = pd.to_datetime(df['Date_Debut'], errors='coerce')
    
    # Nettoyage des techniciens
    if 'Technicien' in df.columns:
        df = df[df['Technicien'].str.contains(' ', na=False)]
        df = df[~df['Technicien'].str.contains('CC-WO|WO-', na=False, case=False)]
    
    df = df.dropna(subset=['Date_Debut', 'Actif_SN', 'Compte'])

    # --- CALCUL REPEAT (7 JOURS OUVRES PAR ACTIF) ---
    df = df.sort_values(['Actif_SN', 'Date_Debut'])
    df['Date_Precedente'] = df.groupby('Actif_SN')['Date_Debut'].shift(1)
    
    def calc_working_days(row):
        if pd.isnull(row['Date_Precedente']): return np.nan
        try:
            return np.busday_count(row['Date_Precedente'].date(), row['Date_Debut'].date())
        except: return np.nan

    df['Jours_Ouvres_Diff'] = df.apply(calc_working_days, axis=1)
    df['Is_Repeat'] = df['Jours_Ouvres_Diff'].le(7).astype(int)
    
    # Dimensions temporelles
    df['Année'] = df['Date_Debut'].dt.year.astype(str)
    df['Mois_Nom'] = df['Date_Debut'].dt.strftime('%B')
    df['Mois_Num'] = df['Date_Debut'].dt.month
    df['Semaine'] = df['Date_Debut'].dt.strftime('%Y-W%V')
    
    return df

df_raw = load_data()

# --- BARRE LATÉRALE AVEC LOGO ET FILTRES ---
if df_raw is not None:
    # --- AJOUT DU LOGO ICI ---
    try:
        # On charge l'image uploadée
        logo = Image.open('download.png')
        # On l'affiche en haut de la sidebar, alignée à gauche, avec une largeur contrôlée
        st.sidebar.image(logo, use_container_width=False, width=150) 
        # Petit espace sous le logo pour respirer
        st.sidebar.markdown("---") 
    except FileNotFoundError:
        # Si le fichier n'est pas trouvé, on n'affiche rien pour éviter de faire planter l'app
        pass

    # --- FILTRES (Suite de la sidebar) ---
    st.sidebar.header("🔍 Filtres")
    
    years = sorted(df_raw['Année'].unique(), reverse=True)
    selected_year = st.sidebar.multiselect("Année", options=years, default=years)
    
    mois_dispo = df_raw[df_raw['Année'].isin(selected_year)].sort_values('Mois_Num')['Mois_Nom'].unique()
    selected_month = st.sidebar.multiselect("Mois", options=list(mois_dispo), default=list(mois_dispo))
    
    tech_list = ["Tous"] + sorted(df_raw['Technicien'].unique().tolist())
    selected_tech = st.sidebar.selectbox("Propriétaire (Technicien)", options=tech_list)

    mask = (df_raw['Année'].isin(selected_year)) & (df_raw['Mois_Nom'].isin(selected_month))
    if selected_tech != "Tous":
        mask = mask & (df_raw['Technicien'] == selected_tech)
    
    df_f = df_raw[mask]

    # --- KPI ---
    st.title("📊 Arkeos Support Dashboard")
    
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

    # --- TENDANCE HEBDOMADAIRE AVEC % AFFICHÉS ---
    st.subheader("📈 Tendance RDR % par Semaine")
    trend_week = df_f.groupby('Semaine')['Is_Repeat'].mean().reset_index()
    trend_week['RDR %'] = (trend_week['Is_Repeat'] * 100).round(1)
    
    fig_week = px.line(trend_week, x='Semaine', y='RDR %', text='RDR %', markers=True,
                        color_discrete_sequence=['#007BFF'])
    # On place le texte au-dessus des points
    fig_week.update_traces(textposition="top center")
    fig_week.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_week, use_container_width=True)

    st.markdown("---")

    # --- TOP ACTIFS ET COMPTES ---
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("📠 Top 10 Actifs (Machines)")
        top_actifs = df_f[df_f['Is_Repeat']==1].groupby('Actif_SN').size().nlargest(10).reset_index(name='Nb')
        # Calcul du % de contribution aux repeats
        top_actifs['% du total'] = (top_actifs['Nb'] / repeats * 100).round(1).astype(str) + '%' if repeats > 0 else "0%"
        
        fig_actifs = px.bar(top_actifs, x='Nb', y='Actif_SN', orientation='h', text='% du total',
                            color_discrete_sequence=['#E74C3C'])
        st.plotly_chart(fig_actifs, use_container_width=True)

    with col_b:
        st.subheader("🏢 Top 10 Comptes de Service")
        top_comptes = df_f[df_f['Is_Repeat']==1].groupby('Compte').size().nlargest(10).reset_index(name='Nb')
        top_comptes['% du total'] = (top_comptes['Nb'] / repeats * 100).round(1).astype(str) + '%' if repeats > 0 else "0%"
        
        fig_comptes = px.bar(top_comptes, x='Nb', y='Compte', orientation='h', text='% du total',
                             color_discrete_sequence=['#3498DB'])
        st.plotly_chart(fig_comptes, use_container_width=True)

    # EXPORT
    buffer = io.BytesIO()
    df_f.to_excel(buffer, index=False)
    st.sidebar.download_button("📥 Export Excel", buffer.getvalue(), "reporting_arkeos.xlsx")

else:
    st.error("Données introuvables. Vérifiez le fichier source.")
