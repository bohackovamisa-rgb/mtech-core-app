import streamlit as st

st.set_page_config(page_title="Kontrolní úřad", page_icon="🏛️")

st.title("🏛️ Kontrolní úřad M-TECH CORE")
st.caption("Panel pro učitele a garanty projektu")

st.subheader("Licenční řízení")
st.write("Zde budete vidět Zakladatelské listiny čekající na schválení.")
st.button("Schválit vybranou firmu")

st.divider()

st.subheader("Generátor M-Kreditů")
st.write("Vytváření bonusových QR voucherů pro aktivní žáky.")
st.number_input("Hodnota (M-Kredity)", min_value=1, value=50)
st.button("Vygenerovat Voucher")
