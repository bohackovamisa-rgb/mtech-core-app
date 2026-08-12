import streamlit as st

st.set_page_config(page_title="Moje peněženka", page_icon=":material/wallet:", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #00B4D8; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0, 180, 216, 0.4); border-color: #00B4D8; }
    </style>
""", unsafe_allow_html=True)

st.title(":material/wallet: Moje peněženka (Zákazník)")
st.info("Zde žáci uvidí svůj zůstatek M-Kreditů a budou moci platit pomocí QR kódů.")

col1, col2 = st.columns(2)
with col1:
    st.metric("Aktuální zůstatek", "100 M-Kreditů")
with col2:
    st.text_input("Naskenujte nebo zadejte QR kód pro platbu:")
    if st.button("Odeslat platbu"):
        st.success("Platba proběhla úspěšně!")
