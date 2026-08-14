import streamlit as st
import requests
import pandas as pd
import json

st.set_page_config(page_title="Kontrolní úřad a Audit", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
    h1, h2, h3, h4 { background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800 !important; }
    .stButton>button { border-radius: 8px; transition: all 0.3s ease; border: 1px solid #00B4D8; width: 100%; font-weight: 600; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0, 180, 216, 0.4); border-color: #00B4D8; background-color: #0f172a; color: white;}
    .card-box { background-color: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 15px; }
    .status-ok { color: #34d399; font-weight: 700; background: rgba(16, 185, 129, 0.1); padding: 4px 8px; border-radius: 6px; }
    .status-wait { color: #fbbf24; font-weight: 700; background: rgba(245, 158, 11, 0.1); padding: 4px 8px; border-radius: 6px; }
    .status-err { color: #f87171; font-weight: 700; background: rgba(239, 68, 68, 0.1); padding: 4px 8px; border-radius: 6px; }
    .alert-box { background-color: rgba(245, 158, 11, 0.1); border: 1px solid #f59e0b; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    .info-box { background-color: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    .asset-link { color: #00B4D8; font-weight: bold; text-decoration: none; }
    .asset-link:hover { text-decoration: underline; color: #0077B6; }
    .licence-box { background: linear-gradient(135deg, rgba(0, 180, 216, 0.15) 0%, rgba(0, 119, 182, 0.15) 100%); border: 1px solid #00B4D8; border-left: 5px solid #00B4D8; padding: 15px 20px; border-radius: 8px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
    .licence-code { font-family: monospace; font-size: 1.4em; font-weight: bold; color: #0ea5e9; background: rgba(0,0,0,0.3); padding: 5px 15px; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.get("prihlasen") or str(st.session_state.get("role")).upper() not in ["UCITEL", "ADMIN"]:
    st.error("Přístup odepřen. Sekce pouze pro vyučující.")
    st.stop()

st.title("Kontrolní úřad a Audit")

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"].rstrip("/")
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Prefer": "return=representation"}
except Exception:
    st.error("Chybí konfigurace databáze.")
    st.stop()

ucitel_jmeno = st.session_state.get("uzivatel", "")
skolni_kod = st.session_state.get("skolni_kod", "")
is_admin = str(st.session_state.get("role")).upper() == "ADMIN"

# Bezpečné načtení údajů o vyučujícím
if not skolni_kod and ucitel_jmeno:
    res_ucitel = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{ucitel_jmeno}", headers=headers).json()
    if isinstance(res_ucitel, list) and len(res_ucitel) > 0:
        skolni_kod = res_ucitel[0].get("skolni_kod", "")
        st.session_state.skolni_kod = skolni_kod

# =========================================================================
# 0. ZOBRAZENÍ LICENČNÍHO KÓDU HNED NAHOŘE
# =========================================================================
if skolni_kod and skolni_kod != "SYSTEM":
    res_nazev_skoly = requests.get(f"{SUPABASE_URL}/rest/v1/licencovane_skoly?licencni_kod=eq.{skolni_kod}", headers=headers).json()
    nazev_skoly_zobrazeni = res_nazev_skoly[0].get('nazev_skoly', 'Neznámá instituce') if (isinstance(res_nazev_skoly, list) and len(res_nazev_skoly) > 0) else 'Neznámá instituce'
    
    st.markdown(f"""
        <div class="licence-box">
            <div>
                <h4 style="margin: 0; color: #cbd5e1;">Vaše škola: {nazev_skoly_zobrazeni}</h4>
                <p style="margin: 0; font-size: 0.9em; color: #94a3b8;">Tento kód předejte žákům pro registraci do systému a vaší třídy.</p>
            </div>
            <div class="licence-code">{skolni_kod}</div>
        </div>
    """, unsafe_allow_html=True)
elif is_admin:
    st.markdown("""
        <div class="licence-box">
            <div>
                <h4 style="margin: 0; color: #cbd5e1;">Režim: Hlavní Administrátor</h4>
                <p style="margin: 0; font-size: 0.9em; color: #94a3b8;">Máte neomezený přístup napříč všemi školami.</p>
            </div>
            <div class="licence-code">SUPERADMIN</div>
        </div>
    """, unsafe_allow_html=True)

# =========================================================================
# 1. ŘÍDÍCÍ PANEL (ACTION CENTER) - NOTIFIKACE PRO UČITELE
# =========================================================================
if is_admin:
    res_moje_tridy_global = requests.get(f"{SUPABASE_URL}/rest/v1/tridy?select=nazev_tridy", headers=headers).json()
else:
    res_moje_tridy_global = requests.get(f"{SUPABASE_URL}/rest/v1/tridy?skolni_kod=eq.{skolni_kod}&ucitel_jmeno=eq.{ucitel_jmeno}&select=nazev_tridy", headers=headers).json()

moje_tridy_nazvy_global = [t["nazev_tridy"] for t in res_moje_tridy_global] if isinstance(res_moje_tridy_global, list) else []

vsechny_firmy_skoly = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?skolni_kod=eq.{skolni_kod}&select=*", headers=headers).json()
if is_admin:
    moje_firmy_global = vsechny_firmy_skoly if isinstance(vsechny_firmy_skoly, list) else []
else:
    moje_firmy_global = [f for f in (vsechny_firmy_skoly if isinstance(vsechny_firmy_skoly, list) else []) if f.get("trida_nazev") in moje_tridy_nazvy_global]

vsichni_zaci_skoly = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?skolni_kod=eq.{skolni_kod}&role=neq.ucitel&select=jmeno,trida_nazev,role", headers=headers).json()
if is_admin:
    moji_zaci_global = vsichni_zaci_skoly if isinstance(vsichni_zaci_skoly, list) else []
else:
    moji_zaci_global = [z for z in (vsichni_zaci_skoly if isinstance(vsichni_zaci_skoly, list) else []) if z.get("trida_nazev") in moje_tridy_nazvy_global]
moji_zaci_jmena_global = [z["jmeno"] for z in moji_zaci_global]

g_firmy_cekajici = [f for f in moje_firmy_global if f.get("stave_licence") == "CEKA_NA_SCHVALENI"]

res_q_all = requests.get(f"{SUPABASE_URL}/rest/v1/questy?stav=eq.K_KONTROLE", headers=headers).json()
g_questy_cekajici = [q for q in (res_q_all if isinstance(res_q_all, list) else []) if q.get("resitel") in moji_zaci_jmena_global]

res_priznani_all = requests.get(f"{SUPABASE_URL}/rest/v1/danova_priznani?stav=eq.ODEVZDANO", headers=headers).json()
g_priznani_cekajici = [p for p in (res_priznani_all if isinstance(res_priznani_all, list) else []) if any(f['id'] == p.get('firma_id') for f in moje_firmy_global)]

res_kalk_all = requests.get(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy?schvaleno_uradem=eq.false", headers=headers).json()
g_kalkulace_cekajici = [k for k in (res_kalk_all if isinstance(res_kalk_all, list) else []) if any(f['id'] == k.get('firma_id') for f in moje_firmy_global)]

res_uvery_all = requests.get(f"{SUPABASE_URL}/rest/v1/bankovni_uvery?stav=eq.ZADOST", headers=headers).json()
g_uvery_cekajici = [u for u in (res_uvery_all if isinstance(res_uvery_all, list) else []) if any(f['id'] == u.get('firma_id') for f in moje_firmy_global)]

g_pocet_celkem_restu = len(g_firmy_cekajici) + len(g_questy_cekajici) + len(g_priznani_cekajici) + len(g_kalkulace_cekajici) + len(g_uvery_cekajici)

pocet_zaku_celkem = len(moji_zaci_global)
pocet_zaku_zakladni_role = len([z for z in moji_zaci_global if z.get("role") == "zak"])

col_dash1, col_dash2 = st.columns(2)

with col_dash1:
    st.markdown(f"""
    <div class='info-box'>
        <h4 style='margin:0; color:#10b981;'>Stav registrací žáků</h4>
        <p style='margin: 5px 0 0 0; color:#cbd5e1; font-size: 15px;'>
            Ve vašich třídách je aktuálně registrováno celkem <b>{pocet_zaku_celkem} žáků</b>.<br>
            Z toho <b>{pocet_zaku_zakladni_role} žáků</b> má zatím jen základní roli. Zkontrolujte je ve Správě žáků a přidělte jim podnikatelská oprávnění.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_dash2:
    if g_pocet_celkem_restu > 0:
        st.markdown(f"""
        <div class='alert-box'>
            <h4 style='margin:0; color:#f59e0b;'>Nevyřízené úkoly a audity ({g_pocet_celkem_restu})</h4>
            <ul style='margin-bottom:0; color:#cbd5e1; font-size: 14px; margin-top: 5px;'>
                {"<li><b>Žádosti o registraci firmy:</b> " + str(len(g_firmy_cekajici)) + " (Záložka 1. Spis)</li>" if g_firmy_cekajici else ""}
                {"<li><b>Odevzdané úkoly ke kontrole:</b> " + str(len(g_questy_cekajici)) + " (Záložka 5. Úřad práce)</li>" if g_questy_cekajici else ""}
                {"<li><b>Kalkulace produktů pro E-shop:</b> " + str(len(g_kalkulace_cekajici)) + " (Záložka 4. E-shop)</li>" if g_kalkulace_cekajici else ""}
                {"<li><b>Odevzdaná daňová přiznání:</b> " + str(len(g_priznani_cekajici)) + " (Záložka 6. Státní pokladna)</li>" if g_priznani_cekajici else ""}
                {"<li><b>Žádosti firem o bankovní úvěr:</b> " + str(len(g_uvery_cekajici)) + " (Záložka 7. Banka)</li>" if g_uvery_cekajici else ""}
            </ul>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class='info-box' style='background-color: rgba(52, 211, 153, 0.05); border-color: #34d399;'>
            <h4 style='margin:0; color:#34d399;'>Čistý stůl</h4>
            <p style='margin: 5px 0 0 0; color:#cbd5e1; font-size: 14px;'>Žádné firmy ani úkoly nečekají na váš audit a schválení.</p>
        </div>
        """, unsafe_allow_html=True)

st.write("---")

# =========================================================================
# SPRÁVA A VÝBĚR TŘÍDY VYUČUJÍCÍHO
# =========================================================================
if is_admin:
    res_tridy = requests.get(f"{SUPABASE_URL}/rest/v1/tridy?select=*&order=id.desc", headers=headers).json()
else:
    res_tridy = requests.get(f"{SUPABASE_URL}/rest/v1/tridy?skolni_kod=eq.{skolni_kod}&ucitel_jmeno=eq.{ucitel_jmeno}&select=*&order=id.desc", headers=headers).json()

moje_tridy = res_tridy if (isinstance(res_tridy, list) and res_tridy) else []

with st.expander("Založení a správa mých tříd / skupin"):
    col_t1, col_t2 = st.columns([2, 1])
    with col_t1:
        nova_trida_nazev = st.text_input("Název nové třídy (např. 3.A nebo Seminář Pondělí):")
    with col_t2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("Založit novou třídu"):
            if nova_trida_nazev.strip():
                requests.post(f"{SUPABASE_URL}/rest/v1/tridy", headers=headers, json={
                    "skolni_kod": skolni_kod,
                    "nazev_tridy": nova_trida_nazev.strip(),
                    "ucitel_jmeno": ucitel_jmeno
                })
                st.success(f"Třída {nova_trida_nazev} byla vytvořena.")
                st.rerun()

if not moje_tridy:
    st.info("Zatím jste si nezaložili žádnou třídu. Vytvořte prosím svou první třídu výše, aby se do ní mohli žáci registrovat.")
    st.stop()

seznam_trid_nazvy = [t["nazev_tridy"] for t in moje_tridy]
aktivni_trida = st.selectbox("Vyberte třídu, se kterou právě pracujete:", seznam_trid_nazvy)

st.write("---")

# =========================================================================
# NAČTENÍ ŽÁKŮ A FIREM VYBRANÉ TŘÍDY
# =========================================================================
res_zaci = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?skolni_kod=eq.{skolni_kod}&trida_nazev=eq.{aktivni_trida}&role=neq.ucitel&order=id.desc", headers=headers).json()
zaci_tridy = res_zaci if isinstance(res_zaci, list) else []

res_firmy = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?skolni_kod=eq.{skolni_kod}&trida_nazev=eq.{aktivni_trida}&select=*&order=id.desc", headers=headers).json()
firmy = res_firmy if isinstance(res_firmy, list) else []

# =========================================================================
# 2. SPRÁVA ŽÁKŮ VYBRANÉ TŘÍDY
# =========================================================================
with st.expander(f"Seznam žáků třídy {aktivni_trida} a udělování podnikatelských rolí", expanded=False):
    if not zaci_tridy:
        st.info(f"Ve třídě {aktivni_trida} zatím nejsou registrováni žádní žáci.")
    else:
        tabulka_zaku = []
        for z in zaci_tridy:
            role_text = "Podnikatel (Může založit firmu)" if z.get("role") == "firma" else "Běžný žák (Práce a nákup)"
            tabulka_zaku.append({
                "Uživatelské jméno": z.get("jmeno"),
                "Aktuální role": role_text,
                "Zůstatek (M-K)": z.get("kredity", 0)
            })
        st.dataframe(pd.DataFrame(tabulka_zaku), use_container_width=True)
        
        col_z1, col_z2, col_z3 = st.columns([2, 2, 1])
        with col_z1:
            vybrany_zak = st.selectbox("Vyberte žáka:", [z["jmeno"] for z in zaci_tridy])
        with col_z2:
            nova_role = st.selectbox("Nastavit oprávnění:", ["firma (Podnikatel / Zakladatel)", "zak (Běžný žák)"])
        with col_z3:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("Uložit roli"):
                role_kod = "firma" if "firma" in nova_role else "zak"
                requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{vybrany_zak}", headers=headers, json={"role": role_kod})
                st.success(f"Žákovi {vybrany_zak} byla nastavena role.")
                st.rerun()

st.write("---")

# =========================================================================
# 3. AUDIT FIREM VYBRANÉ TŘÍDY
# =========================================================================
if not firmy:
    st.info(f"Ve třídě {aktivni_trida} zatím žádný žák neodeslal žádost o registraci firmy.")
    st.stop()

firmy_labels = []
for f in firmy:
    status_tag = " [ČEKÁ NA SCHVÁLENÍ]" if f.get("stave_licence") == "CEKA_NA_SCHVALENI" else ""
    firmy_labels.append(f"{f['nazev_firmy']}{status_tag}")

vybrany_label = st.selectbox("Vyberte startup k auditu:", firmy_labels)
vybrana_firma_nazev = vybrany_label.replace(" [ČEKÁ NA SCHVÁLENÍ]", "")
firma = next(f for f in firmy if f["nazev_firmy"] == vybrana_firma_nazev)
f_id = firma["id"]

tab_legal, tab_aktiva, tab_hr, tab_finance, tab_questy, tab_stat, tab_banka, tab_hodnoceni = st.tabs([
    "1. Spis a Notář", "2. Vize a AI", "3. HR a Tým", "4. E-shop a Zákazníci", "5. Úřad práce a XP", "6. Státní pokladna a Daně", "7. Banka a Ceník", "8. Přehled a Hodnocení"
])

# ==========================================
# ZÁLOŽKA 1: SPIS A NOTÁŘ
# ==========================================
with tab_legal:
    st.subheader(f"Firemní spis: {firma['nazev_firmy']} (Třída: {aktivni_trida})")
    col_l1, col_l2 = st.columns([1.6, 1])
    
    with col_l1:
        res_zamestnanci = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?firma_id=eq.{f_id}", headers=headers).json()
        zamestnanci = res_zamestnanci if isinstance(res_zamestnanci, list) else []
        
        with st.container(border=True):
            st.markdown("#### Identifikace společnosti")
            st.markdown(f"**Obchodní firma:** `{firma['nazev_firmy']}`")
            st.markdown(f"**Třída:** `{aktivni_trida}` | **Licenční kód:** `{firma.get('skolni_kod', '')}`")
            st.markdown(f"**Základní kapitál:** `{firma.get('pocatecni_kapital', 100)} M-K`")
            
            st.divider()
            
            st.markdown("#### Předmět podnikání a Živnost")
            zamer_raw = str(firma.get('podnikatelsky_zamer', ''))
            if "|" in zamer_raw:
                polozky = [p.strip() for p in zamer_raw.split("|")]
                for p in polozky:
                    st.markdown(f"* {p}")
            else:
                st.write(zamer_raw if zamer_raw else "Neuvedeno")
            
            st.divider()
            
            st.markdown("#### Statutární orgány (Vedení)")
            st.markdown(f"* **CEO:** {firma.get('ceo_jmeno', 'Neobsazeno')}")
            st.markdown(f"* **CFO:** {firma.get('cfo_jmeno', 'Neobsazeno')}")
            st.markdown(f"* **CTO:** {firma.get('cto_jmeno', 'Neobsazeno')}")
            
            st.divider()
            
            st.markdown("#### Zaměstnanci a pracovníci")
            if zamestnanci:
                for z in zamestnanci:
                    st.markdown(f"* **{z['jmeno_zamestnance']}** — {z.get('pozice', 'Pracovník')} ({z.get('hodinova_sazba', 0)} M-K/hod)")
            else:
                st.info("Firma zatím nepřijala žádné další zaměstnance.")
                
        with st.expander("Jmenovat / Změnit vedení firmy (CEO, CFO, CTO)"):
            seznam_jmen_zaku = [z['jmeno'] for z in zaci_tridy]
            if not seznam_jmen_zaku:
                st.info("Ve třídě nejsou žádní žáci pro přiřazení do vedení.")
            else:
                with st.form("form_zmena_roli_vedeni"):
                    idx_ceo = seznam_jmen_zaku.index(firma['ceo_jmeno']) if firma.get('ceo_jmeno') in seznam_jmen_zaku else 0
                    idx_cfo = seznam_jmen_zaku.index(firma['cfo_jmeno'])+1 if firma.get('cfo_jmeno') in seznam_jmen_zaku else 0
                    idx_cto = seznam_jmen_zaku.index(firma['cto_jmeno'])+1 if firma.get('cto_jmeno') in seznam_jmen_zaku else 0

                    novy_ceo = st.selectbox("CEO (Generální ředitel):", seznam_jmen_zaku, index=idx_ceo)
                    novy_cfo = st.selectbox("CFO (Finanční ředitel):", ["-- Neobsazeno --"] + seznam_jmen_zaku, index=idx_cfo)
                    novy_cto = st.selectbox("CTO (Technický ředitel):", ["-- Neobsazeno --"] + seznam_jmen_zaku, index=idx_cto)
                    
                    if st.form_submit_button("Uložit změny statutárních orgánů"):
                        cfo_val = None if novy_cfo == "-- Neobsazeno --" else novy_cfo
                        cto_val = None if novy_cto == "-- Neobsazeno --" else novy_cto
                        requests.patch(
                            f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{f_id}",
                            headers=headers,
                            json={"ceo_jmeno": novy_ceo, "cfo_jmeno": cfo_val, "cto_jmeno": cto_val}
                        )
                        st.success("Vedení firmy bylo upraveno.")
                        st.rerun()
                        
    with col_l2:
        stav = firma.get('stave_licence', 'CEKA_NA_SCHVALENI')
        stav_tridy = 'status-ok' if stav == 'SCHVALENO' else ('status-err' if stav in ['ZAMITNUTO', 'UKONCENO'] else 'status-wait')
        
        with st.container(border=True):
            st.markdown("#### Stav zápisu do rejstříku")
            st.markdown(f"Aktuální stav: <span class='{stav_tridy}'>{stav}</span>", unsafe_allow_html=True)
            if firma.get('duvod_zamitnuti'):
                st.error(f"Důvod zamítnutí: {firma.get('duvod_zamitnuti')}")
        
        if st.button("Schválit zápis do rejstříku a povolit činnost", type="primary"):
            requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{f_id}", headers=headers, json={"stave_licence": "SCHVALENO", "duvod_zamitnuti": ""})
            st.success(f"Firma {firma['nazev_firmy']} byla zapsána do rejstříku.")
            st.rerun()
            
        with st.popover("Zamítnout / Vrátit k přepracování"):
            duvod = st.text_area("Pokyny pro žáky k opravě:")
            if st.button("Potvrdit zamítnutí"):
                requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{f_id}", headers=headers, json={"stave_licence": "ZAMITNUTO", "duvod_zamitnuti": duvod})
                st.warning("Spis byl vrácen žákům k přepracování.")
                st.rerun()

# ==========================================
# ZÁLOŽKA 2: VIZE
# ==========================================
with tab_aktiva:
    canvas = requests.get(f"{SUPABASE_URL}/rest/v1/lean_canvas?firma_id=eq.{f_id}", headers=headers).json()
    if canvas and isinstance(canvas, list):
        with st.expander("Detail Lean Canvasu (8 bloků)"):
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.write("**1. Problém:**", canvas[0].get('problem', ''))
                st.write("**3. Cílová skupina:**", canvas[0].get('cilova_skupina', ''))
                st.write("**5. Kanály:**", canvas[0].get('kanaly', ''))
                st.write("**7. Náklady:**", canvas[0].get('naklady', ''))
            with col_c2:
                st.write("**2. Řešení:**", canvas[0].get('reseni', ''))
                st.write("**4. Unikátní hodnota:**", canvas[0].get('hodnota', ''))
                st.write("**6. Nefér výhoda:**", canvas[0].get('vyhoda', ''))
                st.write("**8. Příjmy:**", canvas[0].get('prijmy', ''))
    else:
        st.info("Firma zatím nedodala Lean Canvas.")

# ==========================================
# ZÁLOŽKA 3: HR
# ==========================================
with tab_hr:
    st.markdown("#### Personální audit týmu")
    zamestnanci_full = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?firma_id=eq.{f_id}", headers=headers).json()
    if zamestnanci_full and isinstance(zamestnanci_full, list):
        df_zam_full = pd.DataFrame(zamestnanci_full)[['jmeno_zamestnance', 'pozice', 'hodinova_sazba', 'vyplaceno_celkem']]
        df_zam_full.columns = ['Jméno', 'Pozice', 'Sazba (M-K/hod)', 'Vyplaceno (M-K)']
        st.dataframe(df_zam_full, use_container_width=True)
    else: 
        st.info("Firma zatím neeviduje žádné zaměstnance.")

# ==========================================
# ZÁLOŽKA 4: E-SHOP A ZÁKAZNÍCI
# ==========================================
with tab_finance:
    st.markdown("#### Schvalování produktů pro Tržiště")
    kalkulace = requests.get(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy?firma_id=eq.{f_id}", headers=headers).json()
    if kalkulace and isinstance(kalkulace, list):
        for k in kalkulace:
            barva = "status-ok" if k['schvaleno_uradem'] else "status-wait"
            with st.container(border=True):
                st.markdown(f"**{k['nazev_produktu']}** — <span class='{barva}'>{'Aktivní' if k['schvaleno_uradem'] else 'Čeká na schválení'}</span>", unsafe_allow_html=True)
                st.write(f"Cena: {k['konecna_cena']} M-K")
                if not k['schvaleno_uradem']:
                    if st.button(f"Schválit produkt: {k['nazev_produktu']}", key=f"kalk_{k['id']}"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy?id=eq.{k['id']}", headers=headers, json={"schvaleno_uradem": True})
                        st.rerun()
    else:
        st.info("Žádné kalkulace ke schválení.")

# ==========================================
# ZÁLOŽKA 5: ÚŘAD PRÁCE A KONTROLA ÚKOLŮ
# ==========================================
with tab_questy:
    st.subheader(f"Úkoly žáků třídy {aktivni_trida}")
    
    col_q1, col_q2 = st.columns(2)
    with col_q1:
        with st.form("new_quest"):
            q_nazev = st.text_input("Vlastní název úkolu:")
            q_popis = st.text_area("Rozsah práce:")
            q_odmena = st.number_input("Odměna (M-K):", min_value=1.0, value=20.0)
            if st.form_submit_button("Vypsat úkol"):
                requests.post(f"{SUPABASE_URL}/rest/v1/questy", headers=headers, json={"nazev": q_nazev, "popis": q_popis, "odmena": q_odmena, "zadavatel": ucitel_jmeno, "stav": "VOLNY"})
                st.rerun()
                
    with col_q2:
        st.markdown("#### Odevzdaná práce ke kontrole")
        if questy_cekajici:
            for q in questy_cekajici:
                odkaz = q.get('odkaz_vystup', '')
                vystup_html = f"<a href='{odkaz}' target='_blank' style='color:#0ea5e9; font-weight:bold;'>Otevřít odkaz</a>" if str(odkaz).startswith("http") else f"<b>Komentář:</b> <i>{odkaz}</i>"
                with st.container(border=True):
                    st.markdown(f"**{q['nazev']}** (Zhotovitel: {q['resitel']}, Odměna: {q['odmena']} M-K)")
                    st.markdown(vystup_html, unsafe_allow_html=True)
                    if st.button("Schválit a vyplatit", key=f"btn_q_{q['id']}"):
                        requests.patch(f"{SUPABASE_URL}/rest/v1/questy?id=eq.{q['id']}", headers=headers, json={"stav": "DOKONCENO"})
                        res_r = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{q['resitel']}", headers=headers).json()
                        if res_r and isinstance(res_r, list) and len(res_r) > 0:
                            requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{q['resitel']}", headers=headers, json={"kredity": res_r[0]['kredity'] + q['odmena']})
                        st.success("Úkol schválen a odměna vyplacena.")
                        st.rerun()
        else:
            st.info("Žádné úkoly momentálně nečekají na schválení.")

# ==========================================
# ZÁLOŽKA 6: STÁTNÍ POKLADNA A DAŇOVÝ AUDIT
# ==========================================
with tab_stat:
    res_stat = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers).json()
    stat_kredity = res_stat[0]['kredity'] if (isinstance(res_stat, list) and len(res_stat) > 0) else 0
    with st.container(border=True):
        st.markdown(f"### Rozpočet vybraných daní: `{stat_kredity:.2f} M-K`")
        
    st.write("---")
    st.markdown("#### Audit odevzdaných daňových přiznání")
    if priznani_cekajici:
        for p in priznani_cekajici:
            f_info = next((f for f in firmy if f['id'] == p['firma_id']), None)
            if not f_info: continue
            f_nazev = f_info['nazev_firmy']

            kniha = requests.get(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju?firma_id=eq.{p['firma_id']}&typ_transakce=eq.PRIJEM", headers=headers).json()
            celkem_prijmy = sum(item['castka'] for item in kniha) if (isinstance(kniha, list) and kniha) else 0

            sk_kod_p = f_info.get('skolni_kod', 'SYSTEM')
            nast_res = requests.get(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{sk_kod_p}", headers=headers).json()
            sazba_dan = float(nast_res[0].get('mtech_dan_pct', 15.0)) if (isinstance(nast_res, list) and len(nast_res) > 0) else 15.0
            pozadovana_dan = celkem_prijmy * (sazba_dan / 100.0)

            with st.container(border=True):
                st.markdown(f"**Daňové přiznání: {f_nazev}**")
                st.write(f"Přiznaná daň firmou: {p['dane_priznane']:.2f} M-K | Evidované příjmy: {celkem_prijmy:.2f} M-K | Povinná daň ({sazba_dan} %): {pozadovana_dan:.2f} M-K")

                if st.button(f"Spustit kontrolu přiznání #{p['id']}", key=f"ai_audit_{p['id']}"):
                    vysledek_status = "SCHVALENO" if abs(pozadovana_dan - p['dane_priznane']) <= 1 else "ZAMITNUTO_PENALE"
                    rozdil = max(0, pozadovana_dan - p['dane_priznane'])
                    vymere_penale = rozdil + 50.0 if vysledek_status == "ZAMITNUTO_PENALE" else 0.0

                    if vysledek_status == "SCHVALENO":
                        requests.patch(f"{SUPABASE_URL}/rest/v1/danova_priznani?id=eq.{p['id']}", headers=headers, json={"stav": "SCHVALENO"})
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": p['firma_id'], "typ_transakce": "PRIJEM", "titul": "INFO OD FÚ: Daňové přiznání schváleno", "castka": 0, "auditovano": True})
                        st.success("Daňové přiznání je v pořádku a bylo schváleno.")
                    else:
                        r_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{f_info['ceo_jmeno']}", headers=headers).json()
                        if r_ceo and isinstance(r_ceo, list) and len(r_ceo) > 0:
                            kredity = r_ceo[0]['kredity']
                            requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{f_info['ceo_jmeno']}", headers=headers, json={"kredity": max(0, kredity - vymere_penale)})
                        
                        requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers, json={"kredity": stat_kredity + vymere_penale})
                        requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": p['firma_id'], "typ_transakce": "VYDAJ", "titul": "PENÁLE OD FÚ: Krácení daně", "castka": vymere_penale, "auditovano": True})
                        requests.patch(f"{SUPABASE_URL}/rest/v1/danova_priznani?id=eq.{p['id']}", headers=headers, json={"stav": "ZAMITNUTO_PENALE"})
                        st.error(f"Zjištěno krácení daně. Strženo penále {vymere_penale} M-K.")
                    st.rerun()
    else:
        st.info("Žádné firmy momentálně nečekají na daňový audit.")

# ==========================================
# ZÁLOŽKA 7: BANKA A CENÍK
# ==========================================
with tab_banka:
    nastaveni_res = requests.get(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{skolni_kod}", headers=headers).json()
    akt_nastaveni = nastaveni_res[0] if (isinstance(nastaveni_res, list) and len(nastaveni_res) > 0) else {}
    
    col_cb1, col_cb2 = st.columns(2)
    
    with col_cb1:
        st.markdown("#### Tisk peněz na účet vyučujícího")
        st.caption("Jako guvernér banky si můžete emitovat libovolný počet M-Kreditů pro své nákupy od žáků.")
        with st.form("form_tisk_penez"):
            tisk_castka = st.number_input("Částka k připsání (M-K):", min_value=100, value=1000)
            if st.form_submit_button("Vytisknout a připsat kredity"):
                res_ucitel_akt = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{ucitel_jmeno}", headers=headers).json()
                aktualni_zustatek_ucitele = res_ucitel_akt[0].get("kredity", 0) if (isinstance(res_ucitel_akt, list) and len(res_ucitel_akt) > 0) else 0
                novy_zustatek = aktualni_zustatek_ucitele + tisk_castka
                requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{ucitel_jmeno}", headers=headers, json={"kredity": novy_zustatek})
                st.session_state.kredity = novy_zustatek
                st.success(f"Na váš účet bylo připsáno {tisk_castka} M-K.")
                st.rerun()

    with col_cb2:
        with st.form("form_makro"):
            st.markdown("#### Nastavení ekonomiky")
            st.caption(f"Pravidla pro školní kód: **{skolni_kod}**")
            n_kurz = st.number_input("Kurz M-Kreditu k CZK (1 M-K = X Kč):", min_value=1.0, value=float(akt_nastaveni.get('kurz_kc', 10.0)))
            n_dan = st.number_input("M-TECH Daň pro e-shop (%):", min_value=0.0, max_value=50.0, value=float(akt_nastaveni.get('mtech_dan_pct', 15.0)))
            n_dan_prijem = st.number_input("Daň z příjmu zaměstnanců (%):", min_value=0.0, max_value=50.0, value=float(akt_nastaveni.get('dan_prijem_pct', 15.0)))
            n_cenik = st.text_area("Globální ceník školy:", value=str(akt_nastaveni.get('globalni_cenik', '')), height=150)
            if st.form_submit_button("Uložit makroekonomická pravidla"):
                requests.patch(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{skolni_kod}", headers=headers, json={
                    "kurz_kc": n_kurz, "globalni_cenik": n_cenik, "mtech_dan_pct": n_dan, "dan_prijem_pct": n_dan_prijem
                })
                st.success("Pravidla uložena.")
                st.rerun()
        
        st.write("---")
        st.markdown("#### Žádosti o firemní úvěry")
        res_uvery_all = requests.get(f"{SUPABASE_URL}/rest/v1/bankovni_uvery?stav=eq.ZADOST", headers=headers).json()
        uvery = [u for u in (res_uvery_all if isinstance(res_uvery_all, list) else []) if any(f['id'] == u.get('firma_id') for f in moje_firmy_global)]
        
        if uvery:
            for u in uvery:
                f_jmeno = next((f['nazev_firmy'] for f in firmy if f['id'] == u['firma_id']), "Neznámá firma")
                with st.container(border=True):
                    st.markdown(f"**Žadatel:** {f_jmeno} | Částka: {u['castka']} M-K (Úrok: {u['urok_pct']} %)")
                    st.write(f"Účel: {u['ucel']}")
                    col_u_btn1, col_u_btn2 = st.columns(2)
                    with col_u_btn1:
                        if st.button("Schválit úvěr", key=f"uv_ok_{u['id']}"):
                            f_ceo = next((f['ceo_jmeno'] for f in firmy if f['id'] == u['firma_id']), None)
                            celkem_vratit = u['castka'] * (1 + (u['urok_pct'] / 100.0))
                            requests.patch(f"{SUPABASE_URL}/rest/v1/bankovni_uvery?id=eq.{u['id']}", headers=headers, json={"stav": "SCHVALENO", "zbyva_splatit": celkem_vratit})
                            res_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{f_ceo}", headers=headers).json()
                            if res_ceo:
                                requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{f_ceo}", headers=headers, json={"kredity": res_ceo[0]['kredity'] + u['castka']})
                            requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": u['firma_id'], "typ_transakce": "PRIJEM", "titul": f"Bankovní úvěr: {u['ucel']}", "castka": u['castka'], "auditovano": True})
                            st.rerun()
                    with col_u_btn2:
                        if st.button("Zamítnout", key=f"uv_ne_{u['id']}"):
                            requests.patch(f"{SUPABASE_URL}/rest/v1/bankovni_uvery?id=eq.{u['id']}", headers=headers, json={"stav": "ZAMITNUTO"})
                            st.rerun()
        else:
            st.info("Žádné čekající žádosti o podnikatelský úvěr.")

# ==========================================
# ZÁLOŽKA 8: HODNOCENÍ ŽÁKŮ TŘÍDY
# ==========================================
with tab_hodnoceni:
    st.subheader(f"Přehled žáků třídy {aktivni_trida}")
    if zaci_tridy:
        zaci_data = []
        for z in zaci_tridy:
            zaci_data.append({
                "Jméno": z['jmeno'],
                "Role": z.get('role', 'zak'),
                "Majetek (M-K)": round(z.get('kredity', 0), 2),
                "XP Body": z.get('xp_it', 0) + z.get('xp_marketing', 0) + z.get('xp_byznys', 0)
            })
        st.dataframe(pd.DataFrame(zaci_data), use_container_width=True)
    else:
        st.info("Žádní žáci ve třídě.")
