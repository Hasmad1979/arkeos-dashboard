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
    
    # Lecture du fichier
    df = pd.read_csv(file_name)
    
    # Mapping flexible pour éviter les KeyError
    # On cherche les colonnes par mots-clés si le nom exact change
    def find_col(keywords, default):
        for col in df.columns:
            if any(k.lower() in col.lower() for k in keywords):
                return col
        return default

    mapping = {
        find_col(["incident", "numéro"], "ID"): "ID",
        find_col(["actifs", "client", "sn"], "SN"): "SN",
        find_col(["owner", "technicien"], "Technicien"): "Technicien",
        find_col(["création", "créé le"], "Date_Debut"): "Date_Debut",
        find_col(["fin", "clôture"], "Date_Fin"): "Date_Fin",
        find_col(["type", "panne"], "Panne"): "Panne",
        find_col(["compte", "service"], "Compte"): "Compte"
    }
    
    df = df.rename(columns=mapping)
    
    # Nettoyage et conversion dates
    df['Date_Debut'] = pd.to_datetime(df['Date_Debut'], errors='coerce')
    df['Date_Fin'] = pd.to_datetime(df['Date_Fin'], errors='coerce')
    df = df.dropna(subset=['SN', 'Date_Debut'])

    # --- CALCULS HORS WEEKENDS ---
    def bus_mins(row):
        if pd.isnull(row['Date_Debut']) or pd.isnull(row['Date_Fin']): return 0
        try:
            # np.busday_count exclut les weekends
            d1, d2 = row['Date_Debut'].date(), row['Date_Fin'].date()
            if d1 > d2: return 0
            # Durée brute en minutes
            total_mins = (row['Date_Fin'] - row['Date_Debut']).total_seconds() / 60
            # On ne garde la durée que si elle est sur des jours ouvrés
            return total_mins if np.busday_count(d1, d2) >= 0 else 0
        except: return 0

    df['Duree_Mins'] = df.apply(bus_mins, axis=1)
    
    # Calcul Repeat (22 jours ouvrés)
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
    # --- FILTRES ---
    st.sidebar.title("🎮 Filtres")
    
    years = sorted(df_raw['Date_Debut'].dt.year.unique(), reverse=True)
    sel_years = st.sidebar.multiselect("Années", years, default=years)
    
    # Sécurité pour les filtres si colonnes manquantes
    def get_filter(col_name, label):
        if col_name in df_raw.columns:
            vals = sorted(df_raw[col_name].astype(str).unique())
            return st.sidebar.multiselect(label, vals, default=vals)
        return []

    sel_techs = get_filter('Technicien', "Techniciens")
    sel_comptes = get_filter('Compte', "Comptes de Service")

    # Application filtres
    mask = df_raw['Date_Debut'].dt.year.isin(sel_years)
    if sel_techs: mask &= df_raw['Technicien'].isin(sel_techs)
    if sel_comptes: mask &= df_raw['Compte'].isin(sel_comptes)
    df_f = df_raw[mask].copy()

    st.title("📊 Arkeos Support Dashboard")
    
    if not df_f.empty:
        # --- KPI ---
        total_int = len(df_f)
        total_rep = df_f['Is_Repeat'].sum()
        run_time_h = df_f['Duree_Mins'].sum() / 60
        avg_time_m = df_f['Duree_Mins'].mean()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Interventions", f"{total_int:,}")
        c2.metric("FTTR Rate", f"{(100 - (total_rep/total_int*100)):.1f}%")
        c3.metric("Run Time Total", f"{run_time_h:,.0f} h")
        c4.metric("Avg Time", f"{avg_time_m:.1f} min")

        # --- GRAPHIQUES ---
        st.markdown("---")
        col_l, col_r = st.columns(2)
        
        with col_l:
            st.subheader("🛠️ Top 10 Pannes (Repeats)")
            if 'Panne' in df_f.columns:
                top_p = df_f[df_f['Is_Repeat']==1].groupby('Panne').size().nlargest(10).reset_index(name='Nb')
                st.plotly_chart(px.bar(top_p, x='Nb', y='Panne', orientation='h', color_discrete_sequence=['#004a99']), use_container_width=True)

        with col_r:
            st.subheader("🏢 Impact par Compte")
            if 'Compte' in df_f.columns:
                top_c = df_f[df_f['Is_Repeat']==1].groupby('Compte').size().nlargest(10).reset_index(name='Nb')
                st.plotly_chart(px.bar(top_c, x='Nb', y='Compte', orientation='h', color_discrete_sequence=['#ff4b4b']), use_container_width=True)

        # Export Excel
        buffer = io.BytesIO()
        df_f[df_f['Is_Repeat']==1].to_excel(buffer, index=False)
        st.sidebar.markdown("---")
        st.sidebar.download_button("📥 Liste des Repeats (Excel)", buffer.getvalue(), "repeats_arkeos.xlsx")
    else:
        st.warning("Aucune donnée disponible pour cette sélection.")
else:
    st.error("Le fichier 'data_dynamics_brute.csv.csv' est introuvable sur votre GitHub.")
