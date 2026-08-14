import streamlit as st
import requests
import pandas as pd
import datetime

st.set_page_config(page_title="Moje peněženka a Úřad práce", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3, h4 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #00B4D8; width: 100%; font-weight: 600; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0, 180, 216, 0.4); border-color: #00B4D8; background-color: #0f172a; color: white;}
    .card-box { background-color: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 15px; }
    .kredit-badge { font-size: 2.2em; font-weight: 800; color: #38bdf8; }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.get("prihlasen"):
    st.warning("Pro zobrazení své peněženky se musíte přihlásit.")
    st.stop()

st.title("Osobní účet a Úřad práce")

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}
except Exception:
    st.error("Chybí konfigurace databáze.")
    st.stop()

uzivatel = st.session_state.get("uzivatel", "")
skolni_kod = st.session_state.get("skolni_kod", "")

# Načtení aktuálních dat uživatele přímo z databáze
res_u = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{uzivatel}", headers=headers).json()
if res_u and isinstance(res_u, list) and len(res_u) > 0:
    moje_kredity = int(res_u[0].get("kredity", 0))
    st.session_state.kredity = moje_kredity
    moje_trida = res_u[0].get("trida_nazev", "Nezařazeno")
else:
    moje_kredity = int(st.session_state.get("kredity", 0))
    moje_trida = "Nezařazeno"

# Zjištění, v jaké firmě uživatel působí (aby jí nemohl posílat peníze)
res_moje_f = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?skolni_kod=eq.{skolni_kod}&select=*", headers=headers).json()
vsechny_firmy = res_moje_f if isinstance(res_moje_f, list) else []

moje_vlastni_firma = next((f for f in vsechny_firmy if uzivatel.lower() in [
    str(f.get('ceo_jmeno','')).lower(),
    str(f.get('cfo_jmeno','')).lower(),
    str(f.get('cto_jmeno','')).lower()
]), None)

if not moje_vlastni_firma:
    res_z_check = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?jmeno_zamestnance=eq.{uzivatel}", headers=headers).json()
    if isinstance(res_z_check, list) and len(res_z_check) > 0:
        f_id_zam = res_z_check[0].get('firma_id')
        moje_vlastni_firma = next((f for f in vsechny_firmy if f['id'] == f_id_zam), None)

moje_firma_nazev = moje_vlastni_firma['nazev_firmy'] if moje_vlastni_firma else None

tab_penize, tab_urad, tab_id, tab_investice = st.tabs([
    "1. Moje peněženka a Platby", "2. Úřad práce (Výdělek)", "3. M-TECH ID & Kariéra", "4. Investiční portfolio"
])

# ==========================================
# 1. PENĚŽENKA A PLATBY
# ==========================================
with tab_penize:
    col_p1, col_p2 = st.columns([1, 2])
    with col_p1:
        with st.container(border=True):
            st.caption("Aktuální osobní zůstatek")
            st.markdown(f"<div class='kredit-badge'>{moje_kredity} M-K</div>", unsafe_allow_html=True)
            st.caption(f"Třída: **{moje_trida}** | Uživatel: **{uzivatel}**")
            if moje_firma_nazev:
                st.caption(f"Člen firmy: **{moje_firma_nazev}**")
    
    with col_p2:
        with st.container(border=True):
            st.subheader("Odeslat platbu / Převod kreditů")
            typ_platby = st.radio("Příjemce platby:", ["Spolužákovi (P2P převod)", "Cizí firmě (Platba za zakázku)"], horizontal=True)
            
            # --- PLATBA SPOLUŽÁKOVI ---
            if typ_platby == "Spolužákovi (P2P převod)":
                res_ostatni = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?skolni_kod=eq.{skolni_kod}&role=neq.ucitel", headers=headers).json()
                seznam_lidi = [u['jmeno'] for u in (res_ostatni if isinstance(res_ostatni, list) else []) if u['jmeno'] != uzivatel]
                
                with st.form("form_p2p_platba"):
                    cilovy_zak = st.selectbox("Vyberte příjemce:", seznam_lidi) if seznam_lidi else None
                    castka_p2p = st.number_input("Částka k odeslání (M-K):", min_value=1, max_value=max(1, moje_kredity), value=min(10, max(1, moje_kredity)), step=1)
                    
                    if st.form_submit_button("Odeslat peníze spolužákovi"):
                        if not cilovy_zak:
                            st.error("Není vybrán žádný příjemce.")
                        elif moje_kredity < castka_p2p:
                            st.error("Nemáte dostatek kreditů.")
                        else:
                            r_rec = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{cilovy_zak}", headers=headers).json()
                            if r_rec and isinstance(r_rec, list):
                                novy_prijemce = int(r_rec[0].get("kredity", 0) + castka_p2p)
                                novy_odesilatel = int(moje_kredity - castka_p2p)
                                requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{cilovy_zak}", headers=headers, json={"kredity": novy_prijemce})
                                requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{uzivatel}", headers=headers, json={"kredity": novy_odesilatel})
                                st.success(f"Odesláno {castka_p2p} M-K uživateli {cilovy_zak}.")
                                st.rerun()

            # --- PLATBA CIZÍ FIRMĚ (S BLOKACÍ VLASTNÍ FIRMY) ---
            else:
                cizi_firmy = [f for f in vsechny_firmy if f.get('stave_licence') == 'SCHVALENO' and f.get('nazev_firmy') != moje_firma_nazev]
                
                if not cizi_firmy:
                    st.info("V systému zatím nejsou žádné jiné schválené firmy, kterým by bylo možné platit.")
                else:
                    with st.form("form_platba_firme"):
                        cilova_f_nazev = st.selectbox("Vyberte firmu:", [f['nazev_firmy'] for f in cizi_firmy])
                        castka_firma = st.number_input("Částka za zakázku / produkt (M-K):", min_value=1, max_value=max(1, moje_kredity), value=min(20, max(1, moje_kredity)), step=1)
                        ucel_platby = st.text_input("Účel platby / specifikace zakázky:", value="Nákup prototypu / služby")
                        
                        if st.form_submit_button("Zaplatit firmě"):
                            if moje_kredity < castka_firma:
                                st.error("Nemáte dostatek kreditů.")
                            else:
                                target_f = next((f for f in cizi_firmy if f['nazev_firmy'] == cilova_f_nazev), None)
                                if target_f:
                                    # 1. Stržení z peněženky žáka
                                    novy_odesilatel = int(moje_kredity - castka_firma)
                                    requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{uzivatel}", headers=headers, json={"kredity": novy_odesilatel})
                                    
                                    # 2. Připsání na účet CEO firmy
                                    r_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{target_f['ceo_jmeno']}", headers=headers).json()
                                    if r_ceo:
                                        novy_ceo_bal = int(r_ceo[0].get("kredity", 0) + castka_firma)
                                        requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{target_f['ceo_jmeno']}", headers=headers, json={"kredity": novy_ceo_bal})
                                    
                                    # 3. Zaevidování tržby do knihy transakcí dané firmy
                                    requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={
                                        "firma_id": target_f['id'],
                                        "typ_transakce": "PRIJEM",
                                        "titul": f"Tržba: {ucel_platby} (Zákazník: {uzivatel})",
                                        "castka": castka_firma,
                                        "auditovano": True
                                    })
                                    st.success(f"Platba {castka_firma} M-K byla úspěšně připsána firmě {cilova_f_nazev}.")
                                    st.rerun()

# ==========================================
# 2. ÚŘAD PRÁCE (QUESTY OD UČITELE)
# ==========================================
with tab_urad:
    st.subheader("Dostupné brigády a úkoly k výdělku")
    st.caption("Zde můžete plnit úkoly vypsané vyučujícím a vydělat si počáteční kapitál na podnikání nebo nákupy.")
    
    res_q = requests.get(f"{SUPABASE_URL}/rest/v1/questy?stav=eq.VOLNY&order=id.desc", headers=headers).json()
    questy = res_q if isinstance(res_q, list) else []
    
    if not questy:
        st.info("Na Úřadu práce momentálně nejsou žádné volné úkoly. Požádejte vyučujícího o vypsání nových úkolů.")
    else:
        for q in questy:
            with st.container(border=True):
                col_q1, col_q2 = st.columns([3, 1])
                with col_q1:
                    st.markdown(f"#### {q['nazev']}")
                    st.write(q.get('popis', 'Bez popisu'))
                    st.caption(f"Zadavatel: **{q.get('zadavatel', 'Učitel')}**")
                with col_q2:
                    st.markdown(f"**Odměna:** `{q.get('odmena', 0)} M-K`")
                    if st.button(f"Přijmout a splnit úkol", key=f"btn_q_{q['id']}"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/questy?id=eq.{q['id']}", headers=headers, json={
                            "resitel": uzivatel,
                            "stav": "K_KONTROLE"
                        })
                        st.success("Úkol byl odeslán vyučujícímu ke kontrole a proplacení odměny.")
                        st.rerun()

# ==========================================
# 3. M-TECH ID & KARIÉRA
# ==========================================
with tab_id:
    st.subheader("M-TECH Digitální Identita")
    with st.container(border=True):
        col_id1, col_id2 = st.columns(2)
        with col_id1:
            st.markdown(f"**Jméno studenta:** `{uzivatel}`")
            st.markdown(f"**Školní instituce:** `{skolni_kod}`")
            st.markdown(f"**Třída:** `{moje_trida}`")
        with col_id2:
            st.markdown(f"**Role v ekosystému:** `{'Podnikatel / Vedení' if moje_firma_nazev else 'Žák'}`")
            st.markdown(f"**Příslušnost k firmě:** `{moje_firma_nazev or 'Bez firemní příslušnosti'}`")

# ==========================================
# 4. INVESTIČNÍ PORTFOLIO
# ==========================================
with tab_investice:
    st.subheader("Moje investice a Akcie firem")
    res_moje_akcie = requests.get(f"{SUPABASE_URL}/rest/v1/vlastnici_akcii?majitel_jmeno=eq.{uzivatel}", headers=headers).json()
    if res_moje_akcie and isinstance(res_moje_akcie, list) and len(res_moje_akcie) > 0:
        st.dataframe(pd.DataFrame(res_moje_akcie)[['firma_id', 'pocet_akcii']], use_container_width=True)
    else:
        st.info("Zatím nevlastníte žádné akcie studentských firem. Můžete je nakoupit na Tržišti produktů a Burze.")
