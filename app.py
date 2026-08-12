import streamlit as st
import requests

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

# --- NAČTENÍ KLÍČŮ ZE SECRETS ---
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    st.error("Chybí SUPABASE_URL nebo SUPABASE_KEY ve Streamlit Secrets!")
    st.stop()

# --- INICIALIZACE PAMĚTI ---
if "role" not in st.session_state:
    st.session_state.role = None
if "kredity" not in st.session_state:
    st.session_state.kredity = 0

# --- DEFINICE STRÁNEK ---
zaci_page = st.Page("pages/1_Zaci.py", title="Moje peněženka", icon=":material/wallet:")
firma_page = st.Page("pages/2_Firma.py", title="Firemní Dashboard", icon=":material/insights:")
ucitel_page = st.Page("pages/3_Ucitel.py", title="Kontrolní úřad", icon=":material/account_balance:")

# --- PŘIHLAŠOVACÍ BRÁNA (Přímé HTTP REST API spojení) ---
if st.session_state.role is None:
    st.title(":material/fingerprint: Systém uzamčen")
    st.info("Pro vstup do M-TECH CORE zadejte přihlašovací údaje.")
    
    with st.form("login_form"):
        jmeno = st.text_input("Přihlašovací jméno:")
        heslo = st.text_input("Heslo:", type="password")
        submit = st.form_submit_button("Přihlásit se do systému")
        
        if submit:
            # Přímo oslovíme REST API Supabase
            endpoint = f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{jmeno}&heslo=eq.{heslo}&select=*"
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}"
            }
            
            try:
                odpoved = requests.get(endpoint, headers=headers)
                data = odpoved.json()
                
                if isinstance(data, list) and len(data) > 0:
                    uzivatel = data[0]
                    st.session_state.role = uzivatel["role"]
                    st.session_state.kredity = uzivatel["kredity"]
                    st.rerun()
                else:
                    st.error("Špatné jméno nebo heslo!")
            except Exception as e:
                st.error(f"Chyba při komunikaci s databází: {e}")

# --- DYNAMICKÉ ZOBRAZENÍ STRÁNEK PODLE ROLE ---
else:
    if st.session_state.role == "zak":
        pg = st.navigation([zaci_page])
    elif st.session_state.role == "firma":
        pg = st.navigation([firma_page])
    elif st.session_state.role == "ucitel":
        pg = st.navigation([ucitel_page])
    elif st.session_state.role == "admin":
        pg = st.navigation([zaci_page, firma_page, ucitel_page])
    
    pg.run()
    
    with st.sidebar:
        st.divider()
        st.caption(f"Role: **{st.session_state.role.upper()}**")
        st.markdown(f"Zůstatek: **{st.session_state.kredity} M-Kreditů**")
        
        if st.button("Odhlásit se"):
            st.session_state.role = None
            st.rerun()
