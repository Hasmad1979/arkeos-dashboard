# --- STYLE PERSONNALISÉ (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #F8F9FA; }
    div[data-testid="metric-container"] {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #E5E7EB;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGO & FILTRES ---
with st.sidebar:
    st.image("download.png", width=280) #
    st.markdown("### 🔍 Paramètres")
    # ... vos filtres ici ...
