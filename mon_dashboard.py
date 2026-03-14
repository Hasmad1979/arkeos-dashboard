import streamlit as st
import pandas as pd
import numpy as np
import os
import io

# 1. Configuration
st.set_page_config(page_title="Arkeos Technical Support Dashboard", layout="wide")

# Style CSS pour les métriques
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #004a99; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    file_name = "data_dynamics_brute.csv.csv"
    if not os.path.exists(file_name):
        return None
    df = pd.read_csv(file_name)
    df = df.rename(columns={"Numéro de l'incident": "ID", "Actifs du client": "SN", "Owner": "Technicien", "Créé le": "Date"})
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['SN', 'Date']).sort_values(['SN', 'Date'])
    
    # Calcul Repeat (22 jours ouvrés)
    df['Date_Prev'] = df.groupby('SN')['Date'].shift(1)
    def calc_bus(row):
        if pd.isnull(row['Date_Prev']): return None
        d1, d2 = row['Date_Prev'].date(), row['Date'].date()
        return int(np.busday_count(d1, d2)) if d1 < d2 else 0

    df['Ecart_Ouvres'] = df.apply(calc_bus, axis=1)
    df['Is_Repeat'] = ((df['Ecart_Ouvres'] >= 0) & (df['Ecart_Ouvres'] <= 22)).astype(int)
    return df

df_raw = load_data()

if df_raw is not None:
    # --- SIDEBAR ---
    if os.path.exists("ark.png"):
        st.sidebar.image("ark.png", width=150)
    
    st.sidebar.title("🎮 Filtres")
    years = sorted(df_raw['Date'].dt.year.unique(), reverse=True)
    sel_years = st.sidebar.multiselect("Années", years, default=years)
    
    techs = sorted(df_raw['Technicien'].unique().tolist())
    sel_techs = st.sidebar.multiselect("Techniciens", techs, default=techs)
    
    df_f = df_raw[(df_raw['Date'].dt.year.isin(sel_years)) & (df_raw['Technicien'].isin(sel_techs))]

    # --- PAGE PRINCIPALE ---
    st.title("📊 Arkeos Support Performance")

    if not df_f.empty:
        # Calculs KPI
        total_int = len(df_f)
        total_rep = df_f['Is_Repeat'].sum()
        repeat_rate = (total_rep / total_int * 100) if total_int > 0 else 0
        ftr_rate = 100 - repeat_rate # KPI First Time Resolution

        # Affichage des 4 KPI
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Interventions", f"{total_int:,}")
        c2.metric("Repeats", f"{total_rep:,}")
        c3.metric("Taux de Repeat", f"{repeat_rate:.1f}%", delta=f"{repeat_rate:.1f}%", delta_color="inverse")
        c4.metric("FTR (First Time Resolution)", f"{ftr_rate:.1f}%", delta=f"{ftr_rate:.1f}%")

        st.divider()

        # Graphique Evolution
        st.subheader("📈 Évolution Mensuelle")
        df_f['Mois_Num'] = df_f['Date'].dt.month
        df_f['Mois'] = df_f['Date'].dt.strftime('%B')
        evol = df_f.groupby(['Mois_Num', 'Mois'])['Is_Repeat'].mean() * 100
        evol = evol.reset_index().sort_values('Mois_Num')
        st.line_chart(evol.set_index('Mois')['Is_Repeat'], color="#004a99")

        # --- SECTIONS IMPACTS ---
        st.divider()
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("👨‍🔧 Top 10 Techniciens (Impact Repeat)")
            top_tech = df_f[df_f['Is_Repeat'] == 1].groupby('Technicien').size().sort_values(ascending=False).head(10)
            st.bar_chart(top_tech, color="#004a99")

        with col_right:
            st.subheader("📁 Top 10 Machines (SN) à surveiller")
            top_sn = df_f[df_f['Is_Repeat'] == 1].groupby('SN').size().sort_values(ascending=False).head(10)
            st.bar_chart(top_sn, color="#ff4b4b")

        # --- TABLEAU DÉTAILLÉ ---
        st.divider()
        st.subheader("📋 Liste des Impacts Repeat (Détails)")
        # On montre les incidents qui sont des repeats
        list_rep = df_f[df_f['Is_Repeat'] == 1][['ID', 'Technicien', 'SN', 'Date', 'Ecart_Ouvres']]
        st.dataframe(list_rep, use_container_width=True)

        # Bouton Export
        st.sidebar.markdown("---")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_f.to_excel(writer, index=False)
        st.sidebar.download_button("📥 Télécharger Rapport Complet", buffer.getvalue(), "Arkeos_Performance.xlsx")

    else:
        st.warning("Aucune donnée pour cette sélection.")
else:
    st.error("Fichier CSV introuvable sur GitHub.")
