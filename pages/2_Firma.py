# ==========================================
# 7. BURZA, AI RATING A INVESTICE
# ==========================================
with tab_burza:
    if not moje_firma:
        st.warning("Nejprve založte firmu.")
    else:
        st.markdown("#### 📰 Wall Street (M-TECH Financial News)")
        zpravy = requests.get(f"{SUPABASE_URL}/rest/v1/burza_zpravy?order=datum.desc&limit=3", headers=headers).json()
        if zpravy:
            for z in zpravy:
                st.markdown(f"<div class='card-box' style='border-left: 4px solid #f59e0b;'><b>{z['titulek']}</b><br><span style='color:#cbd5e1; font-size:14px;'>{z['text_zpravy']}</span></div>", unsafe_allow_html=True)
        else:
            st.info("Trh je zatím klidný, žádné nové zprávy.")
            
        st.write("---")
        
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.markdown("#### Emise nových akcií (IPO) & AI Valuace")
            st.caption("Před vstupem na burzu vás musí ohodnotit AI Ratingová agentura.")
            
            rating = moje_firma.get('ai_rating', 'Nehodnoceno')
            max_cena = float(moje_firma.get('ai_hodnota_akcie', 0))
            
            st.markdown(f"<div style='background:rgba(0,180,216,0.1); padding:15px; border-radius:8px; margin-bottom:15px;'>Aktuální AI Rating: <b>{rating}</b><br>Max. povolená cena akcie: <b>{max_cena} M-K</b></div>", unsafe_allow_html=True)
            
            gemini_key = st.secrets.get("GEMINI_API_KEY", "")
            if st.button("Požádat o novou AI Valuaci", key="btn_valuace"):
                with st.spinner("AI Agentura analyzuje vaši firmu..."):
                    if gemini_key:
                        try:
                            z_ucet = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{moje_firma['ceo_jmeno']}", headers=headers).json()[0]['kredity']
                            g_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
                            prompt = f"""Ohodnoť firmu {moje_firma['nazev_firmy']}. Na účtu má {z_ucet} M-K. Má {moje_firma['pocatecni_kapital']} startovní kapitál.
                            Vrať JSON se dvěma klíči: "rating" (např. AAA, AA, A, BBB, BB, B, C podle stavu peněz, nad 500 je AAA, pod 100 je C) a "cena" (doporučená cena jedné akcie od 1 do 100 MK)."""
                            
                            res_ai = requests.post(g_url, json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"response_mime_type": "application/json"}}, timeout=10).json()
                            data_ai = json.loads(res_ai['candidates'][0]['content']['parts'][0]['text'])
                            
                            n_rating = data_ai.get("rating", "BB")
                            n_cena = float(data_ai.get("cena", 15.0))
                            
                            requests.patch(f"{SUPABASE_URL}/rest/v1/firmy?id=eq.{moje_firma['id']}", headers=headers, json={"ai_rating": n_rating, "ai_hodnota_akcie": n_cena})
                            st.rerun()
                        except Exception:
                            st.error("AI Valuace selhala, zkuste to znovu.")
            
            if rating != 'Nehodnoceno':
                with st.form("form_ipo"):
                    pocet_akcii = st.number_input("Počet akcií k prodeji:", min_value=1, value=50)
                    cena_akcie = st.number_input(f"Cena za 1 akcii (Max {max_cena} M-K):", min_value=1.0, max_value=float(max_cena), value=float(max_cena))
                    if st.form_submit_button("Zveřejnit nabídku na burze"):
                        requests.post(f"{SUPABASE_URL}/rest/v1/burza_nabidky", headers=headers, json={"firma_id": moje_firma["id"], "pocet_k_prodeji": pocet_akcii, "cena_za_kus": cena_akcie, "aktivni": True})
                        st.success("Akcie jsou na burze!")
                        st.rerun()
        with col_b2:
            st.markdown("#### Výplata dividend")
            portfolio = requests.get(f"{SUPABASE_URL}/rest/v1/portfolio_investoru?firma_id=eq.{moje_firma['id']}", headers=headers).json()
            celkem_akcii = sum(p['pocet_akcii'] for p in portfolio) if portfolio else 0
            st.info(f"Celkem externích akcií v oběhu: {celkem_akcii} ks.")
            with st.form("form_dividendy"):
                castka_rozdelit = st.number_input("Celková částka k rozdělení mezi akcionáře (M-K):", min_value=1.0, value=100.0)
                if st.form_submit_button("Vyplatit akcionářům"):
                    if not portfolio or celkem_akcii == 0: st.error("Nemáte žádné externí akcionáře.")
                    else:
                        div_na_akcii = castka_rozdelit / celkem_akcii
                        ceo = moje_firma['ceo_jmeno']
                        res_ceo = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{ceo}", headers=headers).json()
                        if res_ceo and castka_rozdelit <= res_ceo[0]['kredity']:
                            requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{ceo}", headers=headers, json={"kredity": res_ceo[0]['kredity'] - castka_rozdelit})
                            for p in portfolio:
                                zisk = p['pocet_akcii'] * div_na_akcii
                                r_inv = requests.get(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{p['investor_jmeno']}", headers=headers).json()
                                if r_inv: requests.patch(f"{SUPABASE_URL}/rest/v1/uzivatele?jmeno=eq.{p['investor_jmeno']}", headers=headers, json={"kredity": r_inv[0]['kredity'] + zisk})
                            requests.post(f"{SUPABASE_URL}/rest/v1/kniha_prijmu_vydaju", headers=headers, json={"firma_id": moje_firma["id"], "typ_transakce": "VYDAJ", "titul": "Výplata dividend", "castka": castka_rozdelit, "auditovano": True})
                            st.rerun()
                        else: st.error("Nedostatek prostředků na vyplacení dividend.")
