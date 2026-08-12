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

# Načtení firem
res_vsechny = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?select=*&order=id.desc", headers=headers)
vsechny_firmy = res_vsechny.json() if res_vsechny.status_code == 200 else []

moje_firma = next((f for f in vsechny_firmy if uzivatel.lower() in [f.get('ceo_jmeno','').lower(), f.get('cfo_jmeno','').lower(), f.get('cto_jmeno','').lower()]), None)
if not moje_firma and len(vsechny_firmy) > 0:
    moje_firma = vsechny_firmy[0]

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

    # --- KONTROLNÍ PANEL STAVU FIRMY ---
    st.subheader(":material/fact_check: Přehled plnění povinností podle metodiky M-TECH CORE")
    col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
    stav = moje_firma['stave_licence']
    
    with col_s1:
        if stav == "SCHVALENO": st.markdown('<div class="status-badge-ok">Licence Udělena</div>', unsafe_allow_html=True)
        elif stav == "CEKA_NA_SCHVALENI": st.markdown('<div class="status-badge-wait">Čeká na Úřad</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="status-badge-err">Licence Zamítnuta</div>', unsafe_allow_html=True)
            
    with col_s2:
        if has_canvas: st.markdown('<div class="status-badge-ok">Lean Canvas OK</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="status-badge-off">Lean Canvas Chybí</div>', unsafe_allow_html=True)

    with col_s3:
        if has_porada: st.markdown('<div class="status-badge-ok">Zápis z Porady OK</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="status-badge-off">Zápis Chybí</div>', unsafe_allow_html=True)
            
    with col_s4:
        if has_kalkulace: st.markdown('<div class="status-badge-ok">Kalkulace OK</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="status-badge-off">Kalkulace Chybí</div>', unsafe_allow_html=True)
            
    with col_s5:
        if has_ucto: st.markdown('<div class="status-badge-ok">Účetnictví OK</div>', unsafe_allow_html=True)
        else: st.markdown('<div class="status-badge-off">Kniha Prázdná</div>', unsafe_allow_html=True)

    st.write("")

    if stav == "CEKA_NA_SCHVALENI":
        st.info(f"📋 **Zakladatelská listina firmy '{moje_firma['nazev_firmy']}' byla úspěšně odeslána na Kontrolní úřad.**")
    elif stav == "ZAMITNUTO":
        st.error(f"❌ **Žádost o licenci byla zamítnuta Kontrolním úřadem.** Důvod: {moje_firma.get('duvod_zamitnuti', 'Není uveden')}")
    elif stav == "SCHVALENO":
        st.success(f"🎉 **Licence firmy '{moje_firma['nazev_firmy']}' je aktivní!** Můžete plně podnikat.")

    st.write("---")

# --- SAMOSTATNÉ ZÁLOŽKY DLE METODIKY ---
tab_zaklad, tab_canvas, tab_porady, tab_kalkulace, tab_ucto = st.tabs([
    ":material/description: 1. Zakladatelská listina", 
    ":material/lightbulb: 2. Lean Canvas", 
    ":material/forum: 3. Zápisy z porad",
    ":material/calculate: 4. Kalkulační listy", 
    ":material/menu_book: 5. Kniha příjmů a výdajů"
])

# --- TAB 1: ZAKLADATELSKÁ LISTINA (DLE PŘÍLOHY Č. 2 METODIKY) ---
with tab_zaklad:
    st.subheader("Žádost o udělení licence a Zakladatelská listina")
    st.caption("Právní a organizační základ firmy v rámci projektu M-TECH CORE.")
    
    if moje_firma:
        st.success(f"✔️ **EVIDOVANÁ FIRMA: {moje_firma['nazev_firmy']}**")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.markdown(f"""
                <div class="card-box">
                    <p><b>Název firmy:</b> {moje_firma['nazev_firmy']}</p>
                    <p><b>Právní forma:</b> Studentská firma M-TECH CORE</p>
                    <p><b>Stav licence:</b> {moje_firma['stave_licence']}</p>
                    <p><b>Zvolená úroveň:</b> Úroveň {moje_firma['uroven_projektu']}</p>
                    <hr style="border-color:#334155;">
                    <p><b>CEO (Generální ředitel):</b> {moje_firma['ceo_jmeno']}</p>
                    <p><b>CFO (Finanční ředitel):</b> {moje_firma['cfo_jmeno']}</p>
                    <p><b>CTO (Technický ředitel):</b> {moje_firma['cto_jmeno']}</p>
                </div>
            """, unsafe_allow_html=True)
        with col_f2:
            st.markdown(f"""
                <div class="card-box">
                    <p><b>Podnikatelský záměr:</b> {moje_firma['podnikatelsky_zamer']}</p>
                    <p><b>Kód školy:</b> {moje_firma['skolni_kod']}</p>
                    <p><b>Počáteční vklad celkem:</b> {moje_firma['pocatecni_kapital']} M-Kreditů</p>
                    <p><b>Datum podání:</b> {moje_firma.get('datum_vzniku', '')[:10]}</p>
                </div>
            """, unsafe_allow_html=True)
            
        if moje_firma['stave_licence'] == "ZAMITNUTO":
            if st.button("Znovupodat žádost ke schválení", icon=":material/refresh:"):
                requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{moje_firma['id']}", headers=headers, json={"stave_licence": "CEKA_NA_SCHVALENI"})
                st.success("Žádost byla znovu odeslána na Úřad!")
                st.rerun()

    else:
        st.info("Vyplňte zakladatelské náležitosti podle Přílohy č. 2 metodiky M-TECH CORE.")
        with st.form("form_zakladatel"):
            col_z1, col_z2 = st.columns(2)
            with col_z1:
                nazev_firmy = st.text_input("Obchodní název firmy (např. Precision Mech s.r.o.):")
                divize = st.selectbox("Oborová Divize:", ["Mechanical (Strojírenství)", "Power (Elektrotechnika)", "Cyber (IT & Software)", "Strategy (Lyceum / Služby)"])
                predmet = st.text_input("Předmět podnikání / Hlavní produkt:")
                skolni_kod = st.text_input("Licenční kód školy:").upper().strip()
                uroven = st.radio("Zvolená úroveň projektu:", [
                    "Úroveň 1: Teoretický start-up (Inkubátor & Prototyp)", 
                    "Úroveň 2: Uzavřený školní trh (Virtuální M-Kredity)", 
                    "Úroveň 3: Plná integrace (Reálná finanční odpovědnost & UR)"
                ])
                
            with col_z2:
                ceo = st.text_input("CEO (Generální ředitel / Statutář):", value=uzivatel)
                cfo = st.text_input("CFO (Finanční ředitel / Správce účtu):")
                cto = st.text_input("CTO (Technický ředitel / Bezpečnost BOZP):")
                vklad_clen = st.number_input("Počáteční vklad na jednoho člena (M-Kredity / CZK):", min_value=10, value=100)
                zamer = st.text_area("Stručný podnikatelský záměr:")

            st.markdown("---")
            st.markdown("**Statutární prohlášení:**")
            prohlaseni_kodex = st.checkbox("Zavazujeme se dodržovat Etický kodex projektu M-TECH CORE a pravidla BOZP v dílnách.")
            prohlaseni_dan = st.checkbox("Zavazujeme se k povinnému odvodu M-TECH daně (15–20 % ze zisku) ve prospěch Fondu rozvoje / Unie rodičů.")

            submit_zaklad = st.form_submit_button("Odeslat Zakladatelskou listinu na Kontrolní úřad", icon=":material/send:")
            
            if submit_zaklad:
                if nazev_firmy and skolni_kod and cfo and cto and prohlaseni_kodex and prohlaseni_dan:
                    u_num = 1 if "Úroveň 1" in uroven else (2 if "Úroveň 2" in uroven else 3)
                    payload = {
                        "nazev_firmy": nazev_firmy,
                        "skolni_kod": skolni_kod,
                        "uroven_projektu": u_num,
                        "ceo_jmeno": ceo,
                        "cfo_jmeno": cfo,
                        "cto_jmeno": cto,
                        "podnikatelsky_zamer": f"[{divize}] {predmet} - {zamer}",
                        "pocatecni_kapital": vklad_clen * 3,
                        "stave_licence": "CEKA_NA_SCHVALENI"
                    }
                    res_post = requests.post(f"{SUPABASE_URL}/rest/v1/firmy", headers=headers, json=payload)
                    if res_post.status_code in [200, 201]:
                        st.success("Zakladatelská listina byla úspěšně odeslána!")
                        st.rerun()
                    else:
                        st.error(f"Chyba při zakládání firmy: {res_post.text}")
                else:
                    st.warning("Vyplňte všechny členy vedení, kód školy a potvrďte obě prohlášení.")

# --- TAB 2: LEAN CANVAS ---
with tab_canvas:
    if not moje_firma:
        st.warning("Nejprve musíte odeslat Zakladatelskou listinu.")
    else:
        st.subheader("Strategický plán (Lean Canvas)")
        with st.form("form_canvas"):
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                prob = st.text_area("1. Problém (Co trh postrádá?):")
                sol = st.text_area("2. Řešení (Co nabízíme?):")
                val = st.text_area("3. Unikátní hodnota (Čím se lišíme?):")
            with col_c2:
                target = st.text_area("4. Cílová skupina (Kdo je zákazník?):")
                costs = st.text_area("5. Nákladová struktura:")
                rev = st.text_area("6. Příjmové toky:")
            
            if st.form_submit_button("Uložit / Aktualizovat Lean Canvas", icon=":material/save:"):
                c_payload = {"firma_id": moje_firma["id"], "problem": prob, "reseni": sol, "cilova_skupina": target, "unikatni_hodnota": val, "nakladova_struktura": costs, "prijmove_toky": rev}
                requests.post(f"{SUPABASE_URL}/rest/v1/lean_canvas", headers=headers, json=c_payload)
                st.success("Lean Canvas uložen!")
                st.rerun()

# --- TAB 3: SAMOSTATNÁ KOLONKA NA ZÁPISY Z PORAD MANAGEMENTU ---
with tab_porady:
    if not moje_firma:
        st.warning("Nejprve musíte odeslat Zakladatelskou listinu.")
    else:
        st.subheader("Zápisy z porad managementu (CEO, CFO, CTO)")
        st.caption("Pravidelná dokumentace týmových porad, rozdělení odpovědností a plnění úkolů.")
        
        with st.form("form_porada"):
            projednano = st.text_area("Projednané body na poradě (Agenda & Problémy):", placeholder="Např. Volba loga, stanovení marže, nákup zkušebního materiálu...")
            ukoly = st.text_area("Rozdělení úkolů a odpovědnost členů týmu:", placeholder="Např. CEO: Tvorba prezentace, CFO: Kalkulační list, CTO: Výrobní výkres...")
            
            if st.form_submit_button("Uložit zápis z porady", icon=":material/post_add:"):
                p_payload = {"firma_id": moje_firma["id"], "projednane_body": projednano, "ukoly_a_odpovednost": ukoly}
                requests.post(f"{SUPABASE_URL}/rest/v1/zapisy_porady", headers=headers, json=p_payload)
                st.success("Zápis z porady byl uložen do databáze!")
                st.rerun()
                
        st.write("---")
        st.caption("Historie odevzdaných zápisů z porad:")
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
        else:
            st.info("Zatím nebyl zapsán žádný protokol z porady.")

# --- TAB 4: KALKULAČNÍ LISTY ---
with tab_kalkulace:
    if not moje_firma:
        st.warning("Nejprve musíte odeslat Zakladatelskou listinu.")
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
        st.warning("Nejprve musíte odeslat Zakladatelskou listinu.")
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
