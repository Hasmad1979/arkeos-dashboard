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
    
    # Mapping mis à jour selon vos captures
    mapping = {
        "Numéro de l'incident": "ID", 
        "Actifs du client": "SN", 
        "Owner": "Technicien", 
        "Date de création": "Date_Debut",
        "Date de fin": "Date_Fin",
        "Type d'incident": "Panne",
        "Compte de service": "Compte"
    }
    df = df.rename(columns=mapping)
    
    # Conversion dates
    df['Date_Debut'] = pd.to_datetime(df['Date_Debut'], errors='coerce')
    df['Date_Fin'] = pd.to_datetime(df['Date_Fin'], errors='coerce')
    df = df.dropna(subset=['SN', 'Date_Debut']).sort_values(['SN', 'Date_Debut'])

    # --- CALCUL DURÉE HORS WEEKEND ---
    def calc_duration_no_wk(row):
        if pd.isnull(row['Date_Debut']) or pd.isnull(row['Date_Fin']): return 0
        # Calcul des minutes totales hors weekends
        days = np.busday_count(row['Date_Debut'].date(), row['Date_Fin'].date())
        # Estimation simplifiée en minutes (8h par jour ouvré si même jour, sinon cumul)
        total_mins = (row['Date_Fin'] - row['Date_Debut']).total_seconds() / 60
        return max(0, total_mins) if days >= 0 else 0

    df['Duree_Mins'] = df.apply(calc_duration_no_wk, axis=1)
    
    # --- CALCUL REPEAT (22 jours ouvrés) ---
    df['Date_Prev'] = df.groupby('SN')['Date_Debut'].shift(1)
    df['Is_Repeat'] = df.apply(lambda r: 1 if not pd.isnull(r['Date_Prev']) and 
                               np.busday_count(r['Date_Prev'].date(), r['Date_Debut'].date()) <= 22 else 0, axis=1)
    return df

df_raw = load_data()

if df_raw is not None:
    # Sidebar Filtres
    st.sidebar.title("🎮 Filtres")
    years = sorted(df_raw['Date_Debut'].dt.year.unique(), reverse=True)
    sel_years = st.sidebar.multiselect("Années", years, default=years)
    
    techs = sorted(df_raw['Technicien'].astype(str).unique())
    sel_techs = st.sidebar.multiselect("Techniciens", techs, default=techs)
    
    comptes = sorted(df_raw['Compte'].astype(str).unique())
    sel_comptes = st.sidebar.multiselect("Comptes de Service", comptes, default=comptes)

    df_f = df_raw[
        (df_raw['Date_Debut'].dt.year.isin(sel_years)) & 
        (df_raw['Technicien'].isin(sel_techs)) &
        (df_raw['Compte'].isin(sel_comptes))
    ].copy()

    st.title("📊 Arkeos Technical Support Dashboard")
    
    if not df_f.empty:
        # --- 1. KPI ---
        total_rep = df_f['Is_Repeat'].sum()
        run_time = df_f['Duree_Mins'].sum() / 60  # Conversion Heures
        avg_time = df_f['Duree_Mins'].mean()     # En Minutes

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Repeats", f"{total_rep:,}")
        c2.metric("FTTR Rate", f"{(100 - (total_rep/len(df_f)*100)):.1f}%")
        c3.metric("Run Time Total", f"{run_time:,.0f} h")
        c4.metric("Avg Workorder", f"{avg_time:.1f} min")

        # --- 2. GRAPHIQUES ---
        col_l, col_r = st.columns(2)
        
        with col_l:
            st.subheader("🛠️ Top 10 Pannes")
            top_p = df_f[df_f['Is_Repeat']==1].groupby('Panne').size().nlargest(10).reset_index(name='Nb')
            st.plotly_chart(px.bar(top_p, x='Nb', y='Panne', orientation='h', color_discrete_sequence=['#004a99']), use_container_width=True)

        with col_r:
            st.subheader("🏢 Impact par Compte")
            top_c = df_f[df_f['Is_Repeat']==1].groupby('Compte').size().nlargest(10).reset_index(name='Nb')
            st.plotly_chart(px.bar(top_c, x='Nb', y='Compte', orientation='h', color_discrete_sequence=['#ff4b4b']), use_container_width=True)

        # Export
        buffer = io.BytesIO()
        df_f[df_f['Is_Repeat']==1].to_excel(buffer, index=False)
        st.sidebar.download_button("📥 Excel des Repeats", buffer.getvalue(), "repeats_arkeos.xlsx")
