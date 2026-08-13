import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Kontrolní úřad & Audit", page_icon="⚖️", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3, h4 { background: -webkit-linear-gradient(45deg, #f43f5e, #eab308); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #f43f5e; width: 100%; font-weight: 600; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(244, 63, 94, 0.4); border-color: #f43f5e; }
    .card-box { background-color: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 15px; }
    
    .status-ok { color: #34d399; font-weight: 700; background: rgba(16, 185, 129, 0.1); padding: 4px 8px; border-radius: 6px; }
    .status-wait { color: #fbbf24; font-weight: 700; background: rgba(245, 158, 11, 0.1); padding: 4px 8px; border-radius: 6px; }
    .status-err { color: #f87171; font-weight: 700; background: rgba(239, 68, 68, 0.1); padding: 4px 8px; border-radius: 6px; }
    .asset-link { color: #f43f5e; font-weight: bold; text-decoration: none; }
    .asset-link:hover { text-decoration: underline; color: #fbbf24; }
    </style>
""", unsafe_allow_html=True)

st.title("⚖️ Kontrolní úřad & Investor Dashboard")
st.caption("Modul vyučujícího pro audit, schvalování spisů a hodnocení startupů v M-TECH CORE.")

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}
except Exception:
    st.error("Chybí konfigurace databáze v Secrets!")
    st.stop()

# 1. Načtení všech firem
res_firmy = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?select=*&order=id.desc", headers=headers)
firmy = res_firmy.json() if res_firmy.status_code == 200 else []

if not firmy:
    st.info("Zatím nejsou v systému registrovány žádné studentské firmy.")
    st.stop()

# 2. Výběr firmy pro audit
vybrana_firma_nazev = st.selectbox("🔍 Vyberte startup k auditu:", [f["nazev_firmy"] for f in firmy])
firma = next(f for f in firmy if f["nazev_firmy"] == vybrana_firma_nazev)
f_id = firma["id"]

# Načtení dat vybrané firmy
canvas = requests.get(f"{SUPABASE_URL}/rest/v1/lean_canvas?firma_id=eq.{f_id}", headers=headers).json()
reporty = requests.get(f"{SUPABASE_URL}/rest/v1/firemni_reporty?firma_id=eq.{f_id}&order=datum_odevzdani.desc", headers=headers).json()
porady = requests.get(f"{SUPABASE_URL}/rest/v1/zapisy_porady?firma_id=eq.{f_id}&order=datum.desc", headers=headers).json()
zamestnanci = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?firma_id=eq.{f_id}", headers=headers).json()
kalkulace = requests.get(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy?firma_id=eq.{f_id}", headers=headers).json()
ucto = requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?firma_id=eq.{f_id}&order=datum.desc", headers=headers).json()

st.write("---")

tab_legal, tab_aktiva, tab_hr, tab_finance = st.tabs([
    "🏛️ Schvalování spisu (Legal)", 
    "📁 Odevzdané Reporty & Vize", 
    "👷 HR & Agilní vývoj", 
    "💰 Audit: Kalkulace a Účetnictví"
])

# ==========================================
# TAB 1: SCHVALOVÁNÍ REGISTRAČNÍHO SPISU
# ==========================================
with tab_legal:
    st.subheader(f"Registrační spis: {firma['nazev_firmy']}")
    
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        st.markdown(f"""
            <div class='card-box'>
                <h4>Orgány a Kód</h4>
                <p><b>Kód školy:</b> {firma['skolni_kod']} (Level {firma['uroven_projektu']})</p>
                <p><b>CEO:</b> {firma['ceo_jmeno']}</p>
                <p><b>CFO:</b> {firma['cfo_jmeno']}</p>
                <p><b>CTO:</b> {firma['cto_jmeno']}</p>
                <p><b>Vklad celkem:</b> {firma['pocatecni_kapital']} M-K</p>
            </div>
        """, unsafe_allow_html=True)
    with col_l2:
        st.markdown(f"""
            <div class='card-box'>
                <h4>Živnost a BOZP</h4>
                <p><b>Předmět:</b> {firma['podnikatelsky_zamer']}</p>
                <p><b>Aktuální stav spisu:</b> <span class="{'status-ok' if firma['stave_licence'] == 'SCHVALENO' else ('status-err' if firma['stave_licence'] == 'ZAMITNUTO' else 'status-wait')}">{firma['stave_licence']}</span></p>
            </div>
        """, unsafe_allow_html=True)

    # AKCE SCHVÁLENÍ / ZAMÍTNUTÍ
    st.markdown("### Rozhodnutí úřadu")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("✅ SCHVÁLIT SPIS (Zapsat do rejstříku)", icon=":material/gavel:"):
            requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{f_id}", headers=headers, json={"stave_licence": "SCHVALENO", "duvod_zamitnuti": ""})
            st.success("Firma byla oficiálně schválena a zapsána!")
            st.rerun()
    with col_btn2:
        with st.popover("❌ ZAMÍTNOUT (Vrátit k přepracování)"):
            duvod = st.text_area("Uveďte důvod zamítnutí pro žáky:")
            if st.button("Potvrdit zamítnutí"):
                requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{f_id}", headers=headers, json={"stave_licence": "ZAMITNUTO", "duvod_zamitnuti": duvod})
                st.error("Spis zamítnut. Startup musí údaje opravit.")
                st.rerun()

# ==========================================
# TAB 2: AKTIVA, REPORTY A LEAN CANVAS
# ==========================================
with tab_aktiva:
    st.subheader("Odevzdané materiály a Business Model")
    
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.markdown("#### Vizuální identita (Brand)")
        if firma.get('logo_url'): st.markdown(f"🎨 <a href='{firma['logo_url']}' class='asset-link' target='_blank'>Firemní Logo</a>", unsafe_allow_html=True)
        if firma.get('web_url'): st.markdown(f"🌐 <a href='{firma['web_url']}' class='asset-link' target='_blank'>Webové stránky</a>", unsafe_allow_html=True)
        if firma.get('promo_url'): st.markdown(f"📄 <a href='{firma['promo_url']}' class='asset-link' target='_blank'>Pitch Deck / Leták</a>", unsafe_allow_html=True)
        if not firma.get('logo_url') and not firma.get('web_url'): st.info("Firma zatím nedodala odkazy na brand.")
        
    with col_a2:
        st.markdown("#### Lean Canvas (Strategie)")
        if canvas:
            c = canvas[0]
            with st.expander("Zobrazit detailní Lean Canvas"):
                st.write("**Problém:**", c['problem'])
                st.write("**Řešení:**", c['reseni'])
                st.write("**Cílová skupina:**", c['cilova_skupina'])
                st.write("**Unikátní hodnota:**", c['unikatni_hodnota'])
        else:
            st.info("Lean Canvas nebyl vyplněn.")

    st.markdown("---")
    st.markdown("#### Odevzdané dokumenty a reporty")
    if reporty:
        df_rep = pd.DataFrame(reporty)[['typ_reportu', 'nazev_reportu', 'odkaz_soubor', 'datum_odevzdani']]
        st.dataframe(df_rep, use_container_width=True)
        for r in reporty:
            st.markdown(f"📥 <a href='{r['odkaz_soubor']}' class='asset-link' target='_blank'>Otevřít: {r['nazev_reportu']} ({r['typ_reportu']})</a>", unsafe_allow_html=True)
    else:
        st.info("Žádné reporty ani prototypy zatím nebyly odevzdány.")


# ==========================================
# TAB 3: HR, MZDY A STAND-UPY
# ==========================================
with tab_hr:
    st.subheader("Personalistika a Zápisy z porad")
    
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        st.markdown("#### Mzdová listina a Hodnocení týmu")
        if zamestnanci:
            df_zam = pd.DataFrame(zamestnanci)[['jmeno_zamestnance', 'pozice', 'hodinova_sazba', 'odpracovane_hodiny', 'vyplaceno_celkem', 'hodnoceni_skore']]
            df_zam.rename(columns={'jmeno_zamestnance': 'Jméno', 'pozice': 'Role', 'hodinova_sazba': 'Sazba/hod', 'vyplaceno_celkem': 'Vyplaceno', 'hodnoceni_skore': '360° Skóre'}, inplace=True)
            st.dataframe(df_zam, use_container_width=True)
        else:
            st.info("Žádní zaměstnanci nebyli onboardováni.")
            
    with col_h2:
        st.markdown("#### Poslední zápisy z porad (Agile)")
        if porady:
            for p in porady[:3]: # Zobrazí poslední 3
                st.markdown(f"<div class='card-box'><small style='color:#f43f5e;'>{p['datum'][:10]}</small><br><b>Projednáno:</b> {p['projednane_body']}<br><b>Úkoly:</b> {p['ukoly_a_odpovednost']}</div>", unsafe_allow_html=True)
        else:
            st.info("Tým neeviduje žádné porady.")


# ==========================================
# TAB 4: AUDIT - KALKULACE A ÚČETNICTVÍ
# ==========================================
with tab_finance:
    st.subheader("Finanční audit a Schvalování produktů")
    
    # 1. KALKULACE PRODUKTŮ
    st.markdown("#### Ke schválení: Prodejní ceny produktů/služeb")
    if kalkulace:
        for k in kalkulace:
            barva = "status-ok" if k['schvaleno_uradem'] else "status-wait"
            st.markdown(f"<div class='card-box'><h5>{k['nazev_produktu']} <span class='{barva}'>{'Schváleno' if k['schvaleno_uradem'] else 'Čeká na audit'}</span></h5>"
                        f"<p>Náklady: {k['prime_naklady']} M-K | Režie: {k['rezie_skoly']} M-K | Marže: {k['marze_zisk']} M-K | M-TECH Daň: {k['mtech_dan_procento']} %</p>"
                        f"<h4>Konečná prodejní cena: {k['konecna_cena']} M-K</h4></div>", unsafe_allow_html=True)
            
            if not k['schvaleno_uradem']:
                if st.button("✅ Schválit kalkulaci a povolit prodej", key=f"kalk_{k['id']}"):
                    requests.patch(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy?id=eq.{k['id']}", headers=headers, json={"schvaleno_uradem": True})
                    st.success(f"Produkt {k['nazev_produktu']} byl schválen pro trh!")
                    st.rerun()
    else:
        st.info("Firma zatím nepodala žádný kalkulační list.")

    st.write("---")

    # 2. AUDIT CASH-FLOW
    st.markdown("#### Audit Knihy příjmů a výdajů")
    st.caption("Jako daňový úřad můžete kontrolovat oprávněnost výdajů a příjmů firmy a opatřit je 'Auditním razítkem'.")
    if ucto:
        df_ucto = pd.DataFrame(ucto)
        
        # Auditní akce
        neauditovane = [u for u in ucto if not u['auditovano']]
        if neauditovane:
            st.warning(f"Nalezeno {len(neauditovane)} neauditovaných transakcí.")
            if st.button("⚖️ Udělit auditní razítko všem transakcím (Schválit účetnictví)", icon=":material/done_all:"):
                for u in neauditovane:
                    requests.patch(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?id=eq.{u['id']}", headers=headers, json={"auditovano": True})
                st.success("Účetnictví bylo auditováno!")
                st.rerun()
        else:
            st.success("Všechny transakce jsou auditované a v pořádku.")

        # Zobrazení tabulky
        df_show = df_ucto[['datum', 'typ_transakce', 'titul', 'castka', 'auditovano']]
        st.dataframe(df_show.style.applymap(lambda x: "background-color: #22c55e" if x else "background-color: #f59e0b", subset=['auditovano']), use_container_width=True)
    else:
        st.info("Kniha příjmů a výdajů je prázdná.")
