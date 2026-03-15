import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io

# 1. CONFIGURATION ET DESIGN CORPORATE
st.set_page_config(page_title="Arkeos Performance Dashboard", layout="wide")

# CSS pour le style pro et les couleurs dynamiques
st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    .kpi-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .kpi-label { font-size: 14px; color: #64748B; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; }
    .value-blue { color: #1E3A8A; font-weight: 800; font-size: 28px; }
    .value-red { color: #DC2626; font-weight: 800; font-size: 28px; }
    .value-green { color: #16A34A; font-weight: 800; font-size: 28px; }
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
    
    # Nettoyage strict (enlever les 'nan' et 'No Actif')
    df['Actif_SN'] = df['Actif_SN'].astype(str).str.replace(r'\.0$', '', regex=True)
    df = df[~df['Actif_SN'].isin(['nan', 'None', '', 'nan.0', 'No Actif'])]
    df = df[~df['Compte'].astype(str).isin(['nan', 'None', ''])]
    
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    
    # Calcul RDR (Repeat sous 7 jours)
    df = df.sort_values(['Actif_SN', 'Date'])
    df['Is_Repeat'] = (df.groupby('Actif_SN')['Date'].diff().dt.days <= 7).astype(int)
    
    df['Année'] = df['Date'].dt.year.astype(str)
    df['Mois'] = df['Date'].dt.strftime('%B')
    df['Semaine'] = df['Date'].dt.strftime('%Y-W%V')
    
    return df

df = load_data()

# 3. SIDEBAR : FILTRES ET EXPORT
if df is not None:
    with st.sidebar:
        st.header("🔍 Paramètres")
        sel_year = st.multiselect("Année", sorted(df['Année'].unique(), reverse=True), default=["2026"])
        sel_month = st.multiselect("Mois", df['Mois'].unique(), default=df['Mois'].unique().tolist())
        sel_tech = st.selectbox("Technicien", ["Tous"] + sorted(df['Technicien'].unique().tolist()))
        
        st.markdown("---")
        st.subheader("📥 Exportation")
        
        # Filtrage dynamique
        mask = (df['Année'].isin(sel_year)) & (df['Mois'].isin(sel_month))
        if sel_tech != "Tous": mask &= (df['Technicien'] == sel_tech)
        df_f = df[mask]
        
        # Export des repeats uniquement
        df_rep = df_f[df_f['Is_Repeat'] == 1]
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_rep.to_excel(writer, index=False, sheet_name='Repeats_Impact')
        
        st.download_button(label="📥 Télécharger Impact (Excel)", data=output.getvalue(), 
                           file_name=f"Arkeos_Repeats_{sel_tech}.xlsx")

    # 4. KPI DYNAMIQUES AVEC COULEURS
    total = len(df_f)
    nb_reps = df_f['Is_Repeat'].sum()
    rdr = (nb_reps / total * 100) if total > 0 else 0
    fttr = 100 - rdr

    st.title("📠 Arkeos Technical Support Performance")
    
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Interventions</div><div class="value-blue">{total:,}</div></div>', unsafe_allow_html=True)
    with k2:
        # Alerte Rouge si RDR > 20%
        rdr_style = "value-red" if rdr > 20 else "value-blue"
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">RDR % (7j)</div><div class="{rdr_style}">{rdr:.1f}%</div></div>', unsafe_allow_html=True)
    with k3:
        # FTTR en vert par défaut
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">FTTR %</div><div class="value-green">{fttr:.1f}%</div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Nb Repeats</div><div class="value-blue">{nb_reps}</div></div>', unsafe_allow_html=True)

    st.divider()

    # 5. ANALYSE DES IMPACTS (REPEATS)
    st.subheader("🚨 Analyse des Sites et Machines Critiques")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        # Top Actifs (Numéros de série)
        top_assets = df_rep['Actif_SN'].value_counts().nlargest(10).reset_index()
        fig_assets = px.bar(top_assets, x='count', y='Actif_SN', orientation='h',
                            title="Top 10 Machines (S/N)", color_discrete_sequence=['#EF4444'])
        fig_assets.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor='white')
        st.plotly_chart(fig_assets, use_container_width=True)
        
    with col_b:
        # Top Comptes de Service (Sites clients)
        top_accounts = df_rep['Compte'].value_counts().nlargest(10).reset_index()
        fig_accounts = px.bar(top_accounts, x='count', y='Compte', orientation='h',
                              title="Top 10 Comptes (Sites Critiques)", color_discrete_sequence=['#F59E0B'])
        fig_accounts.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor='white')
        st.plotly_chart(fig_accounts, use_container_width=True)

else:
    st.error("Données non trouvées. Veuillez vérifier votre fichier source.")
