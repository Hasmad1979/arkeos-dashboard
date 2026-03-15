import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import plotly.express as px

# 1. CONFIGURATION
st.set_page_config(page_title="Arkeos Technical Support Dashboard", layout="wide")

@st.cache_data
def load_data():
    file_name = "data_dynamics_brute.csv.csv" 
    if not os.path.exists(file_name):
        return None
    df = pd.read_csv(file_name)
    
    # On définit explicitement les colonnes cibles
    mapping = {
        "Numéro de l'incident": "ID", 
        "Actifs du client": "SN", 
        "Owner": "Technicien", 
        "Créé le": "Date",
        "Type d'incident": "Panne" 
    }
    df = df.rename(columns=mapping)
    
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['SN', 'Date']).sort_values(['SN', 'Date'])
    
    # Calcul Repeat
    df['Date_Prev'] = df.groupby('SN')['Date'].shift(1)
    def calc_bus(row):
        if pd.isnull(row['Date_Prev']): return None
        try:
            d1, d2 = row['Date_Prev'].date(), row['Date'].date()
            return int(np.busday_count(d1, d2)) if d1 < d2 else 0
        except: return 0
    df['Ecart_Ouvres'] = df.apply(calc_bus, axis=1)
    df['Is_Repeat'] = ((df['Ecart_Ouvres'] >= 0) & (df['Ecart_Ouvres'] <= 22)).astype(int)
    return df

df_raw = load_data()

if df_raw is not None:
    # --- FILTRES ---
    st.sidebar.title("🎮 Filtres")
    years = sorted(df_raw['Date'].dt.year.unique(), reverse=True)
    sel_years = st.sidebar.multiselect("Années", years, default=years)
    
    # Utilisation sécurisée de la colonne Panne dans les filtres
    col_panne = "Panne" if "Panne" in df_raw.columns else "Type d'incident"
    
    df_f = df_raw[df_raw['Date'].dt.year.isin(sel_years)].copy()

    # --- DASHBOARD ---
    st.title("📊 Arkeos Technical Support Dashboard")
    
    if not df_f.empty:
        # KPI
        total_int = len(df_f)
        total_rep = df_f['Is_Repeat'].sum()
        repeat_rate = (total_rep / total_int * 100) if total_int > 0 else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Interventions", f"{total_int:,}")
        c2.metric("Total Repeats", f"{total_rep:,}")
        c3.metric("Taux de Repeat", f"{repeat_rate:.1f}%")
        c4.metric("FTTR Rate", f"{100 - repeat_rate:.1f}%")

        # GRAPHIQUES
        col_left, col_right = st.columns(2)
        
        with col_left:
            with st.container(border=True):
                st.subheader("🛠️ Top 10 Types de Panne")
                # VÉRIFICATION DE SÉCURITÉ ICI
                if "Panne" in df_f.columns:
                    top_p = df_f[df_f['Is_Repeat'] == 1].groupby("Panne").size().reset_index(name='Repeats')
                    top_p = top_p.sort_values(by='Repeats', ascending=True).tail(10)
                    fig_p = px.bar(top_p, x='Repeats', y='Panne', orientation='h', color_discrete_sequence=['#004a99'])
                    st.plotly_chart(fig_p, use_container_width=True)
                else:
                    st.error("Colonne 'Type d'incident' non trouvée dans le fichier.")

        with col_right:
            with st.container(border=True):
                st.subheader("📁 Top 10 Machines (SN)")
                top_sn = df_f[df_f['Is_Repeat'] == 1].groupby('SN').size().reset_index(name='Repeats')
                top_sn = top_sn.sort_values(by='Repeats', ascending=True).tail(10)
                fig_s = px.bar(top_sn, x='Repeats', y='SN', orientation='h', color_discrete_sequence=['#ff4b4b'])
                st.plotly_chart(fig_s, use_container_width=True)

    else:
        st.warning("Aucune donnée disponible.")
else:
    st.error("Le fichier CSV est introuvable sur GitHub.")
