import streamlit as st

st.set_page_config(page_title="Firemní Dashboard", page_icon=":material/insights:", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    </style>
""", unsafe_allow_html=True)

st.title(":material/insights: Firemní Dashboard")
st.info("Přehled firemního účtu v M-TECH CORE.")

if "kredity" not in st.session_state:
    st.session_state.kredity = 0

st.metric("Firemní kapitál", f"{st.session_state.kredity} M-Kreditů")
st.write("---")
st.subheader("Správa zakázek")
st.caption("Příjem a vyplácení odměn studentům za hotové projekty.")
