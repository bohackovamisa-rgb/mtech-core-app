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
        st.info(f"📋 **Registrační spis firmy '{moje_firma['nazev_firmy']}' byl úspěšně podán na Kontrolní úřad.**")
    elif stav == "ZAMITNUTO":
        st.error(f"❌ **Registrační spis byl zamítnut Kontrolním úřadem.** Důvod: {moje_firma.get('duvod_zamitnuti', 'Není uveden')}")
    elif stav == "SCHVALENO":
        st.success(f"🎉 **Firma '{moje_firma['nazev_firmy']}' byla zapsána do Obchodního rejstříku M-TECH CORE!**")

    st.write("---")

tab_zalozeni, tab_canvas, tab_porady, tab_hr, tab_kalkulace, tab_ucto = st.tabs([
    ":material/account_balance: 1. Úřední kolečko", 
    ":material/lightbulb: 2. Lean Canvas", 
    ":material/forum: 3. Zápisy z porad",
    ":material/badge: 4. Personalistika & Mzdy",
    ":material/calculate: 5. Kalkulační listy", 
    ":material/menu_book: 6. Kniha příjmů a výdajů"
])

# --- TAB 1: REÁLNÉ ÚŘEDNÍ KOLEČKO ZALOŽENÍ FIRMY ---
with tab_zalozeni:
    st.subheader("Registrační spis firmy – Úřední tiskopisy")
    st.caption("Vyplňte postupně jednotlivé formuláře pro příslušné orgány státní správy a samosprávy.")
    
    u_notar, u_zivnost, u_financak, u_cssz, u_rejstrik = st.tabs([
        "📜 Notářský zápis", "📋 Živnostenský úřad (JRF)", "⚖️ Finanční úřad", "🏥 ČSSZ a ZP", "🛡️ Obchodní rejstřík"
    ])

    if "reg_data" not in st.session_state:
        st.session_state.reg_data = {}

    with u_notar:
        st.markdown("**Formulář N-01: Zakladatelská listina a jmenování orgánů s.r.o.**")
        st.session_state.reg_data["nazev_firmy"] = st.text_input("1.1 Obchodní firma (přesný název s koncovkou s.r.o.):", value=st.session_state.reg_data.get("nazev_firmy", ""), placeholder="např. Precision Mech s.r.o.")
        st.session_state.reg_data["sidlo"] = st.text_input("1.2 Sídlo společnosti:", value=st.session_state.reg_data.get("sidlo", "Školní 101, Učebna č. 12"))
        st.session_state.reg_data["skolni_kod"] = st.text_input("1.3 Licenční kód školy:", value=st.session_state.reg_data.get("skolni_kod", "")).upper().strip()
        
        col_n1, col_n2 = st.columns(2)
        with col_n1:
            st.session_state.reg_data["ceo"] = st.text_input("1.4 Jednatel / CEO:", value=st.session_state.reg_data.get("ceo", uzivatel))
            st.session_state.reg_data["cfo"] = st.text_input("1.5 Finanční ředitel / CFO:", value=st.session_state.reg_data.get("cfo", ""))
        with col_n2:
            st.session_state.reg_data["cto"] = st.text_input("1.6 Technický ředitel / CTO:", value=st.session_state.reg_data.get("cto", ""))
            st.session_state.reg_data["vklad"] = st.number_input("1.7 Základní kapitál na člena (M-Kredity):", min_value=10, value=int(st.session_state.reg_data.get("vklad", 100)))

        st.session_state.reg_data["uroven"] = st.radio("1.8 Zvolená úroveň integrace M-TECH CORE:", [
            "Úroveň 1: Teoretický start-up (Inkubátor & Prototyp)", 
            "Úroveň 2: Uzavřený školní trh (Virtuální M-Kredity)", 
            "Úroveň 3: Plná integrace (Reálná odpovědnost & Unie rodičů)"
        ])
        st.success("Krok 1 vyplněn.")

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
        st.success("Krok 2 vyplněn.")

    with u_financak:
        st.markdown("**Formulář FÚ-5540: Přihláška k registraci k dani z příjmů a M-TECH dani**")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.session_state.reg_data["zdani_obdobi"] = st.selectbox("3.1 Zdaňovací období:", ["Pololetní cyklus", "Měsíční tržní cyklus", "Celoroční maturitní projekt"])
        with col_f2:
            st.session_state.reg_data["ucet_pro_dan"] = st.text_input("3.2 Účet pro odvod M-TECH daně:", value="Transparentní účet Unie rodičů M-TECH CORE")
            
        st.session_state.reg_data["dan_souhlas"] = st.checkbox("3.3 Zavazujeme se k odvodu M-TECH daně ze zisku (15–20 %).", value=st.session_state.reg_data.get("dan_souhlas", False))
        st.success("Krok 3 vyplněn.")

    with u_cssz:
        st.markdown("**Formulář ČSSZ-801: Oznámení o nástupu do zaměstnání & Registrace zaměstnavatele**")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.session_state.reg_data["seznam_zamestnancu"] = st.text_area("4.1 Seznam členů týmu:", value=st.session_state.reg_data.get("seznam_zamestnancu", f"{uzivatel}, CFO, CTO"))
        with col_p2:
            st.session_state.reg_data["mzdovy_fond"] = st.number_input("4.2 Předpokládaný mzdový fond (M-Kredity):", value=int(st.session_state.reg_data.get("mzdovy_fond", 300)))
        st.success("Krok 4 vyplněn.")

    with u_rejstrik:
        st.markdown("**Formulář OR-LIST: Návrh na zápis do Obchodního rejstříku M-TECH CORE**")
        st.session_state.reg_data["bozp_souhlas"] = st.checkbox("5.1 Prohlašujeme, že jsme absolvovali školení BOZP.", value=st.session_state.reg_data.get("bozp_souhlas", False))
        st.session_state.reg_data["kodex_souhlas"] = st.checkbox("5.2 Zavazujeme se k dodržování Etického kodexu M-TECH CORE.", value=st.session_state.reg_data.get("kodex_souhlas", False))

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

# --- TAB 4: PERSONALISTIKA, MZDY A HODNOCENÍ (DLE SEKCE 6.6 METODIKY) ---
with tab_hr:
    if not moje_firma:
        st.warning("Nejprve musíte podat registrační spis na záložce 1.")
    else:
        st.subheader("Personalistika, Mzdová listina a Vzájemné hodnocení")
        st.caption("Správa zaměstnanců, pracovní smlouvy (DPP/DPČ), docházka, výplaty a 360° vzájemné hodnocení (10 % váhy klasifikace).")
        
        hr_nabor, hr_mzdy, hr_peer = st.tabs([
            "📝 Nábor & Pracovní smlouvy",
            "⏱️ Výkaz práce & Mzdová listina",
            "⭐ 360° Vzájemné hodnocení"
        ])
        
        # 1. Nábor zaměstnance
        with hr_nabor:
            with st.form("form_novy_zamestnanec"):
                st.markdown("**Uzavření pracovní smlouvy / Dohody o provedení práce (DPP)**")
                col_z1, col_z2 = st.columns(2)
                with col_z1:
                    z_jmeno = st.text_input("Jméno a příjmení pracovníka / spolužáka:")
                    z_pozice = st.text_input("Pracovní pozice (např. Operátor CNC, Konstruktér, Účetní):")
                with col_z2:
                    z_smlouva = st.selectbox("Typ smluvního vztahu:", ["Dohoda o provedení práce (DPP)", "Dohoda o pracovní činnosti (DPČ)", "Student - Člen managementu"])
                    z_sazba = st.number_input("Hodinová mzda / odměna (v M-Kreditech / hod):", min_value=10, value=50)
                
                if st.form_submit_button("Sjednat smlouvu a zaevidovat pracovníka", icon=":material/badge:"):
                    if z_jmeno and z_pozice:
                        z_payload = {
                            "firma_id": moje_firma["id"],
                            "jmeno_zamestnance": z_jmeno,
                            "pozice": z_pozice,
                            "typ_smlouva": z_smlouva,
                            "hodinova_sazba": z_sazba,
                            "odpracovane_hodiny": 0,
                            "vyplaceno_celkem": 0,
                            "hodnoceni_skore": 100
                        }
                        requests.post(f"{SUPABASE_URL}/rest/v1/zamestnanci", headers=headers, json=z_payload)
                        st.success(f"Pracovník {z_jmeno} byl zaregistrován!")
                        st.rerun()
                    else:
                        st.warning("Vyplňte jméno i pozici pracovníka.")
                        
            st.write("---")
            st.caption("Registr zaměstnanců firmy:")
            res_z = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?firma_id=eq.{moje_firma['id']}&select=*", headers=headers)
            zamestnanci_seznam = res_z.json() if res_z.status_code == 200 else []
            if zamestnanci_seznam:
                st.dataframe(zamestnanci_seznam, use_container_width=True)
            else:
                st.info("Zatím nebyl zaregistrován žádný zaměstnanec.")

        # 2. Mzdová listina a výkaz práce
        with hr_mzdy:
            st.markdown("**Výkaz odpracovaných hodin a výplata mezd v M-Kreditech**")
            res_z = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?firma_id=eq.{moje_firma['id']}&select=*", headers=headers)
            zamestnanci_seznam = res_z.json() if res_z.status_code == 200 else []
            
            if zamestnanci_seznam:
                vybrany_z_jmeno = st.selectbox("Vyberte pracovníka pro výkaz hodin a výplatu:", [z["jmeno_zamestnance"] for z in zamestnanci_seznam])
                vybrany_z = next((z for z in zamestnanci_seznam if z["jmeno_zamestnance"] == vybrany_z_jmeno), None)
                
                if vybrany_z:
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        hodiny = st.number_input("Odpracované hodiny (v dílnách / na projektu):", min_value=1.0, value=4.0, step=0.5)
                        hruba_mzda = hodiny * vybrany_z["hodinova_sazba"]
                        mtech_dan_mzda = hruba_mzda * 0.15 # 15% odvod M-TECH
                        cista_mzda = hruba_mzda - mtech_dan_mzda
                        
                        st.markdown(f"""
                            <div class="card-box">
                                <p>Hodinová sazba: <b>{vybrany_z['hodinova_sazba']} M-K/hod</b></p>
                                <p>Hrubá mzda: <b>{hruba_mzda:.2f} M-Kreditů</b></p>
                                <p>Odvod M-TECH daň (15 %): <b>{mtech_dan_mzda:.2f} M-Kreditů</b></p>
                                <h4 style="color:#4ade80;">Čistá mzda k výplatě: {cista_mzda:.2f} M-Kreditů</h4>
                            </div>
                        """, unsafe_allow_html=True)
                        
                    with col_m2:
                        if st.button("Vyplatit mzdu a zapsat výdaj do Účetní knihy", icon=":material/payments:"):
                            # 1. Aktualizace zaměstnance
                            novy_stav_hodin = vybrany_z["odpracovane_hodiny"] + hodiny
                            novy_stav_vyplaceno = vybrany_z["vyplaceno_celkem"] + cista_mzda
                            requests.patch(f"{SUPABASE_URL}/rest/v1/zamestnanci?id=eq.{vybrany_z['id']}", headers=headers, json={
                                "odpracovane_hodiny": novy_stav_hodin,
                                "vyplaceno_celkem": novy_stav_vyplaceno
                            })
                            
                            # 2. Automatický zápis výdaje mzdy do účetnictví
                            t_payload = {
                                "firma_id": moje_firma["id"],
                                "typ_transakce": "VYDAJ",
                                "titul": f"Výplata mzdy: {vybrany_z['jmeno_zamestnance']} ({hodiny} hod)",
                                "castka": cista_mzda,
                                "auditovano": False
                            }
                            requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json=t_payload)
                            st.success(f"Mzda {cista_mzda:.2f} M-Kreditů byla úspěšně vyplacena a zaevidována do Účetní knihy!")
                            st.rerun()
            else:
                st.info("Nejprve zaregistrujte pracovníky na záložce 'Nábor & Pracovní smlouvy'.")

        # 3. 360° Hodnocení (Sekce 6.6 metodiky)
        with hr_peer:
            st.markdown("**Vzájemné hodnocení členů týmu (Peer Review - 10 % celkového hodnocení)**")
            st.caption("Podle Sekce 6.6 metodiky M-TECH CORE hodnotí každý člen přínos kolegy pro elminaci tzv. 'černých pasažérů'.")
            
            res_z = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?firma_id=eq.{moje_firma['id']}&select=*", headers=headers)
            zamestnanci_seznam = res_z.json() if res_z.status_code == 200 else []
            
            if zamestnanci_seznam:
                vybrany_z_peer = st.selectbox("Vyberte kolegu pro hodnocení:", [z["jmeno_zamestnance"] for z in zamestnanci_seznam], key="peer_select")
                z_peer_obj = next((z for z in zamestnanci_seznam if z["jmeno_zamestnance"] == vybrany_z_peer), None)
                
                if z_peer_obj:
                    bod_aktivita = st.slider("Aktivita a plnění úkolů (1-100 %):", min_value=10, max_value=100, value=90)
                    bod_spoluprace = st.slider("Týmová spolupráce a komunikace (1-100 %):", min_value=10, max_value=100, value=85)
                    
                    prumer_skore = (bod_aktivita + bod_spoluprace) / 2.0
                    st.markdown(f"**Výsledný koeficient pracovníka:** `{prumer_skore:.1f} %`")
                    
                    if st.button("Uložit peer-review hodnocení", icon=":material/rate_review:"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/zamestnanci?id=eq.{z_peer_obj['id']}", headers=headers, json={"hodnoceni_skore": prumer_skore})
                        st.success(f"Hodnocení pro {vybrany_z_peer} uloženo! Koeficient: {prumer_skore:.1f} %")
                        st.rerun()
            else:
                st.info("Zatím nejsou v databázi žádní zaměstnanci k hodnocení.")

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
