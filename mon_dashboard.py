import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Arkeos AI Dashboard", layout="wide")

# Design Corporate (Cacher les menus et styliser les cartes)
st.markdown("""
    <style>
    [data-testid="stToolbar"] {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
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

# --- 2. SÉCURITÉ ---
USERS = {"admin": "Arkeos2026", "technicien": "ArkeosTech2026"}

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if st.session_state["authenticated"]:
        return True
    st.title("🔐 Accès Arkeos")
    user = st.text_input("Identifiant")
    pw = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter", use_container_width=True):
        if user in USERS and pw == USERS[user]:
            st.session_state["authenticated"] = True
            st.session_state["user_connected"] = user
            st.rerun()
        else:
            st.error("❌ Identifiant ou mot de passe incorrect")
    return False

# --- 3. LOGIQUE PRINCIPALE ---
if check_password():
    @st.cache_data
    def load_data():
        file_path = "data_dynamics_brute.csv"
        if not os.path.exists(file_path):
            return None
        
        df = pd.read_csv(file_path, sep=None, engine='python')
        df.columns = [str(c).strip() for c in df.columns]

        mapping = {
            "Actif client principal de l'incident": "Actif_SN",
            "Propriétaire": "Technicien",
            "Date de création": "Date",
            "Compte de service": "Compte"
        }
        df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})
        
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df = df.dropna(subset=['Date']).sort_values(['Actif_SN', 'Date'])
            df['Is_Repeat'] = (df.groupby('Actif_SN')['Date'].diff().dt.days <= 7).astype(int)
            df['Année'] = df['Date'].dt.year.astype(str)
            df['Mois'] = df['Date'].dt.strftime('%B')
            df['Semaine'] = df['Date'].dt.strftime('%Y-W%V')
        return df

    df = load_data()

    if df is not None:
        # Barre latérale
        with st.sidebar:
            st.write(f"👤 **{st.session_state['user_connected']}**")
            if st.button("Déconnexion"):
                st.session_state["authenticated"] = False
                st.rerun()
            st.header("🔍 Paramètres")
            sel_year = st.multiselect("Année", sorted(df['Année'].unique(), reverse=True), default=[sorted(df['Année'].unique())[-1]])
            sel_tech = st.selectbox("Technicien", ["Tous"] + sorted(df['Technicien'].unique().tolist()))
            
            mask = df['Année'].isin(sel_year)
            if sel_tech != "Tous": mask &= (df['Technicien'] == sel_tech)
            df_f = df[mask]
            df_rep = df_f[df_f['Is_Repeat'] == 1]

        # Dashboard
        st.title("📠 Arkeos Technical Support Dashboard")
        
        # KPIs
        t, r = len(df_f), df_f['Is_Repeat'].sum()
        r_rate = (r/t*100) if t > 0 else 0
        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(f'<div class="kpi-card">Interventions<br><span class="value-blue">{t:,}</span></div>', unsafe_allow_html=True)
        k2.markdown(f'<div class="kpi-card">RDR % (7j)<br><span class="value-red">{r_rate:.1f}%</span></div>', unsafe_allow_html=True)
        k3.markdown(f'<div class="kpi-card">FTTR %<br><span class="value-green">{100-r_rate:.1f}%</span></div>', unsafe_allow_html=True)
        k4.markdown(f'<div class="kpi-card">Nb Repeats<br><span class="value-blue">{r}</span></div>', unsafe_allow_html=True)

        # Graphique
        st.subheader("📈 Tendance RDR % par Semaine")
        trend = df_f.groupby('Semaine')['Is_Repeat'].mean().reset_index()
        trend['RDR %'] = (trend['Is_Repeat'] * 100).round(1)
        fig = px.line(trend, x='Semaine', y='RDR %', markers=True, color_discrete_sequence=['#1E3A8A'])
        st.plotly_chart(fig, use_container_width=True)
