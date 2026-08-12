import streamlit as st

st.set_page_config(page_title="Kontrolní úřad", page_icon=":material/account_balance:", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #00B4D8; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0, 180, 216, 0.4); border-color: #00B4D8; }
    </style>
""", unsafe_allow_html=True)

st.title(":material/account_balance: Kontrolní úřad M-TECH CORE")
st.caption("Panel pro učitele a garanty projektu")

st.subheader(":material/gavel: Licenční řízení")
st.write("Zde budete vidět Zakladatelské listiny čekající na schválení.")
if st.button("Schválit vybranou firmu"):
    st.success("Firma byla schválena.")

st.divider()

st.subheader(":material/qr_code: Generátor M-Kreditů")
st.write("Vytváření bonusových QR voucherů pro aktivní žáky.")
st.number_input("Hodnota (M-Kredity)", min_value=1, value=50)
if st.button("Vygenerovat Voucher"):
    st.success("Voucher byl úspěšně vygenerován!")
