import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io

# 1. CONFIGURATION ET STYLE PROFESSIONNEL
st.set_page_config(page_title="Arkeos Tech Performance", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    /* Style des boutons KPI interactifs */
    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 110px;
        border: 1px solid #e2e8f0;
        background-color: white;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    div.stButton > button:hover {
        border-color: #1e3a8a;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .kpi-title { font-size: 14px; color: #64748b; font-weight: 600; }
    .kpi-value { font-size: 26px; color: #1e3a8a; font-weight: 800; }
    </style>
    """, unsafe_allow_html=True)

# 2. CHARGEMENT ET NETTOYAGE DES DONNÉES
@st.cache_data
def load_data():
    file_path = "data_dynamics_brute.csv.csv"
    if not os.path.exists(file_path): return None
    df = pd.read_csv(file_path)
    
    # Mapping des colonnes
    df = df.rename(columns={
        "Actif client principal de l'incident": "Actif_SN",
        "Propriétaire": "Technicien",
        "Date de création": "Date",
        "Compte de service": "Compte"
    })
    
    # Nettoyage des actifs (suppression des 'nan' et formats 34.8M)
    df['Actif_SN'] = df['Actif_SN'].astype(str).str.replace(r'\.0$', '', regex=True)
    df = df[~df['Actif_SN'].isin(['nan', 'None', 'nan.0', ''])]
    
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    # Calcul RDR (Repeat 7 jours)
    df = df.sort_values(['Actif_SN', 'Date'])
    df['Diff'] = df.groupby('Actif_SN')['Date'].diff().dt.days
    df['Is_Repeat'] = (df['Diff'] <= 7).astype(int)
    
    # Dimensions temporelles
    df['Année'] = df['Date'].dt.year.astype(str)
    df['Mois'] = df['Date'].dt.strftime('%B')
    df['Semaine'] = df['Date'].dt.strftime('%Y-W%V')
    
    return df

df = load_data()

# 3. SIDEBAR : LOGO ET FILTRES
if df is not None:
    with st.sidebar:
        if os.path.exists("download.png"):
            st.image("download.png", use_container_width=True)
        
        st.header("🔍 Paramètres")
        
        years = sorted(df['Année'].unique(), reverse=True)
        sel_year = st.multiselect("Année", years, default=["2026"])
        
        month_order = ["January", "February", "March", "April", "May", "June", 
                       "July", "August", "September", "October", "November", "December"]
        avail_months = [m for m in month_order if m in df['Mois'].unique()]
        sel_month = st.multiselect("Mois", avail_months, default=avail_months)
        
        techs = ["Tous"] + sorted(df['Technicien'].unique().tolist())
        sel_tech = st.selectbox("Technicien", techs)

    # Filtrage global
    mask = (df['Année'].isin(sel_year)) & (df['Mois'].isin(sel_month))
    if sel_tech != "Tous":
        mask &= (df['Technicien'] == sel_tech)
    df_f = df[mask]

    # 4. KPI ET ÉTAT DE VUE
    total_int = len(df_f)
    nb_reps = df_f['Is_Repeat'].sum()
    rdr = (nb_reps / total_int * 100) if total_int > 0 else 0
    fttr = 100 - rdr

    if 'view' not in st.session_state: st.session_state.view = "Tendance"

    # 5. AFFICHAGE DU HEADER ET DES KPI
    st.title("📊 Arkeos Support Technique Dashboard")
    st.markdown(f"**Période :** {', '.join(sel_year)} | **Technicien :** {sel_tech}")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button(f"Interventions\n{total_int:,}"): st.session_state.view = "Tendance"
    with c2:
        if st.button(f"RDR % (7j)\n{rdr:.1f}%"): st.session_state.view = "Impact"
    with c3:
        if st.button(f"FTTR %\n{fttr:.1f}%"): st.session_state.view = "Tendance"
    with c4:
        if st.button(f"Nb Repeats\n{nb_reps}"): st.session_state.view = "Impact"

    st.divider()

    # 6. GRAPHIQUE DE TENDANCE (% PAR SEMAINE)
    st.subheader("📈 Tendance RDR % par Semaine (7j)")
    trend = df_f.groupby('Semaine')['Is_Repeat'].mean().reset_index()
    trend['RDR %'] = (trend['Is_Repeat'] * 100).round(1)
    
    fig_trend = px.line(trend, x='Semaine', y='RDR %', text='RDR %', markers=True,
                        color_discrete_sequence=['#1e3a8a'])
    fig_trend.update_traces(textposition="top center")
    fig_trend.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_trend, use_container_width=True)

    # 7. SECTION DYNAMIQUE : FOCUS IMPACT ET EXPORT EXCEL
    if st.session_state.view == "Impact":
        st.subheader("🚨 Focus Impact : Machines en Repeat")
        df_impact = df_f[df_f['Is_Repeat'] == 1]
        
        col_chart, col_download = st.columns([2, 1])
        
        with col_chart:
            # Top 10 Actifs critiques sans 'nan'
            top_assets = df_impact['Actif_SN'].value_counts().nlargest(10).reset_index()
            fig_a = px.bar(top_assets, x='count', y='Actif_SN', orientation='h',
                           title="Top 10 Actifs Critiques", color_discrete_sequence=['#ef4444'])
            fig_a.update_layout(yaxis={'type': 'category', 'categoryorder': 'total ascending'})
            st.plotly_chart(fig_a, use_container_width=True)
            
        with col_download:
            st.write("### 📥 Export des données")
            st.info("Téléchargez la liste complète des interventions marquées en 'Repeat' pour analyse terrain.")
            
            # Génération du fichier Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_impact.to_excel(writer, index=False, sheet_name='Repeats_Impact')
            
            st.download_button(
                label="📥 Télécharger Impact (Excel)",
                data=output.getvalue(),
                file_name=f"Arkeos_Impact_Repeats_{sel_tech}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

else:
    st.error("Le fichier de données est introuvable ou mal formaté.")
