import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px

# 1. CONFIGURATION
st.set_page_config(page_title="Arkeos Dashboard", layout="wide")

@st.cache_data
def load_data():
    # Liste de tous les noms de fichiers vus sur votre GitHub
    possibilites = [
        "data_dynamics_brute.csv.csv.csv",
        "data_dynamics_brute.csv.csv",
        "data_dynamics_brute.csv"
    ]
    
    file_to_load = None
    for p in possibilites:
        if os.path.exists(p):
            file_to_load = p
            break
            
    if not file_to_load:
        return None

    try:
        # Lecture flexible pour Dynamics (gère virgule ou point-virgule)
        df = pd.read_csv(file_to_load, sep=None, engine='python', on_bad_lines='skip')
        
        # Nettoyage des colonnes (supprime les espaces invisibles)
        df.columns = [str(c).strip() for c in df.columns]

        # Mapping flexible
        mapping = {
            "Numéro de l'incident": "ID", "Incident Number": "ID",
            "Actifs du client": "SN", "Customer Asset": "SN",
            "Owner": "Technicien", "Propriétaire": "Technicien",
            "Créé le": "Date", "Created On": "Date"
        }
        df = df.rename(columns=mapping)
        
        # Conversion Date
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['SN', 'Date']).sort_values(['SN', 'Date'])
        
        # Calcul Repeat (22 jours ouvrés)
        df['Date_Prev'] = df.groupby('SN')['Date'].shift(1)
        def calc_bus(row):
            if pd.isnull(row['Date_Prev']): return None
            try:
                d1, d2 = row['Date_Prev'].date(), row['Date'].date()
                return int(np.busday_count(d1, d2)) if d1 < d2 else 0
            except: return 0
        df['Is_Repeat'] = df.apply(lambda r: 1 if 0 <= calc_bus(r) <= 22 else 0, axis=1)
        return df
    except Exception as e:
        st.error(f"Erreur de lecture : {e}")
        return None

df = load_data()

if df is not None:
    st.title("📊 Arkeos Technical Support")
    
    # Filtres
    techs = ["Tous"] + sorted(df['Technicien'].unique().tolist())
    sel_tech = st.sidebar.selectbox("Technicien", techs)
    
    df_f = df if sel_tech == "Tous" else df[df['Technicien'] == sel_tech]
    
    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Interventions", len(df_f))
    c2.metric("Repeats", df_f['Is_Repeat'].sum())
    rate = (df_f['Is_Repeat'].sum() / len(df_f) * 100) if len(df_f) > 0 else 0
    c3.metric("Taux de Repeat", f"{rate:.1f}%")
    
    # Graphique
    fig = px.histogram(df_f, x=df_f['Date'].dt.month, title="Interventions par mois")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("⚠️ Fichier introuvable. Vérifiez que le fichier est bien à la racine de votre GitHub.")
