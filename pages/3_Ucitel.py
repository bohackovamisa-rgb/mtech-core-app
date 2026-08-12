import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Kontrolní úřad", page_icon=":material/account_balance:", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #00B4D8; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0, 180, 216, 0.4); border-color: #00B4D8; }
    .card-box { background-color: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #334155; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

st.title(":material/account_balance: Kontrolní úřad & Audity (Učitel)")

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

tab_licence, tab_produkty, tab_audit, tab_export = st.tabs([
    "🏢 1. Licenční úřad (Firmy)", 
    "📦 2. Schvalování produktů", 
    "🔍 3. Finanční audit knih", 
    "📊 4. Exporty dat & Hodnocení"
])

# --- TAB 1: LICENČNÍ ÚŘAD ---
with tab_licence:
    st.subheader("Schvalování nových žádostí o provoz firmy")
    res_firmy = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?select=*", headers=headers)
    firmy = res_firmy.json() if res_firmy.status_code == 200 else []
    
    cekajici = [f for f in firmy if f.get("stave_licence") == "CEKA_NA_SCHVALENI"]
    
    if cekajici:
        for f in cekajici:
            col_a, col_b = st.columns([3, 2])
            with col_a:
                st.markdown(f"""
                    <div class="card-box">
                        <h4 style="margin:0; color:#00B4D8;">{f['nazev_firmy']} (Level {f['uroven_projektu']})</h4>
                        <p><b>Management:</b> CEO: {f['ceo_jmeno']} | CFO: {f['cfo_jmeno']} | CTO: {f['cto_jmeno']}</p>
                        <p><b>Záměr:</b> {f['podnikatelsky_zamer']}</p>
                        <small>Kód školy: {f['skolni_kod']} | Počáteční vklad: {f['pocatecni_kapital']} M-Kreditů</small>
                    </div>
                """, unsafe_allow_html=True)
            with col_b:
                if st.button("✅ Udělit licenci", key=f"ok_firm_{f['id']}"):
                    requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{f['id']}", headers=headers, json={"stave_licence": "SCHVALENO", "duvod_zamitnuti": None})
                    st.success(f"Licence udělena firmě {f['nazev_firmy']}!")
                    st.rerun()
                
                duvod = st.text_input("Důvod zamítnutí / co opravit:", key=f"reason_{f['id']}")
                if st.button("❌ Zamítnout s důvodem", key=f"no_firm_{f['id']}"):
                    if duvod:
                        requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{f['id']}", headers=headers, json={"stave_licence": "ZAMITNUTO", "duvod_zamitnuti": duvod})
                        st.warning(f"Žádost zamítnuta s důvodem.")
                        st.rerun()
                    else:
                        st.error("Vyplňte prosím důvod zamítnutí!")
    else:
        st.success("Žádné čekající žádosti o licenci.")

    st.write("---")
    st.caption("Přehled všech evidovaných firem:")
    if firmy:
        st.dataframe(pd.DataFrame(firmy), use_container_width=True)

# --- TAB 2: SCHVALOVÁNÍ PRODUKTŮ ---
with tab_produkty:
    st.subheader("Schvalování Kalkulačních listů před vstupem na trh")
    res_kalk = requests.get(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy?select=*", headers=headers)
    kalkulace = res_kalk.json() if res_kalk.status_code == 200 else []
    
    neschvalene = [k for k in kalkulace if not k.get("schvaleno_uradem", False)]
    
    if neschvalene:
        for k in neschvalene:
            col_k1, col_k2 = st.columns([3, 1])
            with col_k1:
                st.markdown(f"""
                    <div class="card-box">
                        <h4 style="margin:0;">{k['nazev_produktu']}</h4>
                        <p>Přímé náklady: <b>{k['prime_naklady']} M-K</b> | Režie: <b>{k['rezie_skoly']} M-K</b> | Marže: <b>{k['marze_zisk']} M-K</b></p>
                        <p>M-TECH Daň: <b>{k['mtech_dan_procento']}%</b> | Konečná prodejní cena: <b>{k['konecna_cena']} M-Kreditů</b></p>
                    </div>
                """, unsafe_allow_html=True)
            with col_k2:
                if st.button("Schválit kalkulaci", key=f"app_kalk_{k['id']}"):
                    requests.patch(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy?id=eq.{k['id']}", headers=headers, json={"schvaleno_uradem": True})
                    st.success(f"Produkt {k['nazev_produktu']} byl schválen k prodeji!")
                    st.rerun()
    else:
        st.info("Žádné nové kalkulační listy k posouzení.")

# --- TAB 3: FINANČNÍ AUDIT KNIH ---
with tab_audit:
    st.subheader("Finanční audit Knih příjmů a výdajů")
    res_kniha = requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?select=*", headers=headers)
    polozky = res_kniha.json() if res_kniha.status_code == 200 else []
    neauditovane = [p for p in polozky if not p.get("auditovano", False)]
    
    if neauditovane:
        st.warning(f"Nalezeno {len(neauditovane)} neoverených účetních operací.")
        if st.button("Udělit hromadné Auditní razítko"):
            for p in neauditovane:
                requests.patch(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?id=eq.{p['id']}", headers=headers, json={"auditovano": True})
            st.success("Všechny položky byly auditovány!")
            st.rerun()
            
    if polozky:
        st.dataframe(pd.DataFrame(polozky), use_container_width=True)

# --- TAB 4: EXPORTY DAT A HODNOCENÍ ---
with tab_export:
    st.subheader("Export dat a Pedagogické hodnocení (Pilíře I–III)")
    col_ex1, col_ex2, col_ex3 = st.columns(3)
    
    with col_ex1:
        st.markdown("**1. Registr Firem & Licencí**")
        if firmy:
            st.download_button("💾 Stáhnout CSV (Firmy)", data=pd.DataFrame(firmy).to_csv(index=False).encode('utf-8'), file_name="firmy_mtech_core.csv", mime="text/csv")
            
    with col_ex2:
        st.markdown("**2. Produktové kalkulace**")
        if kalkulace:
            st.download_button("💾 Stáhnout CSV (Kalkulace)", data=pd.DataFrame(kalkulace).to_csv(index=False).encode('utf-8'), file_name="kalkulace_mtech_core.csv", mime="text/csv")

    with col_ex3:
        st.markdown("**3. Účetní kniha & Audity**")
        if polozky:
            st.download_button("💾 Stáhnout CSV (Účetnictví)", data=pd.DataFrame(polozky).to_csv(index=False).encode('utf-8'), file_name="ucto_mtech_core.csv", mime="text/csv")
