import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io


# --- SYSTÈME DE SÉCURITÉ ---
def login_screen():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🔐 Accès Restreint - Arkeos")
        user = st.text_input("Identifiant")
        pw = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            if user == "admin" and pw == "Arkeos2026":
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Identifiant ou mot de passe incorrect")
        return False
    return True

# --- EXÉCUTION DE LA SÉCURITÉ ---
if login_screen():
    # Tout ton code actuel de dashboard doit être décalé (indenté) ici
    st.sidebar.button("Se déconnecter", on_click=lambda: st.session_state.update({"authenticated": False}))
    
    # A partir d'ici, remets ton code : st.title("Arkeos..."), etc.
# 1. CONFIGURATION ET DESIGN CORPORATE
st.set_page_config(page_title="Arkeos AI Dashboard", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    .kpi-card {
        background-color: white; padding: 20px; border-radius: 12px;
        border: 1px solid #E2E8F0; text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .insight-card {
        background-color: #EFF6FF; padding: 15px; border-radius: 10px;
        border-left: 5px solid #1E3A8A; margin-bottom: 20px;
    }
    .value-blue { color: #1E3A8A; font-weight: 800; font-size: 28px; }
    .value-red { color: #DC2626; font-weight: 800; font-size: 28px; }
    .value-green { color: #16A34A; font-weight: 800; font-size: 28px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CHARGEMENT ET CALCULS
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
        df['Is_Repeat'] = (df.groupby('Actif_SN')['Date'].diff().dt.days <= 7).astype(int)
        df['Année'] = df['Date'].dt.year.astype(str)
        df['Mois'] = df['Date'].dt.strftime('%B')
        df['Semaine'] = df['Date'].dt.strftime('%Y-W%V')
    return df

df = load_data()

# 3. SIDEBAR ET FILTRES
if df is not None:
    with st.sidebar:
        st.header("🔍 Paramètres")
        sel_year = st.multiselect("Année", sorted(df['Année'].unique(), reverse=True), default=["2026"])
        sel_month = st.multiselect("Mois", df['Mois'].unique(), default=df['Mois'].unique().tolist())
        sel_tech = st.selectbox("Technicien", ["Tous"] + sorted(df['Technicien'].unique().tolist()))
        
        mask = (df['Année'].isin(sel_year)) & (df['Mois'].isin(sel_month))
        if sel_tech != "Tous": mask &= (df['Technicien'] == sel_tech)
        df_f = df[mask]
        df_rep = df_f[df_f['Is_Repeat'] == 1]

        st.markdown("---")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_rep.to_excel(writer, index=False, sheet_name='Repeats')
        st.download_button("📥 Télécharger Excel", output.getvalue(), file_name="Arkeos_Repeats.xlsx")

    # 4. EN-TÊTE ET KPI
    st.title("📠 Arkeos Technical Support Dashboard")
    
    total, nb_reps = len(df_f), df_f['Is_Repeat'].sum()
    rdr = (nb_reps / total * 100) if total > 0 else 0
    fttr = 100 - rdr

    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(f'<div class="kpi-card"><div class="kpi-label">Interventions</div><div class="value-blue">{total:,}</div></div>', unsafe_allow_html=True)
    rdr_class = "value-red" if rdr > 20 else "value-blue"
    k2.markdown(f'<div class="kpi-card"><div class="kpi-label">RDR % (7j)</div><div class="{rdr_class}">{rdr:.1f}%</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="kpi-card"><div class="kpi-label">FTTR %</div><div class="value-green">{fttr:.1f}%</div></div>', unsafe_allow_html=True)
    k4.markdown(f'<div class="kpi-card"><div class="kpi-label">Nb Repeats</div><div class="value-blue">{nb_reps}</div></div>', unsafe_allow_html=True)

    # 5. NOUVEAU : SECTION INSIGHTS DYNAMIQUES
    st.markdown("### 💡 Good To Know")
    if not df_rep.empty:
        worst_machine = df_rep['Actif_SN'].value_counts().idxmax()
        worst_site = df_rep['Compte'].value_counts().idxmax()
        
        c_ins1, c_ins2 = st.columns(2)
        with c_ins1:
            st.markdown(f"""<div class="insight-card">
                <b>🚨 Alerte Priorité Machine :</b><br>
                La machine <b>{worst_machine}</b> nécessite une expertise. Elle totalise {df_rep['Actif_SN'].value_counts().max()} repeats.
                </div>""", unsafe_allow_html=True)
        with c_ins2:
            st.markdown(f"""<div class="insight-card">
                <b>🏢 Alerte Satisfaction Client :</b><br>
                Le compte <b>{worst_site}</b> est le plus impacté ce mois-ci. Une visite préventive est conseillée.
                </div>""", unsafe_allow_html=True)

    st.divider()

    # 6. GRAPHES DE TENDANCE ET PERFORMANCE
    col_t1, col_t2 = st.columns([2, 1])
    
    with col_t1:
        st.subheader("📈 Tendance RDR % Hebdomadaire")
        trend = df_f.groupby('Semaine')['Is_Repeat'].mean().reset_index()
        trend['RDR %'] = (trend['Is_Repeat'] * 100).round(1)
        fig_t = px.line(trend, x='Semaine', y='RDR %', text='RDR %', markers=True, color_discrete_sequence=['#1E3A8A'])
        fig_t.update_layout(plot_bgcolor='white', height=300)
        st.plotly_chart(fig_t, use_container_width=True)


    # 7. ANALYSE DES IMPACTS AVEC COUNTS
    st.subheader("🚨 Analyse détaillée des Repeats")
    ca, cb = st.columns(2)
    with ca:
        top_a = df_rep['Actif_SN'].value_counts().nlargest(10).reset_index()
        fig_a = px.bar(top_a, x='count', y='Actif_SN', orientation='h', text='count', title="Top 10 Machines Critiques", color_discrete_sequence=['#EF4444'])
        fig_a.update_traces(textposition='outside')
        st.plotly_chart(fig_a, use_container_width=True)
    with cb:
        top_c = df_rep['Compte'].value_counts().nlargest(10).reset_index()
        fig_c = px.bar(top_c, x='count', y='Compte', orientation='h', text='count', title="Top 10 Clients Impactés", color_discrete_sequence=['#F59E0B'])
        fig_c.update_traces(textposition='outside')
        st.plotly_chart(fig_c, use_container_width=True)



else:
    st.error("Données non trouvées.")
