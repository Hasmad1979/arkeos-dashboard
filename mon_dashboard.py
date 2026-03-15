import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io

# 1. CONFIGURATION ET DESIGN CORPORATE
st.set_page_config(page_title="Arkeos Performance Dashboard", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #F1F5F9; }
    /* Style des cartes KPI cliquables */
    div.stButton > button {
        width: 100%;
        border-radius: 15px;
        height: 110px;
        border: 1px solid #CBD5E1;
        background-color: white;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    div.stButton > button:hover {
        border-color: #1E3A8A;
        transform: translateY(-3px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    /* Personnalisation de la barre latérale */
    section[data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E2E8F0; }
    </style>
    """, unsafe_allow_html=True)

# 2. CHARGEMENT ET NETTOYAGE DES DONNÉES
@st.cache_data
def load_data():
    file_path = "data_dynamics_brute.csv.csv"
    if not os.path.exists(file_path): return None
    df = pd.read_csv(file_path)
    
    # Nettoyage et mapping
    df = df.rename(columns={
        "Actif client principal de l'incident": "Actif_SN",
        "Propriétaire": "Technicien",
        "Date de création": "Date",
        "Compte de service": "Compte"
    })
    
    # Correction des valeurs 'nan' et formats numériques
    df['Actif_SN'] = df['Actif_SN'].astype(str).str.replace(r'\.0$', '', regex=True)
    df = df[~df['Actif_SN'].isin(['nan', 'None', '', 'nan.0'])]
    df = df[~df['Compte'].isin(['nan', 'None', ''])]
    
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    # Calcul RDR (Repeat 7 jours)
    df = df.sort_values(['Actif_SN', 'Date'])
    df['Is_Repeat'] = (df.groupby('Actif_SN')['Date'].diff().dt.days <= 7).astype(int)
    
    df['Année'] = df['Date'].dt.year.astype(str)
    df['Mois'] = df['Date'].dt.strftime('%B')
    df['Semaine'] = df['Date'].dt.strftime('%Y-W%V')
    
    return df

df = load_data()

# 3. BARRE LATÉRALE : FILTRES ET EXPORT
if df is not None:
    with st.sidebar:
        if os.path.exists("download.png"):
            st.image("download.png", use_container_width=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.header("🔍 Paramètres")
        
        sel_year = st.multiselect("Année", sorted(df['Année'].unique(), reverse=True), default=["2026"])
        
        month_order = ["January", "February", "March", "April", "May", "June", 
                       "July", "August", "September", "October", "November", "December"]
        avail_months = [m for m in month_order if m in df['Mois'].unique()]
        sel_month = st.multiselect("Mois", avail_months, default=avail_months)
        
        techs = ["Tous"] + sorted(df['Technicien'].unique().tolist())
        sel_tech = st.selectbox("Technicien", techs)
        
        st.markdown("---")
        # BOUTON EXPORT À GAUCHE
        st.subheader("📥 Exportation")
        
        mask = (df['Année'].isin(sel_year)) & (df['Mois'].isin(sel_month))
        if sel_tech != "Tous": mask &= (df['Technicien'] == sel_tech)
        df_f = df[mask]
        
        df_rep_only = df_f[df_f['Is_Repeat'] == 1]
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_rep_only.to_excel(writer, index=False, sheet_name='Repeats_Impact')
        
        st.download_button(
            label="📥 Télécharger les Repeats",
            data=output.getvalue(),
            file_name=f"Arkeos_Impact_{sel_tech}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Télécharge la liste des machines critiques pour la sélection actuelle."
        )

    # 4. DASHBOARD PRINCIPAL
    total = len(df_f)
    nb_reps = df_f['Is_Repeat'].sum()
    rdr = (nb_reps / total * 100) if total > 0 else 0
    fttr = 100 - rdr

    st.title("🏛️ Support Technique Performance")
    
    # Indicateurs KPI Clairs
    c1, c2, c3, c4 = st.columns(4)
    c1.button(f"Interventions\n{total:,}")
    c2.button(f"RDR % (7j)\n{rdr:.1f}%")
    c3.button(f"FTTR %\n{fttr:.1f}%")
    c4.button(f"Nb Repeats\n{nb_reps}")

    st.divider()

    # 5. GRAPHIQUE DE TENDANCE
    st.subheader("📈 Tendance RDR % par Semaine")
    trend = df_f.groupby('Semaine')['Is_Repeat'].mean().reset_index()
    trend['RDR %'] = (trend['Is_Repeat'] * 100).round(1)
    
    fig_trend = px.line(trend, x='Semaine', y='RDR %', text='RDR %', markers=True,
                        color_discrete_sequence=['#1E3A8A'], height=400)
    fig_trend.update_traces(textposition="top center")
    fig_trend.update_layout(plot_bgcolor='white', margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_trend, use_container_width=True)

    # 6. ANALYSE DES IMPACTS : CÔTE À CÔTE
    st.subheader("🚨 Analyse des Sites et Machines Critiques")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        # Top Actifs sans 'nan'
        top_assets = df_rep_only['Actif_SN'].value_counts().nlargest(10).reset_index()
        fig_assets = px.bar(top_assets, x='count', y='Actif_SN', orientation='h',
                            title="Top 10 Actifs (Machines)", color_discrete_sequence=['#EF4444'])
        fig_assets.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor='white')
        st.plotly_chart(fig_assets, use_container_width=True)
        
    with col_b:
        # Top Comptes
        top_accounts = df_rep_only['Compte'].value_counts().nlargest(10).reset_index()
        fig_accounts = px.bar(top_accounts, x='count', y='Compte', orientation='h',
                              title="Top 10 Comptes (Sites)", color_discrete_sequence=['#F59E0B'])
        fig_accounts.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor='white')
        st.plotly_chart(fig_accounts, use_container_width=True)

else:
    st.error("Données non trouvées ou erreur de chargement.")
