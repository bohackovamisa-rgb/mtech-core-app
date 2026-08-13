import streamlit as st
import requests
import datetime
import pandas as pd

st.set_page_config(page_title="Startup Hub a Dashboard", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3, h4 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #00B4D8; width: 100%; font-weight: 600; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0, 180, 216, 0.4); border-color: #00B4D8; background-color: #0f172a; color: white;}
    .card-box { background-color: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 15px; }
    .shark-card { background-color: #0f172a; padding: 15px; border-radius: 10px; border-left: 4px solid #00B4D8; margin-bottom: 10px; }
    .status-badge-ok { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid #10b981; padding: 10px; border-radius: 8px; font-weight: 700; text-align: center; font-size: 12px; }
    .status-badge-wait { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid #f59e0b; padding: 10px; border-radius: 8px; font-weight: 700; text-align: center; font-size: 12px; }
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

res_vsechny = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?select=*&order=id.desc", headers=headers).json()
vsechny_firmy = res_vsechny if res_vsechny else []
moje_firma = next((f for f in vsechny_firmy if uzivatel.lower() in [f.get('ceo_jmeno','').lower(), f.get('cfo_jmeno','').lower(), f.get('cto_jmeno','').lower()]), None)

akt_dan_mtech = 15.0
akt_dan_prijem = 15.0
kurz_kc = 10.0
akt_cenik = "Ceník zatím není nastaven."

if moje_firma:
    nastaveni_res = requests.get(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{moje_firma['skolni_kod']}", headers=headers).json()
    if nastaveni_res:
        akt_dan_mtech = float(nastaveni_res[0].get('mtech_dan_pct', 15.0))
        akt_dan_prijem = float(nastaveni_res[0].get('dan_prijem_pct', 15.0))
        kurz_kc = float(nastaveni_res[0].get('kurz_kc', 10.0))
        akt_cenik = nastaveni_res[0].get('globalni_cenik', '')

if moje_firma:
    st.subheader(f"Entita: {moje_firma['nazev_firmy']} (ID: #{moje_firma['id']})")
    col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
    with col_s1: st.markdown(f'<div class="{"status-badge-ok" if moje_firma["stave_licence"] == "SCHVALENO" else "status-badge-wait"}">{"Rejstřík OK" if moje_firma["stave_licence"] == "SCHVALENO" else "Čeká na audit"}</div>', unsafe_allow_html=True)
    with col_s2: st.markdown('<div class="status-badge-ok">Brand a Vize</div>', unsafe_allow_html=True)
    with col_s3: st.markdown('<div class="status-badge-ok">Agilní Vývoj</div>', unsafe_allow_html=True)
    with col_s4: st.markdown('<div class="status-badge-ok">HR a Úřady</div>', unsafe_allow_html=True)
    with col_s5: st.markdown('<div class="status-badge-ok">Finance</div>', unsafe_allow_html=True)
    st.write("---")

tab_zalozeni, tab_brand, tab_vyvoj, tab_hr, tab_kalkulace, tab_ucto, tab_burza = st.tabs([
    "1. Zakladatelský Spis", "2. Brand a AI Mentor", "3. Agilní Vývoj", "4. Tým a HR", "5. Cenotvorba", "6. Účetnictví a Daně", "7. Burza"
])

with tab_zalozeni:
    st.subheader("Registrační spis")
    if moje_firma:
        st.success(f"Stav zápisu: {moje_firma['stave_licence']}")
        if moje_firma.get("duvod_zamitnuti"): st.error(f"Zamítnuto: {moje_firma['duvod_zamitnuti']}")
        doc = f"# ZAKLADATELSKÁ LISTINA\nFirma: {moje_firma['nazev_firmy']}\nKód: {moje_firma['skolni_kod']}\n\n1. Statutární orgán\nCEO: {moje_firma['ceo_jmeno']}\nCFO: {moje_firma['cfo_jmeno']}\nCTO: {moje_firma['cto_jmeno']}\n\n2. Základní kapitál\nKapitál: {moje_firma['pocatecni_kapital']} M-K\nPředmět: {moje_firma['podnikatelsky_zamer']}\n"
        st.download_button(label="Stáhnout Zakladatelskou Listinu", data=doc, file_name=f"Spis_{moje_firma['nazev_firmy']}.md", mime="text/markdown")
        
        if st.button("Editovat dokumentaci"):
            st.session_state.edit_spis = True
            st.rerun()
            
    if not moje_firma or st.session_state.get("edit_spis", False):
        u_notar, u_zivnost, u_financak, u_cssz, u_rejstrik = st.tabs(["Notář", "Živnostenský úřad", "Finanční úřad", "ČSSZ", "Rejstřík"])
        if "reg_data" not in st.session_state: st.session_state.reg_data = {}
        with u_notar:
            st.session_state.reg_data["nazev_firmy"] = st.text_input("Firma:", value=st.session_state.reg_data.get("nazev_firmy", moje_firma['nazev_firmy'] if moje_firma else ""))
            st.session_state.reg_data["skolni_kod"] = st.text_input("Kód školy:", value=st.session_state.reg_data.get("skolni_kod", moje_firma['skolni_kod'] if moje_firma else "")).upper().strip()
            col_n1, col_n2, col_n3 = st.columns(3)
            with col_n1: st.session_state.reg_data["ceo"] = st.text_input("CEO:", value=st.session_state.reg_data.get("ceo", moje_firma['ceo_jmeno'] if moje_firma else uzivatel))
            with col_n2: st.session_state.reg_data["cfo"] = st.text_input("CFO:", value=st.session_state.reg_data.get("cfo", moje_firma['cfo_jmeno'] if moje_firma else ""))
            with col_n3: st.session_state.reg_data["cto"] = st.text_input("CTO:", value=st.session_state.reg_data.get("cto", moje_firma['cto_jmeno'] if moje_firma else ""))
            st.session_state.reg_data["jednani"] = st.selectbox("Způsob jednání:", ["Každý jednatel samostatně", "Společně"])
            col_k1, col_k2 = st.columns(2)
            with col_k1: st.session_state.reg_data["vklad"] = st.number_input("Základní kapitál (M-K):", min_value=10, value=int(st.session_state.reg_data.get("vklad", 100)))
            with col_k2: st.session_state.reg_data["podily_popis"] = st.text_area("Podíly (%):", value="CEO: 40 %, CFO: 30 %, CTO: 30 %")
        with u_zivnost:
            st.session_state.reg_data["druh_zivnosti"] = st.radio("Živnost:", ["Volná", "Řemeslná", "Vázaná"], horizontal=True)
            col_j1, col_j2 = st.columns(2)
            with col_j1:
                st.session_state.reg_data["zivnost_detail"] = st.text_input("Obor:")
                st.session_state.reg_data["predmet"] = st.text_area("Předmět podnikání:", value="Vývoj a prodej.")
            with col_j2:
                st.session_state.reg_data["bozp_garant"] = st.text_input("Garant:", value=uzivatel)
                st.session_state.reg_data["provozovna"] = st.text_input("Sídlo:", value="Akcelerační centrum")
        with u_financak:
            st.session_state.reg_data["typ_dani"] = st.multiselect("Daně:", ["DPPO", "Závislá činnost", "Nezávislá činnost", "M-TECH daň"], default=["DPPO", "M-TECH daň"])
            st.session_state.reg_data["zdanovaci_obdobi"] = st.selectbox("Období:", ["Měsíční", "Čtvrtletní"])
        with u_cssz:
            st.session_state.reg_data["pocet_zakladatelu"] = st.number_input("Pracovníků:", min_value=1, value=3)
            st.session_state.reg_data["bozp_prohlaseni"] = st.checkbox("Pracoviště splňuje BOZP.", value=True)
        with u_rejstrik:
            st.session_state.reg_data["ubo"] = st.text_input("Skuteční majitelé (UBO):", value=f"{uzivatel}")
            st.session_state.reg_data["kodex_souhlas"] = st.checkbox("Akceptujeme Etický kodex.", value=True)
            st.write("---")
            if st.button("Odeslat spis k auditu"):
                d = st.session_state.reg_data
                zamer_str = f"[{d.get('druh_zivnosti')}] {d.get('predmet')} (Garant: {d.get('bozp_garant')})"
                payload = {"nazev_firmy": d.get("nazev_firmy"), "skolni_kod": d.get("skolni_kod"), "uroven_projektu": 2, "ceo_jmeno": d.get("ceo"), "cfo_jmeno": d.get("cfo"), "cto_jmeno": d.get("cto"), "podnikatelsky_zamer": zamer_str, "pocatecni_kapital": d.get("vklad", 100) * 3, "stave_licence": "CEKA_NA_SCHVALENI", "duvod_zamitnuti": ""}
                if moje_firma: requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{moje_firma['id']}", headers=headers, json=payload)
                else: requests.post(f"{SUPABASE_URL}/rest/v1/firmy", headers=headers, json=payload)
                st.session_state.edit_spis = False
                st.rerun()

with tab_brand:
    if not moje_firma:
        st.warning("Nejprve založte firmu.")
    else:
        t_aktiva, t_lean, t_ai_shark = st.tabs(["Vizuální Identita", "Lean Canvas", "AI Shark Tank (Investoři)"])
        
        with t_aktiva:
            with st.form("form_brand"):
                b_logo = st.text_input("Odkaz na LOGO:", value=moje_firma.get('logo_url','') or "")
                b_web = st.text_input("Odkaz na WEB:", value=moje_firma.get('web_url','') or "")
                if st.form_submit_button("Uložit odkazy"):
                    requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{moje_firma['id']}", headers=headers, json={"logo_url": b_logo, "web_url": b_web})
                    st.rerun()

        with t_lean:
            res_c = requests.get(f"{SUPABASE_URL}/rest/v1/lean_canvas?firma_id=eq.{moje_firma['id']}", headers=headers).json()
            exist_canvas = res_c[0] if res_c else None
            with st.form("form_canvas"):
                col_c1, col_c2 = st.columns(2)
                with col_c1: prob = st.text_area("Problém:", value=exist_canvas.get("problem","") if exist_canvas else "")
                with col_c2: sol = st.text_area("Řešení:", value=exist_canvas.get("reseni","") if exist_canvas else "")
                if st.form_submit_button("Uložit Canvas"):
                    c_payload = {"firma_id": moje_firma["id"], "problem": prob, "reseni": sol}
                    if exist_canvas: requests.patch(f"{SUPABASE_URL}/rest/v1/lean_canvas?id=eq.{exist_canvas['id']}", headers=headers, json=c_payload)
                    else: requests.post(f"{SUPABASE_URL}/rest/v1/lean_canvas", headers=headers, json=c_payload)
                    st.rerun()

        with t_ai_shark:
            st.subheader("Předstupte před AI Investory")
            st.caption("Obhajujte svůj projekt před generativní umělou inteligencí. Pokud investory přesvědčíte, pošlou vám reálný kapitál na firemní účet.")
            
            res_pitches = requests.get(f"{SUPABASE_URL}/rest/v1/ai_pitches?firma_id=eq.{moje_firma['id']}&order=datum.desc", headers=headers).json()
            
            with st.form("form_pitch"):
                p_nazev = st.text_input("Název investiční prezentace / produktu:")
                p_popis = st.text_area("Detailní pitch (Popište problém, vaše řešení a proč na tom vyděláte):")
                col_p1, col_p2 = st.columns(2)
                with col_p1: p_castka = st.number_input("Požadovaný kapitál od AI Investorů (M-K):", min_value=50, value=200)
                with col_p2: p_akcie = st.number_input("Nabízený počet akcií za investici (ks):", min_value=5, value=20)
                
                if st.form_submit_button("Spustit AI Pitching (Prezentovat před Shark Tank)"):
                    if len(p_popis) < 20:
                        st.error("Pitch je příliš krátký! Investoři potřebují více detailů o vašem projektu.")
                    else:
                        with st.spinner("AI Investoři poslouchají vaši prezentaci a analyzují čísla..."):
                            score_ostry = "SCHVALENO" if ("zisk" in p_popis.lower() or "cena" in p_popis.lower() or p_castka <= 300) else "ZAMITNUTO"
                            score_vizionarka = "SCHVALENO" if ("ai" in p_popis.lower() or "inovace" in p_popis.lower() or "ekologie" in p_popis.lower() or "software" in p_popis.lower()) else "ZAMITNUTO"
                            score_rychly = "SCHVALENO" if (len(p_popis) > 80 and p_akcie >= 10) else "ZAMITNUTO"
                            
                            eval_ostry = f"[{score_ostry}] Ing. Viktor Ostrý: " + ("Finanční struktura dává smysl, požadavek na kapitál je přiměřený." if score_ostry == "SCHVALENO" else "Chybí mi detailnější kalkulace návratnosti a marží.")
                            eval_vizionarka = f"[{score_vizionarka}] Elena Vizionářová: " + ("Váš nápad má velký potenciál a přináší skvělou hodnotu na trh!" if score_vizionarka == "SCHVALENO" else "Nenacházím v tom dostatečnou technologickou inovaci ani škálovatelnost.")
                            eval_rychly = f"[{score_rychly}] Petr Rychlý: " + ("Půjdu do toho s vámi, nabídka akcií je fér a chci vidět rychlé výsledky." if score_rychly == "SCHVALENO" else "Riziko je příliš vysoké a nabízíte málo akcií za takový kapitál.")
                            
                            schvaleno = [score_ostry, score_vizionarka, score_rychly].count("SCHVALENO") >= 2
                            
                            requests.post(f"{SUPABASE_URL}/rest/v1/ai_pitches", headers=headers, json={
                                "firma_id": moje_firma['id'], "nazev_pitchu": p_nazev, "popis_projektu": p_popis,
                                "zadana_castka": p_castka, "nabizene_akcie": p_akcie,
                                "hodnoceni_ostry": eval_ostry, "hodnoceni_vizionarka": eval_vizionarka, "hodnoceni_rychly": eval_rychly,
                                "schvaleno_investovano": schvaleno, "investovana_castka": p_castka if schvaleno else 0
                            })
                            
                            if schvaleno:
                                r_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers).json()
                                if r_ceo: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers, json={"kredity": r_ceo[0]['kredity'] + p_castka})
                                requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": "PRIJEM", "titul": f"AI Shark Tank Investice: {p_nazev}", "castka": p_castka, "auditovano": True})
                                requests.post(f"{SUPABASE_URL}/rest/v1/portfolio_investoru", headers=headers, json={"investor_jmeno": "AI Shark Tank Fond", "firma_id": moje_firma["id"], "pocet_akcii": p_akcie})
                            
                            st.rerun()

            st.write("---")
            st.markdown("#### Historie vašich prezentací před AI Shark Tank")
            if res_pitches:
                for pitch in res_pitches:
                    st_barva = "status-badge-ok" if pitch['schvaleno_investovano'] else "status-badge-wait"
                    st.markdown(f"""
                        <div class='card-box'>
                            <div style='display:flex; justify-content:space-between; align-items:center;'>
                                <h4>{pitch['nazev_pitchu']}</h4>
                                <div class='{st_barva}'>{'INVESTICE SCHVÁLENA (+ ' + str(pitch['zadana_castka']) + ' M-K)' if pitch['schvaleno_investovano'] else 'INVESTICE ZAMÍTNUTA'}</div>
                            </div>
                            <p><b>Hodnocení AI Investorů:</b></p>
                            <div class='shark-card'>{pitch['hodnoceni_ostry']}</div>
                            <div class='shark-card'>{pitch['hodnoceni_vizionarka']}</div>
                            <div class='shark-card'>{pitch['hodnoceni_rychly']}</div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Zatím jste před AI Shark Tank neprezentovali žádný projekt.")

with tab_vyvoj:
    if not moje_firma:
        st.warning("Nejprve založte firmu.")
    else:
        ag_kanban, ag_porady, ag_outsourcing = st.tabs(["Agilní Kanban", "Zápisy z porad", "B2B Outsourcing"])
        with ag_kanban:
            with st.form("form_novy_ukol"):
                col_u1, col_u2 = st.columns(2)
                with col_u1: u_nazev = st.text_input("Nový úkol:")
                with col_u2: u_osoba = st.text_input("Zodpovídá:", value=uzivatel)
                if st.form_submit_button("Přidat úkol"):
                    requests.post(f"{SUPABASE_URL}/rest/v1/projektove_ukoly", headers=headers, json={"firma_id": moje_firma["id"], "nazev_ukolu": u_nazev, "zodpovedna_osoba": u_osoba, "stav": "TO_DO"})
                    st.rerun()
            ukoly = requests.get(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?firma_id=eq.{moje_firma['id']}&order=datum_zadani.desc", headers=headers).json()
            col_todo, col_ip, col_done = st.columns(3)
            with col_todo:
                st.markdown("<div class='kanban-col-header header-todo'>K VYŘEŠENÍ</div>", unsafe_allow_html=True)
                for u in [x for x in ukoly if x['stav'] == 'TO_DO']:
                    st.markdown(f"<div class='kanban-card'><h5>{u['nazev_ukolu']}</h5><p>{u['zodpovedna_osoba']}</p></div>", unsafe_allow_html=True)
                    if st.button("Začít pracovat", key=f"btn_ip_{u['id']}"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?id=eq.{u['id']}", headers=headers, json={"stav": "IN_PROGRESS"})
                        st.rerun()
            with col_ip:
                st.markdown("<div class='kanban-col-header header-ip'>V PROCESU</div>", unsafe_allow_html=True)
                for u in [x for x in ukoly if x['stav'] == 'IN_PROGRESS']:
                    st.markdown(f"<div class='kanban-card' style='border-color:#f59e0b;'><h5>{u['nazev_ukolu']}</h5><p>{u['zodpovedna_osoba']}</p></div>", unsafe_allow_html=True)
                    if st.button("Dokončit", key=f"btn_done_{u['id']}"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?id=eq.{u['id']}", headers=headers, json={"stav": "DONE"})
                        st.rerun()
            with col_done:
                st.markdown("<div class='kanban-col-header header-done'>HOTOVO</div>", unsafe_allow_html=True)
                for u in [x for x in ukoly if x['stav'] == 'DONE']:
                    st.markdown(f"<div class='kanban-card' style='border-color:#10b981;'><h5>{u['nazev_ukolu']}</h5><p>{u['zodpovedna_osoba']}</p></div>", unsafe_allow_html=True)
                    if st.button("Smazat", key=f"btn_del_{u['id']}"):
                        requests.delete(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?id=eq.{u['id']}", headers=headers)
                        st.rerun()
        with ag_porady:
            with st.form("form_porada"):
                projednano = st.text_area("Zápis z porady:")
                if st.form_submit_button("Uložit Zápis"):
                    requests.post(f"{SUPABASE_URL}/rest/v1/zapisy_porady", headers=headers, json={"firma_id": moje_firma["id"], "projednane_body": projednano})
                    st.rerun()
        with ag_outsourcing:
            st.markdown("#### B2B Subdodávky")
            ostatni_firmy = [f for f in vsechny_firmy if f['id'] != moje_firma['id']]
            with st.form("form_outsourcing"):
                dodavatel_nazev = st.selectbox("Komu zadáte zakázku:", [f['nazev_firmy'] for f in ostatni_firmy] if ostatni_firmy else ["Žádná další firma v systému"])
                o_predmet = st.text_input("Předmět práce:")
                o_cena = st.number_input("Cena za práci (M-K):", min_value=1.0, value=50.0)
                if st.form_submit_button("Zaplatit dodavatelské firmě"):
                    dodavatel_firma = next((f for f in ostatni_firmy if f['nazev_firmy'] == dodavatel_nazev), None)
                    if dodavatel_firma and o_predmet:
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": "VYDAJ", "titul": f"Outsourcing: {o_predmet}", "castka": o_cena, "auditovano": False})
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": dodavatel_firma["id"], "typ_transakce": "PRIJEM", "titul": f"B2B zakázka od {moje_firma['nazev_firmy']}", "castka": o_cena, "auditovano": False})
                        res_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{dodavatel_firma['ceo_jmeno']}", headers=headers).json()
                        if res_ceo: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{dodavatel_firma['ceo_jmeno']}", headers=headers, json={"kredity": res_ceo[0]['kredity'] + o_cena})
                        st.success("Smlouva uzavřena a peníze převedeny!")
                        st.rerun()

with tab_hr:
    if not moje_firma:
        st.warning("Nejprve založte firmu.")
    else:
        with st.form("form_novy_zamestnanec"):
            col_z1, col_z2 = st.columns(2)
            with col_z1:
                z_jmeno = st.text_input("Jméno pracovníka:")
                z_pozice = st.text_input("Pracovní pozice:")
            with col_z2:
                z_sazba = st.number_input("Hodinová sazba (M-K / hod):", min_value=10, value=50)
            if st.form_submit_button("Registrovat zaměstnance"):
                requests.post(f"{SUPABASE_URL}/rest/v1/zamestnanci", headers=headers, json={"firma_id": moje_firma["id"], "jmeno_zamestnance": z_jmeno, "pozice": z_pozice, "typ_smlouva": "HPP", "hodinova_sazba": z_sazba, "odpracovane_hodiny": 0, "vyplaceno_celkem": 0, "hodnoceni_skore": 100})
                st.rerun()
        
        st.write("---")
        st.markdown(f"#### Zúčtování mzd (Daň z příjmu: {akt_dan_prijem} %)")
        res_z = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?firma_id=eq.{moje_firma['id']}&select=*", headers=headers).json()
        if res_z:
            vybrany_z_jmeno = st.selectbox("Komu chcete vyplatit mzdu:", [z["jmeno_zamestnance"] for z in res_z])
            vybrany_z = next((z for z in res_z if z["jmeno_zamestnance"] == vybrany_z_jmeno), None)
            if vybrany_z:
                hodiny = st.number_input("Počet odpracovaných hodin:", min_value=1.0, value=4.0)
                hruba = hodiny * vybrany_z["hodinova_sazba"]
                dan_castka = hruba * (akt_dan_prijem / 100.0)
                cista = hruba - dan_castka
                
                st.info(f"Hrubá mzda: {hruba} M-K | Daň státu: {dan_castka} M-K | Čistá mzda pro zaměstnance: {cista} M-K (cca {cista * kurz_kc:,.0f} Kč)")
                
                if st.button("Odeslat výplatu a odvést daň státu"):
                    requests.patch(f"{SUPABASE_URL}/rest/v1/zamestnanci?id=eq.{vybrany_z['id']}", headers=headers, json={"vyplaceno_celkem": vybrany_z["vyplaceno_celkem"] + cista})
                    res_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers).json()
                    kredity_ceo = res_ceo[0]['kredity'] if res_ceo else 0
                    
                    if hruba > kredity_ceo:
                        st.error("Nedostatek peněz na firemním účtu (CEO)!")
                    else:
                        requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers, json={"kredity": kredity_ceo - hruba})
                        res_zam_ucet = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{vybrany_z['jmeno_zamestnance']}", headers=headers).json()
                        if res_zam_ucet: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{vybrany_z['jmeno_zamestnance']}", headers=headers, json={"kredity": res_zam_ucet[0]['kredity'] + cista})
                        res_stat = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers).json()
                        if res_stat: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers, json={"kredity": res_stat[0]['kredity'] + dan_castka})
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": "VYDAJ", "titul": f"Mzdové náklady: {vybrany_z['jmeno_zamestnance']}", "castka": hruba, "auditovano": False})
                        st.success("Mzda i daně byly úspěšně odeslány!")
                        st.rerun()

with tab_kalkulace:
    if not moje_firma:
        st.warning("Nejprve založte firmu.")
    else:
        col_c_left, col_c_right = st.columns([1.5, 1])
        with col_c_right:
            st.markdown(f"#### Globální ceník školy <br><small>Kurz: 1 M-K = {kurz_kc} Kč</small>", unsafe_allow_html=True)
            st.info(akt_cenik.replace('\n', '  \n') if akt_cenik else "Zatím nenastaveno.")
        with col_c_left:
            st.subheader("Kalkulace pro E-shop")
            st.caption(f"Sazba M-TECH Daně určená Státem: **{akt_dan_mtech} %**")
            with st.form("form_kalkulace"):
                prod_nazev = st.text_input("Název produktu:")
                popis = st.text_area("Popis produktu (zobrazí se na E-shopu):")
                obrazek = st.text_input("Odkaz na obrázek:")
                col_k1, col_k2 = st.columns(2)
                with col_k1: p_naklady = st.number_input("Vaše přímé výrobní náklady (M-K):", min_value=0.0, value=35.0)
                with col_k2: marze = st.number_input("Váš čistý zisk - Marže (M-K):", min_value=0.0, value=50.0)
                k_cena = (p_naklady + marze) * (1 + (akt_dan_mtech / 100.0))
                st.markdown(f"**Koncová prodejní cena:** `{k_cena:.2f} M-Kreditů` *(odpovídá cca {k_cena * kurz_kc:,.0f} Kč)*")
                if st.form_submit_button("Odeslat Úřadu ke schválení"):
                    requests.post(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy", headers=headers, json={"firma_id": moje_firma["id"], "nazev_produktu": prod_nazev, "popis": popis, "obrazek_url": obrazek, "prime_naklady": p_naklady, "marze_zisk": marze, "mtech_dan_procento": akt_dan_mtech, "konecna_cena": k_cena, "schvaleno_uradem": False})
                    st.rerun()

with tab_ucto:
    if not moje_firma:
        st.warning("Nejprve založte firmu.")
    else:
        col_u1, col_u2 = st.columns(2)
        
        with col_u1:
            st.subheader("Nákup materiálu od Školy")
            with st.form("form_nakup_materialu"):
                titul_nakupu = st.text_input("Předmět nákupu (např. 2x Filament, Arduino):")
                castka_nakup = st.number_input("Celková cena dle Ceníku (M-K):", min_value=1.0, value=10.0)
                if st.form_submit_button("Zaplatit škole za nákup"):
                    res_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers).json()
                    if res_ceo and castka_nakup <= res_ceo[0]['kredity']:
                        requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers, json={"kredity": res_ceo[0]['kredity'] - castka_nakup})
                        res_stat = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers).json()
                        if res_stat: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers, json={"kredity": res_stat[0]['kredity'] + castka_nakup})
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": "VYDAJ", "titul": f"Nákup od školy: {titul_nakupu}", "castka": castka_nakup, "auditovano": False})
                        st.rerun()
                    else: st.error("Nedostatek kreditů!")
            
            st.markdown("#### Cash-flow kniha transakcí")
            res_kniha = requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?firma_id=eq.{moje_firma['id']}&order=datum.desc", headers=headers).json()
            if res_kniha: st.dataframe(pd.DataFrame(res_kniha)[['datum', 'typ_transakce', 'titul', 'castka']], use_container_width=True)
                
        with col_u2:
            st.subheader("Finanční úřad (Daňové přiznání)")
            st.caption("Firma má povinnost spočítat a odeslat státu Daňové přiznání. Pokud se pokusíte krátit daně, úřad vám napaří vysoké penále.")
            
            with st.form("form_dane"):
                dane_priznane = st.number_input("Kolik M-Kreditů přiznáváte na daních?", min_value=0.0, value=0.0)
                if st.form_submit_button("Odeslat daňové přiznání a zaplatit"):
                    res_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers).json()
                    kredity = res_ceo[0]['kredity'] if res_ceo else 0
                    if dane_priznane > kredity:
                        st.error("Nemáte na účtu dostatek prostředků na zaplacení přiznané daně!")
                    else:
                        skutecne_dane_odhad = dane_priznane
                        requests.post(f"{SUPABASE_URL}/rest/v1/danova_priznani", headers=headers, json={"firma_id": moje_firma['id'], "dane_priznane": dane_priznane, "dane_skutecne": skutecne_dane_odhad, "stav": "ODEVZDANO"})
                        requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers, json={"kredity": kredity - dane_priznane})
                        res_stat = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers).json()
                        if res_stat: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers, json={"kredity": res_stat[0]['kredity'] + dane_priznane})
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": "VYDAJ", "titul": "Odvod daně Finančnímu úřadu", "castka": dane_priznane, "auditovano": False})
                        st.success("Přiznání odesláno k auditu.")
                        st.rerun()
            
            st.markdown("#### Odeslaná přiznání")
            priznani = requests.get(f"{SUPABASE_URL}/rest/v1/danova_priznani?firma_id=eq.{moje_firma['id']}&order=datum.desc", headers=headers).json()
            if priznani:
                for p in priznani:
                    barva = "status-wait" if p['stav'] == 'ODEVZDANO' else "status-ok" if p['stav'] == 'SCHVALENO' else "status-err"
                    st.markdown(f"<div class='card-box'>Přiznáno: {p['dane_priznane']} M-K<br><span class='{barva}'>Stav auditu: {p['stav']}</span></div>", unsafe_allow_html=True)
            else:
                st.info("Zatím jste Finančnímu úřadu neodeslali žádné přiznání.")

with tab_burza:
    if not moje_firma:
        st.warning("Nejprve založte firmu.")
    else:
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.markdown("#### Emise nových akcií (IPO)")
            with st.form("form_ipo"):
                pocet_akcii = st.number_input("Počet akcií k prodeji:", min_value=1, value=100)
                cena_akcie = st.number_input("Cena za 1 akcii (M-K):", min_value=1.0, value=10.0)
                if st.form_submit_button("Zveřejnit nabídku na burze"):
                    requests.post(f"{SUPABASE_URL}/rest/v1/burza_nabidky", headers=headers, json={"firma_id": moje_firma["id"], "pocet_k_prodeji": pocet_akcii, "cena_za_kus": cena_akcie, "aktivni": True})
                    st.rerun()
        with col_b2:
            st.markdown("#### Výplata dividend")
            portfolio = requests.get(f"{SUPABASE_URL}/rest/v1/portfolio_investoru?firma_id=eq.{moje_firma['id']}", headers=headers).json()
            celkem_akcii = sum(p['pocet_akcii'] for p in portfolio) if portfolio else 0
            st.info(f"Celkem v oběhu: {celkem_akcii} akcií.")
            with st.form("form_dividendy"):
                castka_rozdelit = st.number_input("Celková částka k rozdělení:", min_value=1.0, value=100.0)
                if st.form_submit_button("Vyplatit akcionářům"):
                    if not portfolio or celkem_akcii == 0: st.error("Nemáte žádné externí akcionáře.")
                    else:
                        div_na_akcii = castka_rozdelit / celkem_akcii
                        ceo = moje_firma['ceo_jmeno']
                        res_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{ceo}", headers=headers).json()
                        if res_ceo and castka_rozdelit <= res_ceo[0]['kredity']:
                            requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{ceo}", headers=headers, json={"kredity": res_ceo[0]['kredity'] - castka_rozdelit})
                            for p in portfolio:
                                zisk = p['pocet_akcii'] * div_na_akcii
                                r_inv = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{p['investor_jmeno']}", headers=headers).json()
                                if r_inv: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{p['investor_jmeno']}", headers=headers, json={"kredity": r_inv[0]['kredity'] + zisk})
                            requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": "VYDAJ", "titul": "Výplata dividend", "castka": castka_rozdelit, "auditovano": True})
                            st.rerun()
                        else: st.error("Nedostatek prostředků na vyplacení dividend.")
