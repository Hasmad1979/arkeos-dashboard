import streamlit as st
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="Arkeos", layout="wide")

@st.cache_data
def load_data():
    f = "data_dynamics_brute.csv.csv.csv"
    if not os.path.exists(f): return "Fichier introuvable sur GitHub"
    try:
        # 1. Lecture
        df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
        df.columns = [str(c).strip() for c in df.columns]
        
        # 2. Recherche automatique de la colonne MACHINE (SN)
        for c in df.columns:
            # On cherche des mots clés comme 'actif', 'asset', 'serial', 'sn'
            if any(x in c.lower() for x in ['actif', 'asset', 'serial', 'sn', 'machine']):
                df = df.rename(columns={c: 'SN'})
                break
        
        # 3. Recherche automatique de la colonne DATE
        for c in df.columns:
            if any(x in c.lower() for x in ['date', 'créé', 'created']):
                df = df.rename(columns={c: 'Date'})
                break

        # Vérification si colonnes trouvées
        if 'SN' not in df.columns or 'Date' not in df.columns:
            return f"Colonnes introuvables. Colonnes lues : {list(df.columns)[:5]}"

        # 4. Nettoyage et Calcul
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
        
        df['P'] = df.groupby('SN')['Date'].shift(1)
        def rdr(r):
            try:
                d = int(np.busday_count(r['P'].date(), r['Date'].date()))
                return 1 if 0 <= d <= 22 else 0
            except: return 0
        df['Is_R'] = df.apply(rdr, axis=1)
        return df
    except Exception as e: return f"Erreur : {e}"

# --- AFFICHAGE ---
d = load_data()
if isinstance(d, str):
    st.error(d)
    st.info("Conseil : Vérifiez que votre export Dynamics contient bien une colonne avec le numéro de série de la machine.")
else:
    st.title("📟 Arkeos Dashboard")
    t, r = len(d), d['Is_R'].sum()
    k1, k2, k3 = st.columns(3)
    k1.metric("Interventions", f"{t}")
    k2.metric("Taux RDR", f"{(r/t*100):.1f}%" if t>0 else "0%")
    k3.metric("Repeats", f"{r}")
    
    st.subheader("📈 Tendance Mensuelle")
    st.line_chart(d.set_index('Date')['Is_R'].resample('ME').mean() * 100)
