import streamlit as st
import json
import re
import requests
import base64
import zipfile
import xml.etree.ElementTree as ET
import io

# =========================================================================
# KONFIGURACE DATABÁZE
# =========================================================================
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
API_KEY = st.secrets.get("GEMINI_API_KEY", "") or st.secrets.get("AI_API_KEY", "")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# =========================================================================
# ZÁCHRANNÝ KRUH PŘI STISKNUTÍ F5 (Bypass chyby Streamlitu)
# =========================================================================
if not st.session_state.get("prihlasen"):
    qs_user = st.query_params.get("user")
    if qs_user:
        res_auto = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele", headers=HEADERS, params={"jmeno": f"eq.{qs_user}", "select": "*"}).json()
        if isinstance(res_auto, list) and len(res_auto) > 0:
            st.session_state.prihlasen = True
            st.session_state.role = str(res_auto[0]["role"]).lower()
            st.session_state.kredity = res_auto[0]["kredity"]
            st.session_state.uzivatel = res_auto[0]["jmeno"]
            st.session_state.skolni_kod = res_auto[0].get("skolni_kod", "")
            
            # Rychlé zjištění firmy
            u_name = str(qs_user).strip().lower()
            sk_kod = st.session_state.get("skolni_kod", "")
            r_firmy = requests.get(f"{SUPABASE_URL}/rest/v1/firmy", headers=HEADERS, params={"skolni_kod": f"eq.{sk_kod}", "select": "*"}).json()
            ma_pristup = False
            if isinstance(r_firmy, list):
                for f in r_firmy:
                    if str(f.get('ceo_jmeno','')).lower() == u_name or str(f.get('cfo_jmeno','')).lower() == u_name or str(f.get('cto_jmeno','')).lower() == u_name:
                        st.session_state.firma_id = f.get("id")
                        st.session_state.firma_nazev = f.get("obchodni_firma", f.get("nazev", "Tým"))
                        ma_pristup = True
                        break
            if not ma_pristup:
                r_zam = requests.get(f"{SUPABASE_URL}/rest/v1/zamestnanci", headers=HEADERS, params={"jmeno_zamestnance": f"ilike.{u_name}", "select": "*"}).json()
                if isinstance(r_zam, list) and len(r_zam) > 0:
                    st.session_state.firma_id = r_zam[0].get("firma_id")
                    st.session_state.firma_nazev = r_zam[0].get("firma_nazev", "Tým")
            
            st.rerun() # Okamžitě načte stránku znovu, už s přihlášením

# Pokud ani záchranný kruh nepomohl (žák umazal jméno z URL):
if not st.session_state.get("prihlasen") or not st.session_state.get("uzivatel"):
    st.warning("Spojení s aplikací bylo přerušeno (např. obnovením stránky bez parametrů).")
    if st.button("🏠 Přejít zpět na hlavní přihlašovací stránku"):
        st.switch_page("app.py")
    st.stop()


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
.mtech-header { font-size: 1.5rem; font-weight: 800; background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -0.5px; margin-bottom: 0.5rem; }
.score-panel { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border: 1px solid #334155; border-radius: 8px; padding: 18px; text-align: center; color: #ffffff; margin-bottom: 20px;}
.score-val { font-size: 2.6rem; font-weight: 800; background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; line-height: 1.1; margin: 6px 0; }
.score-lbl { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8; font-weight: 600; }
.canvas-block { background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 15px; min-height: 140px; color: #e2e8f0; }
.canvas-tag { font-size: 0.75rem; font-weight: 800; color: #00B4D8; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #334155; padding-bottom: 6px; margin-bottom: 10px; }
.chat-mentor { background: #1e293b; border-left: 4px solid #00B4D8; padding: 15px; border-radius: 0 8px 8px 0; margin-bottom: 10px; color: #e2e8f0; font-size: 0.95rem; }
.chat-user { background: #0f172a; border: 1px solid #334155; padding: 15px; border-radius: 8px; margin-bottom: 10px; text-align: right; color: #e2e8f0; font-size: 0.95rem; }
.crisis-box { background: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; padding: 20px; border-radius: 8px; color: #fca5a5; font-weight: 600; font-size: 1.05em;}
.file-badge { background: #334155; padding: 4px 8px; border-radius: 6px; font-size: 0.85em; font-weight: 600; color: #94a3b8; display: inline-block; margin-bottom: 6px;}
</style>
""", unsafe_allow_html=True)

if "customer_history" not in st.session_state: st.session_state.customer_history = []
if "krize_aktivni" not in st.session_state: st.session_state.krize_aktivni = None
if "aktivni_model_nazev" not in st.session_state: st.session_state.aktivni_model_nazev = "Automatická detekce"

is_teacher = st.session_state.get("role") == "ucitel"
is_demo = False

if is_teacher:
    st.markdown("<div class='mtech-header'>Kontrolní audit: Lean Startup projekty</div>", unsafe_allow_html=True)
    skolni_kod = st.session_state.get("skolni_kod", "")
    res_f = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?skolni_kod=eq.{skolni_kod}&select=id,obchodni_firma,nazev", headers=HEADERS).json()
    
    firm_opts = {}
    if isinstance(res_f, list) and res_f:
        firm_opts = {f.get("obchodni_firma", f.get("nazev", f"Firma #{f.get('id')}")): f["id"] for f in res_f}
    
    firm_opts = {"DEMO REŽIM (Testovací hřiště pro učitele)": 0, **firm_opts}

    selected_firm_name = st.selectbox("Vyberte firmu k auditu (nebo si aplikaci zkuste v Demo režimu):", list(firm_opts.keys()))
    active_firma_id = firm_opts[selected_firm_name]
    active_firma_nazev = selected_firm_name
    
    if active_firma_id == 0:
        is_demo = True
        st.info("Jste v testovacím Demo režimu. Můžete s aplikací volně pracovat. Po odhlášení se data smažou.")
else:
    active_firma_id = st.session_state.get("firma_id")
    active_firma_nazev = st.session_state.get("firma_nazev", "Váš projekt")
    if not active_firma_id:
        st.info("Pro práci s modulem Lean Startup musíte být zakladatelem nebo členem firmy.")
        st.stop()
    st.markdown(f"<div class='mtech-header'>Lean Startup Validator: {active_firma_nazev}</div>", unsafe_allow_html=True)

if is_demo:
    if "demo_lean_data" not in st.session_state:
        st.session_state.demo_lean_data = {"canvas": {}, "validation_score": 0, "chat_history": []}
    project_data = st.session_state.demo_lean_data
else:
    res_p = requests.get(f"{SUPABASE_URL}/rest/v1/firma_lean_projects?firma_id=eq.{active_firma_id}", headers=HEADERS).json()
    if not res_p or not isinstance(res_p, list) or len(res_p) == 0:
        init_payload = {"firma_id": int(active_firma_id), "skola_id": str(st.session_state.get("skolni_kod", "")), "canvas": {}, "validation_score": 0, "chat_history": []}
        r_create = requests.post(f"{SUPABASE_URL}/rest/v1/firma_lean_projects", headers=HEADERS, json=init_payload).json()
        project_data = r_create[0] if (isinstance(r_create, list) and len(r_create) > 0) else init_payload
    else:
        project_data = res_p[0]

canvas = project_data.get("canvas", {})
val_score = project_data.get("validation_score", 0)
chat_history = project_data.get("chat_history", [])

def save_to_db(updated_fields):
    if is_demo:
        st.session_state.demo_lean_data.update(updated_fields)
        return
    requests.patch(f"{SUPABASE_URL}/rest/v1/firma_lean_projects?firma_id=eq.{active_firma_id}", headers=HEADERS, json=updated_fields)

with st.sidebar:
    st.caption(f"Aktivní engine: `{st.session_state.aktivni_model_nazev}`")
    st.markdown(f"<div class='score-panel'><div class='score-lbl'>Ověření byznys modelu</div><div class='score-val'>{val_score} %</div></div>", unsafe_allow_html=True)
    if val_score == 0: st.info("Představte svůj nápad mentorovi v záložce 2.")
    elif val_score < 40: st.warning("Fáze: Hledání Problem-Solution Fit. Ověřte problém.")
    elif val_score < 75: st.info("Fáze: Příprava MVP a pilotního testování.")
    else: st.success("Fáze: Validovaný model připravený k nasazení!")

def extract_text_from_docx(file_bytes_io):
    try:
        with zipfile.ZipFile(file_bytes_io) as docx:
            return "\n".join([node.text for node in ET.fromstring(docx.read('word/document.xml')).iterfind('.//w:t', {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}) if node.text])
    except: return ""

def prepare_local_file_payload(uploaded_file):
    if not uploaded_file: return None, ""
    fname, fbytes = uploaded_file.name.lower(), uploaded_file.getvalue()
    if fname.endswith(".docx"): return None, f"\n\n[DOKUMENT]:\n{extract_text_from_docx(io.BytesIO(fbytes))}\n"
    elif fname.endswith((".txt", ".csv", ".md")): return None, f"\n\n[DOKUMENT]:\n{fbytes.decode('utf-8', errors='ignore')}\n"
    elif fname.endswith(".pdf"): return {"mime_type": "application/pdf", "data": base64.b64encode(fbytes).decode("utf-8")}, f"\n[PDF: {uploaded_file.name}]"
    elif fname.endswith((".png", ".jpg", ".jpeg", ".webp")):
        mime = "image/png" if fname.endswith(".png") else "image/jpeg" if fname.endswith(".jp") else "image/webp"
        return {"mime_type": mime, "data": base64.b64encode(fbytes).decode("utf-8")}, f"\n[OBRÁZEK: {uploaded_file.name}]"
    return None, ""

def call_ai_multimodal(prompt_text, inline_attachment=None):
    key = API_KEY.strip()
    if key.startswith("gsk_"):
        st.session_state.aktivni_model_nazev = "Groq Llama-3"
        return requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt_text}], "temperature": 0.3}).json()["choices"][0]["message"]["content"]
    elif key.startswith("sk-") and not key.startswith("sk-ant"):
        st.session_state.aktivni_model_nazev = "OpenAI GPT-4o"
        return requests.post("https://api.openai.com/v1/chat/completions", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt_text}], "temperature": 0.3}).json()["choices"][0]["message"]["content"]
    else:
        mods = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={key}").json().get("models", [])
        dm = [m["name"].replace("models/", "") for m in mods if "generateContent" in m.get("supportedGenerationMethods", [])] or ["gemini-1.5-flash"]
        dm.sort(key=lambda x: 0 if "flash" in x.lower() else 1)
        for m in dm:
            payload = {"contents": [{"parts": [{"text": prompt_text}] + ([{"inline_data": inline_attachment}] if inline_attachment else [])}], "generationConfig": {"temperature": 0.3}}
            r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={key}", json=payload)
            if "candidates" in r.json():
                st.session_state.aktivni_model_nazev = f"Gemini ({m})"
                return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        raise Exception("API odmítlo požadavek.")

tab_canvas, tab_mentor, tab_zakaznik, tab_krize = st.tabs(["1. Lean Canvas", "2. Strategický mentor", "3. Zákaznický simulátor", "4. Generátor krizí"])

with tab_canvas:
    st.info("💡 **Lean Canvas je dynamický nástroj**, který se vyvíjí. Můžete si jej sice ručně vyplňovat a přepisovat sami v záložce Firemní Dashboard, ale pokud jej do Dashboardu **propíšete přímo odsud** (až po úspěšném obhájení a splnění 80 % u Mentora), získáte mnohem větší jistotu, že je váš byznys model skutečně reálný a životaschopný.")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"<div class='canvas-block'><div class='canvas-tag'>1. Problém</div>{canvas.get('problem', '')}</div><br><div class='canvas-block'><div class='canvas-tag'>8. Klíčové Metriky</div>{canvas.get('metriky', '')}</div>", unsafe_allow_html=True)
    with col2: st.markdown(f"<div class='canvas-block'><div class='canvas-tag'>4. Řešení (MVP)</div>{canvas.get('reseni', '')}</div>", unsafe_allow_html=True)
    with col3: st.markdown(f"<div class='canvas-block'><div class='canvas-tag'>2. Unikátní Hodnota</div>{canvas.get('hodnota', '')}</div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='canvas-block'><div class='canvas-tag'>5. Nefér Výhoda</div>{canvas.get('nefer_vyhoda', '')}</div><br><div class='canvas-block'><div class='canvas-tag'>9. Kanály</div>{canvas.get('kanaly', '')}</div>", unsafe_allow_html=True)
    with col5: st.markdown(f"<div class='canvas-block'><div class='canvas-tag'>3. Cílovka</div>{canvas.get('cilovka', '')}</div>", unsafe_allow_html=True)
    col6, col7 = st.columns(2)
    with col6: st.markdown(f"<div class='canvas-block'><div class='canvas-tag'>6. Struktura Nákladů</div>{canvas.get('naklady', '')}</div>", unsafe_allow_html=True)
    with col7: st.markdown(f"<div class='canvas-block'><div class='canvas-tag'>7. Zdroje Příjmů</div>{canvas.get('prijmy', '')}</div>", unsafe_allow_html=True)

    if val_score >= 80 and not is_teacher:
        st.divider()
        st.success("Dosáhli jste potřebného ověření (80 %)! Váš byznys model je schválen mentorem.")
        if st.button("Zapsat a přepsat ruční Lean Canvas v Dashboardu", type="primary"):
            spis_text = f"**NAŠE ŘEŠENÍ (MVP):**\n{canvas.get('reseni', '')}\n\n**ŘEŠÍME PROBLÉM:**\n{canvas.get('problem', '')}\n\n**CÍLOVÁ SKUPINA:**\n{canvas.get('cilovka', '')}\n\n**UNIKÁTNÍ HODNOTA:**\n{canvas.get('hodnota', '')}"
            requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{active_firma_id}", headers=HEADERS, json={"popis": spis_text})
            
            lc_payload = {
                "problem": canvas.get("problem", ""), "reseni": canvas.get("reseni", ""), "hodnota": canvas.get("hodnota", ""),
                "nefer_vyhoda": canvas.get("nefer_vyhoda", ""), "cilovka": canvas.get("cilovka", ""), "metriky": canvas.get("metriky", ""),
                "kanaly": canvas.get("kanaly", ""), "naklady": canvas.get("naklady", ""), "prijmy": canvas.get("prijmy", "")
            }
            r_lc = requests.get(f"{SUPABASE_URL}/rest/v1/lean_canvas?firma_id=eq.{active_firma_id}", headers=HEADERS).json()
            if isinstance(r_lc, list) and len(r_lc) > 0:
                r_patch = requests.patch(f"{SUPABASE_URL}/rest/v1/lean_canvas?firma_id=eq.{active_firma_id}", headers=HEADERS, json=lc_payload)
            else:
                lc_payload["firma_id"] = active_firma_id
                r_patch = requests.post(f"{SUPABASE_URL}/rest/v1/lean_canvas", headers=HEADERS, json=lc_payload)
                
            if r_patch.status_code in [200, 201, 204]:
                st.balloons()
                st.success("Úspěšně zapsáno! Váš AI vyvalidovaný plán se právě propsal do všech 9 okének na Firemním Dashboardu.")
            else: st.error(f"Chyba databáze ({r_patch.status_code}).")

with tab_mentor:
    st.subheader("Konzultace s Lean Startup Mentorem")
    uploaded_doc = st.file_uploader("Nahrát soubor (PDF, Word, TXT, IMG)", type=["png", "jpg", "jpeg", "webp", "pdf", "docx", "txt", "csv", "md"])
    for msg in chat_history:
        div_class = "chat-user" if msg["role"] == "user" else "chat-mentor"
        file_tag = f"<div class='file-badge'>Příloha: {msg['file']}</div><br>" if msg.get("file") else ""
        st.markdown(f"<div class='{div_class}'><b>{'Vy' if msg['role']=='user' else 'Mentor'}:</b><br>{file_tag}{msg['content']}</div>", unsafe_allow_html=True)
    def submit_mentor():
        if st.session_state.mentor_input.strip() and (not is_teacher or is_demo):
            ui = st.session_state.mentor_input
            st.session_state.mentor_input = ""
            fp, ext = prepare_local_file_payload(uploaded_doc)
            chat_history.append({"role": "user", "content": ui, "file": uploaded_doc.name if uploaded_doc else None})
            prompt = f"Jsi zkušený Lean Startup mentor. Mluvíš česky. Reaguj na startup.\nCanvas: {json.dumps(canvas, ensure_ascii=False)}\nSkóre: {val_score}\nText: {ui + ext}\nOdpověz JEN jako JSON: {{\"odpoved_mentora\": \"...\", \"nove_skore\": 50, \"canvas_updaty\": {{\"problem\":\"...\", \"reseni\":\"...\", \"hodnota\":\"...\", \"nefer_vyhoda\":\"...\", \"cilovka\":\"...\", \"metriky\":\"...\", \"kanaly\":\"...\", \"naklady\":\"...\", \"prijmy\":\"...\"}}}}"
            with st.spinner("Analyzuji..."):
                try:
                    rt = call_ai_multimodal(prompt, fp)
                    m = re.search(r'\{.*\}', rt, re.DOTALL)
                    if m:
                        js = json.loads(m.group(0))
                        chat_history.append({"role": "mentor", "content": js.get("odpoved_mentora", ""), "file": None})
                        for k, v in js.get("canvas_updaty", {}).items():
                            if v: canvas[k] = v
                        save_to_db({"chat_history": chat_history, "validation_score": js.get("nove_skore", val_score), "canvas": canvas})
                    else:
                        chat_history.append({"role": "mentor", "content": rt, "file": None})
                        save_to_db({"chat_history": chat_history})
                except Exception as e: chat_history.append({"role": "mentor", "content": f"Chyba: {e}", "file": None})
    st.text_input("Zpráva mentorovi...", key="mentor_input", on_change=submit_mentor)

with tab_zakaznik:
    st.subheader("Customer Discovery")
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1: pv = st.text_input("Věk:", "52")
    with col_c2: pr = st.text_input("Pozice:", "Ředitel")
    with col_c3: pz = st.text_input("Priority:", "Málo času")
    for msg in st.session_state.customer_history:
        st.markdown(f"<div class='{'chat-user' if msg['role']=='user' else 'chat-mentor'}'><b>{'Vy' if msg['role']=='user' else 'Zákazník'}:</b><br>{msg['content']}</div>", unsafe_allow_html=True)
    def submit_customer():
        if st.session_state.customer_input.strip() and (not is_teacher or is_demo):
            ci = st.session_state.customer_input
            st.session_state.customer_input = ""
            st.session_state.customer_history.append({"role": "user", "content": ci})
            with st.spinner("Zákazník odpovídá..."):
                try: st.session_state.customer_history.append({"role": "customer", "content": call_ai_multimodal(f"Jsi zákazník. Věk {pv}, {pr}, {pz}. Startup řeší: {json.dumps(canvas, ensure_ascii=False)}. Vstup: {ci}")})
                except Exception as e: st.error(str(e))
    st.text_input("Dotaz na zákazníka...", key="customer_input", on_change=submit_customer)

with tab_krize:
    st.subheader("Black Swan (Simulace rizik)")
    if st.button("Vygenerovat krizi") and (not is_teacher or is_demo):
        with st.spinner("Tvořím scénář..."):
            try: st.session_state.krize_aktivni = call_ai_multimodal(f"Vymysli krizi pro: {json.dumps(canvas, ensure_ascii=False)}. 2 věty, polož otázku.")
            except Exception as e: st.error(str(e))
    if st.session_state.krize_aktivni:
        st.markdown(f"<div class='crisis-box'><b>KRIZE:</b><br>{st.session_state.krize_aktivni}</div><br>", unsafe_allow_html=True)
        def submit_crisis():
            if st.session_state.krize_input.strip() and (not is_teacher or is_demo):
                ri = st.session_state.krize_input
                st.session_state.krize_input = ""
                with st.spinner("Hodnotím..."):
                    try: st.info(call_ai_multimodal(f"Krize: {st.session_state.krize_aktivni}. Řešení: {ri}. Zhodnoť 1-10 body."))
                    except Exception as e: st.error(str(e))
        st.text_input("Návrh řešení...", key="krize_input", on_change=submit_crisis)
