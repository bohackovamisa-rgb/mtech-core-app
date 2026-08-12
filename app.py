import streamlit as st

# Profi vektorová ikona v záložce prohlížeče
st.set_page_config(page_title="M-TECH CORE", page_icon=":material/hub:", layout="wide")

# --- 1. BEZPEČNOSTNÍ ZÁMEK ---
if "prihlasen" not in st.session_state:
    st.session_state.prihlasen = False

if not st.session_state.prihlasen:
    st.title(":material/fingerprint: Systém uzamčen")
    st.info("Pro vstup do M-TECH CORE zadejte přihlašovací údaje.")
    
    jmeno = st.text_input("Přihlašovací jméno:")
    heslo = st.text_input("Heslo:", type="password")
    
    if st.button("Přihlásit"):
        if jmeno == "admin" and heslo == "core2026":
            st.session_state.prihlasen = True
            st.rerun() # Znovu načte stránku, tentokrát už jako přihlášený
        else:
            st.error("Špatné jméno nebo heslo!")
            
    st.stop() # Zastaví vykreslování čehokoliv dalšího

# --- 2. OBSAH ÚVODNÍ STRÁNKY (Zobrazí se až po přihlášení) ---
st.title(":material/hub: Vítejte v M-TECH CORE")
st.markdown("""
**Praktická ekonomie v technickém vzdělávání.**

Tento portál slouží k obsluze virtuálních financí (M-Kreditů), správě studentských firem a komunikaci s Kontrolním úřadem.

👈 **Pro vstup do systému si vyberte svou roli v levém bočním menu.**
""")
