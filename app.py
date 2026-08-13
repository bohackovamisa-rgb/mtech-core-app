import streamlit as st
import requests
import random
import string

st.set_page_config(page_title="M-TECH CORE", page_icon=":material/hub:", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #00B4D8; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0, 180, 216, 0.4); border-color: #00B4D8; }
    .hero-card { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 25px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 20px; }
    .feature-box { background: #1e293b; padding: 15px; border-radius: 8px; border-left: 4px solid #00B4D8; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}
except Exception:
    st.error("Chybí konfigurace v Secrets!")
    st.stop()

if "prihlasen" not in st.session_state: st.session_state.prihlasen = False
if "role" not in st.session_state: st.session_state.role = None
if "kredity" not in st.session_state: st.session_state.kredity = 0
if "uzivatel" not in st.session_state: st.session_state.uzivatel = None

zaci_page = st.Page("pages/1_Zaci.py", title="Moje peněženka", icon=":material/wallet:")
firma_page = st.Page("pages/2_Firma.py", title="Firemní Dashboard", icon=":material/insights:")
ucitel_page = st.Page("pages/3_Ucitel.py", title="Kontrolní úřad", icon=":material/account_balance:")
trh_page = st.Page("pages/4_Trh.py", title="Tržiště produktů", icon=":material/shopping_cart:")
zebricky_page = st.Page("pages/5_Zebricky.py", title="Síň slávy", icon=":material/emoji_events:")

if not st.session_state.prihlasen:
    st.markdown("""
        <div class="hero-card">
            <h1 style="margin:0; font-size: 2.5em;">M-TECH CORE</h1>
            <p style="color: #94a3b8; font-size: 1.2em; margin-top: 5px;">
                Digitální ekosystém pro propojení škol, žáků a reálných firemních zakázek.
            </p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1: st.markdown("<div class='feature-box'><h4>Pro Žáky</h4><p style='font-size: 0.9em; color: #cbd5e1;'>Získávají M-Kredity za plnění úkolů a učí se pracovat s digitální peněženkou.</p></div>", unsafe_allow_html=True)
    with col2: st.markdown("<div class='feature-box'><h4>Pro Firmy</h4><p style='font-size: 0.9em; color: #cbd5e1;'>Vypisují zakázky, nabízí produkty a spravují kapitál v dashboardu.</p></div>", unsafe_allow_html=True)
    with col3: st.markdown("<div class='feature-box'><h4>Pro Školy</h4><p style='font-size: 0.9em; color: #cbd5e1;'>Kontrolní úřad s dohledem nad transakcemi a ekonomikou.</p></div>", unsafe_allow_html=True)

    st.write("---")

    tab_login, tab_user_reg, tab_school_licence = st.tabs(["Přihlášení do systému", "Registrace účtu", "Nová licence školy"])
    
    with tab_login:
        with st.form("login_form"):
            jmeno = st.text_input("Přihlašovací jméno:")
            heslo = st.text_input("Heslo:", type="password")
            if st.form_submit_button("Vstoupit do ekosystému"):
                if jmeno and heslo:
                    res = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{jmeno}&heslo=eq.{heslo}&select=*", headers=headers).json()
                    if res:
                        st.session_state.prihlasen = True
                        st.session_state.role = str(res[0]["role"]).lower()
                        st.session_state.kredity = res[0]["kredity"]
                        st.session_state.uzivatel = res[0]["jmeno"]
                        st.rerun()
                    else:
                        st.error("Nesprávné přihlašovací údaje.")
                else:
                    st.warning("Vyplňte obě pole.")

    with tab_user_reg:
        st.info("Pro registraci zadejte licenční kód vaší školy.")
        with st.form("user_reg_form"):
            skolni_kod = st.text_input("Licenční kód školy:").upper().strip()
            reg_jmeno = st.text_input("Uživatelské jméno:")
            reg_heslo = st.text_input("Heslo:", type="password")
            reg_role = st.selectbox("Typ účtu:", ["zak", "firma", "ucitel"])
            if st.form_submit_button("Vytvořit účet"):
                if skolni_kod and reg_jmeno and reg_heslo:
                    lic_res = requests.get(f"{SUPABASE_URL}/rest/v1/licencovane_skoly?licencni_kod=eq.{skolni_kod}", headers=headers).json()
                    if not lic_res:
                        st.error("Neplatný licenční kód.")
                    else:
                        if requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{reg_jmeno}", headers=headers).json():
                            st.error("Jméno je již obsazené.")
                        else:
                            # Získání makroekonomického nastavení školy
                            nastaveni = requests.get(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{skolni_kod}", headers=headers).json()
                            if nastaveni:
                                start_kredity = nastaveni[0]['start_kredit_zak'] if reg_role == "zak" else nastaveni[0]['start_kredit_firma']
                            else:
                                start_kredity = 100 if reg_role == "zak" else 300
                                
                            requests.post(f"{SUPABASE_URL}/rest/v1/uzivatele", headers=headers, json={"jmeno": reg_jmeno, "heslo": reg_heslo, "role": reg_role, "kredity": start_kredity, "skolni_kod": skolni_kod, "aktivni": True})
                            st.success("Účet vytvořen. Můžete se přihlásit.")

    with tab_school_licence:
        with st.form("school_form"):
            nazev_skoly = st.text_input("Název instituce:")
            email = st.text_input("Kontaktní e-mail:")
            if st.form_submit_button("Generovat licenční kód pro školu"):
                if nazev_skoly and email:
                    kod = "SKOLA-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                    requests.post(f"{SUPABASE_URL}/rest/v1/licencovane_skoly", headers=headers, json={"nazev_skoly": nazev_skoly, "kontaktni_email": email, "licencni_kod": kod, "zaplaceno": False})
                    # Vytvoření defaultního nastavení pro novou školu
                    requests.post(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni", headers=headers, json={"skolni_kod": kod})
                    st.success(f"Poptávka zaznamenána. Licenční kód: {kod}")

else:
    if st.session_state.role == "zak": pg = st.navigation([zaci_page, trh_page, zebricky_page])
    elif st.session_state.role == "firma": pg = st.navigation([firma_page, zaci_page, trh_page, zebricky_page])
    elif st.session_state.role == "ucitel": pg = st.navigation([ucitel_page, trh_page, zebricky_page])
    elif st.session_state.role == "admin": pg = st.navigation([zaci_page, firma_page, ucitel_page, trh_page, zebricky_page])
    
    pg.run()
    
    with st.sidebar:
        st.divider()
        st.markdown(f"Uživatel: **{st.session_state.uzivatel}**")
        st.caption(f"Role: **{st.session_state.role.upper()}**")
        st.markdown(f"Zůstatek: **{st.session_state.kredity} M-K**")
        if st.button("Odhlásit se", icon=":material/logout:"):
            st.session_state.clear()
            st.rerun()
