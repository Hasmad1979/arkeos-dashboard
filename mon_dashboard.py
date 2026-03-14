import streamlit as st
import pandas as pd
import numpy as np
import os
import io

# 1. Configuration de la page
st.set_page_config(page_title="Arkeos Performance", layout="wide")

# 2. Chargement des données
@st.cache_data
def load_data():
    file_name = "data_dynamics_brute.csv.csv"
    if not os.path.exists(file_name):
        return None
    
    df = pd.read_csv(file_name)
    df = df.rename(columns={
        "Numéro de l'incident": "ID", 
        "Actifs du client": "SN", 
        "Owner": "Technicien", 
        "Créé le": "Date"
    })
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['SN', 'Date']).sort_values(['SN', 'Date'])
    
    # Calcul Jours Ouvrés
    df['Date_Prev'] = df.groupby('SN')['Date'].shift(1)
    def calc_bus(row):
        if pd.isnull(row['Date_Prev']): return None
        d1, d2 = row['Date_Prev'].date(), row['Date'].date()
        if d1 >= d2: return 0
        return int(np.busday_count(d1, d2))

    df['Ecart_Ouvres'] = df.apply(calc_bus, axis=1)
    df['Is_Repeat'] = ((df['Ecart_Ouvres'] >= 0) & (df['Ecart_Ouvres'] <= 22)).astype(int)
    return df

# --- EXECUTION ---
df_raw = load_data()

if df_raw is not None:
    # --- SIDEBAR ---
    if os.path.exists("ark.png"):
        st.sidebar.image("ark.png", width=150)
    
    st.sidebar.title("Filtres")
    years = sorted(df_raw['Date'].dt.year.unique(), reverse=True)
    sel_years = st.sidebar.multiselect("Années", years, default=years)
    
    techs = sorted(df_raw['Technicien'].unique().tolist())
    sel_techs = st.sidebar.multiselect("Techniciens", techs, default=techs)
    
    df_f = df_raw[(df_raw['Date'].dt.year.isin(sel_years)) & (df_raw['Technicien'].isin(sel_techs))]
    
    # --- PAGE PRINCIPALE ---
    st.title("📊 Arkeos Support Performance")
    
    # KPI
    c1, c2, c3 = st.columns(3)
    total_int = len(df_f)
    total_rep = df_f['Is_Repeat'].sum()
    c1.metric("Total Interventions", f"{total_int}")
    c2.metric("Total Repeats", f"{total_rep}")
    c3.metric("Taux de Repeat", f"{(total_rep/total_int*100):.1f}%" if total_int > 0 else "0%")

    st.divider()

    # Graphique Evolution
    st.subheader("📈 Évolution Mensuelle du Repeat")
    df_f['Mois_Num'] = df_f['Date'].dt.month
    df_f['Mois'] = df_f['Date'].dt.strftime('%B')
    evol = df_f.groupby(['Mois_Num', 'Mois'])['Is_Repeat'].mean() * 100
    evol = evol.reset_index().sort_values('Mois_Num')
    if not evol.empty:
        st.line_chart(evol.set_index('Mois')['Is_Repeat'], color="#004a99")

    # --- NOUVELLE SECTION : TOP 10 IMPACT ---
    st.divider()
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("👨‍🔧 Top 10 Techniciens (Impact Repeat)")
        # On compte le nombre de repeats par technicien
        top_tech = df_f[df_f['Is_Repeat'] == 1].groupby('Technicien').size().sort_values(ascending=False).head(10)
        if not top_tech.empty:
            st.bar_chart(top_tech, color="#004a99")
        else:
            st.write("Aucun repeat trouvé pour cette sélection.")

    with col_b:
        st.subheader("📁 Top 10 Machines (SN) Critiques")
        top_sn = df_f[df_f['Is_Repeat'] == 1].groupby('SN').size().sort_values(ascending=False).head(10)
        if not top_sn.empty:
            st.bar_chart(top_sn, color="#ff4b4b")
        else:
            st.write("Aucune machine en repeat trouvée.")

    # --- NOUVELLE SECTION : LISTE DETAILLÉE ---
    st.divider()
    st.subheader("📋 Liste détaillée des Impacts Repeat")
    # On affiche uniquement les lignes qui sont des repeats
    df_repeats_only = df_f[df_f['Is_Repeat'] == 1][['ID', 'Technicien', 'SN', 'Date', 'Ecart_Ouvres']]
    st.dataframe(df_repeats_only, use_container_width=True)

    # Bouton Export
    st.sidebar.markdown("---")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_f.to_excel(writer, index=False)
    st.sidebar.download_button("📥 Télécharger Rapport Complet", buffer.getvalue(), "Arkeos_Full_Report.xlsx")

else:
    st.error("Fichier de données absent sur GitHub.")
