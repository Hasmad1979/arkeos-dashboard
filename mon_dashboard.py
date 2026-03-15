import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io

# 1. CONFIGURATION ET DESIGN PROFESSIONNEL
st.set_page_config(page_title="Arkeos Performance Dashboard", layout="wide")

# CSS personnalisé pour les couleurs dynamiques et le gras
st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    .kpi-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #E2E8F0;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .kpi-label { font-size: 16px; color: #64748B; font-weight: 500; margin-bottom: 10px; }
    .value-blue { color: #1E3A8A; font-weight: 800; font-size: 28px; }
    .value-red { color: #DC2626; font-weight: 800; font-size: 28px; }
    .value-green { color: #16A34A; font-weight: 800; font-size: 28px; }
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
        "Date de création": "Date",
        "Compte de service": "Compte"
    })
    # Nettoyage des données 'nan'
    df['Actif_SN'] = df['Actif_SN'].astype(str).str.replace(r'\.0$', '', regex=True)
    df = df[~df['Actif_SN'].isin(['nan', 'None', '', 'nan.0'])]
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

# 3. SIDEBAR ET EXPORT
if df is not None:
    with st.sidebar:
        if os.path.exists("download.png"): st.image("download.png")
        st.header("🔍 Paramètres")
        sel_year = st.multiselect("Année", sorted(df['Année'].unique(), reverse=True), default=["2026"])
        sel_month = st.multiselect("Mois", df['Mois'].unique(), default=df['Mois'].unique().tolist())
        sel_tech = st.selectbox("Technicien", ["Tous"] + sorted(df['Technicien'].unique().tolist()))
        
        st.markdown("---")
        st.subheader("📥 Export")
        mask = (df['Année'].isin(sel_year)) & (df['Mois'].isin(sel_month))
        if sel_tech != "Tous": mask &= (df['Technicien'] == sel_tech)
        df_f = df[mask]
        
        # Bouton Export Excel à gauche
        df_rep = df_f[df_f['Is_Repeat'] == 1]
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_rep.to_excel(writer, index=False, sheet_name='Repeats')
        st.download_button("📥 Télécharger les Repeats", output.getvalue(), 
                           file_name=f"Arkeos_Repeats_{sel_tech}.xlsx")

    # 4. KPI DYNAMIQUES (COULEURS ET GRAS)
    total = len(df_f)
    nb_reps = df_f['Is_Repeat'].sum()
    rdr = (nb_reps / total * 100) if total > 0 else 0
    fttr = 100 - rdr

    st.title("🏛️ Support Technique Performance")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Interventions</div><div class="value-blue">{total:,}</div></div>', unsafe_allow_html=True)
    with c2:
        # Couleur rouge si RDR > 20%
        color_class = "value-red" if rdr > 20 else "value-blue"
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">RDR % (7j)</div><div class="{color_class}">{rdr:.1f}%</div></div>', unsafe_allow_html=True)
    with c3:
        # FTTR en vert
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">FTTR %</div><div class="value-green">{fttr:.1f}%</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Nb Repeats</div><div class="value-blue">{nb_reps}</div></div>', unsafe_allow_html=True)

    st.divider()

    # 5. ANALYSE GRAPHIQUE
    st.subheader("📈 Tendance et Impacts")
    col_chart, col_assets = st.columns([2, 1])
    
    with col_chart:
        trend = df_f.groupby('Semaine')['Is_Repeat'].mean().reset_index()
        trend['RDR %'] = (trend['Is_Repeat'] * 100).round(1)
        fig = px.line(trend, x='Semaine', y='RDR %', text='RDR %', markers=True, color_discrete_sequence=['#1E3A8A'])
        st.plotly_chart(fig, use_container_width=True)
        
    with col_assets:
        top_assets = df_rep['Actif_SN'].value_counts().nlargest(10).reset_index()
        fig_a = px.bar(top_assets, x='count', y='Actif_SN', orientation='h', color_discrete_sequence=['#EF4444'], title="Top Machines Critiques")
        st.plotly_chart(fig_a, use_container_width=True)

else:
    st.error("Données manquantes.")
