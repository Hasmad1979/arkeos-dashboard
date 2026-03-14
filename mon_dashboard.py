import streamlit as st
import pandas as pd
import numpy as np
import os
import io

# 1. Configuration
st.set_page_config(page_title="Arkeos Performance", layout="wide")

# CSS pour forcer l'affichage des métriques en bleu
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 5px solid #004a99; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    div[data-testid="stSidebar"] { background-color: #004a99; color: white; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path)
        # Nettoyage des noms de colonnes
        df = df.rename(columns={
            "Numéro de l'incident": "ID", 
            "Actifs du client": "SN", 
            "Owner": "Technicien", 
            "Créé le": "Date"
        })
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['SN', 'Date'])
        df['SN'] = df['SN'].astype(str).str.strip()
        
        # Préparation Temps
        df['Année'] = df['Date'].dt.year
        df['Mois'] = df['Date'].dt.strftime('%B')
        df['Mois_Num'] = df['Date'].dt.month
        
        # Calcul Jours Ouvrés
        df = df.sort_values(['SN', 'Date'])
        df['Date_Prev'] = df.groupby('SN')['Date'].shift(1)
        
        def calc_bus(row):
            if pd.isnull(row['Date_Prev']): return None
            d1, d2 = row['Date_Prev'].date(), row['Date'].date()
            if d1 >= d2: return 0
            return np.busday_count(d1, d2)

        df['Ecart_Ouvres'] = df.apply(calc_bus, axis=1)
        df['Is_Repeat'] = ((df['Ecart_Ouvres'] >= 0) & (df['Ecart_Ouvres'] <= 22)).astype(int)
        return df
    except Exception as e:
        st.error(f"Erreur lors de la lecture du fichier : {e}")
        return None

# --- EXECUTION ---
path = "data_dynamics_brute.csv.csv"
df_raw = load_data(path)

if df_raw is not None:
    # Sidebar
    if os.path.exists("ark.png"):
        st.sidebar.image("ark.png")
    
    st.sidebar.title("🎮 Filtres")
    
    # On s'assure que les valeurs par défaut existent
    all_years = sorted(df_raw['Année'].unique().tolist(), reverse=True)
    all_techs = sorted(df_raw['Technicien'].unique().tolist())
    
    sel_years = st.sidebar.multiselect("Années", all_years, default=all_years)
    sel_techs = st.sidebar.multiselect("Techniciens", all_techs, default=all_techs)

    # Application du filtre
    df_f = df_raw[(df_raw['Année'].isin(sel_years)) & (df_raw['Technicien'].isin(sel_techs))]

    # --- AFFICHAGE ---
    st.title("📊 Arkeos Support Performance")

    if not df_f.empty:
        # KPI
        t_wo = len(df_f)
        r_cnt = df_f['Is_Repeat'].sum()
        rate = (r_cnt / t_wo * 100)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Interventions", f"{t_wo:,}")
        c2.metric("Vrais Repeats", f"{r_cnt:,}")
        c3.metric("Taux de Repeat", f"{rate:.1f}%")

        st.divider()

        tab1, tab2 = st.tabs(["📈 Graphiques", "📤 Export & Détails"])
        
        with tab1:
            st.subheader("Évolution Mensuelle")
            evol = df_f.groupby(['Année', 'Mois_Num', 'Mois'])['Is_Repeat'].mean() * 100
            st.line_chart(evol.reset_index(), x='Mois', y='Is_Repeat', color="#004a99")
            
            st.subheader("Top 5 Machines (SN)")
            st.bar_chart(df_f.groupby('SN')['Is_Repeat'].sum().sort_values(ascending=False).head(5), color="#ff4b4b")

        with tab2:
            st.subheader("Détail des données filtrées")
            st.dataframe(df_f[['ID', 'Technicien', 'SN', 'Date', 'Ecart_Ouvres', 'Is_Repeat']].tail(20))
            
            # Export
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_f.to_excel(writer, index=False)
            st.download_button("📥 Télécharger Impact Repeat (Excel)", buffer.getvalue(), "Export_Arkeos.xlsx")
    else:
        st.warning("⚠️ Aucune donnée trouvée pour cette sélection. Vérifiez vos filtres dans la barre latérale.")
        st.info(f"Note : Le fichier contient {len(df_raw)} lignes au total.")

else:
    st.error("❌ Fichier introuvable sur le Bureau. Vérifiez le nom du fichier CSV.")
