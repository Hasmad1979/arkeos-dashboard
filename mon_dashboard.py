import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px

# 1. CONFIGURATION
st.set_page_config(page_title="Arkeos Support", layout="wide")

@st.cache_data
def load_data():
    # Liste des noms possibles pour trouver votre fichier sur GitHub
    for f in ["data_dynamics_brute.csv.csv.csv", "data_dynamics_brute.csv"]:
        if os.path.exists(f):
            try:
                df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
                df.columns = [str(c).strip() for c in df.columns]
                
                # Mapping flexible (Dynamics FR/EN)
                m = {"Numéro de l'incident": "ID", "Incident Number": "ID",
                     "Actifs du client": "SN", "Customer Asset": "SN",
                     "Owner": "Tech", "Propriétaire": "Tech",
                     "Créé le": "Date", "Created On": "Date"}
                df = df.rename(columns=m)
                
                if 'Tech' not in df.columns: df['Tech'] = "Inconnu"
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df = df.dropna(subset=['SN', 'Date']).sort_values(['SN', 'Date'])
                
                # Calcul RDR 22j
                df['Prev'] = df.groupby('SN')['Date'].shift(1)
                def check(r):
                    if pd.isnull(r['Prev']): return 0
                    try:
                        diff = int(np.busday_count(r['Prev'].date(), r['Date'].date()))
                        return 1 if 0 <= diff <= 22 else 0
                    except: return 0
                df['Is_Repeat'] = df.apply(check, axis=1)
                return df
            except Exception as e:
                return f"Erreur lecture: {e}"
    return "Fichier CSV introuvable sur votre GitHub."

# 2. AFFICHAGE
data = load_data()

if isinstance(data, str):
    st.error(f"❌ {data}")
else:
    df = data
    st.title("📟 Arkeos Technical Dashboard")
    
    # Filtres simplifiés
    years = sorted(df['Date'].dt.year.unique(), reverse=True)
    sel_year = st.sidebar.multiselect("Année", years, default=years[:1])
    df_f = df[df['Date'].dt.year.isin(sel_year)]
    
    # KPIs
    t, r = len(df_f), df_f['Is_Repeat'].sum()
    rate = (r/t*100) if t > 0 else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Interventions", f"{t:,}")
    c2.metric("RDR % (22j)", f"{rate:.1f}%")
    c3.metric("Nb Repeats", f"{r:,}")

    # Graphique
    st.subheader("📈 Tendance")
    df_f['W'] = df_f['Date'].dt.isocalendar().week
    weekly = df_f.groupby('W')['Is_Repeat'].mean() * 100
    st.plotly_chart(px.line(weekly, labels={'value':'RDR %'}), use_container_width=True)
