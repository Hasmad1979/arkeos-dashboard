import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# --- CONFIG ---
st.set_page_config(layout="wide", page_title="Arkeos Dash")

st.markdown("""
<style>
    div[data-testid="stMetric"] {
        background-color: white; padding: 15px;
        border-radius: 10px; border: 1px solid #eef2f6;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    f = "data_dynamics_brute.csv.csv.csv"
    try:
        df = pd.read_csv(f, sep=None, engine='python', encoding_errors='ignore')
        # Mapping simplifié
        m = {'date':'Date','créé':'Date','actif':'SN','asset':'SN','sn':'SN','owner':'Tech','tech':'Tech','client':'Client'}
        new_c = {}
        for c in df.columns:
            for k, v in m.items():
                if k in str(c).lower(): new_c[c] = v
        df = df.rename(columns=new_c)
        if 'Date' not in df.columns or 'SN' not in df.columns: return pd.DataFrame()
        
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date', 'SN']).sort_values('Date')
        
        for c in ['Tech', 'Client']:
            if c not in df.columns: df[c] = 'N/A'
            df[c] = df[c].fillna('N/A').astype(str)
            
        df = df.drop_duplicates(subset=['SN', 'Date']).reset_index(drop=True)
        df['P'] = df.groupby('SN')['Date'].shift(1)
        df['R'] = (df['Date'] - df['P']).dt.days.apply(lambda x: 1 if (0 <= x <= 22) else 0)
        return df
    except: return pd.DataFrame()

df_raw = load_data()

if df_raw.empty:
    st.error("Données invalides.")
else:
    # --- SIDEBAR ---
    yrs = sorted(df_raw['Date'].dt.year.unique().tolist(), reverse=True)
    s_y = st.sidebar.multiselect("Années", yrs, default=yrs[:1])
