import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import matplotlib.pyplot as plt
import seaborn as sns

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
        try:
            return int(np.busday_count(d1, d2)) if d1 < d2 else 0
        except:
            return 0

    df['Ecart_Ouvres'] = df.apply(calc_bus, axis=1)
    df['Is_Repeat'] = ((df['Ecart_Ouvres'] >= 0) & (df['Ecart_Ouvres'] <= 22)).astype(int)
    return df

df_raw = load_data()

if df_raw is not None:
    # Dictionnaire des mois pour le filtrage et l'affichage
    noms_mois = {1:'Janvier', 2:'Février', 3:'Mars', 4:'Avril', 5:'Mai', 6:'Juin', 
                 7:'Juillet', 8:'Août', 9:'Septembre', 10:'Octobre', 11:'Novembre', 12:'Décembre'}

    # --- SIDEBAR ---
    if os.path.exists("ark.png"):
        st.sidebar.image("ark.png", width=150)
    
    st.sidebar.title("🎮 Filtres")
    
    # Filtre Années
    years = sorted(df_raw['Date'].dt.year.unique(), reverse=True)
    sel_years = st.sidebar.multiselect("Années", years, default=years)
    
    # NOUVEAU : Filtre Mois
    df_raw['Mois_Num'] = df_raw['Date'].dt.month
    df_raw['Mois_Nom'] = df_raw['Mois_Num'].map(noms_mois)
    
    # On trie les mois disponibles par ordre chronologique pour le filtre
    available_months = sorted(df_raw['Mois_Num'].unique())
    month_options = [noms_mois[m] for m in available_months]
    
    sel_months_names = st.sidebar.multiselect("Mois", month_options, default=month_options)
    
    # Filtre Techniciens
    techs = sorted(df_raw['Technicien'].unique().tolist())
    sel_techs = st.sidebar.multiselect("Techniciens", techs, default=techs)
    
    # Application des filtres
    df_f = df_raw[
        (df_raw['Date'].dt.year.isin(sel_years)) & 
        (df_raw['Mois_Nom'].isin(sel_months_names)) &
        (df_raw['Technicien'].isin(sel_techs))
    ].copy()

    # --- PAGE PRINCIPALE ---
    st.title("📊 Arkeos Technical Support Dashboard")

    if not df_f.empty:
        # --- 1. LES KPI ---
        total_int = len(df_f)
        total_rep = df_f['Is_Repeat'].sum()
        repeat_rate = (total_rep / total_int * 100) if total_int > 0 else 0
        ftr_rate = 100 - repeat_rate 

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Interventions", f"{total_int:,}")
        c2.metric("Repeats", f"{total_rep:,}")
        c3.metric("Taux de Repeat", f"{repeat_rate:.1f}%", delta=f"{repeat_rate:.1f}%", delta_color="inverse")
        c4.metric("FTR (First Time Resolution)", f"{ftr_rate:.1f}%", delta=f"{ftr_rate:.1f}%")

        st.divider()

        # --- 2. LE GRAPHIQUE ÉVOLUTION ---
        st.subheader("📈 Évolution Mensuelle du Taux de Repeat")
        
        evol = df_f.groupby('Mois_Num')['Is_Repeat'].mean() * 100
        evol = evol.reset_index()
        evol['Mois_Label'] = evol['Mois_Num'].map(lambda x: noms_mois[x][:4] + ".") # Version courte pour le graph

        fig, ax = plt.subplots(figsize=(12, 4.5)) 
        sns.set_theme(style="whitegrid")
        sns.lineplot(x='Mois_Label', y='Is_Repeat', data=evol, marker='o', 
                     linewidth=3, color='#004a99', markerfacecolor='#ff4b4b', markersize=8, ax=ax)

        for i, row in evol.iterrows():
            ax.text(i, row['Is_Repeat'] + 1.5, f"{row['Is_Repeat']:.1f}%", 
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

        ax.set_xlabel(None)
        ax.set_ylabel("Taux (%)", fontweight='bold')
        ax.set_ylim(0, max(evol['Is_Repeat'].max() + 10, 20))
        sns.despine(left=True, bottom=True)
        st.pyplot(fig)

        # --- 3. SECTIONS IMPACTS (TOP 10) ---
        st.divider()
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("👨‍🔧 Top 10 Techniciens (Impact Repeat)")
            top_tech = df_f[df_f['Is_Repeat'] == 1].groupby('Technicien').size().sort_values(ascending=False).head(10)
            if not top_tech.empty:
                st.bar_chart(top_tech, color="#004a99")
            else:
                st.info("Aucun repeat pour cette sélection.")

        with col_right:
            st.subheader("📁 Top 10 Machines (SN) à surveiller")
            top_sn = df_f[df_f['Is_Repeat'] == 1].groupby('SN').size().sort_values(ascending=False).head(10)
            if not top_sn.empty:
                st.bar_chart(top_sn, color="#ff4b4b")
            else:
                st.info("Aucune machine critique.")

        # --- 4. TABLEAU DÉTAILLÉ ---
        st.divider()
        st.subheader("📋 Liste des Impacts Repeat (Détails)")
        list_rep = df_f[df_f['Is_Repeat'] == 1][['ID', 'Technicien', 'SN', 'Date', 'Ecart_Ouvres']]
        st.dataframe(list_rep, use_container_width=True)

        # --- 5. BOUTON EXPORT ---
        st.sidebar.markdown("---")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_f.to_excel(writer, index=False)
        st.sidebar.download_button("📥 Télécharger Rapport Complet", buffer.getvalue(), "Arkeos_Performance.xlsx")

    else:
        st.warning("Aucune donnée pour cette sélection de mois/années/techniciens.")
else:
    st.error("Fichier CSV introuvable.")
