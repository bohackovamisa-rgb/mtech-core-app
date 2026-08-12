import streamlit as st
from supabase import create_client, Client

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

# --- PŘIPOJENÍ K DATABÁZI ---
# st.cache_resource zajistí, že se aplikace nepřipojuje k databázi zbytečně pořád dokola
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase: Client = init_connection()
except Exception as e:
    st.error("Chyba spojení s databází. Zkontroluj klíče ve Streamlit Secrets.")
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

# --- PŘIHLAŠOVACÍ BRÁNA (Nyní ověřuje přes databázi) ---
if st.session_state.role is None:
    st.title(":material/fingerprint: Systém uzamčen")
    st.info("Pro vstup do M-TECH CORE zadejte přihlašovací údaje.")
    
    with st.form("login_form"):
        jmeno = st.text_input("Přihlašovací jméno:")
        heslo = st.text_input("Heslo:", type="password")
        submit = st.form_submit_button("Přihlásit se do systému")
        
        if submit:
            # Zeptáme se databáze, jestli najde shodu jména a hesla
            odpoved = supabase.table("uzivatele").select("*").eq("jmeno", jmeno).eq("heslo", heslo).execute()
            
            # Pokud databáze něco vrátí (délka dat > 0), přihlášení je úspěšné
            if len(odpoved.data) > 0:
                uzivatel = odpoved.data[0]
                st.session_state.role = uzivatel["role"]
                st.session_state.kredity = uzivatel["kredity"] # Načteme reálné zůstatky z databáze!
                st.rerun()
            else:
                st.error("Špatné jméno nebo heslo!")

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
        # Rovnou do menu vypíšeme reálný stav kreditů z databáze
        st.markdown(f"Zůstatek: **{st.session_state.kredity} M-Kreditů**")
        
        if st.button("Odhlásit se"):
            st.session_state.role = None
            st.rerun()
