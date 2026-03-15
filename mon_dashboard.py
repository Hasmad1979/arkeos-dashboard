import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io

# 1. CONFIGURATION ET DESIGN PROFESSIONNEL
# J'ai mis à jour le titre de la page pour refléter le changement
st.set_page_config(page_title="Arkeos Support Télécopieurs Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    /* Style des boutons KPI interactifs */
    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 100px;
        border: 1px solid #e2e8f0;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# 2. CHARGEMENT ET NETTOYAGE
@st.cache_data
def load_data():
    file_path = "data_dynamics_brute.csv.csv"
    if not os.path.exists(file_path): return None
    df = pd.read_csv(file_path)
    
    df = df.rename(columns={
        "Actif client principal de l'incident": "Actif_SN",
        "Propriétaire": "Technicien",
        "Date de création": "Date"
    })
    
    # Nettoyage des actifs 'nan'
    df['Actif_SN'] = df['Actif_SN'].astype(str).str.replace(r'\.0$', '', regex=False)
    df = df[~df['Actif_SN'].isin(['nan', 'None', ''])]
    
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    # Calcul RDR (Repeat 7j)
    df = df.sort_values(['Actif_SN', 'Date'])
    df['Is_Repeat'] = (df.groupby('Actif_SN')['Date'].diff().dt.days <= 7).astype(int)
    
    df['Année'] = df['Date'].dt.year.astype(str)
    df['Mois'] = df['Date'].dt.strftime('%B')
    df['Semaine'] = df['Date'].dt.strftime('%Y-W%V')
    
    return df

df = load_data()

# 3. SIDEBAR : FILTRES ET BOUTON EXPORT À GAUCHE
if df is not None:
    with st.sidebar:
        if os.path.exists("download.png"):
            st.image("download.png", use_container_width=True)
        
        st.header("🔍 Paramètres")
        
        sel_year = st.multiselect("Année", sorted(df['Année'].unique(), reverse=True), default=["2026"])
        
        month_order = ["January", "February", "March", "April", "May", "June", 
                       "July", "August", "September", "October", "November", "December"]
        avail_months = [m for m in month_order if m in df['Mois'].unique()]
        sel_month = st.multiselect("Mois", avail_months, default=avail_months)
        
        techs = ["Tous"] + sorted(df['Technicien'].unique().tolist())
        sel_tech = st.selectbox("Technicien", techs)
        
        st.markdown("---")
        # BOUTON D'EXPORTATION DANS LA SIDEBAR
        st.subheader("📥 Export")
        
        # Filtrage pour l'export (on exporte les repeats de la sélection actuelle)
        mask = (df['Année'].isin(sel_year)) & (df['Mois'].isin(sel_month))
        if sel_tech != "Tous": mask &= (df['Technicien'] == sel_tech)
        df_export = df[mask & (df['Is_Repeat'] == 1)]
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Impact_Repeats')
        
        st.download_button(
            label="📥 Télécharger les Repeats",
            data=output.getvalue(),
            file_name=f"Arkeos_Repeats_{sel_tech}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Télécharge uniquement les machines en 'Repeat' pour le technicien et la période choisis."
        )

    # 4. DASHBOARD PRINCIPAL
    df_f = df[mask]
    total = len(df_f)
    nb_reps = df_f['Is_Repeat'].sum()
    rdr = (nb_reps / total * 100) if total > 0 else 0
    fttr = 100 - rdr

    # --- CHANGEMENT ICI ---
    # J'ai remplacé l'icône de banque et le texte par un émoji télécopieur et un nouveau titre
    st.title("📠 Arkeos Performance Support Télécopieurs")
    
    # Cartes KPI
    c1, c2, c3, c4 = st.columns(4)
    c1.button(f"Interventions\n{total:,}")
    c2.button(f"RDR % (7j)\n{rdr:.1f}%")
    c3.button(f"FTTR %\n{fttr:.1f}%")
    c4.button(f"Nb Repeats\n{nb_reps}")

    st.divider()

    # Graphique de tendance
    st.subheader("📈 Tendance RDR % par Semaine")
    trend = df_f.groupby('Semaine')['Is_Repeat'].mean().reset_index()
    trend['RDR %'] = (trend['Is_Repeat'] * 100).round(1)
    
    fig = px.line(trend, x='Semaine', y='RDR %', text='RDR %', markers=True, color_discrete_sequence=['#1e3a8a'])
    fig.update_traces(textposition="top center")
    st.plotly_chart(fig, use_container_width=True)

    # Top 10 Actifs
    st.subheader("🚨 Top 10 Télécopieurs Critiques (Repeats)")
    top_assets = df_f[df_f['Is_Repeat'] == 1]['Actif_SN'].value_counts().nlargest(10).reset_index()
    # J'ai aussi mis à jour le titre de l'axe Y pour être plus clair
    fig_bar = px.bar(top_assets, x='count', y='Actif_SN', orientation='h', 
                    color_discrete_sequence=['#ef4444'],
                    labels={'Actif_SN': 'N° Série Télécopieur', 'count': 'Nombre de Repeats'})
    st.plotly_chart(fig_bar, use_container_width=True)

else:
    st.error("Données non trouvées.")
