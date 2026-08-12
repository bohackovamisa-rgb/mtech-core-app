import streamlit as st
import requests

st.set_page_config(page_title="Firemní Kancelář", page_icon=":material/business:", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3, h4 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #00B4D8; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0, 180, 216, 0.4); border-color: #00B4D8; }
    .card-box { background-color: #1e293b; padding: 20px; border-radius: 10px; border: 1px solid #334155; margin-bottom: 15px; }
    .form-section { background-color: #0f172a; padding: 15px; border-radius: 8px; border-left: 4px solid #00B4D8; margin-bottom: 15px; }
    
    .status-badge-ok { background-color: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid #22c55e; padding: 10px; border-radius: 8px; font-weight: 700; text-align: center; }
    .status-badge-wait { background-color: rgba(234, 179, 8, 0.15); color: #fde047; border: 1px solid #eab308; padding: 10px; border-radius: 8px; font-weight: 700; text-align: center; }
    .status-badge-err { background-color: rgba(239, 68, 68, 0.15); color: #fca5a5; border: 1px solid #ef4444; padding: 10px; border-radius: 8px; font-weight: 700; text-align: center; }
    .status-badge-off { background-color: rgba(148, 163, 184, 0.1); color: #94a3b8; border: 1px solid #475569; padding: 10px; border-radius: 8px; font-weight: 600; text-align: center; }
    </style>
""", unsafe_allow_html=True)

st.title(":material/business: Kancelář Studentské Firmy")

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
    st.error("Chybí konfigurace databáze v Secrets!")
    st.stop()

uzivatel = st.session_state.get("uzivatel", "firma")

res_vsechny = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?select=*&order=id.desc", headers=headers)
vsechny_firmy = res_vsechny.json() if res_vsechny.status_code == 200 else []

moje_firma = next((f for f in vsechny_firmy if uzivatel.lower() in [f.get('ceo_jmeno','').lower(), f.get('cfo_jmeno','').lower(), f.get('cto_jmeno','').lower()]), None)

has_canvas = False
has_porada = False
has_kalkulace = False
has_ucto = False

if moje_firma:
    f_id = moje_firma["id"]
    
    res_c = requests.get(f"{SUPABASE_URL}/rest/v1/lean_canvas?firma_id=eq.{f_id}", headers=headers)
    has_canvas = len(res_c.json()) > 0 if res_c.status_code == 200 else False

    res_p = requests.get(f"{SUPABASE_URL}/rest/v1/zapisy_porady?firma_id=eq.{f_id}", headers=headers)
    has_porada = len(res_p.json()) > 0 if res_p.status_code == 200 else False

    res_k = requests.get(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy?firma_id=eq.{f_id}", headers=headers)
    has_kalkulace = len(res_k.json()) > 0 if res_k.status_code == 200 else False

    res_u = requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?firma_id=eq.{f_id}", headers=headers)
    has_ucto = len(res_u.json()) > 0 if res_u.status_code == 200 else False

    st.subheader(":material/fact_check: Přehled plnění povinností podle metodiky M-TECH CORE")
    col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
    stav = moje_firma['stave_licence']
    
    with col_s1:
        if stav == "SCHVALENO": st.markdown('<div class="status-badge-ok">Rejstřík OK</div>', unsafe_allow_html=True)
        elif stav == "CEKA_NA_SCHVALENI": st.markdown('<div class="status-badge-wait">Čeká na Úřad</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="status-badge-err">Spis Zamítnut</div>', unsafe_allow_html=True)
            
    with col_s2:
        if has_canvas: st.markdown('<div class="status-badge-ok">Lean Canvas OK</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="status-badge-off">Lean Canvas Chybí</div>', unsafe_allow_html=True)

    with col_s3:
        if has_porada: st.markdown('<div class="status-badge-ok">Porady OK</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="status-badge-off">Porada Chybí</div>', unsafe_allow_html=True)
            
    with col_s4:
        if has_kalkulace: st.markdown('<div class="status-badge-ok">Kalkulace OK</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="status-badge-off">Kalkulace Chybí</div>', unsafe_allow_html=True)
            
    with col_s5:
        if has_ucto: st.markdown('<div class="status-badge-ok">Účetnictví OK</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="status-badge-off">Kniha Prázdná</div>', unsafe_allow_html=True)

    st.write("")

    if stav == "CEKA_NA_SCHVALENI":
        st.info(f"Registrační spis firmy '{moje_firma['nazev_firmy']}' byl úspěšně podán na Kontrolní úřad a čeká na vyjádření vyučujícího.")
    elif stav == "ZAMITNUTO":
        st.error(f"Registrační spis byl zamítnut Kontrolním úřadem. Důvod: {moje_firma.get('duvod_zamitnuti', 'Není uveden')}")
    elif stav == "SCHVALENO":
        st.success(f"Firma '{moje_firma['nazev_firmy']}' byla zapsána do Obchodního rejstříku M-TECH CORE!")

    st.write("---")

tab_zalozeni, tab_canvas, tab_porady, tab_hr, tab_kalkulace, tab_ucto = st.tabs([
    ":material/account_balance: 1. Úřední kolečko (Založení)", 
    ":material/lightbulb: 2. Lean Canvas", 
    ":material/forum: 3. Zápisy z porad",
    ":material/badge: 4. Personalistika & Mzdy",
    ":material/calculate: 5. Kalkulační listy", 
    ":material/menu_book: 6. Kniha příjmů a výdajů"
])

# --- TAB 1: REÁLNÉ ÚŘEDNÍ KOLEČKO ZALOŽENÍ FIRMY ---
with tab_zalozeni:
    st.subheader("Registrační spis firmy – Úřední tiskopisy a stav podání")
    
    if moje_firma:
        st.success(f"EVIDOVANÝ REGISTRAČNÍ SPIS FIRMY: {moje_firma['nazev_firmy']}")
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.markdown(f"""
                <div class="card-box">
                    <h4>1. Notářský zápis & Orgány s.r.o.</h4>
                    <p><b>Obchodní firma:</b> {moje_firma['nazev_firmy']}</p>
                    <p><b>Právní forma:</b> Společnost s ručením omezeným (s.r.o.)</p>
                    <p><b>Úroveň integrace:</b> Úroveň {moje_firma['uroven_projektu']} (Dle licencování školy)</p>
                    <p><b>Jednatel / CEO:</b> {moje_firma['ceo_jmeno']}</p>
                    <p><b>Finanční ředitel / CFO:</b> {moje_firma['cfo_jmeno']}</p>
                    <p><b>Technický ředitel / CTO:</b> {moje_firma['cto_jmeno']}</p>
                    <p><b>Základní kapitál:</b> {moje_firma['pocatecni_kapital']} M-Kreditů / CZK</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
                <div class="card-box">
                    <h4>3. Finanční úřad & Registrace k dani</h4>
                    <p><b>Režim M-TECH daně:</b> Odvod 15–20 % ze zisku</p>
                    <p><b>Správa daně:</b> {'Transparentní účet Unie rodičů (Úroveň 3)' if moje_firma['uroven_projektu'] == 3 else 'Interní virtuální účet M-Kreditů v aplikaci (Úroveň 1 a 2)'}</p>
                </div>
            """, unsafe_allow_html=True)

        with col_f2:
            st.markdown(f"""
                <div class="card-box">
                    <h4>2. Živnostenský úřad (JRF)</h4>
                    <p><b>Předmět podnikání & Popis:</b> {moje_firma['podnikatelsky_zamer']}</p>
                    <p><b>Kód školy:</b> {moje_firma['skolni_kod']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
                <div class="card-box">
                    <h4>4. ČSSZ, ZP & Obchodní rejstřík</h4>
                    <p><b>Registrace zaměstnavatele:</b> Schváleno</p>
                    <p><b>Školení BOZP & Etický kodex:</b> Potvrzeno</p>
                    <p><b>Stav spisu na Kontrolním úřadu:</b> <b>{moje_firma['stave_licence']}</b></p>
                </div>
            """, unsafe_allow_html=True)
            
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if moje_firma['stave_licence'] == "ZAMITNUTO":
                if st.button("Znovupodat registrační spis ke schválení", icon=":material/refresh:"):
                    requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{moje_firma['id']}", headers=headers, json={"stave_licence": "CEKA_NA_SCHVALENI"})
                    st.success("Spis byl znovu odeslán na Kontrolní úřad!")
                    st.rerun()
        with col_btn2:
            if st.button("Upravit údaje v registračním spisu", icon=":material/edit:"):
                st.session_state.edit_spis = True
                st.rerun()

    if not moje_firma or st.session_state.get("edit_spis", False):
        if st.session_state.get("edit_spis", False):
            st.warning("Režim úprav odeslaného registračního spisu:")
            
        u_notar, u_zivnost, u_financak, u_cssz, u_rejstrik = st.tabs([
            "📜 Notářský zápis", "📋 Živnostenský úřad (JRF)", "⚖️ Finanční úřad", "🏥 ČSSZ a ZP", "🛡️ Obchodní rejstřík"
        ])

        if "reg_data" not in st.session_state:
            st.session_state.reg_data = {}

        # 1. NOTÁŘSKÝ ZÁPIS
        with u_notar:
            st.markdown("**Formulář N-01: Zakladatelská listina a jmenování orgánů s.r.o.**")
            st.session_state.reg_data["nazev_firmy"] = st.text_input("1.1 Obchodní firma (přesný název s koncovkou s.r.o.):", value=st.session_state.reg_data.get("nazev_firmy", moje_firma['nazev_firmy'] if moje_firma else ""), placeholder="např. Precision Mech s.r.o.")
            st.session_state.reg_data["sidlo"] = st.text_input("1.2 Sídlo společnosti:", value=st.session_state.reg_data.get("sidlo", "Školní 101, Učebna č. 12"))
            st.session_state.reg_data["skolni_kod"] = st.text_input("1.3 Licenční kód školy:", value=st.session_state.reg_data.get("skolni_kod", moje_firma['skolni_kod'] if moje_firma else "")).upper().strip()
            
            col_n1, col_n2 = st.columns(2)
            with col_n1:
                st.session_state.reg_data["ceo"] = st.text_input("1.4 Jednatel / CEO:", value=st.session_state.reg_data.get("ceo", moje_firma['ceo_jmeno'] if moje_firma else uzivatel))
                st.session_state.reg_data["cfo"] = st.text_input("1.5 Finanční ředitel / CFO:", value=st.session_state.reg_data.get("cfo", moje_firma['cfo_jmeno'] if moje_firma else ""))
            with col_n2:
                st.session_state.reg_data["cto"] = st.text_input("1.6 Technický ředitel / CTO:", value=st.session_state.reg_data.get("cto", moje_firma['cto_jmeno'] if moje_firma else ""))
                st.session_state.reg_data["vklad"] = st.number_input("1.7 Základní kapitál na člena (M-Kredity):", min_value=10, value=int(st.session_state.reg_data.get("vklad", 100)))

            st.caption("ℹ️ **Úroveň integrace (Level 1–3):** Bude automaticky přiřazena na základě zakoupené licenční smlouvy vaší školy a schválení vyučujícím.")

        # 2. ŽIVNOSTENSKÝ ÚŘAD (JRF)
        with u_zivnost:
            st.markdown("**Formulář JRF: Jednotný registrační formulář**")
            col_j1, col_j2 = st.columns(2)
            with col_j1:
                st.session_state.reg_data["divize"] = st.selectbox("2.1 Oborová divize:", ["Mechanical (Strojírenství)", "Power (Elektrotechnika)", "Cyber (IT)", "Strategy (Služby)"])
                st.session_state.reg_data["provozovna"] = st.text_input("2.2 Místo provozovny / dílny:", value=st.session_state.reg_data.get("provozovna", "Školní dílny – Blok B"))
            with col_j2:
                st.session_state.reg_data["predmet"] = st.text_input("2.3 Předmět podnikání:", value=st.session_state.reg_data.get("predmet", ""), placeholder="Výroba kovových dárkových předmětů")
                st.session_state.reg_data["bozp_garant"] = st.text_input("2.4 Odpovědný zástupce BOZP:", value=st.session_state.reg_data.get("bozp_garant", uzivatel))
                
            st.session_state.reg_data["zamer"] = st.text_area("2.5 Podrobný popis činnosti:", value=st.session_state.reg_data.get("zamer", ""))

        # 3. FINANČNÍ ÚŘAD
        with u_financak:
            st.markdown("**Formulář FÚ-5540: Přihláška k registraci k dani z příjmů a M-TECH dani**")
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                st.session_state.reg_data["zdani_obdobi"] = st.selectbox("3.1 Zdaňovací období:", ["Pololetní cyklus", "Měsíční tržní cyklus", "Celoroční maturitní projekt"])
            with col_f2:
                st.session_state.reg_data["ucet_pro_dan"] = st.text_input("3.2 Režim správy M-TECH daně:", value="Přiřazuje vyučující dle zakoupené licence školy", disabled=True)
                
            st.session_state.reg_data["dan_souhlas"] = st.checkbox("3.3 Zavazujeme se k řádnému odvodu M-TECH daně ze zisku (15–20 %).", value=st.session_state.reg_data.get("dan_souhlas", True))

        # 4. ČSSZ A ZDRAVOTNÍ POJIŠŤOVNA
        with u_cssz:
            st.markdown("**Formulář ČSSZ-801: Oznámení o nástupu do zaměstnání & Registrace zaměstnavatele**")
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.session_state.reg_data["seznam_zamestnancu"] = st.text_area("4.1 Seznam členů týmu:", value=st.session_state.reg_data.get("seznam_zamestnancu", f"{uzivatel}, CFO, CTO"))
            with col_p2:
                st.session_state.reg_data["mzdovy_fond"] = st.number_input("4.2 Předpokládaný mzdový fond (M-Kredity):", value=int(st.session_state.reg_data.get("mzdovy_fond", 300)))

        # 5. OBCHODNÍ REJSTŘÍK
        with u_rejstrik:
            st.markdown("**Formulář OR-LIST: Návrh na zápis do Obchodního rejstříku M-TECH CORE**")
            st.session_state.reg_data["bozp_souhlas"] = st.checkbox("5.1 Prohlašujeme, že jsme absolvovali školení BOZP.", value=st.session_state.reg_data.get("bozp_souhlas", True))
            st.session_state.reg_data["kodex_souhlas"] = st.checkbox("5.2 Zavazujeme se k dodržování Etického kodexu M-TECH CORE.", value=st.session_state.reg_data.get("kodex_souhlas", True))

            st.write("---")
            if st.button("PODAT KOMPLETNÍ REGISTRAČNÍ SPIS NA KONTROLNÍ ÚŘAD", icon=":material/send:"):
                d = st.session_state.reg_data
                if d.get("nazev_firmy") and d.get("skolni_kod") and d.get("cfo") and d.get("cto") and d.get("dan_souhlas") and d.get("bozp_souhlas") and d.get("kodex_souhlas"):
                    
                    # Načtení úrovně licence ze školního kódu
                    u_kod = d.get("skolni_kod")
                    res_lic = requests.get(f"{SUPABASE_URL}/rest/v1/licencovane_skoly?licencni_kod=eq.{u_kod}", headers=headers)
                    lic_data = res_lic.json() if res_lic.status_code == 200 else []
                    u_num = lic_data[0].get("uroven_projektu", 2) if lic_data else 2
                    
                    souhrn_zameru = f"[{d.get('divize')}] {d.get('predmet')} | Sídlo: {d.get('sidlo')} | Provozovna: {d.get('provozovna')} | BOZP Garant: {d.get('bozp_garant')} | Popis: {d.get('zamer')}"
                    
                    payload = {
                        "nazev_firmy": d.get("nazev_firmy"),
                        "skolni_kod": d.get("skolni_kod"),
                        "uroven_projektu": u_num,
                        "ceo_jmeno": d.get("ceo"),
                        "cfo_jmeno": d.get("cfo"),
                        "cto_jmeno": d.get("cto"),
                        "podnikatelsky_zamer": souhrn_zameru,
                        "pocatecni_kapital": d.get("vklad", 100) * 3,
                        "stave_licence": "CEKA_NA_SCHVALENI"
                    }
                    
                    if moje_firma:
                        res_post = requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{moje_firma['id']}", headers=headers, json=payload)
                    else:
                        res_post = requests.post(f"{SUPABASE_URL}/rest/v1/firmy", headers=headers, json=payload)
                        
                    if res_post.status_code in [200, 201, 204]:
                        st.session_state.edit_spis = False
                        st.success("Kompletní registrační spis firmy byl úspěšně odeslán vyučujícímu ke schválení!")
                        st.rerun()
                    else:
                        st.error(f"Chyba při podání spisu: {res_post.text}")
                else:
                    st.warning("Vyplňte prosím všechna povinná pole a potvrďte prohlášení na záložce Obchodní rejstřík.")

# --- TAB 2: LEAN CANVAS ---
with tab_canvas:
    if not moje_firma:
        st.warning("Nejprve musíte podat registrační spis na záložce 1.")
    else:
        st.subheader("Strategický plán (Lean Canvas)")
        with st.form("form_canvas"):
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                prob = st.text_area("1. Problém (Co trh postrádá?):")
                sol = st.text_area("2. Řešení (Co nabízíme?):")
                val = st.text_area("3. Unikátní hodnota:")
            with col_c2:
                target = st.text_area("4. Cílová skupina:")
                costs = st.text_area("5. Nákladová struktura:")
                rev = st.text_area("6. Příjmové toky:")
            
            if st.form_submit_button("Uložit Lean Canvas", icon=":material/save:"):
                c_payload = {"firma_id": moje_firma["id"], "problem": prob, "reseni": sol, "cilova_skupina": target, "unikatni_hodnota": val, "nakladova_struktura": costs, "prijmove_toky": rev}
                requests.post(f"{SUPABASE_URL}/rest/v1/lean_canvas", headers=headers, json=c_payload)
                st.success("Lean Canvas uložen!")
                st.rerun()

# --- TAB 3: ZÁPISY Z PORAD ---
with tab_porady:
    if not moje_firma:
        st.warning("Nejprve musíte podat registrační spis na záložce 1.")
    else:
        st.subheader("Zápisy z porad managementu (CEO, CFO, CTO)")
        with st.form("form_porada"):
            projednano = st.text_area("Projednané body na poradě (Agenda & Problémy):")
            ukoly = st.text_area("Rozdělení úkolů a odpovědnost členů týmu:")
            
            if st.form_submit_button("Uložit zápis z porady", icon=":material/post_add:"):
                p_payload = {"firma_id": moje_firma["id"], "projednane_body": projednano, "ukoly_a_odpovednost": ukoly}
                requests.post(f"{SUPABASE_URL}/rest/v1/zapisy_porady", headers=headers, json=p_payload)
                st.success("Zápis z porady uložen!")
                st.rerun()
                
        st.write("---")
        res_p_hist = requests.get(f"{SUPABASE_URL}/rest/v1/zapisy_porady?firma_id=eq.{moje_firma['id']}&order=datum.desc", headers=headers)
        if res_p_hist.status_code == 200 and len(res_p_hist.json()) > 0:
            for p in res_p_hist.json():
                st.markdown(f"""
                    <div class="card-box">
                        <small style="color:#00B4D8;">Datum porady: {p['datum'][:10]} {p['datum'][11:16]}</small>
                        <p><b>Projednáno:</b> {p['projednane_body']}</p>
                        <p><b>Úkoly a odpovědnost:</b> {p['ukoly_a_odpovednost']}</p>
                    </div>
                """, unsafe_allow_html=True)

# --- TAB 4: PERSONALISTIKA A MZDY ---
with tab_hr:
    if not moje_firma:
        st.warning("Nejprve musíte podat registrační spis na záložce 1.")
    else:
        st.subheader("Personalistika, Mzdová listina a Vzájemné hodnocení")
        hr_nabor, hr_mzdy, hr_peer = st.tabs([
            "📝 Nábor & Pracovní smlouvy", "⏱️ Výkaz práce & Mzdová listina", "⭐ 360° Vzájemné hodnocení"
        ])
        
        with hr_nabor:
            with st.form("form_novy_zamestnanec"):
                col_z1, col_z2 = st.columns(2)
                with col_z1:
                    z_jmeno = st.text_input("Jméno a příjmení pracovníka:")
                    z_pozice = st.text_input("Pracovní pozice:")
                with col_z2:
                    z_smlouva = st.selectbox("Typ smluvního vztahu:", ["Dohoda o provedení práce (DPP)", "Dohoda o pracovní činnosti (DPČ)", "Student - Člen managementu"])
                    z_sazba = st.number_input("Hodinová mzda (v M-Kreditech / hod):", min_value=10, value=50)
                
                if st.form_submit_button("Sjednat smlouvu", icon=":material/badge:"):
                    if z_jmeno and z_pozice:
                        z_payload = {"firma_id": moje_firma["id"], "jmeno_zamestnance": z_jmeno, "pozice": z_pozice, "typ_smlouva": z_smlouva, "hodinova_sazba": z_sazba, "odpracovane_hodiny": 0, "vyplaceno_celkem": 0, "hodnoceni_skore": 100}
                        requests.post(f"{SUPABASE_URL}/rest/v1/zamestnanci", headers=headers, json=z_payload)
                        st.success(f"Pracovník {z_jmeno} zaregistrován!")
                        st.rerun()

        with hr_mzdy:
            res_z = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?firma_id=eq.{moje_firma['id']}&select=*", headers=headers)
            zamestnanci_seznam = res_z.json() if res_z.status_code == 200 else []
            if zamestnanci_seznam:
                vybrany_z_jmeno = st.selectbox("Vyberte pracovníka pro výplatní pásku:", [z["jmeno_zamestnance"] for z in zamestnanci_seznam])
                vybrany_z = next((z for z in zamestnanci_seznam if z["jmeno_zamestnance"] == vybrany_z_jmeno), None)
                if vybrany_z:
                    hodiny = st.number_input("Odpracované hodiny:", min_value=1.0, value=4.0, step=0.5)
                    hruba_mzda = hodiny * vybrany_z["hodinova_sazba"]
                    mtech_dan_mzda = hruba_mzda * 0.15
                    cista_mzda = hruba_mzda - mtech_dan_mzda
                    
                    st.markdown(f"Hrubá mzda: `{hruba_mzda:.2f} M-K` | Daň (15 %): `{mtech_dan_mzda:.2f} M-K` | Čistá mzda: `{cista_mzda:.2f} M-K`")
                    
                    if st.button("Vyplatit mzdu a zapsat výdaj do Účetní knihy", icon=":material/payments:"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/zamestnanci?id=eq.{vybrany_z['id']}", headers=headers, json={"odpracovane_hodiny": vybrany_z["odpracovane_hodiny"] + hodiny, "vyplaceno_celkem": vybrany_z["vyplaceno_celkem"] + cista_mzda})
                        t_payload = {"firma_id": moje_firma["id"], "typ_transakce": "VYDAJ", "titul": f"Výplata mzdy: {vybrany_z['jmeno_zamestnance']}", "castka": cista_mzda, "auditovano": False}
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json=t_payload)
                        st.success("Mzda vyplacena!")
                        st.rerun()

        with hr_peer:
            res_z = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?firma_id=eq.{moje_firma['id']}&select=*", headers=headers)
            zamestnanci_seznam = res_z.json() if res_z.status_code == 200 else []
            if zamestnanci_seznam:
                vybrany_z_peer = st.selectbox("Vyberte kolegu pro hodnocení:", [z["jmeno_zamestnance"] for z in zamestnanci_seznam], key="peer_select")
                z_peer_obj = next((z for z in zamestnanci_seznam if z["jmeno_zamestnance"] == vybrany_z_peer), None)
                if z_peer_obj:
                    bod_aktivita = st.slider("Aktivita a plnění úkolů (%):", min_value=10, max_value=100, value=90)
                    bod_spoluprace = st.slider("Týmová spolupráce (%):", min_value=10, max_value=100, value=85)
                    prumer_skore = (bod_aktivita + bod_spoluprace) / 2.0
                    if st.button("Uložit peer-review hodnocení", icon=":material/rate_review:"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/zamestnanci?id=eq.{z_peer_obj['id']}", headers=headers, json={"hodnoceni_skore": prumer_skore})
                        st.success("Hodnocení uloženo!")
                        st.rerun()

# --- TAB 5: KALKULAČNÍ LISTY ---
with tab_kalkulace:
    if not moje_firma:
        st.warning("Nejprve musíte podat registrační spis na záložce 1.")
    else:
        st.subheader("Návrh nového produktu a Kalkulační vzorec")
        with st.form("form_kalkulace"):
            prod_nazev = st.text_input("Název produktu / služby:")
            p_naklady = st.number_input("Přímé náklady (materiál) v M-Kreditech:", min_value=0.0, value=35.0)
            rezie = st.number_input("Virtuální režie školy v M-Kreditech:", min_value=0.0, value=10.0)
            marze = st.number_input("Plánovaná marže v M-Kreditech:", min_value=0.0, value=50.0)
            dan_pct = st.number_input("M-TECH Daň pro Fond rozvoje (%):", min_value=10.0, max_value=30.0, value=15.0)
            
            zaklad_dane = p_naklady + rezie + marze
            vypoctena_dan = zaklad_dane * (dan_pct / 100.0)
            doporucena_cena = zaklad_dane + vypoctena_dan
            
            st.markdown(f"**M-TECH daň:** `{vypoctena_dan:.2f} M-K` | **Prodejní cena:** `{doporucena_cena:.2f} M-Kreditů`")
            
            if st.form_submit_button("Odeslat kalkulační list ke schválení", icon=":material/send:"):
                k_payload = {"firma_id": moje_firma["id"], "nazev_produktu": prod_nazev, "prime_naklady": p_naklady, "rezie_skoly": rezie, "mtech_dan_procento": dan_pct, "marze_zisk": marze, "konecna_cena": doporucena_cena, "schvaleno_uradem": False}
                requests.post(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy", headers=headers, json=k_payload)
                st.success("Kalkulační list odeslán!")
                st.rerun()

# --- TAB 6: KNIHA PŘÍJMŮ A VÝDAJŮ ---
with tab_ucto:
    if not moje_firma:
        st.warning("Nejprve musíte podat registrační spis na záložce 1.")
    else:
        st.subheader("Kniha příjmů a výdajů (Cash-flow)")
        with st.form("form_transakce"):
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1: typ = st.selectbox("Typ zápisu:", ["PRIJEM", "VYDAJ"])
            with col_t2: titul = st.text_input("Titul:", value="Nákup materiálu")
            with col_t3: castka = st.number_input("Částka v M-Kreditech:", min_value=1.0, value=50.0)
                
            if st.form_submit_button("Zapsat do účetní knihy", icon=":material/add_circle:"):
                t_payload = {"firma_id": moje_firma["id"], "typ_transakce": typ, "titul": titul, "castka": castka, "auditovano": False}
                requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json=t_payload)
                st.success("Položka zapsána!")
                st.rerun()
                
        res_kniha = requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?firma_id=eq.{moje_firma['id']}&order=datum.desc", headers=headers)
        if res_kniha.status_code == 200 and len(res_kniha.json()) > 0:
            st.dataframe(res_kniha.json(), use_container_width=True)
