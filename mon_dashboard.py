import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px

# -----------------------------------------------------------
# CONFIG
# -----------------------------------------------------------
st.set_page_config(layout="wide", page_title="Arkeos Dashboard")

# -----------------------------------------------------------
# LOAD DATA
# -----------------------------------------------------------
@st.cache_data
def load():
    file_name = "data_dynamics_brute.csv.csv.csv"

    if not os.path.exists(file_name):
        return "Fichier introuvable"

    try:
        df = pd.read_csv(
            file_name,
            sep=None,
            engine='python',
            encoding_errors='ignore'
        )

        # Nettoyage colonnes
        df.columns = [str(c).strip() for c in df.columns]

        for c in df.columns:
            lc = c.lower()

            if any(x in lc for x in ['date', 'créé']):
                df = df.rename(columns={c: 'Date'})

            if any(x in lc for x in ['actif', 'asset', 'sn']):
                df = df.rename(columns={c: 'SN'})

            if any(x in lc for x in ['owner', 'propriétaire', 'tech']):
                df = df.rename(columns={c: 'Tech'})

        # Conversion
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Tech'] = df['Tech'].fillna('Inconnu').astype(str)

        # Nettoyage doublons
        df = df.dropna(subset=['Date', 'SN'])
        df = df.drop_duplicates(subset=['Date', 'SN'])
        df = df.sort_values('Date')

        # Colonne précédente (P)
        df['P'] = df.groupby('SN')['Date'].shift(1)

        # Calcul RDR
        def rdr_calc(row):
            try:
                days = int(np.busday_count(row['P'].date(), row['Date'].date()))
                return 1 if 0 <= days <= 22 else 0
            except:
                return 0

        df['R'] = df.apply(rdr_calc, axis=1)

        return df

    except Exception as e:
        return f"Erreur: {e}"

# Chargement
d = load()

# -----------------------------------------------------------
# ERROR HANDLING
# -----------------------------------------------------------
if isinstance(d, str):
    st.error(d)
    st.stop()

# -----------------------------------------------------------
# UI & FILTRES
# -----------------------------------------------------------
st.title("📟 Arkeos Dashboard")

years = sorted(d['Date'].dt.year.unique().tolist(), reverse=True)
selected_years = st.sidebar.multiselect("Année", years, default=years[:1])

techs = sorted(d['Tech'].unique().tolist())
selected_tech = st.sidebar.selectbox("Technicien", ["Tous"] + techs)

df = d[d['Date'].dt.year.isin(selected_years)]

if selected_tech != "Tous":
    df = df[df['Tech'] == selected_tech]

# -----------------------------------------------------------
# KPIs
# -----------------------------------------------------------
total = len(df)
repeat = df['R'].sum()
pct_rdr = (repeat / total * 100) if total > 0 else 0
pct_fttr = 100 - pct_rdr

c1, c2, c3, c4 = st.columns(4)
c1.metric("Interventions", f"{total}")
c2.metric("RDR %", f"{pct_rdr:.1f}%")
c3.metric("FTTR %", f"{pct_fttr:.1f}%")
c4.metric("Repeats", f"{repeat}")

# -----------------------------------------------------------
# GRAPHIQUE MENSUEL CORRIGÉ
# -----------------------------------------------------------
st.subheader("📈 Tendance Mensuelle (%)")

tr = (
    df.groupby(df['Date'].dt.to_period('M'))['R']
      .mean() * 100
)

# Conversion en timestamp sans doublons
tr.index = tr.index.to_timestamp(how='start')

fig = px.line(
    tr,
    labels={'value': '% RDR', 'index': 'Date'},
    title="Tendance Mensuelle (%)",
    markers=True
)

st.plotly_chart(fig, use_container_width=True)
