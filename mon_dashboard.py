import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io

# 1. CONFIGURATION ET DESIGN
st.set_page_config(page_title="Arkeos Performance Pro", layout="wide")

st.markdown("""
    <style>
    /* Cartes KPI interactives */
    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 100px;
        border: 1px solid #e0e6ed;
        background-color: white;
        transition: all 0.3s;
    }
    div.stButton > button:hover {
        border-color: #1E3A8A;
        background-color: #f8fbff;
        transform: translateY(-3px);
    }
    </style>
    """, unsafe_allow_html=True)

# 2. CHARGEMENT ET TRAITEMENT DES DONNÉES
@st.cache_data
def load_data():
    file_path = "data_dynamics_brute.csv.csv"
    if not os.path.exists(file_path): return None
    df = pd.read_csv(file_path)
    
    # Nettoyage et Renommage
    df = df.rename(columns={
        "Actif client principal de l'incident": "Actif_SN",
        "Propriétaire": "Technicien",
        "Date de création": "Date",
        "Compte de service": "Compte"
    })
    
    # Forcer l'Actif en texte pour éviter les erreurs d'affichage
    df['Actif_SN'] = df['Actif_SN'].astype(str).str.replace(r'\.0$', '', regex=True)
    df = df[~df['Actif_SN'].isin(['nan', 'None', 'nan.0', ''])]
    
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    # Calcul du RDR (Repeat dans les 7 jours)
    df = df.sort_values(['Actif_SN', 'Date'])
    df['Diff'] = df.groupby('Actif_SN')['Date'].diff().dt.days
    df['Is_Repeat'] = (df['Diff'] <= 7).astype(int)
    
    # Dimensions temporelles
    df['Année'] = df['Date'].dt.year.astype(str)
    df['Mois'] = df['Date'].dt.strftime('%B')
    df['Semaine'] = df['Date'].dt.strftime('%Y-W%V')
    
    return df

df = load_data()

# 3. BARRE LATÉRALE : LOGO ET FILTRES
if df is not None:
    with st.sidebar:
        if os.path.exists("download.png"):
            st.image("download.png", use_container_width=True)
        
        st.markdown("---")
        st.header("🔍 Filtres")
        
        # Filtre Année et Mois
        years = sorted(df['Année'].unique(), reverse=True)
        sel_year = st.multiselect("Année", years, default=years[:1])
        
        months = ["January", "February", "March", "April", "May", "June", 
                  "July", "August", "September", "October", "November", "December"]
        avail_months = [m for m in months if m in df['Mois'].unique()]
        sel_month = st.multiselect("Mois", avail_months, default=avail_months)
        
        # Filtre Technicien
        techs = ["Tous"] + sorted(df['Technicien'].unique().tolist())
        sel_tech = st.selectbox("Technicien", techs)

    # Application des filtres
    mask = (df['Année'].isin(sel_year)) & (df['Mois'].isin(sel_month))
    if sel_tech != "Tous":
        mask &= (df['Technicien'] == sel_tech)
    df_f = df[mask]

    # 4. CALCULS DES KPI
    total_int = len(df_f)
    repeats = df_f['Is_Repeat'].sum()
    rdr_rate = (repeats / total_int * 100) if total_int > 0 else 0
    fttr_rate = 100 - rdr_rate

    # 5. AFFICHAGE DES KPI CLIQUABLES
    st.title("📊 Arkeos Support Technique Dashboard")
    
    if 'view' not in st.session_state:
        st.session_state.view = "Global"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button(f"Interventions\n{total_int:,}"): st.session_state.view = "Global"
    with c2:
        if st.button(f"RDR % (7j)\n{rdr_rate:.1f}%"): st.session_state.view = "RDR"
    with c3:
        if st.button(f"FTTR %\n{fttr_rate:.1f}%"): st.session_state.view = "Global"
    with c4:
        if st.button(f"Nb Repeats\n{repeats}"): st.session_state.view = "RDR"

    st.markdown("---")

    # 6. GRAPHIQUE DE TENDANCE (% PAR SEMAINE)
    st.subheader("📈 Tendance RDR % par Semaine (7j)")
    trend = df_f.groupby('Semaine')['Is_Repeat'].mean().reset_index()
    trend['RDR %'] = (trend['Is_Repeat'] * 100).round(1)
    
    fig_trend = px.line(trend, x='Semaine', y='RDR %', text='RDR %', markers=True,
                        color_discrete_sequence=['#1E3A8A'])
    fig_trend.update_traces(textposition="top center")
    st.plotly_chart(fig_trend, use_container_width=True)

    # 7. VUE DÉTAILLÉE (DYNAMIQUE AU CLIC)
    if st.session_state.view == "RDR":
        st.subheader("🚨 Analyse des Impacts (Repeats)")
        df_reps = df_f[df_f['Is_Repeat'] == 1]
        
        col_a, col_b = st.columns(2)
        with col_a:
            # Top Actifs sans 'nan'
            top_a = df_reps['Actif_SN'].value_counts().nlargest(10).reset_index()
            fig_a = px.bar(top_a, x='count', y='Actif_SN', orientation='h', title="Top 10 Actifs Critiques", color_discrete_sequence=['#E74C3C'])
            fig_a.update_layout(yaxis={'type': 'category', 'categoryorder': 'total ascending'})
            st.plotly_chart(fig_a, use_container_width=True)
            
        with col_b:
            st.write("📥 **Télécharger les données d'impact**")
            # Option pour télécharger les lignes de repeats en Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_reps.to_excel(writer, index=False, sheet_name='Repeats_Impact')
            st.download_button(
                label="Générer Rapport Excel (Repeats)",
                data=output.getvalue(),
                file_name="arkeos_impact_repeats.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

else:
    st.error("Données introuvables.")
