import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Moje peněženka", page_icon=":material/wallet:", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #00B4D8; width: 100%; font-weight: 600; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0, 180, 216, 0.4); border-color: #00B4D8; background-color: #0f172a;}
    .wallet-card { background: linear-gradient(135deg, #00B4D8 0%, #0077B6 100%); padding: 30px; border-radius: 16px; color: white; text-align: center; box-shadow: 0 10px 25px rgba(0,180,216,0.3); margin-bottom: 30px; }
    .wallet-card h1 { background: none; -webkit-text-fill-color: white; font-size: 3em; margin: 0; }
    .card-box { background-color: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 15px; }
    .transaction-plus { color: #10b981; font-weight: bold; }
    .transaction-minus { color: #f43f5e; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.get("prihlasen"):
    st.warning("Pro zobrazení peněženky se musíte přihlásit na hlavní obrazovce.")
    st.stop()

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}
except Exception:
    st.error("Chybí konfigurace databáze v Secrets!")
    st.stop()

uzivatel = st.session_state.uzivatel

# Aktuální zůstatek načteme raději čerstvě z DB
res_u = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{uzivatel}", headers=headers)
if res_u.status_code == 200 and res_u.json():
    aktualni_kredity = res_u.json()[0]['kredity']
    st.session_state.kredity = aktualni_kredity
else:
    aktualni_kredity = st.session_state.get("kredity", 0)

st.title("Moje Peněženka")

# Velká bankovní karta
st.markdown(f"""
    <div class="wallet-card">
        <p style="margin:0; font-size: 1.2em; opacity: 0.9;">Aktuální disponibilní zůstatek</p>
        <h1>{aktualni_kredity} M-K</h1>
        <p style="margin:0; opacity: 0.8; margin-top: 10px;">Majitel účtu: {uzivatel}</p>
    </div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("Přímá platba (P2P)")
    st.caption("Pošlete M-Kredity jiné firmě (např. za B2B službu) nebo jinému žákovi (freelancerovi).")
    
    # Načtení všech možných příjemců
    res_vse = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?select=jmeno,role", headers=headers)
    všichni = [u['jmeno'] for u in res_vse.json() if u['jmeno'] != uzivatel] if res_vse.status_code == 200 else []
    
    with st.form("platba_form"):
        prijemce = st.selectbox("Komu posíláte platbu:", všichni)
        castka = st.number_input("Částka (M-K):", min_value=1.0, value=10.0, step=1.0)
        ucel = st.text_input("Zpráva pro příjemce (Účel platby):", placeholder="Např. Faktura za logo")
        
        if st.form_submit_button("Odeslat peníze", icon=":material/send_money:"):
            if castka > aktualni_kredity:
                st.error("Nedostatek prostředků na účtu!")
            elif prijemce:
                # 1. Strhnout peníze odesílateli
                novy_zustatek_odesilatel = aktualni_kredity - castka
                requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{uzivatel}", headers=headers, json={"kredity": novy_zustatek_odesilatel})
                
                # 2. Přidat peníze příjemci
                res_prijemce = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{prijemce}", headers=headers).json()
                if res_prijemce:
                    kredity_prijemce = res_prijemce[0]['kredity'] + castka
                    requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{prijemce}", headers=headers, json={"kredity": kredity_prijemce})
                
                # 3. Zapsat do historie převodů
                requests.post(f"{SUPABASE_URL}/rest/v1/bankovni_prevody", headers=headers, json={
                    "odesilatel": uzivatel, "prijemce": prijemce, "castka": castka, "ucel": ucel
                })
                
                st.session_state.kredity = novy_zustatek_odesilatel
                st.success(f"Platba {castka} M-K byla úspěšně odeslána uživateli {prijemce}.")
                st.rerun()

with col2:
    st.subheader("Historie transakcí")
    st.caption("Zde vidíte všechny své příchozí a odchozí přímé platby.")
    
    # Načtení historie převodů, kde figuruje tento uživatel
    res_trans = requests.get(f"{SUPABASE_URL}/rest/v1/bankovni_prevody?or=(odesilatel.eq.{uzivatel},prijemce.eq.{uzivatel})&order=datum.desc", headers=headers)
    transakce = res_trans.json() if res_trans.status_code == 200 else []
    
    if transakce:
        for t in transakce[:10]: # Zobrazí posledních 10
            datum = t['datum'][:10]
            if t['odesilatel'] == uzivatel:
                # Odchozí platba
                st.markdown(f"""
                    <div class='card-box' style='padding: 10px 15px;'>
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <div>
                                <small style='color:#94a3b8;'>{datum} | Pro: <b>{t['prijemce']}</b></small><br>
                                <span>{t['ucel']}</span>
                            </div>
                            <div class='transaction-minus'>- {t['castka']} M-K</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                # Příchozí platba
                st.markdown(f"""
                    <div class='card-box' style='padding: 10px 15px; border-left: 4px solid #10b981;'>
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <div>
                                <small style='color:#94a3b8;'>{datum} | Od: <b>{t['odesilatel']}</b></small><br>
                                <span>{t['ucel']}</span>
                            </div>
                            <div class='transaction-plus'>+ {t['castka']} M-K</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Zatím nemáte žádné přímé bankovní převody.")
