import streamlit as st
import requests

st.set_page_config(page_title="Firemní Kancelář", page_icon=":material/business:", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #00B4D8; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0, 180, 216, 0.4); border-color: #00B4D8; }
    .card-box { background-color: #1e293b; padding: 20px; border-radius: 10px; border: 1px solid #334155; margin-bottom: 15px; }
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

# Načtení firmy uživatele
res_firma = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?ceo_jmeno=eq.{uzivatel}&select=*", headers=headers)
moje_firma = res_firma.json()[0] if (res_firma.status_code == 200 and len(res_firma.json()) > 0) else None

# Kontrola plnění jednotlivých modulů
has_canvas = False
has_kalkulace = False
has_ucto = False

if moje_firma:
    f_id = moje_firma["id"]
    
    res_c = requests.get(f"{SUPABASE_URL}/rest/v1/lean_canvas?firma_id=eq.{f_id}", headers=headers)
    has_canvas = len(res_c.json()) > 0 if res_c.status_code == 200 else False

    res_k = requests.get(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy?firma_id=eq.{f_id}", headers=headers)
    has_kalkulace = len(res_k.json()) > 0 if res_k.status_code == 200 else False

    res_u = requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?firma_id=eq.{f_id}", headers=headers)
    has_ucto = len(res_u.json()) > 0 if res_u.status_code == 200 else False

    # --- KONTROLNÍ NÁSTĚNKA POVINNOSTÍ FIRMY ---
    st.subheader("📌 Stav plnění metodických kroků M-TECH CORE")
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    
    stav = moje_firma['stave_licence']
    
    with col_s1:
        if stav == "SCHVALENO":
            st.success("✅ Licence udělena")
        elif stav == "CEKA_NA_SCHVALENI":
            st.warning("⏳ Čeká na vyučujícího")
        else:
            st.error("❌ Licence zamítnuta")
            
    with col_s2:
        if has_canvas:
            st.success("✅ Lean Canvas vyplněn")
        else:
            st.info("⚪ Lean Canvas chybí")
            
    with col_s3:
        if has_kalkulace:
            st.success("✅ Kalkulace zadána")
        else:
            st.info("⚪ Kalkulace chybí")
            
    with col_s4:
        if has_ucto:
            st.success("✅ Účetnictví vedené")
        else:
            st.info("⚪ Účetní kniha prázdná")

    # --- PŘEHLEDNÝ HLAVNÍ BANNER STAVU LICENCE ---
    if stav == "CEKA_NA_SCHVALENI":
        st.info("⏳ **Žádost o licencování byla úspěšně odeslána.** Čeká na posouzení vyučujícím (Kontrolním úřadem). Mezitím již můžete v záložkách níže vyplňovat Lean Canvas a připravovat kalkulace produktů!")
    elif stav == "ZAMITNUTO":
        st.error(f"❌ **ŽÁDOST O LICENCI BYLA ZAMÍTNUTA**\n\n**Důvod od Kontrolního úřadu:**\n> {moje_firma.get('duvod_zamitnuti', 'Není uveden')}\n\nOpravte potřebné věci a klikněte na tlačítko 'Znovupodat žádost' níže.")
    elif stav == "SCHVALENO":
        st.success("🎉 **LICENCE JE AKTIVNÍ!** Vaše firma je plně registrovaná a schválená k podnikání na trhu.")

    st.write("---")

tab_zaklad, tab_strategie, tab_kalkulace, tab_ucto = st.tabs([
    "📜 1. Zakladatelská listina", 
    "🧠 2. Lean Canvas & Porady", 
    "🧮 3. Kalkulační listy produktů", 
    "📊 4. Kniha příjmů a výdajů"
])

# --- TAB 1: ZAKLADATELSKÁ LISTINA ---
with tab_zaklad:
    st.subheader("Zakladatelská listina a Žádost o licenci")
    
    if moje_firma:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.markdown(f"""
                <div class="card-box">
                    <p><b>Název firmy:</b> {moje_firma['nazev_firmy']}</p>
                    <p><b>Stav licence:</b> {moje_firma['stave_licence']}</p>
                    <p><b>Úroveň projektu:</b> Level {moje_firma['uroven_projektu']}</p>
                    <p><b>Generální ředitel (CEO):</b> {moje_firma['ceo_jmeno']}</p>
                    <p><b>Finanční ředitel (CFO):</b> {moje_firma['cfo_jmeno']}</p>
                    <p><b>Technický ředitel (CTO):</b> {moje_firma['cto_jmeno']}</p>
                </div>
            """, unsafe_allow_html=True)
        with col_f2:
            st.markdown(f"""
                <div class="card-box">
                    <p><b>Podnikatelský záměr:</b> {moje_firma['podnikatelsky_zamer']}</p>
                    <p><b>Počáteční vklad:</b> {moje_firma['pocatecni_kapital']} M-Kreditů</p>
                    <p><b>Kód školy:</b> {moje_firma['skolni_kod']}</p>
                </div>
            """, unsafe_allow_html=True)
            
        if moje_firma['stave_licence'] == "ZAMITNUTO":
            if st.button("🔄 Znovupodat žádost ke schválení"):
                requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{moje_firma['id']}", headers=headers, json={"stave_licence": "CEKA_NA_SCHVALENI"})
                st.success("Žádost byla znovu odeslána na Úřad!")
                st.rerun()

    else:
        st.info("Vaše firma ještě nemá podanou Zakladatelskou listinu. Vyplňte formulář níže.")
        with st.form("form_zakladatel"):
            nazev_firmy = st.text_input("Název firmy (např. MechTech s.r.o.):")
            skolni_kod = st.text_input("Licenční kód školy:").upper().strip()
            uroven = st.selectbox("Zvolená úroveň projektu:", [1, 2, 3])
            ceo = st.text_input("Jméno CEO (Generální ředitel):", value=uzivatel)
            cfo = st.text_input("Jméno CFO (Finanční ředitel):")
            cto = st.text_input("Jméno CTO (Technický ředitel):")
            zamer = st.text_area("Stručný podnikatelský záměr:")
            kapital = st.number_input("Počáteční vklad v M-Kreditech na člena:", value=100)
            
            submit_zaklad = st.form_submit_button("Odeslat Zakladatelskou listinu na Kontrolní úřad")
            
            if submit_zaklad:
                if nazev_firmy and skolni_kod and cfo and cto:
                    payload = {
                        "nazev_firmy": nazev_firmy,
                        "skolni_kod": skolni_kod,
                        "uroven_projektu": uroven,
                        "ceo_jmeno": ceo,
                        "cfo_jmeno": cfo,
                        "cto_jmeno": cto,
                        "podnikatelsky_zamer": zamer,
                        "pocatecni_kapital": kapital * 3,
                        "stave_licence": "CEKA_NA_SCHVALENI"
                    }
                    res_post = requests.post(f"{SUPABASE_URL}/rest/v1/firmy", headers=headers, json=payload)
                    if res_post.status_code in [200, 201]:
                        st.success("Zakladatelská listina odeslána!")
                        st.rerun()
                    else:
                        st.error(f"Chyba při zakládání firmy: {res_post.text}")
                else:
                    st.warning("Vyplňte všechny členy vedení i kód školy.")

# --- TAB 2: LEAN CANVAS & PORADY ---
with tab_strategie:
    if not moje_firma:
        st.warning("Nejprve musíte vytvořit Zakladatelskou listinu.")
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
            
            if st.form_submit_button("Uložit Lean Canvas"):
                c_payload = {"firma_id": moje_firma["id"], "problem": prob, "reseni": sol, "cilova_skupina": target, "unikatni_hodnota": val, "nakladova_struktura": costs, "prijmove_toky": rev}
                requests.post(f"{SUPABASE_URL}/rest/v1/lean_canvas", headers=headers, json=c_payload)
                st.success("Lean Canvas byl úspěšně uložen!")
                st.rerun()

# --- TAB 3: KALKULAČNÍ LISTY ---
with tab_kalkulace:
    if not moje_firma:
        st.warning("Nejprve musíte vytvořit Zakladatelskou listinu.")
    else:
        st.subheader("Návrh nového produktu a Kalkulační vzorec")
        with st.form("form_kalkulace"):
            prod_nazev = st.text_input("Název produktu / služby:")
            p_naklady = st.number_input("Přímé náklady (materiál) v M-Kreditech:", min_value=0.0, value=35.0)
            rezie = st.number_input("Virtuální režie školy v M-Kreditech:", min_value=0.0, value=10.0)
            marze = st.number_input("Plánovaná marže v M-Kreditech:", min_value=0.0, value=50.0)
            dan_pct = st.number_input("M-TECH Daň (%):", min_value=10.0, max_value=30.0, value=15.0)
            
            zaklad_dane = p_naklady + rezie + marze
            vypoctena_dan = zaklad_dane * (dan_pct / 100.0)
            doporucena_cena = zaklad_dane + vypoctena_dan
            
            st.markdown(f"**M-TECH daň:** `{vypoctena_dan:.2f} M-K` | **Prodejní cena:** `{doporucena_cena:.2f} M-Kreditů`")
            
            if st.form_submit_button("Odeslat kalkulační list ke schválení"):
                k_payload = {"firma_id": moje_firma["id"], "nazev_produktu": prod_nazev, "prime_naklady": p_naklady, "rezie_skoly": rezie, "mtech_dan_procento": dan_pct, "marze_zisk": marze, "konecna_cena": doporucena_cena, "schvaleno_uradem": False}
                requests.post(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy", headers=headers, json=k_payload)
                st.success("Kalkulační list odeslán!")
                st.rerun()

# --- TAB 4: KNIHA PŘÍJMŮ A VÝDAJŮ ---
with tab_ucto:
    if not moje_firma:
        st.warning("Nejprve musíte vytvořit Zakladatelskou listinu.")
    else:
        st.subheader("Kniha příjmů a výdajů (Cash-flow)")
        with st.form("form_transakce"):
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1: typ = st.selectbox("Typ zápisu:", ["PRIJEM", "VYDAJ"])
            with col_t2: titul = st.text_input("Titul:", value="Nákup materiálu")
            with col_t3: castka = st.number_input("Částka v M-Kreditech:", min_value=1.0, value=50.0)
                
            if st.form_submit_button("Zapsat do účetní knihy"):
                t_payload = {"firma_id": moje_firma["id"], "typ_transakce": typ, "titul": titul, "castka": castka, "auditovano": False}
                requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json=t_payload)
                st.success("Zapsáno!")
                st.rerun()
                
        res_kniha = requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?firma_id=eq.{moje_firma['id']}&order=datum.desc", headers=headers)
        if res_kniha.status_code == 200 and len(res_kniha.json()) > 0:
            st.dataframe(res_kniha.json(), use_container_width=True)
