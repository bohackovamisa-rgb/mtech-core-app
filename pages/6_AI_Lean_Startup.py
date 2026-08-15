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

is_teacher = st.session_state.get("role") == "ucitel"

# Přímé načtení firmy z app.py! (Tím se vyřeší Pepův odepřený přístup)
if is_teacher:
    st.markdown("### Kontrolní audit: Lean Startup projekty")
    skolni_kod = st.session_state.get("skolni_kod", "")
    res_f = requests.get(f"{SUPABASE_URL}/rest/v1/firmy?skolni_kod=eq.{skolni_kod}&select=id,nazev", headers=HEADERS).json()
    firm_opts = {f["nazev"]: f["id"] for f in res_f} if isinstance(res_f, list) else {}
    if not firm_opts:
        st.warning("Zatím nejsou evidovány žádné studentské firmy.")
        st.stop()
    selected_firm_name = st.selectbox("Vyberte firmu k auditu:", list(firm_opts.keys()))
    active_firma_id = firm_opts[selected_firm_name]
    active_firma_nazev = selected_firm_name
else:
    active_firma_id = st.session_state.get("firma_id")
    active_firma_nazev = st.session_state.get("firma_nazev")

    if not active_firma_id:
        st.info("Pro práci s modulem Lean Startup musíte být zakladatelem nebo členem firmy. Založte si nejprve firmu v záložce Firemní Dashboard.")
        st.stop()

    st.markdown(f"### Lean Startup Validator: {active_firma_nazev}")

# Načtení projektu dané firmy
res_p = requests.get(f"{SUPABASE_URL}/rest/v1/firma_lean_projects?firma_id=eq.{active_firma_id}", headers=HEADERS).json()

if not res_p or not isinstance(res_p, list) or len(res_p) == 0:
    init_payload = {
        "firma_id": int(active_firma_id),
        "skola_id": str(st.session_state.get("skolni_kod", "")),
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
chat_history = project_data.get("chat_history", [])

def call_lean_ai(prompt_text):
    key = API_KEY.strip()
    r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}", json={"contents": [{"parts": [{"text": prompt_text}]}]}).json()
    return r["candidates"][0]["content"]["parts"][0]["text"]

st.sidebar.metric("Validation Score", f"{val_score} %")

tab_canvas, tab_mentor = st.tabs(["🧩 Lean Canvas", "🎓 Strategický mentor"])

with tab_canvas:
    st.write(canvas)

with tab_mentor:
    for m in chat_history:
        role_zobr = "Vy" if m["role"] == "user" else "Mentor"
        st.markdown(f"**{role_zobr}:** {m['content']}")

    if not is_teacher:
        u_msg = st.chat_input("Napište mentorovi...")
        if u_msg:
            chat_history.append({"role": "user", "content": u_msg})
            prompt = f"Jsi Lean mentor. Zhodnoť: {u_msg}. Canvas: {json.dumps(canvas)}. Vrať JSON s klíči: 'odpoved', 'nove_skore', 'canvas_updaty'."
            raw = call_lean_ai(prompt)
            raw = re.sub(r'^```json\s*', '', raw).replace('```', '').strip()
            ai_data = json.loads(re.search(r'\{.*\}', raw, re.DOTALL).group(0))
            
            chat_history.append({"role": "mentor", "content": ai_data["odpoved"]})
            canvas.update({k: v for k, v in ai_data.get("canvas_updaty", {}).items() if v})
            
            requests.patch(f"{SUPABASE_URL}/rest/v1/firma_lean_projects?firma_id=eq.{active_firma_id}", headers=HEADERS, json={
                "chat_history": chat_history, "validation_score": ai_data.get("nove_skore", val_score), "canvas": canvas
            })
            st.rerun()
