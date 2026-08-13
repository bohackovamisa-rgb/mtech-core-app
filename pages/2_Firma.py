import streamlit as st
import requests
import datetime
import pandas as pd
import random

st.set_page_config(page_title="Startup Hub a Dashboard", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3, h4 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #00B4D8; width: 100%; font-weight: 600; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0, 180, 216, 0.4); border-color: #00B4D8; background-color: #0f172a; color: white;}
    .card-box { background-color: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 15px; }
    .shark-card { background-color: #0f172a; padding: 15px; border-radius: 10px; border-left: 4px solid #00B4D8; margin-bottom: 10px; }
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

if moje_firma:
    st.subheader(f"Entita: {moje_firma['nazev_firmy']} (ID: #{moje_firma['id']})")
    st.write("---")

tab_zalozeni, tab_brand, tab_vyvoj, tab_hr, tab_kalkulace, tab_ucto, tab_burza = st.tabs([
    "1. Zakladatelský Spis", "2. Brand a AI Mentor", "3. Agilní Vývoj", "4. Tým a HR", "5. Cenotvorba", "6. Účetnictví a Daně", "7. Burza"
])

with tab_zalozeni: st.info("Zakladatelský spis...")

# ==========================================
# 2. BRAND, LEAN CANVAS A AI SHARK TANK
# ==========================================
with tab_brand:
    if not moje_firma:
        st.warning("Nejprve založte firmu.")
    else:
        t_aktiva, t_lean, t_ai_shark = st.tabs(["Vizuální Identita", "Lean Canvas", "🦈 AI Shark Tank (Investoři)"])
        
        with t_aktiva:
            with st.form("form_brand"):
                b_logo = st.text_input("Odkaz na LOGO:", value=moje_firma.get('logo_url','') or "")
                b_web = st.text_input("Odkaz na WEB:", value=moje_firma.get('web_url','') or "")
                if st.form_submit_button("Uložit odkazy"):
                    requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{moje_firma['id']}", headers=headers, json={"logo_url": b_logo, "web_url": b_web})
                    st.rerun()

        with t_lean:
            res_c = requests.get(f"{SUPABASE_URL}/rest/v1/lean_canvas?firma_id=eq.{moje_firma['id']}", headers=headers).json()
            exist_canvas = res_c[0] if res_c else None
            with st.form("form_canvas"):
                col_c1, col_c2 = st.columns(2)
                with col_c1: prob = st.text_area("Problém:", value=exist_canvas.get("problem","") if exist_canvas else "")
                with col_c2: sol = st.text_area("Řešení:", value=exist_canvas.get("reseni","") if exist_canvas else "")
                if st.form_submit_button("Uložit Canvas"):
                    c_payload = {"firma_id": moje_firma["id"], "problem": prob, "reseni": sol}
                    if exist_canvas: requests.patch(f"{SUPABASE_URL}/rest/v1/lean_canvas?id=eq.{exist_canvas['id']}", headers=headers, json=c_payload)
                    else: requests.post(f"{SUPABASE_URL}/rest/v1/lean_canvas", headers=headers, json=c_payload)
                    st.rerun()

        with t_ai_shark:
            st.subheader("Předstupte před AI Investory")
            st.caption("Obhajujte svůj projekt před generativní umělou inteligencí. Pokud investory přesvědčíte, pošlou vám reálný kapitál na firemní účet.")
            
            # Kontrola předchozích pitchů
            res_pitches = requests.get(f"{SUPABASE_URL}/rest/v1/ai_pitches?firma_id=eq.{moje_firma['id']}&order=datum.desc", headers=headers).json()
            
            with st.form("form_pitch"):
                p_nazev = st.text_input("Název investiční prezentace / produktu:")
                p_popis = st.text_area("Detailní pitch (Popište problém, vaše řešení a proč na tom vyděláte):")
                col_p1, col_p2 = st.columns(2)
                with col_p1: p_castka = st.number_input("Požadovaný kapitál od AI Investorů (M-K):", min_value=50, value=200)
                with col_p2: p_akcie = st.number_input("Nabízený počet akcií za investici (ks):", min_value=5, value=20)
                
                if st.form_submit_button("Spustit AI Pitching (Prezentovat před Shark Tank)"):
                    if len(p_popis) < 20:
                        st.error("Pitch je příliš krátký! Investoři potřebují více detailů o vašem projektu.")
                    else:
                        with st.spinner("AI Investoři poslouchají vaši prezentaci a analyzují čísla..."):
                            # Simulace/Generování hodnocení 3 profilů
                            score_ostry = "SCHVALENO" if ("zisk" in p_popis.lower() or "cena" in p_popis.lower() or p_castka <= 300) else "ZAMITNUTO"
                            score_vizionarka = "SCHVALENO" if ("ai" in p_popis.lower() or "inovace" in p_popis.lower() or "ekologie" in p_popis.lower() or "software" in p_popis.lower()) else "ZAMITNUTO"
                            score_rychly = "SCHVALENO" if (len(p_popis) > 80 and p_akcie >= 10) else "ZAMITNUTO"
                            
                            eval_ostry = f"[{score_ostry}] Ing. Viktor Ostrý: " + ("Finanční struktura dává smysl, požadavek na kapitál je přiměřený." if score_ostry == "SCHVALENO" else "Chybí mi detailnější kalkulace návratnosti a marží.")
                            eval_vizionarka = f"[{score_vizionarka}] Elena Vizionářová: " + ("Váš nápad má velký potenciál a přináší skvělou hodnotu na trh!" if score_vizionarka == "SCHVALENO" else "Nenacházím v tom dostatečnou technologickou inovaci ani škálovatelnost.")
                            eval_rychly = f"[{score_rychly}] Petr Rychlý: " + ("Půjdu do toho s vámi, nabídka akcií je fér a chci vidět rychlé výsledky." if score_rychly == "SCHVALENO" else "Riziko je příliš vysoké a nabízíte málo akcií za takový kapitál.")
                            
                            schvaleno = [score_ostry, score_vizionarka, score_rychly].count("SCHVALENO") >= 2
                            
                            # Zápis do databáze
                            requests.post(f"{SUPABASE_URL}/rest/v1/ai_pitches", headers=headers, json={
                                "firma_id": moje_firma['id'], "nazev_pitchu": p_nazev, "popis_projektu": p_popis,
                                "zadana_castka": p_castka, "nabizene_akcie": p_akcie,
                                "hodnoceni_ostry": eval_ostry, "hodnoceni_vizionarka": eval_vizionarka, "hodnoceni_rychly": eval_rychly,
                                "schvaleno_investovano": schvaleno, "investovana_castka": p_castka if schvaleno else 0
                            })
                            
                            if schvaleno:
                                # Přičtení peněz CEO
                                r_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers).json()
                                if r_ceo: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers, json={"kredity": r_ceo[0]['kredity'] + p_castka})
                                requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": "PRIJEM", "titul": f"AI Shark Tank Investice: {p_nazev}", "castka": p_castka, "auditovano": True})
                                requests.post(f"{SUPABASE_URL}/rest/v1/portfolio_investoru", headers=headers, json={"investor_jmeno": "AI Shark Tank Fond", "firma_id": moje_firma["id"], "pocet_akcii": p_akcie})
                            
                            st.rerun()

            st.write("---")
            st.markdown("#### Historie vašich prezentací před AI Shark Tank")
            if res_pitches:
                for pitch in res_pitches:
                    st_barva = "status-badge-ok" if pitch['schvaleno_investovano'] else "status-badge-wait"
                    st.markdown(f"""
                        <div class='card-box'>
                            <div style='display:flex; justify-content:space-between; align-items:center;'>
                                <h4>{pitch['nazev_pitchu']}</h4>
                                <div class='{st_barva}'>{'INVESTICE SCHVÁLENA (+ ' + str(pitch['zadana_castka']) + ' M-K)' if pitch['schvaleno_investovano'] else 'INVESTICE ZAMÍTNUTA'}</div>
                            </div>
                            <p><b>Hodnocení AI Investorů:</b></p>
                            <div class='shark-card'>{pitch['hodnoceni_ostry']}</div>
                            <div class='shark-card'>{pitch['hodnoceni_vizionarka']}</div>
                            <div class='shark-card'>{pitch['hodnoceni_rychly']}</div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Zatím jste před AI Shark Tank neprezentovali žádný projekt.")

with tab_vyvoj: st.info("Agilní vývoj...")
with tab_hr: st.info("HR a Mzdy...")
with tab_kalkulace: st.info("Cenotvorba...")
with tab_ucto: st.info("Účetnictví...")
with tab_burza: st.info("Burza...")
