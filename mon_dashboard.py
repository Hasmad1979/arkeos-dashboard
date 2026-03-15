import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io

# 1. CONFIGURATION ET DESIGN
st.set_page_config(page_title="Arkeos Support Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
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
    
    # Mapping des colonnes selon votre fichier
    df = df.rename(columns={
        "Actif client principal de l'incident": "Actif_SN",
        "Propriétaire": "Technicien",
        "Date de création": "Date",
        "Compte de service": "Compte"
    })
    
    # Nettoyage des actifs
    df['Actif_SN'] = df['Actif_SN'].astype(str).str.replace(r'\.0$', '', regex=True)
    df = df[~df['Actif_SN'].isin(['nan', 'None', '', 'nan.0'])]
    
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    # Calcul RDR (Repeat 7j)
    df = df.sort_values(['Actif_SN', 'Date'])
    df['Is_Repeat'] = (df.groupby('Actif_SN')['Date'].diff().dt.days <= 7).astype(int)
    
    # Dimensions temporelles
    df['Année'] = df['Date'].dt.year.astype(str)
    df['Mois'] = df['Date'].dt.strftime('%B')
    df['Semaine'] = df['Date'].dt.strftime('%Y-W%V')
    
    return df

df = load_data()

# 3. SIDEBAR : FILTRES ET BOUTON EXPORT
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
        st.subheader("📥 Export")
        
        mask = (df['Année'].isin(sel_year)) & (df['Mois'].isin(sel_month))
        if sel_tech != "Tous": mask &= (df['Technicien'] == sel_tech)
        df_f = df[mask]
        
        # Préparation de l'export Excel (uniquement les repeats)
        df_export = df_f[df_f['Is_Repeat'] == 1]
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Impact_Repeats')
        
        st.download_button(
            label="📥 Télécharger les Repeats",
            data=output.getvalue(),
            file_name=f"Arkeos_Repeats_{sel_tech}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # 4. DASHBOARD PRINCIPAL
    total = len(df_f)
    nb_reps = df_f['Is_Repeat'].sum()
    rdr = (nb_reps / total * 100) if total > 0 else 0
    fttr = 100 - rdr

    st.title("🏛️ Arkeos Performance Support")
    
    # Cartes KPI
    c1, c2, c3, c4 = st.columns(4)
    c1.button(f"Interventions\n{total:,}")
    c2.button(f"RDR % (7j)\n{rdr:.1f}%")
    c3.button(f"FTTR %\n{fttr:.1f}%")
    c4.button(f"Nb Repeats\n{nb_reps}")

    st.divider()

    # Graphique de tendance hebdomadaire
    st.subheader("📈 Tendance RDR % par Semaine")
    trend = df_f.groupby('Semaine')['Is_Repeat'].mean().reset_index()
    trend['RDR %'] = (trend['Is_Repeat'] * 100).round(1)
    fig_trend = px.line(trend, x='Semaine', y='RDR %', text='RDR %', markers=True, color_discrete_sequence=['#1e3a8a'])
    fig_trend.update_traces(textposition="top center")
    st.plotly_chart(fig_trend, use_container_width=True)

    # 5. ANALYSE DES IMPACTS : ACTIFS VS COMPTES
    st.subheader("🚨 Analyse des Impacts (Repeats)")
    df_impact = df_f[df_f['Is_Repeat'] == 1]
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        # Top 10 Actifs
        top_assets = df_impact['Actif_SN'].value_counts().nlargest(10).reset_index()
        fig_assets = px.bar(top_assets, x='count', y='Actif_SN', orientation='h', 
                            title="Top 10 Actifs Critiques", color_discrete_sequence=['#ef4444'])
        fig_assets.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_assets, use_container_width=True)
        
    with col_b:
        # Top 10 Comptes (Sites)
        top_accounts = df_impact['Compte'].value_counts().nlargest(10).reset_index()
        fig_accounts = px.bar(top_accounts, x='count', y='Compte', orientation='h', 
                              title="Top 10 Comptes (Sites Critiques)", color_discrete_sequence=['#f59e0b'])
        fig_accounts.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_accounts, use_container_width=True)

else:
    st.error("Données non trouvées.")
