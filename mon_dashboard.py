import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import plotly.express as px

# Configuration de la page
st.set_page_config(page_title="Arkeos Support Dashboard", layout="wide")

@st.cache_data
def load_data():
    file_name = "data_dynamics_brute.csv.csv" 
    if not os.path.exists(file_name):
        return None
    
    # Lecture du fichier
    df = pd.read_csv(file_name)
    
    # Système de détection automatique des colonnes (évite les KeyError)
    def find_col(keywords):
        for col in df.columns:
            if any(k.lower() in col.lower() for k in keywords):
                return col
        return None

    # Mapping basé sur vos images (ex: 'Actifs du client' devient 'SN')
    mapping = {
        find_col(["ordre de travail"]): "ID",
        find_col(["actifs du client"]): "SN",
        find_col(["propriétaire", "owner"]): "Technicien",
        find_col(["date de création"]): "Date_Debut",
        find_col(["date de fin"]): "Date_Fin",
        find_col(["type d'incident"]): "Panne",
        find_col(["compte de service"]): "Compte"
    }
    
    # On renomme et on nettoie
    mapping = {k: v for k, v in mapping.items() if k is not None}
    df = df.rename(columns=mapping)
    
    # Sécurité : Si les colonnes vitales manquent, on arrête proprement
    if "SN" not in df.columns or "Date_Debut" not in df.columns:
        return pd.DataFrame()

    # Conversion des dates
    df['Date_Debut'] = pd.to_datetime(df['Date_Debut'], errors='coerce')
    df['Date_Fin'] = pd.to_datetime(df['Date_Fin'], errors='coerce')
    df = df.dropna(subset=['SN', 'Date_Debut'])

    # --- CALCUL RUN TIME (HORS WEEKENDS) ---
    def bus_mins(row):
        if pd.isnull(row['Date_Debut']) or pd.isnull(row['Date_Fin']): return 0
        try:
            d1, d2 = row['Date_Debut'].date(), row['Date_Fin'].date()
            if d1 > d2: return 0
            total_mins = (row['Date_Fin'] - row['Date_Debut']).total_seconds() / 60
            # np.busday_count renvoie 0 ou plus si c'est un jour ouvré
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

df_f = load_data()

# --- AFFICHAGE ---
if not df_f.empty:
    st.title("📊 Arkeos Support Dashboard")
    
    # KPI
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interventions", f"{len(df_f):,}")
    c2.metric("Total Repeats", f"{df_f['Is_Repeat'].sum():,}")
    c3.metric("Run Time Total", f"{(df_f['Duree_Mins'].sum()/60):,.0f} h")
    c4.metric("Avg Time", f"{df_f['Duree_Mins'].mean():.1f} min")

    # Graphiques
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👨‍🔧 Top 10 Techniciens")
        if "Technicien" in df_f.columns:
            top_t = df_f.groupby("Technicien").size().nlargest(10).reset_index(name="Nb")
            st.plotly_chart(px.bar(top_t, x="Nb", y="Technicien", orientation='h'), use_container_width=True)

    with col2:
        st.subheader("📠 Top 10 Machines (SN)")
        top_s = df_f.groupby("SN").size().nlargest(10).reset_index(name="Nb")
        st.plotly_chart(px.bar(top_s, x="Nb", y="SN", orientation='h', color_discrete_sequence=['#ff4b4b']), use_container_width=True)

    # Export Excel
    buffer = io.BytesIO()
    df_f[df_f['Is_Repeat']==1].to_excel(buffer, index=False)
    st.sidebar.download_button("📥 Liste des Repeats", buffer.getvalue(), "repeats.xlsx")

else:
    st.error("Impossible de lire les données. Vérifiez que les colonnes 'Actifs du client' et 'Date de création' existent bien.")
