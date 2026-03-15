import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import plotly.express as px

# 1. CONFIGURATION
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
    
    # Mapping des colonnes basé sur votre Excel
    mapping = {
        "Numéro de l'incident": "ID", 
        "Actifs du client": "SN", 
        "Owner": "Technicien", 
        "Créé le": "Date",
        "Type d'incident 2": "Panne" 
    }
    df = df.rename(columns=mapping)
    
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['SN', 'Date']).sort_values(['SN', 'Date'])
    
    # Calcul Repeat (22 jours ouvrés)
    df['Date_Prev'] = df.groupby('SN')['Date'].shift(1)
    def calc_bus(row):
        if pd.isnull(row['Date_Prev']): return None
        try:
            d1, d2 = row['Date_Prev'].date(), row['Date'].date()
            return int(np.busday_count(d1, d2)) if d1 < d2 else 0
        except: return 0
    df['Ecart_Ouvres'] = df.apply(calc_bus, axis=1)
    df['Is_Repeat'] = ((df['Ecart_Ouvres'] >= 0) & (df['Ecart_Ouvres'] <= 22)).astype(int)
    return df

df_raw = load_data()

if df_raw is not None:
    noms_mois = {1:'Janvier', 2:'Février', 3:'Mars', 4:'Avril', 5:'Mai', 6:'Juin', 
                 7:'Juillet', 8:'Août', 9:'Septembre', 10:'Octobre', 11:'Novembre', 12:'Décembre'}

    # --- SIDEBAR FILTRES ---
    st.sidebar.title("🎮 Filtres")
    
    # Années
    years = sorted(df_raw['Date'].dt.year.unique(), reverse=True)
    sel_years = st.sidebar.multiselect("Années", years, default=years)
    
    # Mois
    df_raw['Mois_Num'] = df_raw['Date'].dt.month
    df_raw['Mois_Nom'] = df_raw['Mois_Num'].map(noms_mois)
    available_months = sorted(df_raw['Mois_Num'].unique())
    month_options = [noms_mois[m] for m in available_months]
    sel_months = st.sidebar.multiselect("Mois", month_options, default=month_options)
    
    # Techniciens
    techs = sorted(df_raw['Technicien'].astype(str).unique().tolist())
    sel_techs = st.sidebar.multiselect("Techniciens", techs, default=techs)
    
    # Application des filtres
    df_f = df_raw[
        (df_raw['Date'].dt.year.isin(sel_years)) & 
        (df_raw['Mois_Nom'].isin(sel_months)) &
        (df_raw['Technicien'].isin(sel_techs))
    ].copy()

    st.title("📊 Arkeos Technical Support Dashboard")
    st.markdown("---")

    if not df_f.empty:
        # --- 1. KPI ---
        total_int = len(df_f)
        total_rep = df_f['Is_Repeat'].sum()
        repeat_rate = (total_rep / total_int * 100) if total_int > 0 else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Interventions", f"{total_int:,}")
        c2.metric("Total Repeats", f"{total_rep:,}")
        c3.metric("Taux de Repeat", f"{repeat_rate:.1f}%", delta=f"{repeat_rate:.1f}%", delta_color="inverse")
        c4.metric("FTTR Rate", f"{100 - repeat_rate:.1f}%")

        # --- 2. ÉVOLUTION MENSUELLE ---
        st.write("")
        with st.container(border=True):
            st.subheader("📈 Évolution Mensuelle du Taux de Repeat")
            evol = df_f.groupby('Mois_Num')['Is_Repeat'].mean() * 100
            evol = evol.reset_index()
            evol['Mois_Label'] = evol['Mois_Num'].map(noms_mois)
            
            labels = [f"{v:.1f}%" for v in evol['Is_Repeat']]
            fig_evol = px.line(evol, x='Mois_Label', y='Is_Repeat', markers=True, text=labels)
            fig_evol.update_traces(line_color='#004a99', line_width=3, textposition="top center")
            fig_evol.update_layout(xaxis_title=None, yaxis_title="Taux (%)", height=300, plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_evol, use_container_width=True)

        # --- 3. TOP 10 (PANNES & MACHINES) ---
        col_left, col_right = st.columns(2)
        
        with col_left:
            with st.container(border=True):
                st.subheader("🛠️ Top 10 Types de Panne")
                if "Panne" in df_f.columns:
                    top_p = df_f[df_f['Is_Repeat'] == 1].groupby('Panne').size().reset_index(name='Repeats')
                    top_p = top_p.sort_values(by='Repeats', ascending=True).tail(10)
                    fig_p = px.bar(top_p, x='Repeats', y='Panne', orientation='h', text='Repeats', color_discrete_sequence=['#004a99'])
                    fig_p.update_layout(xaxis_visible=False, yaxis_title=None, height=400, plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_p, use_container_width=True)

        with col_right:
            with st.container(border=True):
                st.subheader("📁 Top 10 Machines (SN)")
                top_sn = df_f[df_f['Is_Repeat'] == 1].groupby('SN').size().reset_index(name='Repeats')
                top_sn = top_sn.sort_values(by='Repeats', ascending=True).tail(10)
                fig_s = px.bar(top_sn, x='Repeats', y='SN', orientation='h', text='Repeats', color_discrete_sequence=['#ff4b4b'])
                fig_s.update_layout(xaxis_visible=False, yaxis_title=None, height=400, plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_s, use_container_width=True)

        # --- 4. EXPORT EXCEL ---
        st.write("")
        buffer = io.BytesIO()
        # On exporte uniquement les repeats pour que le fichier soit utile
        df_repeats = df_f[df_f['Is_Repeat'] == 1].copy()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_repeats.to_excel(writer, index=False, sheet_name='Repeats')
        
        st.sidebar.markdown("---")
        st.sidebar.download_button(
            label="📥 Télécharger les Repeats (Excel)",
            data=buffer.getvalue(),
            file_name="arkeos_repeats_list.xlsx",
            mime="application/vnd.ms-excel"
        )

    else:
        st.warning("⚠️ Aucune donnée ne correspond à vos filtres.")
else:
    st.error("❌ Fichier de données introuvable.")
