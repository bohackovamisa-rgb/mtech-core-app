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
if "skolni_kod" not in st.session_state: st.session_state.skolni_kod = None
if "trida_nazev" not in st.session_state: st.session_state.trida_nazev = None

zaci_page = st.Page("pages/1_Zaci.py", title="Moje peněženka")
firma_page = st.Page("pages/2_Firma.py", title="Firemní Dashboard")
ucitel_page = st.Page("pages/3_Ucitel.py", title="Kontrolní úřad")
trh_page = st.Page("pages/4_Trh.py", title="Tržiště produktů")
zebricky_page = st.Page("pages/5_Zebricky.py", title="Síň slávy")

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

    tab_login, tab_user_reg, tab_school_licence = st.tabs(["Přihlášení do systému", "Registrace pro Žáky", "Registrace Nové Školy (Pro učitele)"])
    
    # ----------------------------------------------------
    # ZÁLOŽKA 1: PŘIHLÁŠENÍ VŠECH UŽIVATELŮ
    # ----------------------------------------------------
    with tab_login:
        with st.form("login_form"):
            jmeno = st.text_input("Přihlašovací jméno (nebo e-mail):")
            heslo = st.text_input("Heslo:", type="password")
            if st.form_submit_button("Vstoupit do ekosystému"):
                if jmeno and heslo:
                    res = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{jmeno}&heslo=eq.{heslo}&select=*", headers=headers).json()
                    if res:
                        st.session_state.prihlasen = True
                        st.session_state.role = str(res[0]["role"]).lower()
                        st.session_state.kredity = res[0]["kredity"]
                        st.session_state.uzivatel = res[0]["jmeno"]
                        st.session_state.skolni_kod = res[0].get("skolni_kod", "")
                        st.session_state.trida_nazev = res[0].get("trida_nazev", "")
                        st.rerun()
                    else:
                        st.error("Nesprávné přihlašovací údaje.")
                else:
                    st.warning("Vyplňte obě pole.")

    # ----------------------------------------------------
    # ZÁLOŽKA 2: BEZPEČNÁ REGISTRACE ŽÁKŮ
    # ----------------------------------------------------
    with tab_user_reg:
        st.info("Zadejte licenční kód školy, který vám poskytl váš vyučující.")
        skolni_kod_input = st.text_input("Licenční kód školy:", key="reg_kod").upper().strip()
        
        dostupne_tridy = []
        if skolni_kod_input:
            res_tridy = requests.get(f"{SUPABASE_URL}/rest/v1/tridy?skolni_kod=eq.{skolni_kod_input}&select=*", headers=headers).json()
            if isinstance(res_tridy, list) and res_tridy:
                dostupne_tridy = res_tridy
        
        with st.form("user_reg_form"):
            reg_jmeno = st.text_input("Vaše jméno (nebo přezdívka):")
            reg_heslo = st.text_input("Zvolte si bezpečné heslo:", type="password")
            
            vybrana_trida_str = None
            if dostupne_tridy:
                moznosti_trid = [f"{t['nazev_tridy']} (Vyučující: {t['ucitel_jmeno']})" for t in dostupne_tridy]
                vybrana_trida_str = st.selectbox("Vyberte svou třídu ze seznamu:", moznosti_trid)
            else:
                st.warning("Vyučující pro tento kód zatím nezaložil žádnou třídu. Přesto se můžete registrovat a učitel vás do třídy zařadí později.")
            
            if st.form_submit_button("Založit žákovský účet"):
                if skolni_kod_input and reg_jmeno and reg_heslo:
                    lic_res = requests.get(f"{SUPABASE_URL}/rest/v1/licencovane_skoly?licencni_kod=eq.{skolni_kod_input}", headers=headers).json()
                    if not lic_res:
                        st.error("Neplatný licenční kód školy.")
                    else:
                        if requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{reg_jmeno}", headers=headers).json():
                            st.error("Toto uživatelské jméno je již v systému obsazené. Zvolte jiné.")
                        else:
                            nastaveni = requests.get(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{skolni_kod_input}", headers=headers).json()
                            start_kredity = nastaveni[0]['start_kredit_zak'] if nastaveni else 100
                            
                            t_nazev = vybrana_trida_str.split(" (")[0] if vybrana_trida_str else None
                                
                            requests.post(f"{SUPABASE_URL}/rest/v1/uzivatele", headers=headers, json={
                                "jmeno": reg_jmeno, "heslo": reg_heslo, "role": "zak",
                                "kredity": start_kredity, "skolni_kod": skolni_kod_input,
                                "trida_nazev": t_nazev, "aktivni": True
                            })
                            st.success("Žákovský účet byl úspěšně vytvořen. Můžete se přihlásit v první záložce.")
                else:
                    st.warning("Vyplňte kód školy, jméno i heslo.")

    # ----------------------------------------------------
    # ZÁLOŽKA 3: REGISTRACE ŠKOLY A PRVNÍHO UČITELE
    # ----------------------------------------------------
    with tab_school_licence:
        st.markdown("### Nová licence pro školu a zakládající účet garanta")
        st.caption("Chráněno systémovým administrátorským heslem.")
        master_password = st.text_input("Zadejte administrátorské heslo:", type="password")
        
        if master_password == "MtechAdmin2026": 
            with st.form("school_form"):
                st.markdown("**1. Údaje o škole**")
                nazev_skoly = st.text_input("Název vzdělávací instituce:")
                st.markdown("**2. Údaje o vyučujícím (první garant školy)**")
                ucitel_jmeno = st.text_input("Přihlašovací jméno garanta (např. email):")
                ucitel_heslo = st.text_input("Přístupové heslo pro garanta:", type="password")
                
                if st.form_submit_button("Generovat školu a učitele"):
                    if nazev_skoly and ucitel_jmeno and ucitel_heslo:
                        if requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{ucitel_jmeno}", headers=headers).json():
                            st.error("Tento učitel (e-mail) je již v systému zaregistrován.")
                        else:
                            # 1. Založení školy
                            kod = "SKOLA-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                            requests.post(f"{SUPABASE_URL}/rest/v1/licencovane_skoly", headers=headers, json={"nazev_skoly": nazev_skoly, "kontaktni_email": ucitel_jmeno, "licencni_kod": kod, "zaplaceno": False})
                            requests.post(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni", headers=headers, json={"skolni_kod": kod})
                            
                            # 2. Založení učitelského účtu automaticky
                            requests.post(f"{SUPABASE_URL}/rest/v1/uzivatele", headers=headers, json={
                                "jmeno": ucitel_jmeno, "heslo": ucitel_heslo, "role": "ucitel",
                                "kredity": 500, "skolni_kod": kod, "aktivni": True
                            })
                            st.success(f"Licence úspěšně vytvořena! Kód školy: **{kod}**")
                            st.success(f"Účet garanta (**{ucitel_jmeno}**) byl založen. Můžete se přihlásit.")
                    else:
                        st.warning("Vyplňte všechny údaje o škole i vyučujícím.")
        elif master_password != "":
            st.error("Nesprávné administrátorské heslo!")

else:
    with st.sidebar:
        st.markdown(f"Uživatel: **{st.session_state.uzivatel}**")
        role_zobr = "Učitel / Garant" if st.session_state.role == "ucitel" else ("Podnikatel" if st.session_state.role == "firma" else ("Běžný žák" if st.session_state.role == "zak" else "Hlavní Admin"))
        st.caption(f"Role: **{role_zobr}**")
        if st.session_state.trida_nazev:
            st.caption(f"Třída: **{st.session_state.trida_nazev}**")
        st.markdown(f"Zůstatek: **{st.session_state.kredity} M-K**")
        if st.button("Odhlásit se"):
            st.session_state.clear()
            st.rerun()
            
    if st.session_state.role == "zak": pg = st.navigation([zaci_page, trh_page, zebricky_page])
    elif st.session_state.role == "firma": pg = st.navigation([firma_page, zaci_page, trh_page, zebricky_page])
    elif st.session_state.role == "ucitel": pg = st.navigation([ucitel_page, trh_page, zebricky_page])
    elif st.session_state.role == "admin": pg = st.navigation([zaci_page, firma_page, ucitel_page, trh_page, zebricky_page])
    
    pg.run()
