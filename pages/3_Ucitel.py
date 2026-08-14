import streamlit as st
import requests
import pandas as pd
import json
import time

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
.licence-box { background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.95) 100%); border: 1px solid #334155; padding: 20px; border-radius: 12px; margin-bottom: 25px; }
.licence-card { background: rgba(15, 23, 42, 0.6); padding: 15px; border-radius: 8px; border: 1px solid #334155; }
.licence-val { font-family: monospace; font-size: 1.5em; font-weight: bold; padding: 4px 10px; border-radius: 5px; display: inline-block; margin-top: 5px; }
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

if not skolni_kod and ucitel_jmeno:
    res_ucitel = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{ucitel_jmeno}", headers=headers).json()
    if isinstance(res_ucitel, list) and len(res_ucitel) > 0:
        skolni_kod = res_ucitel[0].get("skolni_kod", "")
        st.session_state.skolni_kod = skolni_kod

# =========================================================================
# 0. ZOBRAZENÍ OBOU LICENČNÍCH KÓDŮ ŠKOLY
# =========================================================================
if skolni_kod and skolni_kod != "SYSTEM":
    res_nazev_skoly = requests.get(f"{SUPABASE_URL}/rest/v1/licencovane_skoly?licencni_kod=eq.{skolni_kod}", headers=headers).json()
    nazev_skoly_zobrazeni = res_nazev_skoly[0].get('nazev_skoly', 'Neznámá instituce') if (isinstance(res_nazev_skoly, list) and len(res_nazev_skoly) > 0) else 'Neznámá instituce'
    
    akt_nast = requests.get(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{skolni_kod}", headers=headers).json()
    z_kod = akt_nast[0].get('zakaznicky_kod', 'NENASTAVENO') if (isinstance(akt_nast, list) and len(akt_nast) > 0) else 'NENASTAVENO'
    
    box_kody_html = f"""<div class="licence-box">
<h4 style="margin: 0 0 15px 0; color: #f8fafc; font-size: 1.15em;">Přístupové kódy školy: {nazev_skoly_zobrazeni}</h4>
<div style="display: flex; gap: 20px; flex-wrap: wrap;">
<div style="flex: 1; min-width: 280px;" class="licence-card">
<span style="font-size: 11px; font-weight: 700; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.5px;">Výukový kód (Pro žáky ve třídách a učitele)</span>
<div style="color: #cbd5e1; font-size: 13px; margin: 4px 0 8px 0;">Zadávají žáci ve vašich hodinách pro založení firmy a práci ve třídě.</div>
<div class="licence-val" style="background: rgba(14, 165, 233, 0.15); color: #38bdf8; border: 1px solid rgba(14, 165, 233, 0.4);">{skolni_kod}</div>
</div>
<div style="flex: 1; min-width: 280px;" class="licence-card">
<span style="font-size: 11px; font-weight: 700; color: #34d399; text-transform: uppercase; letter-spacing: 0.5px;">Zákaznický kód (Pro ostatní žáky školy)</span>
<div style="color: #cbd5e1; font-size: 13px; margin: 4px 0 8px 0;">Tento kód předejte ostatním žákům školy, aby mohli na E-shopu nakupovat.</div>
<div class="licence-val" style="background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4);">{z_kod}</div>
</div>
</div>
</div>"""
    st.markdown(box_kody_html, unsafe_allow_html=True)
elif is_admin:
    st.markdown("""<div class="licence-box"><h4 style="margin: 0; color: #cbd5e1;">Režim: Hlavní Administrátor</h4><p style="margin: 5px 0 0 0; font-size: 0.9em; color: #94a3b8;">Máte neomezený přístup napříč všemi školami v systému.</p></div>""", unsafe_allow_html=True)

# =========================================================================
# 1. ŘÍDÍCÍ PANEL (ACTION CENTER)
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
    with st.container(border=True):
        st.info(f"**Stav registrací ve vašich třídách**\n\nVe vašich třídách je aktuálně registrováno celkem **{pocet_zaku_celkem} žáků**.\nZ toho **{pocet_zaku_zakladni_role} žáků** má zatím jen základní roli.")

with col_dash2:
    if g_pocet_celkem_restu > 0:
        with st.container(border=True):
            st.warning(f"**Nevyřízené úkoly a audity ({g_pocet_celkem_restu})**")
            if g_firmy_cekajici: st.write(f"• **Žádosti o registraci firmy:** {len(g_firmy_cekajici)}")
            if g_questy_cekajici: st.write(f"• **Odevzdané úkoly ke kontrole:** {len(g_questy_cekajici)}")
            if g_kalkulace_cekajici: st.write(f"• **Kalkulace produktů pro E-shop:** {len(g_kalkulace_cekajici)}")
            if g_priznani_cekajici: st.write(f"• **Odevzdaná daňová přiznání:** {len(g_priznani_cekajici)}")
            if g_uvery_cekajici: st.write(f"• **Žádosti o firemní úvěr:** {len(g_uvery_cekajici)}")
    else:
        with st.container(border=True):
            st.success("**Čistý stůl**\n\nŽádné firmy ani úkoly nečekají na váš audit.")

st.write("---")

# =========================================================================
# 2. DOHLED NAD ZÁKAZNÍKY ŠKOLY
# =========================================================================
st.subheader("Dohled nad Zákazníky školy (Konzumenty)")
with st.expander("Seznam zákazníků školy a správa jejich peněženek (Rozbalit)", expanded=False):
    st.caption("Tito žáci jsou registrováni pod kódem pro zákazníky a nakupují na školním E-shopu od studentských firem.")
    res_zakaznici = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?skolni_kod=eq.{skolni_kod}&trida_nazev=eq.Zákazník&role=neq.ucitel", headers=headers).json()
    zakaznici = res_zakaznici if isinstance(res_zakaznici, list) else []
    
    if not zakaznici:
        st.info("Ve škole zatím nejsou registrováni žádní zákazníci.")
    else:
        df_zak = pd.DataFrame([{"Jméno zákazníka": z["jmeno"], "Zůstatek (M-K)": z.get("kredity", 0)} for z in zakaznici])
        st.dataframe(df_zak, use_container_width=True)
        
        with st.form("form_ucitel_korekce_zakazniku_robust"):
            col_k1, col_k2, col_k3 = st.columns([2, 2, 1])
            with col_k1: 
                z_vyber = st.selectbox("Vyberte zákazníka:", [z["jmeno"] for z in zakaznici])
            with col_k2: 
                akce = st.selectbox("Akce:", ["Resetovat heslo na 1234", "Strhnout kredity (Pokuta)", "Přidat kredity (Bonus)", "Smazat účet (Ban)"])
            with col_k3: 
                hodnota = st.number_input("Částka M-K (při pokutě/bonusu):", min_value=1.0, value=50.0)
            
            sub_zakaznik = st.form_submit_button("Provést akci")
            
        if sub_zakaznik:
            z_target = next((z for z in zakaznici if z["jmeno"] == z_vyber), None)
            if z_target:
                if akce == "Resetovat heslo na 1234":
                    requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?id=eq.{z_target['id']}", headers=headers, json={"heslo": "1234"})
                    st.success(f"✅ Zákazníkovi **{z_vyber}** bylo nastaveno heslo: `1234`.")
                elif akce == "Smazat účet (Ban)":
                    requests.delete(f"{SUPABASE_URL}/rest/v1/uzivatele?id=eq.{z_target['id']}", headers=headers)
                    st.success(f"✅ Účet zákazníka {z_vyber} byl smazán.")
                elif akce == "Strhnout kredity (Pokuta)":
                    novy = max(0, z_target.get("kredity", 0) - hodnota)
                    requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?id=eq.{z_target['id']}", headers=headers, json={"kredity": novy})
                    st.success(f"✅ Zákazníkovi {z_vyber} bylo strženo {hodnota} M-K.")
                elif akce == "Přidat kredity (Bonus)":
                    novy = z_target.get("kredity", 0) + hodnota
                    requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?id=eq.{z_target['id']}", headers=headers, json={"kredity": novy})
                    st.success(f"✅ Zákazníkovi {z_vyber} bylo přidáno {hodnota} M-K.")
                time.sleep(1.5)
                st.rerun()

st.write("---")

# =========================================================================
# 3. SPRÁVA VÝUKOVÝCH TŘÍD A FIREM
# =========================================================================
st.subheader("Výukové třídy a Studentské firmy")

if is_admin:
    res_tridy = requests.get(f"{SUPABASE_URL}/rest/v1/tridy?select=*&order=id.desc", headers=headers).json()
else:
    res_tridy = requests.get(f"{SUPABASE_URL}/rest/v1/tridy?skolni_kod=eq.{skolni_kod}&ucitel_jmeno=eq.{ucitel_jmeno}&select=*&order=id.desc", headers=headers).json()

moje_tridy = res_tridy if (isinstance(res_tridy, list) and res_tridy) else []

with st.expander("Založení nové třídy / skupiny"):
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
                time.sleep(1.5)
                st.rerun()

# Detekce nezařazených žáků
res_nezarazeni = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?skolni_kod=eq.{skolni_kod}&trida_nazev=eq.Nezařazeno&role=neq.ucitel", headers=headers).json()
nezarazeni_zaci = res_nezarazeni if isinstance(res_nezarazeni, list) else []

if nezarazeni_zaci:
    st.error(f"**⚠️ Nezařazení žáci (Čekají na zařazení do třídy)**\n\n{len(nezarazeni_zaci)} žáků se zaregistrovalo výukovým kódem dříve, než jste založili třídu. Přiřaďte je níže.")
    with st.expander("Přiřadit nezařazené žáky do vaší třídy", expanded=True):
        df_nez = pd.DataFrame([{"Jméno žáka": z["jmeno"], "Role": z.get("role", "zak"), "Zůstatek": z.get("kredity", 0)} for z in nezarazeni_zaci])
        st.dataframe(df_nez, use_container_width=True)
        
        if moje_tridy:
            with st.form("form_presun_nezarazenych_do_tridy_robust"):
                col_nz1, col_nz2, col_nz3 = st.columns([2, 2, 1])
                with col_nz1:
                    nz_vyber = st.selectbox("Vyberte žáka:", [z["jmeno"] for z in nezarazeni_zaci])
                with col_nz2:
                    nz_cilova_trida = st.selectbox("Zařadit do třídy:", [t["nazev_tridy"] for t in moje_tridy])
                with col_nz3:
                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    sub_presun = st.form_submit_button("Přesunout žáka")
                    
            if sub_presun:
                target_nz = next((z for z in nezarazeni_zaci if z["jmeno"] == nz_vyber), None)
                if target_nz:
                    requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?id=eq.{target_nz['id']}", headers=headers, json={"trida_nazev": nz_cilova_trida})
                    st.success(f"✅ Žák {nz_vyber} byl přesunut do třídy {nz_cilova_trida}.")
                    time.sleep(1.5)
                    st.rerun()
        else:
            st.info("Založte si nejprve výše svou první třídu, abyste do ní mohli žáky zařadit.")
            
st.write("---")

if not moje_tridy:
    st.info("Zatím jste si nezaložili žádnou třídu. Vytvořte prosím svou první třídu výše, aby se do ní mohli žáci registrovat a zakládat firmy.")
else:
    seznam_trid_nazvy = [t["nazev_tridy"] for t in moje_tridy]
    aktivni_trida = st.selectbox("Vyberte třídu, se kterou právě pracujete:", seznam_trid_nazvy)

    # Načtení žáků a firem vybrané třídy
    res_zaci = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?skolni_kod=eq.{skolni_kod}&trida_nazev=eq.{aktivni_trida}&role=neq.ucitel&order=id.asc", headers=headers).json()
    zaci_tridy = res_zaci if isinstance(res_zaci, list) else []

    res_firmy = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?skolni_kod=eq.{skolni_kod}&trida_nazev=eq.{aktivni_trida}&select=*&order=id.desc", headers=headers).json()
    firmy = res_firmy if isinstance(res_firmy, list) else []

    # Správa žáků vybrané třídy
    with st.expander(f"Seznam žáků třídy {aktivni_trida} (Role, Odměny a Reset hesel)", expanded=True):
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
            
            seznam_jmen_tridy = [z["jmeno"] for z in zaci_tridy]
            
            # --- ZMENA ROLE ---
            st.markdown("##### 1. Správa role žáka")
            with st.form("form_ucitel_zmena_role_zaka_robust"):
                col_z1, col_z2, col_z3 = st.columns([2, 2, 1])
                with col_z1:
                    vybrany_zak_role = st.selectbox("Vyberte žáka pro změnu role:", seznam_jmen_tridy)
                with col_z2:
                    nova_role = st.selectbox("Nastavit oprávnění:", ["firma (Podnikatel / Zakladatel)", "zak (Běžný žák)"])
                with col_z3:
                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    sub_role = st.form_submit_button("Uložit roli")
                    
            if sub_role:
                target_user_role = next((z for z in zaci_tridy if z["jmeno"] == vybrany_zak_role), None)
                if target_user_role:
                    role_kod = "firma" if "firma" in nova_role else "zak"
                    requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?id=eq.{target_user_role['id']}", headers=headers, json={"role": role_kod})
                    st.success(f"✅ Žákovi {vybrany_zak_role} byla úspěšně nastavena role.")
                    time.sleep(1.5)
                    st.rerun()

            st.divider()
            
            # --- ODMENY A POKUTY ---
            st.markdown("##### 2. Přímé udělení odměny / stržení kreditů žákovi")
            with st.form("form_ucitel_odmena_zaka_penez_robust"):
                col_o1, col_o2, col_o3 = st.columns([2, 1.5, 1])
                with col_o1:
                    vybrany_zak_penize = st.selectbox("Vyberte žáka pro transakci:", seznam_jmen_tridy)
                with col_o2:
                    akce_penize = st.selectbox("Typ transakce:", ["Připsat odměnu (Bonus)", "Strhnout kredity (Pokuta)"])
                with col_o3:
                    castka_odmeny = st.number_input("Částka M-K:", min_value=1.0, value=25.0)
                
                sub_penize = st.form_submit_button("Provést transakci")
                
            if sub_penize:
                target_user = next((z for z in zaci_tridy if z["jmeno"] == vybrany_zak_penize), None)
                if target_user:
                    akt_bal = float(target_user.get("kredity", 0))
                    novy_bal = (akt_bal + castka_odmeny) if "Bonus" in akce_penize else max(0.0, akt_bal - castka_odmeny)
                    requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?id=eq.{target_user['id']}", headers=headers, json={"kredity": novy_bal})
                    st.success(f"✅ Transakce úspěšná: Žák **{vybrany_zak_penize}** má nyní **{novy_bal:.2f} M-K**.")
                    time.sleep(1.5)
                    st.rerun()

            st.divider()
            
            # --- RESET HESLA ---
            st.markdown("##### 3. Reset zapomenutého hesla žáka")
            with st.form("form_ucitel_reset_hesla_zaka_tridy_robust"):
                col_r1, col_r2 = st.columns([2, 1])
                with col_r1:
                    vybrany_zak_heslo = st.selectbox("Vyberte žáka pro reset hesla:", seznam_jmen_tridy)
                    nove_heslo_pro_zaka = st.text_input("Zadejte nové heslo:", value="1234")
                with col_r2:
                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    sub_heslo = st.form_submit_button("Nastavit heslo")
                    
            if sub_heslo:
                target_user_pw = next((z for z in zaci_tridy if z["jmeno"] == vybrany_zak_heslo), None)
                if target_user_pw:
                    requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?id=eq.{target_user_pw['id']}", headers=headers, json={"heslo": nove_heslo_pro_zaka.strip()})
                    st.success(f"✅ Žákovi **{vybrany_zak_heslo}** bylo nastaveno heslo: `{nove_heslo_pro_zaka.strip()}`.")

    st.write("---")

    # Audit firem dané třídy
    if not firmy:
        st.info(f"Ve třídě {aktivni_trida} zatím žádný žák neodeslal žádost o registraci firmy.")
    else:
        firmy_labels = []
        for f in firmy:
            status_tag = " [ČEKÁ NA SCHVÁLENÍ]" if f.get("stave_licence") == "CEKA_NA_SCHVALENI" else ""
            firmy_labels.append(f"{f['nazev_firmy']}{status_tag}")

        vybrany_label = st.selectbox("Vyberte startup k auditu:", firmy_labels)
        vybrana_firma_nazev = vybrany_label.replace(" [ČEKÁ NA SCHVÁLENÍ]", "")
        firma = next(f for f in firmy if f["nazev_firmy"] == vybrana_firma_nazev)
        f_id = firma["id"]

        tab_legal, tab_aktiva, tab_hr, tab_finance, tab_questy, tab_stat, tab_banka, tab_hodnoceni = st.tabs([
            "1. Spis a Notář", "2. Vize a AI", "3. HR a Tým", "4. E-shop a Zákazníci", "5. Úřad práce a XP", "6. Státní pokladna a Daně", "7. Pravidla Ekonomiky", "8. Přehled a Hodnocení"
        ])

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
                        for p in [p.strip() for p in zamer_raw.split("|")]: st.markdown(f"* {p}")
                    else: st.write(zamer_raw if zamer_raw else "Neuvedeno")
                    st.divider()
                    st.markdown("#### Statutární orgány (Vedení)")
                    st.markdown(f"* **CEO:** {firma.get('ceo_jmeno', 'Neobsazeno')}")
                    st.markdown(f"* **CFO:** {firma.get('cfo_jmeno', 'Neobsazeno')}")
                    st.markdown(f"* **CTO:** {firma.get('cto_jmeno', 'Neobsazeno')}")
                    st.divider()
                    st.markdown("#### Zaměstnanci a pracovníci")
                    if zamestnanci:
                        for z in zamestnanci: st.markdown(f"* **{z['jmeno_zamestnance']}** — {z.get('pozice', 'Pracovník')} ({z.get('hodinova_sazba', 0)} M-K/hod)")
                    else: st.info("Firma zatím nepřijala žádné další zaměstnance.")
            with col_l2:
                stav = firma.get('stave_licence', 'CEKA_NA_SCHVALENI')
                stav_tridy = 'status-ok' if stav == 'SCHVALENO' else ('status-err' if stav in ['ZAMITNUTO', 'UKONCENO'] else 'status-wait')
                with st.container(border=True):
                    st.markdown("#### Stav zápisu do rejstříku")
                    st.markdown(f"Aktuální stav: <span class='{stav_tridy}'>{stav}</span>", unsafe_allow_html=True)
                if st.button("Schválit zápis do rejstříku a povolit činnost", type="primary"):
                    requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{f_id}", headers=headers, json={"stave_licence": "SCHVALENO", "duvod_zamitnuti": ""})
                    st.success(f"Firma {firma['nazev_firmy']} byla zapsána do rejstříku.")
                    time.sleep(1.5)
                    st.rerun()

        with tab_aktiva:
            canvas = requests.get(f"{SUPABASE_URL}/rest/v1/lean_canvas?firma_id=eq.{f_id}", headers=headers).json()
            if canvas and isinstance(canvas, list):
                with st.expander("Detail Lean Canvasu"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write("**1. Problém:**", canvas[0].get('problem', ''))
                        st.write("**3. Cílová skupina:**", canvas[0].get('cilova_skupina', ''))
                    with c2:
                        st.write("**2. Řešení:**", canvas[0].get('reseni', ''))
                        st.write("**4. Hodnota:**", canvas[0].get('hodnota', ''))
            else: st.info("Firma zatím nedodala Lean Canvas.")

        with tab_hr:
            zamestnanci_full = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?firma_id=eq.{f_id}", headers=headers).json()
            if zamestnanci_full and isinstance(zamestnanci_full, list):
                df_zam_full = pd.DataFrame(zamestnanci_full)[['jmeno_zamestnance', 'pozice', 'hodinova_sazba', 'vyplaceno_celkem']]
                df_zam_full.columns = ['Jméno', 'Pozice', 'Sazba (M-K/hod)', 'Vyplaceno (M-K)']
                st.dataframe(df_zam_full, use_container_width=True)
            else: st.info("Firma neeviduje žádné zaměstnance.")

        with tab_finance:
            kalkulace = requests.get(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy?firma_id=eq.{f_id}", headers=headers).json()
            if kalkulace and isinstance(kalkulace, list):
                for k in kalkulace:
                    with st.container(border=True):
                        st.markdown(f"**{k['nazev_produktu']}** (Cena: {k['konecna_cena']} M-K)")
                        if not k['schvaleno_uradem']:
                            if st.button(f"Schválit produkt: {k['nazev_produktu']}", key=f"kalk_{k['id']}"):
                                requests.patch(f"{SUPABASE_URL}/rest/v1/kalkulacni_listy?id=eq.{k['id']}", headers=headers, json={"schvaleno_uradem": True})
                                st.rerun()
            else: st.info("Žádné kalkulace.")

        with tab_questy:
            st.subheader("Úkoly třídy na Úřadu práce")
            with st.form("form_ucitel_pridat_novy_quest_clean"):
                qn = st.text_input("Název úkolu:")
                qp = st.text_area("Popis:")
                qo = st.number_input("Odměna za splnění (M-K):", min_value=1.0, value=20.0)
                if st.form_submit_button("Vypsat úkol na Úřad práce"):
                    requests.post(f"{SUPABASE_URL}/rest/v1/questy", headers=headers, json={"nazev": qn, "popis": qp, "odmena": qo, "zadavatel": ucitel_jmeno, "stav": "VOLNY"})
                    st.rerun()

        with tab_stat:
            res_stat = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.Stat", headers=headers).json()
            stat_kredity = res_stat[0]['kredity'] if (isinstance(res_stat, list) and len(res_stat) > 0) else 0
            st.markdown(f"### Rozpočet vybraných daní školy: `{stat_kredity:.2f} M-K`")

        with tab_banka:
            nastaveni_res = requests.get(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{skolni_kod}", headers=headers).json()
            akt_nastaveni = nastaveni_res[0] if (isinstance(nastaveni_res, list) and len(nastaveni_res) > 0) else {}
            
            with st.form("form_nastaveni_ekonomiky_skoly"):
                st.markdown("#### Nastavení ekonomických pravidel školy")
                st.caption(f"Platné pro licenční kód: **{skolni_kod}**")
                n_kurz = st.number_input("Kurz M-Kreditu k CZK (1 M-K = X Kč):", min_value=1.0, value=float(akt_nastaveni.get('kurz_kc', 10.0)))
                n_dan = st.number_input("M-TECH Daň pro e-shop (%):", min_value=0.0, max_value=50.0, value=float(akt_nastaveni.get('mtech_dan_pct', 15.0)))
                n_dan_prijem = st.number_input("Daň z příjmu zaměstnanců (%):", min_value=0.0, max_value=50.0, value=float(akt_nastaveni.get('dan_prijem_pct', 15.0)))
                n_zakaznik = st.number_input("Výchozí startovací kredit pro ZÁKAZNÍKA (M-K):", min_value=0.0, value=float(akt_nastaveni.get('start_kredit_zakaznik', 50.0)))
                n_cenik = st.text_area("Globální ceník školy (materiály, pronájmy):", value=str(akt_nastaveni.get('globalni_cenik', '')), height=150)
                
                if st.form_submit_button("Uložit ekonomická pravidla"):
                    requests.patch(f"{SUPABASE_URL}/rest/v1/skolni_nastaveni?skolni_kod=eq.{skolni_kod}", headers=headers, json={
                        "kurz_kc": n_kurz, "globalni_cenik": n_cenik, "mtech_dan_pct": n_dan, "dan_prijem_pct": n_dan_prijem, "start_kredit_zakaznik": n_zakaznik
                    })
                    st.success("Pravidla ekonomiky byla uložena.")
                    time.sleep(1.5)
                    st.rerun()

        with tab_hodnoceni:
            if zaci_tridy:
                st.dataframe(pd.DataFrame([{"Jméno": z['jmeno'], "Role": z.get('role', 'zak'), "Zůstatek (M-K)": z.get('kredity', 0)} for z in zaci_tridy]), use_container_width=True)
