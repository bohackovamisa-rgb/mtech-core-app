import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Tržiště produktů", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3, h4 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #00B4D8; width: 100%; font-weight: 600; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0, 180, 216, 0.4); border-color: #00B4D8; background-color: #00B4D8; color: white; }
    .product-card { background-color: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 20px; transition: all 0.3s; text-align: center; display: flex; flex-direction: column; justify-content: space-between; height: 100%; }
    .product-card:hover { border-color: #00B4D8; box-shadow: 0 8px 20px rgba(0,0,0,0.4); transform: translateY(-5px); }
    .price-tag { color: #34d399; font-size: 22px; font-weight: 800; margin: 10px 0; }
    .price-sub { color: #cbd5e1; font-size: 13px; font-weight: 400; }
    .firm-name { color: #94a3b8; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.get("prihlasen"):
    st.warning("Pro vstup na Tržiště se musíte přihlásit na hlavní obrazovce.")
    st.stop()

st.title("Globální Tržiště produktů")

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}
except Exception:
    st.error("Chybí konfigurace databáze v Secrets!")
    st.stop()

uzivatel = st.session_state.get("uzivatel")
res_u = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{uzivatel}", headers=headers).json()
u_data = res_u[0] if res_u else {}
aktualni_kredity = u_data.get('kredity', 0)
skolni_kod = u_data.get('skolni_kod', 'SYSTEM')
st.session_state.kredity = aktualni_kredity

res_nastaveni = requests.get(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{skolni_kod}", headers=headers).json()
kurz_kc = float(res_nastaveni[0].get('kurz_kc', 10.0)) if res_nastaveni else 10.0

st.markdown(f"### Zůstatek k nákupu: <span style='color:#00B4D8;'>{aktualni_kredity:.2f} M-K</span> *(cca {aktualni_kredity * kurz_kc:,.0f} Kč)*", unsafe_allow_html=True)
st.write("---")

res_firmy = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?select=id,nazev_firmy,ceo_jmeno", headers=headers).json()
firmy_dict = {f['id']: f['nazev_firmy'] for f in res_firmy} if res_firmy else {}
firmy_ceo_dict = {f['id']: f['ceo_jmeno'] for f in res_firmy} if res_firmy else {}

res_produkty = requests.get(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy?schvaleno_uradem=eq.true", headers=headers).json()
produkty = res_produkty if res_produkty else []

if not produkty:
    st.info("Zatím zde nejsou žádné schválené produkty k prodeji.")
else:
    cols = st.columns(3)
    for index, p in enumerate(produkty):
        fid = p['firma_id']
        nazev_firmy = firmy_dict.get(fid, "Neznámá firma")
        ceo_firmy = firmy_ceo_dict.get(fid, "Neznamy")
        cena = float(p['konecna_cena'])
        dan_pct = float(p.get('mtech_dan_procento', 15.0))
        zaklad_dane = cena / (1 + (dan_pct / 100.0))
        castka_dan = cena - zaklad_dane
        cena_kc = cena * kurz_kc

        with cols[index % 3]:
            st.markdown(f"""
                <div class="product-card">
                    <div>
                        <div class="firm-name">{nazev_firmy}</div>
                        <h3 style="margin:0 0 10px 0; font-size: 18px;">{p['nazev_produktu']}</h3>
                        <p style="font-size: 13px; color: #cbd5e1;">{p.get('popis', 'Bez popisu')}</p>
                    </div>
                    <div>
                        <div class="price-tag">{cena:.2f} M-K</div>
                        <div class="price-sub">({cena_kc:,.0f} Kč)</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Koupit produkt", key=f"buy_{p['id']}", use_container_width=True):
                if aktualni_kredity >= cena:
                    requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{uzivatel}", headers=headers, json={"kredity": aktualni_kredity - cena})
                    res_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{ceo_firmy}", headers=headers).json()
                    if res_ceo: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{ceo_firmy}", headers=headers, json={"kredity": res_ceo[0]['kredity'] + zaklad_dane})
                    res_stat = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers).json()
                    if res_stat: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers, json={"kredity": res_stat[0]['kredity'] + castka_dan})
                    requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": fid, "typ_transakce": "PRIJEM", "titul": f"Prodej: {p['nazev_produktu']}", "castka": zaklad_dane, "auditovano": False})
                    requests.post(f"{SUPABASE_URL}/rest/v1/objednavky", headers=headers, json={"kupujici": uzivatel, "prodavajici_firma_id": fid, "produkt": p['nazev_produktu'], "cena": cena})
                    st.success("Nákup úspěšný!")
                    st.rerun()
                else:
                    st.error("Nedostatek kreditů!")

st.write("---")
st.subheader("Historie moji nákupů")
res_moje_objednavky = requests.get(f"{SUPABASE_URL}/rest/v1/objednavky?kupujici=eq.{uzivatel}&order=datum.desc", headers=headers).json()
if res_moje_objednavky:
    df = pd.DataFrame(res_moje_objednavky)
    df['Firma'] = df['prodavajici_firma_id'].map(lambda x: firmy_dict.get(x, "Neznámá firma"))
    st.dataframe(df[['datum', 'Firma', 'produkt', 'cena']], use_container_width=True)
