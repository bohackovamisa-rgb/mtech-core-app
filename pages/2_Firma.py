import streamlit as st
import requests
import datetime

st.set_page_config(page_title="Startup Hub", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3, h4 { background: -webkit-linear-gradient(45deg, #0ea5e9, #10b981); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #0ea5e9; width: 100%; font-weight: 600; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(14, 165, 233, 0.4); border-color: #0ea5e9; }
    .card-box { background-color: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 15px; transition: all 0.3s; }
    .card-box:hover { border-color: #0ea5e9; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
    
    /* Kanban styly */
    .kanban-col-header { text-align: center; font-weight: 800; padding: 12px; border-radius: 8px; margin-bottom: 15px; color: #fff; text-transform: uppercase; letter-spacing: 1px; font-size: 14px; }
    .header-todo { background: linear-gradient(45deg, #475569, #334155); }
    .header-ip { background: linear-gradient(45deg, #f59e0b, #d97706); }
    .header-done { background: linear-gradient(45deg, #10b981, #059669); }
    .kanban-card { background-color: #0f172a; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #0ea5e9; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
    .kanban-card h5 { margin: 0 0 8px 0; color: #f8fafc; font-size: 15px; }
    .kanban-badge { display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: bold; background: rgba(14, 165, 233, 0.15); color: #38bdf8; margin-top: 8px;}
    
    /* Elevator Pitch */
    .pitch-box { background: linear-gradient(135deg, #0f172a, #1e293b); padding: 30px; border-radius: 16px; border: 2px dashed #0ea5e9; text-align: center; margin-top: 20px; }
    .pitch-box h3 { color: #38bdf8 !important; margin-bottom: 15px; font-size: 24px; }
    .pitch-text { font-size: 19px; line-height: 1.6; color: #f8fafc; font-weight: 600; font-style: italic; }
    .pitch-hl { color: #10b981; text-decoration: underline; text-underline-offset: 4px; }
    
    /* Badges */
    .status-badge-ok { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid #10b981; padding: 10px; border-radius: 8px; font-weight: 700; text-align: center; text-transform: uppercase; font-size: 12px; }
    .status-badge-wait { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid #f59e0b; padding: 10px; border-radius: 8px; font-weight: 700; text-align: center; text-transform: uppercase; font-size: 12px; }
    .status-badge-err { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid #ef4444; padding: 10px; border-radius: 8px; font-weight: 700; text-align: center; text-transform: uppercase; font-size: 12px; }
    .status-badge-off { background: rgba(148, 163, 184, 0.1); color: #94a3b8; border: 1px solid #475569; padding: 10px; border-radius: 8px; font-weight: 600; text-align: center; text-transform: uppercase; font-size: 12px; }
    
    .startup-tag { display: inline-block; background: linear-gradient(90deg, #8b5cf6, #3b82f6); color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-bottom: 10px; letter-spacing: 1px;}
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Startup Hub M-TECH CORE")
st.caption("Buduj. Inovuj. Škáluj. Tvoje cesta od nápadu v garáži až po plně funkční byznys.")

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
has_canvas, has_porada, has_kalkulace, has_ucto = False, False, False, False

if moje_firma:
    f_id = moje_firma["id"]
    res_c = requests.get(f"{SUPABASE_URL}/rest/v1/lean_canvas?firma_id=eq.{f_id}", headers=headers)
    if res_c.status_code == 200 and len(res_c.json()) > 0:
        exist_canvas = res_c.json()[0]
        has_canvas = True

    has_porada = len(requests.get(f"{SUPABASE_URL}/rest/v1/zapisy_porady?firma_id=eq.{f_id}", headers=headers).json()) > 0
    has_kalkulace = len(requests.get(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy?firma_id=eq.{f_id}", headers=headers).json()) > 0
    has_ucto = len(requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?firma_id=eq.{f_id}", headers=headers).json()) > 0

    stage = "Garážový Startup 🛠️" if moje_firma['uroven_projektu'] == 1 else ("Seed Fáze (Trh) 🌱" if moje_firma['uroven_projektu'] == 2 else "Scale-up (Pro) 🦄")
    st.markdown(f"<div class='startup-tag'>{stage}</div>", unsafe_allow_html=True)

    st.subheader("📊 Startup Health Check (Trakce)")
    col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
    stav = moje_firma['stave_licence']
    
    with col_s1:
        if stav == "SCHVALENO": st.markdown('<div class="status-badge-ok">Legal OK 🏛️</div>', unsafe_allow_html=True)
        elif stav == "CEKA_NA_SCHVALENI": st.markdown('<div class="status-badge-wait">Čeká na Audit</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="status-badge-err">Spis Zamítnut</div>', unsafe_allow_html=True)
    with col_s2:
        if has_canvas: st.markdown('<div class="status-badge-ok">Vision & Pitch 💡</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="status-badge-off">No Vision</div>', unsafe_allow_html=True)
    with col_s3:
        if has_porada: st.markdown('<div class="status-badge-ok">Agile & Scrum ⚡</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="status-badge-off">Agile Inactive</div>', unsafe_allow_html=True)
    with col_s4:
        if has_kalkulace: st.markdown('<div class="status-badge-ok">Unit Economics 📈</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="status-badge-off">Bez nacenění</div>', unsafe_allow_html=True)
    with col_s5:
        if has_ucto: st.markdown('<div class="status-badge-ok">Cash-flow OK 💸</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="status-badge-off">Runway 0</div>', unsafe_allow_html=True)

    st.write("---")

tab_zalozeni, tab_canvas, tab_agile, tab_hr, tab_kalkulace, tab_ucto = st.tabs([
    "🏛️ 1. Legal & Founders", 
    "💡 2. Vision & Pitch", 
    "⚡ 3. Agilní vývoj (Scrum)",
    "🦄 4. Tým & Kultura (HR)",
    "📈 5. Unit Economics", 
    "💸 6. Cash-flow & Burn Rate"
])

# ==========================================
# TAB 1: ZALOŽENÍ (LEGAL) - REÁLNÁ BYROKRACIE
# ==========================================
with tab_zalozeni:
    st.subheader("Legal & Founders – Právní základ startupu")
    st.caption("Založení firmy není jen o nápadu. Musíte mít v pořádku papíry pro všechny státní úřady. Vyplňte kompletní registrační spis s.r.o.")
    
    if moje_firma:
        st.success(f"EVIDOVANÝ REGISTRAČNÍ SPIS STARTUPU: {moje_firma['nazev_firmy']}")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.markdown(f"""
                <div class='card-box'>
                    <h4>1. Notářský zápis & Orgány s.r.o.</h4>
                    <p><b>Startup:</b> {moje_firma['nazev_firmy']}</p>
                    <p><b>Úroveň:</b> Level {moje_firma['uroven_projektu']}</p>
                    <p><b>CEO (Visionary):</b> {moje_firma['ceo_jmeno']}</p>
                    <p><b>CFO (Finance & Ops):</b> {moje_firma['cfo_jmeno']}</p>
                    <p><b>CTO (Tech & Product):</b> {moje_firma['cto_jmeno']}</p>
                    <p><b>Základní (Seed) Kapitál:</b> {moje_firma['pocatecni_kapital']} M-K</p>
                </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
                <div class='card-box'>
                    <h4>3. Finanční úřad</h4>
                    <p><b>Daňový režim:</b> DPPO, Daň ze závislé činnosti, M-TECH Daň</p>
                    <p><b>Správa daně:</b> {'Transparentní účet' if moje_firma['uroven_projektu'] == 3 else 'Interní systém M-Kreditů'}</p>
                </div>
            """, unsafe_allow_html=True)
        with col_f2:
            st.markdown(f"""
                <div class='card-box'>
                    <h4>2. Živnostenský úřad (JRF)</h4>
                    <p><b>Divize & Předmět:</b> {moje_firma['podnikatelsky_zamer'].split('|')[0] if '|' in moje_firma['podnikatelsky_zamer'] else moje_firma['podnikatelsky_zamer']}</p>
                    <p><b>Licenční kód školy:</b> {moje_firma['skolni_kod']}</p>
                </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
                <div class='card-box'>
                    <h4>4. ČSSZ, ZP & Rejstřík</h4>
                    <p><b>Registrace zaměstnavatele:</b> Hotovo</p>
                    <p><b>BOZP & Kodex:</b> Potvrzeno ✅</p>
                    <p><b>Status na Úřadu:</b> <b style="color:#0ea5e9;">{moje_firma['stave_licence']}</b></p>
                </div>
            """, unsafe_allow_html=True)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if moje_firma['stave_licence'] == "ZAMITNUTO" and st.button("Znovupodat k auditu", icon=":material/refresh:"):
                requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{moje_firma['id']}", headers=headers, json={"stave_licence": "CEKA_NA_SCHVALENI"})
                st.rerun()
        with col_btn2:
            if st.button("Pivot / Upravit úřední údaje", icon=":material/edit:"):
                st.session_state.edit_spis = True
                st.rerun()

    if not moje_firma or st.session_state.get("edit_spis", False):
        if st.session_state.get("edit_spis", False): st.warning("Režim úprav odeslaného registračního spisu:")
        u_notar, u_zivnost, u_financak, u_cssz, u_rejstrik = st.tabs(["📜 Notářství", "📋 JRF (Živnosti)", "⚖️ FÚ (Daně)", "🏥 ČSSZ & ZP", "🛡️ Rejstřík"])
        if "reg_data" not in st.session_state: st.session_state.reg_data = {}

        # 1. NOTÁŘSTVÍ
        with u_notar:
            st.markdown("**Formulář N-01: Zakladatelská listina a jmenování orgánů s.r.o.**")
            st.session_state.reg_data["nazev_firmy"] = st.text_input("1.1 Obchodní firma (včetně koncovky s.r.o.):", value=st.session_state.reg_data.get("nazev_firmy", moje_firma['nazev_firmy'] if moje_firma else ""))
            st.session_state.reg_data["sidlo"] = st.text_input("1.2 Sídlo společnosti (Ulice, č.p., Město, PSČ):", value=st.session_state.reg_data.get("sidlo", "Školní 101, 123 45 Město"))
            st.session_state.reg_data["skolni_kod"] = st.text_input("1.3 Licenční kód školy (Akcelerátoru):", value=st.session_state.reg_data.get("skolni_kod", moje_firma['skolni_kod'] if moje_firma else "")).upper().strip()
            
            col_n1, col_n2 = st.columns(2)
            with col_n1:
                st.session_state.reg_data["ceo"] = st.text_input("1.4 Jednatel / CEO (Jméno a příjmení):", value=st.session_state.reg_data.get("ceo", moje_firma['ceo_jmeno'] if moje_firma else uzivatel))
                st.session_state.reg_data["cfo"] = st.text_input("1.5 Finanční ředitel / CFO:", value=st.session_state.reg_data.get("cfo", moje_firma['cfo_jmeno'] if moje_firma else ""))
                st.session_state.reg_data["cto"] = st.text_input("1.6 Technický ředitel / CTO:", value=st.session_state.reg_data.get("cto", moje_firma['cto_jmeno'] if moje_firma else ""))
            with col_n2:
                st.session_state.reg_data["ceo_narozeni"] = st.date_input("1.7 Datum narození jednatele (CEO):", value=datetime.date(2005, 1, 1))
                st.session_state.reg_data["spravce_vkladu"] = st.text_input("1.8 Správce vkladu (kdo nese odpovědnost za kapitál):", value="CFO")
                st.session_state.reg_data["vklad"] = st.number_input("1.9 Základní kapitál na 1 společníka (M-K / CZK):", min_value=10, value=int(st.session_state.reg_data.get("vklad", 100)))

        # 2. ŽIVNOSTENSKÝ ÚŘAD (JRF)
        with u_zivnost:
            st.markdown("**Formulář JRF: Jednotný registrační formulář pro právnické osoby**")
            col_j1, col_j2 = st.columns(2)
            with col_j1:
                st.session_state.reg_data["divize"] = st.selectbox("2.1 Oborová divize (Sektor):", ["Hardware & Strojírenství", "Energy & Elektro", "Software, AI & IT", "Služby & Marketing"])
                st.session_state.reg_data["druh_zivnosti"] = st.selectbox("2.2 Druh živnosti:", ["Ohlašovací volná", "Ohlašovací řemeslná", "Ohlašovací vázaná"])
                st.session_state.reg_data["provozovna"] = st.text_input("2.3 Sídlo provozovny (Dílny / Laboratoře):", value="Školní dílny – Výzkumný blok B")
            with col_j2:
                st.session_state.reg_data["predmet"] = st.text_input("2.4 Předmět podnikání (Přesný název oboru):", value=st.session_state.reg_data.get("predmet", ""))
                st.session_state.reg_data["datum_zahajeni"] = st.date_input("2.5 Datum zahájení provozování živnosti:", value=datetime.date.today())
                st.session_state.reg_data["bozp_garant"] = st.text_input("2.6 Odpovědný zástupce BOZP a PO:", value=st.session_state.reg_data.get("bozp_garant", uzivatel))
            st.session_state.reg_data["zamer"] = st.text_area("2.7 Detailní popis činnosti (Pro zápis do JRF):", value=st.session_state.reg_data.get("zamer", ""))

        # 3. FINANČNÍ ÚŘAD
        with u_financak:
            st.markdown("**Formulář FÚ-5540: Přihláška k registraci k daním**")
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                st.session_state.reg_data["typ_dani"] = st.multiselect("3.1 Registrace k daním (Zaškrtněte platné):", ["Daň z příjmů právnických osob (DPPO)", "Daň ze závislé činnosti (Mzdy)", "M-TECH Daň"], default=["Daň z příjmů právnických osob (DPPO)", "Daň ze závislé činnosti (Mzdy)", "M-TECH Daň"])
                st.session_state.reg_data["zdani_obdobi"] = st.selectbox("3.2 Zdaňovací období:", ["Kalendářní rok", "Pololetní cyklus (M-TECH)"])
            with col_f2:
                st.session_state.reg_data["dph_status"] = st.selectbox("3.3 Registrace k DPH:", ["Neplátce DPH", "Plátce DPH", "Identifikovaná osoba"])
                st.session_state.reg_data["ucet_pro_dan"] = st.text_input("3.4 Účet pro odvod daní (Číslo účtu):", value="Přiřazuje systém automaticky (Dle úrovně licence)", disabled=True)
            st.session_state.reg_data["dan_souhlas"] = st.checkbox("3.5 Souhlasím s povinností automatického výpočtu a odvodu M-TECH daně z profitu.", value=st.session_state.reg_data.get("dan_souhlas", True))

        # 4. ČSSZ A ZP
        with u_cssz:
            st.markdown("**Formulář ČSSZ-801 a ZP: Oznámení o nástupu & Registrace zaměstnavatele**")
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.session_state.reg_data["datum_prvniho_zamestnance"] = st.date_input("4.1 Datum nástupu prvního zaměstnance:")
                st.session_state.reg_data["zp_kod"] = st.selectbox("4.2 Převažující zdravotní pojišťovna zaměstnanců:", ["111 - VZP ČR", "201 - VoZP ČR", "205 - ČPZP", "207 - OZP", "211 - ZPMV ČR"])
            with col_p2:
                st.session_state.reg_data["seznam_zamestnancu"] = st.text_area("4.3 Seznam prvních pojištěnců (Zaměstnanci/Dohodáři):", value=st.session_state.reg_data.get("seznam_zamestnancu", f"{uzivatel}, CFO, CTO"))
                st.session_state.reg_data["mzdovy_fond"] = st.number_input("4.4 Předpokládaný měsíční mzdový fond (M-Kredity):", value=int(st.session_state.reg_data.get("mzdovy_fond", 300)))

        # 5. OBCHODNÍ REJSTŘÍK
        with u_rejstrik:
            st.markdown("**Formulář OR-LIST: Návrh na zápis do Obchodního rejstříku M-TECH CORE**")
            st.session_state.reg_data["bozp_souhlas"] = st.checkbox("5.1 Prohlašujeme, že jako zakladatelé máme platné proškolení z BOZP a PO pro naši provozovnu.", value=st.session_state.reg_data.get("bozp_souhlas", True))
            st.session_state.reg_data["kodex_souhlas"] = st.checkbox("5.2 Zavazujeme se k Etickému kodexu (Férové podnikání).", value=st.session_state.reg_data.get("kodex_souhlas", True))
            
            st.write("---")
            if st.button("🚀 ODESLAT REGISTRAČNÍ SPIS DO AKCELERÁTORU (Úřad)", icon=":material/send:"):
                d = st.session_state.reg_data
                if d.get("nazev_firmy") and d.get("skolni_kod") and d.get("cfo") and d.get("cto") and d.get("dan_souhlas") and d.get("bozp_souhlas") and d.get("kodex_souhlas"):
                    res_lic = requests.get(f"{SUPABASE_URL}/rest/v1/licencovane_skoly?licencni_kod=eq.{d.get('skolni_kod')}", headers=headers)
                    u_num = res_lic.json()[0].get("uroven_projektu", 2) if (res_lic.status_code == 200 and res_lic.json()) else 2
                    
                    # Agregace všech úředních dat do jednoho textu pro databázi
                    souhrn_zameru = f"[{d.get('divize')}] {d.get('predmet')} | Sídlo: {d.get('sidlo')} | FÚ: {d.get('dph_status')} | ČSSZ: od {d.get('datum_prvniho_zamestnance')} (ZP: {d.get('zp_kod')}) | BOZP: {d.get('bozp_garant')} | Záměr: {d.get('zamer')}"
                    
                    payload = {
                        "nazev_firmy": d.get("nazev_firmy"), "skolni_kod": d.get("skolni_kod"), "uroven_projektu": u_num,
                        "ceo_jmeno": d.get("ceo"), "cfo_jmeno": d.get("cfo"), "cto_jmeno": d.get("cto"),
                        "podnikatelsky_zamer": souhrn_zameru,
                        "pocatecni_kapital": d.get("vklad", 100) * 3, "stave_licence": "CEKA_NA_SCHVALENI"
                    }
                    if moje_firma: requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{moje_firma['id']}", headers=headers, json=payload)
                    else: requests.post(f"{SUPABASE_URL}/rest/v1/firmy", headers=headers, json=payload)
                    st.session_state.edit_spis = False
                    st.rerun()
                else:
                    st.warning("Vyplňte všechny povinné pole a potvrďte souhlasy.")


# ==========================================
# TAB 2: VISION & PITCH (LEAN CANVAS)
# ==========================================
with tab_canvas:
    if not moje_firma:
        st.warning("Nejprve musíte projít procesem Založení (Legal).")
    else:
        st.subheader("Business Model & Elevator Pitch")
        with st.form("form_canvas"):
            col_c1, col_c2, col_c3, col_c4 = st.columns(4)
            with col_c1:
                prob = st.text_area("1. Pain Point (Problém trhu)", value=exist_canvas.get("problem","") if exist_canvas else "", placeholder="Co lidi štve?", height=150)
            with col_c2:
                sol = st.text_area("2. Náš Produkt (Řešení)", value=exist_canvas.get("reseni","") if exist_canvas else "", placeholder="Jak to vyřešíme?", height=150)
            with col_c3:
                val = st.text_area("3. Unfair Advantage (Hodnota)", value=exist_canvas.get("unikatni_hodnota","") if exist_canvas else "", placeholder="Proč nás konkurence nedožene?", height=150)
            with col_c4:
                target = st.text_area("4. Target Audience (Zákazníci)", value=exist_canvas.get("cilova_skupina","") if exist_canvas else "", placeholder="Kdo je early adopter?", height=150)
            
            col_c5, col_c6 = st.columns(2)
            with col_c5:
                costs = st.text_area("5. Burn Rate (Náklady)", value=exist_canvas.get("nakladova_struktura","") if exist_canvas else "", placeholder="Za co budeme pálit peníze?", height=100)
            with col_c6:
                rev = st.text_area("6. Revenue Streams (Příjmy)", value=exist_canvas.get("prijmove_toky","") if exist_canvas else "", placeholder="Jak budeme monetizovat?", height=100)
            
            if st.form_submit_button("💾 Ship it! (Uložit Lean Canvas)"):
                c_payload = {"firma_id": moje_firma["id"], "problem": prob, "reseni": sol, "cilova_skupina": target, "unikatni_hodnota": val, "nakladova_struktura": costs, "prijmove_toky": rev}
                if exist_canvas: requests.patch(f"{SUPABASE_URL}/rest/v1/lean_canvas?id=eq.{exist_canvas['id']}", headers=headers, json=c_payload)
                else: requests.post(f"{SUPABASE_URL}/rest/v1/lean_canvas", headers=headers, json=c_payload)
                st.rerun()

        if exist_canvas and exist_canvas.get("cilova_skupina") and exist_canvas.get("problem"):
            st.markdown(f"""
                <div class="pitch-box">
                    <h3>🎤 Váš Elevator Pitch (Připraveno pro investory)</h3>
                    <p class="pitch-text">
                        "Náš startup {moje_firma['nazev_firmy']} pomáhá <span class="pitch-hl">{exist_canvas['cilova_skupina']}</span>, 
                        kteří řeší obrovský problém s <span class="pitch-hl">{exist_canvas['problem']}</span>. <br><br>
                        Naše řešení je <span class="pitch-hl">{exist_canvas['reseni']}</span>. 
                        Naše unfair advantage, díky které ovládneme trh, je <span class="pitch-hl">{exist_canvas['unikatni_hodnota']}</span>."
                    </p>
                </div>
            """, unsafe_allow_html=True)


# ==========================================
# TAB 3: AGILNÍ VÝVOJ & SCRUM
# ==========================================
with tab_agile:
    if not moje_firma:
        st.warning("Nejprve musíte projít procesem Založení.")
    else:
        st.subheader("Agilní řízení (Kanban) & Daily Stand-upy")
        ag_kanban, ag_porady = st.tabs(["📋 Backlog & Sprint (Kanban)", "👥 Stand-up Log (Porady)"])
        
        with ag_kanban:
            with st.form("form_novy_ukol"):
                col_u1, col_u2, col_u3 = st.columns(3)
                with col_u1:
                    u_nazev = st.text_input("Nový Task / Feature (Co je potřeba?):")
                with col_u2:
                    u_osoba = st.text_input("Owner (Kdo to dodá?):", value=uzivatel)
                with col_u3:
                    u_termin = st.date_input("Deadline:", value=datetime.date.today() + datetime.timedelta(days=7))
                
                if st.form_submit_button("➕ Přidat do Backlogu", icon=":material/add_task:"):
                    requests.post(f"{SUPABASE_URL}/rest/v1/projektove_ukoly", headers=headers, json={"firma_id": moje_firma["id"], "nazev_ukolu": u_nazev, "zodpovedna_osoba": u_osoba, "termin": str(u_termin), "stav": "TO_DO"})
                    st.rerun()

            st.write("---")
            res_ukoly = requests.get(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?firma_id=eq.{moje_firma['id']}&order=datum_zadani.desc", headers=headers)
            ukoly = res_ukoly.json() if res_ukoly.status_code == 200 else []
            
            col_todo, col_ip, col_done = st.columns(3)
            with col_todo:
                st.markdown("<div class='kanban-col-header header-todo'>📌 BACKLOG (To Do)</div>", unsafe_allow_html=True)
                for u in [x for x in ukoly if x['stav'] == 'TO_DO']:
                    st.markdown(f"<div class='kanban-card'><h5>{u['nazev_ukolu']}</h5><p>Owner: <b>{u['zodpovedna_osoba']}</b></p><span class='kanban-badge'>Deadline: {u['termin']}</span></div>", unsafe_allow_html=True)
                    if st.button("Zařadit do Sprintu", key=f"btn_ip_{u['id']}", icon=":material/play_arrow:"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?id=eq.{u['id']}", headers=headers, json={"stav": "IN_PROGRESS"})
                        st.rerun()

            with col_ip:
                st.markdown("<div class='kanban-col-header header-ip'>⏳ SPRINT (In Progress)</div>", unsafe_allow_html=True)
                for u in [x for x in ukoly if x['stav'] == 'IN_PROGRESS']:
                    st.markdown(f"<div class='kanban-card' style='border-color:#f59e0b;'><h5>{u['nazev_ukolu']}</h5><p>Owner: <b>{u['zodpovedna_osoba']}</b></p><span class='kanban-badge'>Deadline: {u['termin']}</span></div>", unsafe_allow_html=True)
                    if st.button("Dokončit task", key=f"btn_done_{u['id']}", icon=":material/check_circle:"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?id=eq.{u['id']}", headers=headers, json={"stav": "DONE"})
                        st.rerun()

            with col_done:
                st.markdown("<div class='kanban-col-header header-done'>🚀 SHIPPED! (Done)</div>", unsafe_allow_html=True)
                for u in [x for x in ukoly if x['stav'] == 'DONE']:
                    st.markdown(f"<div class='kanban-card' style='border-color:#10b981;'><h5>{u['nazev_ukolu']}</h5><p>Owner: <b>{u['zodpovedna_osoba']}</b></p></div>", unsafe_allow_html=True)
                    if st.button("Smazat & Uklidit", key=f"btn_del_{u['id']}", icon=":material/delete:"):
                        requests.delete(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?id=eq.{u['id']}", headers=headers)
                        st.rerun()

        with ag_porady:
            with st.form("form_porada"):
                projednano = st.text_area("Stand-up Agenda & Blockers:")
                ukoly_zapis = st.text_area("Akční kroky (Action Items):")
                if st.form_submit_button("Uložit Log", icon=":material/post_add:"):
                    requests.post(f"{SUPABASE_URL}/rest/v1/zapisy_porady", headers=headers, json={"firma_id": moje_firma["id"], "projednane_body": projednano, "ukoly_a_odpovednost": ukoly_zapis})
                    st.rerun()
                    
            res_p_hist = requests.get(f"{SUPABASE_URL}/rest/v1/zapisy_porady?firma_id=eq.{moje_firma['id']}&order=datum.desc", headers=headers)
            if res_p_hist.status_code == 200 and res_p_hist.json():
                for p in res_p_hist.json():
                    st.markdown(f"<div class='card-box'><small style='color:#0ea5e9;'>Sync: {p['datum'][:10]}</small><p><b>Agenda:</b> {p['projednane_body']}</p><p><b>Action Items:</b> {p['ukoly_a_odpovednost']}</p></div>", unsafe_allow_html=True)


# ==========================================
# TAB 4: HR & KULTURA
# ==========================================
with tab_hr:
    if not moje_firma:
        st.warning("Nejprve musíte projít procesem Založení.")
    else:
        st.subheader("Tým, Hiring & Kultura (HR)")
        hr_nabor, hr_mzdy, hr_peer = st.tabs(["🤝 Talent Acquisition (Nábor)", "💸 Výplatní pásky", "⭐ 360° Kulturní Fit"])
        
        with hr_nabor:
            st.caption("U každého zaměstnance musíte uzavřít smlouvu a zkontrolovat proškolení BOZP.")
            with st.form("form_novy_zamestnanec"):
                col_z1, col_z2 = st.columns(2)
                with col_z1:
                    z_jmeno = st.text_input("Nová posila (Jméno a příjmení):")
                    z_pozice = st.text_input("Pracovní role (např. Operátor, Sales):")
                with col_z2:
                    z_smlouva = st.selectbox("Typ kontraktu:", ["Pracovní smlouva (HPP)", "Dohoda o provedení práce (DPP)", "Dohoda o pracovní činnosti (DPČ)"])
                    z_sazba = st.number_input("Hodinový rate / Tarif (M-K / hod):", min_value=10, value=50)
                
                st.markdown("**Povinné HR náležitosti:**")
                z_podpis = st.checkbox("Pracovní smlouva (DPP/DPČ) byla fyzicky/digitálně podepsána.")
                z_bozp = st.checkbox("Zaměstnanec prošel prokazatelným školením BOZP a PO.")
                
                if st.form_submit_button("Onboardovat nováčka", icon=":material/badge:"):
                    if z_jmeno and z_pozice and z_podpis and z_bozp:
                        requests.post(f"{SUPABASE_URL}/rest/v1/zamestnanci", headers=headers, json={"firma_id": moje_firma["id"], "jmeno_zamestnance": z_jmeno, "pozice": z_pozice, "typ_smlouva": z_smlouva, "hodinova_sazba": z_sazba, "odpracovane_hodiny": 0, "vyplaceno_celkem": 0, "hodnoceni_skore": 100})
                        st.success(f"Zaměstnanec {z_jmeno} byl legálně přidán do firmy!")
                        st.rerun()
                    else:
                        st.error("Pro nábor musíte vyplnit jméno, roli a potvrdit PODPIS SMLOUVY a proškolení BOZP!")

        with hr_mzdy:
            res_z = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?firma_id=eq.{moje_firma['id']}&select=*", headers=headers)
            zamestnanci_seznam = res_z.json() if res_z.status_code == 200 else []
            if zamestnanci_seznam:
                vybrany_z_jmeno = st.selectbox("Vyberte člena týmu k výplatě:", [z["jmeno_zamestnance"] for z in zamestnanci_seznam])
                vybrany_z = next((z for z in zamestnanci_seznam if z["jmeno_zamestnance"] == vybrany_z_jmeno), None)
                if vybrany_z:
                    hodiny = st.number_input("Odpracovaný čas ve Sprintu (hodiny):", min_value=1.0, value=4.0, step=0.5)
                    hruba = hodiny * vybrany_z["hodinova_sazba"]
                    dan = hruba * 0.15
                    cista = hruba - dan
                    st.markdown(f"Hrubá mzda: `{hruba:.2f} M-K` | Daň (15 %): `{dan:.2f} M-K` | **Čistá k výplatě: `{cista:.2f} M-K`**")
                    if st.button("Odeslat výplatu (Zatížit Cash-flow)", icon=":material/payments:"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/zamestnanci?id=eq.{vybrany_z['id']}", headers=headers, json={"odpracovane_hodiny": vybrany_z["odpracovane_hodiny"] + hodiny, "vyplaceno_celkem": vybrany_z["vyplaceno_celkem"] + cista})
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": "VYDAJ", "titul": f"Výplata: {vybrany_z['jmeno_zamestnance']}", "castka": cista, "auditovano": False})
                        st.success("Mzda odeslána!")
                        st.rerun()

        with hr_peer:
            st.caption("No toxic culture. 360° feedback zajišťuje, že všichni táhnou za jeden provaz.")
            if zamestnanci_seznam:
                vybrany_z_peer = st.selectbox("Vyberte kolegu k feedbacku:", [z["jmeno_zamestnance"] for z in zamestnanci_seznam], key="peer_select")
                z_peer_obj = next((z for z in zamestnanci_seznam if z["jmeno_zamestnance"] == vybrany_z_peer), None)
                if z_peer_obj:
                    bod_aktivita = st.slider("Drive & Ownership (Tah na branku v %):", min_value=10, max_value=100, value=90)
                    bod_spoluprace = st.slider("Týmový hráč (Culture Fit v %):", min_value=10, max_value=100, value=85)
                    if st.button("Odeslat 360° Feedback", icon=":material/rate_review:"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/zamestnanci?id=eq.{z_peer_obj['id']}", headers=headers, json={"hodnoceni_skore": (bod_aktivita + bod_spoluprace) / 2.0})
                        st.rerun()


# ==========================================
# TAB 5: UNIT ECONOMICS (KALKULACE)
# ==========================================
with tab_kalkulace:
    if not moje_firma:
        st.warning("Nejprve musíte projít procesem Založení.")
    else:
        st.subheader("Unit Economics & Cenotvorba produktu")
        with st.form("form_kalkulace"):
            prod_nazev = st.text_input("Core Produkt / Služba (Název):")
            p_naklady = st.number_input("Přímé náklady materiálu (M-K / ks):", min_value=0.0, value=35.0)
            rezie = st.number_input("Režijní náklady & Provoz (M-K / ks):", min_value=0.0, value=10.0)
            marze = st.number_input("Target Marže / Zisk (M-K / ks):", min_value=0.0, value=50.0)
            dan_pct = st.number_input("M-TECH Daň (Kalkulační %):", min_value=10.0, max_value=30.0, value=15.0)
            
            z_dane = p_naklady + rezie + marze
            v_dan = z_dane * (dan_pct / 100.0)
            k_cena = z_dane + v_dan
            
            st.markdown(f"**M-TECH odvod:** `{v_dan:.2f} M-K` | **Doporučená Retail Cena:** `{k_cena:.2f} M-Kreditů`")
            if st.form_submit_button("Odeslat pricing k validaci (Úřadu)", icon=":material/send:"):
                requests.post(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy", headers=headers, json={"firma_id": moje_firma["id"], "nazev_produktu": prod_nazev, "prime_naklady": p_naklady, "rezie_skoly": rezie, "mtech_dan_procento": dan_pct, "marze_zisk": marze, "konecna_cena": k_cena, "schvaleno_uradem": False})
                st.rerun()


# ==========================================
# TAB 6: CASH-FLOW & BURN RATE
# ==========================================
with tab_ucto:
    if not moje_firma:
        st.warning("Nejprve musíte projít procesem Založení.")
    else:
        st.subheader("Cash-flow deník & Runway")
        with st.form("form_transakce"):
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1: typ = st.selectbox("Typ transakce:", ["PRIJEM (Revenue)", "VYDAJ (Burn)"])
            with col_t2: titul = st.text_input("Položka / Důvod:", value="Nákup komponent")
            with col_t3: castka = st.number_input("Částka v M-Kreditech:", min_value=1.0, value=50.0)
            if st.form_submit_button("Zaevidovat do Cash-flow", icon=":material/add_circle:"):
                t_str = "PRIJEM" if "PRIJEM" in typ else "VYDAJ"
                requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": t_str, "titul": titul, "castka": castka, "auditovano": False})
                st.rerun()
                
        res_kniha = requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?firma_id=eq.{moje_firma['id']}&order=datum.desc", headers=headers)
        if res_kniha.status_code == 200 and len(res_kniha.json()) > 0:
            st.dataframe(res_kniha.json(), use_container_width=True)
