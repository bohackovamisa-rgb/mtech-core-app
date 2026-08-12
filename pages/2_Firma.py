import streamlit as st
import pandas as pd

st.set_page_config(page_title="Firemní Dashboard", page_icon="🏢")

st.title("🏢 Management firmy (CFO)")
st.caption("Správa financí a odvod M-TECH daně")

st.metric("Firemní kapitál", "450 M-Kreditů")
st.metric("Očekávaná M-TECH Daň (15%)", "67 M-Kreditů")

st.subheader("Kniha příjmů a výdajů")
# Prozatím jen ukázková (falešná) data, později napojíme na reálnou databázi
df = pd.DataFrame({
    "Položka": ["Prodej", "Nákup materiálu"],
    "Částka (M)": ["+150", "-45"]
})
st.dataframe(df, use_container_width=True, hide_index=True)
