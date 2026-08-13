import streamlit as st
import requests
import datetime

st.set_page_config(page_title="Startup Hub & Dashboard", page_icon=":material/insights:", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3, h4 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #00B4D8; width: 100%; font-weight: 600; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0, 180, 216, 0.4); border-color: #00B4D8; }
    .card-box { background-color: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 15px; }
    .status-badge-ok { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid #10b981; padding: 10px; border-radius: 8px; font-weight: 700; text-align: center; font-size: 12px; }
    .status-badge-wait { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid #f59e0b; padding: 10px; border-radius: 8px; font-weight: 700; text-align: center; font-size: 12px; }
    .asset-link { color: #00B4D8; font-weight: bold; text-decoration: none; font-size: 15px; }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.get("prihlasen"):
    st.warning("Pro zobrazení Firemního Dashboardu se musíte přihlásit na hlavní obrazovce.")
    st.stop()

st.title("🚀 Startup Hub & Dashboard M-TECH CORE")

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}
except Exception:
    st.error("Chybí konfigurace databáze v Secrets!")
    st.stop()

uzivatel = st.session_state.get("uzivatel")

res_vsechny = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?select=*&order=id.desc", headers=headers)
vsechny_firmy = res_vsechny.json() if res_vsechny.status_code == 200 else []
moje_firma = next((f for f in vsechny_firmy if uzivatel.lower() in [f.get('ceo_jmeno','').lower(), f.get('cfo_jmeno','').lower(), f.get('cto_jmeno','').lower()]), None)

if moje_firma:
    f_id = moje_firma["id"]
    st.subheader(f"Startup: {moje_firma['nazev_firmy']} (ID spisu: #{f_id})")
    col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
    stav = moje_firma['stave_licence']
    
    with col_s1:
        if stav == "SCHVALENO": st.markdown('<div class="status-badge-ok">Zápis v rejstříku OK 🏛️</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="status-badge-wait">Založení čeká ⏳</div>', unsafe_allow_html=True)
    with col_s2: st.markdown('<div class="status-badge-ok">Brand & Vize 🎨</div>', unsafe_allow_html=True)
    with col_s3: st.markdown('<div class="status-badge-ok">Agilní Vývoj ⚡</div>', unsafe_allow_html=True)
    with col_s4: st.markdown('<div class="status-badge-ok">HR & Úřady 👷</div>', unsafe_allow_html=True)
    with col_s5: st.markdown('<div class="status-badge-ok">Finance & Pricing 💸</div>', unsafe_allow_html=True)

    st.write("---")

tab_zalozeni, tab_brand, tab_vyvoj, tab_hr, tab_kalkulace, tab_ucto = st.tabs([
    "📜 1. Zakladatelský Spis (Legal)", 
    "🎨 2. Brand Kit & Lean Canvas", 
    "⚡ 3. Agilní Vývoj & Reporty",
    "👷 4. Tým & HR (Onboarding na Úřady)",
    "📈 5. Cenotvorba pro E-shop", 
    "💸 6. Cash-flow a Banka"
])

with tab_zalozeni:
    st.subheader("Registrační spis zakládané entity")
    st.caption("Kompletní zakladatelská dokumentace pro notáře, živnostenský úřad, finanční úřad a obchodní rejstřík.")
    
    if moje_firma:
        st.success(f"Registrační spis evidován. Stav zápisu v rejstříku: **{moje_firma['stave_licence']}**")
        if moje_firma.get("duvod_zamitnuti"):
            st.error(f"Připomínky Kontrolního úřadu k opravení: {moje_firma['duvod_zamitnuti']}")
        
        if st.button("✏️ Editovat zakladatelskou dokumentaci (Pivot)"):
            st.session_state.edit_spis = True
            st.rerun()

    if not moje_firma or st.session_state.get("edit_spis", False):
        u_notar, u_zivnost, u_financak, u_cssz, u_rejstrik = st.tabs([
            "📜 Zakladatelská listina", 
            "📋 Živnostenský úřad (JRF)", 
            "⚖️ Finanční úřad", 
            "🏥 ČSSZ & Pojišťovny", 
            "🛡️ Obchodní Rejstřík"
        ])
        
        if "reg_data" not in st.session_state: st.session_state.reg_data = {}

        # --- 1. NOTÁŘSTVÍ ---
        with u_notar:
            st.markdown("#### Zakladatelská listina / Společenská smlouva")
            st.session_state.reg_data["nazev_firmy"] = st.text_input("Obchodní firma (Název startupu):", value=st.session_state.reg_data.get("nazev_firmy", moje_firma['nazev_firmy'] if moje_firma else ""))
            st.session_state.reg_data["skolni_kod"] = st.text_input("Licenční kód Akcelerátoru (Školy):", value=st.session_state.reg_data.get("skolni_kod", moje_firma['skolni_kod'] if moje_firma else "")).upper().strip()
            
            st.markdown("##### Statutární orgán a Vedení (Jednatelé)")
            col_n1, col_n2, col_n3 = st.columns(3)
            with col_n1: st.session_state.reg_data["ceo"] = st.text_input("Jednatel 1 (CEO):", value=st.session_state.reg_data.get("ceo", moje_firma['ceo_jmeno'] if moje_firma else uzivatel))
            with col_n2: st.session_state.reg_data["cfo"] = st.text_input("Jednatel 2 (CFO):", value=st.session_state.reg_data.get("cfo", moje_firma['cfo_jmeno'] if moje_firma else ""))
            with col_n3: st.session_state.reg_data["cto"] = st.text_input("Jednatel 3 (CTO):", value=st.session_state.reg_data.get("cto", moje_firma['cto_jmeno'] if moje_firma else ""))
            
            st.session_state.reg_data["jednani"] = st.selectbox("Způsob jednání za společnost:", ["Každý jednatel zastupuje společnost samostatně", "Společně alespoň dva jednatelé", "Všichni jednatelé společně"])

            st.markdown("##### Kapitálová struktura (Cap Table)")
            col_k1, col_k2 = st.columns(2)
            with col_k1:
                st.session_state.reg_data["vklad"] = st.number_input("Základní kapitál (M-Kreditů):", min_value=10, value=int(st.session_state.reg_data.get("vklad", 100)))
                st.session_state.reg_data["spravce_vkladu"] = st.text_input("Správce vkladu (Osoba):", value=uzivatel)
            with col_k2:
                st.session_state.reg_data["podily_popis"] = st.text_area("Rozdělení obchodních podílů (%):", value="CEO: 40 %, CFO: 30 %, CTO: 30 %")

        # --- 2. ŽIVNOSTENSKÝ ÚŘAD (ROZŠÍŘENÉ JRF) ---
        with u_zivnost:
            st.markdown("#### Jednotný registrační formulář (JRF) – Živnostenský odbor")
            
            st.session_state.reg_data["druh_zivnosti"] = st.radio(
                "Druh ohlašované živnosti:", 
                ["Volná (Nevyžaduje odbornou způsobilost)", "Řemeslná (Vyžaduje výuční list/garanta)", "Vázaná (Vyžaduje odbornou certifikaci)"],
                horizontal=True
            )
            
            col_j1, col_j2 = st.columns(2)
            
            with col_j1:
                if "Volná" in st.session_state.reg_data["druh_zivnosti"]:
                    st.session_state.reg_data["zivnost_detail"] = st.multiselect(
                        "Obory voľné živnosti (čísla oborů dle ŽZ):",
                        [
                            "56. Poskytování softwaru, poradenství v oblasti IT a výpočetní techniky",
                            "52. Výroba a vývoj elektronických součástek a přístrojů",
                            "47. Zprostředkování obchodu a služeb",
                            "48. Velkoobchod a maloobchod (E-shop)",
                            "62. Reklamní činnost, marketing, media a výlep plakátů",
                            "63. Návrhářská, designérská, aranžérská činnost a modelování (3D)",
                            "66. Fotografické a audiovizuální služby",
                            "70. Mimoškolní výchova a vzdělávání, pořádání kurzů a workshopů",
                            "31. Výroba strojů a zařízení a 3D aditivní výroba",
                            "80. Výroba, obchod a služby jinde nezařazené"
                        ],
                        default=["56. Poskytování softwaru, poradenství v oblasti IT a výpočetní techniky", "48. Velkoobchod a maloobchod (E-shop)"]
                    )
                elif "Řemeslná" in st.session_state.reg_data["druh_zivnosti"]:
                    st.session_state.reg_data["zivnost_detail"] = st.selectbox(
                        "Obor řemeslné živnosti:",
                        [
                            "Obrábění kovů a zámečnictví",
                            "Výroba, instalace a opravy elektrických strojů a přístrojů",
                            "Truhlářství a stolářství",
                            "Pekařství a cukrářství",
                            "Opravy silničních vozidel"
                        ]
                    )
                else:
                    st.session_state.reg_data["zivnost_detail"] = st.selectbox(
                        "Obor vázané živnosti:",
                        [
                            "Projektová činnost ve výstavbě a konstrukci",
                            "Nákup, prodej a skladování nebezpečných chemických látek",
                            "Provozování autoškoly",
                            "Nákup a prodej pyrotechnických výrobků"
                        ]
                    )
                
                st.session_state.reg_data["predmet"] = st.text_area(
                    "Předmět podnikání (Přesné vymezení produktů/služeb):", 
                    value="Vývoj inovačních softwarových a hardwarových řešení, prototypování a jejich B2B/B2C prodej."
                )

            with col_j2:
                st.session_state.reg_data["bozp_garant"] = st.text_input("Odborný zástupce / Garant živnosti:", value=uzivatel, help="Osoba, která splňuje podmínky odborné způsobilosti a odpovídá za provoz.")
                st.session_state.reg_data["garant_doklad"] = st.text_input("Doklad o odborné způsobilosti garanta:", value="M-TECH Certifikát odbornosti / Výuční list č. 2026/01")
                st.session_state.reg_data["sidlo"] = st.text_input("Adresa sídla startupu:", value="M-TECH Akcelerační centrum, Učebna 102")
                st.session_state.reg_data["provozovna"] = st.text_input("Provozovna (Adresa + IČP):", value="Provozovna 01 – Laboratoř 3D tisku a prototypování (IČP: 1002345)")

        # --- 3. FINANČNÍ ÚŘAD ---
        with u_financak:
            st.markdown("#### Registrace k daňovým povinnostem")
            st.session_state.reg_data["typ_dani"] = st.multiselect("Přihláška k registraci daní:", ["Daň z příjmů právnických osob (DPPO)", "Daň ze závislé činnosti (Zaměstnanci)", "M-TECH Ekologická a vývojová daň"], default=["Daň z příjmů právnických osob (DPPO)", "Daň ze závislé činnosti (Zaměstnanci)", "M-TECH Ekologická a vývojová daň"])
            st.session_state.reg_data["zdanovaci_obdobi"] = st.selectbox("Zdaňovací období:", ["Měsíční (Sprint)", "Čtvrtletní", "Projektové"])

        # --- 4. ČSSZ ---
        with u_cssz:
            st.markdown("#### Registrace zaměstnavatele u OSSZ a Zdravotní pojišťovny")
            st.info("Zde registrujete firmu jako plátce pojistného za své budoucí zaměstnance.")
            st.session_state.reg_data["pocet_zakladatelu"] = st.number_input("Počet pojištěných zakladatelů/pracovníků:", min_value=1, value=3)
            st.session_state.reg_data["bozp_prohlaseni"] = st.checkbox("Prohlašujeme, že pracoviště splňuje bezpečnostní standardy BOZP.", value=True)

        # --- 5. OBCHODNÍ REJSTŘÍK ---
        with u_rejstrik:
            st.markdown("#### Návrh na zápis do Obchodního Rejstříku")
            st.session_state.reg_data["ubo"] = st.text_input("Skuteční majitelé (UBO - Ultimate Beneficial Owners):", value=f"{uzivatel} a spoluzakladatelé")
            st.session_state.reg_data["kodex_souhlas"] = st.checkbox("Akceptujeme Etický a startupový kodex akcelerátoru M-TECH CORE.", value=True)
            
            st.write("---")
            if st.button("🚀 ODESLAT ZAKLADATELSKÝ SPIS ÚŘADU K AUDITU", icon=":material/send:"):
                d = st.session_state.reg_data
                if d.get("nazev_firmy") and d.get("skolni_kod") and d.get("cfo") and d.get("cto"):
                    res_lic = requests.get(f"{SUPABASE_URL}/rest/v1/licencovane_skoly?licencni_kod=eq.{d.get('skolni_kod')}", headers=headers)
                    u_num = res_lic.json()[0].get("uroven_projektu", 2) if (res_lic.status_code == 200 and res_lic.json()) else 2
                    
                    zivnost_info = d.get('zivnost_detail')
                    if isinstance(zivnost_info, list):
                        zivnost_str = ", ".join(zivnost_info)
                    else:
                        zivnost_str = str(zivnost_info)
                        
                    zamer_str = f"[{d.get('druh_zivnosti')} | Obory: {zivnost_str}] {d.get('predmet')} (Garant: {d.get('bozp_garant')} - {d.get('garant_doklad')}, Sídlo/Provozovna: {d.get('provozovna')})"
                    
                    payload = {
                        "nazev_firmy": d.get("nazev_firmy"), 
                        "skolni_kod": d.get("skolni_kod"), 
                        "uroven_projektu": u_num,
                        "ceo_jmeno": d.get("ceo"), 
                        "cfo_jmeno": d.get("cfo"), 
                        "cto_jmeno": d.get("cto"),
                        "podnikatelsky_zamer": zamer_str,
                        "pocatecni_kapital": d.get("vklad", 100) * 3, 
                        "stave_licence": "CEKA_NA_SCHVALENI",
                        "duvod_zamitnuti": ""
                    }
                    if moje_firma: requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{moje_firma['id']}", headers=headers, json=payload)
                    else: requests.post(f"{SUPABASE_URL}/rest/v1/firmy", headers=headers, json=payload)
                    st.session_state.edit_spis = False
                    st.success("Zakladatelský spis byl zkompletován a odeslán Kontrolnímu úřadu!")
                    st.rerun()
                else:
                    st.error("Chybí povinné údaje! Vyplňte název firmy, kód školy a všechny 3 jednatele.")

# ==========================================
# TAB 2-6 (ZŮSTÁVAJÍ V PLNÉ KRÁSE)
# ==========================================
with tab_brand:
    if not moje_firma:
        st.warning("Nejprve založte firmu (Záložka 1).")
    else:
        tab_aktiva, tab_lean = st.tabs(["Vizuální Identita (Assets)", "Lean Canvas (Strategie)"])
        with tab_aktiva:
            with st.form("form_brand"):
                b_logo = st.text_input("🔗 Odkaz na LOGO:", value=moje_firma.get('logo_url','') or "")
                b_web = st.text_input("🔗 Odkaz na WEBOVÉ STRÁNKY:", value=moje_firma.get('web_url','') or "")
                b_promo = st.text_input("🔗 Odkaz na PITCH DECK:", value=moje_firma.get('promo_url','') or "")
                if st.form_submit_button("Uložit Brand Kit", icon=":material/save:"):
                    requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{moje_firma['id']}", headers=headers, json={"logo_url": b_logo, "web_url": b_web, "promo_url": b_promo})
                    st.success("Aktiva uložena!")
                    st.rerun()
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
                if st.form_submit_button("Uložit Lean Canvas", icon=":material/save:"):
                    c_payload = {"firma_id": moje_firma["id"], "problem": prob, "reseni": sol, "cilova_skupina": target, "unikatni_hodnota": val, "nakladova_struktura": costs, "prijmove_toky": rev}
                    if exist_canvas: requests.patch(f"{SUPABASE_URL}/rest/v1/lean_canvas?id=eq.{exist_canvas['id']}", headers=headers, json=c_payload)
                    else: requests.post(f"{SUPABASE_URL}/rest/v1/lean_canvas", headers=headers, json=c_payload)
                    st.rerun()

with tab_vyvoj:
    if not moje_firma:
        st.warning("Nejprve založte firmu.")
    else:
        ag_kanban, ag_porady, ag_reporty = st.tabs(["Agilní Kanban (Sprint)", "Zápisy ze Stand-upů", "Odevzdávárna Reportů"])
        with ag_kanban:
            with st.form("form_novy_ukol"):
                col_u1, col_u2, col_u3 = st.columns(3)
                with col_u1: u_nazev = st.text_input("Nový úkol:")
                with col_u2: u_osoba = st.text_input("Assignee:", value=uzivatel)
                with col_u3: u_termin = st.date_input("Deadline Sprintu:", value=datetime.date.today() + datetime.timedelta(days=7))
                if st.form_submit_button("Přidat do Backlogu", icon=":material/add_task:"):
                    requests.post(f"{SUPABASE_URL}/rest/v1/projektove_ukoly", headers=headers, json={"firma_id": moje_firma["id"], "nazev_ukolu": u_nazev, "zodpovedna_osoba": u_osoba, "termin": str(u_termin), "stav": "TO_DO"})
                    st.rerun()
            ukoly = requests.get(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?firma_id=eq.{moje_firma['id']}&order=datum_zadani.desc", headers=headers).json()
            col_todo, col_ip, col_done = st.columns(3)
            with col_todo:
                st.markdown("<div class='kanban-col-header header-todo'>BACKLOG</div>", unsafe_allow_html=True)
                for u in [x for x in ukoly if x['stav'] == 'TO_DO']:
                    st.markdown(f"<div class='kanban-card'><h5>{u['nazev_ukolu']}</h5><p><b>{u['zodpovedna_osoba']}</b> ({u['termin']})</p></div>", unsafe_allow_html=True)
                    if st.button("▶️ Do procesu", key=f"btn_ip_{u['id']}"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?id=eq.{u['id']}", headers=headers, json={"stav": "IN_PROGRESS"})
                        st.rerun()
            with col_ip:
                st.markdown("<div class='kanban-col-header header-ip'>IN PROGRESS</div>", unsafe_allow_html=True)
                for u in [x for x in ukoly if x['stav'] == 'IN_PROGRESS']:
                    st.markdown(f"<div class='kanban-card' style='border-color:#f59e0b;'><h5>{u['nazev_ukolu']}</h5><p><b>{u['zodpovedna_osoba']}</b></p></div>", unsafe_allow_html=True)
                    if st.button("✅ Dokončit", key=f"btn_done_{u['id']}"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?id=eq.{u['id']}", headers=headers, json={"stav": "DONE"})
                        st.rerun()
            with col_done:
                st.markdown("<div class='kanban-col-header header-done'>DONE</div>", unsafe_allow_html=True)
                for u in [x for x in ukoly if x['stav'] == 'DONE']:
                    st.markdown(f"<div class='kanban-card' style='border-color:#10b981;'><h5>{u['nazev_ukolu']}</h5><p><b>{u['zodpovedna_osoba']}</b></p></div>", unsafe_allow_html=True)
                    if st.button("🗑️ Smazat", key=f"btn_del_{u['id']}"):
                        requests.delete(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?id=eq.{u['id']}", headers=headers)
                        st.rerun()
        with ag_porady:
            with st.form("form_porada"):
                projednano = st.text_area("Stand-up Log:")
                ukoly_zapis = st.text_area("Akční kroky:")
                if st.form_submit_button("Uložit Zápis", icon=":material/post_add:"):
                    requests.post(f"{SUPABASE_URL}/rest/v1/zapisy_porady", headers=headers, json={"firma_id": moje_firma["id"], "projednane_body": projednano, "ukoly_a_odpovednost": ukoly_zapis})
                    st.rerun()
        with ag_reporty:
            with st.form("form_report"):
                r_typ = st.selectbox("Typ dokumentu:", ["Měsíční report", "Fotodokumentace prototypu", "Prezentace pro investory", "Závěrečná zpráva"])
                r_nazev = st.text_input("Název dokumentu:")
                r_odkaz = st.text_input("🔗 Odkaz na soubor:")
                if st.form_submit_button("Odevzdat úřadu", icon=":material/cloud_upload:"):
                    if r_nazev and r_odkaz:
                        requests.post(f"{SUPABASE_URL}/rest/v1/firemni_reporty", headers=headers, json={"firma_id": moje_firma["id"], "typ_reportu": r_typ, "nazev_reportu": r_nazev, "odkaz_soubor": r_odkaz})
                        st.rerun()

with tab_hr:
    if not moje_firma:
        st.warning("Nejprve musíte projít procesem Založení.")
    else:
        hr_nabor, hr_mzdy, hr_peer = st.tabs(["Nábor & Úřední Přihlášky", "Zúčtování Mzd", "360° Kulturní Fit"])
        with hr_nabor:
            with st.form("form_novy_zamestnanec"):
                col_z1, col_z2 = st.columns(2)
                with col_z1:
                    z_jmeno = st.text_input("Jméno a Příjmení pracovníka:")
                    z_pozice = st.text_input("Role:")
                with col_z2:
                    z_smlouva = st.selectbox("Typ smlouvy:", ["HPP", "DPP", "DPČ"])
                    z_sazba = st.number_input("Hodinová sazba (M-K / hod):", min_value=10, value=50)
                z_podpis = st.checkbox("Smlouva podepsána.")
                z_cssz = st.checkbox("Zaměstnanec přihlášen na ČSSZ / ZP.")
                z_bozp = st.checkbox("Školení BOZP provedeno.")
                if st.form_submit_button("Registrovat nového zaměstnance", icon=":material/person_add:"):
                    if z_jmeno and z_pozice and z_podpis and z_cssz and z_bozp:
                        requests.post(f"{SUPABASE_URL}/rest/v1/zamestnanci", headers=headers, json={"firma_id": moje_firma["id"], "jmeno_zamestnance": z_jmeno, "pozice": z_pozice, "typ_smlouva": z_smlouva, "hodinova_sazba": z_sazba, "odpracovane_hodiny": 0, "vyplaceno_celkem": 0, "hodnoceni_skore": 100})
                        st.rerun()
        with hr_mzdy:
            res_z = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?firma_id=eq.{moje_firma['id']}&select=*", headers=headers)
            zamestnanci_seznam = res_z.json() if res_z.status_code == 200 else []
            if zamestnanci_seznam:
                vybrany_z_jmeno = st.selectbox("Člen týmu k výplatě:", [z["jmeno_zamestnance"] for z in zamestnanci_seznam])
                vybrany_z = next((z for z in zamestnanci_seznam if z["jmeno_zamestnance"] == vybrany_z_jmeno), None)
                if vybrany_z:
                    hodiny = st.number_input("Odpracované hodiny ve Sprintu:", min_value=1.0, value=4.0, step=0.5)
                    hruba = hodiny * vybrany_z["hodinova_sazba"]
                    cista = hruba - (hruba * 0.15)
                    st.markdown(f"**Čistá k výplatě: `{cista:.2f} M-K`**")
                    if st.form_submit_button("💸 Odeslat výplatu", icon=":material/payments:"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/zamestnanci?id=eq.{vybrany_z['id']}", headers=headers, json={"odpracovane_hodiny": vybrany_z["odpracovane_hodiny"] + hodiny, "vyplaceno_celkem": vybrany_z["vyplaceno_celkem"] + cista})
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": "VYDAJ", "titul": f"Výplata: {vybrany_z['jmeno_zamestnance']}", "castka": cista, "auditovano": False})
                        st.rerun()
        with hr_peer:
            if zamestnanci_seznam:
                vybrany_z_peer = st.selectbox("Vyberte kolegu k hodnocení:", [z["jmeno_zamestnance"] for z in zamestnanci_seznam], key="peer_select")
                z_peer_obj = next((z for z in zamestnanci_seznam if z["jmeno_zamestnance"] == vybrany_z_peer), None)
                if z_peer_obj:
                    bod_aktivita = st.slider("Tah na branku v %:", min_value=10, max_value=100, value=90)
                    bod_spoluprace = st.slider("Culture Fit v %:", min_value=10, max_value=100, value=85)
                    if st.button("Uložit 360° Feedback", icon=":material/rate_review:"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/zamestnanci?id=eq.{z_peer_obj['id']}", headers=headers, json={"hodnoceni_skore": (bod_aktivita + bod_spoluprace) / 2.0})
                        st.rerun()

with tab_kalkulace:
    if not moje_firma:
        st.warning("Nejprve musíte projít procesem Založení (Záložka 1).")
    else:
        st.subheader("Unit Economics & Založení produktu pro E-shop")
        with st.form("form_kalkulace"):
            prod_nazev = st.text_input("Produkt / Služba (Název):")
            popis = st.text_area("Lákavý marketingový popis pro E-shop (Tržiště):")
            obrazek = st.text_input("🔗 Odkaz na fotografii produktu:")
            col_k1, col_k2 = st.columns(2)
            with col_k1:
                p_naklady = st.number_input("Přímé náklady (M-K / ks):", min_value=0.0, value=35.0)
                rezie = st.number_input("Režijní náklady (M-K / ks):", min_value=0.0, value=10.0)
            with col_k2:
                marze = st.number_input("Marže / Zisk (M-K / ks):", min_value=0.0, value=50.0)
                dan_pct = st.number_input("M-TECH Daň (%):", min_value=10.0, max_value=30.0, value=15.0)
            k_cena = (p_naklady + rezie + marze) * (1 + (dan_pct / 100.0))
            st.markdown(f"**Konečná prodejní cena pro Tržiště:** `{k_cena:.2f} M-Kreditů`")
            if st.form_submit_button("Odeslat ke schválení", icon=":material/send:"):
                requests.post(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy", headers=headers, json={"firma_id": moje_firma["id"], "nazev_produktu": prod_nazev, "popis": popis, "obrazek_url": obrazek, "prime_naklady": p_naklady, "rezie_skoly": rezie, "mtech_dan_procento": dan_pct, "marze_zisk": marze, "konecna_cena": k_cena, "schvaleno_uradem": False})
                st.rerun()

with tab_ucto:
    if not moje_firma:
        st.warning("Nejprve musíte projít procesem Založení (Záložka 1).")
    else:
        st.subheader("Cash-flow deník & Runway")
        with st.form("form_transakce"):
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1: typ = st.selectbox("Typ transakce:", ["PRIJEM", "VYDAJ"])
            with col_t2: titul = st.text_input("Důvod:", value="Nákup komponent")
            with col_t3: castka = st.number_input("Částka v M-Kreditech:", min_value=1.0, value=50.0)
            if st.form_submit_button("Zaevidovat do Cash-flow", icon=":material/account_balance_wallet:"):
                requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": typ, "titul": titul, "castka": castka, "auditovano": False})
                st.rerun()
        res_kniha = requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?firma_id=eq.{moje_firma['id']}&order=datum.desc", headers=headers)
        if res_kniha.status_code == 200 and len(res_kniha.json()) > 0:
            st.dataframe(res_kniha.json(), use_container_width=True)
