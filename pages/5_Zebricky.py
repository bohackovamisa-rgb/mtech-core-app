import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Síň slávy & Statistiky", page_icon=":material/emoji_events:", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3 { background: -webkit-linear-gradient(45deg, #f59e0b, #d97706); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .card-box { background-color: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.get("prihlasen"):
    st.warning("Pro zobrazení žebříčků se musíte přihlásit na hlavní obrazovce.")
    st.stop()

st.title("🏆 Síň slávy a Statistiky")
st.caption("Žebříčky nejúspěšnějších žáků a startupů v ekosystému M-TECH CORE.")

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}
except Exception:
    st.error("Chybí konfigurace databáze v Secrets!")
    st.stop()
    
tab_zaci, tab_ekonomika = st.tabs(["Nejbohatší uživatelé", "Ziskovost Startupů"])

with tab_zaci:
    res_u = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?order=kredity.desc", headers=headers)
    if res_u.status_code == 200:
        uzivatele = res_u.json()
        # Odfiltrujeme systémové účty (Stát a Admin), aby soutěžili jen žáci a firmy
        bezni_uzivatele = [u for u in uzivatele if str(u.get('role', '')).upper() in ['ZAK', 'FIRMA']]
        
        if bezni_uzivatele:
            df = pd.DataFrame(bezni_uzivatele)[['jmeno', 'role', 'kredity']]
            df.columns = ['Uživatel', 'Role', 'Zůstatek (M-K)']
            df.index = df.index + 1
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown("#### Top 10 uživatelů")
                st.dataframe(df.head(10), use_container_width=True)
            with col2:
                st.markdown("#### Rozložení bohatství (Graf)")
                st.bar_chart(df.set_index('Uživatel')['Zůstatek (M-K)'])
        else:
            st.info("Zatím nejsou v systému žádní žáci.")

with tab_ekonomika:
    res_firmy = requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?select=*", headers=headers)
    if res_firmy.status_code == 200 and res_firmy.json():
        transakce = res_firmy.json()
        df_t = pd.DataFrame(transakce)
        
        # Filtrujeme pouze příjmy (tržby firem)
        prijmy = df_t[df_t['typ_transakce'] == 'PRIJEM']
        if not prijmy.empty:
            # Spárování s reálnými jmény firem
            res_f = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?select=id,nazev_firmy", headers=headers)
            firmy_dict = {f['id']: f['nazev_firmy'] for f in res_f.json()} if res_f.status_code == 200 else {}
            
            prijmy['Firma'] = prijmy['firma_id'].map(lambda x: firmy_dict.get(x, 'Neznámá'))
            sumy = prijmy.groupby('Firma')['castka'].sum().reset_index()
            sumy = sumy.sort_values(by='castka', ascending=False)
            
            col_e1, col_e2 = st.columns([1, 2])
            with col_e1:
                st.markdown("#### Nejziskovější startupy")
                st.dataframe(sumy.rename(columns={'castka': 'Celkové příjmy (M-K)'}).set_index('Firma'), use_container_width=True)
            with col_e2:
                st.markdown("#### Tržby firem (Graf)")
                st.bar_chart(sumy.set_index('Firma')['castka'])
        else:
            st.info("Firmy zatím nemají evidované žádné příjmy.")
    else:
        st.info("Zatím neproběhly žádné firemní transakce.")
