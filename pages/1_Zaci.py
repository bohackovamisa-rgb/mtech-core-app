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

moje_jmeno = "zak"

# Hlavní metrika
col_stav, col_info = st.columns([1, 2])
with col_stav:
    st.metric("Aktuální zůstatek", f"{st.session_state.get('kredity', 0)} M-Kreditů")

st.write("---")

# --- NABÍDKA TRŽIŠTĚ / ZAKÁZEK ---
st.subheader(":: Tržiště zakázek a služeb firem")
res_zakazky = requests.get(f"{SUPABASE_URL}/rest/v1/zakazky?select=*", headers=headers)

if res_zakazky.status_code == 200 and len(res_zakazky.json()) > 0:
    vsechny_zakazky = res_zakazky.json()
    cols = st.columns(3)
    
    for idx, z in enumerate(vsechny_zakazky):
        with cols[idx % 3]:
            st.markdown(f"""
                <div style="padding: 15px; border-radius: 10px; background-color: #1e293b; border: 1px solid #334155; margin-bottom: 15px;">
                    <h4 style="margin: 0; color: #00B4D8;">{z['nazev']}</h4>
                    <p style="margin: 5px 0; color: #94a3b8; font-size: 0.9em;">Firma: <b>{z['firma']}</b></p>
                    <p style="margin: 10px 0;">{z['popis']}</p>
                    <h3 style="margin: 10px 0; color: #38bdf8;">{z['cena']} M-Kreditů</h3>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Koupit / Objednat", key=f"buy_{z['id']}"):
                aktualni_kredity = st.session_state.get("kredity", 0)
                cena_prodej = z["cena"]
                prijemce_firma = z["firma"]
                
                if aktualni_kredity < cena_prodej:
                    st.error("Nemáte dostatek M-Kreditů na tuto zakázku!")
                else:
                    # 1. Odečíst žákovi
                    novy_stav_zak = aktualni_kredity - cena_prodej
                    requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_jmeno}", headers=headers, json={"kredity": novy_stav_zak})
                    
                    # 2. Přičíst firmě
                    res_firma = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{prijemce_firma}", headers=headers)
                    firma_data = res_firma.json() if res_firma.status_code == 200 else []
                    firma_kredity = firma_data[0]["kredity"] if firma_data else 0
                    
                    requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{prijemce_firma}", headers=headers, json={"kredity": firma_kredity + cena_prodej})
                    
                    # 3. Zapsat transakci
                    transakce_payload = {
                        "odesilatel": moje_jmeno,
                        "prijemce": prijemce_firma,
                        "castka": cena_prodej,
                        "popis": f"Nákup: {z['nazev']}"
                    }
                    requests.post(f"{SUPABASE_URL}/rest/v1/transakce", headers=headers, json=transakce_payload)
                    
                    st.session_state.kredity = novy_stav_zak
                    st.success(f"Zakázka '{z['nazev']}' byla zakoupena!")
                    st.rerun()
else:
    st.info("Zatím nejsou k dispozici žádné zakázky od firem.")

st.write("---")

# --- FORMULÁŘ PRO PŘÍMOU PLATBU A HISTORIE ---
col_platba, col_historie = st.columns(2)

with col_platba:
    st.subheader(":: Přímý převod M-Kreditů")
    res_users = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?select=jmeno,kredity", headers=headers)
    vsichni_uzivatele = res_users.json() if res_users.status_code == 200 else []
    prijemci = [u["jmeno"] for u in vsichni_uzivatele if u["jmeno"] != moje_jmeno]
    
    vybrany_prijemce = st.selectbox("Komu posíláte platbu:", prijemci if prijemci else ["firma"])
    posilana_castka = st.number_input("Částka M-Kreditů:", min_value=1, value=10)
    zprava = st.text_input("Poznámka / Účel platby:", value="Přímá platba")
    
    if st.button("Odeslat M-Kredity"):
        aktualni_kredity = st.session_state.get("kredity", 0)
        
        if aktualni_kredity < posilana_castka:
            st.error("Nemáte dostatek M-Kreditů!")
        else:
            novy_stav_odesilatel = aktualni_kredity - posilana_castka
            requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_jmeno}", headers=headers, json={"kredity": novy_stav_odesilatel})
            
            prijemce_data = next((u for u in vsichni_uzivatele if u["jmeno"] == vybrany_prijemce), None)
            prijemce_kredity = prijemce_data["kredity"] if prijemce_data else 0
            
            requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{vybrany_prijemce}", headers=headers, json={"kredity": prijemce_kredity + posilana_castka})
            
            transakce_payload = {
                "odesilatel": moje_jmeno,
                "prijemce": vybrany_prijemce,
                "castka": posilana_castka,
                "popis": zprava
            }
            requests.post(f"{SUPABASE_URL}/rest/v1/transakce", headers=headers, json=transakce_payload)
            
            st.session_state.kredity = novy_stav_odesilatel
            st.success(f"Platba {posilana_castka} M-Kreditů odeslána!")
            st.rerun()

with col_historie:
    st.subheader(":: Výpis mé historie")
    res_trans = requests.get(f"{SUPABASE_URL}/rest/v1/transakce?or=(odesilatel.eq.{moje_jmeno},prijemce.eq.{moje_jmeno})&order=datum.desc", headers=headers)
    
    if res_trans.status_code == 200 and len(res_trans.json()) > 0:
        for t in res_trans.json():
            je_odesilatel = t["odesilatel"] == moje_jmeno
            znamenko = "-" if je_odesilatel else "+"
            druha_strana = f"pro {t['prijemce']}" if je_odesilatel else f"od {t['odesilatel']}"
            
            st.markdown(f"""
                <div style="padding: 10px; border-radius: 8px; background-color: #1e293b; margin-bottom: 8px; border-left: 4px solid {'#ef4444' if je_odesilatel else '#22c55e'};">
                    <strong>{znamenko}{t['castka']} M-Kreditů</strong> ({druha_strana})<br>
                    <small style="color: #94a3b8;">{t['popis']} | {t['datum'][:10]}</small>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Zatím žádné transakce.")
