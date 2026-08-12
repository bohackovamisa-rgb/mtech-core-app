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
        st.info(f"📋 **Registrační spis firmy '{moje_firma['nazev_firmy']}' byl úspěšně podán na Kontrolní úřad.**")
    elif stav == "ZAMITNUTO":
        st.error(f"❌ **Registrační spis byl zamítnut Kontrolním úřadem.** Důvod: {moje_firma.get('duvod_zamitnuti', 'Není uveden')}")
    elif stav == "SCHVALENO":
        st.success(f"🎉 **Firma '{moje_firma['nazev_firmy']}' byla zapsána do Obchodního rejstříku M-TECH CORE!**")

    st.write("---")

tab_zalozeni, tab_canvas, tab_porady, tab_kalkulace, tab_ucto = st.tabs([
    ":material/account_balance: 1. Úřední kolečko (Založení)", 
    ":material/lightbulb: 2. Lean Canvas", 
    ":material/forum: 3. Zápisy z porad",
    ":material/calculate: 4. Kalkulační listy", 
    ":material/menu_book: 5. Kniha příjmů a výdajů"
])

# --- TAB 1: ÚŘEDNÍ KOLEČKO ZALOŽENÍ FIRMY ---
with tab_zalozeni:
    st.subheader("Registrační spis firmy – Úřední tiskopisy")
    st.caption("Vyplňte postupně jednotlivé formuláře pro příslušné orgány státní správy a samosprávy.")
    
    # Pod-záložky pro jednotlivé úřady
    u_notar, u_zivnost, u_financak, u_cssz, u_rejstrik = st.tabs([
        "📜 Notářský zápis",
        "📋 Živnostenský úřad (JRF)",
        "⚖️ Finanční úřad",
        "🏥 ČSSZ a ZP",
        "🛡️ Obchodní rejstřík"
    ])

    # Inicializace dočasného stavu formuláře
    if "reg_data" not in st.session_state:
        st.session_state.reg_data = {}

    # 1. NOTÁŘSKÝ ZÁPIS
    with u_notar:
        st.markdown("**Formulář N-01: Zakladatelská listina a jmenování orgánů s.r.o.**")
        st.session_state.reg_data["nazev_firmy"] = st.text_input("1.1 Obchodní firma (přesný název s koncovkou s.r.o.):", value=st.session_state.reg_data.get("nazev_firmy", ""), placeholder="např. Precision Mech s.r.o.")
        st.session_state.reg_data["sidlo"] = st.text_input("1.2 Sídlo společnosti (adresa školy / učebna):", value=st.session_state.reg_data.get("sidlo", "Školní 101, Učebna č. 12"))
        st.session_state.reg_data["skolni_kod"] = st.text_input("1.3 Licenční kód školy:", value=st.session_state.reg_data.get("skolni_kod", "")).upper().strip()
        
        col_n1, col_n2 = st.columns(2)
        with col_n1:
            st.session_state.reg_data["ceo"] = st.text_input("1.4 Jednatel / CEO (Statutární orgán):", value=st.session_state.reg_data.get("ceo", uzivatel))
            st.session_state.reg_data["cfo"] = st.text_input("1.5 Finanční ředitel / CFO (Správce vkladů):", value=st.session_state.reg_data.get("cfo", ""))
        with col_n2:
            st.session_state.reg_data["cto"] = st.text_input("1.6 Technický ředitel / CTO (Garant výroby):", value=st.session_state.reg_data.get("cto", ""))
            st.session_state.reg_data["vklad"] = st.number_input("1.7 Základní kapitál – Vklad společníka (M-Kredity / CZK):", min_value=10, value=int(st.session_state.reg_data.get("vklad", 100)))

        st.session_state.reg_data["uroven"] = st.radio("1.8 Zvolená úroveň integrace M-TECH CORE:", [
            "Úroveň 1: Teoretický start-up (Inkubátor & Prototyp)", 
            "Úroveň 2: Uzavřený školní trh (Virtuální M-Kredity)", 
            "Úroveň 3: Plná integrace (Reálná odpovědnost & Unie rodičů)"
        ])
        st.success("Krok 1 (Notářství) vyplněn. Přejděte na záložku Živnostenský úřad (JRF).")

    # 2. ŽIVNOSTENSKÝ ÚŘAD (JRF)
    with u_zivnost:
        st.markdown("**Formulář JRF: Jednotný registrační formulář pro fyzické i právnické osoby**")
        col_j1, col_j2 = st.columns(2)
        with col_j1:
            st.session_state.reg_data["divize"] = st.selectbox("2.1 Oborová divize (Druh živnosti):", [
                "Mechanical (Strojírenství & Kovoobrábění)", 
                "Power (Elektrotechnika & Diagnostika)", 
                "Cyber (IT, Software & 3D Tisk)", 
                "Strategy (Služby, Marketing & Káva)"
            ])
            st.session_state.reg_data["provozovna"] = st.text_input("2.2 Místo provozovny / dílny:", value=st.session_state.reg_data.get("provozovna", "Školní dílny – Strojírenský blok B"))
        with col_j2:
            st.session_state.reg_data["predmet"] = st.text_input("2.3 Předmět podnikání (Volná živnost):", value=st.session_state.reg_data.get("predmet", ""), placeholder="např. Výroba kovových dárkových předmětů")
            st.session_state.reg_data["bozp_garant"] = st.text_input("2.4 Odpovědný zástupce pro BOZP & Živnost:", value=st.session_state.reg_data.get("bozp_garant", uzivatel))
            
        st.session_state.reg_data["zamer"] = st.text_area("2.5 Podrobný popis činnosti a výrobního programu pro JRF:", value=st.session_state.reg_data.get("zamer", ""))
        st.success("Krok 2 (Živnostenský úřad) vyplněn. Přejděte na záložku Finanční úřad.")

    # 3. FINANČNÍ ÚŘAD
    with u_financak:
        st.markdown("**Formulář FÚ-5540: Přihláška k registraci k dani z příjmů a M-TECH dani**")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.session_state.reg_data["zdani_obdobi"] = st.selectbox("3.1 Zdaňovací období:", ["Pololetní cyklus", "Měsíční tržní cyklus", "Celoroční maturitní projekt"])
        with col_f2:
            st.session_state.reg_data["ucet_pro_dan"] = st.text_input("3.2 Účet pro odvod M-TECH daně:", value="Transparentní účet Unie rodičů M-TECH CORE")
            
        st.session_state.reg_data["dan_souhlas"] = st.checkbox("3.3 Zavazujeme se k řádnému výpočtu a odvodu M-TECH daně ze zisku (15–20 %) Kontrolnímu úřadu.", value=st.session_state.reg_data.get("dan_souhlas", False))
        st.success("Krok 3 (Finanční úřad) vyplněn. Přejděte na záložku ČSSZ a ZP.")

    # 4. ČSSZ A ZDRAVOTNÍ POJIŠŤOVNA
    with u_cssz:
        st.markdown("**Formulář ČSSZ-801: Oznámení o nástupu do zaměstnání & Registrace zaměstnavatele**")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.session_state.reg_data["seznam_zamestnancu"] = st.text_area("4.1 Seznam pojištěných členů týmu (CEO, CFO, CTO):", value=st.session_state.reg_data.get("seznam_zamestnancu", f"{uzivatel}, CFO, CTO"))
        with col_p2:
            st.session_state.reg_data["mzdovy_fond"] = st.number_input("4.2 Předpokládaný mzdový fond / Odměny členů (M-Kredity):", value=int(st.session_state.reg_data.get("mzdovy_fond", 300)))
        st.success("Krok 4 (ČSSZ a ZP) vyplněn. Přejděte na záložku Obchodní rejstřík k finálnímu podání.")

    # 5. OBCHODNÍ REJSTŘÍK & PODÁNÍ SPISU
    with u_rejstrik:
        st.markdown("**Formulář OR-LIST: Návrh na zápis do Obchodního rejstříku M-TECH CORE**")
        st.session_state.reg_data["bozp_souhlas"] = st.checkbox("5.1 Prohlašujeme, že jsme absolvovali školení BOZP pro práci na školních strojích a zařízeních.", value=st.session_state.reg_data.get("bozp_souhlas", False))
        st.session_state.reg_data["kodex_souhlas"] = st.checkbox("5.2 Zavazujeme se k dodržování Etického kodexu M-TECH CORE a poctivému vedení účetní knihy.", value=st.session_state.reg_data.get("kodex_souhlas", False))

        st.write("---")
        if st.button("🚀 PODAT KOMPLETNÍ REGISTRAČNÍ SPIS NA KONTROLNÍ ÚŘAD", icon=":material/send:"):
            d = st.session_state.reg_data
            if d.get("nazev_firmy") and d.get("skolni_kod") and d.get("cfo") and d.get("cto") and d.get("dan_souhlas") and d.get("bozp_souhlas") and d.get("kodex_souhlas"):
                u_num = 1 if "Úroveň 1" in d.get("uroven", "") else (2 if "Úroveň 2" in d.get("uroven", "") else 3)
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
                res_post = requests.post(f"{SUPABASE_URL}/rest/v1/firmy", headers=headers, json=payload)
                if res_post.status_code in [200, 201]:
                    st.success("Kompletní registrační spis firmy byl úspěšně odeslán vyučujícímu ke schválení!")
                    st.rerun()
                else:
                    st.error(f"Chyba při podání spisu: {res_post.text}")
            else:
                st.warning("Vyplňte prosím všechna pole na záložkách 1 až 4 a potvrďte prohlášení na záložce 5.")

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

# --- TAB 4: KALKULAČNÍ LISTY ---
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

# --- TAB 5: KNIHA PŘÍJMŮ A VÝDAJŮ ---
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
