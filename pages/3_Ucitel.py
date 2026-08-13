import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Kontrolní úřad & Audit", page_icon=":material/account_balance:", layout="wide")

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

# Ochrana úřadu – povolí vstup jen učitelům nebo adminům
if not st.session_state.get("prihlasen") or str(st.session_state.get("role")).upper() not in ["UCITEL", "ADMIN"]:
    st.error("Na tuto stránku mají přístup pouze vyučující a administrátoři!")
    st.stop()

st.title("Kontrolní úřad & Audit")

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}
except Exception:
    st.error("Chybí konfigurace databáze v Secrets!")
    st.stop()

res_firmy = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?select=*&order=id.desc", headers=headers)
firmy = res_firmy.json() if res_firmy.status_code == 200 else []

if not firmy:
    st.info("Zatím nejsou v systému registrovány žádné studentské firmy.")
    st.stop()

vybrana_firma_nazev = st.selectbox("Vyberte startup k auditu:", [f["nazev_firmy"] for f in firmy])
firma = next(f for f in firmy if f["nazev_firmy"] == vybrana_firma_nazev)
f_id = firma["id"]

canvas = requests.get(f"{SUPABASE_URL}/rest/v1/lean_canvas?firma_id=eq.{f_id}", headers=headers).json()
reporty = requests.get(f"{SUPABASE_URL}/rest/v1/firemni_reporty?firma_id=eq.{f_id}&order=datum_odevzdani.desc", headers=headers).json()
porady = requests.get(f"{SUPABASE_URL}/rest/v1/zapisy_porady?firma_id=eq.{f_id}&order=datum.desc", headers=headers).json()
zamestnanci = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?firma_id=eq.{f_id}", headers=headers).json()
kalkulace = requests.get(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy?firma_id=eq.{f_id}", headers=headers).json()
ucto = requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?firma_id=eq.{f_id}&order=datum.desc", headers=headers).json()

st.write("---")

tab_legal, tab_aktiva, tab_hr, tab_finance = st.tabs([
    "Schvalování spisu", 
    "Reporty & Vize", 
    "HR & Agilní vývoj", 
    "Audit: Kalkulace a Účto"
])

with tab_legal:
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        st.markdown(f"<div class='card-box'><h4>Orgány a Kód</h4><p><b>Kód školy:</b> {firma['skolni_kod']}</p><p><b>CEO:</b> {firma['ceo_jmeno']}</p></div>", unsafe_allow_html=True)
    with col_l2:
        st.markdown(f"<div class='card-box'><h4>Stav spisu: <span class='{'status-ok' if firma['stave_licence'] == 'SCHVALENO' else 'status-wait'}'>{firma['stave_licence']}</span></h4></div>", unsafe_allow_html=True)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("SCHVÁLIT SPIS (Zapsat do rejstříku)", icon=":material/gavel:"):
            requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{f_id}", headers=headers, json={"stave_licence": "SCHVALENO", "duvod_zamitnuti": ""})
            st.rerun()
    with col_btn2:
        with st.popover("ZAMÍTNOUT (Vrátit k přepracování)", icon=":material/block:"):
            duvod = st.text_area("Důvod zamítnutí:")
            if st.button("Potvrdit zamítnutí"):
                requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{f_id}", headers=headers, json={"stave_licence": "ZAMITNUTO", "duvod_zamitnuti": duvod})
                st.rerun()

with tab_aktiva:
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.markdown("#### Vizuální identita (Brand)")
        if firma.get('logo_url'): st.markdown(f"<a href='{firma['logo_url']}' class='asset-link' target='_blank'>Firemní Logo</a>", unsafe_allow_html=True)
        if firma.get('web_url'): st.markdown(f"<a href='{firma['web_url']}' class='asset-link' target='_blank'>Webové stránky</a>", unsafe_allow_html=True)
        if firma.get('promo_url'): st.markdown(f"<a href='{firma['promo_url']}' class='asset-link' target='_blank'>Pitch Deck</a>", unsafe_allow_html=True)
    with col_a2:
        st.markdown("#### Lean Canvas")
        if canvas:
            with st.expander("Zobrazit Lean Canvas"):
                st.write("**Problém:**", canvas[0]['problem'])
                st.write("**Řešení:**", canvas[0]['reseni'])

    st.markdown("#### Odevzdané dokumenty a reporty")
    if reporty:
        for r in reporty:
            st.markdown(f"📄 <a href='{r['odkaz_soubor']}' class='asset-link' target='_blank'>Otevřít: {r['nazev_reportu']} ({r['typ_reportu']})</a>", unsafe_allow_html=True)

with tab_hr:
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        st.markdown("#### Mzdová listina")
        if zamestnanci:
            df_zam = pd.DataFrame(zamestnanci)[['jmeno_zamestnance', 'pozice', 'vyplaceno_celkem', 'hodnoceni_skore']]
            st.dataframe(df_zam, use_container_width=True)
    with col_h2:
        st.markdown("#### Zápisy z porad")
        if porady:
            for p in porady[:3]:
                st.markdown(f"<div class='card-box'><b>{p['datum'][:10]}</b><br>{p['projednane_body']}</div>", unsafe_allow_html=True)

with tab_finance:
    st.markdown("#### Ke schválení: Prodejní ceny produktů")
    if kalkulace:
        for k in kalkulace:
            barva = "status-ok" if k['schvaleno_uradem'] else "status-wait"
            st.markdown(f"<div class='card-box'><h5>{k['nazev_produktu']} <span class='{barva}'>{'Schváleno' if k['schvaleno_uradem'] else 'Čeká na audit'}</span></h5><p>Konečná cena: {k['konecna_cena']} M-K</p></div>", unsafe_allow_html=True)
            if not k['schvaleno_uradem']:
                if st.button(f"Schválit kalkulaci pro {k['nazev_produktu']}", key=f"kalk_{k['id']}", icon=":material/verified:"):
                    requests.patch(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy?id=eq.{k['id']}", headers=headers, json={"schvaleno_uradem": True})
                    st.rerun()

    st.write("---")
    st.markdown("#### Audit Knihy příjmů a výdajů")
    if ucto:
        neauditovane = [u for u in ucto if not u['auditovano']]
        if neauditovane:
            if st.button("Udělit auditní razítko všem transakcím", icon=":material/done_all:"):
                for u in neauditovane:
                    requests.patch(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?id=eq.{u['id']}", headers=headers, json={"auditovano": True})
                st.rerun()
        df_show = pd.DataFrame(ucto)[['datum', 'typ_transakce', 'titul', 'castka', 'auditovano']]
        st.dataframe(df_show, use_container_width=True)
