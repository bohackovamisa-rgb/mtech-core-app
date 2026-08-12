import streamlit as st

st.set_page_config(page_title="Moje peněženka", page_icon=":material/wallet:")
st.markdown("<style>@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap'); html, body, [class*='css'] {font-family: 'Montserrat', sans-serif !important;}</style>", unsafe_allow_html=True)

st.title(":material/wallet: Moje peněženka (Zákazník)")
st.info("Zde žáci uvidí svůj zůstatek M-Kreditů a budou moci platit pomocí QR kódů.")

st.metric("Aktuální zůstatek", "100 M-Kreditů")
st.text_input("Naskenujte nebo zadejte QR kód pro platbu:")
if st.button("Odeslat platbu"):
    st.success("Platba proběhla úspěšně!")
