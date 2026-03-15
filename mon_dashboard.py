import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Arkeos Support", layout="wide")

# Chargement sécurisé
@st.cache_data
def load_and_clean():
    file_path = "data_dynamics_brute.csv.csv"
    if not os.path.exists(file_path):
        return None
    
    df = pd.read_csv(file_path)
    
    # Renommage pour plus de clarté
    df = df.rename(columns={
        "Actif client principal de l'incident": "Actif_SN",
        "Propriétaire": "Technicien",
        "Date de création": "Date"
    })

    # NETTOYAGE DES "nan"
    df['Actif_SN'] = df['Actif_SN'].astype(str).str.replace(r'\.0$', '', regex=True)
    df = df[~df['Actif_SN'].isin(['nan', 'None', 'nan.0'])]
    
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Semaine'] = df['Date'].dt.strftime('%Y-W%V')
    
    return df

df = load_and_clean()

if df is not None:
    # Sidebar avec Logo et Filtres
    with st.sidebar:
        if os.path.exists("download.png"):
            st.image("download.png")
        st.header("🔍 Filtres")
        sel_tech = st.selectbox("Technicien", ["Tous"] + sorted(df['Technicien'].unique().tolist()))

    # Filtrage
    df_f = df if sel_tech == "Tous" else df[df['Technicien'] == sel_tech]

    # Dashboard
    st.title("📊 Arkeos Support Technique")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📠 Top 10 Actifs (Sans nan)")
        # On affiche uniquement les actifs réels
        top_data = df_f['Actif_SN'].value_counts().nlargest(10).reset_index()
        top_data.columns = ['Actif_SN', 'Nombre']
        fig = px.bar(top_data, x='Nombre', y='Actif_SN', orientation='h', 
                     color_discrete_sequence=['#E74C3C'])
        fig.update_layout(yaxis={'type': 'category', 'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📈 Tendance hebdomadaire")
        trend = df_f.groupby('Semaine').size().reset_index(name='Interventions')
        st.line_chart(trend.set_index('Semaine'))

else:
    st.error("Fichier de données manquant ou corrompu.")
