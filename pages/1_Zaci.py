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
    .wallet-card h4 { background: none; -webkit-text-fill-color: rgba(255,255,255,0.8); font-size: 1.2em; margin-top: 5px; font-weight: 400; }
    .card-box { background-color: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 15px; }
    .transaction-plus { color: #10b981; font-weight: bold; }
    .transaction-minus { color: #f43f5e; font-weight: bold; }
    .quest-card { border-left: 4px solid #00B4D8; padding: 15px; background: #0f172a; border-radius: 8px; margin-bottom: 10px; }
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

res_u = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{uzivatel}", headers=headers).json()
aktualni_kredity = res_u[0]['kredity'] if res_u else 0
st.session_state.kredity = aktualni_kredity
skolni_kod = res_u[0].get('skolni_kod', 'SYSTEM') if res_u else 'SYSTEM'

res_nastaveni = requests.get(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{skolni_kod}", headers=headers).json()
kurz_kc = float(res_nastaveni[0].get('kurz_kc', 10.0)) if res_nastaveni else 10.0
hodnota_kc = aktualni_kredity * kurz_kc

st.title("Moje Peněženka a Úřad práce")

st.markdown(f"""
    <div class="wallet-card">
        <p style="margin:0; font-size: 1.2em; opacity: 0.9;">Aktuální disponibilní zůstatek</p>
        <h1>{aktualni_kredity:.2f} M-K</h1>
        <h4>(Reálná hodnota: {hodnota_kc:,.0f} Kč)</h4>
        <p style="margin:0; opacity: 0.8; margin-top: 10px;">Majitel účtu: {uzivatel} | Kurz: 1 M-K = {kurz_kc} Kč</p>
    </div>
""", unsafe_allow_html=True)

tab_banka, tab_questy, tab_burza = st.tabs(["Banka a Převody", "Úřad práce (Brigády)", "Investice a Burza"])

with tab_banka:
    col1, col2 = st.columns([1, 1.5])
    with col1:
        st.subheader("Přímá platba (P2P)")
        res_vse = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?select=jmeno,role", headers=headers)
        všichni = [u['jmeno'] for u in res_vse.json() if u['jmeno'] != uzivatel] if res_vse.status_code == 200 else []
        with st.form("platba_form"):
            prijemce = st.selectbox("Komu posíláte platbu:", všichni)
            castka = st.number_input("Částka (M-K):", min_value=1.0, value=10.0, step=1.0)
            ucel = st.text_input("Zpráva pro příjemce (Účel platby):")
            if st.form_submit_button("Odeslat peníze", icon=":material/send_money:"):
                if castka > aktualni_kredity: st.error("Nedostatek prostředků na účtu!")
                elif prijemce:
                    n_odesilatel = aktualni_kredity - castka
                    requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{uzivatel}", headers=headers, json={"kredity": n_odesilatel})
                    res_prijemce = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{prijemce}", headers=headers).json()
                    if res_prijemce: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{prijemce}", headers=headers, json={"kredity": res_prijemce[0]['kredity'] + castka})
                    requests.post(f"{SUPABASE_URL}/rest/v1/bankovni_prevody", headers=headers, json={"odesilatel": uzivatel, "prijemce": prijemce, "castka": castka, "ucel": ucel})
                    st.session_state.kredity = n_odesilatel
                    st.success(f"Platba {castka} M-K odeslána.")
                    st.rerun()
    with col2:
        st.subheader("Historie transakcí")
        res_trans = requests.get(f"{SUPABASE_URL}/rest/v1/bankovni_prevody?or=(odesilatel.eq.{uzivatel},prijemce.eq.{uzivatel})&order=datum.desc", headers=headers)
        transakce = res_trans.json() if res_trans.status_code == 200 else []
        if transakce:
            for t in transakce[:10]:
                datum = t['datum'][:10]
                if t['odesilatel'] == uzivatel: st.markdown(f"<div class='card-box' style='padding: 10px 15px;'><div style='display:flex; justify-content:space-between; align-items:center;'><div><small style='color:#94a3b8;'>{datum} | Pro: <b>{t['prijemce']}</b></small><br><span>{t['ucel']}</span></div><div class='transaction-minus'>- {t['castka']} M-K</div></div></div>", unsafe_allow_html=True)
                else: st.markdown(f"<div class='card-box' style='padding: 10px 15px; border-left: 4px solid #10b981;'><div style='display:flex; justify-content:space-between; align-items:center;'><div><small style='color:#94a3b8;'>{datum} | Od: <b>{t['odesilatel']}</b></small><br><span>{t['ucel']}</span></div><div class='transaction-plus'>+ {t['castka']} M-K</div></div></div>", unsafe_allow_html=True)
        else: st.info("Zatím nemáte žádné přímé bankovní převody.")

with tab_questy:
    st.subheader("Nástěnka úkolů a brigád")
    res_questy = requests.get(f"{SUPABASE_URL}/rest/v1/questy?order=datum_zadani.desc", headers=headers).json()
    if not res_questy: st.info("Zatím nejsou vypsány žádné úkoly.")
    else:
        q_volne = [q for q in res_questy if q['stav'] == 'VOLNY']
        q_moje = [q for q in res_questy if q['resitel'] == uzivatel and q['stav'] in ['V_PROCESU', 'K_KONTROLE']]
        col_q1, col_q2 = st.columns(2)
        with col_q1:
            st.markdown("#### Volné brigády (K přijetí)")
            for q in q_volne:
                odmena_kc = q['odmena'] * kurz_kc
                st.markdown(f"<div class='quest-card'><h4>{q['nazev']}</h4><p>{q['popis']}</p><p><b>Odměna:</b> <span class='transaction-plus'>{q['odmena']} M-K ({odmena_kc:,.0f} Kč)</span></p></div>", unsafe_allow_html=True)
                if st.button("Přijmout úkol", key=f"q_{q['id']}", icon=":material/task:"):
                    requests.patch(f"{SUPABASE_URL}/rest/v1/questy?id=eq.{q['id']}", headers=headers, json={"stav": "V_PROCESU", "resitel": uzivatel})
                    st.rerun()
        with col_q2:
            st.markdown("#### Moje rozpracované úkoly")
            for q in q_moje:
                if q['stav'] == 'V_PROCESU':
                    st.markdown(f"<div class='quest-card' style='border-color:#0ea5e9;'><h4>{q['nazev']}</h4><p>Stav: <b>Řešíte vy</b></p></div>", unsafe_allow_html=True)
                    with st.form(f"f_q_{q['id']}"):
                        odkaz = st.text_input("Odkaz na hotovou práci:")
                        if st.form_submit_button("Odevzdat ke kontrole"):
                            requests.patch(f"{SUPABASE_URL}/rest/v1/questy?id=eq.{q['id']}", headers=headers, json={"stav": "K_KONTROLE", "odkaz_vystup": odkaz})
                            st.rerun()
                elif q['stav'] == 'K_KONTROLE':
                    st.markdown(f"<div class='quest-card' style='border-color:#34d399;'><h4>{q['nazev']}</h4><p>Stav: <b>Čeká na kontrolu učitelem</b></p></div>", unsafe_allow_html=True)

with tab_burza:
    st.subheader("Investiční Burza M-TECH")
    col_b1, col_b2 = st.columns([1.5, 1])
    res_f = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?select=id,nazev_firmy,ceo_jmeno", headers=headers).json()
    firmy_dict = {f['id']: f for f in res_f} if res_f else {}
    
    with col_b1:
        st.markdown("#### Aktivní nabídky akcií (IPO)")
        nabidky = requests.get(f"{SUPABASE_URL}/rest/v1/burza_nabidky?aktivni=eq.true", headers=headers).json()
        if not nabidky: st.info("Momentálně žádná firma nenabízí své akcie.")
        else:
            for n in nabidky:
                firma_info = firmy_dict.get(n['firma_id'])
                if firma_info and n['pocet_k_prodeji'] > 0:
                    cena_akcie_kc = n['cena_za_kus'] * kurz_kc
                    st.markdown(f"<div class='card-box' style='border-left: 4px solid #f59e0b;'><h4>{firma_info['nazev_firmy']}</h4><p>K dispozici: <b>{n['pocet_k_prodeji']} ks</b> | Cena za akcii: <b>{n['cena_za_kus']} M-K ({cena_akcie_kc:,.0f} Kč)</b></p></div>", unsafe_allow_html=True)
                    with st.form(f"buy_shares_{n['id']}"):
                        pocet_koupit = st.number_input("Počet akcií k nákupu:", min_value=1, max_value=n['pocet_k_prodeji'], value=1)
                        celkova_cena = pocet_koupit * n['cena_za_kus']
                        if st.form_submit_button(f"Koupit za {celkova_cena} M-K", icon=":material/shopping_cart:"):
                            if celkova_cena > aktualni_kredity: st.error("Nedostatek prostředků!")
                            else:
                                requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{uzivatel}", headers=headers, json={"kredity": aktualni_kredity - celkova_cena})
                                ceo = firma_info['ceo_jmeno']
                                res_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{ceo}", headers=headers).json()
                                if res_ceo: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{ceo}", headers=headers, json={"kredity": res_ceo[0]['kredity'] + celkova_cena})
                                exist_port = requests.get(f"{SUPABASE_URL}/rest/v1/portfolio_investoru?investor_jmeno=eq.{uzivatel}&firma_id=eq.{n['firma_id']}", headers=headers).json()
                                if exist_port: requests.patch(f"{SUPABASE_URL}/rest/v1/portfolio_investoru?id=eq.{exist_port[0]['id']}", headers=headers, json={"pocet_akcii": exist_port[0]['pocet_akcii'] + pocet_koupit})
                                else: requests.post(f"{SUPABASE_URL}/rest/v1/portfolio_investoru", headers=headers, json={"investor_jmeno": uzivatel, "firma_id": n['firma_id'], "pocet_akcii": pocet_koupit})
                                zbyva = n['pocet_k_prodeji'] - pocet_koupit
                                requests.patch(f"{SUPABASE_URL}/rest/v1/burza_nabidky?id=eq.{n['id']}", headers=headers, json={"pocet_k_prodeji": zbyva, "aktivni": zbyva > 0})
                                requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": n['firma_id'], "typ_transakce": "PRIJEM", "titul": f"Investice od {uzivatel}", "castka": celkova_cena, "auditovano": False})
                                st.rerun()

    with col_b2:
        st.markdown("#### Moje Portfolio")
        portfolio = requests.get(f"{SUPABASE_URL}/rest/v1/portfolio_investoru?investor_jmeno=eq.{uzivatel}", headers=headers).json()
        if not portfolio: st.info("Zatím nevlastníte žádné akcie.")
        else:
            for p in portfolio:
                f_nazev = firmy_dict.get(p['firma_id'], {}).get('nazev_firmy', 'Neznámá firma')
                st.markdown(f"<div class='card-box'><b>{f_nazev}</b><br>Vlastníte: {p['pocet_akcii']} ks</div>", unsafe_allow_html=True)
