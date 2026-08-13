import streamlit as st
import requests
import datetime

st.set_page_config(page_title="Startup Hub a Dashboard", page_icon=":material/insights:", layout="wide")

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
    .kanban-col-header { text-align: center; font-weight: 800; padding: 12px; border-radius: 8px; margin-bottom: 15px; color: #fff; text-transform: uppercase; font-size: 14px; }
    .header-todo { background: linear-gradient(45deg, #475569, #334155); }
    .header-ip { background: linear-gradient(45deg, #f59e0b, #d97706); }
    .header-done { background: linear-gradient(45deg, #10b981, #059669); }
    .kanban-card { background-color: #0f172a; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #00B4D8; }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.get("prihlasen"):
    st.warning("Pro zobrazení Dashboardu se musíte přihlásit na hlavní obrazovce.")
    st.stop()

st.title("Startup Hub a Firemní Dashboard")

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}
except Exception:
    st.error("Chybí konfigurace databáze.")
    st.stop()

uzivatel = st.session_state.get("uzivatel")

res_vsechny = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?select=*&order=id.desc", headers=headers)
vsechny_firmy = res_vsechny.json() if res_vsechny.status_code == 200 else []
moje_firma = next((f for f in vsechny_firmy if uzivatel.lower() in [f.get('ceo_jmeno','').lower(), f.get('cfo_jmeno','').lower(), f.get('cto_jmeno','').lower()]), None)

# --- NAČTENÍ ŠKOLNÍHO NASTAVENÍ (DANĚ A CENÍK) ---
akt_dan_mtech = 15.0
akt_dan_prijem = 15.0
akt_cenik = "Ceník zatím není nastaven."
if moje_firma:
    nastaveni_res = requests.get(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{moje_firma['skolni_kod']}", headers=headers).json()
    if nastaveni_res:
        akt_dan_mtech = float(nastaveni_res[0].get('mtech_dan_pct', 15.0))
        akt_dan_prijem = float(nastaveni_res[0].get('dan_prijem_pct', 15.0))
        akt_cenik = nastaveni_res[0].get('globalni_cenik', '')

if moje_firma:
    f_id = moje_firma["id"]
    st.subheader(f"Entita: {moje_firma['nazev_firmy']} (ID: #{f_id})")
    col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
    
    with col_s1:
        if moje_firma['stave_licence'] == "SCHVALENO": st.markdown('<div class="status-badge-ok">Rejstřík OK</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="status-badge-wait">Založení čeká</div>', unsafe_allow_html=True)
    with col_s2: st.markdown('<div class="status-badge-ok">Brand a Vize</div>', unsafe_allow_html=True)
    with col_s3: st.markdown('<div class="status-badge-ok">Agilní Vývoj</div>', unsafe_allow_html=True)
    with col_s4: st.markdown('<div class="status-badge-ok">HR a Úřady</div>', unsafe_allow_html=True)
    with col_s5: st.markdown('<div class="status-badge-ok">Finance</div>', unsafe_allow_html=True)

    st.write("---")

tab_zalozeni, tab_brand, tab_vyvoj, tab_hr, tab_kalkulace, tab_ucto, tab_burza = st.tabs([
    "1. Zakladatelský Spis", 
    "2. Brand a AI Mentor", 
    "3. Agilní Vývoj",
    "4. Tým a HR",
    "5. Cenotvorba", 
    "6. Účetnictví a Úvěry",
    "7. Burza"
])

# ==========================================
# TAB 1 A 2 (Zůstávají beze změny)
# ==========================================
with tab_zalozeni:
    st.subheader("Registrační spis")
    if moje_firma:
        st.success(f"Stav zápisu v rejstříku: {moje_firma['stave_licence']}")
        if moje_firma.get("duvod_zamitnuti"): st.error(f"Připomínky úřadu: {moje_firma['duvod_zamitnuti']}")
        doc_content = f"# ZAKLADATELSKÁ LISTINA\nFirma: {moje_firma['nazev_firmy']}\nLicenční kód: {moje_firma['skolni_kod']}\nDatum zápisu: {datetime.date.today().strftime('%d. %m. %Y')}\n\n1. Statutární orgán\nCEO: {moje_firma['ceo_jmeno']}\nCFO: {moje_firma['cfo_jmeno']}\nCTO: {moje_firma['cto_jmeno']}\n\n2. Základní kapitál a podnikání\nKapitál: {moje_firma['pocatecni_kapital']} M-Kreditů\nPředmět: {moje_firma['podnikatelsky_zamer']}\n"
        st.download_button(label="Stáhnout Zakladatelskou listinu", data=doc_content, file_name=f"Spis_{moje_firma['nazev_firmy']}.md", mime="text/markdown", icon=":material/download:")
        if st.button("Editovat dokumentaci", icon=":material/edit:"):
            st.session_state.edit_spis = True
            st.rerun()

    if not moje_firma or st.session_state.get("edit_spis", False):
        u_notar, u_zivnost, u_financak, u_cssz, u_rejstrik = st.tabs(["Notář", "Živnostenský úřad", "Finanční úřad", "ČSSZ", "Obchodní Rejstřík"])
        if "reg_data" not in st.session_state: st.session_state.reg_data = {}
        with u_notar:
            st.session_state.reg_data["nazev_firmy"] = st.text_input("Obchodní firma:", value=st.session_state.reg_data.get("nazev_firmy", moje_firma['nazev_firmy'] if moje_firma else ""))
            st.session_state.reg_data["skolni_kod"] = st.text_input("Kód školy:", value=st.session_state.reg_data.get("skolni_kod", moje_firma['skolni_kod'] if moje_firma else "")).upper().strip()
            col_n1, col_n2, col_n3 = st.columns(3)
            with col_n1: st.session_state.reg_data["ceo"] = st.text_input("CEO:", value=st.session_state.reg_data.get("ceo", moje_firma['ceo_jmeno'] if moje_firma else uzivatel))
            with col_n2: st.session_state.reg_data["cfo"] = st.text_input("CFO:", value=st.session_state.reg_data.get("cfo", moje_firma['cfo_jmeno'] if moje_firma else ""))
            with col_n3: st.session_state.reg_data["cto"] = st.text_input("CTO:", value=st.session_state.reg_data.get("cto", moje_firma['cto_jmeno'] if moje_firma else ""))
            st.session_state.reg_data["jednani"] = st.selectbox("Způsob jednání:", ["Každý jednatel samostatně", "Společně alespoň dva jednatelé"])
            col_k1, col_k2 = st.columns(2)
            with col_k1: st.session_state.reg_data["vklad"] = st.number_input("Základní kapitál (M-K):", min_value=10, value=int(st.session_state.reg_data.get("vklad", 100)))
            with col_k2: st.session_state.reg_data["podily_popis"] = st.text_area("Rozdělení podílů (%):", value="CEO: 40 %, CFO: 30 %, CTO: 30 %")
        with u_zivnost:
            st.session_state.reg_data["druh_zivnosti"] = st.radio("Druh živnosti:", ["Volná", "Řemeslná", "Vázaná"], horizontal=True)
            col_j1, col_j2 = st.columns(2)
            with col_j1:
                st.session_state.reg_data["zivnost_detail"] = st.text_input("Obor činnosti:")
                st.session_state.reg_data["predmet"] = st.text_area("Předmět podnikání:", value="Vývoj a prodej.")
            with col_j2:
                st.session_state.reg_data["bozp_garant"] = st.text_input("Garant:", value=uzivatel)
                st.session_state.reg_data["provozovna"] = st.text_input("Sídlo:", value="Akcelerační centrum")
        with u_financak:
            st.session_state.reg_data["typ_dani"] = st.multiselect("Registrace k daním:", ["DPPO", "Závislá činnost", "Nezávislá činnost", "Ekologická daň"], default=["DPPO"])
            st.session_state.reg_data["zdanovaci_obdobi"] = st.selectbox("Období:", ["Měsíční", "Čtvrtletní"])
        with u_cssz:
            st.session_state.reg_data["pocet_zakladatelu"] = st.number_input("Počet pracovníků:", min_value=1, value=3)
            st.session_state.reg_data["bozp_prohlaseni"] = st.checkbox("Pracoviště splňuje BOZP.", value=True)
        with u_rejstrik:
            st.session_state.reg_data["ubo"] = st.text_input("Skuteční majitelé (UBO):", value=f"{uzivatel}")
            st.session_state.reg_data["kodex_souhlas"] = st.checkbox("Akceptujeme Etický kodex.", value=True)
            st.write("---")
            if st.button("Odeslat spis k auditu", icon=":material/send:"):
                d = st.session_state.reg_data
                if d.get("nazev_firmy") and d.get("skolni_kod"):
                    zamer_str = f"[{d.get('druh_zivnosti')}] {d.get('predmet')} (Garant: {d.get('bozp_garant')})"
                    payload = {"nazev_firmy": d.get("nazev_firmy"), "skolni_kod": d.get("skolni_kod"), "uroven_projektu": 2, "ceo_jmeno": d.get("ceo"), "cfo_jmeno": d.get("cfo"), "cto_jmeno": d.get("cto"), "podnikatelsky_zamer": zamer_str, "pocatecni_kapital": d.get("vklad", 100) * 3, "stave_licence": "CEKA_NA_SCHVALENI", "duvod_zamitnuti": ""}
                    if moje_firma: requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{moje_firma['id']}", headers=headers, json=payload)
                    else: requests.post(f"{SUPABASE_URL}/rest/v1/firmy", headers=headers, json=payload)
                    st.session_state.edit_spis = False
                    st.rerun()

with tab_brand:
    if not moje_firma: st.warning("Nejprve založte firmu.")
    else:
        tab_aktiva, tab_lean = st.tabs(["Vizuální Identita", "Lean Canvas"])
        with tab_aktiva:
            with st.form("form_brand"):
                b_logo = st.text_input("Odkaz na LOGO:", value=moje_firma.get('logo_url','') or "")
                b_web = st.text_input("Odkaz na WEB:", value=moje_firma.get('web_url','') or "")
                if st.form_submit_button("Uložit aktiva", icon=":material/save:"):
                    requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{moje_firma['id']}", headers=headers, json={"logo_url": b_logo, "web_url": b_web})
                    st.rerun()
        with tab_lean:
            res_c = requests.get(f"{SUPABASE_URL}/rest/v1/lean_canvas?firma_id=eq.{moje_firma['id']}", headers=headers)
            exist_canvas = res_c.json()[0] if res_c.status_code == 200 and res_c.json() else None
            with st.form("form_canvas"):
                col_c1, col_c2 = st.columns(2)
                with col_c1: prob = st.text_area("Problém", value=exist_canvas.get("problem","") if exist_canvas else "")
                with col_c2: sol = st.text_area("Řešení", value=exist_canvas.get("reseni","") if exist_canvas else "")
                if st.form_submit_button("Uložit Canvas", icon=":material/save:"):
                    c_payload = {"firma_id": moje_firma["id"], "problem": prob, "reseni": sol}
                    if exist_canvas: requests.patch(f"{SUPABASE_URL}/rest/v1/lean_canvas?id=eq.{exist_canvas['id']}", headers=headers, json=c_payload)
                    else: requests.post(f"{SUPABASE_URL}/rest/v1/lean_canvas", headers=headers, json=c_payload)
                    st.rerun()

# ==========================================
# TAB 3: AGILNÍ VÝVOJ
# ==========================================
with tab_vyvoj:
    if not moje_firma: st.warning("Nejprve založte firmu.")
    else:
        ag_kanban, ag_porady, ag_outsourcing = st.tabs(["Agilní Kanban", "Zápisy z porad", "B2B Outsourcing"])
        with ag_kanban:
            with st.form("form_novy_ukol"):
                col_u1, col_u2 = st.columns(2)
                with col_u1: u_nazev = st.text_input("Nový úkol:")
                with col_u2: u_osoba = st.text_input("Zodpovídá:", value=uzivatel)
                if st.form_submit_button("Přidat úkol", icon=":material/add:"):
                    requests.post(f"{SUPABASE_URL}/rest/v1/projektove_ukoly", headers=headers, json={"firma_id": moje_firma["id"], "nazev_ukolu": u_nazev, "zodpovedna_osoba": u_osoba, "stav": "TO_DO"})
                    st.rerun()
            ukoly = requests.get(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?firma_id=eq.{moje_firma['id']}&order=datum_zadani.desc", headers=headers).json()
            col_todo, col_ip, col_done = st.columns(3)
            with col_todo:
                st.markdown("<div class='kanban-col-header header-todo'>K VYŘEŠENÍ</div>", unsafe_allow_html=True)
                for u in [x for x in ukoly if x['stav'] == 'TO_DO']:
                    st.markdown(f"<div class='kanban-card'><h5>{u['nazev_ukolu']}</h5><p>{u['zodpovedna_osoba']}</p></div>", unsafe_allow_html=True)
                    if st.button("Do procesu", key=f"btn_ip_{u['id']}", icon=":material/arrow_forward:"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?id=eq.{u['id']}", headers=headers, json={"stav": "IN_PROGRESS"})
                        st.rerun()
            with col_ip:
                st.markdown("<div class='kanban-col-header header-ip'>V PROCESU</div>", unsafe_allow_html=True)
                for u in [x for x in ukoly if x['stav'] == 'IN_PROGRESS']:
                    st.markdown(f"<div class='kanban-card' style='border-color:#f59e0b;'><h5>{u['nazev_ukolu']}</h5><p>{u['zodpovedna_osoba']}</p></div>", unsafe_allow_html=True)
                    if st.button("Dokončit", key=f"btn_done_{u['id']}", icon=":material/check:"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?id=eq.{u['id']}", headers=headers, json={"stav": "DONE"})
                        st.rerun()
            with col_done:
                st.markdown("<div class='kanban-col-header header-done'>HOTOVO</div>", unsafe_allow_html=True)
                for u in [x for x in ukoly if x['stav'] == 'DONE']:
                    st.markdown(f"<div class='kanban-card' style='border-color:#10b981;'><h5>{u['nazev_ukolu']}</h5><p>{u['zodpovedna_osoba']}</p></div>", unsafe_allow_html=True)
                    if st.button("Smazat", key=f"btn_del_{u['id']}", icon=":material/delete:"):
                        requests.delete(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?id=eq.{u['id']}", headers=headers)
                        st.rerun()
        with ag_porady:
            with st.form("form_porada"):
                projednano = st.text_area("Projednáno:")
                if st.form_submit_button("Uložit Zápis", icon=":material/post_add:"):
                    requests.post(f"{SUPABASE_URL}/rest/v1/zapisy_porady", headers=headers, json={"firma_id": moje_firma["id"], "projednane_body": projednano})
                    st.rerun()
        with ag_outsourcing:
            st.markdown("#### B2B Subdodávky")
            ostatni_firmy = [f for f in vsechny_firmy if f['id'] != moje_firma['id']]
            with st.form("form_outsourcing"):
                dodavatel_nazev = st.selectbox("Dodavatel:", [f['nazev_firmy'] for f in ostatni_firmy] if ostatni_firmy else ["Žádná další firma"])
                o_predmet = st.text_input("Předmět:")
                o_cena = st.number_input("Částka (M-K):", min_value=1.0, value=50.0)
                if st.form_submit_button("Uzavřít kontrakt a odeslat platbu", icon=":material/handshake:"):
                    dodavatel_firma = next((f for f in ostatni_firmy if f['nazev_firmy'] == dodavatel_nazev), None)
                    if dodavatel_firma and o_predmet:
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": "VYDAJ", "titul": f"Outsourcing: {o_predmet}", "castka": o_cena, "auditovano": False})
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": dodavatel_firma["id"], "typ_transakce": "PRIJEM", "titul": f"B2B zakázka od {moje_firma['nazev_firmy']}", "castka": o_cena, "auditovano": False})
                        res_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{dodavatel_firma['ceo_jmeno']}", headers=headers).json()
                        if res_ceo: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{dodavatel_firma['ceo_jmeno']}", headers=headers, json={"kredity": res_ceo[0]['kredity'] + o_cena})
                        st.rerun()

# ==========================================
# TAB 4: HR A MZDY (S AUTO DANÍ Z PŘÍJMU)
# ==========================================
with tab_hr:
    if not moje_firma: st.warning("Nejprve založte firmu.")
    else:
        with st.form("form_novy_zamestnanec"):
            col_z1, col_z2 = st.columns(2)
            with col_z1:
                z_jmeno = st.text_input("Jméno pracovníka:")
                z_pozice = st.text_input("Pozice:")
            with col_z2:
                z_sazba = st.number_input("Hodinová sazba (M-K / hod):", min_value=10, value=50)
            if st.form_submit_button("Registrovat zaměstnance", icon=":material/person_add:"):
                requests.post(f"{SUPABASE_URL}/rest/v1/zamestnanci", headers=headers, json={"firma_id": moje_firma["id"], "jmeno_zamestnance": z_jmeno, "pozice": z_pozice, "typ_smlouva": "HPP", "hodinova_sazba": z_sazba, "odpracovane_hodiny": 0, "vyplaceno_celkem": 0, "hodnoceni_skore": 100})
                st.rerun()
        
        st.write("---")
        st.markdown(f"#### Zúčtování mzd (Daň z příjmu: {akt_dan_prijem} %)")
        res_z = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?firma_id=eq.{moje_firma['id']}&select=*", headers=headers)
        zamestnanci_seznam = res_z.json() if res_z.status_code == 200 else []
        if zamestnanci_seznam:
            vybrany_z_jmeno = st.selectbox("Výplata mzdy:", [z["jmeno_zamestnance"] for z in zamestnanci_seznam])
            vybrany_z = next((z for z in zamestnanci_seznam if z["jmeno_zamestnance"] == vybrany_z_jmeno), None)
            if vybrany_z:
                hodiny = st.number_input("Odpracované hodiny:", min_value=1.0, value=4.0)
                hruba = hodiny * vybrany_z["hodinova_sazba"]
                dan_castka = hruba * (akt_dan_prijem / 100.0)
                cista = hruba - dan_castka
                
                st.info(f"Hrubá mzda: {hruba:.2f} M-K | Daň státu: {dan_castka:.2f} M-K | Čistá mzda: {cista:.2f} M-K")
                
                if st.button(f"Odeslat výplatu a odvést daň", icon=":material/payments:"):
                    # 1. Zapsat výplatu zaměstnanci do HR systému
                    requests.patch(f"{SUPABASE_URL}/rest/v1/zamestnanci?id=eq.{vybrany_z['id']}", headers=headers, json={"vyplaceno_celkem": vybrany_z["vyplaceno_celkem"] + cista})
                    
                    # 2. Strhnout celou hrubou mzdu z účtu firmy (CEO)
                    res_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers).json()
                    kredity_ceo = res_ceo[0]['kredity'] if res_ceo else 0
                    if hruba > kredity_ceo:
                        st.error("Nedostatek peněz na firemním účtu (CEO)!")
                    else:
                        requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers, json={"kredity": kredity_ceo - hruba})
                        
                        # 3. Připsat čistou mzdu zaměstnanci
                        res_zam_ucet = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{vybrany_z['jmeno_zamestnance']}", headers=headers).json()
                        if res_zam_ucet: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{vybrany_z['jmeno_zamestnance']}", headers=headers, json={"kredity": res_zam_ucet[0]['kredity'] + cista})
                        
                        # 4. Odvést daň státu
                        res_stat = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers).json()
                        if res_stat: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers, json={"kredity": res_stat[0]['kredity'] + dan_castka})
                        
                        # 5. Účetnictví firmy
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": "VYDAJ", "titul": f"Mzdové náklady: {vybrany_z['jmeno_zamestnance']}", "castka": hruba, "auditovano": False})
                        st.rerun()

# ==========================================
# TAB 5: CENOTVORBA (Uzamčená M-TECH daň a viditelný Ceník)
# ==========================================
with tab_kalkulace:
    if not moje_firma: st.warning("Nejprve založte firmu.")
    else:
        col_c_left, col_c_right = st.columns([1.5, 1])
        
        with col_c_right:
            st.markdown("#### Globální ceník školy")
            st.info(akt_cenik.replace('\n', '  \n') if akt_cenik else "Zatím nenastaveno.")
                
        with col_c_left:
            st.subheader("Kalkulační list produktu")
            st.caption(f"Sazba M-TECH Daně stanovená Centrální bankou: **{akt_dan_mtech} %**")
            
            with st.form("form_kalkulace"):
                prod_nazev = st.text_input("Název produktu pro E-shop:")
                popis = st.text_area("Popis produktu:")
                obrazek = st.text_input("Odkaz na obrázek:")
                
                col_k1, col_k2 = st.columns(2)
                with col_k1: p_naklady = st.number_input("Přímé náklady dle ceníku (M-K):", min_value=0.0, value=35.0)
                with col_k2: marze = st.number_input("Zisková marže (M-K):", min_value=0.0, value=50.0)
                
                k_cena = (p_naklady + marze) * (1 + (akt_dan_mtech / 100.0))
                
                st.markdown(f"**Koncová cena pro E-shop:** `{k_cena:.2f} M-Kreditů`")
                if st.form_submit_button("Odeslat ke schválení", icon=":material/send:"):
                    requests.post(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy", headers=headers, json={"firma_id": moje_firma["id"], "nazev_produktu": prod_nazev, "popis": popis, "obrazek_url": obrazek, "prime_naklady": p_naklady, "marze_zisk": marze, "mtech_dan_procento": akt_dan_mtech, "konecna_cena": k_cena, "schvaleno_uradem": False})
                    st.rerun()

# ==========================================
# TAB 6 A 7: ÚČETNICTVÍ A BURZA (Zůstávají beze změny)
# ==========================================
with tab_ucto:
    if not moje_firma: st.warning("Nejprve založte firmu.")
    else:
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            st.subheader("Cash-flow deník")
            with st.form("form_transakce"):
                typ = st.selectbox("Typ:", ["PRIJEM", "VYDAJ"])
                castka = st.number_input("Částka (M-K):", min_value=1.0)
                titul = st.text_input("Důvod:")
                if st.form_submit_button("Zaevidovat", icon=":material/account_balance_wallet:"):
                    requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": typ, "titul": titul, "castka": castka, "auditovano": False})
                    st.rerun()
            res_kniha = requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?firma_id=eq.{moje_firma['id']}&order=datum.desc", headers=headers)
            if res_kniha.status_code == 200 and len(res_kniha.json()) > 0:
                st.dataframe(pd.DataFrame(res_kniha.json())[['datum', 'typ_transakce', 'titul', 'castka']], use_container_width=True)
                
        with col_u2:
            st.subheader("Financování a Bankovní úvěry")
            with st.form("form_uver"):
                u_castka = st.number_input("Požadovaná částka (M-K):", min_value=50, value=500)
                u_ucel = st.text_input("Účel půjčky (např. Nákup materiálu):")
                if st.form_submit_button("Zažádat banku o úvěr", icon=":material/account_balance:"):
                    requests.post(f"{SUPABASE_URL}/rest/v1/bankovni_uvery", headers=headers, json={"firma_id": moje_firma["id"], "castka": u_castka, "ucel": u_ucel, "urok_pct": 10, "stav": "ZADOST"})
                    st.rerun()
            
            uvery = requests.get(f"{SUPABASE_URL}/rest/v1/bankovni_uvery?firma_id=eq.{moje_firma['id']}", headers=headers).json()
            if uvery:
                for uv in uvery:
                    if uv['stav'] == 'ZADOST': st.markdown(f"<div class='card-box'><p>Žádost o {uv['castka']} M-K</p><span class='status-wait'>Čeká na schválení</span></div>", unsafe_allow_html=True)
                    elif uv['stav'] == 'ZAMITNUTO': st.markdown(f"<div class='card-box'><p>Žádost o {uv['castka']} M-K</p><span class='status-err'>Zamítnuto úřadem</span></div>", unsafe_allow_html=True)
                    elif uv['stav'] == 'SCHVALENO':
                        zbyva = uv['zbyva_splatit']
                        st.markdown(f"<div class='card-box'><p>Úvěr: {uv['ucel']}</p><b>Zbývá splatit: {zbyva:.2f} M-K</b></div>", unsafe_allow_html=True)
                        with st.form(f"splatka_{uv['id']}"):
                            splatka = st.number_input("Splátka (M-K):", min_value=1.0, max_value=float(zbyva), value=float(min(100.0, zbyva)))
                            if st.form_submit_button("Odeslat splátku"):
                                res_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers).json()
                                k_dispozici = res_ceo[0]['kredity'] if res_ceo else 0
                                if splatka > k_dispozici: st.error("Nedostatek peněz.")
                                else:
                                    requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers, json={"kredity": k_dispozici - splatka})
                                    requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": "VYDAJ", "titul": f"Splátka úvěru", "castka": splatka, "auditovano": True})
                                    novy_zustatek = zbyva - splatka
                                    n_stav = "SPLACENO" if novy_zustatek <= 0 else "SCHVALENO"
                                    requests.patch(f"{SUPABASE_URL}/rest/v1/bankovni_uvery?id=eq.{uv['id']}", headers=headers, json={"zbyva_splatit": novy_zustatek, "stav": n_stav})
                                    st.rerun()

with tab_burza:
    if not moje_firma: st.warning("Nejprve založte firmu.")
    else:
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.markdown("#### Emise nových akcií (IPO)")
            with st.form("form_ipo"):
                pocet_akcii = st.number_input("Počet akcií k prodeji:", min_value=1, value=100)
                cena_akcie = st.number_input("Cena za 1 akcii (M-K):", min_value=1.0, value=10.0)
                if st.form_submit_button("Zveřejnit nabídku", icon=":material/campaign:"):
                    requests.post(f"{SUPABASE_URL}/rest/v1/burza_nabidky", headers=headers, json={"firma_id": moje_firma["id"], "pocet_k_prodeji": pocet_akcii, "cena_za_kus": cena_akcie, "aktivni": True})
                    st.rerun()
        with col_b2:
            st.markdown("#### Výplata dividend")
            portfolio = requests.get(f"{SUPABASE_URL}/rest/v1/portfolio_investoru?firma_id=eq.{moje_firma['id']}", headers=headers).json()
            celkem_akcii = sum(p['pocet_akcii'] for p in portfolio) if portfolio else 0
            st.info(f"Vydáno {celkem_akcii} akcií.")
            with st.form("form_dividendy"):
                castka_rozdelit = st.number_input("Celková částka zisku k rozdělení:", min_value=1.0, value=100.0)
                if st.form_submit_button("Vyplatit akcionářům", icon=":material/payments:"):
                    if not portfolio or celkem_akcii == 0: st.error("Nemáte akcionáře.")
                    else:
                        div_na_akcii = castka_rozdelit / celkem_akcii
                        ceo = moje_firma['ceo_jmeno']
                        res_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{ceo}", headers=headers).json()
                        zustatek_ceo = res_ceo[0]['kredity'] if res_ceo else 0
                        if castka_rozdelit > zustatek_ceo: st.error("Nedostatek prostředků.")
                        else:
                            requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{ceo}", headers=headers, json={"kredity": zustatek_ceo - castka_rozdelit})
                            for p in portfolio:
                                zisk = p['pocet_akcii'] * div_na_akcii
                                r_inv = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{p['investor_jmeno']}", headers=headers).json()
                                if r_inv: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{p['investor_jmeno']}", headers=headers, json={"kredity": r_inv[0]['kredity'] + zisk})
                            requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": "VYDAJ", "titul": "Dividendy", "castka": castka_rozdelit, "auditovano": True})
                            st.rerun()
