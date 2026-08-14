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
    .status-badge-ok { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid #10b981; padding: 10px; border-radius: 8px; font-weight: 700; text-align: center; font-size: 12px; }
    .status-badge-wait { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid #f59e0b; padding: 10px; border-radius: 8px; font-weight: 700; text-align: center; font-size: 12px; }
    .kanban-col-header { text-align: center; font-weight: 800; padding: 12px; border-radius: 8px; margin-bottom: 15px; color: #fff; text-transform: uppercase; font-size: 14px; }
    .header-todo { background: linear-gradient(45deg, #475569, #334155); }
    .header-ip { background: linear-gradient(45deg, #f59e0b, #d97706); }
    .header-done { background: linear-gradient(45deg, #10b981, #059669); }
    .kanban-card { background-color: #0f172a; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #00B4D8; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .sp-badge { float: right; background-color: #334155; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold; color: #cbd5e1; }
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
trida_nazev = st.session_state.get("trida_nazev", "")

res_akt_u = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{uzivatel}", headers=headers).json()
if res_akt_u and isinstance(res_akt_u, list):
    aktualni_zustatek_zaka = float(res_akt_u[0].get("kredity", 0))
    if not skolni_kod: skolni_kod = res_akt_u[0].get("skolni_kod", "")
    if not trida_nazev: trida_nazev = res_akt_u[0].get("trida_nazev", "")
else:
    aktualni_zustatek_zaka = float(st.session_state.get("kredity", 0))

res_vsechny = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?skolni_kod=eq.{skolni_kod}&select=*&order=id.desc", headers=headers).json()
vsechny_firmy = res_vsechny if isinstance(res_vsechny, list) else []

moje_firma = next((f for f in vsechny_firmy if uzivatel.lower() in [
    str(f.get('ceo_jmeno','')).lower(),
    str(f.get('cfo_jmeno','')).lower(),
    str(f.get('cto_jmeno','')).lower()
]), None)

if not moje_firma:
    res_z_check = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?jmeno_zamestnance=eq.{uzivatel}", headers=headers).json()
    if isinstance(res_z_check, list) and len(res_z_check) > 0:
        f_id_check = res_z_check[0].get('firma_id')
        moje_firma = next((f for f in vsechny_firmy if f['id'] == f_id_check), None)

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

target_skola = moje_firma['skolni_kod'] if moje_firma else (skolni_kod or 'SYSTEM')
nastaveni_res = requests.get(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{target_skola}", headers=headers).json()
if isinstance(nastaveni_res, list) and len(nastaveni_res) > 0:
    akt_dan_mtech = float(nastaveni_res[0].get('mtech_dan_pct', 15.0))
    akt_dan_prijem = float(nastaveni_res[0].get('dan_prijem_pct', 15.0))
    kurz_kc = float(nastaveni_res[0].get('kurz_kc', 10.0))

# =========================================================================
# 1. ZALOŽENÍ FIRMY (PŘEVOD KAPITÁLU Z OSOBNÍHO ÚČTU)
# =========================================================================
if not moje_firma:
    st.info(f"Vítejte v podnikatelském akcelerátoru M-TECH (Třída: {trida_nazev or 'Vaše třída'}).")
    st.markdown("Získali jste oprávnění k založení startupu. Vyplňte níže zakladatelský zápis u Notáře a odešlete spis ke schválení na Kontrolní úřad.")
    
    res_spoluzaci = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?skolni_kod=eq.{skolni_kod}&trida_nazev=eq.{trida_nazev}&role=neq.ucitel", headers=headers).json()
    seznam_spoluzaku = [u['jmeno'] for u in res_spoluzaci if u['jmeno'] != uzivatel] if isinstance(res_spoluzaci, list) else []

    u_notar, u_zivnost, u_financak, u_cssz, u_rejstrik = st.tabs([
        "1. Notářský zápis", "2. Živnostenský úřad", "3. Finanční úřad", "4. ČSSZ", "5. Zápis do Rejstříku"
    ])
    
    if "reg_data" not in st.session_state: st.session_state.reg_data = {}
    
    with u_notar:
        st.session_state.reg_data["nazev_firmy"] = st.text_input("Obchodní název firmy (Startupu):", placeholder="Např. EcoTech s.r.o.")
        col_n1, col_n2, col_n3 = st.columns(3)
        with col_n1: st.session_state.reg_data["ceo"] = st.text_input("CEO (Generální ředitel):", value=uzivatel, disabled=True)
        with col_n2: st.session_state.reg_data["cfo"] = st.selectbox("CFO (Finanční ředitel):", ["-- Neobsazeno --"] + seznam_spoluzaku)
        with col_n3: st.session_state.reg_data["cto"] = st.selectbox("CTO (Technický ředitel):", ["-- Neobsazeno --"] + seznam_spoluzaku)
        st.session_state.reg_data["jednani"] = st.selectbox("Způsob jednání statutárních orgánů:", ["Každý jednatel samostatně", "Společně"])
        
        col_k1, col_k2 = st.columns(2)
        with col_k1: 
            if aktualni_zustatek_zaka < 10.0:
                st.error(f"Váš osobní zůstatek je pouze {aktualni_zustatek_zaka:.2f} M-K. Pro založení firmy potřebujete minimálně 10 M-K. Jděte do Moje peněženka -> Úřad práce a splňte úkoly od vyučujícího, abyste získali kapitál!")
                vklad_hodnota = 0.0
            else:
                vklad_hodnota = st.number_input(
                    f"Vklad základního kapitálu z vaší peněženky (Máte k dispozici: {aktualni_zustatek_zaka:.2f} M-K):",
                    min_value=10.0,
                    max_value=aktualni_zustatek_zaka,
                    value=min(100.0, aktualni_zustatek_zaka)
                )
            st.session_state.reg_data["vklad"] = vklad_hodnota
        with col_k2: 
            st.session_state.reg_data["podily_popis"] = st.text_area("Rozdělení podílů (%):", value="CEO: 100 %")

    with u_zivnost:
        st.session_state.reg_data["druh_zivnosti"] = st.radio("Druh živnosti:", ["Volná", "Řemeslná", "Vázaná"], horizontal=True)
        col_j1, col_j2 = st.columns(2)
        with col_j1:
            st.session_state.reg_data["zivnost_detail"] = st.text_input("Obor činnosti:", placeholder="Např. 3D tisk a modelování...")
            st.session_state.reg_data["predmet"] = st.text_area("Předmět podnikání:", value="Vývoj inovativních produktů a zakázková výroba.")
        with col_j2:
            st.session_state.reg_data["bozp_garant"] = st.text_input("Odpovědný zástupce za BOZP:", value=uzivatel)
            st.session_state.reg_data["provozovna"] = st.text_input("Sídlo provozovny:", value="Školní dílna a MakerSpace")

    with u_financak:
        st.session_state.reg_data["typ_dani"] = st.multiselect("Registrace k daním:", ["DPPO (Daň z příjmu PO)", "M-TECH daň z e-shopu", "Daň ze závislé činnosti (Mzdy)"], default=["DPPO (Daň z příjmu PO)", "M-TECH daň z e-shopu"])
        st.session_state.reg_data["zdanovaci_obdobi"] = st.selectbox("Zdaňovací období:", ["Měsíční", "Čtvrtletní"])

    with u_cssz:
        st.session_state.reg_data["pocet_zakladatelu"] = st.number_input("Předpokládaný celkový počet členů týmu:", min_value=1, value=10)
        st.session_state.reg_data["bozp_prohlaseni"] = st.checkbox("Čestně prohlašuji, že pracoviště splňuje bezpečnostní předpisy BOZP.", value=True)

    with u_rejstrik:
        st.session_state.reg_data["ubo"] = st.text_input("Skutečný majitel (UBO):", value=f"{uzivatel}")
        st.session_state.reg_data["kodex_souhlas"] = st.checkbox("Zavazujeme se dodržovat Etický kodex mladého podnikatele.", value=True)
        st.write("---")
        
        vklad_k_prevodu = float(st.session_state.reg_data.get("vklad", 0))
        st.caption(f"Odesláním žádosti bude z vaší osobní peněženky převedena částka **{vklad_k_prevodu:.2f} M-K** do základního jmění společnosti.")
        
        if st.button("Převést kapitál a odeslat spis na Kontrolní úřad", type="primary"):
            d = st.session_state.reg_data
            nazev = d.get("nazev_firmy", "").strip()
            
            if not nazev:
                st.error("Vyplňte prosím název firmy v záložce Notářský zápis.")
            elif aktualni_zustatek_zaka < vklad_k_prevodu or vklad_k_prevodu < 10.0:
                st.error(f"Nemáte dostatek financí ve své peněžence (Požadováno: {vklad_k_prevodu} M-K).")
            else:
                cfo_val = None if d.get("cfo") == "-- Neobsazeno --" else d.get("cfo")
                cto_val = None if d.get("cto") == "-- Neobsazeno --" else d.get("cto")
                
                zamer_str = f"Druh živnosti: {d.get('druh_zivnosti')} | Obor: {d.get('zivnost_detail', '')} | Předmět: {d.get('predmet', '')} | Garant BOZP: {d.get('bozp_garant', '')} | Provozovna: {d.get('provozovna', '')}"
                
                # 1. Stržení peněz z osobní peněženky CEO
                novy_osobni_zustatek = aktualni_zustatek_zaka - vklad_k_prevodu
                requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{uzivatel}", headers=headers, json={"kredity": novy_osobni_zustatek})
                st.session_state.kredity = novy_osobni_zustatek

                # 2. Vytvoření firmy v databázi
                payload = {
                    "nazev_firmy": nazev,
                    "skolni_kod": skolni_kod,
                    "trida_nazev": trida_nazev,
                    "uroven_projektu": 2,
                    "ceo_jmeno": uzivatel,
                    "cfo_jmeno": cfo_val,
                    "cto_jmeno": cto_val,
                    "podnikatelsky_zamer": zamer_str,
                    "pocatecni_kapital": int(vklad_k_prevodu),
                    "stave_licence": "CEKA_NA_SCHVALENI",
                    "duvod_zamitnuti": ""
                }
                res_create = requests.post(f"{SUPABASE_URL}/rest/v1/firmy", headers=headers, json=payload)
                if res_create.status_code in [200, 201]:
                    new_f_data = res_create.json()
                    new_f_id = new_f_data[0]['id'] if (isinstance(new_f_data, list) and len(new_f_data) > 0) else None
                    
                    # 3. Zaevidování prvního vkladu do firemní knihy
                    if new_f_id:
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={
                            "firma_id": new_f_id,
                            "typ_transakce": "PRIJEM",
                            "titul": f"Vklad základního kapitálu zakladatelem ({uzivatel})",
                            "castka": vklad_k_prevodu,
                            "auditovano": True
                        })
                    st.success(f"Základní kapitál {vklad_k_prevodu} M-K byl úspěšně převeden a žádost odeslána vyučujícímu.")
                    st.rerun()
                else:
                    st.error(f"Chyba při zakládání firmy: {res_create.text}")
    st.stop()

# =========================================================================
# 2. HLAVNÍ STRÁNKA FIRMY
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
    st.warning("Vaše firma byla odeslána na Kontrolní úřad a čeká na posouzení vyučujícím.")
    
if moje_firma["stave_licence"] == "ZAMITNUTO":
    st.error(f"Žádost o zápis do rejstříku byla Kontrolním úřadem vrácena k přepracování.\n\n**Důvod zamítnutí:** {moje_firma.get('duvod_zamitnuti', 'Bez udání důvodu.')}")

# Rozdělení záložek podle role
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
        "1. Můj profil a Moje firma", "2. Výkazy práce"
    ])
    tab_brand = tab_vyvoj = tab_hr = tab_kalkulace = tab_ucto = tab_burza = None

# ==========================================
# ZÁLOŽKA 1: SPIS
# ==========================================
with tab_zalozeni:
    st.subheader("Registrační spis a Právní status")
    barva_statusu = "status-ok" if moje_firma['stave_licence'] == 'SCHVALENO' else ("status-err" if moje_firma['stave_licence'] in ['UKONCENO', 'ZAMITNUTO'] else "status-wait")
    st.markdown(f"**Stav v rejstříku:** <span class='{barva_statusu}'>{moje_firma['stave_licence']}</span>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown(f"**Obchodní firma:** `{moje_firma['nazev_firmy']}`")
        st.markdown(f"**Třída:** `{moje_firma.get('trida_nazev', trida_nazev)}`")
        st.markdown(f"**CEO:** `{moje_firma.get('ceo_jmeno', 'Neobsazeno')}` | **CFO:** `{moje_firma.get('cfo_jmeno', 'Neobsazeno')}` | **CTO:** `{moje_firma.get('cto_jmeno', 'Neobsazeno')}`")
        st.markdown(f"**Základní kapitál:** `{moje_firma.get('pocatecni_kapital', 100)} M-K`")
        st.divider()
        st.markdown("**Předmět podnikání a záměr:**")
        st.write(moje_firma.get('podnikatelsky_zamer', 'Neuvedeno'))

# ==========================================
# ZÁLOŽKA 2: BRAND A AI TANK
# ==========================================
if tab_brand:
    with tab_brand:
        t_aktiva, t_lean, t_ai_shark = st.tabs(["Vizuální Identita", "Lean Canvas", "AI Shark Tank"])
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

            if ma_uspesnou_investici:
                st.success("Získali jste Seed investici od AI Shark Tanku.")
            else:
                with st.form("form_pitch"):
                    p_nazev = st.text_input("Název investiční prezentace:")
                    p_popis = st.text_area("Detailní pitch:")
                    col_p1, col_p2 = st.columns(2)
                    with col_p1: p_castka = st.number_input("Požadovaný kapitál (M-K):", min_value=50, value=200)
                    with col_p2: p_akcie = st.number_input("Nabízené akcie (ks):", min_value=5, value=20)
                    
                    if st.form_submit_button("Spustit AI Pitching"):
                        requests.post(f"{SUPABASE_URL}/rest/v1/ai_pitches", headers=headers, json={"firma_id": moje_firma['id'], "nazev_pitchu": p_nazev, "popis_projektu": p_popis, "zadana_castka": p_castka, "nabizene_akcie": p_akcie, "hodnoceni_ostry": "[SCHVALENO] Ostrý: Čísla dávají smysl.", "hodnoceni_vizionarka": "[SCHVALENO] Vizionářová: Projekt má potenciál.", "hodnoceni_rychly": "[SCHVALENO] Rychlý: Investici schvaluji.", "schvaleno_investovano": True, "investovana_castka": p_castka})
                        r_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers).json()
                        if r_ceo: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers, json={"kredity": r_ceo[0]['kredity'] + p_castka})
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": "PRIJEM", "titul": f"AI Shark Tank: {p_nazev}", "castka": p_castka, "auditovano": True})
                        st.rerun()

# ==========================================
# ZÁLOŽKA 3: AGILE
# ==========================================
if tab_vyvoj:
    with tab_vyvoj:
        st.markdown("#### Týmový Backlog a Sprint")
        with st.form("form_novy_ukol"):
            col_u1, col_u2 = st.columns([3, 1])
            with col_u1: u_nazev = st.text_input("Úkol:")
            with col_u2: u_sp = st.number_input("Story Points:", min_value=1, value=3)
            if st.form_submit_button("Přidat úkol"):
                requests.post(f"{SUPABASE_URL}/rest/v1/projektove_ukoly", headers=headers, json={"firma_id": moje_firma["id"], "nazev_ukolu": u_nazev, "zodpovedna_osoba": uzivatel, "story_points": u_sp, "stav": "TO_DO"})
                st.rerun()

        res_tasks = requests.get(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?firma_id=eq.{moje_firma['id']}&order=id.asc", headers=headers).json()
        tasks = res_tasks if isinstance(res_tasks, list) else []

        col_todo, col_ip, col_done = st.columns(3)
        with col_todo:
            st.markdown("<div class='kanban-col-header header-todo'>K řešení (To Do)</div>", unsafe_allow_html=True)
            for t in [x for x in tasks if x.get('stav') == 'TO_DO']:
                with st.container(border=True):
                    st.write(f"**{t['nazev_ukolu']}** ({t.get('story_points', 1)} SP)")
                    if st.button("Začít řešit", key=f"start_{t['id']}"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?id=eq.{t['id']}", headers=headers, json={"stav": "IN_PROGRESS"})
                        st.rerun()

        with col_ip:
            st.markdown("<div class='kanban-col-header header-ip'>V řešení (In Progress)</div>", unsafe_allow_html=True)
            for t in [x for x in tasks if x.get('stav') == 'IN_PROGRESS']:
                with st.container(border=True):
                    st.write(f"**{t['nazev_ukolu']}** ({t.get('story_points', 1)} SP)")
                    if st.button("Dokončit", key=f"done_{t['id']}"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/projektove_ukoly?id=eq.{t['id']}", headers=headers, json={"stav": "DONE"})
                        st.rerun()

        with col_done:
            st.markdown("<div class='kanban-col-header header-done'>Hotovo (Done)</div>", unsafe_allow_html=True)
            for t in [x for x in tasks if x.get('stav') == 'DONE']:
                with st.container(border=True):
                    st.write(f"**{t['nazev_ukolu']}** ({t.get('story_points', 1)} SP)")

# ==========================================
# ZÁLOŽKA 4: TÝM A HR
# ==========================================
if tab_hr:
    with tab_hr:
        st.subheader("Správa týmu a zaměstnanců")
        
        res_z = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?firma_id=eq.{moje_firma['id']}&select=*", headers=headers).json()
        zamestnanci = res_z if isinstance(res_z, list) else []
        
        st.markdown("#### Seznam zaměstnanců firmy")
        if zamestnanci:
            df_zam = pd.DataFrame(zamestnanci)
            zobrazit_sloupce = [c for c in ['jmeno_zamestnance', 'pozice', 'hodinova_sazba', 'vyplaceno_celkem'] if c in df_zam.columns]
            df_show = df_zam[zobrazit_sloupce].rename(columns={
                'jmeno_zamestnance': 'Jméno pracovníka',
                'pozice': 'Pracovní pozice',
                'hodinova_sazba': 'Sazba (M-K/hod)',
                'vyplaceno_celkem': 'Vyplaceno (M-K)'
            })
            st.dataframe(df_show, use_container_width=True)
        else:
            st.info("Ve firmě zatím nemáte zaregistrovány žádné další zaměstnance.")

        st.divider()

        st.markdown("#### Přijmout nového pracovníka do týmu")
        
        res_zaci_tridy = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?skolni_kod=eq.{skolni_kod}&trida_nazev=eq.{trida_nazev}&role=neq.ucitel", headers=headers).json()
        jmena_v_tyme = [z['jmeno_zamestnance'].lower() for z in zamestnanci]
        if moje_firma.get('ceo_jmeno'): jmena_v_tyme.append(moje_firma['ceo_jmeno'].lower())
        if moje_firma.get('cfo_jmeno'): jmena_v_tyme.append(moje_firma['cfo_jmeno'].lower())
        if moje_firma.get('cto_jmeno'): jmena_v_tyme.append(moje_firma['cto_jmeno'].lower())
        
        volni_zaci = [u['jmeno'] for u in (res_zaci_tridy if isinstance(res_zaci_tridy, list) else []) if u['jmeno'].lower() not in jmena_v_tyme]

        with st.form("form_novy_zamestnanec"):
            col_z1, col_z2 = st.columns(2)
            with col_z1:
                if volni_zaci:
                    z_jmeno = st.selectbox("Vyberte spolužáka ze své třídy:", volni_zaci)
                else:
                    st.info("Ve vaší třídě již nejsou žádní volní žáci.")
                    z_jmeno = None
                z_pozice = st.text_input("Pracovní pozice (např. Operátor 3D tisku, Grafik):")
            with col_z2:
                z_sazba = st.number_input("Hodinová sazba (M-K / hod):", min_value=10.0, value=50.0)
                
            if st.form_submit_button("Přijmout zaměstnance do týmu", type="primary"):
                if z_jmeno and z_pozice:
                    res_post = requests.post(f"{SUPABASE_URL}/rest/v1/zamestnanci", headers=headers, json={
                        "firma_id": int(moje_firma["id"]),
                        "jmeno_zamestnance": str(z_jmeno),
                        "pozice": str(z_pozice),
                        "hodinova_sazba": float(z_sazba),
                        "vyplaceno_celkem": 0.0
                    })
                    if res_post.status_code in [200, 201]:
                        st.success(f"Pracovník {z_jmeno} byl přijat do firmy.")
                        st.rerun()
                    else:
                        st.error(f"Chyba při ukládání: {res_post.text}")
                else:
                    st.error("Vyberte spolužáka a zadejte jeho pracovní pozici.")

        st.divider()

        st.markdown(f"#### Zúčtování mezd")
        if zamestnanci:
            vybrany_z_jmeno = st.selectbox("Komu chcete vyplatit mzdu:", [z["jmeno_zamestnance"] for z in zamestnanci])
            vybrany_z = next((z for z in zamestnanci if z["jmeno_zamestnance"] == vybrany_z_jmeno), None)
            if vybrany_z:
                hodiny = st.number_input("Počet odpracovaných hodin:", min_value=1.0, value=4.0)
                hruba = hodiny * vybrany_z["hodinova_sazba"]
                dan_castka = hruba * (akt_dan_prijem / 100.0)
                cista = hruba - dan_castka
                
                st.info(f"Hrubá mzda: {hruba} M-K | Daň: {dan_castka} M-K | Čistá mzda: {cista} M-K")
                
                if st.button("Odeslat výplatu"):
                    res_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers).json()
                    kredity_ceo = res_ceo[0]['kredity'] if res_ceo else 0
                    
                    if hruba > kredity_ceo:
                        st.error("Nedostatek peněz na firemním účtu (na účtu CEO).")
                    else:
                        requests.patch(f"{SUPABASE_URL}/rest/v1/zamestnanci?id=eq.{vybrany_z['id']}", headers=headers, json={"vyplaceno_celkem": vybrany_z.get("vyplaceno_celkem", 0) + cista})
                        requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers, json={"kredity": kredity_ceo - hruba})
                        res_zam_ucet = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{vybrany_z['jmeno_zamestnance']}", headers=headers).json()
                        if res_zam_ucet: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{vybrany_z['jmeno_zamestnance']}", headers=headers, json={"kredity": res_zam_ucet[0]['kredity'] + cista})
                        st.success("Mzda odeslána.")
                        st.rerun()

# ==========================================
# ZÁLOŽKA 5: CENOTVORBA
# ==========================================
if tab_kalkulace:
    with tab_kalkulace:
        st.subheader("Kalkulace produktů pro E-shop")
        with st.form("form_kalkulace"):
            prod_nazev = st.text_input("Název produktu:")
            popis = st.text_area("Popis:")
            p_naklady = st.number_input("Výrobní náklady (M-K):", min_value=0.0, value=35.0)
            marze = st.number_input("Marže (M-K):", min_value=0.0, value=50.0)
            k_cena = (p_naklady + marze) * (1 + (akt_dan_mtech / 100.0))
            st.markdown(f"**Koncová prodejní cena:** `{k_cena:.2f} M-K`")
            if st.form_submit_button("Odeslat Úřadu ke schválení"):
                requests.post(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy", headers=headers, json={"firma_id": moje_firma["id"], "nazev_produktu": prod_nazev, "popis": popis, "prime_naklady": p_naklady, "marze_zisk": marze, "mtech_dan_procento": akt_dan_mtech, "konecna_cena": k_cena, "schvaleno_uradem": False})
                st.rerun()

# ==========================================
# ZÁLOŽKA 6: ÚČETNICTVÍ
# ==========================================
if tab_ucto:
    with tab_ucto:
        st.subheader("Účetnictví a Kniha transakcí")
        res_kniha = requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?firma_id=eq.{moje_firma['id']}&order=datum.desc", headers=headers).json()
        if isinstance(res_kniha, list) and len(res_kniha) > 0: 
            st.dataframe(pd.DataFrame(res_kniha)[['datum', 'typ_transakce', 'titul', 'castka']], use_container_width=True)
        else:
            st.info("Kniha transakcí je prázdná.")

# ==========================================
# ZÁLOŽKA 7: BURZA
# ==========================================
if tab_burza:
    with tab_burza:
        st.subheader("Investiční burza")
        with st.form("form_ipo"):
            pocet_akcii = st.number_input("Počet akcií k prodeji:", min_value=1, value=50)
            cena_akcie = st.number_input("Cena za 1 akcii (M-K):", min_value=1.0, value=15.0)
            if st.form_submit_button("Zveřejnit na burze"):
                requests.post(f"{SUPABASE_URL}/rest/v1/burza_nabidky", headers=headers, json={"firma_id": moje_firma["id"], "pocet_k_prodeji": pocet_akcii, "cena_za_kus": cena_akcie, "aktivni": True})
                st.success("Akcie zveřejněny.")
                st.rerun()

# ==========================================
# ZÁLOŽKA 8: DENÍK PRÁCE
# ==========================================
if tab_denik:
    with tab_denik:
        st.subheader("Deník práce a Výkazy")
        st.markdown("Zde evidujte, na čem jste konkrétně pracovali. Tyto výkazy slouží pro vyučujícího k hodnocení vaší aktivity.")
        
        with st.form("form_denik_prace_safe"):
            dp_popis = st.text_area("Co přesně jste udělali / odpracovali:")
            dp_hodiny = st.number_input("Počet odpracovaných hodin:", min_value=0.5, max_value=12.0, value=1.0, step=0.5)
            if st.form_submit_button("Uložit do výkazu"):
                if dp_popis.strip():
                    requests.post(f"{SUPABASE_URL}/rest/v1/denik_prace", headers=headers, json={
                        "jmeno_zaka": uzivatel, 
                        "firma_id": moje_firma['id'], 
                        "popis_prace": dp_popis.strip(), 
                        "hodiny": dp_hodiny
                    })
                    st.success("Záznam byl úspěšně uložen.")
                    st.rerun()
                else:
                    st.error("Vyplňte popis práce.")
        
        st.divider()
        st.markdown("#### Historie odvedené práce ve firmě")
        res_denik = requests.get(f"{SUPABASE_URL}/rest/v1/denik_prace?firma_id=eq.{moje_firma['id']}&order=id.desc", headers=headers).json()
        if isinstance(res_denik, list) and len(res_denik) > 0:
            df_denik = pd.DataFrame(res_denik)
            zobrazit = [c for c in ['datum', 'jmeno_zaka', 'popis_prace', 'hodiny'] if c in df_denik.columns]
            df_show = df_denik[zobrazit].rename(columns={'datum': 'Datum', 'jmeno_zaka': 'Pracovník', 'popis_prace': 'Popis činnosti', 'hodiny': 'Hodiny'})
            st.dataframe(df_show, use_container_width=True)
        else:
            st.info("Zatím nebyly zaznamenány žádné pracovní výkazy.")
