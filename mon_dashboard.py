import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import plotly.express as px

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="Arkeos Technical Support Dashboard", layout="wide")

# --- STYLE CSS ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { background-color: #f8f9fa; }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #004a99;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    file_name = "data_dynamics_brute.csv.csv" 
    if not os.path.exists(file_name):
        return None
    df = pd.read_csv(file_name)
    df = df.rename(columns={
        "Numéro de l'incident": "ID", 
        "Actifs du client": "SN", 
        "Owner": "Technicien", 
        "Créé le": "Date"
    })
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['SN', 'Date']).sort_values(['SN', 'Date'])
    
    df['Date_Prev'] = df.groupby('SN')['Date'].shift(1)
    def calc_bus(row):
        if pd.isnull(row['Date_Prev']): return None
        d1, d2 = row['Date_Prev'].date(), row['Date'].date()
        try:
            return int(np.busday_count(d1, d2)) if d1 < d2 else 0
        except:
            return 0
    df['Ecart_Ouvres'] = df.apply(calc_bus, axis=1)
    df['Is_Repeat'] = ((df['Ecart_Ouvres'] >= 0) & (df['Ecart_Ouvres'] <= 22)).astype(int)
    return df

df_raw = load_data()

if df_raw is not None:
    noms_mois = {1:'Janvier', 2:'Février', 3:'Mars', 4:'Avril', 5:'Mai', 6:'Juin', 
                 7:'Juillet', 8:'Août', 9:'Septembre', 10:'Octobre', 11:'Novembre', 12:'Décembre'}

    if os.path.exists("ark.png"):
        st.sidebar.image("ark.png", width=150)
    
    st.sidebar.title("🎮 Filtres")
    years = sorted(df_raw['Date'].dt.year.unique(), reverse=True)
    sel_years = st.sidebar.multiselect("Années", years, default=years)
    
    df_raw['Mois_Num'] = df_raw['Date'].dt.month
    df_raw['Mois_Nom'] = df_raw['Mois_Num'].map(noms_mois)
    available_months = sorted(df_raw['Mois_Num'].unique())
    month_options = [noms_mois[m] for m in available_months]
    sel_months_names = st.sidebar.multiselect("Mois", month_options, default=month_options)
    
    techs = sorted(df_raw['Technicien'].astype(str).unique().tolist())
    sel_techs = st.sidebar.multiselect("Techniciens", techs, default=techs)
    
    df_f = df_raw[
        (df_raw['Date'].dt.year.isin(sel_years)) & 
        (df_raw['Mois_Nom'].isin(sel_months_names)) &
        (df_raw['Technicien'].isin(sel_techs))
    ].copy()

    st.title("📊 Arkeos Technical Support Dashboard")
    st.markdown("---")

    if not df_f.empty:
        total_int = len(df_f)
        total_rep = df_f['Is_Repeat'].sum()
        repeat_rate = (total_rep / total_int * 100) if total_int > 0 else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Interventions", f"{total_int:,}")
        c2.metric("Total Repeats", f"{total_rep:,}")
        c3.metric("Taux de Repeat", f"{repeat_rate:.1f}%")
        # 1. KPI
        total_int = len(df_f)
        total_rep = df_f['Is_Repeat'].sum()
        repeat_rate = (total_rep / total_int * 100) if total_int > 0 else 0
        fttr_rate = 100 - repeat_rate # Le calcul du FTTR

        c1, c2, c3, c4 = st.columns(4) # On passe à 4 colonnes
        c1.metric("Interventions", f"{total_int:,}")
        c2.metric("Total Repeats", f"{total_rep:,}")
        c3.metric("Taux de Repeat", f"{repeat_rate:.1f}%", delta=f"{repeat_rate:.1f}%", delta_color="inverse")
        c4.metric("FTTR Rate", f"{fttr_rate:.1f}%")
        # --- ÉVOLUTION MENSUELLE (CORRIGÉ) ---
        st.write("")
        with st.container(border=True):
            st.subheader("📈 Évolution Mensuelle du Taux de Repeat")
            evol = df_f.groupby('Mois_Num')['Is_Repeat'].mean() * 100
            evol = evol.reset_index()
            evol['Mois_Label'] = evol['Mois_Num'].map(noms_mois)
            # Création propre des étiquettes de texte
            labels = [f"{v:.1f}%" for v in evol['Is_Repeat']]

            fig_evol = px.line(evol, x='Mois_Label', y='Is_Repeat', markers=True, text=labels)
            fig_evol.update_traces(line_color='#004a99', line_width=3, textposition="top center")
            fig_evol.update_layout(xaxis_title=None, yaxis_title="Taux (%)", height=300, plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_evol, use_container_width=True, config={'displayModeBar': False})

        # --- TOP 10 ---
        col_left, col_right = st.columns(2)
        with col_left:
            with st.container(border=True):
                st.subheader("👨‍🔧 Top 10 Techniciens")
                top_tech = df_f[df_f['Is_Repeat'] == 1].groupby('Technicien').size().reset_index(name='Repeats')
                top_tech = top_tech.sort_values(by='Repeats', ascending=True).tail(10)
                if not top_tech.empty:
                    fig_t = px.bar(top_tech, x='Repeats', y='Technicien', orientation='h', text='Repeats', color_discrete_sequence=['#004a99'])
                    fig_t.update_layout(xaxis_visible=False, yaxis_title=None, height=350, margin=dict(l=0, r=40, t=10, b=10), plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_t, use_container_width=True, config={'displayModeBar': False})

        with col_right:
            with st.container(border=True):
                st.subheader("📁 Top 10 Machines (SN)")
                top_sn = df_f[df_f['Is_Repeat'] == 1].groupby('SN').size().reset_index(name='Repeats')
                top_sn = top_sn.sort_values(by='Repeats', ascending=True).tail(10)
                if not top_sn.empty:
                    fig_s = px.bar(top_sn, x='Repeats', y='SN', orientation='h', text='Repeats', color_discrete_sequence=['#ff4b4b'])
                    fig_s.update_layout(xaxis_visible=False, yaxis_title=None, height=350, margin=dict(l=0, r=40, t=10, b=10), plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_s, use_container_width=True, config={'displayModeBar': False})

        with st.expander("🔍 Liste détaillée des Repeats"):
            st.dataframe(df_f[df_f['Is_Repeat'] == 1][['ID', 'Technicien', 'SN', 'Date', 'Ecart_Ouvres']], use_container_width=True)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_f.to_excel(writer, index=False)
        st.sidebar.download_button("📥 Télécharger Rapport (.xlsx)", buffer.getvalue(), "Arkeos_Performance.xlsx")

    else:
        st.warning("Aucune donnée disponible pour les filtres sélectionnés.")
else:
    st.error("❌ Fichier 'data_dynamics_brute.csv.csv' introuvable.")
