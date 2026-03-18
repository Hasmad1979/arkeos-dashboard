import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px

# 1. CONFIGURATION
st.set_page_config(page_title="Arkeos Dashboard", layout="wide")

@st.cache_data
def load_data():
    # On définit le nom exact vu sur votre capture GitHub
    file_name = "data_dynamics_brute.csv.csv.csv"
    
    if not os.path.exists(file_name):
        st.error(f"Fichier {file_name} non trouvé à la racine du dépôt.")
        return None

    try:
        # Lecture robuste : Dynamics exporte souvent en UTF-16 avec des tabulations
        # sep=None avec engine='python' détecte automatiquement si c'est , ou ; ou tabulation
        df = pd.read_csv(file_name, sep=None, engine='python', encoding_errors='ignore')
        
        # Nettoyage radical des noms de colonnes
        df.columns = [str(c).strip() for c in df.columns]

        # Mapping flexible (on cherche les mots clés si le nom exact échoue)
        def find_and_rename(keywords, new_name):
            for col in df.columns:
                if any(k.lower() in col.lower() for k in keywords):
                    return col
            return None

        col_id = find_and_rename(["incident", "numéro"], "ID")
        col_sn = find_and_rename(["actif", "asset", "série"], "SN")
        col_tech = find_and_rename(["owner", "propriétaire", "technicien"], "Technicien")
        col_date = find_and_rename(["créé", "created", "date"], "Date")

        if not all([col_id, col_sn, col_tech, col_date]):
            st.error(f"Colonnes manquantes. Trouvées : ID={col_id}, SN={col_sn}, Tech={col_tech}, Date={col_date}")
            return None

        df = df.rename(columns={col_id: "ID", col_sn: "SN", col_tech: "Technicien", col_date: "Date"})
        
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
            
        df['Is_Repeat'] = df.apply(lambda r: 1 if 0 <= (calc_bus(r) or 999) <= 22 else 0, axis=1)
        return df
    except Exception as e:
        st.error(f"Erreur lors de la lecture : {e}")
        return None

df_raw = load_data()

if df_raw is not None:
    st.title("📊 Arkeos Technical Support")
    
    # Sidebar Filtres
    st.sidebar.header("Filtres")
    techs = ["Tous"] + sorted(df_raw['Technicien'].unique().tolist())
    sel_tech = st.sidebar.selectbox("Sélectionner un Technicien", techs)
    
    df_f = df_raw if sel_tech == "Tous" else df_raw[df_raw['Technicien'] == sel_tech]
    
    # KPIs
    c1, c2, c3 = st.columns(3)
    total = len(df_f)
    repeats = df_f['Is_Repeat'].sum()
    c1.metric("Interventions", f"{total:,}")
    c2.metric("Nombre de Repeats", f"{repeats:,}")
    c3.metric("Taux de Repeat", f"{(repeats/total*100):.1f}%" if total > 0 else "0%")
    
    # Graphique Simple
    df_f['Mois'] = df_f['Date'].dt.to_period('M').astype(str)
    evol = df_f.groupby('Mois')['Is_Repeat'].mean().reset_index()
    fig = px.line(evol, x='Mois', y='Is_Repeat', title="Evolution du Taux de Repeat")
    st.plotly_chart(fig, use_container_width=True)
