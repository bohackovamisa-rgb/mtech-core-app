import streamlit as st
import requests
import random
import string

st.set_page_config(page_title="M-TECH CORE", page_icon=":material/hub:", layout="wide")

# --- VYLEPŠENÉ UI / CSS STYLY ---
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
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
except Exception:
    st.error("Chybí konfigurace v Secrets!")
    st.stop()

if "role" not in st.session_state:
    st.session_state.role = None
if "kredity" not in st.session_state:
    st.session_state.kredity = 0
if "uzivatel" not in st.session_state:
    st.session_state.uzivatel = None

zaci_page = st.Page("pages/1_Zaci.py", title="Moje peněženka", icon=":material/wallet:")
firma_page = st.Page("pages/2_Firma.py", title="Firemní Dashboard", icon=":material/insights:")
ucitel_page = st.Page("pages/3_Ucitel.py", title="Kontrolní úřad", icon=":material/account_balance:")

if st.session_state.role is None:
    # --- HERO LANDING PAGE ---
    st.markdown("""
        <div class="hero-card">
            <h1 style="margin:0; font-size: 2.5em;">M-TECH CORE</h1>
            <p style="color: #94a3b8; font-size: 1.2em; margin-top: 5px;">
                Digitální ekosystém pro propojení škol, žáků a reálných firemních zakázek.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # --- PŘEDSTAVENÍ SYSTÉMU ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
            <div class="feature-box">
                <h4>🎓 Pro Žáky</h4>
                <p style="font-size: 0.9em; color: #cbd5e1;">Získávají M-Kredity za plnění úkolů, nakupují služby na tržišti a učí se pracovat s digitální peněženkou.</p>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
            <div class="feature-box">
                <h4>🏢 Pro Firmy</h4>
                <p style="font-size: 0.9em; color: #cbd5e1;">Vypisují reálné zakázky, nabízí produkty a spravují svůj firemní kapitál v přehledném dashboardu.</p>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
            <div class="feature-box">
                <h4>🏛️ Pro Školy</h4>
                <p style="font-size: 0.9em; color: #cbd5e1;">Kontrolní úřad s kompletním dohledem nad transakcemi, dohledem nad fiktivní ekonomikou a licencemi.</p>
            </div>
        """, unsafe_allow_html=True)

    st.write("---")

    # --- ZÁLOŽKY PRO PŘÍSTUP / OBJEDNÁVKU ---
    tab_login, tab_user_reg, tab_school_licence = st.tabs([
        "🔒 Přihlášení do systému", 
        "🎓 Registrace uživatele (Kód školy)", 
        "🏫 Objednávka Školní Licencie"
    ])
    
    # 1. PŘIHLÁŠENÍ
    with tab_login:
        with st.form("login_form"):
            jmeno = st.text_input("Přihlašovací jméno:")
            heslo = st.text_input("Heslo:", type="password")
            submit = st.form_submit_button("Vstoupit do M-TECH CORE")
            
            if submit:
                endpoint = f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{jmeno}&heslo=eq.{heslo}&select=*"
                try:
                    res = requests.get(endpoint, headers=headers)
                    data = res.json()
                    if isinstance(data, list) and len(data) > 0:
                        uzivatel = data[0]
                        st.session_state.role = uzivatel["role"]
                        st.session_state.kredity = uzivatel["kredity"]
                        st.session_state.uzivatel = uzivatel["jmeno"]
                        st.rerun()
                    else:
                        st.error("Nesprávné přihlašovací údaje!")
                except Exception as e:
                    st.error(f"Chyba databáze: {e}")

    # 2. REGISTRACE S KÓDEM ŠKOLY
    with tab_user_reg:
        st.info("Máte licenční kód od vaší školy? Zadejte jej níže pro vytvoření účtu.")
        with st.form("user_reg_form"):
            skolni_kod = st.text_input("Licenční kód školy:").upper().strip()
            reg_jmeno = st.text_input("Nové uživatelské jméno:")
            reg_heslo = st.text_input("Heslo:", type="password")
            reg_role = st.selectbox("Typ účtu:", ["zak", "firma"])
            reg_submit = st.form_submit_button("Vytvořit účet")
            
            if reg_submit:
                if skolni_kod and reg_jmeno and reg_heslo:
                    lic_res = requests.get(f"{SUPABASE_URL}/rest/v1/licencovane_skoly?licencni_kod=eq.{skolni_kod}&zaplaceno=eq.true", headers=headers)
                    lic_data = lic_res.json()
                    
                    if not lic_data:
                        st.error("Neplatný nebo dosud neaktivní licenční kód!")
                    else:
                        check_res = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{reg_jmeno}", headers=headers)
                        if len(check_res.json()) > 0:
                            st.error("Uživatelské jméno je již obsazené!")
                        else:
                            start_kredity = 100 if reg_role == "zak" else 300
                            novy_u = {
                                "jmeno": reg_jmeno,
                                "heslo": reg_heslo,
                                "role": reg_role,
                                "kredity": start_kredity,
                                "skolni_kod": skolni_kod,
                                "aktivni": True
                            }
                            post_u = requests.post(f"{SUPABASE_URL}/rest/v1/uzivatele", headers=headers, json=novy_u)
                            if post_u.status_code in [200, 201]:
                                st.success("Účet vytvořen! Nyní se můžete přihlásit.")
                            else:
                                st.error("Chyba při registrace.")
                else:
                    st.warning("Vyplňte všechny údaje!")

    # 3. LICENCE BEZ CENÍKU
    with tab_school_licence:
        st.subheader("Poptávka licencování pro školy")
        st.caption("Licenční balíčky upravujeme na míru podle velikosti školy a počtu zapojených firem.")
        
        with st.form("school_form"):
            nazev_skoly = st.text_input("Název školy / organizace:")
            email = st.text_input("Kontaktní e-mail zástupce:")
            pocet_firem = st.number_input("Odhadovaný počet zapojených firem:", min_value=1, value=5)
            pocet_zaku = st.number_input("Odhadovaný počet žáků:", min_value=10, value=100)
            poznamka = st.text_area("Doplňující dotazy nebo požadavky:")
            
            submit_licence = st.form_submit_button("Odeslat nezávaznou poptávku")
            
            if submit_licence:
                if nazev_skoly and email:
                    generovany_kod = "SKOLA-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                    payload = {
                        "nazev_skoly": nazev_skoly,
                        "kontaktni_email": email,
                        "licencni_kod": generovany_kod,
                        "max_firem": pocet_firem,
                        "max_zaku": pocet_zaku,
                        "zaplaceno": False
                    }
                    res_lic = requests.post(f"{SUPABASE_URL}/rest/v1/licencovane_skoly", headers=headers, json=payload)
                    
                    if res_lic.status_code in [200, 201]:
                        st.success(f"Děkujeme za zájem! Poptávka byla zaznamenána pod kódem **{generovany_kod}**.")
                        st.info("Na zadaný e-mail vás budeme kontaktovat s nabídkou a po schválení kód aktivujeme.")
                    else:
                        st.error("Chyba při odesílání poptávky.")
                else:
                    st.warning("Vyplňte prosím název školy i e-mail.")

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
