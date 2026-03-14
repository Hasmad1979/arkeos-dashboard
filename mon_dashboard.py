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
    # --- BARRE LATÉRALE (SIDEBAR) ---
    # Affichage du logo
    if os.path.exists("ark.png"):
        st.sidebar.image("ark.png", width=150)
    
    st.sidebar.title("Filtres")
    
    # Filtre Années
    years = sorted(df_raw['Date'].dt.year.unique(), reverse=True)
    sel_years = st.sidebar.multiselect("Années", years, default=years)
    
    # Filtre Techniciens (C'est ce qui manquait !)
    techs = sorted(df_raw['Technicien'].unique().tolist())
    sel_techs = st.sidebar.multiselect("Techniciens", techs, default=techs)
    
    # Application des filtres
    df_f = df_raw[
        (df_raw['Date'].dt.year.isin(sel_years)) & 
        (df_raw['Technicien'].isin(sel_techs))
    ]
    
    # --- PAGE PRINCIPALE ---
    st.title("📊 Arkeos Support Performance")
    
    # KPI
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Interventions", f"{len(df_f)}")
    c2.metric("Total Repeats", f"{df_f['Is_Repeat'].sum()}")
    c3.metric("Taux de Repeat", f"{(df_f['Is_Repeat'].mean()*100):.1f}%" if len(df_f)>0 else "0%")

    # Graphique
    st.subheader("📈 Évolution Mensuelle")
    df_f['Mois_Sort'] = df_f['Date'].dt.month
    df_f['Mois'] = df_f['Date'].dt.strftime('%B')
    evol = df_f.groupby(['Mois_Sort', 'Mois'])['Is_Repeat'].mean() * 100
    evol = evol.reset_index().sort_values('Mois_Sort')
    
    if not evol.empty:
        st.line_chart(evol.set_index('Mois')['Is_Repeat'], color="#004a99")

    # --- BOUTON EXCEL (En bas de la sidebar) ---
    st.sidebar.markdown("---")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_f.to_excel(writer, index=False)
    st.sidebar.download_button("📥 Télécharger Rapport Excel", buffer.getvalue(), "Arkeos_Export.xlsx")

else:
    st.error("Fichier de données absent sur GitHub.")
