import streamlit as st
import requests

st.set_page_config(page_title="Firemní Dashboard", page_icon=":material/insights:", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #00B4D8; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0, 180, 216, 0.4); border-color: #00B4D8; }
    </style>
""", unsafe_allow_html=True)

st.title(":material/insights: Firemní Dashboard")

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

moje_jmeno = "firma"

# Metrika kapitálu
st.metric("Firemní kapitál", f"{st.session_state.get('kredity', 0)} M-Kreditů")
st.write("---")

col_zakazky, col_prijmy = st.columns(2)

# --- SPRÁVA ZAKÁZEK / NABÍDEK ---
with col_zakazky:
    st.subheader(":: Nabídka zakázek a služeb")
    
    with st.form("nova_zakazka_form"):
        nazev = st.text_input("Název zakázky / produktu:")
        popis = st.text_area("Popis:")
        cena = st.number_input("Cena v M-Kreditech:", min_value=1, value=50)
        submit = st.form_submit_button("Přidat zakázku do nabídky")
        
        if submit:
            if nazev:
                payload = {
                    "firma": moje_jmeno,
                    "nazev": nazev,
                    "popis": popis,
                    "cena": cena
                }
                res = requests.post(f"{SUPABASE_URL}/rest/v1/zakazky", headers=headers, json=payload)
                if res.status_code in [200, 201]:
                    st.success("Zakázka byla úspěšně přidána!")
                    st.rerun()
                else:
                    st.error("Chyba při ukládání zakázky.")
            else:
                st.warning("Vyplňte název zakázky.")
                
    st.write("---")
    st.caption("Aktivní nabídka vaší firmy:")
    res_z = requests.get(f"{SUPABASE_URL}/rest/v1/zakazky?firma=eq.{moje_jmeno}", headers=headers)
    if res_z.status_code == 200 and len(res_z.json()) > 0:
        for z in res_z.json():
            st.markdown(f"🔹 **{z['nazev']}** – `{z['cena']} M-Kreditů`<br><small>{z['popis']}</small>", unsafe_allow_html=True)
    else:
        st.info("Zatím nemáte vystavené žádné zakázky.")

# --- HISTORIE PŘÍCHOZÍCH PLATEB ---
with col_prijmy:
    st.subheader(":: Přijaté platby")
    res_trans = requests.get(f"{SUPABASE_URL}/rest/v1/transakce?prijemce=eq.{moje_jmeno}&order=datum.desc", headers=headers)
    
    if res_trans.status_code == 200 and len(res_trans.json()) > 0:
        for t in res_trans.json():
            st.markdown(f"""
                <div style="padding: 10px; border-radius: 8px; background-color: #1e293b; margin-bottom: 8px; border-left: 4px solid #22c55e;">
                    <strong>+{t['castka']} M-Kreditů</strong> od <i>{t['odesilatel']}</i><br>
                    <small style="color: #94a3b8;">{t['popis']} | {t['datum'][:10]}</small>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Zatím nemáte žádné přijaté platby.")
