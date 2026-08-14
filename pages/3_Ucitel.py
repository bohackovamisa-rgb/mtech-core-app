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
    .alert-box { background-color: rgba(245, 158, 11, 0.1); border: 1px solid #f59e0b; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    .asset-link { color: #00B4D8; font-weight: bold; text-decoration: none; }
    .asset-link:hover { text-decoration: underline; color: #0077B6; }
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

# Zjištění školního kódu přihlášeného učitele
res_ucitel = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{st.session_state.uzivatel}", headers=headers).json()
skolni_kod_ucitele = res_ucitel[0].get("skolni_kod", "") if res_ucitel else ""
is_admin = str(st.session_state.get("role")).upper() == "ADMIN"

# Načtení firem školy
if is_admin:
    res_firmy = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?select=*&order=id.desc", headers=headers).json()
else:
    res_firmy = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?skolni_kod=eq.{skolni_kod_ucitele}&select=*&order=id.desc", headers=headers).json()

firmy = res_firmy if (isinstance(res_firmy, list) and res_firmy) else []

# =========================================================================
# 1. PŘEHLED NEVYŘÍZENÝCH ŽÁDOSTÍ
# =========================================================================
firmy_cekajici = [f for f in firmy if f.get("stave_licence") == "CEKA_NA_SCHVALENI"]

res_q_check = requests.get(f"{SUPABASE_URL}/rest/v1/questy?stav=eq.K_KONTROLE", headers=headers).json()
questy_cekajici = res_q_check if isinstance(res_q_check, list) else []

res_priznani_check = requests.get(f"{SUPABASE_URL}/rest/v1/danova_priznani?stav=eq.ODEVZDANO", headers=headers).json()
priznani_cekajici = [p for p in (res_priznani_check if isinstance(res_priznani_check, list) else []) if any(f['id'] == p.get('firma_id') for f in firmy)]

res_kalk_check = requests.get(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy?schvaleno_uradem=eq.false", headers=headers).json()
kalkulace_cekajici = [k for k in (res_kalk_check if isinstance(res_kalk_check, list) else []) if any(f['id'] == k.get('firma_id') for f in firmy)]

pocet_celkem_restu = len(firmy_cekajici) + len(questy_cekajici) + len(priznani_cekajici) + len(kalkulace_cekajici)

if pocet_celkem_restu > 0:
    st.markdown(f"""<div class='alert-box'>
<h4 style='margin:0; color:#f59e0b;'>Nevyřízené položky vyžadující vaši pozornost ({pocet_celkem_restu})</h4>
<ul style='margin-bottom:0; color:#cbd5e1; font-size: 14px;'>
{"<li><b>Nové žádosti o založení firmy:</b> " + str(len(firmy_cekajici)) + " (Zkontrolujte níže v záložce 1. Spis)</li>" if firmy_cekajici else ""}
{"<li><b>Odevzdané úkoly žáků ke kontrole a udělení XP:</b> " + str(len(questy_cekajici)) + " (Záložka 5. Úřad práce)</li>" if questy_cekajici else ""}
{"<li><b>Kalkulace produktů pro E-shop ke schválení:</b> " + str(len(kalkulace_cekajici)) + " (Záložka 4. E-shop)</li>" if kalkulace_cekajici else ""}
{"<li><b>Odevzdaná daňová přiznání k auditu:</b> " + str(len(priznani_cekajici)) + " (Záložka 6. Státní pokladna)</li>" if priznani_cekajici else ""}
</ul></div>""", unsafe_allow_html=True)
else:
    st.success("Všechny studentské žádosti, úkoly i audity jsou vyřízené.")

# =========================================================================
# 2. SPRÁVA ŽÁKŮ A OPRÁVNĚNÍ
# =========================================================================
with st.expander("Správa žáků a přidělování podnikatelských rolí", expanded=False):
    if is_admin:
        zaci_skoly = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?role=neq.ucitel&order=id.desc", headers=headers).json()
    else:
        zaci_skoly = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?skolni_kod=eq.{skolni_kod_ucitele}&role=neq.ucitel&order=id.desc", headers=headers).json()
    
    if not zaci_skoly or not isinstance(zaci_skoly, list):
        st.info("Ve vaší škole zatím nejsou registrováni žádní žáci.")
    else:
        tabulka_zaku = []
        for z in zaci_skoly:
            role_text = "Podnikatel (Může založit firmu)" if z.get("role") == "firma" else "Běžný žák (Práce a nákup)"
            tabulka_zaku.append({
                "Uživatelské jméno": z.get("jmeno"),
                "Aktuální role": role_text,
                "Zůstatek (M-K)": z.get("kredity", 0)
            })
        st.dataframe(pd.DataFrame(tabulka_zaku), use_container_width=True)
        
        col_z1, col_z2, col_z3 = st.columns([2, 2, 1])
        with col_z1:
            vybrany_zak = st.selectbox("Vyberte žáka:", [z["jmeno"] for z in zaci_skoly])
        with col_z2:
            nova_role = st.selectbox("Nastavit oprávnění:", ["firma (Podnikatel / Zakladatel)", "zak (Běžný žák)"])
        with col_z3:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("Uložit roli"):
                role_kod = "firma" if "firma" in nova_role else "zak"
                requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{vybrany_zak}", headers=headers, json={"role": role_kod})
                st.success(f"Žákovi {vybrany_zak} byla nastavena nová role.")
                st.rerun()

st.write("---")

# =========================================================================
# 3. VÝBĚR FIRMY A JEJÍ AUDIT
# =========================================================================
if not firmy:
    st.info("Ve vaší škole zatím žádný žák neodeslal žádost o registraci firmy.")
    st.stop()

firmy_labels = []
for f in firmy:
    status_tag = " [ČEKÁ NA SCHVÁLENÍ]" if f.get("stave_licence") == "CEKA_NA_SCHVALENI" else ""
    firmy_labels.append(f"{f['nazev_firmy']}{status_tag}")

vybrany_label = st.selectbox("Vyberte startup k auditu:", firmy_labels)
vybrana_firma_nazev = vybrany_label.replace(" [ČEKÁ NA SCHVÁLENÍ]", "")
firma = next(f for f in firmy if f["nazev_firmy"] == vybrana_firma_nazev)
f_id = firma["id"]

tab_legal, tab_aktiva, tab_hr, tab_finance, tab_questy, tab_stat, tab_banka, tab_krize, tab_hodnoceni = st.tabs([
    "1. Spis a Notář", "2. Vize a AI", "3. HR", "4. E-shop a Zákazníci", "5. Úřad práce a XP", "6. Státní pokladna a Daně", "7. Banka a Ceník", "8. Krizové řízení", "9. Přehled a Hodnocení"
])

# ==========================================
# ZÁLOŽKA 1: SPIS A NOTÁŘ (OPRAVENÉ ZOBRAZENÍ)
# ==========================================
with tab_legal:
    st.subheader(f"Firemní spis: {firma['nazev_firmy']}")
    
    col_l1, col_l2 = st.columns([1.6, 1])
    
    with col_l1:
        res_zamestnanci = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?firma_id=eq.{f_id}", headers=headers).json()
        seznam_zamestnancu = ", ".join([z['jmeno_zamestnance'] for z in res_zamestnanci]) if isinstance(res_zamestnanci, list) and res_zamestnanci else "Zatím žádní zaměstnanci"
        
        with st.container(border=True):
            st.markdown("#### Identifikace společnosti")
            st.markdown(f"**Obchodní firma:** `{firma['nazev_firmy']}`")
            st.markdown(f"**Licenční kód školy:** `{firma.get('skolni_kod', '')}`")
            st.markdown(f"**Základní vklad / kapitál:** `{firma.get('pocatecni_kapital', 100)} M-K`")
            
            st.divider()
            
            st.markdown("#### Předmět podnikání a Živnost")
            st.write(firma.get('podnikatelsky_zamer', 'Neuvedeno'))
            
            st.divider()
            
            st.markdown("#### Statutární orgány a Vedení")
            st.markdown(f"* **CEO (Generální ředitel):** {firma.get('ceo_jmeno', 'Neobsazeno')}")
            st.markdown(f"* **CFO (Finanční ředitel):** {firma.get('cfo_jmeno', 'Neobsazeno')}")
            st.markdown(f"* **CTO (Technický ředitel):** {firma.get('cto_jmeno', 'Neobsazeno')}")
            st.markdown(f"* **Zaměstnanci ve výrobě:** {seznam_zamestnancu}")
        
        with st.expander("Jmenovat / Změnit vedení firmy (CEO, CFO, CTO)"):
            if is_admin:
                zaci_vse = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?role=eq.zak", headers=headers).json()
            else:
                zaci_vse = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?role=eq.zak&skolni_kod=eq.{skolni_kod_ucitele}", headers=headers).json()
            
            seznam_jmen_zaku = [z['jmeno'] for z in zaci_vse] if isinstance(zaci_vse, list) else []
            
            if not seznam_jmen_zaku:
                st.info("Ve vaší škole zatím nejsou žádní další žáci.")
            else:
                with st.form("form_zmena_roli"):
                    idx_ceo = seznam_jmen_zaku.index(firma['ceo_jmeno']) if firma.get('ceo_jmeno') in seznam_jmen_zaku else 0
                    idx_cfo = seznam_jmen_zaku.index(firma['cfo_jmeno'])+1 if firma.get('cfo_jmeno') in seznam_jmen_zaku else 0
                    idx_cto = seznam_jmen_zaku.index(firma['cto_jmeno'])+1 if firma.get('cto_jmeno') in seznam_jmen_zaku else 0

                    novy_ceo = st.selectbox("CEO (Generální ředitel):", seznam_jmen_zaku, index=idx_ceo)
                    novy_cfo = st.selectbox("CFO (Finanční ředitel):", ["-- Neobsazeno --"] + seznam_jmen_zaku, index=idx_cfo)
                    novy_cto = st.selectbox("CTO (Technický ředitel):", ["-- Neobsazeno --"] + seznam_jmen_zaku, index=idx_cto)
                    
                    if st.form_submit_button("Uložit změny statutárních orgánů"):
                        cfo_val = None if novy_cfo == "-- Neobsazeno --" else novy_cfo
                        cto_val = None if novy_cto == "-- Neobsazeno --" else novy_cto
                        requests.patch(
                            f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{f_id}",
                            headers=headers,
                            json={"ceo_jmeno": novy_ceo, "cfo_jmeno": cfo_val, "cto_jmeno": cto_val}
                        )
                        st.success("Vedení firmy bylo upraveno.")
                        st.rerun()
        
    with col_l2:
        stav = firma.get('stave_licence', 'CEKA_NA_SCHVALENI')
        stav_tridy = 'status-ok' if stav == 'SCHVALENO' else ('status-err' if stav in ['ZAMITNUTO', 'UKONCENO'] else 'status-wait')
        
        with st.container(border=True):
            st.markdown("#### Stav zápisu do rejstříku")
            st.markdown(f"Aktuální stav: <span class='{stav_tridy}'>{stav}</span>", unsafe_allow_html=True)
            if firma.get('duvod_zamitnuti'):
                st.error(f"Důvod zamítnutí: {firma.get('duvod_zamitnuti')}")
        
        if st.button("Schválit zápis do rejstříku a povolit činnost", type="primary"):
            requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{f_id}", headers=headers, json={"stave_licence": "SCHVALENO", "duvod_zamitnuti": ""})
            st.success(f"Firma {firma['nazev_firmy']} byla úspěšně zapsána do rejstříku.")
            st.rerun()
            
        with st.popover("Zamítnout / Vrátit k přepracování"):
            duvod = st.text_area("Pokyny pro žáky k opravě:")
            if st.button("Potvrdit zamítnutí"):
                requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{f_id}", headers=headers, json={"stave_licence": "ZAMITNUTO", "duvod_zamitnuti": duvod})
                st.warning("Spis byl vrácen žákům k přepracování.")
                st.rerun()

# ==========================================
# ZÁLOŽKA 2: VIZE A AI (LEAN CANVAS + SHARK TANK)
# ==========================================
with tab_aktiva:
    canvas = requests.get(f"{SUPABASE_URL}/rest/v1/lean_canvas?firma_id=eq.{f_id}", headers=headers).json()
    
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.markdown("#### Digitální identita")
        if firma.get('logo_url'): 
            st.markdown(f"<a href='{firma['logo_url']}' class='asset-link' target='_blank'>Firemní Logo</a>", unsafe_allow_html=True)
        if firma.get('web_url'): 
            st.markdown(f"<a href='{firma['web_url']}' class='asset-link' target='_blank'>Webové stránky</a>", unsafe_allow_html=True)
        if not firma.get('logo_url') and not firma.get('web_url'):
            st.info("Firma zatím nenahrála logo ani odkaz na web.")
    
    with col_a2:
        st.markdown("#### Byznys model")
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
    st.markdown("#### Historie AI Shark Tank")
    res_pitches = requests.get(f"{SUPABASE_URL}/rest/v1/ai_pitches?firma_id=eq.{f_id}&order=datum.desc", headers=headers).json()
    if res_pitches:
        for p in res_pitches:
            stav = "SCHVÁLENO" if p['schvaleno_investovano'] else "ZAMÍTNUTO"
            barva = "status-ok" if p['schvaleno_investovano'] else "status-err"
            with st.container(border=True):
                st.markdown(f"**Projekt:** {p['nazev_pitchu']} — <span class='{barva}'>{stav}</span>", unsafe_allow_html=True)
                st.write(f"Požadováno: {p['zadana_castka']} M-K za {p['nabizene_akcie']} ks akcií")
                st.info(f"Pitch žáků: {p['popis_projektu']}")
                with st.expander("Rozbalit hodnocení AI poroty"):
                    st.write(p['hodnoceni_ostry'])
                    st.write(p['hodnoceni_vizionarka'])
                    st.write(p['hodnoceni_rychly'])
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
            with st.container(border=True):
                st.markdown(f"**{k['nazev_produktu']}** — <span class='{barva}'>{'Aktivní' if k['schvaleno_uradem'] else 'Čeká na schválení'}</span>", unsafe_allow_html=True)
                st.write(f"Koncová cena pro trh: {k['konecna_cena']} M-K")
                if not k['schvaleno_uradem']:
                    if st.button(f"Schválit produkt do E-shopu: {k['nazev_produktu']}", key=f"kalk_{k['id']}"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy?id=eq.{k['id']}", headers=headers, json={"schvaleno_uradem": True})
                        st.rerun()
    else:
        st.info("Žádné kalkulace ke schválení.")

    st.write("---")
    st.markdown("#### AI Zákaznická podpora (Reklamace)")
    reklamace_list = requests.get(f"{SUPABASE_URL}/rest/v1/ai_reklamace?firma_id=eq.{f_id}&order=datum.desc", headers=headers).json()
    if reklamace_list:
        for r in reklamace_list:
            stav = "VYŘEŠENO" if r['vysledek'] in ['SCHVALENO', 'ZAMITNUTO_POKUTA'] else "NEODPOVĚZENO"
            barva = "status-ok" if r['vysledek'] == 'SCHVALENO' else ("status-err" if r['vysledek'] == 'ZAMITNUTO_POKUTA' else "status-wait")
            odpoved_firmy = r.get('odpoved_firmy', 'Zatím bez odpovědi.')
            with st.container(border=True):
                st.markdown(f"**Zákazník:** {r['zakaznik_jmeno']} — <span class='{barva}'>{stav}</span>", unsafe_allow_html=True)
                st.write(f"Stížnost: {r['text_stiznosti']}")
                st.info(f"Reakce firmy: {odpoved_firmy}")
    else:
        st.info("Firma zatím neměla žádné reklamace.")

    st.write("---")
    with st.expander("Účetní audit a kniha transakcí (Zobrazit)"):
        ucto = requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?firma_id=eq.{f_id}&order=datum.desc", headers=headers).json()
        if ucto:
            df_show = pd.DataFrame(ucto)[['datum', 'typ_transakce', 'titul', 'castka', 'auditovano']]
            st.dataframe(df_show, use_container_width=True)
        else:
            st.info("Kniha transakcí je zatím prázdná.")

# ==========================================
# ZÁLOŽKA 5: ÚŘAD PRÁCE A KONTROLA ÚKOLŮ
# ==========================================
with tab_questy:
    st.subheader("Správa úkolů a kontrola odevzdané práce")
    
    with st.expander("Rychlé vypsání školních úkolů pro žáky"):
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            if st.button("Vypsat: Úklid a organizace dílny"):
                requests.post(f"{SUPABASE_URL}/rest/v1/questy", headers=headers, json={"nazev": "Úklid a organizace 3D dílny", "popis": "Rovnání filamentů, úklid pracovního stolu a kontrola stavu tiskáren.", "odmena": 25.0, "zadavatel": st.session_state.uzivatel, "stav": "VOLNY"})
                st.success("Úkol vypsán.")
                st.rerun()
        with col_s2:
            if st.button("Vypsat: PR a Foto ze školní akce"):
                requests.post(f"{SUPABASE_URL}/rest/v1/questy", headers=headers, json={"nazev": "Fotodokumentace a PR článek", "popis": "Nafocení fotek ze školní akce a napsání kratičkého článku na web.", "odmena": 35.0, "zadavatel": st.session_state.uzivatel, "stav": "VOLNY"})
                st.success("Úkol vypsán.")
                st.rerun()
        with col_s3:
            if st.button("Vypsat: Pomoc s Dnem otevřených dveří"):
                requests.post(f"{SUPABASE_URL}/rest/v1/questy", headers=headers, json={"nazev": "Průvodce na Dni otevřených dveří", "popis": "Aktivní prezentace školních projektů a provádění návštěvníků.", "odmena": 50.0, "zadavatel": st.session_state.uzivatel, "stav": "VOLNY"})
                st.success("Úkol vypsán.")
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
        st.markdown("#### Odevzdaná práce ke kontrole")
        
        if questy_cekajici:
            for q in questy_cekajici:
                odkaz = q.get('odkaz_vystup', '')
                vystup_html = f"<a href='{odkaz}' target='_blank' style='color:#0ea5e9; font-weight:bold;'>Otevřít odkaz na odevzdanou práci</a>" if str(odkaz).startswith("http") else f"<b>Komentář:</b> <i>{odkaz}</i>"
                
                with st.container(border=True):
                    st.markdown(f"**{q['nazev']}** (Zhotovitel: {q['resitel']}, Odměna: {q['odmena']} M-K)")
                    st.markdown(vystup_html, unsafe_allow_html=True)
                    
                    with st.form(f"schvaleni_{q['id']}"):
                        col_xp1, col_xp2 = st.columns([2, 1])
                        with col_xp1:
                            kategorie_xp = st.selectbox("Oblast dovednosti:", ["IT a Technologie", "Marketing a Kreativita", "Byznys a Finance"], label_visibility="collapsed")
                        with col_xp2:
                            pocet_xp = st.number_input("Počet XP:", min_value=0, max_value=50, value=10, label_visibility="collapsed")
                        
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            btn_schvalit = st.form_submit_button("Schválit úkol a odeslat odměnu")
                        with col_btn2:
                            btn_zamitnout = st.form_submit_button("Zamítnout (Vrátit k opravě)")

                        if btn_schvalit:
                            res_r = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{q['resitel']}", headers=headers).json()
                            if res_r: 
                                z_data = res_r[0]
                                nove_kredity = z_data['kredity'] + q['odmena']
                                xp_col = "xp_it" if kategorie_xp == "IT a Technologie" else ("xp_marketing" if kategorie_xp == "Marketing a Kreativita" else "xp_byznys")
                                nove_xp = z_data.get(xp_col, 0) + pocet_xp
                                requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{q['resitel']}", headers=headers, json={"kredity": nove_kredity, xp_col: nove_xp})
                            
                            requests.patch(f"{SUPABASE_URL}/rest/v1/questy?id=eq.{q['id']}", headers=headers, json={"stav": "DOKONCENO"})
                            requests.post(f"{SUPABASE_URL}/rest/v1/bankovni_prevody", headers=headers, json={"odesilatel": "Stát", "prijemce": q['resitel'], "castka": q['odmena'], "ucel": f"Odměna za: {q['nazev']} (+ {pocet_xp} XP)"})
                            st.success("Odměna i XP body odeslány.")
                            st.rerun()
                            
                        if btn_zamitnout:
                            requests.patch(f"{SUPABASE_URL}/rest/v1/questy?id=eq.{q['id']}", headers=headers, json={"stav": "VOLNY", "resitel": None, "odkaz_vystup": ""})
                            st.warning("Úkol byl vrácen do nabídky k přepracování.")
                            st.rerun()
        else:
            st.info("Žádné úkoly momentálně nečekají na schválení.")

# ==========================================
# ZÁLOŽKA 6: STÁTNÍ POKLADNA A DAŇOVÝ AUDIT
# ==========================================
with tab_stat:
    st.subheader("Státní pokladna a Daňové audity")
    res_stat = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers).json()
    stat_kredity = res_stat[0]['kredity'] if res_stat else 0
    with st.container(border=True):
        st.markdown(f"### Vybrané daně a poplatky v rozpočtu: `{stat_kredity:.2f} M-K`")

    with st.form("form_dotace"):
        vybrana_dotace_firma = st.selectbox("Příjemce grantu (Firma):", [f["nazev_firmy"] for f in firmy])
        castka_dotace = st.number_input("Výše grantu (M-K):", min_value=1.0, value=100.0)
        ucel_dotace = st.text_input("Účel grantu:", value="Státní podpora inovací")
        if st.form_submit_button("Schválit dotační program"):
            if castka_dotace > stat_kredity:
                st.error("Nedostatek prostředků ve státní pokladně.")
            else:
                firma_prijemce = next((f for f in firmy if f["nazev_firmy"] == vybrana_dotace_firma), None)
                if firma_prijemce:
                    requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers, json={"kredity": stat_kredity - castka_dotace})
                    r_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{firma_prijemce['ceo_jmeno']}", headers=headers).json()
                    if r_ceo:
                        requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{firma_prijemce['ceo_jmeno']}", headers=headers, json={"kredity": r_ceo[0]['kredity'] + castka_dotace})
                    requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": firma_prijemce["id"], "typ_transakce": "PRIJEM", "titul": f"Státní dotace: {ucel_dotace}", "castka": castka_dotace, "auditovano": True})
                    st.rerun()

    st.write("---")
    st.markdown("#### Audit odevzdaných daňových přiznání")
    if priznani_cekajici:
        for p in priznani_cekajici:
            f_info = next((f for f in firmy if f['id'] == p['firma_id']), None)
            if not f_info: continue
            f_nazev = f_info['nazev_firmy']

            kniha = requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?firma_id=eq.{p['firma_id']}&typ_transakce=eq.PRIJEM", headers=headers).json()
            celkem_prijmy = sum(item['castka'] for item in kniha) if kniha else 0

            sk_kod = f_info.get('skolni_kod', 'SYSTEM')
            nast_res = requests.get(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{sk_kod}", headers=headers).json()
            sazba_dan = float(nast_res[0].get('mtech_dan_pct', 15.0)) if nast_res else 15.0
            pozadovana_dan = celkem_prijmy * (sazba_dan / 100.0)

            with st.container(border=True):
                st.markdown(f"**Daňové přiznání: {f_nazev}**")
                st.write(f"Přiznaná daň firmou: {p['dane_priznane']:.2f} M-K | Evidované příjmy: {celkem_prijmy:.2f} M-K | Povinná daň ({sazba_dan} %): {pozadovana_dan:.2f} M-K")

                if st.button(f"Spustit kontrolu přiznání #{p['id']}", key=f"ai_audit_{p['id']}"):
                    vysledek_status = "SCHVALENO" if abs(pozadovana_dan - p['dane_priznane']) <= 1 else "ZAMITNUTO_PENALE"
                    rozdil = max(0, pozadovana_dan - p['dane_priznane'])
                    vymere_penale = rozdil + 50.0 if vysledek_status == "ZAMITNUTO_PENALE" else 0.0

                    if vysledek_status == "SCHVALENO":
                        requests.patch(f"{SUPABASE_URL}/rest/v1/danova_priznani?id=eq.{p['id']}", headers=headers, json={"stav": "SCHVALENO"})
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": p['firma_id'], "typ_transakce": "PRIJEM", "titul": "INFO OD FÚ: Daňové přiznání schváleno", "castka": 0, "auditovano": True})
                        st.success("Daňové přiznání je v pořádku a bylo schváleno.")
                    else:
                        r_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{f_info['ceo_jmeno']}", headers=headers).json()
                        if r_ceo:
                            kredity = r_ceo[0]['kredity']
                            requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{f_info['ceo_jmeno']}", headers=headers, json={"kredity": max(0, kredity - vymere_penale)})
                        
                        requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers, json={"kredity": stat_kredity + vymere_penale})
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": p['firma_id'], "typ_transakce": "VYDAJ", "titul": "PENÁLE OD FÚ: Krácení daně", "castka": vymere_penale, "auditovano": True})
                        requests.patch(f"{SUPABASE_URL}/rest/v1/danova_priznani?id=eq.{p['id']}", headers=headers, json={"stav": "ZAMITNUTO_PENALE"})
                        st.error(f"Zjištěno krácení daně. Strženo penále {vymere_penale} M-K.")
                    st.rerun()
    else:
        st.info("Žádné firmy momentálně nečekají na daňový audit.")

# ==========================================
# ZÁLOŽKA 7: BANKA, CENÍK A BURZOVNÍ DOHLED
# ==========================================
with tab_banka:
    st.subheader("Centrální Banka a Dozor nad Burzou")
    col_cb1, col_cb2 = st.columns(2)
    
    target_skola = skolni_kod_ucitele or 'SYSTEM'
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
                st.success("Ekonomická pravidla uložena.")
                st.rerun()

    with col_cb2:
        st.markdown("#### Zprávy z trhu a Úvěry")
        uvery = requests.get(f"{SUPABASE_URL}/rest/v1/bankovni_uvery?stav=eq.ZADOST", headers=headers).json()
        if uvery:
            for u in uvery:
                f_jmeno = next((f['nazev_firmy'] for f in firmy if f['id'] == u['firma_id']), "Neznámá firma")
                with st.container(border=True):
                    st.markdown(f"**Žadatel:** {f_jmeno} | Částka: {u['castka']} M-K (Úrok: {u['urok_pct']} %)")
                    st.write(f"Účel: {u['ucel']}")
                    col_u_btn1, col_u_btn2 = st.columns(2)
                    with col_u_btn1:
                        if st.button("Schválit úvěr", key=f"uv_ok_{u['id']}"):
                            f_ceo = next((f['ceo_jmeno'] for f in firmy if f['id'] == u['firma_id']), None)
                            celkem_vratit = u['castka'] * (1 + (u['urok_pct'] / 100.0))
                            requests.patch(f"{SUPABASE_URL}/rest/v1/bankovni_uvery?id=eq.{u['id']}", headers=headers, json={"stav": "SCHVALENO", "zbyva_splatit": celkem_vratit})
                            res_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{f_ceo}", headers=headers).json()
                            if res_ceo:
                                requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{f_ceo}", headers=headers, json={"kredity": res_ceo[0]['kredity'] + u['castka']})
                            requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": u['firma_id'], "typ_transakce": "PRIJEM", "titul": f"Bankovní úvěr: {u['ucel']}", "castka": u['castka'], "auditovano": True})
                            st.rerun()
                    with col_u_btn2:
                        if st.button("Zamítnout", key=f"uv_ne_{u['id']}"):
                            requests.patch(f"{SUPABASE_URL}/rest/v1/bankovni_uvery?id=eq.{u['id']}", headers=headers, json={"stav": "ZAMITNUTO"})
                            st.rerun()
        else:
            st.info("Žádné čekající žádosti o podnikatelský úvěr.")

# ==========================================
# ZÁLOŽKA 8: KRIZOVÉ ŘÍZENÍ
# ==========================================
with tab_krize:
    st.subheader("Krizové řízení a Měsíční uzávěrky")
    target_skola = skolni_kod_ucitele or 'SYSTEM'
    nastaveni_res = requests.get(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{target_skola}", headers=headers).json()
    akt_nast = nastaveni_res[0] if nastaveni_res else {}
    
    col_k1, col_k2 = st.columns(2)
    with col_k1:
        st.markdown("#### Běžná správa")
        if st.button("Provést měsíční uzávěrku a vymáhat nájmy"):
            if is_admin:
                requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?role=eq.zak", headers=headers, json={"naklady_zaplaceny": False})
            else:
                requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?role=eq.zak&skolni_kod=eq.{skolni_kod_ucitele}", headers=headers, json={"naklady_zaplaceny": False})
            st.success("Uzávěrka provedena. Žákům byla zaslána výzva k úhradě.")
            st.rerun()

    with col_k2:
        st.markdown("#### Krizové zásahy")
        if st.button("Odvolat krizový stav (Návrat k normálu)"):
            requests.patch(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{target_skola}", headers=headers, json={"aktivni_krize": "ZADNA", "krize_popis": ""})
            st.success("Krizový stav byl odvolán.")
            st.rerun()

# ==========================================
# ZÁLOŽKA 9: HODNOCENÍ A PŘEHLED
# ==========================================
with tab_hodnoceni:
    st.subheader("Celkový přehled a hodnocení žáků")
    
    st.markdown("#### Firemní semafor")
    semafor_data = []
    for f in firmy:
        r_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{f['ceo_jmeno']}", headers=headers).json()
        finance = r_ceo[0]['kredity'] if r_ceo else 0
        semafor_data.append({
            "Firma": f['nazev_firmy'],
            "CEO": f.get('ceo_jmeno', 'Neobsazeno'),
            "Stav rejstříku": f.get('stave_licence', 'CEKA'),
            "Kapitál (M-K)": round(finance, 2)
        })
    if semafor_data:
        st.dataframe(pd.DataFrame(semafor_data), use_container_width=True)

    st.write("---")
    st.markdown("#### Žebříček aktivity žáků")
    if is_admin:
        zaci = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?role=eq.zak&order=kredity.desc", headers=headers).json()
    else:
        zaci = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?role=eq.zak&skolni_kod=eq.{skolni_kod_ucitele}&order=kredity.desc", headers=headers).json()
    
    if zaci and isinstance(zaci, list):
        zaci_data = []
        for z in zaci:
            xp_celkem = z.get('xp_it', 0) + z.get('xp_marketing', 0) + z.get('xp_byznys', 0)
            majetek = z.get('kredity', 0)
            zaci_data.append({
                "Jméno": z['jmeno'],
                "Majetek (M-K)": round(majetek, 2),
                "XP Body": xp_celkem
            })
        st.dataframe(pd.DataFrame(zaci_data), use_container_width=True)
