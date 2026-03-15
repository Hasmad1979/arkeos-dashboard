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
    
    # Détection automatique intelligente des colonnes (évite les KeyError)
    def find_col(keywords):
        for col in df.columns:
            if any(k.lower() in col.lower() for k in keywords):
                return col
        return None

    mapping = {
        find_col(["ordre", "incident"]): "ID",
        find_col(["actifs", "client", "sn"]): "SN",
        find_col(["propriétaire", "owner"]): "Technicien",
        find_col(["création", "créé le"]): "Date_Debut",
        find_col(["fin", "clôture", "terminé"]): "Date_Fin",
        find_col(["type", "panne"]): "Panne",
        find_col(["compte", "service"]): "Compte"
    }
    
    # Nettoyage du mapping et renommage
    mapping = {k: v for k, v in mapping.items() if k is not None}
    df = df.rename(columns=mapping)
    
    # Conversion dates
    for c in ['Date_Debut', 'Date_Fin']:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors='coerce')
    
    # Utilisation des colonnes renommées pour le nettoyage
    if 'SN' in df.columns and 'Date_Debut' in df.columns:
        df = df.dropna(subset=['SN', 'Date_Debut'])
    else:
        st.error("Colonnes critiques (SN ou Date) introuvables dans le fichier.")
        return pd.DataFrame()

    # --- CALCUL RUN TIME (HORS WEEKENDS) ---
    def bus_mins(row):
        if pd.isnull(row.get('Date_Debut')) or pd.isnull(row.get('Date_Fin')): return 0
        try:
            d1, d2 = row['Date_Debut'].date(), row['Date_Fin'].date()
            if d1 > d2: return 0
            total_mins = (row['Date_Fin'] - row['Date_Debut']).total_seconds() / 60
            return total_mins if np.busday_count(d1, d2) >= 0 else 0
        except: return 0

    df['Duree_Mins'] = df.apply(bus_mins, axis=1)
    
    # --- CALCUL REPEAT (22 JOURS OUVRÉS) ---
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

# --- INTERFACE ---
if df_raw is not None and not df_raw.empty:
    st.title("📊 Arkeos Support Dashboard")
    st.markdown("---")

    # KPI principaux
    total_int = len(df_raw)
    total_rep = df_raw['Is_Repeat'].sum()
    run_time_h = df_raw['Duree_Mins'].sum() / 60

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interventions", f"{total_int:,}")
    c2.metric("Taux Repeat", f"{(total_rep/total_int*100):.1f}%")
    c3.metric("Run Time Total", f"{run_time_h:,.0f} h")
    c4.metric("Avg Time", f"{df_raw['Duree_Mins'].mean():.1f} min")

    # Graphiques
    st.write("")
    col_l, col_r = st.columns(2)
    
    with col_l:
        st.subheader("🛠️ Top 10 Pannes (Repeats)")
        if 'Panne' in df_raw.columns:
            top_p = df_raw[df_raw['Is_Repeat']==1].groupby('Panne').size().nlargest(10).reset_index(name='Nb')
            st.plotly_chart(px.bar(top_p, x='Nb', y='Panne', orientation='h'), use_container_width=True)

    with col_r:
        st.subheader("🏢 Impact par Compte")
        if 'Compte' in df_raw.columns:
            top_c = df_raw[df_raw['Is_Repeat']==1].groupby('Compte').size().nlargest(10).reset_index(name='Nb')
            st.plotly_chart(px.bar(top_c, x='Nb', y='Compte', orientation='h'), use_container_width=True)

    # Export
    buffer = io.BytesIO()
    df_raw[df_raw['Is_Repeat']==1].to_excel(buffer, index=False)
    st.sidebar.download_button("📥 Liste des Repeats", buffer.getvalue(), "repeats.xlsx")

elif df_raw is not None:
    st.warning("Le fichier a été chargé mais semble vide.")
else:
    st.error("Fichier 'data_dynamics_brute.csv.csv' introuvable.")
