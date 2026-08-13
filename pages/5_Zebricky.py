import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Síň slávy a Statistiky", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .card-box { background-color: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.get("prihlasen"):
    st.warning("Pro zobrazení žebříčků se musíte přihlásit na hlavní obrazovce.")
    st.stop()

st.title("Síň slávy a Statistiky")

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}
except Exception:
    st.error("Chybí konfigurace databáze!")
    st.stop()

tab_zaci, tab_xp, tab_ekonomika = st.tabs(["Nejbohatší uživatelé", "Top Šikovní Žáci (XP)", "Ziskovost Startupů"])

with tab_zaci:
    res_u = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?order=kredity.desc", headers=headers).json()
    if res_u:
        bezni_uzivatele = [u for u in res_u if str(u.get('role', '')).upper() in ['ZAK', 'FIRMA']]
        if bezni_uzivatele:
            df = pd.DataFrame(bezni_uzivatele)[['jmeno', 'role', 'kredity']]
            df.columns = ['Uživatel', 'Role', 'Zůstatek (M-K)']
            df.index = df.index + 1
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown("#### Top 10 finančníků")
                st.dataframe(df.head(10), use_container_width=True)
            with col2:
                st.markdown("#### Porovnání majetku")
                st.bar_chart(df.set_index('Uživatel')['Zůstatek (M-K)'])

with tab_xp:
    res_xp = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?role=eq.zak&order=xp_it.desc", headers=headers).json()
    if res_xp:
        for z in res_xp:
            z['celkem_xp'] = z.get('xp_it', 0) + z.get('xp_marketing', 0) + z.get('xp_byznys', 0)
        
        df_xp = pd.DataFrame(res_xp).sort_values(by='celkem_xp', ascending=False)
        df_xp_show = df_xp[['jmeno', 'xp_it', 'xp_marketing', 'xp_byznys', 'celkem_xp']]
        df_xp_show.columns = ['Žák', 'IT XP', 'Marketing XP', 'Byznys XP', 'Celkem XP']
        df_xp_show.index = range(1, len(df_xp_show) + 1)
        
        col_x1, col_x2 = st.columns([1.5, 1])
        with col_x1:
            st.markdown("#### Žebříček dovedností (Skill Leaderboard)")
            st.dataframe(df_xp_show, use_container_width=True)
        with col_x2:
            st.markdown("#### Celkové skóre XP")
            st.bar_chart(df_xp_show.set_index('Žák')['Celkem XP'])

with tab_ekonomika:
    res_firmy = requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?select=*", headers=headers).json()
    if res_firmy:
        df_t = pd.DataFrame(res_firmy)
        prijmy = df_t[df_t['typ_transakce'] == 'PRIJEM']
        
        if not prijmy.empty:
            res_f = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?select=id,nazev_firmy", headers=headers).json()
            firmy_dict = {f['id']: f['nazev_firmy'] for f in res_f} if res_f else {}
            
            prijmy['Firma'] = prijmy['firma_id'].map(lambda x: firmy_dict.get(x, 'Neznámá'))
            sumy = prijmy.groupby('Firma')['castka'].sum().reset_index().sort_values(by='castka', ascending=False)
            
            col_e1, col_e2 = st.columns([1, 2])
            with col_e1:
                st.markdown("#### Tržby firem")
                st.dataframe(sumy.rename(columns={'castka': 'Celkové příjmy (M-K)'}).set_index('Firma'), use_container_width=True)
            with col_e2:
                st.markdown("#### Graf tržeb")
                st.bar_chart(sumy.set_index('Firma')['castka'])
        else:
            st.info("Firmy zatím nemají evidované žádné příjmy.")
    else:
        st.info("Zatím neproběhly žádné firemní transakce.")
