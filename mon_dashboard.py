import streamlit as st
import pandas as pd
import numpy as np
import os
import io

# 1. Configuration
st.set_page_config(page_title="Arkeos Performance", layout="wide")

# 2. Chargement des données sécurisé
@st.cache_data
def load_data():
    file_name = "data_dynamics_brute.csv.csv"
    if not os.path.exists(file_name):
        return None
    
    df = pd.read_csv(file_name)
    # Nettoyage des noms
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

# --- INTERFACE ---
df_raw = load_data()

if df_raw is not None:
    st.title("📊 Arkeos Support Performance")
    
    # Filtres Sidebar
    st.sidebar.header("Filtres")
    years = sorted(df_raw['Date'].dt.year.unique(), reverse=True)
    sel_years = st.sidebar.multiselect("Années", years, default=years)
    
    df_f = df_raw[df_raw['Date'].dt.year.isin(sel_years)]
    
    # KPI
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Interventions", f"{len(df_f)}")
    c2.metric("Total Repeats", f"{df_f['Is_Repeat'].sum()}")
    c3.metric("Taux de Repeat", f"{(df_f['Is_Repeat'].mean()*100):.1f}%")

    # Graphique (Correction pour éviter l'aide Streamlit)
    st.subheader("📈 Évolution Mensuelle")
    df_f['Mois'] = df_f['Date'].dt.strftime('%m - %B') # Tri alphabétique facilité
    evol = df_f.groupby('Mois')['Is_Repeat'].mean() * 100
    
    if not evol.empty:
        st.line_chart(evol, color="#004a99")
    else:
        st.info("Sélectionnez une année pour voir l'évolution.")

    # Export
    st.sidebar.markdown("---")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_f.to_excel(writer, index=False)
    st.sidebar.download_button("📥 Télécharger Rapport Excel", buffer.getvalue(), "Arkeos_Export.xlsx")

else:
    st.error("Fichier de données absent sur GitHub. Vérifiez que 'data_dynamics_brute.csv.csv' est bien téléversé.")
