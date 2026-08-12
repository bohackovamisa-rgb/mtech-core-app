import streamlit as st
import pandas as pd

st.set_page_config(page_title="M-TECH CORE", page_icon="🪙", layout="wide")

# --- BOČNÍ PANEL: PŘIHLÁŠENÍ ROLÍ ---
st.sidebar.title("🔐 Přihlášení do systému")
role = st.sidebar.radio("Vyberte svou roli:", ["Běžný žák (Zákazník)", "Management firmy (CFO)", "Učitel (Kontrolní úřad)"])

# --- ZOBRAZENÍ PODLE ROLE ---

if role == "Běžný žák (Zákazník)":
    st.title("🪙 Moje peněženka")
    st.info("Při prvním přihlášení ti aplikace automaticky vložila startovní balíček M-Kreditů.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Zůstatek", "100 M-Kreditů")
    with col2:
        st.metric("Osobní skóre", "Začátečník")
        
    st.divider()
    st.subheader("📷 Naskenovat QR voucher nebo zaplatit")
    kod = st.text_input("Zadej kód stánku nebo voucheru od učitele:")
    if st.button("Odeslat / Přijmout"):
        st.success("Transakce proběhla úspěšně!")

elif role == "Management firmy (CFO)":
    st.title("🏢 Firemní palubní deska")
    st.caption("Správa financí, úroveň projektu a odvod M-TECH daně")
    
    # Simulace načtení dat firmy
    st.write("**Firma:** Precision Mech a.s.")
    st.write("**Aktivní úroveň:** Úroveň 2 (Uzavřený školní trh v M-Kreditech)")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Firemní kapitál", "450 M-Kreditů")
    col2.metric("Očekávaná M-TECH Daň (15%)", "67 M-Kreditů")
    col3.metric("Status licence", "✅ Schváleno Úřadem")
    
    st.divider()
    st.subheader("📊 Kniha příjmů a výdajů")
    df = pd.DataFrame({
        "Datum": ["12.10.2026", "14.10.2026"],
        "Položka": ["Prodej - Těžítko", "Nákup materiálu"],
        "Částka (M)": ["+150", "-45"]
    })
    st.dataframe(df, use_container_width=True, hide_index=True)

elif role == "Učitel (Kontrolní úřad)":
    st.title("🏛️ Kontrolní úřad M-TECH CORE")
    st.caption("Garant projektu - správa licencí a audity")
    
    st.subheader("📝 Žádosti o licenci (Čekající na schválení)")
    licence_df = pd.DataFrame({
        "Název firmy": ["RoboTech s.r.o.", "Cyber Logic"],
        "Požadovaná Úroveň": ["Úroveň 2", "Úroveň 3"],
        "CEO": ["Jan Novák", "Petr Svoboda"],
        "Akce": ["Čeká na audit", "Čeká na audit"]
    })
    st.dataframe(licence_df, use_container_width=True, hide_index=True)
    
    st.divider()
    st.subheader("🎁 Generátor M-Kreditů (Bonusy pro žáky)")
    pocet_kreditu = st.number_input("Hodnota voucheru (M-Kredity):", min_value=1, value=50)
    if st.button("Vytvořit QR Voucher"):
        st.success(f"Voucher na {pocet_kreditu} M-Kreditů byl úspěšně vygenerován!")
