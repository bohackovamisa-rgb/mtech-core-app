import streamlit as st
import requests
import pandas as pd
import datetime

st.set_page_config(page_title="Moje peněženka", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #00B4D8; width: 100%; font-weight: 600; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0, 180, 216, 0.4); border-color: #00B4D8; background-color: #0f172a;}
    .wallet-card { background: linear-gradient(135deg, #00B4D8 0%, #0077B6 100%); padding: 30px; border-radius: 16px; color: white; text-align: center; box-shadow: 0 10px 25px rgba(0,180,216,0.3); margin-bottom: 20px; }
    .wallet-card h1 { background: none; -webkit-text-fill-color: white; font-size: 3em; margin: 0; }
    .wallet-card h4 { background: none; -webkit-text-fill-color: rgba(255,255,255,0.8); font-size: 1.2em; margin-top: 5px; font-weight: 400; }
    .card-box { background-color: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 15px; }
    .transaction-plus { color: #10b981; font-weight: bold; }
    .transaction-minus { color: #f43f5e; font-weight: bold; }
    .quest-card { border-left: 4px solid #00B4D8; padding: 15px; background: #0f172a; border-radius: 8px; margin-bottom: 10px; }
    .alert-banner { background-color: rgba(239, 68, 68, 0.1); border: 2px solid #ef4444; color: #f87171; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center; font-weight: bold; }
    .crisis-banner { background-color: rgba(245, 158, 11, 0.1); border: 2px solid #f59e0b; color: #fbbf24; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center; font-weight: bold; }
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
u_data = res_u[0] if res_u else {}
aktualni_kredity = u_data.get('kredity', 0)
skolni_kod = u_data.get('skolni_kod', 'SYSTEM')
st.session_state.kredity = aktualni_kredity

res_nastaveni = requests.get(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{skolni_kod}", headers=headers).json()
nastaveni = res_nastaveni[0] if res_nastaveni else {}
kurz_kc = float(nastaveni.get('kurz_kc', 10.0))
hodnota_kc = aktualni_kredity * kurz_kc

st.title("Moje Peněženka a Úřad práce")

if nastaveni.get('aktivni_krize') != 'ZADNA':
    st.markdown(f"<div class='crisis-banner'>GLOBÁLNÍ KRIZE NA TRHU: {nastaveni.get('krize_popis')}</div>", unsafe_allow_html=True)

if not u_data.get('naklady_zaplaceny', True):
    st.markdown("<div class='alert-banner'>POZOR! Nemáte zaplacené životní náklady za tento měsíc! Přejděte do záložky 'M-TECH ID' a účty zaplaťte.</div>", unsafe_allow_html=True)

st.markdown(f"""
    <div class="wallet-card">
        <p style="margin:0; font-size: 1.2em; opacity: 0.9;">Aktuální disponibilní zůstatek</p>
        <h1>{aktualni_kredity:.2f} M-K</h1>
        <h4>(Reálná hodnota: {hodnota_kc:,.0f} Kč)</h4>
        <p style="margin:0; opacity: 0.8; margin-top: 10px;">Majitel účtu: {uzivatel} | Kurz: 1 M-K = {kurz_kc} Kč</p>
    </div>
""", unsafe_allow_html=True)

tab_banka, tab_questy, tab_burza, tab_profil = st.tabs(["1. Banka a Převody", "2. Úřad práce", "3. Burza", "4. M-TECH ID (Certifikát)"])

with tab_banka:
    col1, col2 = st.columns([1, 1.5])
    with col1:
        st.subheader("Přímá platba (P2P)")
        res_vse = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?select=jmeno,role", headers=headers).json()
        všichni = [u['jmeno'] for u in res_vse if u['jmeno'] != uzivatel] if res_vse else []
        with st.form("platba_form"):
            prijemce = st.selectbox("Komu posíláte platbu:", všichni)
            castka = st.number_input("Částka (M-K):", min_value=1.0, value=10.0)
            ucel = st.text_input("Účel platby:")
            if st.form_submit_button("Odeslat peníze"):
                if castka > aktualni_kredity: st.error("Nedostatek prostředků!")
                elif prijemce:
                    requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{uzivatel}", headers=headers, json={"kredity": aktualni_kredity - castka})
                    res_prijemce = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{prijemce}", headers=headers).json()
                    if res_prijemce: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{prijemce}", headers=headers, json={"kredity": res_prijemce[0]['kredity'] + castka})
                    requests.post(f"{SUPABASE_URL}/rest/v1/bankovni_prevody", headers=headers, json={"odesilatel": uzivatel, "prijemce": prijemce, "castka": castka, "ucel": ucel})
                    st.rerun()
    with col2:
        st.subheader("Historie transakcí")
        res_trans = requests.get(f"{SUPABASE_URL}/rest/v1/bankovni_prevody?or=(odesilatel.eq.{uzivatel},prijemce.eq.{uzivatel})&order=datum.desc", headers=headers).json()
        if res_trans:
            for t in res_trans[:10]:
                datum = t['datum'][:10]
                if t['odesilatel'] == uzivatel: st.markdown(f"<div class='card-box' style='padding: 10px;'><div style='display:flex; justify-content:space-between;'><div><small>{datum} | Pro: {t['prijemce']}</small><br><span>{t['ucel']}</span></div><div class='transaction-minus'>- {t['castka']} M-K</div></div></div>", unsafe_allow_html=True)
                else: st.markdown(f"<div class='card-box' style='padding: 10px; border-left: 4px solid #10b981;'><div style='display:flex; justify-content:space-between;'><div><small>{datum} | Od: {t['odesilatel']}</small><br><span>{t['ucel']}</span></div><div class='transaction-plus'>+ {t['castka']} M-K</div></div></div>", unsafe_allow_html=True)

with tab_questy:
    st.subheader("Nástěnka úkolů")
    res_questy = requests.get(f"{SUPABASE_URL}/rest/v1/questy?order=datum_zadani.desc", headers=headers).json()
    if not res_questy: st.info("Zatím nejsou vypsány žádné úkoly.")
    else:
        q_volne = [q for q in res_questy if q['stav'] == 'VOLNY']
        q_moje = [q for q in res_questy if q['resitel'] == uzivatel and q['stav'] in ['V_PROCESU', 'K_KONTROLE']]
        col_q1, col_q2 = st.columns(2)
        with col_q1:
            st.markdown("#### Volné brigády")
            for q in q_volne:
                st.markdown(f"<div class='quest-card'><h4>{q['nazev']}</h4><p>{q['popis']}</p><p><b>Odměna:</b> <span class='transaction-plus'>{q['odmena']} M-K ({q['odmena'] * kurz_kc:,.0f} Kč)</span></p></div>", unsafe_allow_html=True)
                if st.button("Přijmout úkol", key=f"q_{q['id']}"):
                    requests.patch(f"{SUPABASE_URL}/rest/v1/questy?id=eq.{q['id']}", headers=headers, json={"stav": "V_PROCESU", "resitel": uzivatel})
                    st.rerun()
        with col_q2:
            st.markdown("#### Moje úkoly")
            for q in q_moje:
                if q['stav'] == 'V_PROCESU':
                    st.markdown(f"<div class='quest-card' style='border-color:#0ea5e9;'><h4>{q['nazev']}</h4><p>Stav: <b>Řešíte vy</b></p></div>", unsafe_allow_html=True)
                    with st.form(f"f_q_{q['id']}"):
                        odkaz = st.text_input("Odkaz na hotovou práci:")
                        if st.form_submit_button("Odevzdat ke kontrole"):
                            requests.patch(f"{SUPABASE_URL}/rest/v1/questy?id=eq.{q['id']}", headers=headers, json={"stav": "K_KONTROLE", "odkaz_vystup": odkaz})
                            st.rerun()
                elif q['stav'] == 'K_KONTROLE':
                    st.markdown(f"<div class='quest-card' style='border-color:#34d399;'><h4>{q['nazev']}</h4><p>Stav: <b>Čeká na schválení učitelem</b></p></div>", unsafe_allow_html=True)

with tab_burza:
    st.subheader("Investiční Burza")
    col_b1, col_b2 = st.columns([1.5, 1])
    res_f = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?select=id,nazev_firmy,ceo_jmeno", headers=headers).json()
    firmy_dict = {f['id']: f['nazev_firmy'] for f in res_f} if res_f else {}
    with col_b1:
        st.markdown("#### Aktivní nabídky akcií")
        nabidky = requests.get(f"{SUPABASE_URL}/rest/v1/burza_nabidky?aktivni=eq.true", headers=headers).json()
        if not nabidky: st.info("Momentálně žádná firma nenabízí akcie.")
        else:
            for n in nabidky:
                f_info = firmy_dict.get(n['firma_id'])
                if f_info and n['pocet_k_prodeji'] > 0:
                    st.markdown(f"<div class='card-box' style='border-left: 4px solid #f59e0b;'><h4>{f_info}</h4><p>K dispozici: <b>{n['pocet_k_prodeji']} ks</b> | Cena: <b>{n['cena_za_kus']} M-K ({n['cena_za_kus'] * kurz_kc:,.0f} Kč)</b></p></div>", unsafe_allow_html=True)
                    with st.form(f"buy_{n['id']}"):
                        pocet = st.number_input("Počet ks:", min_value=1, max_value=n['pocet_k_prodeji'])
                        cena_c = pocet * n['cena_za_kus']
                        if st.form_submit_button(f"Koupit za {cena_c} M-K"):
                            if cena_c <= aktualni_kredity:
                                requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{uzivatel}", headers=headers, json={"kredity": aktualni_kredity - cena_c})
                                f_full = next((f for f in res_f if f['id'] == n['firma_id']), None)
                                ceo = f_full['ceo_jmeno'] if f_full else None
                                if ceo:
                                    r_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{ceo}", headers=headers).json()
                                    if r_ceo: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{ceo}", headers=headers, json={"kredity": r_ceo[0]['kredity'] + cena_c})
                                e_port = requests.get(f"{SUPABASE_URL}/rest/v1/portfolio_investoru?investor_jmeno=eq.{uzivatel}&firma_id=eq.{n['firma_id']}", headers=headers).json()
                                if e_port: requests.patch(f"{SUPABASE_URL}/rest/v1/portfolio_investoru?id=eq.{e_port[0]['id']}", headers=headers, json={"pocet_akcii": e_port[0]['pocet_akcii'] + pocet})
                                else: requests.post(f"{SUPABASE_URL}/rest/v1/portfolio_investoru", headers=headers, json={"investor_jmeno": uzivatel, "firma_id": n['firma_id'], "pocet_akcii": pocet})
                                requests.patch(f"{SUPABASE_URL}/rest/v1/burza_nabidky?id=eq.{n['id']}", headers=headers, json={"pocet_k_prodeji": n['pocet_k_prodeji'] - pocet, "aktivni": (n['pocet_k_prodeji'] - pocet) > 0})
                                st.rerun()
    with col_b2:
        st.markdown("#### Moje Portfolio")
        port = requests.get(f"{SUPABASE_URL}/rest/v1/portfolio_investoru?investor_jmeno=eq.{uzivatel}", headers=headers).json()
        if not port: st.info("Zatím nevlastníte akcie.")
        else:
            for p in port: st.markdown(f"<div class='card-box'><b>{firmy_dict.get(p['firma_id'], 'Neznámá firma')}</b><br>Vlastníte: {p['pocet_akcii']} ks</div>", unsafe_allow_html=True)

with tab_profil:
    col_p1, col_p2 = st.columns([1, 1])
    
    with col_p1:
        st.markdown("#### Můj osobní život (Výdaje)")
        st.caption("Každý měsíc musíte státu zaplatit poplatky za nájem, jídlo a služby.")
        uroven = u_data.get('zivotni_uroven', 'STUDENT')
        zaplaceno = u_data.get('naklady_zaplaceny', True)
        ceny_zivot = {"STUDENT": 30, "STANDARD": 60, "LUXUS": 120}
        castka_k_uhrade = ceny_zivot.get(uroven, 30)
        
        with st.form("form_zivot"):
            nova_uroven = st.radio("Zvolte si životní standard:", ["STUDENT", "STANDARD", "LUXUS"], index=["STUDENT", "STANDARD", "LUXUS"].index(uroven))
            st.markdown(f"**Aktuální měsíční náklad:** `{ceny_zivot[nova_uroven]} M-K` (cca {ceny_zivot[nova_uroven]*kurz_kc:,.0f} Kč)")
            if st.form_submit_button("Uložit životní styl"):
                requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{uzivatel}", headers=headers, json={"zivotni_uroven": nova_uroven})
                st.rerun()
                
        if not zaplaceno:
            st.markdown("---")
            st.error("NEMÁTE ZAPLACENO ZA TENTO MĚSÍC!")
            if st.button(f"Zaplatit složenky ({castka_k_uhrade} M-K)"):
                if aktualni_kredity >= castka_k_uhrade:
                    requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{uzivatel}", headers=headers, json={"kredity": aktualni_kredity - castka_k_uhrade, "naklady_zaplaceny": True})
                    res_stat = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers).json()
                    if res_stat: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers, json={"kredity": res_stat[0]['kredity'] + castka_k_uhrade})
                    requests.post(f"{SUPABASE_URL}/rest/v1/bankovni_prevody", headers=headers, json={"odesilatel": uzivatel, "prijemce": "Stát", "castka": castka_k_uhrade, "ucel": "Platba životních nákladů"})
                    st.success("Složenky zaplaceny, děkujeme!")
                    st.rerun()
                else: st.error("Nemáte dostatek peněz na účtu!")
        else:
            st.success("Složenky za tento měsíc máte zaplacené.")

    with col_p2:
        st.markdown("#### M-TECH ID (Osobní Certifikát)")
        st.caption("Toto je vaše digitální stopa a dovednosti. Můžete si je exportovat do reálného CV.")
        
        xp_it = u_data.get('xp_it', 0)
        xp_mark = u_data.get('xp_marketing', 0)
        xp_byz = u_data.get('xp_byznys', 0)
        celkem_xp = xp_it + xp_mark + xp_byz
        
        st.markdown(f"<div class='card-box' style='text-align:center;'><h3>Celkové Skóre: {celkem_xp} XP</h3></div>", unsafe_allow_html=True)
        st.write("**IT a Technologie**")
        st.progress(min(xp_it / 200.0, 1.0), text=f"{xp_it} XP")
        st.write("**Marketing a Kreativita**")
        st.progress(min(xp_mark / 200.0, 1.0), text=f"{xp_mark} XP")
        st.write("**Byznys a Finance**")
        st.progress(min(xp_byz / 200.0, 1.0), text=f"{xp_byz} XP")
        
        res_moje_firmy = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?or=(ceo_jmeno.eq.{uzivatel},cfo_jmeno.eq.{uzivatel},cto_jmeno.eq.{uzivatel})", headers=headers).json()
        pozice_text = ""
        if res_moje_firmy:
            for f in res_moje_firmy:
                role = "CEO" if f['ceo_jmeno'] == uzivatel else "CFO" if f['cfo_jmeno'] == uzivatel else "CTO"
                pozice_text += f"- **{role}** ve startupu *{f['nazev_firmy']}*\n"
        else:
            pozice_text = "- Nezávislý pracovník / Freelancer na Úřadu práce\n"

        cert_content = f"""# OFICIÁLNÍ M-TECH CERTIFIKÁT
**Jméno držitele:** {uzivatel}
**Datum vystavení:** {datetime.date.today().strftime('%d. %m. %Y')}
**Licenční kód instituce:** {skolni_kod}

## Dosažená úroveň dovedností (XP)
* IT a Technologie: {xp_it} XP
* Marketing a Kreativita: {xp_mark} XP
* Byznys a Finance: {xp_byz} XP
* CELKOVÉ SKÓRE: {celkem_xp} XP

## Pracovní a manažerské zkušenosti
{pozice_text}

## Finanční spolehlivost
Držitel certifikátu má v M-TECH ekosystému platební morálku: **{"VYNIKAJÍCÍ (Bez dluhů)" if zaplaceno else "MÁ ZPOŽDĚNÍ S PLATBOU"}**.

---
*Tento certifikát osvědčuje prokazatelné zkušenosti z praktického podnikatelského simulátoru M-TECH CORE.*
"""
        st.write("---")
        st.download_button(label="Stáhnout M-TECH ID Certifikát (.txt)", data=cert_content, file_name=f"MTECH_ID_{uzivatel}.txt", mime="text/plain")
