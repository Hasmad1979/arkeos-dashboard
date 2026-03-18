import streamlit as st

hide_st_style = """
            <style>
            /* Masquer le menu Streamlit (Hamburger) */
            [data-testid="stToolbar"] {visibility: hidden !important;}
            
            /* Masquer le footer (Built with Streamlit) */
            footer {visibility: hidden !important;}
            [data-testid="stFooter"] {display: none !important;}
            
            /* Masquer la barre en haut (Header) */
            header {visibility: hidden !important;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)
st.markdown(
    """
    <style>
    footer {visibility: hidden !important;}
    .stApp [data-testid="stFooter"] {display: none !important;}
    .stApp footer {display: none !important;}
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)
# --------------------------------------------

# Le reste de votre code commence ici...
st.title("Technical Support Dashboard")

import pandas as pd
import plotly.express as px
import os
import io

# --- 1. CONFIGURATION ET DESIGN CORPORATE ---
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

# --- 2. MENU DE SÉCURISATION ---
USERS = {
    "admin": "Arkeos2026",
    "technicien": "ArkeosTech2026"
}

def check_password():
    """Retourne True si l'utilisateur est authentifié."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    # Formulaire de connexion
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_l, col_c, col_r = st.columns([1, 1.5, 1])
    with col_c:
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

# --- LANCEMENT DU DASHBOARD SI CONNECTÉ ---
if check_password():
    
    # Bouton de déconnexion en haut de la sidebar
    st.sidebar.write(f"👤 Connecté en tant que : **{st.session_state['user_connected']}**")
    if st.sidebar.button("Se déconnecter"):
        st.session_state["authenticated"] = False
        st.rerun()

    # --- 3. CHARGEMENT ET CALCULS ---
    @st.cache_data
    def load_data():
        file_path = "data_dynamics_brute.csv.csv"

df = pd.read_csv("data_dynamics_brute.csv")
st.write(df.columns.tolist()) # Cette ligne va afficher les noms exacts des colonnes
        if not os.path.exists(file_path): 
            return None
        
        # Lecture flexible pour éviter les erreurs de séparateurs
        df = pd.read_csv(file_path, sep=None, engine='python')
        
        mapping = {
            "Actif client principal de l'incident": "Actif_SN",
            "Propriétaire": "Technicien",
            "Date de création": "Date",
            "Compte de service": "Compte"
        }
        df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})
        
        # Nettoyage des noms de colonnes (espaces invisibles)
        df.columns = [str(c).strip() for c in df.columns]
        
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

    # --- 4. SIDEBAR ET FILTRES ---
    if df is not None:
        with st.sidebar:
            st.header("🔍 Paramètres")
            # Tri des années pour le filtre
            annees_dispo = sorted(df['Année'].unique(), reverse=True)
            sel_year = st.multiselect("Année", annees_dispo, default=[annees_dispo[0]])
            
            sel_month = st.multiselect("Mois", df['Mois'].unique(), default=df['Mois'].unique().tolist())
            sel_tech = st.selectbox("Technicien", ["Tous"] + sorted(df['Technicien'].unique().tolist()))
            
            mask = (df['Année'].isin(sel_year)) & (df['Mois'].isin(sel_month))
            if sel_tech != "Tous": 
                mask &= (df['Technicien'] == sel_tech)
            
            df_f = df[mask]
            df_rep = df_f[df_f['Is_Repeat'] == 1]

            st.markdown("---")
            # Export Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_rep.to_excel(writer, index=False, sheet_name='Repeats')
            st.download_button("📥 Télécharger Excel", output.getvalue(), file_name="Arkeos_Repeats.xlsx")

        # --- 5. EN-TÊTE ET KPI ---
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

        # --- 6. SECTION INSIGHTS DYNAMIQUES ---
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

        # --- 7. GRAPHES DE TENDANCE ---
        col_t1, col_t2 = st.columns([2, 1])
        with col_t1:
            st.subheader("📈 Tendance RDR % Hebdomadaire")
            trend = df_f.groupby('Semaine')['Is_Repeat'].mean().reset_index()
            trend['RDR %'] = (trend['Is_Repeat'] * 100).round(1)
            fig_t = px.line(trend, x='Semaine', y='RDR %', text='RDR %', markers=True, color_discrete_sequence=['#1E3A8A'])
            fig_t.update_layout(plot_bgcolor='white', height=300)
            st.plotly_chart(fig_t, use_container_width=True)

        # --- 8. ANALYSE DES IMPACTS ---
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
        st.error("Données non trouvées. Vérifiez la présence du fichier CSV sur GitHub.")
