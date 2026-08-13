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

# ==========================================
# ZÁLOŽKA 1: SPIS
# ==========================================
with tab_legal:
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        res_zamestnanci = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?firma_id=eq.{f_id}", headers=headers).json()
        seznam_zamestnancu = ", ".join([z['jmeno_zamestnance'] for z in res_zamestnanci]) if res_zamestnanci else "Žádní další zaměstnanci"
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
        stav_ikona = 'status-ok' if firma['stave_licence'] == 'SCHVALENO' else 'status-wait'
        st.markdown(f"<div class='card-box'><h4>Stav licence: <span class='{stav_ikona}'>{firma['stave_licence']}</span></h4></div>", unsafe_allow_html=True)
    
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
# ZÁLOŽKA 2: VIZE A AI
# ==========================================
with tab_aktiva:
    canvas = requests.get(f"{SUPABASE_URL}/rest/v1/lean_canvas?firma_id=eq.{f_id}", headers=headers).json()
    
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.markdown("#### Digitální aktiva")
        if firma.get('logo_url'): 
            st.markdown(f"<a href='{firma['logo_url']}' class='asset-link' target='_blank'>Firemní Logo</a>", unsafe_allow_html=True)
        if firma.get('web_url'): 
            st.markdown(f"<a href='{firma['web_url']}' class='asset-link' target='_blank'>Webové stránky</a>", unsafe_allow_html=True)
    
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
                    for u in neauditovane: 
                        requests.patch(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?id=eq.{u['id']}", headers=headers, json={"auditovano": True})
                    st.rerun()
            df_show = pd.DataFrame(ucto)[['datum', 'typ_transakce', 'titul', 'castka', 'auditovano']]
            st.dataframe(df_show, use_container_width=True)
        else:
            st.info("Kniha transakcí je zatím prázd
