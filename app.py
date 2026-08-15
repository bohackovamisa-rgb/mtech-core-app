import streamlit as st
import requests
import random
import string

st.set_page_config(page_title="M-TECH CORE", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #00B4D8; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0, 180, 216, 0.4); border-color: #00B4D8; }
    .hero-card { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 25px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}
except Exception:
    st.error("Chybí konfigurace v Secrets!")
    st.stop()

# Inicializace prázdných proměnných
if "prihlasen" not in st.session_state: st.session_state.prihlasen = False
if "role" not in st.session_state: st.session_state.role = None
if "kredity" not in st.session_state: st.session_state.kredity = 0
if "uzivatel" not in st.session_state: st.session_state.uzivatel = None
if "skolni_kod" not in st.session_state: st.session_state.skolni_kod = None
if "trida_nazev" not in st.session_state: st.session_state.trida_nazev = None
if "firma_id" not in st.session_state: st.session_state.firma_id = None
if "firma_nazev" not in st.session_state: st.session_state.firma_nazev = None

# =========================================================================
# NEPRŮSTŘELNÝ AUTO-LOGIN PŘI F5 (Z URL PARAMETRU)
# =========================================================================
qs_user = st.query_params.get("user")
if not st.session_state.prihlasen and qs_user:
    res_auto = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{qs_user}&select=*", headers=headers).json()
    if isinstance(res_auto, list) and len(res_auto) > 0:
        st.session_state.prihlasen = True
        st.session_state.role = str(res_auto[0]["role"]).lower()
        st.session_state.kredity = res_auto[0]["kredity"]
        st.session_state.uzivatel = res_auto[0]["jmeno"]
        st.session_state.skolni_kod = res_auto[0].get("skolni_kod", "")
        st.session_state.trida_nazev = res_auto[0].get("trida_nazev", "")

# DEFINICE STRÁNEK
zaci_page = st.Page("pages/1_Zaci.py", title="Moje peněženka")
firma_page = st.Page("pages/2_Firma.py", title="Firemní Dashboard")
ucitel_page = st.Page("pages/3_Ucitel.py", title="Kontrolní úřad")
trh_page = st.Page("pages/4_Trh.py", title="Tržiště produktů")
zebricky_page = st.Page("pages/5_Zebricky.py", title="Síň slávy")
lean_page = st.Page("pages/6_AI_Lean_Startup.py", title="Lean Startup Validator")

ma_pristup_k_firme = False
moje_firemni_pozice = None

# Pokud je uživatel přihlášen, zjistíme jeho firmu a uložíme si ji do Session State
if st.session_state.prihlasen and st.session_state.uzivatel and st.session_state.role in ["zak", "firma"]:
    u_name = str(st.session_state.uzivatel).strip().lower()
    sk_kod = st.session_state.get("skolni_kod", "")
    
    r_firmy = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?skolni_kod=eq.{sk_kod}&select=*", headers=headers).json()
    if isinstance(r_firmy, list):
        for f in r_firmy:
            # Bezpečné získání názvu firmy (obchodni_firma nebo nazev)
            jmeno_firmy = f.get("obchodni_firma", f.get("nazev", "Firemní tým"))
            
            if str(f.get('ceo_jmeno','')).lower() == u_name:
                ma_pristup_k_firme = True
                moje_firemni_pozice = "CEO"
                st.session_state.firma_id = f.get("id")
                st.session_state.firma_nazev = jmeno_firmy
                break
            elif str(f.get('cfo_jmeno','')).lower() == u_name:
                ma_pristup_k_firme = True
                moje_firemni_pozice = "CFO"
                st.session_state.firma_id = f.get("id")
                st.session_state.firma_nazev = jmeno_firmy
                break
            elif str(f.get('cto_jmeno','')).lower() == u_name:
                ma_pristup_k_firme = True
                moje_firemni_pozice = "CTO"
                st.session_state.firma_id = f.get("id")
                st.session_state.firma_nazev = jmeno_firmy
                break
                
    if not ma_pristup_k_firme:
        r_zam = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?jmeno_zamestnance=ilike.{u_name}&select=*", headers=headers).json()
        if isinstance(r_zam, list) and len(r_zam) > 0:
            ma_pristup_k_firme = True
            moje_firemni_pozice = r_zam[0].get("pozice", "Zaměstnanec")
            st.session_state.firma_id = r_zam[0].get("firma_id")
            st.session_state.firma_nazev = r_zam[0].get("firma_nazev", "Tým")

if not st.session_state.prihlasen:
    st.markdown("""
        <div class="hero-card">
            <h1 style="margin:0; font-size: 2.5em;">M-TECH CORE</h1>
            <p style="color: #94a3b8; font-size: 1.2em; margin-top: 5px;">Digitální ekosystém pro propojení škol, žáků a reálných firemních zakázek.</p>
        </div>
    """, unsafe_allow_html=True)

    with st.form("main_login_form"):
        jmeno = st.text_input("Přihlašovací jméno:")
        heslo = st.text_input("Heslo:", type="password")
        if st.form_submit_button("Vstoupit do ekosystému"):
            if jmeno and heslo:
                res = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{jmeno}&heslo=eq.{heslo}&select=*", headers=headers).json()
                if isinstance(res, list) and len(res) > 0:
                    st.session_state.prihlasen = True
                    st.session_state.role = str(res[0]["role"]).lower()
                    st.session_state.kredity = res[0]["kredity"]
                    st.session_state.uzivatel = res[0]["jmeno"]
                    st.session_state.skolni_kod = res[0].get("skolni_kod", "")
                    st.session_state.trida_nazev = res[0].get("trida_nazev", "")
                    # Uložení do URL
                    st.query_params["user"] = res[0]["jmeno"]
                    st.rerun()
                else:
                    st.error("Nesprávné přihlašovací údaje.")
            else:
                st.warning("Vyplňte obě pole.")
else:
    with st.sidebar:
        st.markdown(f"Uživatel: **{st.session_state.uzivatel}**")
        st.caption(f"Role: **{moje_firemni_pozice if moje_firemni_pozice else st.session_state.role.upper()}**")
        st.markdown(f"Zůstatek: **{st.session_state.kredity} M-K**")
        
        if st.button("Odhlásit se", type="primary"):
            st.query_params.clear()
            st.session_state.clear()
            st.rerun()
            
    if st.session_state.role == "ucitel":
        pg = st.navigation([ucitel_page, trh_page, zebricky_page, lean_page])
    elif st.session_state.role == "admin":
        pg = st.navigation([zaci_page, firma_page, ucitel_page, trh_page, zebricky_page, lean_page])
    elif st.session_state.role == "firma" or ma_pristup_k_firme:
        pg = st.navigation([firma_page, zaci_page, trh_page, zebricky_page, lean_page])
    else:
        pg = st.navigation([zaci_page, trh_page, zebricky_page])
    
    pg.run()
