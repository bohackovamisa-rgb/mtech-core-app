import streamlit as st
import pandas as pd

st.set_page_config(page_title="Firemní Dashboard", page_icon=":material/insights:")
st.markdown("<style>@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap'); html, body, [class*='css'] {font-family: 'Montserrat', sans-serif !important;}</style>", unsafe_allow_html=True)

st.title(":material/insights: Management firmy (CFO)")
st.caption("Správa financí a odvod M-TECH daně")

st.metric("Firemní kapitál", "450 M-Kreditů")
st.metric("Očekávaná M-TECH Daň (15%)", "67 M-Kreditů")

st.subheader(":material/list_alt: Kniha příjmů a výdajů")
df = pd.DataFrame({
    "Položka": ["Prodej", "Nákup materiálu"],
    "Částka (M)": ["+150", "-45"]
})
st.dataframe(df, use_container_width=True, hide_index=True)
