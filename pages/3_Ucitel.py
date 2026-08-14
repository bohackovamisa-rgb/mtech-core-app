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

# Živá synchronizace aktuální role žáka přímo z databáze
if st.session_state.prihlasen and st.session_state.uzivatel:
    res_live = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{st.session_state.uzivatel}&select=role,kredity,trida_nazev,skolni_kod", headers=headers).json()
    if res_live and isinstance(res_live, list) and len(res_live) > 0:
        st.session_state.role = str(res_live[0]["role"]).lower()
        st.session_state.kredity = res_live[0]["kredity"]
        st.session_state.trida_nazev = res_live[0].get("trida_nazev", "")
        st.session_state.skolni_kod = res_live[0].get("skolni_kod", "")

if not st.session_state.prihlasen:
    st.markdown("""
        <div class="hero-card">
            <h1 style="margin:0; font-size: 2.5em;">M-TECH CORE</h1>
            <p style="color: #94a3b8; font-size: 1.2em; margin-top: 5px;">
                Digitální ekosystém pro propojení škol, žáků a reálných firemních zakázek.
            </p>
        </div>
    """, unsafe_allow_html=True)

    tab_login, tab_user_reg, tab_admin_licence = st.tabs([
        "Přihlášení do systému", 
        "Registrace účtu (Žáci a Učitelé)", 
        "Správa licencí (Pouze Administrátor)"
    ])
    
    with tab_login:
        with st.form("login_form"):
            jmeno = st.text_input("Přihlašovací jméno:")
            heslo = st.text_input("Heslo:", type="password")
            if st.form_submit_button("Vstoupit do ekosystému"):
                if jmeno and heslo:
                    res = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{jmeno}&heslo=eq.{heslo}&select=*", headers=headers).json()
                    if res and isinstance(res, list) and len(res) > 0:
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
        st.caption("Zapomněli jste heslo? Žáci požádají svého vyučujícího o reset. Učitelé kontaktují správce systému.")

    with tab_user_reg:
        st.info("Zadejte přístupový kód školy, který jste obdrželi.")
        vstupni_kod = st.text_input("Kód školy (Výukový nebo Zákaznický):", key="reg_kod").upper().strip()
        
        is_customer = False
        skolni_kod_actual = None
        start_kredit_zakaznik = 50
        dostupne_tridy = []
        
        if vstupni_kod:
            res_nast = requests.get(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?zakaznicky_kod=eq.{vstupni_kod}", headers=headers).json()
            if res_nast and isinstance(res_nast, list) and len(res_nast) > 0:
                is_customer = True
                skolni_kod_actual = res_nast[0]['skolni_kod']
                start_kredit_zakaznik = res_nast[0].get('start_kredit_zakaznik', 50)
            else:
                res_lic = requests.get(f"{SUPABASE_URL}/rest/v1/licencovane_skoly?licencni_kod=eq.{vstupni_kod}", headers=headers).json()
                if res_lic and isinstance(res_lic, list) and len(res_lic) > 0:
                    skolni_kod_actual = vstupni_kod
                    res_tridy = requests.get(f"{SUPABASE_URL}/rest/v1/tridy?skolni_kod=eq.{skolni_kod_actual}&select=*", headers=headers).json()
                    if isinstance(res_tridy, list) and res_tridy:
                        dostupne_tridy = res_tridy

        with st.form("user_reg_form"):
            reg_jmeno = st.text_input("Uživatelské jméno:")
            reg_heslo = st.text_input("Heslo:", type="password")
            
            vybrana_role = "zak"
            vybrana_trida_str = None
            
            if skolni_kod_actual and not is_customer:
                vybrana_role_radio = st.radio("Registruji se jako:", ["Žák", "Učitel"], horizontal=True)
                vybrana_role = "ucitel" if vybrana_role_radio == "Učitel" else "zak"
                
                if vybrana_role == "zak":
                    if dostupne_tridy:
                        moznosti_trid = [f"{t['nazev_tridy']} (Vyučující: {t['ucitel_jmeno']})" for t in dostupne_tridy]
                        vybrana_trida_str = st.selectbox("Vyberte svou třídu:", moznosti_trid)
                    else:
                        st.warning("Vyučující zatím nezaložil žádnou třídu. Třídu vám učitel přiřadí později.")
            elif is_customer:
                st.success("Byl zadán zákaznický kód. Budete registrováni jako Zákazník školy.")
            
            if st.form_submit_button("Vytvořit účet"):
                if skolni_kod_actual and reg_jmeno and reg_heslo:
                    if requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{reg_jmeno}", headers=headers).json():
                        st.error("Toto uživatelské jméno je již obsazené.")
                    else:
                        if is_customer:
                            requests.post(f"{SUPABASE_URL}/rest/v1/uzivatele", headers=headers, json={
                                "jmeno": reg_jmeno, "heslo": reg_heslo, "role": "zak",
                                "kredity": start_kredit_zakaznik, "skolni_kod": skolni_kod_actual,
                                "trida_nazev": "Zákazník", "aktivni": True
                            })
                            st.success("Zákaznický účet byl vytvořen. Nyní se můžete přihlásit.")
                        elif vybrana_role == "ucitel":
                            requests.post(f"{SUPABASE_URL}/rest/v1/uzivatele", headers=headers, json={
                                "jmeno": reg_jmeno, "heslo": reg_heslo, "role": "ucitel",
                                "kredity": 500, "skolni_kod": skolni_kod_actual,
                                "trida_nazev": None, "aktivni": True
                            })
                            st.success("Učitelský účet byl vytvořen. Nyní se můžete přihlásit a založit své třídy.")
                        else:
                            t_nazev = vybrana_trida_str.split(" (")[0] if vybrana_trida_str else "Nezařazeno"
                            nastaveni = requests.get(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{skolni_kod_actual}", headers=headers).json()
                            start_kredity = nastaveni[0]['start_kredit_zak'] if nastaveni else 100
                            requests.post(f"{SUPABASE_URL}/rest/v1/uzivatele", headers=headers, json={
                                "jmeno": reg_jmeno, "heslo": reg_heslo, "role": "zak",
                                "kredity": start_kredity, "skolni_kod": skolni_kod_actual,
                                "trida_nazev": t_nazev, "aktivni": True
                            })
                            st.success("Žákovský účet byl vytvořen. Nyní se můžete přihlásit.")
                else:
                    st.warning("Vyplňte platný kód školy, jméno i heslo.")

    with tab_admin_licence:
        st.markdown("### Administrátorská konzole")
        st.caption("Sekce přístupná pouze pro hlavního administrátora platformy.")
        master_password = st.text_input("Zadejte administrátorské heslo:", type="password")
        
        if master_password == "MtechAdmin2026": 
            adm_tab1, adm_tab2 = st.tabs(["Generování licencí pro školy", "Správa hesel vyučujících"])
            
            with adm_tab1:
                with st.form("school_admin_form"):
                    nazev_skoly = st.text_input("Název vzdělávací instituce:")
                    kontakt_email = st.text_input("Kontaktní e-mail zástupce školy:")
                    
                    if st.form_submit_button("Vygenerovat novou školu a licenční kódy"):
                        if nazev_skoly and kontakt_email:
                            kod_vyuka = "SKOLA-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                            kod_zakaznik = "KUPUJ-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                            
                            requests.post(f"{SUPABASE_URL}/rest/v1/licencovane_skoly", headers=headers, json={
                                "nazev_skoly": nazev_skoly, "kontaktni_email": kontakt_email, "licencni_kod": kod_vyuka, "zaplaceno": False
                            })
                            requests.post(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni", headers=headers, json={
                                "skolni_kod": kod_vyuka, "zakaznicky_kod": kod_zakaznik, "start_kredit_zakaznik": 50
                            })
                            
                            st.success(f"Škola **{nazev_skoly}** byla úspěšně založena!")
                            st.info(f"Výukový kód: **{kod_vyuka}**\n\nZákaznický kód: **{kod_zakaznik}**")
                        else:
                            st.warning("Vyplňte název školy i e-mail.")

            with adm_tab2:
                st.markdown("#### Reset hesla pro vyučujícího")
                res_ucitele = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?role=eq.ucitel", headers=headers).json()
                if res_ucitele and isinstance(res_ucitele, list):
                    with st.form("form_admin_reset_ucitele"):
                        ucitel_reset_jmeno = st.selectbox("Vyberte vyučujícího:", [f"{u['jmeno']} (Kód školy: {u.get('skolni_kod', '')})" for u in res_ucitele])
                        nove_heslo_ucitele = st.text_input("Zadejte nové heslo:", value="1234")
                        if st.form_submit_button("Nastavit nové heslo učiteli"):
                            cilovy_ucitel = ucitel_reset_jmeno.split(" (")[0]
                            requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{cilovy_ucitel}", headers=headers, json={"heslo": nove_heslo_ucitele})
                            st.success(f"Učiteli **{cilovy_ucitel}** bylo nastaveno nové heslo.")
                else:
                    st.info("V systému zatím nejsou žádní učitelé.")
        elif master_password != "":
            st.error("Nesprávné administrátorské heslo!")

else:
    with st.sidebar:
        st.markdown(f"Uživatel: **{st.session_state.uzivatel}**")
        role_zobr = "Učitel" if st.session_state.role == "ucitel" else ("Podnikatel" if st.session_state.role == "firma" else ("Běžný žák" if st.session_state.role == "zak" else "Hlavní Admin"))
        st.caption(f"Role: **{role_zobr}**")
        if st.session_state.trida_nazev:
            st.caption(f"Třída: **{st.session_state.trida_nazev}**")
        st.markdown(f"Zůstatek: **{st.session_state.kredity} M-K**")
        
        with st.expander("Změnit mé heslo"):
            with st.form("form_zmena_vlastniho_hesla"):
                moje_nove_heslo = st.text_input("Nové heslo:", type="password")
                if st.form_submit_button("Uložit nové heslo"):
                    if moje_nove_heslo.strip():
                        requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{st.session_state.uzivatel}", headers=headers, json={"heslo": moje_nove_heslo.strip()})
                        st.success("Vaše heslo bylo úspěšně změněno.")
                    else:
                        st.error("Heslo nesmí být prázdné.")

        if st.button("Odhlásit se"):
            st.session_state.clear()
            st.rerun()
            
    if st.session_state.role == "zak": pg = st.navigation([zaci_page, trh_page, zebricky_page])
    elif st.session_state.role == "firma": pg = st.navigation([firma_page, zaci_page, trh_page, zebricky_page])
    elif st.session_state.role == "ucitel": pg = st.navigation([ucitel_page, trh_page, zebricky_page])
    elif st.session_state.role == "admin": pg = st.navigation([zaci_page, firma_page, ucitel_page, trh_page, zebricky_page])
    
    pg.run()
