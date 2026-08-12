import streamlit as st

st.set_page_config(page_title="Moje peněženka", page_icon="👨‍🎓")

st.title("👨‍🎓 Moje peněženka (Zákazník)")
st.info("Zde žáci uvidí svůj zůstatek M-Kreditů a budou moci platit pomocí QR kódů.")

st.metric("Aktuální zůstatek", "100 M-Kreditů")
st.text_input("Naskenujte nebo zadejte QR kód pro platbu:")
st.button("Odeslat platbu")
