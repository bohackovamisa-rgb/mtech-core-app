import streamlit as st
import requests
import datetime
import pandas as pd
import json

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
    .kanban-card { background-color: #0f172a; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #00B4D8; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .sp-badge { float: right; background-color: #334155; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; color: #cbd5e1; }
    .swot-box { padding: 15px; border-radius: 8px; height: 100%; border: 1px solid #334155; }
    .swot-s { border-top: 4px solid #10b981; }
    .swot-w { border-top: 4px solid #ef4444; }
    .swot-o { border-top: 4px solid #3b82f6; }
    .swot-t { border-top: 4px solid #f59e0b; }
    .status-ok { color: #34d399; font-weight: 700; }
    .status-wait { color: #fbbf24; font-weight: 700; }
    .status-err { color: #f87171; font-weight: 700; }
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

uzivatel = st.session_state.get("uzivatel", "")
skolni_kod = st.session_state.get("skolni_kod", "")

# Doplnění kódu školy z profilu uživatele, pokud v session chybí
if not skolni_kod and uzivatel:
    res_u = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{uzivatel}", headers=headers).json()
    if res_u and isinstance(res_u, list):
        skolni_kod = res_u[0].get("skolni_kod", "")
        st.session_state.skolni_kod = skolni_kod

# Načtení firem z dané školy
res_vsechny = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?skolni_kod=eq.{skolni_kod}&select=*&order=id.desc", headers=headers).json()
vsechny_firmy = res_vsechny if isinstance(res_vsechny, list) else []

# Ověření, zda je uživatel veden jako statutární orgán
moje_firma = next((f for f in vsechny_firmy if uzivatel.lower() in [
    str(f.get('ceo_jmeno','')).lower(),
    str(f.get('cfo_jmeno','')).lower(),
    str(f.get('cto_jmeno','')).lower()
]), None)

# Pokud není statutárním zástupcem, ověříme evidenci mezi zaměstnanci
if not moje_firma:
    res_z_check = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?jmeno_zamestnance=eq.{uzivatel}", headers=headers).json()
    if isinstance(res_z_check, list) and len(res_z_check) > 0:
        f_id_check = res_z_check[0].get('firma_id')
        moje_firma = next((f for f in vsechny_firmy if f['id'] == f_id_check), None)

# Určení role uživatele
if moje_firma:
    if str(moje_firma.get('ceo_jmeno', '')).lower() == uzivatel.lower(): moje_role = "CEO"
    elif str(moje_firma.get('cfo_jmeno', '')).lower() == uzivatel.lower(): moje_role = "CFO"
    elif str(moje_firma.get('cto_jmeno', '')).lower() == uzivatel.lower(): moje_role = "CTO"
    else: moje_role = "ZAMESTNANEC"
else:
    moje_role = "CEO" if st.session_state.get("role") in ["firma", "admin"] else "ZAMESTNANEC"

akt_dan_mtech = 15.0
akt_dan_prijem = 15.0
kurz_kc = 10.0
akt_cenik = "Ceník zatím není nastaven."
dnesni_datum = datetime.date.today().isoformat()

target_skola = moje_firma['skolni_kod'] if moje_firma else (skolni_kod or 'SYSTEM')
nastaveni_res = requests.get(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{target_skola}", headers=headers).json()
if isinstance(nastaveni_res, list) and len(nastaveni_res) > 0:
    akt_dan_mtech = float(nastaveni_res[0].get('mtech_dan_pct', 15.0))
    akt_dan_prijem = float(nastaveni_res[0].get('dan_prijem_pct', 15.0))
    kurz_kc = float(nastaveni_res[0].get('kurz_kc', 10.0))
    akt_cenik = nastaveni_res[0].get('globalni_cenik', '')

# =========================================================================
# 1. PRVNÍ VSTUP – ŽÁK ZATÍM NEMÁ ZALOŽENOU FIRMU
# =========================================================================
if not moje_firma:
    st.info("Vítejte v podnikatelském akcelerátoru M-TECH.")
    st.markdown("Získali jste oprávnění k založení startupu. Vyplňte níže zakladatelský zápis u Notáře a odešlete spis ke schválení na Kontrolní úřad.")
    
    u_notar, u_zivnost, u_financak, u_cssz, u_rejstrik = st.tabs([
        "1. Notářský zápis", "2. Živnostenský úřad", "3. Finanční úřad", "4. ČSSZ", "5. Zápis do Rejstříku"
    ])
    
    if "reg_data" not in st.session_state: st.session_state.reg_data = {}
    
    with u_notar:
        st.session_state.reg_data["nazev_firmy"] = st.text_input("Obchodní název firmy (Startupu):", placeholder="Např. EcoTech s.r.o.")
        col_n1, col_n2, col_n3 = st.columns(3)
        with col_n1: st.session_state.reg_data["ceo"] = st.text_input("CEO (Generální ředitel):", value=uzivatel, disabled=True)
        with col_n2: st.session_state.reg_data["cfo"] = st.text_input("CFO (Finanční ředitel - volitelné):", placeholder="Jméno spolužáka")
        with col_n3: st.session_state.reg_data["cto"] = st.text_input("CTO (Technický ředitel - volitelné):", placeholder="Jméno spolužáka")
        st.session_state.reg_data["jednani"] = st.selectbox("Způsob jednání statutárních orgánů:", ["Každý jednatel samostatně", "Společně"])
        col_k1, col_k2 = st.columns(2)
        with col_k1: st.session_state.reg_data["vklad"] = st.number_input("Základní kapitál zakladatelů (M-K):", min_value=10, value=100)
        with col_k2: st.session_state.reg_data["podily_popis"] = st.text_area("Rozdělení podílů (%):", value="CEO: 100 % (případně např. CEO: 50 %, CFO: 50 %)")

    with u_zivnost:
        st.session_state.reg_data["druh_zivnosti"] = st.radio("Druh živnosti:", ["Volná", "Řemeslná", "Vázaná"], horizontal=True)
        col_j1, col_j2 = st.columns(2)
        with col_j1:
            st.session_state.reg_data["zivnost_detail"] = st.text_input("Obor činnosti:", placeholder="Např. 3D tisk a modelování, grafické práce...")
            st.session_state.reg_data["predmet"] = st.text_area("Předmět podnikání:", value="Vývoj inovativních produktů a zakázková výroba.")
        with col_j2:
            st.session_state.reg_data["bozp_garant"] = st.text_input("Odpovědný zástupce za BOZP:", value=uzivatel)
            st.session_state.reg_data["provozovna"] = st.text_input("Sídlo provozovny:", value="Školní dílna a MakerSpace")

    with u_financak:
        st.session_state.reg_data["typ_dani"] = st.multiselect("Registrace k daním:", ["DPPO (Daň z příjmu PO)", "M-TECH daň z e-shopu", "Daň ze závislé činnosti (Mzdy)"], default=["DPPO (Daň z příjmu PO)", "M-TECH daň z e-shopu"])
        st.session_state.reg_data["zdanovaci_obdobi"] = st.selectbox("Zdaňovací období:", ["Měsíční", "Čtvrtletní"])

    with u_cssz:
        st.session_state.reg_data["pocet_zakladatelu"] = st.number_input("Předpokládaný počet členů týmu:", min_value=1, value=3)
        st.session_state.reg_data["bozp_prohlaseni"] = st.checkbox("Čestně prohlašuji, že pracoviště splňuje bezpečnostní předpisy BOZP.", value=True)

    with u_rejstrik:
        st.session_state.reg_data["ubo"] = st.text_input("Skutečný majitel (UBO):", value=f"{uzivatel}")
        st.session_state.reg_data["kodex_souhlas"] = st.checkbox("Zavazujeme se dodržovat Etický kodex mladého podnikatele.", value=True)
        st.write("---")
        
        if st.button("Odeslat zakladatelský spis na Kontrolní úřad ke schválení", type="primary"):
            d = st.session_state.reg_data
            nazev = d.get("nazev_firmy", "").strip()
            
            if not nazev:
                st.error("Vyplňte prosím název firmy v záložce Notářský zápis.")
            else:
                zamer_str = f"[{d.get('druh_zivnosti')}] {d.get('predmet')} (Garant: {d.get('bozp_garant')})"
                payload = {
                    "nazev_firmy": nazev,
                    "skolni_kod": skolni_kod,
                    "uroven_projektu": 2,
                    "ceo_jmeno": uzivatel,
                    "cfo_jmeno": d.get("cfo") if d.get("cfo") else None,
                    "cto_jmeno": d.get("cto") if d.get("cto") else None,
                    "podnikatelsky_zamer": zamer_str,
                    "pocatecni_kapital": int(d.get("vklad", 100)),
                    "stave_licence": "CEKA_NA_SCHVALENI",
                    "duvod_zamitnuti": ""
                }
                res_create = requests.post(f"{SUPABASE_URL}/rest/v1/firmy", headers=headers, json=payload)
                if res_create.status_code in [200, 201]:
                    st.success("Žádost o registraci firmy byla úspěšně odeslána vyučujícímu ke schválení.")
                    st.rerun()
                else:
                    st.error(f"Chyba při zakládání firmy: {res_create.text}")
    st.stop()

# =========================================================================
# 2. FIRMA EXISTUJE – HLAVNÍ DASHBOARD
# =========================================================================
st.subheader(f"Entita: {moje_firma['nazev_firmy']} (Vaše role: {moje_role})")
col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)

stav_text = "Rejstřík OK" if moje_firma["stave_licence"] == "SCHVALENO" else ("Zamítnuto" if moje_firma["stave_licence"] == "ZAMITNUTO" else "Čeká na audit")
badge_class = "status-badge-ok" if moje_firma["stave_licence"] == "SCHVALENO" else "status-badge-wait"

with col_s1: st.markdown(f'<div class="{badge_class}">{stav_text}</div>', unsafe_allow_html=True)
with col_s2: st.markdown('<div class="status-badge-ok">Brand a Vize</div>', unsafe_allow_html=True)
with col_s3: st.markdown('<div class="status-badge-ok">Agilní Vývoj</div>', unsafe_allow_html=True)
with col_s4: st.markdown('<div class="status-badge-ok">HR a Úřady</div>', unsafe_allow_html=True)
with col_s5: st.markdown('<div class="status-badge-ok">Finance</div>', unsafe_allow_html=True)
st.write("---")

if moje_firma["stave_licence"] == "CEKA_NA_SCHVALENI":
    st.warning("Vaše firma byla odeslána na Kontrolní úřad a čeká na posouzení. Jakmile vyučující registraci schválí, odemknou se vám všechny firemní funkce.")
    
if moje_firma["stave_licence"] == "ZAMITNUTO":
    st.error(f"Žádost o zápis do rejstříku byla Kontrolním úřadem vrácena k přepracování.\n\n**Důvod zamítnutí:** {moje_firma.get('duvod_zamitnuti', 'Bez udání důvodu.')}")
    if st.button("Upravit zakladatelský spis a odeslat znovu"):
        st.session_state.edit_spis = True
        st.rerun()

# Dynamické záložky podle role uživatele
if moje_role == "CEO":
    tab_zalozeni, tab_brand, tab_vyvoj, tab_hr, tab_kalkulace, tab_ucto, tab_burza, tab_denik = st.tabs([
        "1. Zakladatelský Spis", "2. Brand a AI Tank", "3. Řízení (Agile)", "4. Tým a HR", "5. Cenotvorba", "6. Účetnictví a Daně", "7. Burza", "8. Výkazy práce"
    ])
elif moje_role == "CFO":
    tab_zalozeni, tab_hr, tab_ucto, tab_denik = st.tabs([
        "1. Spis a Rejstřík", "2. Mzdy a HR", "3. Účetnictví a Daně", "4. Výkazy práce"
    ])
    tab_brand = tab_vyvoj = tab_kalkulace = tab_burza = None
elif moje_role == "CTO":
    tab_zalozeni, tab_brand, tab_vyvoj, tab_kalkulace, tab_denik = st.tabs([
        "1. Spis a Rejstřík", "2. Brand a Identita", "3. Řízení Vývoje", "4. Cenotvorba a E-shop", "5. Výkazy práce"
    ])
    tab_hr = tab_ucto = tab_burza = None
else:
    tab_zalozeni, tab_denik = st.tabs([
        "1. Můj profil a Moje firma", "2. Výkaz odpracované práce a Tým"
    ])
    tab_brand = tab_vyvoj = tab_hr = tab_kalkulace = tab_ucto = tab_burza = None

# ==========================================
# 1. ZAKLADATELSKÝ SPIS A LIKVIDACE
# ==========================================
with tab_zalozeni:
    st.subheader("Registrační spis a Právní status")
    barva_statusu = "status-ok" if moje_firma['stave_licence'] == 'SCHVALENO' else ("status-err" if moje_firma['stave_licence'] in ['UKONCENO', 'ZAMITNUTO'] else "status-wait")
    st.markdown(f"**Stav v rejstříku:** <span class='{barva_statusu}'>{moje_firma['stave_licence']}</span>", unsafe_allow_html=True)
    
    if moje_firma.get("duvod_zamitnuti"):
        st.error(f"Důvod zamítnutí / pokyny k úpravě: {moje_firma['duvod_zamitnuti']}")
        
    doc = f"ZAKLADATELSKÁ LISTINA\n======================\nFirma: {moje_firma['nazev_firmy']}\nKód: {moje_firma['skolni_kod']}\n\n1. Statutární orgán\nCEO: {moje_firma['ceo_jmeno']}\nCFO: {moje_firma.get('cfo_jmeno','Neobsazeno')}\nCTO: {moje_firma.get('cto_jmeno','Neobsazeno')}\n\n2. Základní kapitál\nKapitál: {moje_firma['pocatecni_kapital']} M-K\nPředmět: {moje_firma.get('podnikatelsky_zamer','')}\n"
    st.download_button(label="Stáhnout Zakladatelskou listinu (.txt)", data=doc, file_name=f"Zakladatelska_listina_{moje_firma['nazev_firmy']}.txt", mime="text/plain")
    
    if moje_role == "CEO":
        if st.button("Editovat dokumentaci a údaje spisu"):
            st.session_state.edit_spis = True
            st.rerun()
            
    if st.session_state.get("edit_spis", False):
        st.write("---")
        st.markdown("#### Úprava zakladatelského spisu")
        u_notar, u_zivnost, u_likvidace = st.tabs(["Notář", "Živnost a Předmět", "Likvidace firmy"])
        
        with u_notar:
            e_nazev = st.text_input("Název firmy:", value=moje_firma['nazev_firmy'])
            col_en1, col_en2 = st.columns(2)
            with col_en1: e_cfo = st.text_input("CFO (Finanční ředitel):", value=moje_firma.get('cfo_jmeno','') or "")
            with col_en2: e_cto = st.text_input("CTO (Technický ředitel):", value=moje_firma.get('cto_jmeno','') or "")
            
        with u_zivnost:
            e_zamer = st.text_area("Předmět podnikání a záměr:", value=moje_firma.get('podnikatelsky_zamer','') or "")
            if st.button("Uložit změny a odeslat znovu k auditu", type="primary"):
                requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{moje_firma['id']}", headers=headers, json={
                    "nazev_firmy": e_nazev, "cfo_jmeno": e_cfo if e_cfo else None, "cto_jmeno": e_cto if e_cto else None,
                    "podnikatelsky_zamer": e_zamer, "stave_licence": "CEKA_NA_SCHVALENI", "duvod_zamitnuti": ""
                })
                st.session_state.edit_spis = False
                st.success("Změny uloženy a odeslány na Kontrolní úřad.")
                st.rerun()
                
        with u_likvidace:
            st.markdown("#### Ukončení činnosti (Likvidace firmy)")
            st.caption("Při ukončení projektu nebo bankrotu je nutné firmu vymazat z rejstříku.")
            if moje_firma['stave_licence'] != 'UKONCENO':
                if st.button("Podat úřadu žádost o zrušení firmy a výmaz"):
                    requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{moje_firma['id']}", headers=headers, json={"stave_licence": "ZADOST_O_ZRUSENI"})
                    st.session_state.edit_spis = False
                    st.rerun()

# ==========================================
# 2. BRAND A AI SHARK TANK
# ==========================================
if tab_brand:
    with tab_brand:
        t_aktiva, t_lean, t_ai_shark, t_reklamace = st.tabs(["Vizuální Identita", "Lean Canvas", "AI Shark Tank", "Zákazníci a AI Reklamace"])
        
        with t_aktiva:
            with st.form("form_brand"):
                b_logo = st.text_input("Odkaz na logo:", value=moje_firma.get('logo_url','') or "")
                b_web = st.text_input("Odkaz na web:", value=moje_firma.get('web_url','') or "")
                if st.form_submit_button("Uložit odkazy"):
                    requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{moje_firma['id']}", headers=headers, json={"logo_url": b_logo, "web_url": b_web})
                    st.rerun()

        with t_lean:
            st.subheader("Kompletní Lean Canvas")
            res_c = requests.get(f"{SUPABASE_URL}/rest/v1/lean_canvas?firma_id=eq.{moje_firma['id']}", headers=headers).json()
            exist_canvas = res_c[0] if isinstance(res_c, list) and len(res_c) > 0 else None
            
            with st.form("form_full_canvas"):
                c1, c2, c3 = st.columns(3)
                with c1: prob = st.text_area("1. Problém", value=exist_canvas.get("problem","") if exist_canvas else "", height=150)
                with c2: hodnota = st.text_area("2. Unikátní Hodnota", value=exist_canvas.get("hodnota","") if exist_canvas else "", height=150)
                with c3: cilovka = st.text_area("3. Cílová Skupina", value=exist_canvas.get("cilova_skupina","") if exist_canvas else "", height=150)
                    
                c4, c5, c6 = st.columns(3)
                with c4: sol = st.text_area("4. Řešení", value=exist_canvas.get("reseni","") if exist_canvas else "", height=150)
                with c5: kanaly = st.text_area("5. Prodejní Kanály", value=exist_canvas.get("kanaly","") if exist_canvas else "", height=150)
                with c6: vyhoda = st.text_area("6. Nefér Výhoda", value=exist_canvas.get("vyhoda","") if exist_canvas else "", height=150)
                    
                c7, c8 = st.columns(2)
                with c7: naklady = st.text_area("7. Struktura Nákladů", value=exist_canvas.get("naklady","") if exist_canvas else "", height=100)
                with c8: prijmy = st.text_area("8. Zdroje Příjmů", value=exist_canvas.get("prijmy","") if exist_canvas else "", height=100)
                    
                if st.form_submit_button("Uložit Lean Canvas"):
                    c_payload = {"firma_id": moje_firma["id"], "problem": prob, "reseni": sol, "hodnota": hodnota, "cilova_skupina": cilovka, "kanaly": kanaly, "vyhoda": vyhoda, "naklady": naklady, "prijmy": prijmy}
                    if exist_canvas: requests.patch(f"{SUPABASE_URL}/rest/v1/lean_canvas?id=eq.{exist_canvas['id']}", headers=headers, json=c_payload)
                    else: requests.post(f"{SUPABASE_URL}/rest/v1/lean_canvas", headers=headers, json=c_payload)
                    st.success("Byznys plán byl uložen.")
                    st.rerun()

        with t_ai_shark:
            st.subheader("Předstupte před AI Investory")
            res_pitches = requests.get(f"{SUPABASE_URL}/rest/v1/ai_pitches?firma_id=eq.{moje_firma['id']}&order=datum.desc", headers=headers).json()
            ma_uspesnou_investici = any(p.get('schvaleno_investovano', False) for p in res_pitches) if isinstance(res_pitches, list) else False
            posledni_pitch_dnes = any(str(p.get('datum', '')).startswith(dnesni_datum) for p in res_pitches) if isinstance(res_pitches, list) else False

            if ma_uspesnou_investici:
                st.success("Získali jste Seed investici od AI Shark Tanku. Pro další kapitál přejděte na Burzu.")
            elif posledni_pitch_dnes:
                st.warning("Dnes už jste prezentovali. Další pitch můžete provést zítra.")
            else:
                with st.form("form_pitch"):
                    p_nazev = st.text_input("Název investiční prezentace:")
                    p_popis = st.text_area("Detailní pitch:")
                    col_p1, col_p2 = st.columns(2)
                    with col_p1: p_castka = st.number_input("Požadovaný kapitál (M-K):", min_value=50, value=200)
                    with col_p2: p_akcie = st.number_input("Nabízené akcie (ks):", min_value=5, value=20)
                    
                    if st.form_submit_button("Spustit AI Pitching"):
                        if len(p_popis) < 20:
                            st.error("Pitch je příliš krátký.")
                        else:
                            gemini_key = st.secrets.get("GEMINI_API_KEY", "")
                            score_ostry, score_vizionarka, score_rychly = "SCHVALENO", "SCHVALENO", "SCHVALENO"
                            eval_ostry = "[SCHVALENO] Ostrý: Čísla dávají smysl."
                            eval_vizionarka = "[SCHVALENO] Vizionářová: Projekt má potenciál."
                            eval_rychly = "[SCHVALENO] Rychlý: Investici schvaluji."
                            
                            if gemini_key:
                                try:
                                    g_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
                                    p_t = f"Porota: Viktor Ostrý(čísla), Elena Vizionářová(inovace), Petr Rychlý(VC). Pitch: {p_nazev}, {p_popis}, {p_castka} MK, {p_akcie} ks. JSON: {{\"ostry_status\":\"SCHVALENO/ZAMITNUTO\",\"ostry_text\":\"...\",\"vizionarka_status\":\"SCHVALENO/ZAMITNUTO\",\"vizionarka_text\":\"...\",\"rychly_status\":\"SCHVALENO/ZAMITNUTO\",\"rychly_text\":\"...\"}}"
                                    res = requests.post(g_url, json={"contents": [{"parts": [{"text": p_t}]}], "generationConfig": {"response_mime_type": "application/json"}}, timeout=10).json()
                                    data_ai = json.loads(res['candidates'][0]['content']['parts'][0]['text'])
                                    score_ostry = data_ai.get("ostry_status", "ZAMITNUTO").upper()
                                    score_vizionarka = data_ai.get("vizionarka_status", "ZAMITNUTO").upper()
                                    score_rychly = data_ai.get("rychly_status", "ZAMITNUTO").upper()
                                    eval_ostry = f"[{score_ostry}] Ing. Viktor Ostrý: " + data_ai.get("ostry_text", "")
                                    eval_vizionarka = f"[{score_vizionarka}] Elena Vizionářová: " + data_ai.get("vizionarka_text", "")
                                    eval_rychly = f"[{score_rychly}] Petr Rychlý: " + data_ai.get("rychly_text", "")
                                except Exception:
                                    pass
                            
                            schvaleno = [score_ostry, score_vizionarka, score_rychly].count("SCHVALENO") >= 2
                            requests.post(f"{SUPABASE_URL}/rest/v1/ai_pitches", headers=headers, json={"firma_id": moje_firma['id'], "nazev_pitchu": p_nazev, "popis_projektu": p_popis, "zadana_castka": p_castka, "nabizene_akcie": p_akcie, "hodnoceni_ostry": eval_ostry, "hodnoceni_vizionarka": eval_vizionarka, "hodnoceni_rychly": eval_rychly, "schvaleno_investovano": schvaleno, "investovana_castka": p_castka if schvaleno else 0})
                            if schvaleno:
                                r_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers).json()
                                if r_ceo: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers, json={"kredity": r_ceo[0]['kredity'] + p_castka})
                                requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": "PRIJEM", "titul": f"AI Shark Tank: {p_nazev}", "castka": p_castka, "auditovano": True})
                            st.rerun()

        with t_reklamace:
            st.subheader("AI Reklamace")
            reklamace_list = requests.get(f"{SUPABASE_URL}/rest/v1/ai_reklamace?firma_id=eq.{moje_firma['id']}&order=datum.desc", headers=headers).json()
            if isinstance(reklamace_list, list) and any(str(r.get('datum', '')).startswith(dnesni_datum) for r in reklamace_list):
                st.success("Čistý stůl. Všechny reklamace byly vyřešeny.")
            else:
                if st.button("Načíst novou stížnost zákazníka"):
                    requests.post(f"{SUPABASE_URL}/rest/v1/ai_reklamace", headers=headers, json={"firma_id": moje_firma['id'], "zakaznik_jmeno": "Testovací zákazník", "text_stiznosti": "Dobrý den, produkt neodpovídá popisu a má vadu.", "vysledek": "CEKA_NA_ODPOVED"})
                    st.rerun()
            if isinstance(reklamace_list, list) and len(reklamace_list) > 0:
                for r in reklamace_list:
                    if r.get('vysledek') == 'CEKA_NA_ODPOVED':
                        st.warning(f"Od: {r['zakaznik_jmeno']} - {r['text_stiznosti']}")
                        with st.form(f"f_rek_{r['id']}"):
                            odpoved = st.text_area("Vaše odpověď a návrh řešení:")
                            if st.form_submit_button("Odeslat zákazníkovi"):
                                requests.patch(f"{SUPABASE_URL}/rest/v1/ai_reklamace?id=eq.{r['id']}", headers=headers, json={"odpoved_firmy": odpoved, "hodnoceni_ai": "Zákazník odpověď přijal.", "vysledek": "SCHVALENO"})
                                st.rerun()

# ==========================================
# 3. MODERNÍ ŘÍZENÍ (AGILE, OKR, SWOT)
# ==========================================
if tab_vyvoj:
    with tab_vyvoj:
        ag_kanban, ag_okr, ag_swot, ag_b2b = st.tabs(["Agilní Kanban & Scrum", "OKR (Cíle firmy)", "SWOT Analýza", "B2B Outsourcing"])
        
        with ag_kanban:
            st.markdown("#### Týmový Backlog & Sprint")
            with st.form("form_novy_ukol"):
                col_u1, col_u2, col_u3 = st.columns([2,1,1])
                with col_u1: u_nazev = st.text_input("Co se musí udělat (User Story):")
                with col_u2: u_osoba = st.text_input("Zodpovídá:", value=uzivatel)
                with col_u3: u_sp = st.number_input("Story Points (Náročnost 1-10):", min_value=1, max_value=10, value=3)
                if st.form_submit_button("Přidat do Backlogu"):
                    requests.post(f"{SUPABASE_URL}/rest/v1/projektove_ukoly", headers=headers, json={"firma_id": moje_firma["id"], "nazev_ukolu": u_nazev, "zodpovedna_osoba": u_osoba, "story_points": u_sp, "stav": "TO_DO"})
                    st.rerun()
            
            ukoly = requests.get(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?firma_id=eq.{moje_firma['id']}&order=datum_zadani.desc", headers=headers).json()
            if isinstance(ukoly, list) and len(ukoly) > 0:
                celkem_sp = sum(u.get('story_points', 1) for u in ukoly)
                hotovo_sp = sum(u.get('story_points', 1) for u in ukoly if u.get('stav') == 'DONE')
                progress = int((hotovo_sp / celkem_sp) * 100) if celkem_sp > 0 else 0
                st.write(f"**Průběh aktuálního Sprintu:** {progress} % ({hotovo_sp} / {celkem_sp} Story Points hotovo)")
                st.progress(progress / 100.0)
            
                col_todo, col_ip, col_done = st.columns(3)
                with col_todo:
                    st.markdown("<div class='kanban-col-header header-todo'>K VYŘEŠENÍ (BACKLOG)</div>", unsafe_allow_html=True)
                    for u in [x for x in ukoly if x.get('stav') == 'TO_DO']:
                        st.markdown(f"<div class='kanban-card'><span class='sp-badge'>{u.get('story_points',1)} SP</span><h5>{u['nazev_ukolu']}</h5><p style='font-size:12px;'>@ {u['zodpovedna_osoba']}</p></div>", unsafe_allow_html=True)
                        if st.button("Začít řešit", key=f"btn_ip_{u['id']}"):
                            requests.patch(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?id=eq.{u['id']}", headers=headers, json={"stav": "IN_PROGRESS"})
                            st.rerun()
                with col_ip:
                    st.markdown("<div class='kanban-col-header header-ip'>V PROCESU (SPRINT)</div>", unsafe_allow_html=True)
                    for u in [x for x in ukoly if x.get('stav') == 'IN_PROGRESS']:
                        st.markdown(f"<div class='kanban-card' style='border-color:#f59e0b;'><span class='sp-badge'>{u.get('story_points',1)} SP</span><h5>{u['nazev_ukolu']}</h5><p style='font-size:12px;'>@ {u['zodpovedna_osoba']}</p></div>", unsafe_allow_html=True)
                        if st.button("Hotovo", key=f"btn_done_{u['id']}"):
                            requests.patch(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?id=eq.{u['id']}", headers=headers, json={"stav": "DONE"})
                            r_u = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{u['zodpovedna_osoba']}", headers=headers).json()
                            if r_u: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{u['zodpovedna_osoba']}", headers=headers, json={"xp_it": r_u[0].get('xp_it',0) + 5})
                            st.rerun()
                with col_done:
                    st.markdown("<div class='kanban-col-header header-done'>DOKONČENO</div>", unsafe_allow_html=True)
                    for u in [x for x in ukoly if x.get('stav') == 'DONE']:
                        st.markdown(f"<div class='kanban-card' style='border-color:#10b981;'><span class='sp-badge'>{u.get('story_points',1)} SP</span><h5>{u['nazev_ukolu']}</h5><p style='font-size:12px;'>@ {u['zodpovedna_osoba']}</p></div>", unsafe_allow_html=True)
                        if st.button("Smazat", key=f"btn_del_{u['id']}"):
                            requests.delete(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?id=eq.{u['id']}", headers=headers)
                            st.rerun()

        with ag_okr:
            st.markdown("#### OKR (Objectives and Key Results)")
            with st.form("form_okr"):
                col_o1, col_o2 = st.columns([1,1])
                with col_o1: n_obj = st.text_input("Hlavní Cíl (Objective):", placeholder="Např. Dosáhnout vedoucí pozice na trhu")
                with col_o2: n_kr = st.text_input("Měřitelný výsledek (Key Result):", placeholder="Např. Obrat 1000 M-K")
                if st.form_submit_button("Vytvořit OKR"):
                    requests.post(f"{SUPABASE_URL}/rest/v1/firemni_okr", headers=headers, json={"firma_id": moje_firma['id'], "objective": n_obj, "key_result": n_kr, "splneno_pct": 0})
                    st.rerun()
                    
            res_okr = requests.get(f"{SUPABASE_URL}/rest/v1/firemni_okr?firma_id=eq.{moje_firma['id']}", headers=headers).json()
            if isinstance(res_okr, list) and len(res_okr) > 0:
                for okr in res_okr:
                    st.markdown(f"<div class='card-box'><h4>{okr['objective']}</h4><p><b>Klíčový výsledek:</b> {okr['key_result']}</p></div>", unsafe_allow_html=True)
                    sl = st.slider("Splněno (%)", min_value=0, max_value=100, value=okr.get('splneno_pct', 0), key=f"sl_{okr['id']}")
                    col_b1, col_b2 = st.columns([1,5])
                    with col_b1:
                        if st.button("Uložit %", key=f"btn_okr_{okr['id']}"):
                            requests.patch(f"{SUPABASE_URL}/rest/v1/firemni_okr?id=eq.{okr['id']}", headers=headers, json={"splneno_pct": sl})
                            st.rerun()
                    with col_b2:
                        if st.button("Smazat Cíl", key=f"del_okr_{okr['id']}"):
                            requests.delete(f"{SUPABASE_URL}/rest/v1/firemni_okr?id=eq.{okr['id']}", headers=headers)
                            st.rerun()

        with ag_swot:
            st.markdown("#### Strategická SWOT Matice")
            res_c = requests.get(f"{SUPABASE_URL}/rest/v1/lean_canvas?firma_id=eq.{moje_firma['id']}", headers=headers).json()
            exist_swot = res_c[0] if isinstance(res_c, list) and len(res_c) > 0 else None
            
            with st.form("form_swot"):
                col_sw1, col_sw2 = st.columns(2)
                with col_sw1:
                    s_str = st.text_area("S - Silné stránky:", value=exist_swot.get("swot_s","") if exist_swot else "")
                    s_opp = st.text_area("O - Příležitosti:", value=exist_swot.get("swot_o","") if exist_swot else "")
                with col_sw2:
                    s_wea = st.text_area("W - Slabé stránky:", value=exist_swot.get("swot_w","") if exist_swot else "")
                    s_thr = st.text_area("T - Hrozby:", value=exist_swot.get("swot_t","") if exist_swot else "")
                
                if st.form_submit_button("Uložit SWOT Matici"):
                    payload = {"firma_id": moje_firma["id"], "swot_s": s_str, "swot_w": s_wea, "swot_o": s_opp, "swot_t": s_thr}
                    if exist_swot: requests.patch(f"{SUPABASE_URL}/rest/v1/lean_canvas?id=eq.{exist_swot['id']}", headers=headers, json=payload)
                    else: requests.post(f"{SUPABASE_URL}/rest/v1/lean_canvas", headers=headers, json=payload)
                    st.rerun()

        with ag_b2b:
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
                        st.success("Smlouva uzavřena a platba převedena.")
                        st.rerun()

# ==========================================
# 4. TÝM A HR
# ==========================================
if tab_hr:
    with tab_hr:
        with st.form("form_novy_zamestnanec"):
            col_z1, col_z2 = st.columns(2)
            with col_z1:
                z_jmeno = st.text_input("Jméno pracovníka (spolužáka):")
                z_pozice = st.text_input("Pracovní pozice (např. Operátor 3D tisku):")
            with col_z2:
                z_sazba = st.number_input("Hodinová sazba (M-K / hod):", min_value=10, value=50)
            if st.form_submit_button("Registrovat zaměstnance"):
                requests.post(f"{SUPABASE_URL}/rest/v1/zamestnanci", headers=headers, json={"firma_id": moje_firma["id"], "jmeno_zamestnance": z_jmeno, "pozice": z_pozice, "typ_smlouva": "HPP", "hodinova_sazba": z_sazba, "odpracovane_hodiny": 0, "vyplaceno_celkem": 0, "hodnoceni_skore": 100})
                st.rerun()
        
        st.write("---")
        st.markdown(f"#### Zúčtování mezd (Daň z příjmu: {akt_dan_prijem} %)")
        res_z = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?firma_id=eq.{moje_firma['id']}&select=*", headers=headers).json()
        if isinstance(res_z, list) and len(res_z) > 0:
            vybrany_z_jmeno = st.selectbox("Komu chcete vyplatit mzdu:", [z["jmeno_zamestnance"] for z in res_z])
            vybrany_z = next((z for z in res_z if z["jmeno_zamestnance"] == vybrany_z_jmeno), None)
            if vybrany_z:
                hodiny = st.number_input("Počet odpracovaných hodin:", min_value=1.0, value=4.0)
                hruba = hodiny * vybrany_z["hodinova_sazba"]
                dan_castka = hruba * (akt_dan_prijem / 100.0)
                cista = hruba - dan_castka
                
                st.info(f"Hrubá mzda: {hruba} M-K | Daň státu: {dan_castka} M-K | Čistá mzda pro zaměstnance: {cista} M-K (cca {cista * kurz_kc:,.0f} Kč)")
                
                if st.button("Odeslat výplatu a odvést daň státu"):
                    res_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers).json()
                    kredity_ceo = res_ceo[0]['kredity'] if res_ceo else 0
                    
                    if hruba > kredity_ceo:
                        st.error("Nedostatek peněz na firemním účtu.")
                    else:
                        requests.patch(f"{SUPABASE_URL}/rest/v1/zamestnanci?id=eq.{vybrany_z['id']}", headers=headers, json={"vyplaceno_celkem": vybrany_z["vyplaceno_celkem"] + cista})
                        requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers, json={"kredity": kredity_ceo - hruba})
                        res_zam_ucet = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{vybrany_z['jmeno_zamestnance']}", headers=headers).json()
                        if res_zam_ucet: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{vybrany_z['jmeno_zamestnance']}", headers=headers, json={"kredity": res_zam_ucet[0]['kredity'] + cista})
                        res_stat = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers).json()
                        if res_stat: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers, json={"kredity": res_stat[0]['kredity'] + dan_castka})
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": "VYDAJ", "titul": f"Mzdové náklady: {vybrany_z['jmeno_zamestnance']}", "castka": hruba, "auditovano": False})
                        st.success("Mzda i daně byly úspěšně odeslány.")
                        st.rerun()

# ==========================================
# 5. CENOTVORBA PRODUKTŮ
# ==========================================
if tab_kalkulace:
    with tab_kalkulace:
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

# ==========================================
# 6. ÚČETNICTVÍ A DAŇOVÉ PŘIZNÁNÍ
# ==========================================
if tab_ucto:
    with tab_ucto:
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            st.subheader("Nákup materiálu od Školy")
            with st.form("form_nakup_materialu"):
                titul_nakupu = st.text_input("Předmět nákupu (např. Filament, Arduino):")
                castka_nakup = st.number_input("Celková cena dle Ceníku (M-K):", min_value=1.0, value=10.0)
                if st.form_submit_button("Zaplatit škole za nákup"):
                    res_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers).json()
                    if res_ceo and castka_nakup <= res_ceo[0]['kredity']:
                        requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers, json={"kredity": res_ceo[0]['kredity'] - castka_nakup})
                        res_stat = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers).json()
                        if res_stat: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers, json={"kredity": res_stat[0]['kredity'] + castka_nakup})
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": "VYDAJ", "titul": f"Nákup od školy: {titul_nakupu}", "castka": castka_nakup, "auditovano": False})
                        st.rerun()
                    else: st.error("Nedostatek kreditů.")
            
            st.markdown("#### Cash-flow kniha transakcí")
            res_kniha = requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?firma_id=eq.{moje_firma['id']}&order=datum.desc", headers=headers).json()
            if isinstance(res_kniha, list) and len(res_kniha) > 0: 
                st.dataframe(pd.DataFrame(res_kniha)[['datum', 'typ_transakce', 'titul', 'castka']], use_container_width=True)
                
        with col_u2:
            st.subheader("Finanční úřad (Daňové přiznání)")
            with st.form("form_dane"):
                dane_priznane = st.number_input("Kolik M-Kreditů přiznáváte na daních?", min_value=0.0, value=0.0)
                if st.form_submit_button("Odeslat daňové přiznání a zaplatit"):
                    res_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers).json()
                    kredity = res_ceo[0]['kredity'] if res_ceo else 0
                    if dane_priznane > kredity:
                        st.error("Nemáte na účtu dostatek prostředků.")
                    else:
                        requests.post(f"{SUPABASE_URL}/rest/v1/danova_priznani", headers=headers, json={"firma_id": moje_firma['id'], "dane_priznane": dane_priznane, "dane_skutecne": dane_priznane, "stav": "ODEVZDANO"})
                        requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers, json={"kredity": kredity - dane_priznane})
                        res_stat = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers).json()
                        if res_stat: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers, json={"kredity": res_stat[0]['kredity'] + dane_priznane})
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": "VYDAJ", "titul": "Odvod daně Finančnímu úřadu", "castka": dane_priznane, "auditovano": False})
                        st.success("Přiznání odesláno k auditu.")
                        st.rerun()

# ==========================================
# 7. BURZA, AI RATING A INVESTICE
# ==========================================
if tab_burza:
    with tab_burza:
        st.markdown("#### Wall Street (M-TECH Financial News)")
        zpravy = requests.get(f"{SUPABASE_URL}/rest/v1/burza_zpravy?order=datum.desc&limit=3", headers=headers).json()
        if isinstance(zpravy, list) and len(zpravy) > 0:
            for z in zpravy:
                st.markdown(f"<div class='card-box' style='border-left: 4px solid #f59e0b;'><b>{z['titulek']}</b><br><span style='color:#cbd5e1; font-size:14px;'>{z['text_zpravy']}</span></div>", unsafe_allow_html=True)
        
        st.write("---")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.markdown("#### Emise nových akcií (IPO) & AI Valuace")
            rating = moje_firma.get('ai_rating', 'Nehodnoceno')
            max_cena = float(moje_firma.get('ai_hodnota_akcie', 0))
            
            st.markdown(f"<div style='background:rgba(0,180,216,0.1); padding:15px; border-radius:8px; margin-bottom:15px;'>Aktuální AI Rating: <b>{rating}</b><br>Max. povolená cena akcie: <b>{max_cena} M-K</b></div>", unsafe_allow_html=True)
            
            gemini_key = st.secrets.get("GEMINI_API_KEY", "")
            if st.button("Požádat o novou AI Valuaci", key="btn_valuace"):
                with st.spinner("AI Agentura analyzuje vaši firmu..."):
                    if gemini_key:
                        try:
                            z_ucet = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers).json()[0]['kredity']
                            g_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
                            prompt = f"Ohodnoť firmu {moje_firma['nazev_firmy']}. Kapitál: {z_ucet} M-K. Vrať JSON: {{\"rating\":\"AAA/AA/A/BBB/BB/C\",\"cena\":10}}"
                            res_ai = requests.post(g_url, json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "application/json"}}, timeout=10).json()
                            data_ai = json.loads(res_ai['candidates'][0]['content']['parts'][0]['text'])
                            requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{moje_firma['id']}", headers=headers, json={"ai_rating": data_ai.get("rating", "BB"), "ai_hodnota_akcie": float(data_ai.get("cena", 15.0))})
                            st.rerun()
                        except Exception:
                            st.error("AI Valuace selhala, zkuste to znovu.")
            
            if rating != 'Nehodnoceno':
                with st.form("form_ipo"):
                    pocet_akcii = st.number_input("Počet akcií k prodeji:", min_value=1, value=50)
                    cena_akcie = st.number_input(f"Cena za 1 akcii (Max {max_cena} M-K):", min_value=1.0, max_value=float(max_cena) if max_cena > 1.0 else 10.0, value=float(max_cena) if max_cena > 1.0 else 10.0)
                    if st.form_submit_button("Zveřejnit nabídku na burze"):
                        requests.post(f"{SUPABASE_URL}/rest/v1/burza_nabidky", headers=headers, json={"firma_id": moje_firma["id"], "pocet_k_prodeji": pocet_akcii, "cena_za_kus": cena_akcie, "aktivni": True})
                        st.success("Akcie jsou na burze.")
                        st.rerun()

        with col_b2:
            st.markdown("#### Výplata dividend")
            portfolio = requests.get(f"{SUPABASE_URL}/rest/v1/portfolio_investoru?firma_id=eq.{moje_firma['id']}", headers=headers).json()
            celkem_akcii = sum(p['pocet_akcii'] for p in portfolio) if isinstance(portfolio, list) else 0
            st.info(f"Celkem externích akcií v oběhu: {celkem_akcii} ks.")
            with st.form("form_dividendy"):
                castka_rozdelit = st.number_input("Celková částka k rozdělení (M-K):", min_value=1.0, value=100.0)
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

# ==========================================
# 8. DENÍK PRÁCE A TÝMOVÉ HODNOCENÍ
# ==========================================
if tab_denik:
    with tab_denik:
        st.subheader("Deník práce a Týmové hodnocení")
        
        if moje_role in ["CEO", "CFO", "CTO"]:
            sub_vykaz, sub_kontrola, sub_peer = st.tabs([
                "1. Můj výkaz práce", "2. Kontrola odpracovaných hodin zaměstnanců", "3. Hodnocení týmu"
            ])
        else:
            sub_vykaz, sub_peer = st.tabs([
                "1. Můj výkaz práce (Výroba)", "2. Hodnocení týmu"
            ])
            sub_kontrola = None

        with sub_vykaz:
            st.markdown("#### Výkaz mé odvedené práce (Manuální práce / Výroba / Schůzky)")
            st.caption(f"Přihlášený žák: **{uzivatel}** | Firma: **{moje_firma['nazev_firmy']}**")
            
            with st.form("form_denik_prace_safe"):
                dp_popis = st.text_area("Popis odvedené práce (např. 2h tisk 3D modelů, balení produktů, úklid dílny):")
                dp_hodiny = st.number_input("Počet odpracovaných hodin:", min_value=0.5, max_value=12.0, value=1.0, step=0.5)
                
                if st.form_submit_button("Uložit zápis do výkazu"):
                    if dp_popis.strip():
                        requests.post(
                            f"{SUPABASE_URL}/rest/v1/denik_prace",
                            headers=headers,
                            json={
                                "jmeno_zaka": uzivatel,
                                "firma_id": moje_firma['id'],
                                "popis_prace": dp_popis.strip(),
                                "hodiny": dp_hodiny
                            }
                        )
                        st.success("Záznam byl úspěšně uložen do vašeho výkazu práce.")
                        st.rerun()
                    else:
                        st.error("Vyplňte popis práce.")

            st.markdown("##### Vaše zapsané hodiny")
            res_moje_prace = requests.get(
                f"{SUPABASE_URL}/rest/v1/denik_prace?jmeno_zaka=eq.{uzivatel}&order=datum.desc",
                headers=headers
            ).json()
            
            if isinstance(res_moje_prace, list) and len(res_moje_prace) > 0:
                df_prace = pd.DataFrame(res_moje_prace)
                kolecka = [c for c in ['datum', 'popis_prace', 'hodiny'] if c in df_prace.columns]
                st.dataframe(df_prace[kolecka], use_container_width=True)
            else:
                st.info("Zatím nemáte v deníku práce žádné zapsané hodiny.")

        if sub_kontrola:
            with sub_kontrola:
                st.markdown(f"#### Přehled odpracovaných hodin zaměstnanců firmy {moje_firma['nazev_firmy']}")
                st.caption("Jako vedení firmy zde vidíte výkazy práce všech vašich dělníků a zaměstnanců.")
                
                res_tým_prace = requests.get(
                    f"{SUPABASE_URL}/rest/v1/denik_prace?firma_id=eq.{moje_firma['id']}&order=datum.desc",
                    headers=headers
                ).json()
                
                if isinstance(res_tým_prace, list) and len(res_tým_prace) > 0:
                    df_tym = pd.DataFrame(res_tým_prace)
                    kolecka_tym = [c for c in ['datum', 'jmeno_zaka', 'popis_prace', 'hodiny'] if c in df_tym.columns]
                    st.dataframe(df_tym[kolecka_tym], use_container_width=True)
                    
                    celkem_hodin_firma = sum(item.get('hodiny', 0) for item in res_tým_prace)
                    st.markdown(f"**Celkem odpracováno ve výrobě/dílně pro vaši firmu:** `{celkem_hodin_firma} hodin`")
                else:
                    st.info("Vaši zaměstnanci zatím nezapsali žádnou odpracovanou práci.")

        with sub_peer:
            st.markdown("#### Vzájemné hodnocení spoluhráčů")
            st.caption("Ohodnoťte přínos a pracovitost ostatních členů vašeho týmu.")
            
            vsechni_clenove = []
            if moje_firma.get('ceo_jmeno'): vsechni_clenove.append(moje_firma['ceo_jmeno'])
            if moje_firma.get('cfo_jmeno'): vsechni_clenove.append(moje_firma['cfo_jmeno'])
            if moje_firma.get('cto_jmeno'): vsechni_clenove.append(moje_firma['cto_jmeno'])
            
            res_z = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?firma_id=eq.{moje_firma['id']}", headers=headers).json()
            if isinstance(res_z, list):
                for z in res_z:
                    if z.get('jmeno_zamestnance'):
                        vsechni_clenove.append(z['jmeno_zamestnance'])
                        
            kolegovi = [c for c in list(set(vsechni_clenove)) if c.lower() != uzivatel.lower()]
            
            if kolegovi:
                with st.form("form_peer_review_safe"):
                    vybrany_kolega = st.selectbox("Vyberte kolegu k ohodnocení:", kolegovi)
                    body_hodnoceni = st.slider("Hodnocení pracovitosti a přínosu (1 = Neaktivní, 5 = Vynikající):", 1, 5, 5)
                    slovni_komentar = st.text_area("Stručný komentář k jeho práci:")
                    
                    if st.form_submit_button("Odeslat hodnocení kolegy"):
                        requests.post(
                            f"{SUPABASE_URL}/rest/v1/peer_review",
                            headers=headers,
                            json={
                                "hodnotitel": uzivatel,
                                "hodnoceny": vybrany_kolega,
                                "firma_id": moje_firma['id'],
                                "body": body_hodnoceni,
                                "komentar": slovni_komentar.strip()
                            }
                        )
                        st.success(f"Hodnocení pro žáka {vybrany_kolega} bylo uloženo.")
                        st.rerun()
            else:
                st.info("Ve firmě jste zatím sami, nemáte koho hodnotit.")
