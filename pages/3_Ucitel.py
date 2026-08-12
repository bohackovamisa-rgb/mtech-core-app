import streamlit as st
import requests

st.set_page_config(page_title="Kontrolní úřad", page_icon=":material/account_balance:", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #00B4D8; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0, 180, 216, 0.4); border-color: #00B4D8; }
    </style>
""", unsafe_allow_html=True)

st.title(":material/account_balance: Kontrolní úřad (Učitel)")
st.info("Zde máte kompletní přehled nad všemi účty v systému a můžete spravovat jejich kredity.")

# --- NAČTENÍ KLÍČŮ ZE SECRETS ---
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

# --- FUNKCE PRO NAČTENÍ VŠECH UŽIVATELŮ ---
def nacti_uzivatele():
    endpoint = f"{SUPABASE_URL}/rest/v1/uzivatele?select=id,jmeno,role,kredity"
    res = requests.get(endpoint, headers=headers)
    if res.status_code == 200:
        return res.json()
    return []

uzivatele = nacti_uzivatele()

# --- ZOBRAZENÍ TABULKY UŽIVATELŮ ---
st.subheader("Přehled uživatelů a zůstatků")
if uzivatele:
    st.dataframe(uzivatele, use_container_width=True)
else:
    st.warning("Nenašel jsem žádné uživatele v databázi.")

st.write("---")

# --- FORMULÁŘ PRO ÚPRAVU KREDITŮ ---
st.subheader("Připsat / Strhnout M-Kredity")

if uzivatele:
    jmena_uzivatelu = [u["jmeno"] for u in uzivatele]
    vybrany_uzivatel = st.selectbox("Vyberte uživatele:", jmena_uzivatelu)
    
    # Najdeme aktuální kredity vybraného uživatele
    aktualni_data = next((u for u in uzivatele if u["jmeno"] == vybrany_uzivatel), None)
    aktualni_kredity = aktualni_data["kredity"] if aktualni_data else 0
    
    st.write(f"Aktuální zůstatek uživatele **{vybrany_uzivatel}**: `{aktualni_kredity} M-Kreditů`")
    
    zmena = st.number_input("Počet M-Kreditů k připsání/stržení (např. +50 nebo -20):", value=10, step=5)
    
    if st.button("Provést změnu kreditů"):
        nove_kredity = aktualni_kredity + zmena
        
        # Odeslání změny do databáze (PATCH REST API)
        patch_endpoint = f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{vybrany_uzivatel}"
        payload = {"kredity": nove_kredity}
        
        patch_res = requests.patch(patch_endpoint, headers=headers, json=payload)
        
        if patch_res.status_code in [200, 204]:
            st.success(f"Úspěšně upraveno! Uživatel **{vybrany_uzivatel}** má nyní **{nove_kredity} M-Kreditů**.")
            st.rerun()
        else:
            st.error(f"Chyba při ukládání do databáze: {patch_res.text}")
