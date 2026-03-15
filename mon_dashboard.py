import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io

# 1. CONFIGURATION ET STYLE CORPORATE
st.set_page_config(page_title="Arkeos Performance Dashboard", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    .kpi-card {
        background-color: white; padding: 20px; border-radius: 12px;
        border: 1px solid #E2E8F0; text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .kpi-label { font-size: 14px; color: #64748B; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; }
    .value-blue { color: #1E3A8A; font-weight: 800; font-size: 28px; }
    .value-red { color: #DC2626; font-weight: 800; font-size: 28px; }
    .value-green { color: #16A34A; font-weight: 800; font-size: 28px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CHARGEMENT DES DONNÉES ET CALCULS
@st.cache_data
def load_data():
    file_path = "data_dynamics_brute.csv.csv"
    if not os.path.exists(file_path): return None
    df = pd.read_csv(file_path)
    
    mapping = {
        "Actif client principal de l'incident": "Actif_SN",
        "Propriétaire": "Technicien",
        "Date de création": "Date",
        "Compte de service": "Compte"
    }
    df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})
    
    if 'Actif_SN' in df.columns:
        df['Actif_SN'] = df['Actif_SN'].astype(str).str.replace(r'\.0$', '', regex=True)
        df = df[~df['Actif_SN'].isin(['nan', 'None', '', 'nan.0', 'No Actif'])]
    
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])
        df = df.sort_values(['Actif_SN', 'Date'])
        # Calcul du Repeat à 7 jours
        df['Is_Repeat'] = (df.groupby('Actif_SN')['Date'].diff().dt.days <= 7).astype(int)
        df['Année'] = df['Date'].dt.year.astype(str)
        df['Mois'] = df['Date'].dt.strftime('%B')
        df['Semaine'] = df['Date'].dt.strftime('%Y-W%V')
    
    return df

df = load_data()

# 3. FILTRES ET EXPORT DANS LA SIDEBAR
if df is not None:
    with st.sidebar:
        st.header("🔍 Paramètres")
        years = sorted(df['Année'].unique(), reverse=True)
        sel_year = st.multiselect("Année", years, default=[years[0]] if years else [])
        
        months = df['Mois'].unique().tolist()
        sel_month = st.multiselect("Mois", months, default=months)
        
        techs = ["Tous"] + sorted(df['Technicien'].unique().tolist())
        sel_tech = st.selectbox("Technicien", techs)
        
        mask = (df['Année'].isin(sel_year)) & (df['Mois'].isin(sel_month))
        if sel_tech != "Tous": mask &= (df['Technicien'] == sel_tech)
        df_f = df[mask]
        df_rep = df_f[df_f['Is_Repeat'] == 1]

        st.markdown("---")
        st.subheader("📥 Export")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_rep.to_excel(writer, index=False, sheet_name='Repeats_Impact')
        st.download_button("📥 Télécharger Impact (Excel)", output.getvalue(), file_name=f"Arkeos_RDR_{sel_tech}.xlsx")

    # 4. KPI DYNAMIQUES
    total, nb_reps = len(df_f), df_f['Is_Repeat'].sum()
    rdr = (nb_reps / total * 100) if total > 0 else 0
    fttr = 100 - rdr

    st.title("📠 Arkeos Performance Dashboard")
    
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(f'<div class="kpi-card"><div class="kpi-label">Interventions</div><div class="value-blue">{total:,}</div></div>', unsafe_allow_html=True)
    rdr_class = "value-red" if rdr > 20 else "value-blue"
    k2.markdown(f'<div class="kpi-card"><div class="kpi-label">RDR % (7j)</div><div class="{rdr_class}">{rdr:.1f}%</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="kpi-card"><div class="kpi-label">FTTR %</div><div class="value-green">{fttr:.1f}%</div></div>', unsafe_allow_html=True)
    k4.markdown(f'<div class="kpi-card"><div class="kpi-label">Nb Repeats</div><div class="value-blue">{nb_reps}</div></div>', unsafe_allow_html=True)

    st.divider()

    # 5. TENDANCE ET PERFORMANCE
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("📈 Tendance RDR % Hebdomadaire")
        trend = df_f.groupby('Semaine')['Is_Repeat'].mean().reset_index()
        trend['RDR %'] = (trend['Is_Repeat'] * 100).round(1)
        fig_t = px.line(trend, x='Semaine', y='RDR %', text='RDR %', markers=True, color_discrete_sequence=['#1E3A8A'])
        fig_t.update_traces(textposition="top center")
        fig_t.update_layout(plot_bgcolor='white', height=350)
        st.plotly_chart(fig_t, use_container_width=True)

    with col_right:
        st.subheader("🏆 Top Performers (FTTR %)")
        tech_perf = df_f.groupby('Technicien')['Is_Repeat'].agg(['count', 'mean']).reset_index()
        tech_perf['FTTR %'] = ((1 - tech_perf['mean']) * 100).round(1)
        # On filtre ceux qui ont au moins 5 interventions pour la pertinence
        top_techs = tech_perf[tech_perf['count'] >= 5].nlargest(5, 'FTTR %')
        fig_p = px.bar(top_techs, x='FTTR %', y='Technicien', orientation='h', text='FTTR %', color_discrete_sequence=['#16A34A'])
        fig_p.update_layout(plot_bgcolor='white', height=350)
        st.plotly_chart(fig_p, use_container_width=True)

    # 6. ANALYSE DES IMPACTS AVEC COUNTS
    st.subheader("🚨 Analyse des Sites et Machines Critiques")
    ca, cb = st.columns(2)
    
    with ca:
        top_a = df_rep['Actif_SN'].value_counts().nlargest(10).reset_index()
        fig_a = px.bar(top_a, x='count', y='Actif_SN', orientation='h', text='count',
                       title="Top 10 Machines (S/N)", color_discrete_sequence=['#EF4444'])
        fig_a.update_traces(textposition='outside')
        fig_a.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor='white')
        st.plotly_chart(fig_a, use_container_width=True)
        
    with cb:
        top_c = df_rep['Compte'].value_counts().nlargest(10).reset_index()
        fig_c = px.bar(top_c, x='count', y='Compte', orientation='h', text='count',
                       title="Top 10 Comptes (Sites Critiques)", color_discrete_sequence=['#F59E0B'])
        fig_c.update_traces(textposition='outside')
        fig_c.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor='white')
        st.plotly_chart(fig_c, use_container_width=True)
else:
    st.error("Données non trouvées.")
