import streamlit as st
import pandas as pd

st.set_page_config(page_title="M-TECH CORE", page_icon="🪙", layout="centered")

st.title("🪙 M-TECH CORE — Školní Peněženka & Burza")
st.caption("Pilotní systém pro žáky a učitele")

col1, col2 = st.columns(2)
with col1:
    st.metric(label="Můj zůstatek", value="120 M-Kreditů", delta="+15 dnes")
with col2:
    st.metric(label="Hodnota portfolia", value="450 M-Kreditů", delta="+14.2% ↑")

st.divider()

st.subheader("📷 Zaplatit u stánku")
kod_stanku = st.text_input("Zadej kód stánku:", placeholder="např. STANEK-DILNY-01")
castka = st.number_input("Částka v M-Kreditech:", min_value=1, value=10)

if st.button("Odeslat M-Kredity 🚀", use_container_width=True):
    if kod_stanku:
        st.success(f"Úspěšně odesláno {castka} M-Kreditů na {kod_stanku}!")
    else:
        st.warning("Nejprve zadej kód stánku.")

st.divider()

st.subheader("📈 Školní Wall Street")
df = pd.DataFrame({
    "Školní Firma": ["Precision Mech a.s.", "RoboTech s.r.o.", "Print3D Lab"],
    "Cena akcie (M)": [45, 120, 85],
    "Změna 24h": ["+14.2%", "-2.1%", "+8.5%"]
})
st.dataframe(df, use_container_width=True, hide_index=True)
