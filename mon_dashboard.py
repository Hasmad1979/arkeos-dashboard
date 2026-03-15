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
    
    # Lecture (on force le séparateur virgule qui est standard pour les CSV)
    df = pd.read_csv(file_name)
    
    # SYSTEME DE DETECTION FLEXIBLE
    def find_col(keywords):
        for col in df.columns:
            if any(k.lower() in col.lower() for k in keywords):
                return col
        return None

    # On adapte le mapping à vos colonnes visibles sur l'image
    mapping = {
        find_col(["ordre", "trav"]): "ID",
        find_col(["actifs", "client", "sn", "produit"]): "SN", # Cherche SN ou Actifs
        find_col(["propriétaire", "owner"]): "Technicien",
        find_col(["création"]): "Date_Debut",
        find_col(["fin"]): "Date_Fin",
        find_col(["incident", "type"]): "Panne",
        find_col(["compte", "service"]): "Compte"
    }
    
    df = df.rename(columns={k: v for k, v in mapping.items() if k is not None})
    
    # SECURITÉ : Si 'SN' n'est pas trouvé, on utilise 'ID' pour ne pas faire planter l'app
    if "SN" not in df.columns:
        if "ID" in df.columns:
            df["SN"] = df["ID"] 
        else:
            return pd.DataFrame()

    # Nettoyage et conversion
    for c in ['Date_Debut', 'Date_Fin']:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors='coerce')
    
    df = df.dropna(subset=['Date_Debut'])

    # --- CALCUL RUN TIME (EN MINUTES) ---
    def bus_mins(row):
        if pd.isnull(row.get('Date_Debut')) or pd.isnull(row.get('Date_Fin')): return 0
        try:
            diff = (row['Date_Fin'] - row['Date_Debut']).total_seconds() / 60
            return max(0, diff)
        except: return 0

    df['Duree_Mins'] = df.apply(bus_mins, axis=1)
    
    # --- CALCUL REPEAT (Logique simplifiée) ---
    df = df.sort_values(['SN', 'Date_Debut'])
    df['Is_Repeat'] = df.groupby('SN')['Date_Debut'].diff().dt.days.le(22).astype(int)
    
    return df

df_raw = load_data()

# --- AFFICHAGE ---
if df_raw is not None and not df_raw.empty:
    st.title("📊 Arkeos Support Dashboard")
    
    # KPI
    total_int = len(df_raw)
    total_rep = df_raw['Is_Repeat'].sum()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Interventions", f"{total_int:,}")
    c2.metric("Taux Repeat", f"{(total_rep/total_int*100):.1f}%")
    c3.metric("Run Time Total", f"{(df_raw['Duree_Mins'].sum()/60):,.0f} h")
    c4.metric("Délai Moyen", f"{df_raw['Duree_Mins'].mean():.1f} min")

    # Graphiques
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🛠️ Top Pannes")
        if 'Panne' in df_raw.columns:
            top_p = df_raw.groupby('Panne').size().nlargest(10).reset_index(name='Nb')
            st.plotly_chart(px.bar(top_p, x='Nb', y='Panne', orientation='h'), use_container_width=True)

    with col2:
        st.subheader("👨‍🔧 Top Techniciens")
        if 'Technicien' in df_raw.columns:
            top_t = df_raw.groupby('Technicien').size().nlargest(10).reset_index(name='Nb')
            st.plotly_chart(px.bar(top_t, x='Nb', y='Technicien', orientation='h'), use_container_width=True)

    # Export
    buffer = io.BytesIO()
    df_raw.to_excel(buffer, index=False)
    st.sidebar.download_button("📥 Télécharger les données", buffer.getvalue(), "data_arkeos.xlsx")

else:
    st.error("Erreur : Le fichier CSV ne contient pas les colonnes attendues ou est mal formaté.")
