import streamlit as st
import requests

st.set_page_config(page_title="Tržiště a Banka", page_icon=":material/shopping_cart:", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3, h4 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #00B4D8; width: 100%; font-weight: 600; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0, 180, 216, 0.4); border-color: #00B4D8; background-color: #00B4D8; color: white; }
    .product-card { background-color: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 20px; transition: all 0.3s; text-align: center; display: flex; flex-direction: column; justify-content: space-between; height: 100%; }
    .product-card:hover { border-color: #00B4D8; box-shadow: 0 8px 20px rgba(0,0,0,0.4); transform: translateY(-5px); }
    .product-img { width: 100%; height: 180px; object-fit: cover; border-radius: 8px; margin-bottom: 15px; background-color: #0f172a; }
    .product-desc { font-size: 13px; color: #cbd5e1; height: 60px; overflow: hidden; text-overflow: ellipsis; margin-bottom: 15px; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; }
    .price-tag { color: #34d399; font-size: 24px; font-weight: 800; margin: 15px 0; }
    .firm-name { color: #94a3b8; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.get("prihlasen"):
    st.warning("Pro vstup na Tržiště se musíte přihlásit na hlavní obrazovce.")
    st.stop()

st.title("Globální Tržiště M-TECH CORE")

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}
except Exception:
    st.error("Chybí konfigurace databáze v Secrets!")
    st.stop()

uzivatel = st.session_state.get("uzivatel")
res_u = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{uzivatel}", headers=headers)
aktualni_kredity = res_u.json()[0]['kredity'] if res_u.status_code == 200 and res_u.json() else st.session_state.get("kredity", 0)
st.session_state.kredity = aktualni_kredity

st.markdown(f"### Vaše peněženka: <span style='color:#00B4D8;'>{aktualni_kredity:.2f} M-Kreditů</span>", unsafe_allow_html=True)
st.write("---")

res_firmy = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?select=id,nazev_firmy,ceo_jmeno", headers=headers)
firmy_dict = {f['id']: f['nazev_firmy'] for f in res_firmy.json()} if res_firmy.status_code == 200 else {}
firmy_ceo_dict = {f['id']: f['ceo_jmeno'] for f in res_firmy.json()} if res_firmy.status_code == 200 else {}

res_produkty = requests.get(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy?schvaleno_uradem=eq.true", headers=headers)
produkty = res_produkty.json() if res_produkty.status_code == 200 else []

if not produkty:
    st.info("Zatím zde nejsou žádné produkty. Firmy musí nejprve nechat schválit své kalkulace na Kontrolním úřadě.")
else:
    cols = st.columns(3)
    for index, p in enumerate(produkty):
        fid = p['firma_id']
        nazev_firmy = firmy_dict.get(fid, "Neznámá firma")
        ceo_firmy = firmy_ceo_dict.get(fid, "Neznamy")
        cena = float(p['konecna_cena'])
        dan_pct = float(p.get('mtech_dan_procento', 15.0))
        
        # Matematika daně
        zaklad_dane = cena / (1 + (dan_pct / 100.0))
        castka_dan = cena - zaklad_dane
        
        obrazek = p.get('obrazek_url') or "https://via.placeholder.com/300x200/0f172a/00B4D8?text=Bez+fotografie"
        popis = p.get('popis') or "Prodejce zatím nedodal popis produktu."
        
        with cols[index % 3]:
            st.markdown(f"""
                <div class="product-card">
                    <div>
                        <img src="{obrazek}" class="product-img" onerror="this.src='https://via.placeholder.com/300x200/0f172a/ef4444?text=Chyba+obrázku'">
                        <div class="firm-name">{nazev_firmy}</div>
                        <h3 style="margin:0 0 10px 0; font-size: 18px;">{p['nazev_produktu']}</h3>
                        <p class="product-desc">{popis}</p>
                    </div>
                    <div>
                        <div class="price-tag">{cena:.2f} M-K</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("Koupit produkt", key=f"buy_{p['id']}", icon=":material/shopping_cart_checkout:", use_container_width=True):
                if aktualni_kredity >= cena:
                    # 1. Strhnout kupujícímu celou cenu
                    requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{uzivatel}", headers=headers, json={"kredity": aktualni_kredity - cena})
                    
                    # 2. Přičíst zisk firmě (CEO)
                    res_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{ceo_firmy}", headers=headers).json()
                    if res_ceo:
                        requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{ceo_firmy}", headers=headers, json={"kredity": res_ceo[0]['kredity'] + zaklad_dane})
                    
                    # 3. Přičíst daň státu
                    res_stat = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers).json()
                    if res_stat:
                        requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers, json={"kredity": res_stat[0]['kredity'] + castka_dan})
                    
                    # 4. Účetnictví firmy (Zapsat jen základ jako čistý příjem)
                    requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={
                        "firma_id": fid, "typ_transakce": "PRIJEM", "titul": f"E-shop (Po zdanění): {p['nazev_produktu']}",
                        "castka": zaklad_dane, "auditovano": False
                    })
                    
                    # 5. Zápis objednávky
                    requests.post(f"{SUPABASE_URL}/rest/v1/objednavky", headers=headers, json={
                        "kupujici": uzivatel, "prodavajici_firma_id": fid, "produkt": p['nazev_produktu'], "cena": cena
                    })
                    
                    st.success(f"Zakoupeno za {cena:.2f} M-K! (Z toho odvedena M-TECH daň {castka_dan:.2f} M-K státu).")
                    st.rerun()
                else:
                    st.error(f"Nedostatek prostředků! Chybí vám {cena - aktualni_kredity:.2f} M-Kreditů.")

st.write("---")
st.subheader("Moje historie nákupů")
res_moje_objednavky = requests.get(f"{SUPABASE_URL}/rest/v1/objednavky?kupujici=eq.{uzivatel}&order=datum.desc", headers=headers)
if res_moje_objednavky.status_code == 200 and res_moje_objednavky.json():
    import pandas as pd
    df = pd.DataFrame(res_moje_objednavky.json())
    df['Firma'] = df['prodavajici_firma_id'].map(lambda x: firmy_dict.get(x, "Neznámá firma"))
    st.dataframe(df[['datum', 'Firma', 'produkt', 'cena']], use_container_width=True)
