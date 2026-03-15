import streamlit as st
import pd as pd
import pandas as pd
import plotly.express as px
import os
import io

# 1. CONFIGURATION DE LA PAGE ET STYLE CSS
st.set_page_config(page_title="Arkeos Performance Dashboard", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    /* Style des cartes KPI */
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

# 2. FONCTION DE CHARGEMENT ET NETTOYAGE
@st.cache_data
def load_data():
    file_path = "data_dynamics_brute.csv.csv"
    if not os.path.exists(file_path): 
        return None
    
    df = pd.read_csv(file_path)
    
    # Mapping des colonnes sécurisé
    mapping = {
        "Actif client principal de l'incident": "Actif_SN",
        "Propriétaire": "Technicien",
        "Date de création": "Date",
        "Compte de service": "Compte"
    }
    df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})
    
    # Nettoyage des Actifs (Numéros de série)
    if 'Actif_SN' in df.columns:
        df['Actif_SN'] = df['Actif_SN'].astype(str).str.replace(r'\.0$', '', regex=True)
        df = df[~df['Actif_SN'].isin(['nan', 'None', '', 'nan.0', 'No Actif'])]
    
    # Nettoyage des Comptes
    if 'Compte' in df.columns:
        df = df[~df['Compte'].astype(str).isin(['nan', 'None', ''])]

    # Traitement des dates et calcul du Repeat (RDR)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        
        # Calcul RDR (Intervention sur le même actif en moins de 7 jours)
        df = df.sort_values(['Actif_SN', 'Date'])
        df['Is_Repeat'] = (df.groupby('Actif_SN')['Date'].diff().dt.days <= 7).astype(int)
        
        # Dimensions temporelles
        df['Année'] = df['Date'].dt.year.astype(str)
        df['Mois'] = df['Date'].dt.strftime('%B')
        df['Semaine'] = df['Date'].dt.strftime('%Y-W%V')
    
    return df

df = load_data()

# 3. INTERFACE ET FILTRES (SIDEBAR)
if df is not None:
    with st.sidebar:
        st.header("🔍 Paramètres")
        
        # Filtres multidimensionnels
        years = sorted(df['Année'].unique(), reverse=True)
        sel_year = st.multiselect("Année", years, default=[years[0]] if years else [])
        
        months = df['Mois'].unique().tolist()
        sel_month = st.multiselect("Mois", months, default=months)
        
        techs = ["Tous"] + sorted(df['Technicien'].unique().tolist())
        sel_tech = st.selectbox("Technicien", techs)
        
        # Application des filtres
        mask = (df['Année'].isin(sel_year)) & (df['Mois'].isin(sel_month))
        if sel_tech != "Tous":
            mask &= (df['Technicien'] == sel_tech)
        
        df_filtered = df[mask]
        df_repeats = df_filtered[df_filtered['Is_Repeat'] == 1]

        st.markdown("---")
        
        # BOUTON DE TÉLÉCHARGEMENT (SIDEBAR GAUCHE)
        st.subheader("📥 Exportation")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_repeats.to_excel(writer, index=False, sheet_name='Repeats_Details')
        
        st.download_button(
            label="📥 Télécharger les Repeats (Excel)",
            data=output.getvalue(),
            file_name=f"Arkeos_Repeats_{sel_tech}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # 4. DASHBOARD PRINCIPAL - KPI
    total_inter = len(df_filtered)
    nb_repeats = df_filtered['Is_Repeat'].sum()
    rdr_rate = (nb_repeats / total_inter * 100) if total_inter > 0 else 0
    fttr_rate = 100 - rdr_rate

    st.title("📠 Arkeos Performance Télécopieurs")
    
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    
    with col_kpi1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Interventions</div><div class="value-blue">{total_inter:,}</div></div>', unsafe_allow_html=True)
    
    with col_kpi2:
        # Alerte Rouge si RDR > 20%
        rdr_color = "value-red" if rdr_rate > 20 else "value-blue"
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">RDR % (7j)</div><div class="{rdr_color}">{rdr_rate:.1f}%</div></div>', unsafe_allow_html=True)
    
    with col_kpi3:
        # FTTR en Vert
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">FTTR %</div><div class="value-green">{fttr_rate:.1f}%</div></div>
