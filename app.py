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
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
except Exception:
    st.error("Chybí SUPABASE_URL nebo SUPABASE_KEY ve Streamlit Secrets!")
    st.stop()

# --- INICIALIZACE PAMĚTI ---
if "role" not in st.session_state:
    st.session_state.role = None
if "kredity" not in st.session_state:
    st.session_state.kredity = 0
if "uzivatel" not in st.session_state:
    st.session_state.uzivatel = None

# --- DEFINICE STRÁNEK ---
zaci_page = st.Page("pages/1_Zaci.py", title="Moje peněženka", icon=":material/wallet:")
firma_page = st.Page("pages/2_Firma.py", title="Firemní Dashboard", icon=":material/insights:")
ucitel_page = st.Page("pages/3_Ucitel.py", title="Kontrolní úřad", icon=":material/account_balance:")

# --- PŘIHLAŠOVACÍ A REGISTRAČNÍ BRÁNA ---
if st.session_state.role is None:
    st.title(":material/fingerprint: Vstup do M-TECH CORE")
    
    tab_login, tab_reg = st.tabs(["🔒 Přihlášení", "📝 Registrace nového účtu"])
    
    # 1. PŘIHLÁŠENÍ
    with tab_login:
        with st.form("login_form"):
            jmeno = st.text_input("Přihlašovací jméno:")
            heslo = st.text_input("Heslo:", type="password")
            submit = st.form_submit_button("Přihlásit se")
            
            if submit:
                endpoint = f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{jmeno}&heslo=eq.{heslo}&select=*"
                try:
                    odpoved = requests.get(endpoint, headers=headers)
                    data = odpoved.json()
                    
                    if isinstance(data, list) and len(data) > 0:
                        uzivatel = data[0]
                        st.session_state.role = uzivatel["role"]
                        st.session_state.kredity = uzivatel["kredity"]
                        st.session_state.uzivatel = uzivatel["jmeno"]
                        st.rerun()
                    else:
                        st.error("Nespravné přihlašovací údaje!")
                except Exception as e:
                    st.error(f"Chyba databáze: {e}")

    # 2. REGISTRACE
    with tab_reg:
        with st.form("reg_form"):
            reg_jmeno = st.text_input("Nové uživatelské jméno:")
            reg_heslo = st.text_input("Nové heslo:", type="password")
            reg_role = st.selectbox("Typ účtu / Role:", ["zak", "firma"])
            reg_submit = st.form_submit_button("Vytvořit účet")
            
            if reg_submit:
                if reg_jmeno and reg_heslo:
                    # Kontrola, zda už jméno neexistuje
                    check_res = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{reg_jmeno}", headers=headers)
                    if len(check_res.json()) > 0:
                        st.error("Toto uživatelské jméno je již obsazené!")
                    else:
                        # Výchozí kredity: 100 pro žáky, 300 pro firmy
                        start_kredity = 100 if reg_role == "zak" else 300
                        novy_uzivatel = {
                            "jmeno": reg_jmeno,
                            "heslo": reg_heslo,
                            "role": reg_role,
                            "kredity": start_kredity
                        }
                        reg_post = requests.post(f"{SUPABASE_URL}/rest/v1/uzivatele", headers=headers, json=novy_uzivatel)
                        if reg_post.status_code in [200, 201]:
                            st.success(f"Účet {reg_jmeno} byl úspěšně vytvořen! Nyní se můžete přihlásit.")
                        else:
                            st.error("Chyba při registrace nového účtu.")
                else:
                    st.warning("Vyplňte jméno i heslo.")

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
        st.markdown(f"Přihlášen: **{st.session_state.uzivatel}**")
        st.caption(f"Role: **{st.session_state.role.upper()}**")
        st.markdown(f"Zůstatek: **{st.session_state.kredity} M-Kreditů**")
        
        if st.button("Odhlásit se"):
            st.session_state.role = None
            st.session_state.uzivatel = None
            st.rerun()
