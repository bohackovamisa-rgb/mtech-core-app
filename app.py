import streamlit as st

st.set_page_config(page_title="M-TECH CORE", page_icon=":material/hub:", layout="wide")

# --- VIZUÁLNÍ ŠMRNC (CSS) ---
st.markdown("""
    <style>
    /* Písmo Montserrat */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Montserrat', sans-serif !important;
    }
    
    /* Moderní azurový gradient pro všechny nadpisy */
    h1, h2, h3 {
        background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
    }
    
    /* Efekty pro tlačítka (vznášení a záře) */
    .stButton>button {
        border-radius: 8px;
        transition: all 0.3s ease;
        border: 1px solid #00B4D8;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 180, 216, 0.4);
        border-color: #00B4D8;
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. BEZPEČNOSTNÍ ZÁMEK S PODPOROU ENTER ---
if "prihlasen" not in st.session_state:
    st.session_state.prihlasen = False

if not st.session_state.prihlasen:
    st.title(":material/fingerprint: Systém uzamčen")
    st.info("Pro vstup do M-TECH CORE zadejte přihlašovací údaje.")
    
    # st.form zajistí, že po stisknutí klávesy ENTER se formulář odešle
    with st.form("login_form"):
        jmeno = st.text_input("Přihlašovací jméno:")
        heslo = st.text_input("Heslo:", type="password")
        
        # Toto tlačítko nyní reaguje i na Enter
        submit = st.form_submit_button("Přihlásit se do systému")
        
        if submit:
            if jmeno == "admin" and heslo == "core2026":
                st.session_state.prihlasen = True
                st.rerun() # Znovu načte stránku, tentokrát už jako přihlášený
            else:
                st.error("Špatné jméno nebo heslo!")
                
    st.stop() # Zastaví vykreslování dalšího obsahu

# --- 2. OBSAH ÚVODNÍ STRÁNKY (po přihlášení) ---
st.title(":material/hub: Vítejte v M-TECH CORE")
st.markdown("""
**Praktická ekonomie v technickém vzdělávání.**

Tento portál slouží k obsluze virtuálních financí (M-Kreditů), správě studentských firem a komunikaci s Kontrolním úřadem.

:material/arrow_back: **Pro vstup do systému si vyberte svou roli v levém bočním menu.**
""")
