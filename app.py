import streamlit as st
import requests
import random
import string

st.set_page_config(page_title="M-TECH CORE | Startup Hub", page_icon="🚀", layout="wide")

# --- VYLEPŠENÉ UI / CSS STYLY ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3 { background: -webkit-linear-gradient(45deg, #0ea5e9, #10b981); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #0ea5e9; width: 100%; font-weight: 600;}
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(14, 165, 233, 0.4); border-color: #0ea5e9; }
    .hero-card { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 30px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 20px; text-align: center; }
    .feature-box { background: #1e293b; padding: 20px; border-radius: 8px; border-left: 4px solid #0ea5e9; margin-bottom: 10px; height: 100%; }
    .highlight { color: #0ea5e9; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

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
    st.error("Chybí konfigurace v Secrets!")
    st.stop()

# --- BEZPEČNOSTNÍ INICIALIZACE STAVU ---
if "prihlasen" not in st.session_state: st.session_state.prihlasen = False
if "role" not in st.session_state: st.session_state.role = None
if "kredity" not in st.session_state: st.session_state.kredity = 0
if "uzivatel" not in st.session_state: st.session_state.uzivatel = None

# ==========================================
# DEFINICE PŘIHLAŠOVACÍ OBRAZOVKY
# ==========================================
def login_screen():
    st.markdown("""
        <div class="hero-card">
            <h1 style="margin:0; font-size: 3em;">M-TECH <span class='highlight'>CORE</span> 🚀</h1>
            <p style="color: #94a3b8; font-size: 1.3em; margin-top: 10px;">
                Edukativní startupový ekosystém. Propojení škol, žáků a reálných byznysových procesů.
            </p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='feature-box'><h4 style='color:#f8fafc; margin-top:0;'>🎓 Pro Žáky</h4><p style='font-size: 0.9em; color: #cbd5e1;'>Získávají M-Kredity za práci na projektech a učí se finanční gramotnosti.</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='feature-box'><h4 style='color:#f8fafc; margin-top:0;'>🚀 Pro Startupy</h4><p style='font-size: 0.9em; color: #cbd5e1;'>Založení s.r.o., Lean Canvas, Agilní vývoj (Scrum), HR a evidence Cash-flow.</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='feature-box'><h4 style='color:#f8fafc; margin-top:0;'>⚖️ Pro Školy</h4><p style='font-size: 0.9em; color: #cbd5e1;'>Kontrolní úřad s kompletním dohledem nad audity, byrokracií a hodnocením.</p></div>", unsafe_allow_html=True)

    st.write("---")

    tab_login, tab_user_reg, tab_school_licence = st.tabs(["🔒 Přihlášení", "🤝 Registrace uživatele", "🏫 Objednávka pro školy"])
    
    with tab_login:
        with st.form("login_form"):
            jmeno = st.text_input("Přihlašovací jméno (Startup/Jméno):")
            heslo = st.text_input("Heslo:", type="password")
            if st.form_submit_button("Vstoupit do M-TECH CORE"):
                if jmeno and heslo:
                    try:
                        res = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{jmeno}&heslo=eq.{heslo}&select=*", headers=headers)
                        data = res.json()
                        if isinstance(data, list) and len(data) > 0:
                            uzivatel = data[0]
                            st.session_state.prihlasen = True
                            st.session_state.role = str(uzivatel.get("role", "ZAK")).upper()
                            st.session_state.kredity = uzivatel.get("kredity", 0)
                            st.session_state.uzivatel = uzivatel["jmeno"]
                            st.rerun()
                        else:
                            st.error("Nesprávné jméno nebo heslo!")
                    except Exception as e:
                        st.error(f"Chyba databáze: {e}")
                else:
                    st.warning("Vyplňte jméno a heslo.")

    with tab_user_reg:
        st.info("Máte licenční kód z vašeho Akcelerátoru (školy)? Zadejte jej níže.")
        with st.form("user_reg_form"):
            skolni_kod = st.text_input("Licenční kód akcelerátoru (školy):").upper().strip()
            reg_jmeno = st.text_input("Nové uživatelské jméno (Název firmy nebo příjmení):")
            reg_heslo = st.text_input("Heslo:", type="password")
            reg_role = st.selectbox("Typ účtu:", ["ZAK", "FIRMA", "UCITEL"])
            if st.form_submit_button("Vytvořit účet"):
                if skolni_kod and reg_jmeno and reg_heslo:
                    lic_res = requests.get(f"{SUPABASE_URL}/rest/v1/licencovane_skoly?licencni_kod=eq.{skolni_kod}&zaplaceno=eq.true", headers=headers)
                    if not lic_res.json():
                        st.error("Neplatný nebo dosud neaktivní licenční kód!")
                    else:
                        check_res = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{reg_jmeno}", headers=headers)
                        if len(check_res.json()) > 0:
                            st.error("Uživatelské jméno je již obsazené!")
                        else:
                            start_kredity = 100 if reg_role == "ZAK" else 300
                            requests.post(f"{SUPABASE_URL}/rest/v1/uzivatele", headers=headers, json={"jmeno": reg_jmeno, "heslo": reg_heslo, "role": reg_role, "kredity": start_kredity, "skolni_kod": skolni_kod})
                            st.success("Účet úspěšně vytvořen! Nyní se můžete přihlásit.")
                else:
                    st.warning("Vyplňte všechny údaje!")

    with tab_school_licence:
        st.subheader("Poptávka licencování pro školy")
        with st.form("school_form"):
            nazev_skoly = st.text_input("Název školy / organizace:")
            email = st.text_input("Kontaktní e-mail zástupce:")
            pocet_firem = st.number_input("Odhadovaný počet zapojených startupů:", min_value=1, value=5)
            pocet_zaku = st.number_input("Odhadovaný počet žáků:", min_value=10, value=100)
            if st.form_submit_button("Odeslat nezávaznou poptávku"):
                if nazev_skoly and email:
                    generovany_kod = "SKOLA-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                    requests.post(f"{SUPABASE_URL}/rest/v1/licencovane_skoly", headers=headers, json={"nazev_skoly": nazev_skoly, "kontaktni_email": email, "licencni_kod": generovany_kod, "max_firem": pocet_firem, "max_zaku": pocet_zaku, "zaplaceno": False, "uroven_projektu": 2})
                    st.success(f"Poptávka byla zaznamenána pod kódem **{generovany_kod}**.")
                else:
                    st.warning("Vyplňte prosím název školy i e-mail.")

# ==========================================
# DEFINICE ODHLÁŠENÍ A STRÁNEK
# ==========================================
def logout():
    st.session_state.prihlasen = False
    st.session_state.role = None
    st.session_state.uzivatel = None
    st.rerun()

# Definování jednotlivých stránek jako objektů st.Page
login_page = st.Page(login_screen, title="Úvod a Přihlášení", icon="🏠")
logout_page = st.Page(logout, title="Odhlásit se", icon="🚪")

# Načítání souborů z tvojí složky 'pages/'
zaci_page = st.Page("pages/1_Zaci.py", title="Moje peněženka", icon="💳")
firma_page = st.Page("pages/2_Firma.py", title="Firemní Hub", icon="🏢")
ucitel_page = st.Page("pages/3_Ucitel.py", title="Kontrolní úřad", icon="⚖️")

# ==========================================
# SMĚROVÁNÍ (ROUTING) - KDO VIDÍ CO
# ==========================================
if not st.session_state.prihlasen:
    # Pokud není přihlášen, vynuť zobrazení pouze Login obrazovky (Schová postranní panel)
    pg = st.navigation([login_page])
else:
    # Zjisti roli a ukaž jen to, co dotyčný smí vidět
    role = st.session_state.role
    pages_to_show = []
    
    if role == "ZAK": pages_to_show = [zaci_page]
    elif role == "FIRMA": pages_to_show = [firma_page, zaci_page]
    elif role == "UCITEL": pages_to_show = [ucitel_page]
    elif role == "ADMIN": pages_to_show = [zaci_page, firma_page, ucitel_page]
    
    # Přidej tlačítko "Odhlásit" nakonec menu pro všechny
    pages_to_show.append(logout_page)
    
    pg = st.navigation(pages_to_show)

pg.run()

# Doplňující informace v postranním panelu dole
if st.session_state.prihlasen:
    with st.sidebar:
        st.divider()
        st.markdown(f"👤 Uživatel: **{st.session_state.uzivatel}**")
        st.caption(f"Role: **{st.session_state.role}**")
        if st.session_state.role in ["ZAK", "FIRMA"]:
            st.markdown(f"💰 Zůstatek: **{st.session_state.kredity} M-K**")
