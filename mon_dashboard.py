import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io
from PIL import Image

# 1. CONFIGURATION ET DESIGN "EXECUTIVE"
st.set_page_config(page_title="Arkeos Analytics Pro", layout="wide")

st.markdown("""
    <style>
    /* Style général */
    .main { background-color: #F8FAFC; }
    
    /* Design des boutons KPI */
    div.stButton > button {
        width: 100%;
        border-radius: 15px;
        height: 120px;
        border: 1px solid #E2E8F0;
        background-color: white;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        padding: 10px;
    }
    div.stButton > button:hover {
        border-color: #1E3A8A;
        transform: translateY(-4px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    /* Style pour les labels dans les boutons */
    .kpi-label { font-size: 14px; color: #64748B; font-weight: 600; text-transform: uppercase; }
    .kpi-val { font-size: 28px; color: #1E3A8A; font-weight: 800; display: block; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CHARGEMENT ET NETTOYAGE (Données updatées par l'utilisateur)
@st.cache_data
def load_and_clean():
    file_path = "data_dynamics_brute.csv.csv"
    if not os.path.exists(file_path): return None
    df = pd.read_csv(file_path)
    
    # Renommage et formatage
    df = df.rename(columns={
        "Actif client principal de l'incident": "Actif_SN",
        "Propriétaire": "Technicien",
        "Date de création": "Date"
    })
    
    # Correction des erreurs de type "nan" et "34.8M"
    df['Actif_SN'] = df['Actif_SN'].astype(str).str.replace(r'\.0$', '', regex=True)
    df = df[~df['Actif_SN'].isin(['nan', 'None', ''])]
    
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    # Calcul RDR (Repeat 7j)
    df = df.sort_values(['Actif_SN', 'Date'])
    df['Diff'] = df.groupby('Actif_SN')['Date'].diff().dt.days
    df['Is_Repeat'] = (df['Diff'] <= 7).astype(int)
    
    df['Année'] = df['Date'].dt.year.astype(str)
    df['Mois'] = df['Date'].dt.strftime('%B')
    df['Semaine'] = df['Date'].dt.strftime('%Y-W%V')
    
    return df

df = load_and_clean()

# 3. SIDEBAR : LOGO ET FILTRES
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

    # Filtrage
    mask = (df['Année'].isin(sel_year)) & (df['Mois'].isin(sel_month))
    if sel_tech != "Tous": mask &= (df['Technicien'] == sel_tech)
    df_f = df[mask]

    # 4. CALCULS KPI
    total = len(df_f)
    reps = df_f['Is_Repeat'].sum()
    rdr = (reps / total * 100) if total > 0 else 0
    fttr = 100 - rdr

    # 5. HEADER ET KPI INTERACTIFS
    st.title("🏛️ Support Technique Performance")
    st.markdown(f"**Période :** {', '.join(sel_year)} | **Filtre :** {sel_tech}")

    if 'view' not in st.session_state: st.session_state.view = "Global"

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button(f"Interventions\n{total:,}"): st.session_state.view = "Global"
    with c2:
        # Couleur rouge subtile si RDR > 30%
        label_rdr = "🔴 RDR % (7j)" if rdr > 30 else "🔄 RDR % (7j)"
        if st.button(f"{label_rdr}\n{rdr:.1f}%"): st.session_state.view = "Impact"
    with c3:
        if st.button(f"✅ FTTR %\n{fttr:.1f}%"): st.session_state.view = "Global"
    with c4:
        if st.button(f"⚠️ Nb Repeats\n{reps}"): st.session_state.view = "Impact"

    st.markdown("---")

    # 6. GRAPHIQUE DE TENDANCE (% PAR SEMAINE)
    st.subheader("📈 Tendance RDR % Hebdomadaire")
    trend = df_f.groupby('Semaine')['Is_Repeat'].mean().reset_index()
    trend['RDR %'] = (trend['Is_Repeat'] * 100).round(1)
    
    fig_trend = px.line(trend, x='Semaine', y='RDR %', text='RDR %', markers=True,
                        color_discrete_sequence=['#1E3A8A'], height=450)
    fig_trend.update_traces(textposition="top center", line_width=3, marker_size=10)
    fig_trend.update_layout(plot_bgcolor='white', hovermode='x unified')
    st.plotly_chart(fig_trend, use_container_width=True)

    # 7. SECTION DYNAMIQUE : IMPACT & EXPORT
    if st.session_state.view == "Impact":
        st.divider()
        st.subheader("🚨 Détails des Impacts (Repeats)")
        df_reps = df_f[df_f['Is_Repeat'] == 1]
        
        col_list, col_exp = st.columns([2, 1])
        
        with col_list:
            top_a = df_reps['Actif_SN'].value_counts().nlargest(10).reset_index()
            fig_a = px.bar(top_a, x='count', y='Actif_SN', orientation='h', 
                           title="Top 10 Actifs Critiques", color_discrete_sequence=['#E74C3C'])
            fig_a.update_layout(yaxis={'type': 'category', 'categoryorder': 'total ascending'})
            st.plotly_chart(fig_a, use_container_width=True)
            
        with col_exp:
            st.info("Utilisez le bouton ci-dessous pour extraire la liste des machines en 'Repeat' pour action immédiate.")
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_reps.to_excel(writer, index=False, sheet_name='Détail_Impact')
            st.download_button(
                label="📥 Télécharger l'Impact Excel",
                data=output.getvalue(),
                file_name=f"arkeos_impact_{sel_tech}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
else:
    st.error("Données manquantes.")
