import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Kontrolní úřad a Audit", page_icon=":material/account_balance:", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3, h4 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #00B4D8; width: 100%; font-weight: 600; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0, 180, 216, 0.4); border-color: #00B4D8; }
    .card-box { background-color: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 15px; }
    .status-ok { color: #34d399; font-weight: 700; background: rgba(16, 185, 129, 0.1); padding: 4px 8px; border-radius: 6px; }
    .status-wait { color: #fbbf24; font-weight: 700; background: rgba(245, 158, 11, 0.1); padding: 4px 8px; border-radius: 6px; }
    .status-err { color: #f87171; font-weight: 700; background: rgba(239, 68, 68, 0.1); padding: 4px 8px; border-radius: 6px; }
    .asset-link { color: #00B4D8; font-weight: bold; text-decoration: none; }
    .asset-link:hover { text-decoration: underline; color: #0077B6; }
    </style>
""", unsafe_allow_html=True)

DEFAULT_CENIK = """=== 🛠️ 3D TISK A CNC ===
• 3D Tisk PLA/PETG (Základní): 5 M-K / hodina tisku
• 3D Tisk SLA (Pryskyřice): 15 M-K / hodina
• Laser - Překližka (3mm, A3): 15 M-K / deska
• Laser - Plexisklo (3mm, A3): 25 M-K / deska

=== ⚡ ELEKTRONIKA A SOUČÁSTKY ===
• Vývojová deska (Arduino Uno klon): 25 M-K / ks
• Senzory (teplota, vlhkost, ultrazvuk): 5 M-K / ks
• Mikro servo motor: 10 M-K / ks
• Krokový motor (NEMA 17): 35 M-K / ks
• LED diody (balení 10 ks): 2 M-K
• Propojovací kabely (dupont, 20 ks): 3 M-K
• Nepájivé pole (Breadboard): 8 M-K / ks
• Baterie (9V / Li-Pol článek): 15 M-K / ks

=== 📦 SPOTŘEBNÍ MATERIÁL A BALENÍ ===
• Kartonový papír (A3, 5 ks): 5 M-K
• Spojovací materiál (šroubky, matice - sada): 10 M-K
• Balicí krabice E-commerce (standard): 3 M-K / ks

=== 💻 DIGITÁLNÍ SLUŽBY A SOFTWARE ===
• Doména (.cz/.com) + Webhosting: 50 M-K / rok
• Cloud Databáze / Server (Základní): 20 M-K / měsíc
• ChatGPT / OpenAI API kredity: 20 M-K / balíček
• Premium grafika (Canva Pro prvky): 10 M-K / projekt

=== 🏢 SLUŽBY ŠKOLY A REŽIE ===
• Odborná konzultace s expertem (Učitel): 25 M-K / 30 minut
• Pronájem zasedací místnosti pro schůzku: 15 M-K / hodina
• Marketingové promo na školních sítích: 30 M-K / kampaň"""

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

res_firmy = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?select=*&order=id.desc", headers=headers)
firmy = res_firmy.json() if res_firmy.status_code == 200 else []

if not firmy:
    st.info("V systému zatím nejsou žádné studentské entity.")
    st.stop()

vybrana_firma_nazev = st.selectbox("Vyberte startup k auditu:", [f["nazev_firmy"] for f in firmy])
firma = next(f for f in firmy if f["nazev_firmy"] == vybrana_firma_nazev)
f_id = firma["id"]

canvas = requests.get(f"{SUPABASE_URL}/rest/v1/lean_canvas?firma_id=eq.{f_id}", headers=headers).json()
reporty = requests.get(f"{SUPABASE_URL}/rest/v1/firemni_reporty?firma_id=eq.{f_id}&order=datum_odevzdani.desc", headers=headers).json()
zamestnanci = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?firma_id=eq.{f_id}", headers=headers).json()
kalkulace = requests.get(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy?firma_id=eq.{f_id}", headers=headers).json()
ucto = requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?firma_id=eq.{f_id}&order=datum.desc", headers=headers).json()

st.write("---")

tab_legal, tab_aktiva, tab_hr, tab_finance, tab_questy, tab_stat, tab_banka = st.tabs([
    "1. Spis a Rejstřík", "2. Vize a Reporty", "3. HR a Mzdy", "4. E-shop (Schvalování)", "5. Úřad práce (Questy)", "6. Státní pokladna (Dotace)", "7. Centrální Banka (Daně a Ceník)"
])

with tab_legal:
    col_l1, col_l2 = st.columns(2)
    with col_l1: st.markdown(f"<div class='card-box'><h4>Kód a Management</h4><p>Kód: {firma['skolni_kod']}</p><p>CEO: {firma['ceo_jmeno']}</p></div>", unsafe_allow_html=True)
    with col_l2: st.markdown(f"<div class='card-box'><h4>Stav licence: <span class='{'status-ok' if firma['stave_licence'] == 'SCHVALENO' else 'status-wait'}'>{firma['stave_licence']}</span></h4></div>", unsafe_allow_html=True)
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Schválit zápis do rejstříku", icon=":material/gavel:"):
            requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{f_id}", headers=headers, json={"stave_licence": "SCHVALENO", "duvod_zamitnuti": ""})
            st.rerun()
    with col_btn2:
        with st.popover("Zamítnout a vrátit k přepracování", icon=":material/block:"):
            duvod = st.text_area("Odůvodnění zamítnutí:")
            if st.button("Potvrdit zamítnutí"):
                requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{f_id}", headers=headers, json={"stave_licence": "ZAMITNUTO", "duvod_zamitnuti": duvod})
                st.rerun()

with tab_aktiva:
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.markdown("#### Digitální aktiva")
        if firma.get('logo_url'): st.markdown(f"<a href='{firma['logo_url']}' class='asset-link' target='_blank'>Firemní Logo</a>", unsafe_allow_html=True)
        if firma.get('web_url'): st.markdown(f"<a href='{firma['web_url']}' class='asset-link' target='_blank'>Webové stránky</a>", unsafe_allow_html=True)
        if firma.get('promo_url'): st.markdown(f"<a href='{firma['promo_url']}' class='asset-link' target='_blank'>Prezentace</a>", unsafe_allow_html=True)
    with col_a2:
        st.markdown("#### Strategie")
        if canvas:
            with st.expander("Detail Lean Canvasu"):
                st.write("**Problém:**", canvas[0]['problem'])
                st.write("**Řešení:**", canvas[0]['reseni'])
        else: st.info("Firma zatím nedodala Lean Canvas.")
    st.write("---")
    st.markdown("#### Vykázané reporty")
    if reporty:
        for r in reporty: st.markdown(f"<a href='{r['odkaz_soubor']}' class='asset-link' target='_blank'>Zobrazit: {r['nazev_reportu']} ({r['typ_reportu']})</a>", unsafe_allow_html=True)
    else: st.info("Firma zatím neodevzdala žádný report.")

with tab_hr:
    st.markdown("#### Mzdový a personální audit")
    if zamestnanci: st.dataframe(pd.DataFrame(zamestnanci)[['jmeno_zamestnance', 'pozice', 'hodinova_sazba', 'vyplaceno_celkem']], use_container_width=True)
    else: st.info("Firma zatím neeviduje žádné zaměstnance.")

with tab_finance:
    st.markdown("#### Schvalování produktů pro Tržiště")
    if kalkulace:
        for k in kalkulace:
            barva = "status-ok" if k['schvaleno_uradem'] else "status-wait"
            st.markdown(f"<div class='card-box'><h5>{k['nazev_produktu']} <span class='{barva}'>{'Aktivní' if k['schvaleno_uradem'] else 'Čeká na kontrolu'}</span></h5><p>Koncová cena pro trh: {k['konecna_cena']} M-K</p></div>", unsafe_allow_html=True)
            if not k['schvaleno_uradem']:
                if st.button(f"Schválit kalkulaci: {k['nazev_produktu']}", key=f"kalk_{k['id']}", icon=":material/verified:"):
                    requests.patch(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy?id=eq.{k['id']}", headers=headers, json={"schvaleno_uradem": True})
                    st.rerun()
    else: st.info("Žádné kalkulace ke schválení.")
    st.write("---")
    st.markdown("#### Účetní audit a kniha transakcí")
    if ucto:
        neauditovane = [u for u in ucto if not u['auditovano']]
        if neauditovane:
            if st.button("Provést hromadný audit (Schválit transakce)", icon=":material/done_all:"):
                for u in neauditovane: requests.patch(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?id=eq.{u['id']}", headers=headers, json={"auditovano": True})
                st.rerun()
        st.dataframe(pd.DataFrame(ucto)[['datum', 'typ_transakce', 'titul', 'castka', 'auditovano']], use_container_width=True)
    else: st.info("Kniha transakcí je zatím prázdná.")

with tab_questy:
    st.subheader("Správa úkolů a zadávání práce")
    col_q1, col_q2 = st.columns(2)
    with col_q1:
        with st.form("new_quest"):
            q_nazev = st.text_input("Název zakázky / úkolu:")
            q_popis = st.text_area("Rozsah práce:")
            q_odmena = st.number_input("Odměna (M-K):", min_value=1.0, value=20.0)
            if st.form_submit_button("Vypsat do Úřadu práce", icon=":material/campaign:"):
                if q_nazev:
                    requests.post(f"{SUPABASE_URL}/rest/v1/questy", headers=headers, json={"nazev": q_nazev, "popis": q_popis, "odmena": q_odmena, "zadavatel": st.session_state.uzivatel, "stav": "VOLNY"})
                    st.rerun()
    with col_q2:
        st.markdown("#### Práce ke kontrole")
        res_q_check = requests.get(f"{SUPABASE_URL}/rest/v1/questy?stav=eq.K_KONTROLE", headers=headers).json()
        if res_q_check:
            for q in res_q_check:
                st.markdown(f"<div class='card-box'><h5>{q['nazev']}</h5><p>Zhotovitel: {q['resitel']} <br> <a href='{q['odkaz_vystup']}' target='_blank'>Výstup k posouzení</a></p></div>", unsafe_allow_html=True)
                if st.button(f"Schválit a vyplatit {q['odmena']} M-K", key=f"pay_{q['id']}", icon=":material/payments:"):
                    res_r = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{q['resitel']}", headers=headers).json()
                    if res_r: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{q['resitel']}", headers=headers, json={"kredity": res_r[0]['kredity'] + q['odmena']})
                    requests.patch(f"{SUPABASE_URL}/rest/v1/questy?id=eq.{q['id']}", headers=headers, json={"stav": "DOKONCENO"})
                    requests.post(f"{SUPABASE_URL}/rest/v1/bankovni_prevody", headers=headers, json={"odesilatel": "Stát", "prijemce": q['resitel'], "castka": q['odmena'], "ucel": f"Odměna za: {q['nazev']}"})
                    st.rerun()
        else: st.info("Žádné úkoly nečekají na schválení.")

with tab_stat:
    st.subheader("Státní pokladna a Fond rozvoje")
    res_stat = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers).json()
    stat_kredity = res_stat[0]['kredity'] if res_stat else 0
    st.markdown(f"<div class='card-box' style='text-align: center; background: linear-gradient(135deg, #0ea5e9 0%, #0369a1 100%); border: none;'><h3 style='color: white; font-weight: 400; margin-bottom: 5px;'>Vybrané daně v rozpočtu</h3><h1 style='background: none; -webkit-text-fill-color: white; margin: 0; font-size: 3em;'>{stat_kredity:.2f} M-K</h1></div>", unsafe_allow_html=True)
    
    with st.form("form_dotace"):
        vybrana_dotace_firma = st.selectbox("Příjemce grantu (Firma):", [f["nazev_firmy"] for f in firmy])
        castka_dotace = st.number_input("Výše grantu (M-K):", min_value=1.0, value=100.0)
        ucel_dotace = st.text_input("Účel grantu:", value="Státní podpora inovací")
        if st.form_submit_button("Schválit dotační program", icon=":material/account_balance:"):
            if castka_dotace > stat_kredity: st.error("Nedostatek prostředků ve státní pokladně.")
            else:
                firma_prijemce = next((f for f in firmy if f["nazev_firmy"] == vybrana_dotace_firma), None)
                if firma_prijemce:
                    requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers, json={"kredity": stat_kredity - castka_dotace})
                    res_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{firma_prijemce['ceo_jmeno']}", headers=headers).json()
                    if res_ceo: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{firma_prijemce['ceo_jmeno']}", headers=headers, json={"kredity": res_ceo[0]['kredity'] + castka_dotace})
                    requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": firma_prijemce["id"], "typ_transakce": "PRIJEM", "titul": f"Státní dotace: {ucel_dotace}", "castka": castka_dotace, "auditovano": True})
                    st.rerun()

with tab_banka:
    st.subheader("Centrální Banka (Kurz, Daně a Ceník)")
    col_cb1, col_cb2 = st.columns(2)
    
    with col_cb1:
        st.markdown("#### Nastavení ekonomiky školy")
        target_skola = skolni_kod_ucitele or firma.get('skolni_kod', '') or 'SYSTEM'
        nastaveni_res = requests.get(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{target_skola}", headers=headers).json()
        
        if not nastaveni_res:
            default_data = {
                "skolni_kod": target_skola, "start_kredit_zak": 100, "start_kredit_firma": 300,
                "mtech_dan_pct": 15.0, "dan_prijem_pct": 15.0, "kurz_kc": 10.0, "globalni_cenik": DEFAULT_CENIK
            }
            requests.post(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni", headers=headers, json=default_data)
            akt_nastaveni = default_data
        else:
            akt_nastaveni = nastaveni_res[0]

        with st.form("form_makro"):
            st.caption(f"Pravidla platná pro školní kód: **{target_skola}**")
            
            st.markdown("##### 1. Kurz a Startovací kapitál")
            n_kurz = st.number_input("Kurz M-Kreditu k CZK (1 M-K = X Kč):", min_value=1.0, value=float(akt_nastaveni.get('kurz_kc', 10.0)))
            n_zak = st.number_input("Startovací kredit pro ŽÁKA (M-K):", value=float(akt_nastaveni.get('start_kredit_zak', 100)))
            n_firma = st.number_input("Startovací kredit pro FIRMU (M-K):", value=float(akt_nastaveni.get('start_kredit_firma', 300)))
            
            st.markdown("##### 2. Daňová politika")
            n_dan = st.number_input("M-TECH Daň pro e-shop (% z prodeje):", min_value=0.0, max_value=50.0, value=float(akt_nastaveni.get('mtech_dan_pct', 15.0)))
            n_dan_prijem = st.number_input("Daň z příjmu zaměstnanců (% ze mzdy):", min_value=0.0, max_value=50.0, value=float(akt_nastaveni.get('dan_prijem_pct', 15.0)))
            
            st.markdown("##### 3. Centrální ceník materiálu a služeb")
            n_cenik = st.text_area("Ceník pro výpočet nákladů:", value=str(akt_nastaveni.get('globalni_cenik', '')), height=300)
            
            if st.form_submit_button("Uložit makroekonomická pravidla", icon=":material/settings:"):
                requests.patch(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{target_skola}", headers=headers, json={
                    "start_kredit_zak": n_zak, "start_kredit_firma": n_firma, "kurz_kc": n_kurz,
                    "globalni_cenik": n_cenik, "mtech_dan_pct": n_dan, "dan_prijem_pct": n_dan_prijem
                })
                st.success("Ekonomika byla úspěšně uložena!")
                st.rerun()

    with col_cb2:
        st.markdown("#### Žádosti o podnikatelský úvěr")
        uvery = requests.get(f"{SUPABASE_URL}/rest/v1/bankovni_uvery?stav=eq.ZADOST", headers=headers).json()
        if uvery:
            for u in uvery:
                f_jmeno = next((f['nazev_firmy'] for f in firmy if f['id'] == u['firma_id']), "Neznámá firma")
                st.markdown(f"<div class='card-box'><h5>Žadatel: {f_jmeno}</h5><p>Požadovaná částka: <b>{u['castka']} M-K</b> (Úrok: {u['urok_pct']} %)<br>Účel: {u['ucel']}</p></div>", unsafe_allow_html=True)
                col_u_btn1, col_u_btn2 = st.columns(2)
                with col_u_btn1:
                    if st.button("Schválit úvěr", key=f"uv_ok_{u['id']}", icon=":material/check:"):
                        f_ceo = next((f['ceo_jmeno'] for f in firmy if f['id'] == u['firma_id']), None)
                        celkem_vratit = u['castka'] * (1 + (u['urok_pct'] / 100.0))
                        requests.patch(f"{SUPABASE_URL}/rest/v1/bankovni_uvery?id=eq.{u['id']}", headers=headers, json={"stav": "SCHVALENO", "zbyva_splatit": celkem_vratit})
                        res_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{f_ceo}", headers=headers).json()
                        if res_ceo: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{f_ceo}", headers=headers, json={"kredity": res_ceo[0]['kredity'] + u['castka']})
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": u['firma_id'], "typ_transakce": "PRIJEM", "titul": f"Bankovní úvěr: {u['ucel']}", "castka": u['castka'], "auditovano": True})
                        st.rerun()
                with col_u_btn2:
                    if st.button("Zamítnout", key=f"uv_ne_{u['id']}", icon=":material/close:"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/bankovni_uvery?id=eq.{u['id']}", headers=headers, json={"stav": "ZAMITNUTO"})
                        st.rerun()
        else: st.info("Centrální banka neeviduje žádné čekající žádosti o úvěr.")
