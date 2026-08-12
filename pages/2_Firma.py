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
    
    .kanban-col-header { text-align: center; font-weight: 800; padding: 12px; border-radius: 8px; margin-bottom: 15px; color: #fff; text-transform: uppercase; font-size: 14px; }
    .header-todo { background: linear-gradient(45deg, #475569, #334155); }
    .header-ip { background: linear-gradient(45deg, #f59e0b, #d97706); }
    .header-done { background: linear-gradient(45deg, #10b981, #059669); }
    .kanban-card { background-color: #0f172a; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #0ea5e9; }
    .kanban-card h5 { margin: 0 0 8px 0; color: #f8fafc; font-size: 15px; }
    .kanban-badge { display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: bold; background: rgba(14, 165, 233, 0.15); color: #38bdf8; margin-top: 8px;}
    
    .status-badge-ok { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid #10b981; padding: 10px; border-radius: 8px; font-weight: 700; text-align: center; font-size: 12px; }
    .status-badge-wait { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid #f59e0b; padding: 10px; border-radius: 8px; font-weight: 700; text-align: center; font-size: 12px; }
    .status-badge-err { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid #ef4444; padding: 10px; border-radius: 8px; font-weight: 700; text-align: center; font-size: 12px; }
    .status-badge-off { background: rgba(148, 163, 184, 0.1); color: #94a3b8; border: 1px solid #475569; padding: 10px; border-radius: 8px; font-weight: 600; text-align: center; font-size: 12px; }
    .startup-tag { display: inline-block; background: linear-gradient(90deg, #8b5cf6, #3b82f6); color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-bottom: 10px;}
    .asset-link { color: #10b981; font-weight: bold; text-decoration: none; font-size: 15px; }
    .asset-link:hover { text-decoration: underline; color: #34d399; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Startup Hub M-TECH CORE")
st.caption("Buduj. Inovuj. Škáluj. Od byrokracie přes reálný prototyp až po prodej na trhu.")

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}
except Exception:
    st.error("Chybí konfigurace databáze v Secrets!")
    st.stop()

uzivatel = st.session_state.get("uzivatel", "firma")

res_vsechny = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?select=*&order=id.desc", headers=headers)
vsechny_firmy = res_vsechny.json() if res_vsechny.status_code == 200 else []
moje_firma = next((f for f in vsechny_firmy if uzivatel.lower() in [f.get('ceo_jmeno','').lower(), f.get('cfo_jmeno','').lower(), f.get('cto_jmeno','').lower()]), None)

has_brand, has_canvas, has_report, has_hr, has_kalkulace, has_ucto = False, False, False, False, False, False

if moje_firma:
    f_id = moje_firma["id"]
    if moje_firma.get("logo_url") or moje_firma.get("web_url"): has_brand = True
    if len(requests.get(f"{SUPABASE_URL}/rest/v1/lean_canvas?firma_id=eq.{f_id}", headers=headers).json()) > 0: has_canvas = True
    if len(requests.get(f"{SUPABASE_URL}/rest/v1/firemni_reporty?firma_id=eq.{f_id}", headers=headers).json()) > 0: has_report = True
    if len(requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?firma_id=eq.{f_id}", headers=headers).json()) > 0: has_hr = True
    if len(requests.get(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy?firma_id=eq.{f_id}", headers=headers).json()) > 0: has_kalkulace = True
    if len(requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?firma_id=eq.{f_id}", headers=headers).json()) > 0: has_ucto = True

    stage = "Garážový Startup 🛠️" if moje_firma['uroven_projektu'] == 1 else ("Seed Fáze (Trh) 🌱" if moje_firma['uroven_projektu'] == 2 else "Scale-up (Pro) 🦄")
    st.markdown(f"<div class='startup-tag'>{stage}</div>", unsafe_allow_html=True)

    st.subheader("📊 Health Check (Kontrola stavu)")
    col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
    stav = moje_firma['stave_licence']
    
    with col_s1:
        if stav == "SCHVALENO": st.markdown('<div class="status-badge-ok">Legal OK 🏛️</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="status-badge-wait">Založení čeká</div>', unsafe_allow_html=True)
    with col_s2:
        if has_brand and has_canvas: st.markdown('<div class="status-badge-ok">Brand & Vize 🎨</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="status-badge-off">Chybí Brand</div>', unsafe_allow_html=True)
    with col_s3:
        if has_report: st.markdown('<div class="status-badge-ok">Reporty OK 📁</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="status-badge-off">Bez Reportů</div>', unsafe_allow_html=True)
    with col_s4:
        if has_hr: st.markdown('<div class="status-badge-ok">Tým a BOZP 👷</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="status-badge-off">Chybí Tým</div>', unsafe_allow_html=True)
    with col_s5:
        if has_kalkulace and has_ucto: st.markdown('<div class="status-badge-ok">Finance OK 💸</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="status-badge-off">Finance prázdné</div>', unsafe_allow_html=True)

    st.write("---")

tab_zalozeni, tab_brand, tab_vyvoj, tab_hr, tab_kalkulace, tab_ucto = st.tabs([
    "🏛️ 1. Založení (Legal)", 
    "🎨 2. Brand & Vize", 
    "⚡ 3. Vývoj & Reporty",
    "🦄 4. Tým & HR",
    "📈 5. Kalkulace", 
    "💸 6. Účetnictví"
])

# ==========================================
# TAB 1: ZALOŽENÍ (LEGAL) - KOMPLETNÍ FORMULÁŘE
# ==========================================
with tab_zalozeni:
    st.subheader("Registrační spis firmy – Úřední tiskopisy")
    if moje_firma:
        st.success(f"EVIDOVANÝ REGISTRAČNÍ SPIS STARTUPU: {moje_firma['nazev_firmy']} (Stav: {moje_firma['stave_licence']})")
        if st.button("Pivot / Upravit úřední údaje", icon=":material/edit:"):
            st.session_state.edit_spis = True
            st.rerun()

    if not moje_firma or st.session_state.get("edit_spis", False):
        u_notar, u_zivnost, u_financak, u_cssz, u_rejstrik = st.tabs(["📜 Notářství", "📋 JRF (Živnosti)", "⚖️ FÚ (Daně)", "🏥 ČSSZ", "🛡️ Rejstřík"])
        if "reg_data" not in st.session_state: st.session_state.reg_data = {}

        with u_notar:
            st.session_state.reg_data["nazev_firmy"] = st.text_input("1.1 Obchodní firma (včetně koncovky s.r.o.):", value=st.session_state.reg_data.get("nazev_firmy", moje_firma['nazev_firmy'] if moje_firma else ""))
            st.session_state.reg_data["skolni_kod"] = st.text_input("1.2 Licenční kód školy:", value=st.session_state.reg_data.get("skolni_kod", moje_firma['skolni_kod'] if moje_firma else "")).upper().strip()
            col_n1, col_n2 = st.columns(2)
            with col_n1:
                st.session_state.reg_data["ceo"] = st.text_input("1.3 CEO:", value=st.session_state.reg_data.get("ceo", moje_firma['ceo_jmeno'] if moje_firma else uzivatel))
                st.session_state.reg_data["cfo"] = st.text_input("1.4 CFO:", value=st.session_state.reg_data.get("cfo", moje_firma['cfo_jmeno'] if moje_firma else ""))
            with col_n2:
                st.session_state.reg_data["cto"] = st.text_input("1.5 CTO:", value=st.session_state.reg_data.get("cto", moje_firma['cto_jmeno'] if moje_firma else ""))
                st.session_state.reg_data["vklad"] = st.number_input("1.6 Základní kapitál (M-K):", min_value=10, value=int(st.session_state.reg_data.get("vklad", 100)))

        with u_zivnost:
            col_j1, col_j2 = st.columns(2)
            with col_j1:
                st.session_state.reg_data["divize"] = st.selectbox("2.1 Divize:", ["Hardware & Strojírenství", "Energy & Elektro", "Software & IT", "Služby & Marketing"])
                st.session_state.reg_data["druh_zivnosti"] = st.selectbox("2.2 Druh živnosti:", ["Volná", "Řemeslná", "Vázaná"])
            with col_j2:
                st.session_state.reg_data["predmet"] = st.text_input("2.3 Předmět podnikání:", value=st.session_state.reg_data.get("predmet", ""))
                st.session_state.reg_data["bozp_garant"] = st.text_input("2.4 Garant BOZP:", value=st.session_state.reg_data.get("bozp_garant", uzivatel))
            st.session_state.reg_data["zamer"] = st.text_area("2.5 Záměr pro JRF:", value=st.session_state.reg_data.get("zamer", ""))

        with u_financak:
            st.session_state.reg_data["typ_dani"] = st.multiselect("3.1 Registrace k daním:", ["DPPO", "Daň ze závislé činnosti", "M-TECH Daň"], default=["DPPO", "Daň ze závislé činnosti", "M-TECH Daň"])
            st.session_state.reg_data["dan_souhlas"] = st.checkbox("3.2 Zavazujeme se k odvodu M-TECH daně z profitu.", value=st.session_state.reg_data.get("dan_souhlas", True))

        with u_cssz:
            st.session_state.reg_data["seznam_zamestnancu"] = st.text_area("4.1 Core Team Members:", value=st.session_state.reg_data.get("seznam_zamestnancu", f"{uzivatel}, CFO, CTO"))

        with u_rejstrik:
            st.session_state.reg_data["bozp_souhlas"] = st.checkbox("5.1 Prohlašujeme, že máme hotový bezpečnostní onboarding (BOZP).", value=st.session_state.reg_data.get("bozp_souhlas", True))
            st.session_state.reg_data["kodex_souhlas"] = st.checkbox("5.2 Přijímáme Etický kodex.", value=st.session_state.reg_data.get("kodex_souhlas", True))
            
            if st.button("🚀 ODESLAT REGISTRAČNÍ SPIS ÚŘADU", icon=":material/send:"):
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
# TAB 2: BRAND & VIZE (AKTIVA FIRMY)
# ==========================================
with tab_brand:
    if not moje_firma:
        st.warning("Nejprve založte firmu (Tab 1).")
    else:
        tab_aktiva, tab_lean = st.tabs(["🎨 Vizuální Identita (Odkazy)", "💡 Lean Canvas"])
        
        with tab_aktiva:
            st.markdown("### Firemní aktiva (Digital Assets)")
            st.caption("Firma bez tváře neexistuje. Vytvořte reálné logo (např. v Canvě), firemní web (např. Webnode/Wix) a prezentační leták. Sem vložte pouze veřejné odkazy na tyto výstupy.")
            with st.form("form_brand"):
                b_logo = st.text_input("🔗 Odkaz na LOGO (Canva, Google Drive):", value=moje_firma.get('logo_url','') or "")
                b_web = st.text_input("🔗 Odkaz na WEBOVÉ STRÁNKY:", value=moje_firma.get('web_url','') or "")
                b_promo = st.text_input("🔗 Odkaz na PROMO LETÁK / PITCH DECK:", value=moje_firma.get('promo_url','') or "")
                if st.form_submit_button("Aktualizovat Brand Kit", icon=":material/save:"):
                    requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{moje_firma['id']}", headers=headers, json={"logo_url": b_logo, "web_url": b_web, "promo_url": b_promo})
                    st.success("Aktiva uložena!")
                    st.rerun()
                    
            if moje_firma.get("logo_url") or moje_firma.get("web_url"):
                st.markdown("---")
                st.markdown("#### Vaše odevzdaná identita:")
                if moje_firma.get("logo_url"): st.markdown(f"🖼️ <a href='{moje_firma['logo_url']}' class='asset-link' target='_blank'>Zobrazit firemní logo</a>", unsafe_allow_html=True)
                if moje_firma.get("web_url"): st.markdown(f"🌐 <a href='{moje_firma['web_url']}' class='asset-link' target='_blank'>Přejít na firemní web</a>", unsafe_allow_html=True)
                if moje_firma.get("promo_url"): st.markdown(f"📄 <a href='{moje_firma['promo_url']}' class='asset-link' target='_blank'>Zobrazit leták / prezentaci</a>", unsafe_allow_html=True)

        with tab_lean:
            res_c = requests.get(f"{SUPABASE_URL}/rest/v1/lean_canvas?firma_id=eq.{moje_firma['id']}", headers=headers)
            exist_canvas = res_c.json()[0] if res_c.status_code == 200 and res_c.json() else None
            
            with st.form("form_canvas"):
                col_c1, col_c2, col_c3, col_c4 = st.columns(4)
                with col_c1: prob = st.text_area("1. Problém trhu", value=exist_canvas.get("problem","") if exist_canvas else "", height=120)
                with col_c2: sol = st.text_area("2. Naše Řešení", value=exist_canvas.get("reseni","") if exist_canvas else "", height=120)
                with col_c3: val = st.text_area("3. Unikátní hodnota", value=exist_canvas.get("unikatni_hodnota","") if exist_canvas else "", height=120)
                with col_c4: target = st.text_area("4. Cílová skupina", value=exist_canvas.get("cilova_skupina","") if exist_canvas else "", height=120)
                col_c5, col_c6 = st.columns(2)
                with col_c5: costs = st.text_area("5. Náklady", value=exist_canvas.get("nakladova_struktura","") if exist_canvas else "")
                with col_c6: rev = st.text_area("6. Příjmy", value=exist_canvas.get("prijmove_toky","") if exist_canvas else "")
                if st.form_submit_button("Uložit Lean Canvas"):
                    c_payload = {"firma_id": moje_firma["id"], "problem": prob, "reseni": sol, "cilova_skupina": target, "unikatni_hodnota": val, "nakladova_struktura": costs, "prijmove_toky": rev}
                    if exist_canvas: requests.patch(f"{SUPABASE_URL}/rest/v1/lean_canvas?id=eq.{exist_canvas['id']}", headers=headers, json=c_payload)
                    else: requests.post(f"{SUPABASE_URL}/rest/v1/lean_canvas", headers=headers, json=c_payload)
                    st.rerun()

# ==========================================
# TAB 3: VÝVOJ & REPORTY
# ==========================================
with tab_vyvoj:
    if not moje_firma:
        st.warning("Nejprve založte firmu.")
    else:
        st.subheader("Vývoj produktu, Plánování a Odevzdávání Reportů")
        ag_kanban, ag_porady, ag_reporty = st.tabs(["📋 Agilní Kanban", "👥 Zápisy z porad", "📁 Odevzdávárna Reportů"])
        
        with ag_kanban:
            st.caption("Neodklikávejte úkoly naprázdno. Zde řídíte výrobu prototypu nebo stavbu služby.")
            with st.form("form_novy_ukol"):
                col_u1, col_u2, col_u3 = st.columns(3)
                with col_u1: u_nazev = st.text_input("Nový úkol:")
                with col_u2: u_osoba = st.text_input("Zodpovídá:", value=uzivatel)
                with col_u3: u_termin = st.date_input("Deadline:", value=datetime.date.today() + datetime.timedelta(days=7))
                if st.form_submit_button("Přidat do Backlogu", icon=":material/add_task:"):
                    requests.post(f"{SUPABASE_URL}/rest/v1/projektove_ukoly", headers=headers, json={"firma_id": moje_firma["id"], "nazev_ukolu": u_nazev, "zodpovedna_osoba": u_osoba, "termin": str(u_termin), "stav": "TO_DO"})
                    st.rerun()
            
            ukoly = requests.get(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?firma_id=eq.{moje_firma['id']}&order=datum_zadani.desc", headers=headers).json()
            col_todo, col_ip, col_done = st.columns(3)
            with col_todo:
                st.markdown("<div class='kanban-col-header header-todo'>📌 K VYŘEŠENÍ</div>", unsafe_allow_html=True)
                for u in [x for x in ukoly if x['stav'] == 'TO_DO']:
                    st.markdown(f"<div class='kanban-card'><h5>{u['nazev_ukolu']}</h5><p><b>{u['zodpovedna_osoba']}</b> ({u['termin']})</p></div>", unsafe_allow_html=True)
                    if st.button("Do procesu", key=f"btn_ip_{u['id']}"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?id=eq.{u['id']}", headers=headers, json={"stav": "IN_PROGRESS"})
                        st.rerun()
            with col_ip:
                st.markdown("<div class='kanban-col-header header-ip'>⏳ V PROCESU</div>", unsafe_allow_html=True)
                for u in [x for x in ukoly if x['stav'] == 'IN_PROGRESS']:
                    st.markdown(f"<div class='kanban-card' style='border-color:#f59e0b;'><h5>{u['nazev_ukolu']}</h5><p><b>{u['zodpovedna_osoba']}</b></p></div>", unsafe_allow_html=True)
                    if st.button("Dokončit", key=f"btn_done_{u['id']}"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?id=eq.{u['id']}", headers=headers, json={"stav": "DONE"})
                        st.rerun()
            with col_done:
                st.markdown("<div class='kanban-col-header header-done'>✅ HOTOVO</div>", unsafe_allow_html=True)
                for u in [x for x in ukoly if x['stav'] == 'DONE']:
                    st.markdown(f"<div class='kanban-card' style='border-color:#10b981;'><h5>{u['nazev_ukolu']}</h5><p><b>{u['zodpovedna_osoba']}</b></p></div>", unsafe_allow_html=True)
                    if st.button("Smazat", key=f"btn_del_{u['id']}"):
                        requests.delete(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?id=eq.{u['id']}", headers=headers)
                        st.rerun()

        with ag_porady:
            st.caption("Pravidelné syncy managementu a členů týmu.")
            with st.form("form_porada"):
                projednano = st.text_area("Projednaná Agenda:")
                ukoly_zapis = st.text_area("Akční kroky (Kdo, co, do kdy):")
                if st.form_submit_button("Uložit Log z porady", icon=":material/post_add:"):
                    requests.post(f"{SUPABASE_URL}/rest/v1/zapisy_porady", headers=headers, json={"firma_id": moje_firma["id"], "projednane_body": projednano, "ukoly_a_odpovednost": ukoly_zapis})
                    st.rerun()
            res_p_hist = requests.get(f"{SUPABASE_URL}/rest/v1/zapisy_porady?firma_id=eq.{moje_firma['id']}&order=datum.desc", headers=headers)
            if res_p_hist.status_code == 200 and res_p_hist.json():
                for p in res_p_hist.json():
                    st.markdown(f"<div class='card-box'><small style='color:#0ea5e9;'>Porada: {p['datum'][:10]}</small><p><b>Agenda:</b> {p['projednane_body']}</p><p><b>Úkoly:</b> {p['ukoly_a_odpovednost']}</p></div>", unsafe_allow_html=True)

        with ag_reporty:
            st.markdown("### 📁 Odevzdávání povinných zpráv a reportů")
            st.caption("Zde odevzdáváte vyučujícímu (Kontrolnímu úřadu) měsíční zprávy, fotky prototypů nebo závěrečné prezentace.")
            with st.form("form_report"):
                r_typ = st.selectbox("Typ odevzdávaného dokumentu:", ["Měsíční report (Trakce)", "Fotodokumentace / Video prototypu", "Zpráva o stavu vývoje (Roadmapa)", "Závěrečná prezentace / Obhajoba"])
                r_nazev = st.text_input("Název dokumentu:")
                r_odkaz = st.text_input("🔗 Odkaz na soubor (Google Drive, OneDrive, YouTube, PDF link):")
                if st.form_submit_button("Odevzdat report úřadu", icon=":material/cloud_upload:"):
                    if r_nazev and r_odkaz:
                        requests.post(f"{SUPABASE_URL}/rest/v1/firemni_reporty", headers=headers, json={"firma_id": moje_firma["id"], "typ_reportu": r_typ, "nazev_reportu": r_nazev, "odkaz_soubor": r_odkaz})
                        st.success("Report byl úspěšně odevzdán!")
                        st.rerun()
                    else:
                        st.warning("Musíte vyplnit název a vložit platný odkaz na soubor.")
            
            res_reporty = requests.get(f"{SUPABASE_URL}/rest/v1/firemni_reporty?firma_id=eq.{moje_firma['id']}&order=datum_odevzdani.desc", headers=headers)
            if res_reporty.status_code == 200 and res_reporty.json():
                st.markdown("#### Historie odevzdaných dokumentů:")
                for r in res_reporty.json():
                    st.markdown(f"📄 **{r['typ_reportu']}:** {r['nazev_reportu']} ➔ <a href='{r['odkaz_soubor']}' target='_blank' class='asset-link'>Otevřít dokument</a> <small>({r['datum_odevzdani'][:10]})</small>", unsafe_allow_html=True)


# ==========================================
# TAB 4: HR & TÝM
# ==========================================
with tab_hr:
    if not moje_firma:
        st.warning("Nejprve musíte projít procesem Založení.")
    else:
        st.subheader("Personalistika, Mzdy a BOZP")
        hr_nabor, hr_mzdy, hr_peer = st.tabs(["🤝 Nábor & Pracovní smlouvy", "💸 Výplatní pásky", "⭐ 360° Kulturní Fit"])
        
        with hr_nabor:
            st.caption("Při náboru MUSÍTE potvrdit uzavření smlouvy a proškolení BOZP.")
            with st.form("form_novy_zamestnanec"):
                col_z1, col_z2 = st.columns(2)
                with col_z1:
                    z_jmeno = st.text_input("Nová posila (Jméno):")
                    z_pozice = st.text_input("Role (např. Dev, Operátor):")
                with col_z2:
                    z_smlouva = st.selectbox("Typ kontraktu:", ["Pracovní smlouva (HPP)", "Dohoda o provedení práce (DPP)", "Dohoda o pracovní činnosti (DPČ)"])
                    z_sazba = st.number_input("Hodinový rate (M-K / hod):", min_value=10, value=50)
                z_podpis = st.checkbox("Smlouva byla fyzicky/digitálně podepsána oběma stranami.")
                z_bozp = st.checkbox("Zaměstnanec prošel prokazatelným školením BOZP a PO.")
                if st.form_submit_button("Onboardovat nováčka", icon=":material/badge:"):
                    if z_jmeno and z_pozice and z_podpis and z_bozp:
                        requests.post(f"{SUPABASE_URL}/rest/v1/zamestnanci", headers=headers, json={"firma_id": moje_firma["id"], "jmeno_zamestnance": z_jmeno, "pozice": z_pozice, "typ_smlouva": z_smlouva, "hodinova_sazba": z_sazba, "odpracovane_hodiny": 0, "vyplaceno_celkem": 0, "hodnoceni_skore": 100})
                        st.rerun()
                    else:
                        st.error("Pro nábor musíte vyplnit jméno, roli a potvrdit PODPIS a BOZP!")

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
            if zamestnanci_seznam:
                vybrany_z_peer = st.selectbox("Vyberte kolegu k feedbacku:", [z["jmeno_zamestnance"] for z in zamestnanci_seznam], key="peer_select")
                z_peer_obj = next((z for z in zamestnanci_seznam if z["jmeno_zamestnance"] == vybrany_z_peer), None)
                if z_peer_obj:
                    bod_aktivita = st.slider("Tah na branku v %:", min_value=10, max_value=100, value=90)
                    bod_spoluprace = st.slider("Culture Fit v %:", min_value=10, max_value=100, value=85)
                    if st.button("Odeslat 360° Feedback", icon=":material/rate_review:"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/zamestnanci?id=eq.{z_peer_obj['id']}", headers=headers, json={"hodnoceni_skore": (bod_aktivita + bod_spoluprace) / 2.0})
                        st.rerun()

# ==========================================
# TAB 5 & 6: KALKULACE A ÚČETNICTVÍ
# ==========================================
with tab_kalkulace:
    if moje_firma:
        st.subheader("Unit Economics & Cenotvorba")
        with st.form("form_kalkulace"):
            prod_nazev = st.text_input("Core Produkt / Služba (Název):")
            p_naklady = st.number_input("Přímé náklady materiálu (M-K / ks):", min_value=0.0, value=35.0)
            rezie = st.number_input("Režijní náklady & Provoz (M-K / ks):", min_value=0.0, value=10.0)
            marze = st.number_input("Target Marže / Zisk (M-K / ks):", min_value=0.0, value=50.0)
            dan_pct = st.number_input("M-TECH Daň (Kalkulační %):", min_value=10.0, max_value=30.0, value=15.0)
            
            z_dane = p_naklady + rezie + marze
            v_dan = z_dane * (dan_pct / 100.0)
            k_cena = z_dane + v_dan
            
            st.markdown(f"**M-TECH odvod:** `{v_dan:.2f} M-K` | **Retail Cena:** `{k_cena:.2f} M-Kreditů`")
            if st.form_submit_button("Odeslat pricing k validaci", icon=":material/send:"):
                requests.post(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy", headers=headers, json={"firma_id": moje_firma["id"], "nazev_produktu": prod_nazev, "prime_naklady": p_naklady, "rezie_skoly": rezie, "mtech_dan_procento": dan_pct, "marze_zisk": marze, "konecna_cena": k_cena, "schvaleno_uradem": False})
                st.rerun()

with tab_ucto:
    if moje_firma:
        st.subheader("Cash-flow deník & Runway")
        with st.form("form_transakce"):
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1: typ = st.selectbox("Typ transakce:", ["PRIJEM", "VYDAJ"])
            with col_t2: titul = st.text_input("Důvod:", value="Nákup komponent")
            with col_t3: castka = st.number_input("Částka v M-Kreditech:", min_value=1.0, value=50.0)
            if st.form_submit_button("Zaevidovat do Cash-flow", icon=":material/add_circle:"):
                t_str = "PRIJEM" if "PRIJEM" in typ else "VYDAJ"
                requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": t_str, "titul": titul, "castka": castka, "auditovano": False})
                st.rerun()
                
        res_kniha = requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?firma_id=eq.{moje_firma['id']}&order=datum.desc", headers=headers)
        if res_kniha.status_code == 200 and len(res_kniha.json()) > 0:
            st.dataframe(res_kniha.json(), use_container_width=True)
