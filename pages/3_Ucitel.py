import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Kontrolní úřad a Audit", layout="wide")

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

tab_legal, tab_aktiva, tab_hr, tab_finance, tab_questy, tab_stat, tab_banka, tab_krize = st.tabs([
    "1. Spis", "2. Vize", "3. HR", "4. E-shop", "5. Úřad práce a XP", "6. Státní pokladna a Daně", "7. Banka a Ceník", "8. Krizové řízení"
])

with tab_legal:
    st.markdown(f"<h4>Stav licence: {firma['stave_licence']}</h4>", unsafe_allow_html=True)
    if st.button("Schválit zápis do rejstříku"):
        requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{f_id}", headers=headers, json={"stave_licence": "SCHVALENO", "duvod_zamitnuti": ""})
        st.rerun()

with tab_aktiva: st.info("Sekce Vize a reporty...")
with tab_hr: st.info("Sekce HR auditu...")
with tab_finance: st.info("Sekce E-shopu...")

# ==========================================
# 5. ÚŘAD PRÁCE A ŠABLONY ŠKOLNÍCH ÚKOLŮ
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

with tab_stat: st.info("Sekce Státní pokladny...")
with tab_banka: st.info("Sekce Centrální banky...")
with tab_krize: st.info("Sekce Krizového řízení...")
