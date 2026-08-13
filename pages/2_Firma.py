import streamlit as st
import requests
import datetime

st.set_page_config(page_title="Startup Hub a Dashboard", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3, h4 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #00B4D8; width: 100%; font-weight: 600; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0, 180, 216, 0.4); border-color: #00B4D8; }
    .card-box { background-color: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 15px; }
    .status-badge-ok { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid #10b981; padding: 10px; border-radius: 8px; font-weight: 700; text-align: center; font-size: 12px; }
    .status-badge-wait { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid #f59e0b; padding: 10px; border-radius: 8px; font-weight: 700; text-align: center; font-size: 12px; }
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

uzivatel = st.session_state.get("uzivatel")

res_vsechny = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?select=*&order=id.desc", headers=headers).json()
vsechny_firmy = res_vsechny if res_vsechny else []
moje_firma = next((f for f in vsechny_firmy if uzivatel.lower() in [f.get('ceo_jmeno','').lower(), f.get('cfo_jmeno','').lower(), f.get('cto_jmeno','').lower()]), None)

akt_dan_mtech = 15.0
akt_dan_prijem = 15.0
kurz_kc = 10.0
akt_cenik = "Ceník zatím není nastaven."

if moje_firma:
    nastaveni_res = requests.get(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{moje_firma['skolni_kod']}", headers=headers).json()
    if nastaveni_res:
        akt_dan_mtech = float(nastaveni_res[0].get('mtech_dan_pct', 15.0))
        akt_dan_prijem = float(nastaveni_res[0].get('dan_prijem_pct', 15.0))
        kurz_kc = float(nastaveni_res[0].get('kurz_kc', 10.0))
        akt_cenik = nastaveni_res[0].get('globalni_cenik', '')

if moje_firma:
    st.subheader(f"Entita: {moje_firma['nazev_firmy']} (ID: #{moje_firma['id']})")
    col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
    with col_s1: st.markdown(f'<div class="{"status-badge-ok" if moje_firma["stave_licence"] == "SCHVALENO" else "status-badge-wait"}">{"Rejstřík OK" if moje_firma["stave_licence"] == "SCHVALENO" else "Čeká na audit"}</div>', unsafe_allow_html=True)
    with col_s2: st.markdown('<div class="status-badge-ok">Brand a Vize</div>', unsafe_allow_html=True)
    with col_s3: st.markdown('<div class="status-badge-ok">Agilní Vývoj</div>', unsafe_allow_html=True)
    with col_s4: st.markdown('<div class="status-badge-ok">HR a Úřady</div>', unsafe_allow_html=True)
    with col_s5: st.markdown('<div class="status-badge-ok">Finance</div>', unsafe_allow_html=True)
    st.write("---")

tab_zalozeni, tab_brand, tab_vyvoj, tab_hr, tab_kalkulace, tab_ucto, tab_burza = st.tabs([
    "1. Zakladatelský Spis", "2. Brand a AI Mentor", "3. Agilní Vývoj", "4. Tým a HR", "5. Cenotvorba", "6. Účetnictví a Daně", "7. Burza"
])

with tab_zalozeni: st.info("Zakladatelský spis a JRF...")
with tab_brand: st.info("Brand Kit a Lean Canvas...")
with tab_vyvoj: st.info("Agilní Kanban...")
with tab_hr: st.info("Nábor a Mzdy...")
with tab_kalkulace: st.info("Cenotvorba produktu...")

# ==========================================
# TAB 6: ÚČETNICTVÍ A DAŇOVÉ PŘIZNÁNÍ
# ==========================================
with tab_ucto:
    if moje_firma:
        col_u1, col_u2 = st.columns(2)
        
        with col_u1:
            st.subheader("Nákup materiálu od Školy")
            with st.form("form_nakup_materialu"):
                titul_nakupu = st.text_input("Předmět nákupu (např. 2x Filament):")
                castka_nakup = st.number_input("Celková cena dle Ceníku (M-K):", min_value=1.0, value=10.0)
                if st.form_submit_button("Zaplatit škole"):
                    res_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers).json()
                    if res_ceo and castka_nakup <= res_ceo[0]['kredity']:
                        requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers, json={"kredity": res_ceo[0]['kredity'] - castka_nakup})
                        res_stat = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers).json()
                        if res_stat: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers, json={"kredity": res_stat[0]['kredity'] + castka_nakup})
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": "VYDAJ", "titul": f"Nákup od školy: {titul_nakupu}", "castka": castka_nakup, "auditovano": False})
                        st.rerun()
                    else: st.error("Nedostatek kreditů!")
            
            st.markdown("#### Historie transakcí")
            res_kniha = requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?firma_id=eq.{moje_firma['id']}&order=datum.desc", headers=headers).json()
            if res_kniha: st.dataframe(pd.DataFrame(res_kniha)[['datum', 'typ_transakce', 'titul', 'castka']], use_container_width=True)
                
        with col_u2:
            st.subheader("Finanční úřad (Daňové přiznání)")
            st.caption("Firma (CFO) má povinnost spočítat obrat a odeslat státu Daňové přiznání. Pokud se pokusíte krátit daně, úřad vám napaří vysoké penále.")
            
            # Formulář pro Daňové přiznání
            with st.form("form_dane"):
                dane_priznane = st.number_input("Kolik M-Kreditů přiznáváte na daních?", min_value=0.0, value=0.0)
                if st.form_submit_button("Odeslat daňové přiznání a zaplatit"):
                    # 1. Zkontrolujeme, jestli mají peníze
                    res_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers).json()
                    kredity = res_ceo[0]['kredity'] if res_ceo else 0
                    if dane_priznane > kredity:
                        st.error("Nemáte na účtu dostatek prostředků na zaplacení přiznané daně!")
                    else:
                        # 2. Skutečný výpočet daní, abychom věděli, jestli nelžou (Úřad to uvidí v auditu)
                        # V reálu by sečetli příjmy. Pro zjednodušení simulace to necháme na FÚ.
                        skutecne_dane_odhad = dane_priznane # (Zde by byla složitá logika z tržeb)
                        
                        # Zápis do databáze Daňových přiznání
                        requests.post(f"{SUPABASE_URL}/rest/v1/danova_priznani", headers=headers, json={"firma_id": moje_firma['id'], "dane_priznane": dane_priznane, "dane_skutecne": skutecne_dane_odhad, "stav": "ODEVZDANO"})
                        
                        # Stržení peněz a odeslání Státu
                        requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers, json={"kredity": kredity - dane_priznane})
                        res_stat = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers).json()
                        if res_stat: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers, json={"kredity": res_stat[0]['kredity'] + dane_priznane})
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": "VYDAJ", "titul": "Odvod daně Finančnímu úřadu", "castka": dane_priznane, "auditovano": False})
                        
                        st.success("Přiznání odesláno k auditu.")
                        st.rerun()
            
            st.markdown("#### Odeslaná přiznání")
            priznani = requests.get(f"{SUPABASE_URL}/rest/v1/danova_priznani?firma_id=eq.{moje_firma['id']}&order=datum.desc", headers=headers).json()
            if priznani:
                for p in priznani:
                    barva = "status-wait" if p['stav'] == 'ODEVZDANO' else "status-ok" if p['stav'] == 'SCHVALENO' else "status-err"
                    st.markdown(f"<div class='card-box'>Přiznáno: {p['dane_priznane']} M-K<br><span class='{barva}'>Stav: {p['stav']}</span></div>", unsafe_allow_html=True)
            else:
                st.info("Zatím jste Finančnímu úřadu neodeslali žádné přiznání.")

with tab_burza: st.info("Investiční burza...")
