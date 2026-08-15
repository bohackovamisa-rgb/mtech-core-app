import streamlit as st
import json
import re
import requests
import base64
import zipfile
import xml.etree.ElementTree as ET
import io

# =========================================================================
# AUTENTIZACE A NAPOJENÍ NA M-TECH CORE
# =========================================================================
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
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Montserrat', sans-serif !important; }
.mtech-header { font-size: 1.5rem; font-weight: 800; background: -webkit-linear-gradient(45deg, #00B4D8, #0077B6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -0.5px; margin-bottom: 0.5rem; }
.mtech-sub { color: #94a3b8; font-size: 0.9rem; margin-bottom: 1.5rem; }
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

# Paměť pro funkce
if "customer_history" not in st.session_state: st.session_state.customer_history = []
if "krize_aktivni" not in st.session_state: st.session_state.krize_aktivni = None
if "aktivni_model_nazev" not in st.session_state: st.session_state.aktivni_model_nazev = "Automatická detekce"

is_teacher = st.session_state.get("role") == "ucitel"

if is_teacher:
    st.markdown("<div class='mtech-header'>Kontrolní audit: Lean Startup projekty</div>", unsafe_allow_html=True)
    skolni_kod = st.session_state.get("skolni_kod", "")
    res_f = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?skolni_kod=eq.{skolni_kod}&select=id,obchodni_firma,nazev", headers=HEADERS).json()
    
    if isinstance(res_f, list) and res_f:
        firm_opts = {f.get("obchodni_firma", f.get("nazev", f"Firma #{f.get('id')}")): f["id"] for f in res_f}
    else:
        firm_opts = {}

    if not firm_opts:
        st.warning("Zatím nejsou evidovány žádné studentské firmy.")
        st.stop()
        
    selected_firm_name = st.selectbox("Vyberte firmu k auditu:", list(firm_opts.keys()))
    active_firma_id = firm_opts[selected_firm_name]
    active_firma_nazev = selected_firm_name
else:
    active_firma_id = st.session_state.get("firma_id")
    active_firma_nazev = st.session_state.get("firma_nazev", "Váš projekt")

    if not active_firma_id:
        st.info("Pro práci s modulem Lean Startup musíte být zakladatelem nebo členem firmy. Založte si nejprve firmu v záložce Firemní Dashboard.")
        st.stop()

    st.markdown(f"<div class='mtech-header'>Lean Startup Validator: {active_firma_nazev}</div>", unsafe_allow_html=True)

# Načtení projektu z databáze
res_p = requests.get(f"{SUPABASE_URL}/rest/v1/firma_lean_projects?firma_id=eq.{active_firma_id}", headers=HEADERS).json()

if not res_p or not isinstance(res_p, list) or len(res_p) == 0:
    init_payload = {
        "firma_id": int(active_firma_id),
        "skola_id": str(st.session_state.get("skolni_kod", "")),
        "canvas": {"problem": "", "reseni": "", "hodnota": "", "nefer_vyhoda": "", "cilovka": "", "metriky": "", "kanaly": "", "naklady": "", "prijmy": ""},
        "validation_score": 0,
        "chat_history": []
    }
    r_create = requests.post(f"{SUPABASE_URL}/rest/v1/firma_lean_projects", headers=HEADERS, json=init_payload).json()
    project_data = r_create[0] if (isinstance(r_create, list) and len(r_create) > 0) else init_payload
else:
    project_data = res_p[0]

canvas = project_data.get("canvas", {})
val_score = project_data.get("validation_score", 0)
chat_history = project_data.get("chat_history", [])

def save_to_db(updated_fields):
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/firma_lean_projects?firma_id=eq.{active_firma_id}",
        headers=HEADERS,
        json=updated_fields
    )

with st.sidebar:
    st.caption(f"Aktivní engine: `{st.session_state.aktivni_model_nazev}`")
    st.markdown(f"""
    <div class="score-panel">
        <div class="score-lbl">Ověření byznys modelu</div>
        <div class="score-val">{val_score} %</div>
    </div>
    """, unsafe_allow_html=True)
    
    if val_score == 0:
        st.info("Představte svůj nápad mentorovi v záložce 2.")
    elif val_score < 40:
        st.warning("Fáze: Hledání Problem-Solution Fit. Ověřte problém u zákazníků.")
    elif val_score < 75:
        st.info("Fáze: Příprava MVP a pilotního testování.")
    else:
        st.success("Fáze: Validovaný model připravený k nasazení!")

# =========================================================================
# ZPRACOVÁNÍ LOKÁLNÍCH SOUBORŮ
# =========================================================================
def extract_text_from_docx(file_bytes_io):
    try:
        with zipfile.ZipFile(file_bytes_io) as docx:
            xml_content = docx.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            texts = [node.text for node in tree.iterfind('.//w:t', namespaces) if node.text]
            return "\n".join(texts)
    except Exception:
        return "[Chyba při čtení Word dokumentu]"

def prepare_local_file_payload(uploaded_file):
    if not uploaded_file:
        return None, ""
    
    fname = uploaded_file.name.lower()
    fbytes = uploaded_file.getvalue()
    
    if fname.endswith(".docx"):
        extracted = extract_text_from_docx(io.BytesIO(fbytes))
        return None, f"\n\n[OBSAH PŘILOŽENÉHO WORD DOKUMENTU ({uploaded_file.name})]:\n{extracted}\n"
    elif fname.endswith(".txt") or fname.endswith(".csv") or fname.endswith(".md"):
        try:
            text_content = fbytes.decode("utf-8")
        except Exception:
            text_content = fbytes.decode("latin-1", errors="ignore")
        return None, f"\n\n[OBSAH PŘILOŽENÉHO TEXTOVÉHO SOUBORU ({uploaded_file.name})]:\n{text_content}\n"
    elif fname.endswith(".pdf"):
        b64 = base64.b64encode(fbytes).decode("utf-8")
        return {"mime_type": "application/pdf", "data": b64}, f"\n[PŘILOŽENO PDF: {uploaded_file.name}]"
    elif fname.endswith(".png"):
        b64 = base64.b64encode(fbytes).decode("utf-8")
        return {"mime_type": "image/png", "data": b64}, f"\n[PŘILOŽEN OBRÁZEK: {uploaded_file.name}]"
    elif fname.endswith(".jpg") or fname.endswith(".jpeg"):
        b64 = base64.b64encode(fbytes).decode("utf-8")
        return {"mime_type": "image/jpeg", "data": b64}, f"\n[PŘILOŽEN OBRÁZEK: {uploaded_file.name}]"
    elif fname.endswith(".webp"):
        b64 = base64.b64encode(fbytes).decode("utf-8")
        return {"mime_type": "image/webp", "data": b64}, f"\n[PŘILOŽEN OBRÁZEK: {uploaded_file.name}]"
        
    return None, ""

# =========================================================================
# MULTIMODÁLNÍ VOLÁNÍ AI
# =========================================================================
def call_ai_multimodal(prompt_text, inline_attachment=None):
    key = API_KEY.strip()
    
    if key.startswith("gsk_"):
        st.session_state.aktivni_model_nazev = "Groq Llama-3"
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt_text}], "temperature": 0.3},
            timeout=35
        ).json()
        if "choices" in res:
            return res["choices"][0]["message"]["content"]
        raise Exception(f"Groq API chyba: {res}")

    elif key.startswith("sk-") and not key.startswith("sk-ant"):
        st.session_state.aktivni_model_nazev = "OpenAI GPT-4o"
        res = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt_text}], "temperature": 0.3},
            timeout=35
        ).json()
        if "choices" in res:
            return res["choices"][0]["message"]["content"]
        raise Exception(f"OpenAI API chyba: {res}")

    else:
        list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
        res_list = requests.get(list_url, timeout=15).json()
        
        dostupne_modely = []
        if "models" in res_list:
            dostupne_modely = [
                m["name"] for m in res_list["models"] 
                if "generateContent" in m.get("supportedGenerationMethods", [])
            ]
        
        if not dostupne_modely:
            dostupne_modely = ["models/gemini-1.5-flash", "models/gemini-2.0-flash", "models/gemini-1.5-pro"]

        dostupne_modely.sort(key=lambda x: 0 if "flash" in x.lower() else (1 if "pro" in x.lower() else 2))

        parts = [{"text": prompt_text}]
        if inline_attachment:
            parts.append({
                "inline_data": {
                    "mime_type": inline_attachment["mime_type"],
                    "data": inline_attachment["data"]
                }
            })

        posledni_err = None
        for m_name in dostupne_modely:
            clean_m = m_name.replace("models/", "")
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_m}:generateContent?key={key}"
            payload = {
                "contents": [{"parts": parts}],
                "generationConfig": {"temperature": 0.3}
            }
            try:
                r = requests.post(endpoint, json=payload, headers={"Content-Type": "application/json"}, timeout=40)
                res_json = r.json()
                
                if "candidates" in res_json and len(res_json["candidates"]) > 0:
                    st.session_state.aktivni_model_nazev = f"Gemini ({clean_m})"
                    return res_json["candidates"][0]["content"]["parts"][0]["text"]
                elif "error" in res_json:
                    posledni_err = res_json["error"].get("message", "Neznámá chyba")
            except Exception as e:
                posledni_err = str(e)
                continue

        raise Exception(f"Google API odmítlo požadavek. Hlášení: {posledni_err}")

# =========================================================================
# STRUKTURA ZÁLOŽEK
# =========================================================================
tab_canvas, tab_mentor, tab_zakaznik, tab_krize = st.tabs([
    "1. Lean Canvas", "2. Strategický mentor", "3. Zákaznický simulátor", "4. Generátor krizí"
])

# ==================== TAB 1: LEAN CANVAS ====================
with tab_canvas:
    st.markdown("Plánovací nástroj synchronizovaný s výstupy z rozhovoru v záložce **Strategický mentor**.")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"<div class='canvas-block'><div class='canvas-tag'>1. Problém</div>{canvas.get('problem', '')}</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<div class='canvas-block'><div class='canvas-tag'>8. Klíčové Metriky</div>{canvas.get('metriky', '')}</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='canvas-block'><div class='canvas-tag'>4. Řešení (MVP)</div>{canvas.get('reseni', '')}</div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='canvas-block'><div class='canvas-tag'>2. Unikátní Hodnota</div>{canvas.get('hodnota', '')}</div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='canvas-block'><div class='canvas-tag'>5. Nefér Výhoda</div>{canvas.get('nefer_vyhoda', '')}</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<div class='canvas-block'><div class='canvas-tag'>9. Prodejní Kanály</div>{canvas.get('kanaly', '')}</div>", unsafe_allow_html=True)
    with col5:
        st.markdown(f"<div class='canvas-block'><div class='canvas-tag'>3. Cílová Skupina</div>{canvas.get('cilovka', '')}</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col6, col7 = st.columns(2)
    with col6:
        st.markdown(f"<div class='canvas-block'><div class='canvas-tag'>6. Struktura Nákladů</div>{canvas.get('naklady', '')}</div>", unsafe_allow_html=True)
    with col7:
        st.markdown(f"<div class='canvas-block'><div class='canvas-tag'>7. Zdroje Příjmů</div>{canvas.get('prijmy', '')}</div>", unsafe_allow_html=True)

    if val_score >= 80 and not is_teacher:
        st.divider()
        st.success("Dosáhli jste potřebného ověření (80 %)! Váš byznys model je schválen mentorem.")
        st.markdown("Nyní můžete svůj validovaný model zapsat do hlavního profilu vaší firmy (Zakladatelského spisu).")
        
        if st.button("Zapsat schválený byznys plán do firemního rejstříku", type="primary"):
            # OPRAVA CHYBY: Bezpečné sčítání textu (odstraněna zpětná lomítka z konce řádků)
            spis_text = (
                f"**NAŠE ŘEŠENÍ (MVP):**\n{canvas.get('reseni', '')}\n\n"
                f"**ŘEŠÍME PROBLÉM:**\n{canvas.get('problem', '')}\n\n"
                f"**CÍLOVÁ SKUPINA:**\n{canvas.get('cilovka', '')}\n\n"
                f"**UNIKÁTNÍ HODNOTA:**\n{canvas.get('hodnota', '')}"
            )
            
            r_patch = requests.patch(
                f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{active_firma_id}",
                headers=HEADERS,
                json={"popis": spis_text}
            )
            
            if r_patch.status_code in [200, 204]:
                st.balloons()
                st.success("Úspěšně zapsáno! Váš byznys plán je nyní viditelný na profilu firmy v M-TECH CORE.")
            else:
                st.error(f"Něco se pokazilo při zápisu do databáze (Kód: {r_patch.status_code}).")

# ==================== TAB 2: MENTOR ====================
with tab_mentor:
    st.subheader("Konzultace s Lean Startup Mentorem")
    st.caption("Napište zprávu a stiskněte **Enter**. Volitelně můžete nahrát soubor jako podklad k analýze.")
    
    with st.expander("Připojit podklady (PDF, Word, obrázky, text)", expanded=False):
        uploaded_doc = st.file_uploader(
            "Nahrát soubor z počítače:",
            type=["png", "jpg", "jpeg", "webp", "pdf", "docx", "txt", "csv", "md"],
            key="mentor_file_uploader"
        )

    st.divider()

    for msg in chat_history:
        div_class = "chat-user" if msg["role"] == "user" else "chat-mentor"
        file_tag = f"<div class='file-badge'>Příloha: {msg['file']}</div><br>" if msg.get("file") else ""
        st.markdown(f"<div class='{div_class}'><b>{'Vy' if msg['role']=='user' else 'Strategický Mentor'}:</b><br>{file_tag}{msg['content']}</div>", unsafe_allow_html=True)
        
    def submit_mentor():
        if st.session_state.mentor_input.strip() and not is_teacher:
            user_input = st.session_state.mentor_input
            st.session_state.mentor_input = ""  # Automatické vymazání pole po odeslání Enterem
            
            file_payload = None
            extra_text_content = ""
            attached_name = None
            
            if uploaded_doc:
                file_payload, extra_text_content = prepare_local_file_payload(uploaded_doc)
                attached_name = uploaded_doc.name
            
            chat_history.append({
                "role": "user", 
                "content": user_input,
                "file": attached_name
            })
            
            full_user_prompt = user_input + extra_text_content
            
            prompt = f"""
            Jsi zkušený, konstruktivní a věcný Lean Startup mentor a akcelerátorový partner (metodika Eric Ries / Steve Blank / Y Combinator).
            Mluvíš česky. Nepoužívej žádné emotikony.

            TVŮJ PŘÍSTUP:
            1. Buď věcný, analytický, profesionální partner k diskusi.
            2. Pokud zakladatel přiložil dokument, detailně jej zanalyzuj a zohledni ve své odpovědi.
            3. Rozuměj fázím vývoje: Pokud je projekt ve fázi MVP/pilotu, zaměř se na ověření u Early Adopters a první reálné testy.
            4. Zhodnoť argumenty zakladatele, potvrď, co dává smysl, a polož 1-2 přesné diagnostické otázky k ověření rizik.

            Aktuální stav Lean Canvasu: {json.dumps(canvas, ensure_ascii=False)}
            Aktuální skóre validace (0-100): {val_score}
            Vstup od zakladatele: {full_user_prompt}

            POKYN: Odpověz VÝHRADNĚ ve validním JSON formátu bez jakýchkoliv markdown značek okolo.
            Struktura:
            {{
                "odpoved_mentora": "Strukturovaná, věcná zpětná vazba + 1-2 přesné otázky k ověření hypotézy.",
                "nove_skore": 50,
                "canvas_updaty": {{
                    "problem": "Stručný souhrn problému",
                    "reseni": "Stručný souhrn řešení / MVP",
                    "hodnota": "Unikátní hodnota (USP)",
                    "nefer_vyhoda": "Bariéra vstupu / nefér výhoda",
                    "cilovka": "Konkrétní Early Adopters",
                    "metriky": "Klíčové metriky úspěchu pilotu",
                    "kanaly": "Jak se dostat k nákupčímu",
                    "naklady": "Hlavní nákladové položky",
                    "prijmy": "Cenový model / monetizace"
                }}
            }}
            """
            
            with st.spinner("Mentor analyzuje zprávu a přiložené podklady..."):
                try:
                    raw_text = call_ai_multimodal(prompt, file_payload)
                    raw_text = re.sub(r'^```json\s*', '', raw_text)
                    raw_text = re.sub(r'\s*```$', '', raw_text)
                    
                    match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                    if match:
                        ai_data = json.loads(match.group(0))
                        chat_history.append({
                            "role": "mentor", 
                            "content": ai_data.get("odpoved_mentora", "Rozumím."),
                            "file": None
                        })
                        new_score = ai_data.get("nove_skore", val_score)
                        
                        new_canvas = ai_data.get("canvas_updaty", {})
                        for k in canvas.keys():
                            if k in new_canvas and new_canvas[k]: 
                                canvas[k] = new_canvas[k]

                        save_to_db({
                            "chat_history": chat_history,
                            "validation_score": new_score,
                            "canvas": canvas
                        })
                    else:
                        chat_history.append({"role": "mentor", "content": raw_text, "file": None})
                        save_to_db({"chat_history": chat_history})
                except Exception as e:
                    chat_history.append({"role": "mentor", "content": f"Chyba při zpracování: {str(e)}", "file": None})
                    save_to_db({"chat_history": chat_history})

    st.text_input("Napište zprávu mentorovi a stiskněte Enter (odeslání proběhne bez tlačítka)...", key="mentor_input", on_change=submit_mentor)

# ==================== TAB 3: ZÁKAZNÍK ====================
with tab_zakaznik:
    st.subheader("Customer Discovery (Rozhovory nanečisto)")
    st.write("Otestujte svou hodnotovou nabídku na konkrétní personě zákazníka.")
    
    with st.container(border=True):
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1: persona_vek = st.text_input("Věk zákazníka:", value="52")
        with col_c2: persona_role = st.text_input("Povolání / Pozice:", value="Ředitel / Učitel odborné školy")
        with col_c3: persona_zajem = st.text_input("Charakteristika / Priority:", value="Konzervativní, málo času na novinky, limitovaný rozpočet")
    
    st.divider()
    for msg in st.session_state.customer_history:
        div_class = "chat-user" if msg["role"] == "user" else "chat-mentor"
        st.markdown(f"<div class='{div_class}'><b>{'Vy' if msg['role']=='user' else 'Zákazník'}:</b><br>{msg['content']}</div>", unsafe_allow_html=True)
    
    def submit_customer():
        if st.session_state.customer_input.strip() and not is_teacher:
            cust_input = st.session_state.customer_input
            st.session_state.customer_input = "" # Automatické vymazání pole po odeslání Enterem
            
            st.session_state.customer_history.append({"role": "user", "content": cust_input})
            
            prompt_cust = f"""
            Hraješ roli reálného potenciálního zákazníka. Tvé parametry: Věk {persona_vek}, Pozice: {persona_role}, Vlastnosti: {persona_zajem}.
            Kontext projektu zakladatele: {json.dumps(canvas, ensure_ascii=False)}.
            Mluvíš česky. Reaguj autenticky a realisticky podle své role. Zajímej se o to, co ti to ušetří, kolik času tě to bude stát a jak složité je to zavést. Nepoužívej emotikony.

            Vstup od zakladatele: {cust_input}
            """
            with st.spinner("Zákazník formuluje odpověď..."):
                try:
                    res_cust = call_ai_multimodal(prompt_cust)
                    st.session_state.customer_history.append({"role": "customer", "content": res_cust})
                except Exception as e:
                    st.error(f"Chyba: {e}")

    st.text_input("Položte zákazníkovi otázku a stiskněte Enter (odeslání proběhne bez tlačítka)...", key="customer_input", on_change=submit_customer)

# ==================== TAB 4: KRIZE ====================
with tab_krize:
    st.subheader("Black Swan (Simulace tržních rizik)")
    st.write("Vygenerujte realistickou tržní komplikaci a otestujte schopnost týmu reagovat.")
    
    if st.button("Simulovat tržní komplikaci", type="primary") and not is_teacher:
        prompt_krize = f"""
        Kontext projektu: {json.dumps(canvas, ensure_ascii=False)}.
        Vymysli věcnou, vysoce realistickou tržní nebo provozní komplikaci (např. zpoždění dotačních titulů na školách, nezájem části sboru o novou metodiku, změna legislativy).
        Popiš situaci ve 2-3 větách a polož otázku na strategické řešení. Nepoužívej emotikony.
        """
        with st.spinner("Generuji krizový scénář..."):
            try:
                st.session_state.krize_aktivni = call_ai_multimodal(prompt_krize)
            except Exception as e:
                st.error(f"Chyba: {e}")
        
    if st.session_state.krize_aktivni:
        st.markdown(f"<div class='crisis-box'><b>SCÉNÁŘ K ŘEŠENÍ:</b><br><br>{st.session_state.krize_aktivni}</div><br>", unsafe_allow_html=True)
        
        def submit_crisis():
            if st.session_state.krize_input.strip() and not is_teacher:
                reseni = st.session_state.krize_input
                st.session_state.krize_input = "" # Automatické vymazání pole po odeslání Enterem
                
                prompt_reseni = f"""
                Krizová situace: {st.session_state.krize_aktivni}.
                Navržené řešení zakladatele: {reseni}.
                Zhodnoť věcně a realisticky, zda je toto řešení proveditelné a jaká nová rizika případně přináší. Ohodnoť 1-10 body. Nepoužívej emotikony.
                """
                with st.spinner("Vyhodnocuji řešení..."):
                    try:
                        st.info(call_ai_multimodal(prompt_reseni))
                    except Exception as e:
                        st.error(f"Chyba: {e}")

        st.text_input("Váš návrh řešení a mitigace rizika (Odešlete stisknutím klávesy Enter)...", key="krize_input", on_change=submit_crisis)
