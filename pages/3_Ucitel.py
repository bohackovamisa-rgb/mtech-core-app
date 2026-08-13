import streamlit as st
import requests
import pandas as pd
import json

st.set_page_config(page_title="Kontrolní úřad a Audit", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3, h4 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #00B4D8; width: 100%; font-weight: 600; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0, 180, 216, 0.4); border-color: #00B4D8; background-color: #0f172a; color: white;}
    .card-box { background-color: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 15px; }
    .status-ok { color: #34d399; font-weight: 700; background: rgba(16, 185, 129, 0.1); padding: 4px 8px; border-radius: 6px; }
    .status-wait { color: #fbbf24; font-weight: 700; background: rgba(245, 158, 11, 0.1); padding: 4px 8px; border-radius: 6px; }
    .status-err { color: #f87171; font-weight: 700; background: rgba(239, 68, 68, 0.1); padding: 4px 8px; border-radius: 6px; }
    .asset-link { color: #00B4D8; font-weight: bold; text-decoration: none; }
    .asset-link:hover { text-decoration: underline; color: #0077B6; }
    details { background: rgba(255,255,255,0.05); padding: 10px; border-radius: 5px; margin-top: 10px; }
    summary { font-weight: bold; cursor: pointer; color: #00B4D8; }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.get("prihlasen") or str(st.session_state.get("role")).upper() not in ["UCITEL", "ADMIN"]:
    st.error("Přístup odepřen. Sekce pouze pro administrátory a vyučující.")
    st.stop()

st.title("Kontrolní úřad a Audit")

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}
except Exception:
    st.error("Chybí konfigurace databáze.")
    st.stop()

res_ucitel = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{st.session_state.uzivatel}", headers=headers).json()
skolni_kod_ucitele = res_ucitel[0].get("skolni_kod", "") if res_ucitel else ""

res_firmy = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?select=*&order=id.desc", headers=headers).json()
firmy = res_firmy if res_firmy else []

if not firmy:
    st.info("V systému zatím nejsou žádné studentské entity.")
    st.stop()

vybrana_firma_nazev = st.selectbox("Vyberte startup k auditu:", [f["nazev_firmy"] for f in firmy])
firma = next(f for f in firmy if f["nazev_firmy"] == vybrana_firma_nazev)
f_id = firma["id"]

tab_legal, tab_aktiva, tab_hr, tab_finance, tab_questy, tab_stat, tab_banka, tab_krize, tab_hodnoceni = st.tabs([
    "1. Spis", "2. Vize a AI", "3. HR", "4. E-shop a Zákazníci", "5. Úřad práce a XP", "6. Státní pokladna a Daně", "7. Banka a Ceník", "8. Krizové řízení", "9. Přehled a Hodnocení"
])
])

# ==========================================
# ZÁLOŽKA 1: SPIS
# ==========================================
with tab_legal:
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        # Načtení řadových zaměstnanců z databáze
        res_zamestnanci = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?firma_id=eq.{f_id}", headers=headers).json()
        seznam_zamestnancu = ", ".join([z['jmeno_zamestnance'] for z in res_zamestnanci]) if res_zamestnanci else "Žádní další zaměstnanci"
        
        # Ošetření, pokud firma nemá CFO nebo CTO
        cfo_text = f"<br><b>CFO:</b> {firma['cfo_jmeno']}" if firma.get('cfo_jmeno') else ""
        cto_text = f"<br><b>CTO:</b> {firma['cto_jmeno']}" if firma.get('cto_jmeno') else ""
        
        st.markdown(f"""
        <div class='card-box'>
            <h4>Management a Tým</h4>
            <p style='margin-bottom: 8px;'><b>Kód:</b> {firma.get('skolni_kod', '')}</p>
            <p style='margin-bottom: 8px; color: #cbd5e1;'>
                <b>Zakladatelé (Vedení):</b><br>
                <b>CEO:</b> {firma.get('ceo_jmeno', '')}{cfo_text}{cto_text}
            </p>
            <p style='margin-bottom: 0; color: #cbd5e1;'>
                <b>Zaměstnanci (HR):</b><br>
                {seznam_zamestnancu}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_l2:
        st.markdown(f"<div class='card-box'><h4>Stav licence: <span class='{'status-ok' if firma['stave_licence'] == 'SCHVALENO' else 'status-wait'}'>{firma['stave_licence']}</span></h4></div>", unsafe_allow_html=True)
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Schválit zápis do rejstříku"):
            requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{f_id}", headers=headers, json={"stave_licence": "SCHVALENO", "duvod_zamitnuti": ""})
            st.rerun()
    with col_btn2:
        with st.popover("Zamítnout a vrátit k přepracování"):
            duvod = st.text_area("Odůvodnění zamítnutí:")
            if st.button("Potvrdit zamítnutí"):
                requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{f_id}", headers=headers, json={"stave_licence": "ZAMITNUTO", "duvod_zamitnuti": duvod})
                st.rerun()

# ==========================================
# ZÁLOŽKA 2: VIZE A AI (LEAN CANVAS + SHARK TANK)
# ==========================================
with tab_aktiva:
    canvas = requests.get(f"{SUPABASE_URL}/rest/v1/lean_canvas?firma_id=eq.{f_id}", headers=headers).json()
    
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.markdown("#### Digitální aktiva")
        if firma.get('logo_url'): st.markdown(f"<a href='{firma['logo_url']}' class='asset-link' target='_blank'>Firemní Logo</a>", unsafe_allow_html=True)
        if firma.get('web_url'): st.markdown(f"<a href='{firma['web_url']}' class='asset-link' target='_blank'>Webové stránky</a>", unsafe_allow_html=True)
    
    with col_a2:
        st.markdown("#### Strategie")
        if canvas:
            with st.expander("Detail Lean Canvasu (8 bloků)"):
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    st.write("**1. Problém:**", canvas[0].get('problem', ''))
                    st.write("**3. Cílová skupina:**", canvas[0].get('cilova_skupina', ''))
                    st.write("**5. Kanály:**", canvas[0].get('kanaly', ''))
                    st.write("**7. Náklady:**", canvas[0].get('naklady', ''))
                with col_c2:
                    st.write("**2. Řešení:**", canvas[0].get('reseni', ''))
                    st.write("**4. Unikátní hodnota:**", canvas[0].get('hodnota', ''))
                    st.write("**6. Nefér výhoda:**", canvas[0].get('vyhoda', ''))
                    st.write("**8. Příjmy:**", canvas[0].get('prijmy', ''))
        else:
            st.info("Firma zatím nedodala Lean Canvas.")
    
    st.write("---")
    st.markdown("#### Historie AI Shark Tank (Pitching)")
    st.caption("Náhled toho, jak se firma prezentovala před umělou inteligencí.")
    
    res_pitches = requests.get(f"{SUPABASE_URL}/rest/v1/ai_pitches?firma_id=eq.{f_id}&order=datum.desc", headers=headers).json()
    if res_pitches:
        for p in res_pitches:
            stav = "SCHVÁLENO" if p['schvaleno_investovano'] else "ZAMÍTNUTO"
            barva = "status-ok" if p['schvaleno_investovano'] else "status-err"
            st.markdown(f"""
            <div class='card-box'>
                <h5>Projekt: {p['nazev_pitchu']} <span class='{barva}' style='float: right;'>{stav}</span></h5>
                <p><b>Požadováno:</b> {p['zadana_castka']} M-K za {p['nabizene_akcie']} ks akcií</p>
                <p style="background: rgba(0,0,0,0.2); padding: 10px; border-left: 3px solid #00B4D8;">
                    <b>Pitch žáků:</b><br>
                    <i>"{p['popis_projektu']}"</i>
                </p>
                <details>
                    <summary>Rozbalit verdikt AI investorů</summary>
                    <p>{p['hodnoceni_ostry']}</p>
                    <p>{p['hodnoceni_vizionarka']}</p>
                    <p>{p['hodnoceni_rychly']}</p>
                </details>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Firma zatím před investory nevystoupila.")

# ==========================================
# ZÁLOŽKA 3: HR
# ==========================================
with tab_hr:
    st.markdown("#### Mzdový a personální audit")
    zamestnanci = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?firma_id=eq.{f_id}", headers=headers).json()
    if zamestnanci:
        df_zam = pd.DataFrame(zamestnanci)[['jmeno_zamestnance', 'pozice', 'hodinova_sazba', 'vyplaceno_celkem']]
        st.dataframe(df_zam, use_container_width=True)
    else: 
        st.info("Firma zatím neeviduje žádné zaměstnance.")

# ==========================================
# ZÁLOŽKA 4: E-SHOP + ZÁKAZNICKÁ PODPORA
# ==========================================
with tab_finance:
    st.markdown("#### Schvalování produktů pro Tržiště")
    kalkulace = requests.get(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy?firma_id=eq.{f_id}", headers=headers).json()
    if kalkulace:
        for k in kalkulace:
            barva = "status-ok" if k['schvaleno_uradem'] else "status-wait"
            st.markdown(f"<div class='card-box'><h5>{k['nazev_produktu']} <span class='{barva}'>{'Aktivní' if k['schvaleno_uradem'] else 'Čeká na kontrolu'}</span></h5><p>Koncová cena pro trh: {k['konecna_cena']} M-K</p></div>", unsafe_allow_html=True)
            if not k['schvaleno_uradem']:
                if st.button(f"Schválit kalkulaci: {k['nazev_produktu']}", key=f"kalk_{k['id']}"):
                    requests.patch(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy?id=eq.{k['id']}", headers=headers, json={"schvaleno_uradem": True})
                    st.rerun()
    else:
        st.info("Žádné kalkulace ke schválení.")

    st.write("---")
    st.markdown("#### AI Zákaznická podpora (Reklamace)")
    st.caption("Zde vidíte, jak žáci komunikují se zákazníky a řeší stížnosti.")
    
    reklamace_list = requests.get(f"{SUPABASE_URL}/rest/v1/ai_reklamace?firma_id=eq.{f_id}&order=datum.desc", headers=headers).json()
    if reklamace_list:
        for r in reklamace_list:
            stav = "VYŘEŠENO" if r['vysledek'] in ['SCHVALENO', 'ZAMITNUTO_POKUTA'] else "NEODPOVĚZENO"
            barva = "status-ok" if r['vysledek'] == 'SCHVALENO' else ("status-err" if r['vysledek'] == 'ZAMITNUTO_POKUTA' else "status-wait")
            
            st.markdown(f"""
            <div class='card-box'>
                <h5>Stěžovatel: {r['zakaznik_jmeno']} <span class='{barva}' style='float: right;'>{stav}</span></h5>
                <p><b>Stížnost:</b> <i>"{r['text_stiznosti']}"</i></p>
                <p style="background: rgba(0,0,0,0.2); padding: 10px; border-left: 3px solid {'#10b981' if r['vysledek'] == 'SCHVALENO' else '#f43f5e'};">
                    <b>Odpověď firmy:</b><br>
                    {r.get('odpoved_firmy') if r.get('odpoved_firmy') else '<i>Zatím bez odpovědi.</i>'}
                </p>
                <p><b>Verdikt AI a dopad:</b> {r.get('hodnoceni_ai', 'Čeká se na reakci firmy')}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Firma zatím neměla žádné reklamace.")

    st.write("---")
    with st.expander("Účetní audit a kniha transakcí (Zobrazit)"):
        ucto = requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?firma_id=eq.{f_id}&order=datum.desc", headers=headers).json()
        if ucto:
            neauditovane = [u for u in ucto if not u['auditovano']]
            if neauditovane:
                if st.button("Provést hromadný audit (Schválit transakce)"):
                    for u in neauditovane: requests.patch(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?id=eq.{u['id']}", headers=headers, json={"auditovano": True})
                    st.rerun()
            df_show = pd.DataFrame(ucto)[['datum', 'typ_transakce', 'titul', 'castka', 'auditovano']]
            st.dataframe(df_show, use_container_width=True)
        else:
            st.info("Kniha transakcí je zatím prázdná.")

# ==========================================
# ZÁLOŽKA 5: ÚŘAD PRÁCE
# ==========================================
with tab_questy:
    st.subheader("Správa úkolů a přidělování XP bodů")
    
    with st.expander("Rychlé vypsání předpřipravených školních úkolů"):
        st.caption("Kliknutím na tlačítko okamžitě vypsat standardní školní úkol pro žáky bez firmy.")
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            if st.button("Vypsat: Úklid a organizace dílny"):
                requests.post(f"{SUPABASE_URL}/rest/v1/questy", headers=headers, json={"nazev": "Úklid a organizace 3D dílny", "popis": "Rovnání filamentů, úklid pracovního stolu a kontrola stavu tiskáren.", "odmena": 25.0, "zadavatel": st.session_state.uzivatel, "stav": "VOLNY"})
                st.success("Úkol vypsán!")
                st.rerun()
        with col_s2:
            if st.button("Vypsat: PR a Foto ze školní akce"):
                requests.post(f"{SUPABASE_URL}/rest/v1/questy", headers=headers, json={"nazev": "Fotodokumentace a PR článek", "popis": "Nafocení fotek ze školní akce a napsání kratičkého článku na web.", "odmena": 35.0, "zadavatel": st.session_state.uzivatel, "stav": "VOLNY"})
                st.success("Úkol vypsán!")
                st.rerun()
        with col_s3:
            if st.button("Vypsat: Pomoc s Dnem otevřených dveří"):
                requests.post(f"{SUPABASE_URL}/rest/v1/questy", headers=headers, json={"nazev": "Průvodce na Dni otevřených dveří", "popis": "Aktivní prezentace školních projektů a provádění návštěvníků.", "odmena": 50.0, "zadavatel": st.session_state.uzivatel, "stav": "VOLNY"})
                st.success("Úkol vypsán!")
                st.rerun()

    st.write("---")
    col_q1, col_q2 = st.columns(2)
    with col_q1:
        with st.form("new_quest"):
            q_nazev = st.text_input("Vlastní název zakázky / úkolu:")
            q_popis = st.text_area("Rozsah práce:")
            q_odmena = st.number_input("Odměna (M-K):", min_value=1.0, value=20.0)
            if st.form_submit_button("Vypsat vlastní úkol"):
                requests.post(f"{SUPABASE_URL}/rest/v1/questy", headers=headers, json={"nazev": q_nazev, "popis": q_popis, "odmena": q_odmena, "zadavatel": st.session_state.uzivatel, "stav": "VOLNY"})
                st.rerun()
    with col_q2:
        st.markdown("#### Práce ke kontrole")
        res_q_check = requests.get(f"{SUPABASE_URL}/rest/v1/questy?stav=eq.K_KONTROLE", headers=headers).json()
        if res_q_check:
            for q in res_q_check:
                st.markdown(f"<div class='card-box'><h5>{q['nazev']}</h5><p>Zhotovitel: {q['resitel']} <br> <a href='{q['odkaz_vystup']}' target='_blank'>Výstup k posouzení</a></p></div>", unsafe_allow_html=True)
                with st.form(f"schvaleni_{q['id']}"):
                    kategorie_xp = st.selectbox("Typ XP bodů:", ["IT a Technologie", "Marketing a Kreativita", "Byznys a Finance"])
                    pocet_xp = st.number_input("Počet XP:", min_value=0, max_value=50, value=10)
                    if st.form_submit_button("Schválit úkol a odeslat odměny"):
                        res_r = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{q['resitel']}", headers=headers).json()
                        if res_r: 
                            z_data = res_r[0]
                            nove_kredity = z_data['kredity'] + q['odmena']
                            xp_col = "xp_it" if kategorie_xp == "IT a Technologie" else "xp_marketing" if kategorie_xp == "Marketing a Kreativita" else "xp_byznys"
                            nove_xp = z_data.get(xp_col, 0) + pocet_xp
                            requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{q['resitel']}", headers=headers, json={"kredity": nove_kredity, xp_col: nove_xp})
                        
                        requests.patch(f"{SUPABASE_URL}/rest/v1/questy?id=eq.{q['id']}", headers=headers, json={"stav": "DOKONCENO"})
                        requests.post(f"{SUPABASE_URL}/rest/v1/bankovni_prevody", headers=headers, json={"odesilatel": "Stát", "prijemce": q['resitel'], "castka": q['odmena'], "ucel": f"Odměna za: {q['nazev']} (+ {pocet_xp} XP)"})
                        st.success("Odměna i XP body odeslány!")
                        st.rerun()
        else: st.info("Žádné úkoly nečekají na schválení.")

# ==========================================
# ZÁLOŽKA 6: STÁTNÍ POKLADNA A AI DAŇOVÝ AUDIT
# ==========================================
with tab_stat:
    st.subheader("Státní pokladna a Daňové audity")
    res_stat = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers).json()
    stat_kredity = res_stat[0]['kredity'] if res_stat else 0
    # Zde je oprava - pridano -webkit-text-fill-color: white; a background: none; do H3 tagu!
    st.markdown(f"<div class='card-box' style='text-align: center; background: linear-gradient(135deg, #0ea5e9 0%, #0369a1 100%); border: none;'><h3 style='background: none; -webkit-text-fill-color: white; font-weight: 400; margin-bottom: 5px;'>Vybrané daně a poplatky v rozpočtu</h3><h1 style='background: none; -webkit-text-fill-color: white; margin: 0; font-size: 3em;'>{stat_kredity:.2f} M-K</h1></div>", unsafe_allow_html=True)

    with st.form("form_dotace"):
        vybrana_dotace_firma = st.selectbox("Příjemce grantu (Firma):", [f["nazev_firmy"] for f in firmy])
        castka_dotace = st.number_input("Výše grantu (M-K):", min_value=1.0, value=100.0)
        ucel_dotace = st.text_input("Účel grantu:", value="Státní podpora inovací")
        if st.form_submit_button("Schválit dotační program"):
            if castka_dotace > stat_kredity: st.error("Nedostatek prostředků ve státní pokladně.")
            else:
                firma_prijemce = next((f for f in firmy if f["nazev_firmy"] == vybrana_dotace_firma), None)
                if firma_prijemce:
                    requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers, json={"kredity": stat_kredity - castka_dotace})
                    r_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{firma_prijemce['ceo_jmeno']}", headers=headers).json()
                    if r_ceo: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{firma_prijemce['ceo_jmeno']}", headers=headers, json={"kredity": r_ceo[0]['kredity'] + castka_dotace})
                    requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": firma_prijemce["id"], "typ_transakce": "PRIJEM", "titul": f"Státní dotace: {ucel_dotace}", "castka": castka_dotace, "auditovano": True})
                    st.rerun()

    st.write("---")
    st.markdown("#### Audit odevzdaných daňových přiznání")
    st.caption("Nechte umělou inteligenci zkontrolovat účetnictví firmy. AI inspektor odhalí případné krácení daně a vyměří pokutu.")
    
    priznani_list = requests.get(f"{SUPABASE_URL}/rest/v1/danova_priznani?stav=eq.ODEVZDANO&order=datum.desc", headers=headers).json()

    if priznani_list:
        for p in priznani_list:
            f_info = next((f for f in firmy if f['id'] == p['firma_id']), None)
            f_nazev = f_info['nazev_firmy'] if f_info else f"Firma #{p['firma_id']}"

            kniha = requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?firma_id=eq.{p['firma_id']}&typ_transakce=eq.PRIJEM", headers=headers).json()
            celkem_prijmy = sum(item['castka'] for item in kniha) if kniha else 0

            sk_kod = f_info.get('skolni_kod', 'SYSTEM') if f_info else 'SYSTEM'
            nast_res = requests.get(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{sk_kod}", headers=headers).json()
            sazba_dan = float(nast_res[0].get('mtech_dan_pct', 15.0)) if nast_res else 15.0

            pozadovana_dan = celkem_prijmy * (sazba_dan / 100.0)

            st.markdown(f"""
                <div class='card-box'>
                    <h5>Daňové přiznání: {f_nazev}</h5>
                    <p>
                    • Přiznaná daň firmou: <b>{p['dane_priznane']:.2f} M-K</b><br>
                    • Evidované příjmy v účetnictví: <b>{celkem_prijmy:.2f} M-K</b><br>
                    • Vypočtená povinná daň ({sazba_dan} %): <b>{pozadovana_dan:.2f} M-K</b>
                    </p>
                </div>
            """, unsafe_allow_html=True)

            gemini_key = st.secrets.get("GEMINI_API_KEY", "")
            if st.button(f"Spustit AI Daňový Audit (Zkontrolovat přiznání #{p['id']})", key=f"ai_audit_{p['id']}"):
                with st.spinner("AI Inspektor Klement Neúprosný kontroluje účetnictví..."):
                    vysledek_status = "SCHVALENO" if abs(pozadovana_dan - p['dane_priznane']) <= 1 else "ZAMITNUTO_PENALE"
                    rozdil = max(0, pozadovana_dan - p['dane_priznane'])
                    vymere_penale = rozdil + 50.0 if vysledek_status == "ZAMITNUTO_PENALE" else 0.0
                    zprava = "Přiznání je v pořádku. Daň byla odvedena správně." if vysledek_status == "SCHVALENO" else f"Bylo zjištěno krácení daně. Vyměřuji doplatek a pokutu ve výši {vymere_penale} M-K."

                    if gemini_key:
                        try:
                            g_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
                            prompt_text = f"""Jsi přísný AI Daňový inspektor (Klement Neúprosný).
                            Firma {f_nazev} podala daňové přiznání.
                            Celkové příjmy dle účetnictví: {celkem_prijmy:.2f} M-K. Daňová sazba: {sazba_dan} %.
                            Správná daň má být: {pozadovana_dan:.2f} M-K. Firma zaplatila: {p['dane_priznane']:.2f} M-K.
                            
                            Pokud zaplatili správně (odchylka do 1 M-K je ok), schval to. 
                            Pokud zaplatili méně, nekompromisně to zamítni a vyměř penále: rozdil + fixní pokuta 50.
                            
                            Odpověz VÝHRADNĚ ve formátu JSON s těmito třemi klíči:
                            {{ "status": "SCHVALENO" nebo "ZAMITNUTO_PENALE", "zprava": "Krátká úřední zpráva", "vymere_penale": číslo }}"""
                            
                            p_load = {"contents": [{"parts": [{"text": prompt_text}]}], "generationConfig": {"response_mime_type": "application/json"}}
                            res_ai = requests.post(g_url, json=p_load, timeout=10).json()
                            data_ai = json.loads(res_ai['candidates'][0]['content']['parts'][0]['text'])

                            vysledek_status = data_ai.get("status", vysledek_status)
                            zprava = data_ai.get("zprava", zprava)
                            vymere_penale = float(data_ai.get("vymere_penale", vymere_penale))
                        except Exception:
                            pass

                    if vysledek_status == "SCHVALENO":
                        requests.patch(f"{SUPABASE_URL}/rest/v1/danova_priznani?id=eq.{p['id']}", headers=headers, json={"stav": "SCHVALENO"})
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": p['firma_id'], "typ_transakce": "PRIJEM", "titul": f"INFO OD FÚ: {zprava}", "castka": 0, "auditovano": True})
                        st.success(f"Inspektor: {zprava}")
                    else:
                        if f_info:
                            r_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{f_info['ceo_jmeno']}", headers=headers).json()
                            if r_ceo:
                                kredity = r_ceo[0]['kredity']
                                requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{f_info['ceo_jmeno']}", headers=headers, json={"kredity": max(0, kredity - vymere_penale)})
                            
                            requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers, json={"kredity": stat_kredity + vymere_penale})
                            requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": p['firma_id'], "typ_transakce": "VYDAJ", "titul": f"PENÁLE OD FÚ: {zprava}", "castka": vymere_penale, "auditovano": True})
                        requests.patch(f"{SUPABASE_URL}/rest/v1/danova_priznani?id=eq.{p['id']}", headers=headers, json={"stav": "ZAMITNUTO_PENALE"})
                        st.error(f"Inspektor: {zprava} (Strženo {vymere_penale} M-K)")
                    
                    st.rerun()
    else:
        st.info("Žádné firmy momentálně nečekají na daňový audit.")

# ==========================================
# ZÁLOŽKA 7: BANKA, CENÍK A BURZOVNÍ DOHLED
# ==========================================
with tab_banka:
    st.subheader("Centrální Banka a Dozor nad Burzou")
    col_cb1, col_cb2 = st.columns(2)
    
    target_skola = skolni_kod_ucitele or firma.get('skolni_kod', '') or 'SYSTEM'
    nastaveni_res = requests.get(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{target_skola}", headers=headers).json()
    akt_nastaveni = nastaveni_res[0] if nastaveni_res else {}
    
    with col_cb1:
        st.markdown("#### Nastavení ekonomiky školy")
        with st.form("form_makro"):
            st.caption(f"Pravidla platná pro školní kód: **{target_skola}**")
            n_kurz = st.number_input("Kurz M-Kreditu k CZK (1 M-K = X Kč):", min_value=1.0, value=float(akt_nastaveni.get('kurz_kc', 10.0)))
            n_zak = st.number_input("Startovací kredit pro ŽÁKA (M-K):", value=float(akt_nastaveni.get('start_kredit_zak', 100)))
            n_firma = st.number_input("Startovací kredit pro FIRMU (M-K):", value=float(akt_nastaveni.get('start_kredit_firma', 300)))
            n_dan = st.number_input("M-TECH Daň pro e-shop (% z prodeje):", min_value=0.0, max_value=50.0, value=float(akt_nastaveni.get('mtech_dan_pct', 15.0)))
            n_dan_prijem = st.number_input("Daň z příjmu zaměstnanců (% ze mzdy):", min_value=0.0, max_value=50.0, value=float(akt_nastaveni.get('dan_prijem_pct', 15.0)))
            n_cenik = st.text_area("Ceník pro výpočet nákladů:", value=str(akt_nastaveni.get('globalni_cenik', '')), height=200)
            
            if st.form_submit_button("Uložit makroekonomická pravidla"):
                requests.patch(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{target_skola}", headers=headers, json={
                    "start_kredit_zak": n_zak, "start_kredit_firma": n_firma, "kurz_kc": n_kurz,
                    "globalni_cenik": n_cenik, "mtech_dan_pct": n_dan, "dan_prijem_pct": n_dan_prijem
                })
                st.success("Ekonomika byla úspěšně uložena!")
                st.rerun()

    with col_cb2:
        st.markdown("#### 📰 Ovlivňování nálady na trhu (AI News)")
        st.caption("Kliknutím vygenerujete zprávu z trhu, kterou uvidí všechny firmy. Zpráva vznikne na základě aktuálních krizí a dění.")
        gemini_key = st.secrets.get("GEMINI_API_KEY", "")
        
        if st.button("Vygenerovat AI Burzovní zprávu", type="primary"):
            with st.spinner("Zjišťuji dostupné AI modely a generuji zprávu (může to chvíli trvat)..."):
                if gemini_key:
                    try:
                        list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_key}"
                        models_data = requests.get(list_url, timeout=30).json()
                        
                        dostupne_modely = []
                        if "models" in models_data:
                            for m in models_data["models"]:
                                if "generateContent" in m.get("supportedGenerationMethods", []):
                                    nazev = m["name"].replace("models/", "")
                                    if "flash" in nazev and "vision" not in nazev and "audio" not in nazev:
                                        dostupne_modely.insert(0, nazev)
                                    else:
                                        dostupne_modely.append(nazev)
                        
                        if not dostupne_modely:
                            dostupne_modely = ["gemini-3.5-flash", "gemini-3.0-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
                        
                        krize_text = akt_nastaveni.get('krize_popis', '')
                        if not krize_text: 
                            krize_text = 'Na trzích je klid, žádná makroekonomická krize neprobíhá.'

                        prompt = f"""Jsi finanční reportér na Wall Street v M-TECH (školní byznys simulátor, kde žáci řídí startupy a obchodují ve virtuální měně M-Kredit). 
                        Na trhu se právě stalo toto: {krize_text}
                        Napiš stručný, úderný finanční článek (1 věta titulek, 2 věty text), který komentuje dopad této události na studentské firmy a investory. 
                        Pravidlo: NEPIŠ o známkách, učitelích ani školních testech, piš jako skutečný reportér z Forbesu nebo Bloombergu.
                        Odpověz VÝHRADNĚ jako čistý JSON objekt: {{"titulek": "...", "text_zpravy": "..."}}"""
                        
                        p_load = {"contents": [{"parts": [{"text": prompt}]}]}
                        
                        uspesna_odpoved = None
                        chyba_msg = ""
                        pouzity_model = ""
                        
                        for model in dostupne_modely:
                            g_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
                            res = requests.post(g_url, json=p_load, timeout=30).json()
                            if 'error' not in res:
                                uspesna_odpoved = res
                                pouzity_model = model
                                break
                            else:
                                chyba_msg = res['error']['message']
                                
                        if not uspesna_odpoved:
                            st.error(f"Googlu selhalo všech {len(dostupne_modely)} modelů! Poslední chyba: {chyba_msg}")
                        else:
                            raw_text = uspesna_odpoved['candidates'][0]['content']['parts'][0]['text']
                            clean_text = raw_text.replace("```json", "").replace("```", "").strip()
                            data_ai = json.loads(clean_text)
                            
                            res_db = requests.post(f"{SUPABASE_URL}/rest/v1/burza_zpravy", headers=headers, json={"titulek": data_ai['titulek'], "text_zpravy": data_ai['text_zpravy']})
                            
                            if res_db.status_code in [200, 201]:
                                st.success(f"Zpráva úspěšně vydána! (Vygeneroval model: {pouzity_model})")
                                st.rerun()
                            else:
                                st.error(f"Chyba při ukládání do DB: {res_db.text}")
                    except requests.exceptions.Timeout:
                        st.error("Chyba: Servery Googlu jsou aktuálně přetížené a nestihly odpovědět do 30 vteřin. Zkuste to za okamžik znovu.")
                    except Exception as e:
                        st.error(f"Kritická chyba v kódu: {str(e)}")

        st.markdown("##### 📰 Náhled vydaných zpráv")
        zpravy_ucitel = requests.get(f"{SUPABASE_URL}/rest/v1/burza_zpravy?order=datum.desc&limit=2", headers=headers).json()
        if zpravy_ucitel:
            for z in zpravy_ucitel:
                st.markdown(f"<div style='border-left: 3px solid #f59e0b; padding-left: 10px; margin-bottom: 10px;'><b style='color:#f59e0b;'>{z['titulek']}</b><br><span style='font-size:13px; color:#cbd5e1;'>{z['text_zpravy']}</span></div>", unsafe_allow_html=True)
        else:
            st.info("Zatím jste nevydali žádnou zprávu.")
        
        st.write("---")
        st.markdown("#### Žádosti o podnikatelský úvěr")
        uvery = requests.get(f"{SUPABASE_URL}/rest/v1/bankovni_uvery?stav=eq.ZADOST", headers=headers).json()
        if uvery:
            for u in uvery:
                f_jmeno = next((f['nazev_firmy'] for f in firmy if f['id'] == u['firma_id']), "Neznámá firma")
                st.markdown(f"<div class='card-box'><h5>Žadatel: {f_jmeno}</h5><p>Požadovaná částka: <b>{u['castka']} M-K</b> (Úrok: {u['urok_pct']} %)<br>Účel: {u['ucel']}</p></div>", unsafe_allow_html=True)
                col_u_btn1, col_u_btn2 = st.columns(2)
                with col_u_btn1:
                    if st.button("Schválit úvěr", key=f"uv_ok_{u['id']}"):
                        f_ceo = next((f['ceo_jmeno'] for f in firmy if f['id'] == u['firma_id']), None)
                        celkem_vratit = u['castka'] * (1 + (u['urok_pct'] / 100.0))
                        requests.patch(f"{SUPABASE_URL}/rest/v1/bankovni_uvery?id=eq.{u['id']}", headers=headers, json={"stav": "SCHVALENO", "zbyva_splatit": celkem_vratit})
                        res_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{f_ceo}", headers=headers).json()
                        if res_ceo: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{f_ceo}", headers=headers, json={"kredity": res_ceo[0]['kredity'] + u['castka']})
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": u['firma_id'], "typ_transakce": "PRIJEM", "titul": f"Bankovní úvěr: {u['ucel']}", "castka": u['castka'], "auditovano": True})
                        st.rerun()
                with col_u_btn2:
                    if st.button("Zamítnout", key=f"uv_ne_{u['id']}"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/bankovni_uvery?id=eq.{u['id']}", headers=headers, json={"stav": "ZAMITNUTO"})
                        st.rerun()
        else: st.info("Centrální banka neeviduje žádné čekající žádosti o úvěr.")
# ==========================================
# ZÁLOŽKA 8: KRIZOVÉ ŘÍZENÍ
# ==========================================
with tab_krize:
    st.subheader("Krizové řízení a Řízení intenzity krizí")
    st.caption("Plošné krizové akce. Zde můžete libovolně nastavit procentuální nebo finanční sílu jednotlivých dopadů!")
    
    target_skola = skolni_kod_ucitele or firma.get('skolni_kod', '') or 'SYSTEM'
    nastaveni_res = requests.get(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{target_skola}", headers=headers).json()
    akt_nast = nastaveni_res[0] if nastaveni_res else {}
    
    col_k1, col_k2 = st.columns(2)
    
    with col_k1:
        st.markdown("#### 1. Rutinní spravování trhu")
        
        with st.expander("Měsíční uzávěrka (Vyžadovat nájmy)"):
            st.caption("Všem žákům zruší zaplacení životních nákladů. Budou muset uhradit složenky ze své peněženky.")
            if st.button("Provést uzávěrku a vymáhat nájmy"):
                requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?role=eq.zak", headers=headers, json={"naklady_zaplaceny": False})
                st.success("Uzávěrka provedena! Žákům byla zaslána výzva k úhradě.")
                st.rerun()
                
        with st.expander("Hospodářský stimulus (Příspěvek žákům)"):
            stimulus_castka = st.number_input("Výše příspěvku (M-K):", min_value=10, value=50)
            if st.button("Rozdat plošný stimulus žákům"):
                vsi_zaci = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?role=eq.zak", headers=headers).json()
                if vsi_zaci:
                    for z in vsi_zaci:
                        requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?id=eq.{z['id']}", headers=headers, json={"kredity": z['kredity'] + stimulus_castka})
                        requests.post(f"{SUPABASE_URL}/rest/v1/bankovni_prevody", headers=headers, json={"odesilatel": "Stát (Stimulus)", "prijemce": z['jmeno'], "castka": stimulus_castka, "ucel": "Státní příspěvek na podporu poptávky"})
                    st.success(f"Příspěvek {stimulus_castka} M-K byl úspěšně připsán všem žákům!")
                    st.rerun()

    with col_k2:
        st.markdown("#### 2. Nastavení a vyhlášení krizí")
        
        with st.expander("KYBERNETICKÝ RANSOMWARE ÚTOK"):
            pct_kyber = st.number_input("Kolik % kapitálu se firmám strhne jako výkupné?", min_value=1, max_value=50, value=15)
            if st.button("Vyhlásit Kyberútok"):
                requests.patch(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{target_skola}", headers=headers, json={"aktivni_krize": "KYBER", "krize_popis": f"Kybernetický útok! Firmám bylo strženo {pct_kyber} % kapitálu jako výkupné."})
                for f in firmy:
                    r_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{f['ceo_jmeno']}", headers=headers).json()
                    if r_ceo:
                        kredity = r_ceo[0]['kredity']
                        ztrata = kredity * (pct_kyber / 100.0)
                        requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{f['ceo_jmeno']}", headers=headers, json={"kredity": kredity - ztrata})
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": f["id"], "typ_transakce": "VYDAJ", "titul": f"VÝKUPNÉ: Ransomware (-{pct_kyber} %)", "castka": ztrata, "auditovano": True})
                st.success("Kyberútok spuštěn!")
                st.rerun()

        with st.expander("MEZINÁRODNÍ SANKCE A DAŇOVÝ ŠOK"):
            zvyseni_dan = st.number_input("O kolik % se zvýší M-TECH daň e-shopu?", min_value=1.0, max_value=30.0, value=10.0)
            if st.button("Vyhlásit Sankce"):
                akt_dan = float(akt_nast.get('mtech_dan_pct', 15.0))
                nova_dan = akt_dan + zvyseni_dan
                requests.patch(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{target_skola}", headers=headers, json={
                    "aktivni_krize": "SANKCE",
                    "krize_popis": f"Vyhlášeny sankce! M-TECH daň e-shopu stoupla o +{zvyseni_dan} % na celkových {nova_dan} %.",
                    "mtech_dan_pct": nova_dan
                })
                st.success("Sankce vyhlášeny!")
                st.rerun()

        with st.expander("MĚNOVÝ ŠOK A DEVALVACE KURZU"):
            nasobek_kurzu = st.number_input("Kolikrát se znásobí kurz koruny? (např. 2.0 = 2x dražší)", min_value=1.1, max_value=5.0, value=2.0, step=0.1)
            if st.button("Vyhlásit Měnový šok"):
                akt_k = float(akt_nast.get('kurz_kc', 10.0))
                novy_k = akt_k * nasobek_kurzu
                requests.patch(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{target_skola}", headers=headers, json={
                    "aktivni_krize": "DEVALVACE",
                    "krize_popis": f"Propad hodnoty měny! Kurz M-Kreditu se změnil na 1 M-K = {novy_k} Kč.",
                    "kurz_kc": novy_k
                })
                st.success("Měnový šok spuštěn!")
                st.rerun()

        with st.expander("ENERGETICKÁ KRIZE (Nedoplatky)"):
            zaloha_energie = st.number_input("Plošný nedoplatek na firmu (M-K):", min_value=10, value=100)
            if st.button("Vyhlásit Energetickou krizi"):
                requests.patch(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{target_skola}", headers=headers, json={"aktivni_krize": "ENERGIE", "krize_popis": f"Skokové zdražení energií! Strženo {zaloha_energie} M-K všem firmám."})
                for f in firmy:
                    r_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{f['ceo_jmeno']}", headers=headers).json()
                    if r_ceo:
                        kredity = r_ceo[0]['kredity']
                        requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{f['ceo_jmeno']}", headers=headers, json={"kredity": max(0, kredity - zaloha_energie)})
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": f["id"], "typ_transakce": "VYDAJ", "titul": "MIMOŘÁDNÝ VÝDAJ: Nedoplatek za energie", "castka": zaloha_energie, "auditovano": True})
                st.success("Energetická krize aplikována!")
                st.rerun()
            
        st.write("---")
        if st.button("Odvolat krizový stav (Návrat k normálu)"):
            requests.patch(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{target_skola}", headers=headers, json={"aktivni_krize": "ZADNA", "krize_popis": ""})
            st.success("Krizový stav byl odvolán.")
            st.rerun()
