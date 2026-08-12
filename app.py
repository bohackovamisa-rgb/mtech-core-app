import streamlit as st

st.set_page_config(page_title="M-TECH CORE", page_icon=":material/hub:", layout="wide")

# --- VIZUÁLNÍ ŠMRNC (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #00B4D8; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0, 180, 216, 0.4); border-color: #00B4D8; }
    </style>
""", unsafe_allow_html=True)

# Inicializace paměti pro roli
if "role" not in st.session_state:
    st.session_state.role = None

# --- DEFINICE STRÁNEK ---
zaci_page = st.Page("pages/1_Zaci.py", title="Moje peněženka", icon=":material/wallet:")
firma_page = st.Page("pages/2_Firma.py", title="Firemní Dashboard", icon=":material/insights:")
ucitel_page = st.Page("pages/3_Ucitel.py", title="Kontrolní úřad", icon=":material/account_balance:")

# --- PŘIHLAŠOVACÍ BRÁNA ---
if st.session_state.role is None:
    st.title(":material/fingerprint: Systém uzamčen")
    st.info("Pro vstup do M-TECH CORE zadejte přihlašovací údaje (zak / firma / ucitel).")
    
    with st.form("login_form"):
        jmeno = st.text_input("Přihlašovací jméno:")
        heslo = st.text_input("Heslo:", type="password")
        submit = st.form_submit_button("Přihlásit se do systému")
        
        if submit:
            if jmeno == "zak" and heslo == "123":
                st.session_state.role = "zak"
                st.rerun()
            elif jmeno == "firma" and heslo == "123":
                st.session_state.role = "firma"
                st.rerun()
            elif jmeno == "ucitel" and heslo == "123":
                st.session_state.role = "ucitel"
                st.rerun()
            else:
                st.error("Špatné jméno nebo heslo!")

# --- DYNAMICKÉ ZOBRAZENÍ STRÁNEK PODLE ROLE ---
else:
    # Aplikace sestaví navigaci jen z těch stránek, na které má uživatel právo
    if st.session_state.role == "zak":
        pg = st.navigation([zaci_page])
    elif st.session_state.role == "firma":
        pg = st.navigation([firma_page])
    elif st.session_state.role == "ucitel":
        pg = st.navigation([ucitel_page])
    
    # Spuštění povolené stránky
    pg.run()
    
    # Přidání odhlašovacího tlačítka do bočního panelu
    with st.sidebar:
        st.divider()
        if st.button("Odhlásit se"):
            st.session_state.role = None
            st.rerun()
