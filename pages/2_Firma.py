import streamlit as st
import pandas as pd

st.set_page_config(page_title="Firemní Dashboard", page_icon=":material/insights:", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #00B4D8; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0, 180, 216, 0.4); border-color: #00B4D8; }
    </style>
""", unsafe_allow_html=True)

st.title(":material/insights: Management firmy (CFO)")
st.caption("Správa financí a odvod M-TECH daně")

col1, col2 = st.columns(2)
col1.metric("Firemní kapitál", "450 M-Kreditů")
col2.metric("Očekávaná M-TECH Daň (15%)", "67 M-Kreditů")

st.subheader(":material/list_alt: Kniha příjmů a výdajů")
df = pd.DataFrame({
    "Položka": ["Prodej", "Nákup materiálu"],
    "Částka (M)": ["+150", "-45"]
})
st.dataframe(df, use_container_width=True, hide_index=True)
