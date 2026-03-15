import streamlit as st
import pandas as pd
import plotly.express as px

# 1. NETTOYAGE STRICT DES DONNÉES
def clean_data(df):
    # Mapping des colonnes
    df = df.rename(columns={
        "Propriétaire": "Technicien",
        "Compte de service": "Compte",
        "Actif client principal de l'incident": "Actif_SN",
        "Date de création": "Date"
    })
    
    # --- LA CORRECTION : Forcer le format texte ---
    # On supprime les '.0' et on force en chaîne de caractères
    df['Actif_SN'] = df['Actif_SN'].astype(str).str.replace(r'\.0$', '', regex=True)
    
    # Suppression des lignes sans identifiant d'actif (inutilisables pour le RDR)
    df = df.dropna(subset=['Actif_SN'])
    return df

# 2. GRAPHIQUE CORRIGÉ
def plot_top_actifs(df_filtered):
    # On ne prend que les interventions marquées comme "Repeat"
    df_reps = df_filtered[df_filtered['Is_Repeat'] == 1]
    
    if not df_reps.empty:
        top_actifs = df_reps.groupby('Actif_SN').size().nlargest(10).reset_index(name='Nb')
        
        # fig_a : Barres horizontales avec identifiants réels
        fig = px.bar(top_actifs, x='Nb', y='Actif_SN', orientation='h',
                     title="Top 10 Actifs (Machines critiques)",
                     color_discrete_sequence=['#E74C3C'],
                     text='Nb')
        
        # On force l'axe Y à traiter les valeurs comme des noms (catégories)
        fig.update_layout(yaxis={'type': 'category', 'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
