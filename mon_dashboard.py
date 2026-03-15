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
    
    df = pd.read_csv(file_name)
    
    # Mapping dynamique basé sur vos nouvelles colonnes
    # On cherche les colonnes par mots-clés pour éviter les KeyError
    def find_col(keywords):
        for col in df.columns:
            if any(k.lower() in col.lower() for k in keywords):
                return col
        return None

    mapping = {
        find_col(["ordre de travail", "incident"]): "ID",
        find_col(["actifs", "client", "sn"]): "SN",
        find_col(["propriétaire", "owner"]): "Technicien",
        find_col(["création", "créé le"]): "Date_Debut",
        find_col(["fin", "clôture"]): "Date_Fin",
        find_col(["type d'incident principal", "panne"]): "Panne",
        find_col(["compte de service"]): "Compte"
    }
    
    mapping = {k: v for k, v in mapping.items() if k is not None}
    df = df.rename(columns=mapping)
    
    # Conversion dates
    for col in ['Date_Debut', 'Date_Fin']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Suppression des lignes sans identifiant ou date
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
    
    # --- KPI ---
    if not df_raw.empty:
        total_int = len(df_raw)
        total_rep = df_raw['Is_Repeat'].sum()
        run_time_h = df_raw['Duree_Mins'].sum() / 60
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Interventions", f"{total_int:,}")
        c2.metric("Total Repeats", f"{total_rep:,}")
        c3.metric("Taux Repeat", f"{(total_rep/total_int*100):.1f}%")
        c4.metric("Run Time Total", f"{run_time_h:,.0f} h")

        # --- GRAPHIQUE ÉVOLUTION (Correction SyntaxError) ---
        st.markdown("---")
        st.subheader("📈 Évolution Mensuelle du Taux de Repeat")
        df_raw['Mois'] = df_raw['Date_Debut'].dt.to_period('M').astype(str)
        evol = df_raw.groupby('Mois')['Is_Repeat'].mean().reset_index()
        evol['Is_Repeat'] = evol['Is_Repeat'] * 100
        
        fig_evol = px.line(evol, x='Mois', y='Is_Repeat', markers=True, 
                           labels={'Is_Repeat': 'Taux de Repeat (%)'})
        st.plotly_chart(fig_evol, use_container_width=True)

        # --- IMPACT PAR COMPTE ---
        st.markdown("---")
        if 'Compte' in df_raw.columns:
            st.subheader("🏢 Impact par Compte de Service")
            top_c = df_raw[df_raw['Is_Repeat']==1].groupby('Compte').size().nlargest(10).reset_index(name='Nb')
            fig_c = px.bar(top_c, x='Nb', y='Compte', orientation='h', color_discrete_sequence=['#ff4b4b'])
            st.plotly_chart(fig_c, use_container_width=True)

        # Export Excel
        buffer = io.BytesIO()
        df_raw[df_raw['Is_Repeat']==1].to_excel(buffer, index=False)
        st.sidebar.download_button("📥 Liste des Repeats", buffer.getvalue(), "repeats.xlsx")
else:
    st.error("Fichier de données introuvable. Vérifiez la présence de 'data_dynamics_brute.csv.csv'.")
