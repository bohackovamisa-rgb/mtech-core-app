import streamlit as st
import requests

st.set_page_config(page_title="Moje peněženka", page_icon=":material/wallet:", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #00B4D8; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0, 180, 216, 0.4); border-color: #00B4D8; }
    </style>
""", unsafe_allow_html=True)

st.title(":material/wallet: Moje peněženka")

# --- KONEKTOR K DATABÁZI ---
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
    st.error("Chybí konfigurace databáze!")
    st.stop()

# Získání aktuálního přihlášeného uživatele (výchozí zak)
moje_jmeno = "zak"

# --- HLAVNÍ METRIKA ---
col_stav, col_info = st.columns([1, 2])
with col_stav:
    st.metric("Aktuální zůstatek", f"{st.session_state.get('kredity', 0)} M-Kreditů")

st.write("---")

# --- FORMULÁŘ PRO PLATBU / PREVOD ---
col_platba, col_historie = st.columns(2)

with col_platba:
    st.subheader(":: Send Platba / Převod")
    
    # Načtení ostatních uživatelů jako příjemců
    res_users = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?select=jmeno,kredity", headers=headers)
    vsichni_uzivatele = res_users.json() if res_users.status_code == 200 else []
    prijemci = [u["jmeno"] for u in vsichni_uzivatele if u["jmeno"] != moje_jmeno]
    
    vybrany_prijemce = st.selectbox("Komu posíláte platbu:", prijemci if prijemci else ["firma"])
    posilana_castka = st.number_input("Částka M-Kreditů:", min_value=1, max_value=int(st.session_state.get("kredity", 0)) if st.session_state.get("kredity", 0) > 0 else 1, value=10)
    zprava = st.text_input("Poznámka / Účel platby:", value="Nákup zboží / Služba")
    
    if st.button("Odeslat M-Kredity"):
        aktualni_kredity = st.session_state.get("kredity", 0)
        
        if aktualni_kredity < posilana_castka:
            st.error("Nemáte dostatek M-Kreditů!")
        else:
            # 1. Odečíst odesílateli
            novy_stav_odesilatel = aktualni_kredity - posilana_castka
            requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_jmeno}", headers=headers, json={"kredity": novy_stav_odesilatel})
            
            # 2. Přičíst příjemci
            prijemce_data = next((u for u in vsichni_uzivatele if u["jmeno"] == vybrany_prijemce), None)
            prijemce_kredity = prijemce_data["kredity"] if prijemce_data else 0
            novy_stav_prijemce = prijemce_kredity + posilana_castka
            requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{vybrany_prijemce}", headers=headers, json={"kredity": novy_stav_prijemce})
            
            # 3. Zapsat transakci do historie
            transakce_payload = {
                "odesilatel": moje_jmeno,
                "prijemce": vybrany_prijemce,
                "castka": posilana_castka,
                "popis": zprava
            }
            requests.post(f"{SUPABASE_URL}/rest/v1/transakce", headers=headers, json=transakce_payload)
            
            # Aktualizace session
            st.session_state.kredity = novy_stav_odesilatel
            st.success(f"Platba {posilana_castka} M-Kreditů úspěšně odeslána uživateli {vybrany_prijemce}!")
            st.rerun()

# --- HISTORIE TRANSAKCÍ ---
with col_historie:
    st.subheader(":: Výpis transakcí")
    res_trans = requests.get(f"{SUPABASE_URL}/rest/v1/transakce?or=(odesilatel.eq.{moje_jmeno},prijemce.eq.{moje_jmeno})&order=datum.desc", headers=headers)
    
    if res_trans.status_code == 200 and len(res_trans.json()) > 0:
        data_trans = res_trans.json()
        
        for t in data_trans:
            je_odesilatel = t["odesilatel"] == moje_jmeno
            znamenko = "-" if je_odesilatel else "+"
            barva = "red" if je_odesilatel else "green"
            druha_strana = f"pro {t['prijemce']}" if je_odesilatel else f"od {t['odesilatel']}"
            
            st.markdown(f"""
                <div style="padding: 10px; border-radius: 8px; background-color: #1e293b; margin-bottom: 8px; border-left: 4px solid {'#ef4444' if je_odesilatel else '#22c55e'};">
                    <strong>{znamenko}{t['castka']} M-Kreditů</strong> ({druha_strana})<br>
                    <small style="color: #94a3b8;">{t['popis']} | {t['datum'][:10]}</small>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Zatím nemáte žádné transakce.")
