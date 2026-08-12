import streamlit as st
import requests
import datetime

st.set_page_config(page_title="Firemní Kancelář", page_icon=":material/business:", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3, h4 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #00B4D8; width: 100%; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0, 180, 216, 0.4); border-color: #00B4D8; }
    .card-box { background-color: #1e293b; padding: 20px; border-radius: 10px; border: 1px solid #334155; margin-bottom: 15px; }
    
    /* Kanban styly */
    .kanban-col-header { text-align: center; font-weight: 800; padding: 10px; border-radius: 8px; margin-bottom: 15px; color: #fff; }
    .header-todo { background: linear-gradient(45deg, #475569, #334155); }
    .header-ip { background: linear-gradient(45deg, #eab308, #ca8a04); }
    .header-done { background: linear-gradient(45deg, #22c55e, #16a34a); }
    .kanban-card { background-color: #0f172a; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #00B4D8; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
    .kanban-card h5 { margin: 0 0 8px 0; color: #f8fafc; font-size: 15px; }
    .kanban-card p { margin: 0; font-size: 13px; color: #94a3b8; }
    .kanban-badge { display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; background: rgba(0,180,216,0.15); color: #38bdf8; margin-top: 8px;}
    
    /* Elevator Pitch Box */
    .pitch-box { background: linear-gradient(135deg, #0f172a, #1e293b); padding: 25px; border-radius: 12px; border: 2px dashed #00B4D8; text-align: center; margin-top: 20px; }
    .pitch-box h3 { color: #38bdf8 !important; margin-bottom: 15px; font-size: 22px; }
    .pitch-text { font-size: 18px; line-height: 1.6; color: #f8fafc; font-weight: 600; font-style: italic; }
    .pitch-hl { color: #4ade80; text-decoration: underline; text-underline-offset: 4px; }
    
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

exist_canvas = None
has_canvas = False
has_porada = False
has_kalkulace = False
has_ucto = False

if moje_firma:
    f_id = moje_firma["id"]
    
    res_c = requests.get(f"{SUPABASE_URL}/rest/v1/lean_canvas?firma_id=eq.{f_id}", headers=headers)
    if res_c.status_code == 200 and len(res_c.json()) > 0:
        exist_canvas = res_c.json()[0]
        has_canvas = True

    res_p = requests.get(f"{SUPABASE_URL}/rest/v1/zapisy_porady?firma_id=eq.{f_id}", headers=headers)
    has_porada = len(res_p.json()) > 0 if res_p.status_code == 200 else False
    
    res_k = requests.get(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy?firma_id=eq.{f_id}", headers=headers)
    has_kalkulace = len(res_k.json()) > 0 if res_k.status_code == 200 else False
    
    res_u = requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?firma_id=eq.{f_id}", headers=headers)
    has_ucto = len(res_u.json()) > 0 if res_u.status_code == 200 else False

    # --- KONTROLNÍ PANEL STAVU ---
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
        if has_porada: st.markdown('<div class="status-badge-ok">Kanban & Porady OK</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="status-badge-off">Projekt neaktivní</div>', unsafe_allow_html=True)
    with col_s4:
        if has_kalkulace: st.markdown('<div class="status-badge-ok">Kalkulace OK</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="status-badge-off">Kalkulace Chybí</div>', unsafe_allow_html=True)
    with col_s5:
        if has_ucto: st.markdown('<div class="status-badge-ok">Účetnictví OK</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="status-badge-off">Kniha Prázdná</div>', unsafe_allow_html=True)

    st.write("---")

tab_zalozeni, tab_canvas, tab_agile, tab_hr, tab_kalkulace, tab_ucto = st.tabs([
    ":material/account_balance: 1. Založení", 
    ":material/rocket_launch: 2. Lean Canvas & Pitch", 
    ":material/view_kanban: 3. Agilní řízení (Kanban)",
    ":material/badge: 4. Personalistika & Mzdy",
    ":material/calculate: 5. Kalkulace", 
    ":material/menu_book: 6. Účetnictví"
])

# ==========================================
# TAB 1: ZALOŽENÍ (ÚŘEDNÍ KOLEČKO)
# ==========================================
with tab_zalozeni:
    st.subheader("Registrační spis firmy – Úřední tiskopisy a stav podání")
    
    if moje_firma:
        st.success(f"EVIDOVANÝ REGISTRAČNÍ SPIS FIRMY: {moje_firma['nazev_firmy']}")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.markdown(f"<div class='card-box'><h4>1. Notářský zápis & Orgány s.r.o.</h4><p><b>Obchodní firma:</b> {moje_firma['nazev_firmy']}</p><p><b>Úroveň:</b> Level {moje_firma['uroven_projektu']}</p><p><b>CEO:</b> {moje_firma['ceo_jmeno']}</p><p><b>CFO:</b> {moje_firma['cfo_jmeno']}</p><p><b>CTO:</b> {moje_firma['cto_jmeno']}</p><p><b>Kapitál:</b> {moje_firma['pocatecni_kapital']} M-K</p></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='card-box'><h4>3. Finanční úřad</h4><p><b>Režim M-TECH daně:</b> Odvod 15–20 % ze zisku</p></div>", unsafe_allow_html=True)
        with col_f2:
            st.markdown(f"<div class='card-box'><h4>2. Živnostenský úřad (JRF)</h4><p><b>Předmět:</b> {moje_firma['podnikatelsky_zamer']}</p><p><b>Kód školy:</b> {moje_firma['skolni_kod']}</p></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='card-box'><h4>4. ČSSZ, ZP & Rejstřík</h4><p><b>BOZP & Kodex:</b> Potvrzeno</p><p><b>Stav na Úřadu:</b> <b>{moje_firma['stave_licence']}</b></p></div>", unsafe_allow_html=True)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if moje_firma['stave_licence'] == "ZAMITNUTO" and st.button("Znovupodat registrační spis", icon=":material/refresh:"):
                requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{moje_firma['id']}", headers=headers, json={"stave_licence": "CEKA_NA_SCHVALENI"})
                st.rerun()
        with col_btn2:
            if st.button("Upravit údaje ve spisu", icon=":material/edit:"):
                st.session_state.edit_spis = True
                st.rerun()

    if not moje_firma or st.session_state.get("edit_spis", False):
        if st.session_state.get("edit_spis", False): st.warning("Režim úprav odeslaného registračního spisu:")
        u_notar, u_zivnost, u_financak, u_cssz, u_rejstrik = st.tabs(["📜 Notářství", "📋 JRF", "⚖️ FÚ", "🏥 ČSSZ", "🛡️ Rejstřík"])
        if "reg_data" not in st.session_state: st.session_state.reg_data = {}

        with u_notar:
            st.session_state.reg_data["nazev_firmy"] = st.text_input("1.1 Obchodní firma:", value=st.session_state.reg_data.get("nazev_firmy", moje_firma['nazev_firmy'] if moje_firma else ""))
            st.session_state.reg_data["skolni_kod"] = st.text_input("1.2 Kód školy:", value=st.session_state.reg_data.get("skolni_kod", moje_firma['skolni_kod'] if moje_firma else "")).upper().strip()
            col_n1, col_n2 = st.columns(2)
            with col_n1:
                st.session_state.reg_data["ceo"] = st.text_input("1.3 CEO:", value=st.session_state.reg_data.get("ceo", moje_firma['ceo_jmeno'] if moje_firma else uzivatel))
                st.session_state.reg_data["cfo"] = st.text_input("1.4 CFO:", value=st.session_state.reg_data.get("cfo", moje_firma['cfo_jmeno'] if moje_firma else ""))
            with col_n2:
                st.session_state.reg_data["cto"] = st.text_input("1.5 CTO:", value=st.session_state.reg_data.get("cto", moje_firma['cto_jmeno'] if moje_firma else ""))
                st.session_state.reg_data["vklad"] = st.number_input("1.6 Kapitál (M-K):", min_value=10, value=int(st.session_state.reg_data.get("vklad", 100)))

        with u_zivnost:
            col_j1, col_j2 = st.columns(2)
            with col_j1:
                st.session_state.reg_data["divize"] = st.selectbox("2.1 Divize:", ["Mechanical", "Power", "Cyber", "Strategy"])
            with col_j2:
                st.session_state.reg_data["predmet"] = st.text_input("2.2 Předmět podnikání:", value=st.session_state.reg_data.get("predmet", ""))
            st.session_state.reg_data["zamer"] = st.text_area("2.3 Detailní popis:", value=st.session_state.reg_data.get("zamer", ""))

        with u_financak:
            st.session_state.reg_data["dan_souhlas"] = st.checkbox("3.1 Zavazujeme se k odvodu M-TECH daně (15–20 %).", value=st.session_state.reg_data.get("dan_souhlas", True))

        with u_cssz:
            st.session_state.reg_data["seznam_zamestnancu"] = st.text_area("4.1 Členové:", value=st.session_state.reg_data.get("seznam_zamestnancu", f"{uzivatel}, CFO, CTO"))

        with u_rejstrik:
            st.session_state.reg_data["bozp_souhlas"] = st.checkbox("5.1 Prohlašujeme, že jsme absolvovali školení BOZP.", value=st.session_state.reg_data.get("bozp_souhlas", True))
            st.session_state.reg_data["kodex_souhlas"] = st.checkbox("5.2 Zavazujeme se k Etickému kodexu.", value=st.session_state.reg_data.get("kodex_souhlas", True))
            
            if st.button("PODAT REGISTRAČNÍ SPIS", icon=":material/send:"):
                d = st.session_state.reg_data
                if d.get("nazev_firmy") and d.get("skolni_kod") and d.get("cfo") and d.get("cto"):
                    res_lic = requests.get(f"{SUPABASE_URL}/rest/v1/licencovane_skoly?licencni_kod=eq.{d.get('skolni_kod')}", headers=headers)
                    u_num = res_lic.json()[0].get("uroven_projektu", 2) if (res_lic.status_code == 200 and res_lic.json()) else 2
                    payload = {
                        "nazev_firmy": d.get("nazev_firmy"), "skolni_kod": d.get("skolni_kod"), "uroven_projektu": u_num,
                        "ceo_jmeno": d.get("ceo"), "cfo_jmeno": d.get("cfo"), "cto_jmeno": d.get("cto"),
                        "podnikatelsky_zamer": f"[{d.get('divize')}] {d.get('predmet')} - {d.get('zamer')}",
                        "pocatecni_kapital": d.get("vklad", 100) * 3, "stave_licence": "CEKA_NA_SCHVALENI"
                    }
                    if moje_firma: requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{moje_firma['id']}", headers=headers, json=payload)
                    else: requests.post(f"{SUPABASE_URL}/rest/v1/firmy", headers=headers, json=payload)
                    st.session_state.edit_spis = False
                    st.rerun()


# ==========================================
# TAB 2: LEAN CANVAS A VÝTAHOVÝ PROJEV
# ==========================================
with tab_canvas:
    if not moje_firma:
        st.warning("Nejprve musíte založit firmu na záložce 1.")
    else:
        st.subheader("1-Page Business Plan (Lean Canvas)")
        st.caption("Jednostránkový vizuální model podnikání. Vyplňte jednotlivé bloky stručně a výstižně.")
        
        with st.form("form_canvas"):
            # Horní mřížka 4 sloupců
            col_c1, col_c2, col_c3, col_c4 = st.columns(4)
            with col_c1:
                prob = st.text_area("1. Problém trhu", value=exist_canvas.get("problem","") if exist_canvas else "", placeholder="Co lidi štve?", height=150)
            with col_c2:
                sol = st.text_area("2. Řešení (Produkt)", value=exist_canvas.get("reseni","") if exist_canvas else "", placeholder="Jak to vyřešíme?", height=150)
            with col_c3:
                val = st.text_area("3. Unikátní hodnota", value=exist_canvas.get("unikatni_hodnota","") if exist_canvas else "", placeholder="Proč jsme lepší než ostatní?", height=150)
            with col_c4:
                target = st.text_area("4. Cílová skupina", value=exist_canvas.get("cilova_skupina","") if exist_canvas else "", placeholder="Kdo nám zaplatí?", height=150)
            
            # Spodní mřížka 2 sloupců
            col_c5, col_c6 = st.columns(2)
            with col_c5:
                costs = st.text_area("5. Nákladová struktura", value=exist_canvas.get("nakladova_struktura","") if exist_canvas else "", placeholder="Materiál, stroje, mzdy...", height=100)
            with col_c6:
                rev = st.text_area("6. Příjmové toky", value=exist_canvas.get("prijmove_toky","") if exist_canvas else "", placeholder="Z čeho budeme mít zisk?", height=100)
            
            if st.form_submit_button("💾 Uložit do podnikatelského plánu"):
                c_payload = {"firma_id": moje_firma["id"], "problem": prob, "reseni": sol, "cilova_skupina": target, "unikatni_hodnota": val, "nakladova_struktura": costs, "prijmove_toky": rev}
                if exist_canvas:
                    requests.patch(f"{SUPABASE_URL}/rest/v1/lean_canvas?id=eq.{exist_canvas['id']}", headers=headers, json=c_payload)
                else:
                    requests.post(f"{SUPABASE_URL}/rest/v1/lean_canvas", headers=headers, json=c_payload)
                st.success("Lean Canvas byl úspěšně uložen!")
                st.rerun()

        # Automatický generátor Elevator Pitch (ŠMRNC)
        if exist_canvas and exist_canvas.get("cilova_skupina") and exist_canvas.get("problem"):
            st.markdown(f"""
                <div class="pitch-box">
                    <h3>🚀 Váš Elevator Pitch (Výtahový projev)</h3>
                    <p class="pitch-text">
                        "Naše studentská firma {moje_firma['nazev_firmy']} pomáhá zákazníkům z oblasti <span class="pitch-hl">{exist_canvas['cilova_skupina']}</span>, 
                        kteří řeší problém s <span class="pitch-hl">{exist_canvas['problem']}</span>. <br><br>
                        Řešíme to tak, že jim nabízíme <span class="pitch-hl">{exist_canvas['reseni']}</span>. 
                        Naše absolutní výhoda na trhu je <span class="pitch-hl">{exist_canvas['unikatni_hodnota']}</span>."
                    </p>
                </div>
            """, unsafe_allow_html=True)


# ==========================================
# TAB 3: AGILNÍ ŘÍZENÍ A PORADY
# ==========================================
with tab_agile:
    if not moje_firma:
        st.warning("Nejprve musíte podat registrační spis.")
    else:
        st.subheader("Agilní řízení projektů (Kanban)")
        ag_kanban, ag_porady = st.tabs(["📋 Kanban Board (Úkoly)", "👥 Zápisy z porad"])
        
        with ag_kanban:
            with st.form("form_novy_ukol"):
                col_u1, col_u2, col_u3 = st.columns(3)
                with col_u1:
                    u_nazev = st.text_input("Název úkolu (např. Tvorba loga):")
                with col_u2:
                    u_osoba = st.text_input("Zodpovídá (Jméno):", value=uzivatel)
                with col_u3:
                    u_termin = st.date_input("Deadline:", value=datetime.date.today() + datetime.timedelta(days=7))
                
                if st.form_submit_button("➕ Přidat úkol", icon=":material/add_task:"):
                    requests.post(f"{SUPABASE_URL}/rest/v1/projektove_ukoly", headers=headers, json={"firma_id": moje_firma["id"], "nazev_ukolu": u_nazev, "zodpovedna_osoba": u_osoba, "termin": str(u_termin), "stav": "TO_DO"})
                    st.rerun()

            st.write("---")
            res_ukoly = requests.get(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?firma_id=eq.{moje_firma['id']}&order=datum_zadani.desc", headers=headers)
            ukoly = res_ukoly.json() if res_ukoly.status_code == 200 else []
            
            col_todo, col_ip, col_done = st.columns(3)
            with col_todo:
                st.markdown("<div class='kanban-col-header header-todo'>📌 K VYŘEŠENÍ (To Do)</div>", unsafe_allow_html=True)
                for u in [x for x in ukoly if x['stav'] == 'TO_DO']:
                    st.markdown(f"<div class='kanban-card'><h5>{u['nazev_ukolu']}</h5><p><b>{u['zodpovedna_osoba']}</b></p><span class='kanban-badge'>Do: {u['termin']}</span></div>", unsafe_allow_html=True)
                    if st.button("Začít řešit", key=f"btn_ip_{u['id']}", icon=":material/play_arrow:"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?id=eq.{u['id']}", headers=headers, json={"stav": "IN_PROGRESS"})
                        st.rerun()

            with col_ip:
                st.markdown("<div class='kanban-col-header header-ip'>⏳ V PROCESU (In Progress)</div>", unsafe_allow_html=True)
                for u in [x for x in ukoly if x['stav'] == 'IN_PROGRESS']:
                    st.markdown(f"<div class='kanban-card' style='border-color:#eab308;'><h5>{u['nazev_ukolu']}</h5><p><b>{u['zodpovedna_osoba']}</b></p><span class='kanban-badge'>Do: {u['termin']}</span></div>", unsafe_allow_html=True)
                    if st.button("Dokončit", key=f"btn_done_{u['id']}", icon=":material/check_circle:"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?id=eq.{u['id']}", headers=headers, json={"stav": "DONE"})
                        st.rerun()

            with col_done:
                st.markdown("<div class='kanban-col-header header-done'>✅ HOTOVO (Done)</div>", unsafe_allow_html=True)
                for u in [x for x in ukoly if x['stav'] == 'DONE']:
                    st.markdown(f"<div class='kanban-card' style='border-color:#22c55e;'><h5>{u['nazev_ukolu']}</h5><p><b>{u['zodpovedna_osoba']}</b></p></div>", unsafe_allow_html=True)
                    if st.button("Smazat", key=f"btn_del_{u['id']}", icon=":material/delete:"):
                        requests.delete(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?id=eq.{u['id']}", headers=headers)
                        st.rerun()

        with ag_porady:
            with st.form("form_porada"):
                projednano = st.text_area("Projednané body na poradě (Agenda & Problémy):")
                ukoly_zapis = st.text_area("Slovní rozdělení úkolů:")
                if st.form_submit_button("Uložit zápis z porady", icon=":material/post_add:"):
                    requests.post(f"{SUPABASE_URL}/rest/v1/zapisy_porady", headers=headers, json={"firma_id": moje_firma["id"], "projednane_body": projednano, "ukoly_a_odpovednost": ukoly_zapis})
                    st.rerun()
                    
            res_p_hist = requests.get(f"{SUPABASE_URL}/rest/v1/zapisy_porady?firma_id=eq.{moje_firma['id']}&order=datum.desc", headers=headers)
            if res_p_hist.status_code == 200 and res_p_hist.json():
                for p in res_p_hist.json():
                    st.markdown(f"<div class='card-box'><small style='color:#00B4D8;'>Datum: {p['datum'][:10]}</small><p><b>Projednáno:</b> {p['projednane_body']}</p><p><b>Úkoly:</b> {p['ukoly_a_odpovednost']}</p></div>", unsafe_allow_html=True)


# ==========================================
# TAB 4: PERSONALISTIKA A MZDY
# ==========================================
with tab_hr:
    if not moje_firma:
        st.warning("Nejprve musíte podat registrační spis.")
    else:
        st.subheader("Personalistika, Mzdová listina a Hodnocení")
        hr_nabor, hr_mzdy, hr_peer = st.tabs(["📝 Pracovní smlouvy", "⏱️ Výkaz práce & Mzdy", "⭐ Peer Review (Hodnocení)"])
        
        with hr_nabor:
            with st.form("form_novy_zamestnanec"):
                col_z1, col_z2 = st.columns(2)
                with col_z1:
                    z_jmeno = st.text_input("Jméno a příjmení pracovníka:")
                    z_pozice = st.text_input("Pracovní pozice:")
                with col_z2:
                    z_smlouva = st.selectbox("Typ smluvního vztahu:", ["DPP", "DPČ", "Management"])
                    z_sazba = st.number_input("Hodinová mzda (M-K / hod):", min_value=10, value=50)
                if st.form_submit_button("Sjednat smlouvu", icon=":material/badge:"):
                    requests.post(f"{SUPABASE_URL}/rest/v1/zamestnanci", headers=headers, json={"firma_id": moje_firma["id"], "jmeno_zamestnance": z_jmeno, "pozice": z_pozice, "typ_smlouva": z_smlouva, "hodinova_sazba": z_sazba, "odpracovane_hodiny": 0, "vyplaceno_celkem": 0, "hodnoceni_skore": 100})
                    st.rerun()

        with hr_mzdy:
            res_z = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?firma_id=eq.{moje_firma['id']}&select=*", headers=headers)
            zamestnanci_seznam = res_z.json() if res_z.status_code == 200 else []
            if zamestnanci_seznam:
                vybrany_z_jmeno = st.selectbox("Vyberte pracovníka pro výplatní pásku:", [z["jmeno_zamestnance"] for z in zamestnanci_seznam])
                vybrany_z = next((z for z in zamestnanci_seznam if z["jmeno_zamestnance"] == vybrany_z_jmeno), None)
                if vybrany_z:
                    hodiny = st.number_input("Odpracované hodiny:", min_value=1.0, value=4.0, step=0.5)
                    hruba = hodiny * vybrany_z["hodinova_sazba"]
                    dan = hruba * 0.15
                    cista = hruba - dan
                    st.markdown(f"Hrubá mzda: `{hruba:.2f} M-K` | Daň (15 %): `{dan:.2f} M-K` | **Čistá mzda: `{cista:.2f} M-K`**")
                    if st.button("Vyplatit a zapsat do účetnictví", icon=":material/payments:"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/zamestnanci?id=eq.{vybrany_z['id']}", headers=headers, json={"odpracovane_hodiny": vybrany_z["odpracovane_hodiny"] + hodiny, "vyplaceno_celkem": vybrany_z["vyplaceno_celkem"] + cista})
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": "VYDAJ", "titul": f"Výplata: {vybrany_z['jmeno_zamestnance']}", "castka": cista, "auditovano": False})
                        st.success("Mzda vyplacena!")
                        st.rerun()

        with hr_peer:
            if zamestnanci_seznam:
                vybrany_z_peer = st.selectbox("Vyberte kolegu pro hodnocení:", [z["jmeno_zamestnance"] for z in zamestnanci_seznam], key="peer_select")
                z_peer_obj = next((z for z in zamestnanci_seznam if z["jmeno_zamestnance"] == vybrany_z_peer), None)
                if z_peer_obj:
                    bod_aktivita = st.slider("Aktivita a plnění úkolů (%):", min_value=10, max_value=100, value=90)
                    bod_spoluprace = st.slider("Týmová spolupráce (%):", min_value=10, max_value=100, value=85)
                    if st.button("Uložit peer-review hodnocení", icon=":material/rate_review:"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/zamestnanci?id=eq.{z_peer_obj['id']}", headers=headers, json={"hodnoceni_skore": (bod_aktivita + bod_spoluprace) / 2.0})
                        st.rerun()

# ==========================================
# TAB 5: KALKULAČNÍ LISTY
# ==========================================
with tab_kalkulace:
    if not moje_firma:
        st.warning("Nejprve musíte podat registrační spis.")
    else:
        st.subheader("Návrh nového produktu a Kalkulační vzorec")
        with st.form("form_kalkulace"):
            prod_nazev = st.text_input("Název produktu / služby:")
            p_naklady = st.number_input("Přímé náklady (materiál) v M-Kreditech:", min_value=0.0, value=35.0)
            rezie = st.number_input("Virtuální režie školy v M-Kreditech:", min_value=0.0, value=10.0)
            marze = st.number_input("Plánovaná marže v M-Kreditech:", min_value=0.0, value=50.0)
            dan_pct = st.number_input("M-TECH Daň pro Fond rozvoje (%):", min_value=10.0, max_value=30.0, value=15.0)
            
            z_dane = p_naklady + rezie + marze
            v_dan = z_dane * (dan_pct / 100.0)
            k_cena = z_dane + v_dan
            
            st.markdown(f"**M-TECH daň:** `{v_dan:.2f} M-K` | **Prodejní cena:** `{k_cena:.2f} M-Kreditů`")
            if st.form_submit_button("Odeslat kalkulaci ke schválení", icon=":material/send:"):
                requests.post(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy", headers=headers, json={"firma_id": moje_firma["id"], "nazev_produktu": prod_nazev, "prime_naklady": p_naklady, "rezie_skoly": rezie, "mtech_dan_procento": dan_pct, "marze_zisk": marze, "konecna_cena": k_cena, "schvaleno_uradem": False})
                st.rerun()

# ==========================================
# TAB 6: ÚČETNICTVÍ A CASH-FLOW
# ==========================================
with tab_ucto:
    if not moje_firma:
        st.warning("Nejprve musíte podat registrační spis.")
    else:
        st.subheader("Kniha příjmů a výdajů (Cash-flow)")
        with st.form("form_transakce"):
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1: typ = st.selectbox("Typ zápisu:", ["PRIJEM", "VYDAJ"])
            with col_t2: titul = st.text_input("Titul:", value="Nákup materiálu")
            with col_t3: castka = st.number_input("Částka v M-Kreditech:", min_value=1.0, value=50.0)
            if st.form_submit_button("Zapsat do účetní knihy", icon=":material/add_circle:"):
                requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": typ, "titul": titul, "castka": castka, "auditovano": False})
                st.rerun()
                
        res_kniha = requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?firma_id=eq.{moje_firma['id']}&order=datum.desc", headers=headers)
        if res_kniha.status_code == 200 and len(res_kniha.json()) > 0:
            st.dataframe(res_kniha.json(), use_container_width=True)
