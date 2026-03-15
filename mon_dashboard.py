import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import plotly.express as px

# Configuration
st.set_page_config(page_title="Arkeos Support Dashboard", layout="wide")

@st.cache_data
def load_data():
    file_name = "data_dynamics_brute.csv.csv" 
    if not os.path.exists(file_name):
        return None
    
    df = pd.read_csv(file_name)
    
    # Système de détection automatique des colonnes pour éviter les KeyError
    def find_col(keywords):
        for col in df.columns:
            if any(k.lower() in col.lower() for k in keywords):
                return col
        return None

    # Mapping basé sur vos dernières captures d'écran
    mapping = {
        find_col(["ordre", "incident"]): "ID",
        find_col(["actifs", "client", "sn"]): "SN",
        find_col(["propriétaire", "owner"]): "Technicien",
        find_col(["création", "créé le"]): "Date_Debut",
        find_col(["fin", "clôture"]): "Date_Fin",
        find_col(["type", "panne"]): "Panne",
        find_col(["compte", "service"]): "Compte"
    }
    
    mapping = {k: v for k, v in mapping.items() if k is not None}
    df = df.rename(columns=mapping)
    
    # Conversion dates
    for col in ['Date_Debut', 'Date_Fin']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    df = df.dropna(subset=['SN', 'Date_Debut'])

    # --- CALCUL RUN TIME HORS WEEKENDS ---
    def bus_mins(row):
        if pd.isnull(row.get('Date_Debut')) or pd.isnull(row.get('Date_Fin')): return 0
        try:
            d1, d2 = row['Date_Debut'].date(), row['Date_Fin'].date()
            if d1 > d2: return 0
            total_mins = (row['Date_Fin'] - row['Date_Debut']).total_seconds() / 60
            return total_mins if np.busday_count(d1, d2) >= 0 else 0
        except: return 0

    df['Duree_Mins'] = df.apply(bus_mins, axis=1)
    
    # --- CALCUL REPEAT (22 jours ouvrés) ---
    df = df.sort_values(['SN', 'Date_Debut'])
    df['Date_Prev'] = df.groupby('SN')['Date_Debut'].shift(1)
    
    def check_repeat(row):
        if pd.isnull(row['Date_Prev']): return 0
        try:
            diff = np.busday_count(row['Date_Prev'].date(), row['Date_Debut'].date())
            return 1 if 0 <= diff <= 22 else 0
        except: return 0
        
    df['Is_Repeat'] = df.apply(check_repeat, axis=1)
    return df

df_raw = load_data()

if df_raw is not None:
    st.title("📊 Arkeos Technical Support Dashboard")
    
    if not df_raw.empty:
        # --- KPI ---
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Interventions", f"{len(df_raw):,}")
        c2.metric("Total Repeats", f"{df_raw['Is_Repeat'].sum():,}")
        c3.metric("Run Time Total", f"{(df_raw['Duree_Mins'].sum()/60):,.0f} h")
        c4.metric("Avg Time", f"{df_raw['Duree_Mins'].mean():.1f} min")

        # --- GRAPHIQUES ---
        st.markdown("---")
        col_l, col_r = st.columns(2)
        
        with col_l:
            st.subheader("🛠️ Top 10 Pannes")
            if 'Panne' in df_raw.columns:
                top_p = df_raw[df_raw['Is_Repeat']==1].groupby('Panne').size().nlargest(10).reset_index(name='Nb')
                st.plotly_chart(px.bar(top_p, x='Nb', y='Panne', orientation='h'), use_container_width=True)

        with col_r:
            st.subheader("🏢 Impact par Compte")
            if 'Compte' in df_raw.columns:
                top_c = df_raw[df_raw['Is_Repeat']==1].groupby('Compte').size().nlargest(10).reset_index(name='Nb')
                st.plotly_chart(px.bar(top_c, x='Nb', y='Compte', orientation='h'), use_container_width=True)

        # Export Excel
        buffer = io.BytesIO()
        df_raw[df_raw['Is_Repeat']==1].to_excel(buffer, index=False)
        st.sidebar.download_button("📥 Télécharger les Repeats", buffer.getvalue(), "repeats.xlsx")
else:
    st.error("Fichier de données introuvable sur GitHub.")
