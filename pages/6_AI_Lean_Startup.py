import streamlit as st
import json
import re
import requests

if not st.session_state.get("prihlasen") or not st.session_state.get("uzivatel"):
    st.warning("Pro přístup k modulu Lean Startup je nutné se přihlásit na hlavní stránce.")
    st.stop()

SUPABASE_URL = st.secrets.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
API_KEY = st.secrets.get("GEMINI_API_KEY", "") or st.secrets.get("AI_API_KEY", "")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.mtech-header { font-size: 1.5rem; font-weight: 800; color: #0f172a; letter-spacing: -0.5px; margin-bottom: 0.5rem; }
.mtech-sub { color: #64748b; font-size: 0.9rem; margin-bottom: 1.5rem; }
.score-panel { background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 18px; text-align: center; color: #ffffff; }
.score-val { font-size: 2.6rem; font-weight: 800; color: #38bdf8; line-height: 1.1; margin: 6px 0; }
.score-lbl { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8; font-weight: 600; }
.canvas-block { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; min-height: 130px; }
.canvas-tag { font-size: 0.75rem; font-weight: 700; color: #0369a1; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #cbd5e1; padding-bottom: 4px; margin-bottom: 8px; }
.chat-mentor { background: #f1f5f9; border-left: 3px solid #0284c7; padding: 12px 14px; border-radius: 0 6px 6px 0; margin-bottom: 8px; color: #0f172a; font-size: 0.95rem; }
.chat-user { background: #ffffff; border: 1px solid #e2e8f0; padding: 12px 14px; border-radius: 6px; margin-bottom: 8px; text-align: right; color: #334155; font-size: 0.95rem; }
.log-item { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px 12px; margin-bottom: 6px; font-size: 0.85rem; color: #334155; }
.phase-active { background: #0284c7; color: #ffffff; font-weight: 700; padding: 6px 12px; border-radius: 4px; font-size: 0.8rem; text-align: center; }
.phase-inactive { background: #f1f5f9; color: #64748b; font-weight: 500; padding: 6px 12px; border-radius: 4px; font-size: 0.8rem; text-align: center; }
</style>
""", unsafe_allow_html=True)

uzivatel = str(st.session_state.uzivatel).strip()
skolni_kod = st.session_state.get("skolni_kod", "")
is_teacher = st.session_state.get("role") == "ucitel"

active_firma_id = None
active_firma_nazev = None

# Automatická detekce firemní příslušnosti
if is_teacher:
    st.markdown("<div class='mtech-header'>Kontrolní audit: Lean Startup projekty</div>", unsafe_allow_html=True)
    url_f = f"{SUPABASE_URL}/rest/v1/firmy?select=id,nazev,skolni_kod"
    if skolni_kod:
        url_f += f"&skolni_kod=eq.{skolni_kod}"
    res_f = requests.get(url_f, headers=HEADERS).json()
    firm_opts = {f["nazev"]: f["id"] for f in res_f} if isinstance(res_f, list) and res_f else {}
    if not firm_opts:
        st.warning("V této škole zatím nejsou evidovány žádné studentské firmy.")
        st.stop()
    selected_firm_name = st.selectbox("Vyberte firmu k auditu:", list(firm_opts.keys()))
    active_firma_id = firm_opts[selected_firm_name]
    active_firma_nazev = selected_firm_name
else:
    # 1. Kontrola vedení (CEO, CFO, CTO) napříč celou tabulkou firem
    r_firmy = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?select=id,nazev,ceo_jmeno,cfo_jmeno,cto_jmeno,skolni_kod", headers=HEADERS).json()
    if isinstance(r_firmy, list):
        for f in r_firmy:
            ceo = str(f.get('ceo_jmeno', '') or '').strip().lower()
            cfo = str(f.get('cfo_jmeno', '') or '').strip().lower()
            cto = str(f.get('cto_jmeno', '') or '').strip().lower()
            u_low = uzivatel.lower()
            if u_low in [ceo, cfo, cto]:
                active_firma_id = f["id"]
                active_firma_nazev = f["nazev"]
                if not skolni_kod and f.get("skolni_kod"):
                    skolni_kod = f.get("skolni_kod")
                break
                
    # 2. Kontrola řadových zaměstnanců
    if not active_firma_id:
        r_zam = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci?jmeno_zamestnance=eq.{uzivatel}&select=*", headers=HEADERS).json()
        if isinstance(r_zam, list) and len(r_zam) > 0:
            active_firma_id = r_zam[0].get("firma_id")
            active_firma_nazev = r_zam[0].get("firma_nazev", "Firemní tým")
            if not active_firma_id and active_firma_nazev:
                r_f_by_name = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?nazev=eq.{active_firma_nazev}&select=id", headers=HEADERS).json()
                if isinstance(r_f_by_name, list) and r_f_by_name:
                    active_firma_id = r_f_by_name[0]["id"]

    if not active_firma_id:
        st.info("Pro práci s modulem Lean Startup musíte být zakladatelem nebo členem firmy. Založte firmu v záložce Firemní Dashboard.")
        st.stop()

    st.markdown(f"<div class='mtech-header'>M-TECH Lean Startup Validator: {active_firma_nazev}</div>", unsafe_allow_html=True)
    st.markdown("<div class='mtech-sub'>Validace hypotéz, experimentální testování a řízení životního cyklu produktu podle metodiky Erica Riese.</div>", unsafe_allow_html=True)

# Načtení dat z tabulky firma_lean_projects
res_p = requests.get(f"{SUPABASE_URL}/rest/v1/firma_lean_projects?firma_id=eq.{active_firma_id}", headers=HEADERS).json()

if not res_p or not isinstance(res_p, list) or len(res_p) == 0:
    init_payload = {
        "firma_id": int(active_firma_id),
        "skola_id": str(skolni_kod or ""),
        "canvas": {"problem": "", "reseni": "", "hodnota": "", "nefer_vyhoda": "", "cilovka": "", "metriky": "", "kanaly": "", "naklady": "", "prijmy": ""},
        "validation_score": 0,
        "current_phase": "1. Formulace hypotézy",
        "test_cards": [],
        "mom_test_questions": [],
        "chat_history": [],
        "pivot_history": []
    }
    r_create = requests.post(f"{SUPABASE_URL}/rest/v1/firma_lean_projects", headers=HEADERS, json=init_payload).json()
    project_data = r_create[0] if (isinstance(r_create, list) and len(r_create) > 0) else init_payload
else:
    project_data = res_p[0]

canvas = project_data.get("canvas", {})
val_score = project_data.get("validation_score", 0)
test_cards = project_data.get("test_cards", [])
mom_questions = project_data.get("mom_test_questions", [])
chat_history = project_data.get("chat_history", [])
pivot_history = project_data.get("pivot_history", [])
curr_phase = project_data.get("current_phase", "1. Formulace hypotézy")

def save_to_db(updated_fields):
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/firma_lean_projects?firma_id=eq.{active_firma_id}",
        headers=HEADERS,
        json=updated_fields
    )

def call_lean_ai(prompt_text):
    key = API_KEY.strip()
    if key.startswith("gsk_"):
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {key}"}, json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt_text}], "temperature": 0.2}).json()
        return res["choices"][0]["message"]["content"]
    elif key.startswith("sk-"):
        res = requests.post("https://api.openai.com/v1/chat/completions", headers={"Authorization": f"Bearer {key}"}, json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt_text}], "temperature": 0.2}).json()
        return res["choices"][0]["message"]["content"]
    else:
        for m in ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]:
            try:
                r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={key}", json={"contents": [{"parts": [{"text": prompt_text}]}], "generationConfig": {"temperature": 0.2}}).json()
                if "candidates" in r:
                    return r["candidates"][0]["content"]["parts"][0]["text"]
            except Exception:
                continue
    raise Exception("AI integrační rozhraní není dostupné.")

phases = ["1. Formulace hypotézy", "2. Vývoj MVP", "3. Testování na trhu", "4. Vyhodnocení / Pivot"]
p_cols = st.columns(4)
for idx, p in enumerate(phases):
    with p_cols[idx]:
        css_cls = "phase-active" if p == curr_phase else "phase-inactive"
        st.markdown(f"<div class='{css_cls}'>{p}</div>", unsafe_allow_html=True)

st.divider()

with st.sidebar:
    st.markdown(f"""
    <div class="score-panel">
        <div class="score-lbl">Validation Score</div>
        <div class="score-val">{val_score} %</div>
        <div class="score-lbl">Ověření byznys modelu</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if not is_teacher:
        selected_phase = st.selectbox("Aktuální fáze cyklu:", phases, index=phases.index(curr_phase) if curr_phase in phases else 0)
        if selected_phase != curr_phase:
            save_to_db({"current_phase": selected_phase})
            st.rerun()

tab_canvas, tab_mentor, tab_cards, tab_mom, tab_pivots = st.tabs([
    "Lean Canvas", "Strategický mentor", "Experimentální karty", "The Mom Test", "Protokol učení"
])

with tab_canvas:
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"<div class='canvas-block'><div class='canvas-tag'>1. Problém</div>{canvas.get('problem','')}</div><br>", unsafe_allow_html=True)
        st.markdown(f"<div class='canvas-block'><div class='canvas-tag'>8. Klíčové metriky</div>{canvas.get('metriky','')}</div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='canvas-block'><div class='canvas-tag'>4. Řešení (MVP)</div>{canvas.get('reseni','')}</div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='canvas-block'><div class='canvas-tag'>2. Unikátní hodnota</div>{canvas.get('hodnota','')}</div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='canvas-block'><div class='canvas-tag'>5. Konkurenční výhoda</div>{canvas.get('nefer_vyhoda','')}</div><br>", unsafe_allow_html=True)
        st.markdown(f"<div class='canvas-block'><div class='canvas-tag'>9. Distribuční kanály</div>{canvas.get('kanaly','')}</div>", unsafe_allow_html=True)
    with c5:
        st.markdown(f"<div class='canvas-block'><div class='canvas-tag'>3. Cílový segment</div>{canvas.get('cilovka','')}</div>", unsafe_allow_html=True)

    c6, c7 = st.columns(2)
    with c6: st.markdown(f"<br><div class='canvas-block'><div class='canvas-tag'>6. Nákladová struktura</div>{canvas.get('naklady','')}</div>", unsafe_allow_html=True)
    with c7: st.markdown(f"<br><div class='canvas-block'><div class='canvas-tag'>7. Příjmové toky</div>{canvas.get('prijmy','')}</div>", unsafe_allow_html=True)

with tab_mentor:
    for m in chat_history:
        d_class = "chat-user" if m["role"] == "user" else "chat-mentor"
        sender = "Tým" if m["role"] == "user" else "Mentor"
        st.markdown(f"<div class='{d_class}'><b>{sender}:</b><br>{m['content']}</div>", unsafe_allow_html=True)

    if not is_teacher:
        u_msg = st.chat_input("Zadejte zprávu pro mentora a odešlete klávesou Enter...")
        if u_msg:
            chat_history.append({"role": "user", "content": u_msg})
            prompt = f"""
            Jsi analytický Lean Startup mentor (metodika Eric Ries, Steve Blank).
            Vystupuj věcně, bez emotikonů, bez přehnaných frází.
            Posuď odpověď týmu. Pokud tým zmiňuje Vanity Metrics (lajky, imprese), upozorni na to a navrhni Actionable Metrics (konverze, retence).
            Aktuální Lean Canvas: {json.dumps(canvas, ensure_ascii=False)}
            Skóre: {val_score}
            Zpráva týmu: {u_msg}

            Odpověz VÝHRADNĚ ve formátu JSON:
            {{
                "odpoved": "Strukturovaná zpětná vazba a 1-2 otázky k validaci rizik.",
                "nove_skore": 50,
                "canvas_updaty": {{"problem":"", "reseni":"", "hodnota":"", "nefer_vyhoda":"", "cilovka":"", "metriky":"", "kanaly":"", "naklady":"", "prijmy":""}}
            }}
            """
            with st.spinner("Probíhá analýza byznys modelu..."):
                raw = call_lean_ai(prompt)
                raw = re.sub(r'^```json\s*', '', raw).replace('```', '').strip()
                ai_data = json.loads(re.search(r'\{.*\}', raw, re.DOTALL).group(0))
                
                chat_history.append({"role": "mentor", "content": ai_data["odpoved"]})
                new_score = ai_data.get("nove_skore", val_score)
                
                new_updates = ai_data.get("canvas_updaty", {})
                for k, v in new_updates.items():
                    if v and v != canvas.get(k):
                        canvas[k] = v

                save_to_db({
                    "chat_history": chat_history,
                    "validation_score": new_score,
                    "canvas": canvas
                })
            st.rerun()

with tab_cards:
    st.markdown("#### Experimentální testovací karty")
    st.caption("Formulace hypotéz a kritérií ověření před zahájením vývoje.")

    if not is_teacher:
        with st.expander("Přidat novou testovací kartu", expanded=False):
            h_text = st.text_input("Předpoklad (Hypotéza):", placeholder="Věříme, že zákazníci postrádají...")
            e_text = st.text_input("Způsob ověření (Experiment):", placeholder="Ověříme to provedením...")
            m_text = st.text_input("Sledovaná veličina (Metrika):", placeholder="Budeme měřit počet...")
            c_text = st.text_input("Kritérium úspěchu:", placeholder="Hypotéza platí, pokud alespoň X z Y...")
            
            if st.button("Uložit kartu experimentu"):
                if h_text and e_text:
                    test_cards.append({"hypoteza": h_text, "experiment": e_text, "metrika": m_text, "kriterium": c_text, "stav": "Probíhá"})
                    save_to_db({"test_cards": test_cards})
                    st.rerun()

    for idx, card in enumerate(test_cards):
        with st.container(border=True):
            st.markdown(f"**Testovací karta #{idx+1} | Stav: {card.get('stav','Probíhá')}**")
            st.write(f"Hypotéza: {card['hypoteza']}")
            st.write(f"Experiment: {card['experiment']}")
            st.write(f"Metrika a kritérium: {card['metrika']} (Cíl: {card['kriterium']})")
            
            if not is_teacher and card.get("stav") == "Probíhá":
                cb1, cb2 = st.columns(2)
                with cb1:
                    if st.button("Potvrdit hypotézu", key=f"btn_val_{idx}"):
                        card["stav"] = "Potvrzeno"
                        save_to_db({"test_cards": test_cards})
                        st.rerun()
                with cb2:
                    if st.button("Zamítnout hypotézu (Nutný pivot)", key=f"btn_piv_{idx}"):
                        card["stav"] = "Zamítnuto"
                        pivot_history.append({"datum": "Aktuální cyklus", "duvod": f"Vyvrácena hypotéza #{idx+1}: {card['hypoteza']}"})
                        save_to_db({"test_cards": test_cards, "pivot_history": pivot_history})
                        st.rerun()

with tab_mom:
    st.markdown("#### The Mom Test dotazník")
    st.caption("Otázky zaměřené na minulé reálné chování a řešení problému bez návodného zkreslení.")

    if not is_teacher:
        if st.button("Generovat sadu otázek k rozhovorům"):
            prompt_mom = f"""
            Na základě Lean Canvasu: {json.dumps(canvas, ensure_ascii=False)}
            Vygeneruj 5 konkrétních otázek podle knihy The Mom Test (Rob Fitzpatrick) pro ověření problému u segmentu {canvas.get('cilovka','zákazníci')}.
            Otázky nesmí být návodné. Žádné emotikony. Čistý věcný text.
            """
            with st.spinner("Příprava dotazníku..."):
                mom_res = call_lean_ai(prompt_mom)
                save_to_db({"mom_test_questions": [{"text": mom_res}]})
                st.rerun()

    if mom_questions:
        st.info(mom_questions[0]["text"])

with tab_pivots:
    st.markdown("#### Protokol ověřeného učení a změn strategie")
    if not pivot_history:
        st.write("V průběhu simulace zatím nebyl evidován žádný strategický pivot.")
    for p in pivot_history:
        st.markdown(f"<div class='log-item'><b>Záznam:</b> {p.get('duvod','')}</div>", unsafe_allow_html=True)
