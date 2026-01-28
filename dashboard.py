import streamlit as st
import os
from backend.media_service import search_external_media
from backend.db_operations import save_user_like, get_user_likes

def dashboard():
    # --- SIDEBAR ---
    with st.sidebar:
        # Logo handling - fixing deprecated parameter from your screenshot
        logo_path = os.path.join("frontend", "assets", "logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, width=150)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        # Pill-shaped sidebar button
        if st.button("Log Out"):
            st.session_state.clear()
            st.rerun()

    # --- MAIN CONTENT ---
    user = st.session_state.user
    
    # Hero Greeting matching the "Vault." branding
    st.markdown(f"""
        <h1 style='font-family: "Instrument Serif", serif; font-size: 64px; font-weight: 400; margin-bottom: 0;'>
            Hello, {user['name']}.
        </h1>
        <div class='rainbow-bar' style='width: 100%; height: 4px; margin: 10px 0 40px 0;'></div>
    """, unsafe_allow_html=True)

    # Simplified Tabbed Navigation
    tab_search, tab_vault, tab_analytics = st.tabs(["SEARCH LIBRARY", "MY VAULT", "ANALYTICS"])

    # --- TAB 1: SEARCH & DISCOVER ---
    with tab_search:
        col1, col2 = st.columns([3, 1])
        with col1:
            query = st.text_input("DISCOVER", placeholder="e.g. Inception, 1984, After Hours", label_visibility="collapsed")
        with col2:
            # Updated to include 'music'
            m_type = st.selectbox("TYPE", ["movie", "book", "music"], label_visibility="collapsed")

        if query:
            results = search_external_media(query, m_type)
            st.markdown("<br>", unsafe_allow_html=True)
            
            if not results:
                st.warning("No results found in the external archives.")
            
            for item in results:
                # Media Card UI
                with st.container():
                    st.markdown(f"""
                        <div class='media-card'>
                            <p style='color: #888; font-size: 11px; margin-bottom: 4px; letter-spacing: 1px;'>{item['type'].upper()}</p>
                            <h3 style='font-family: "Instrument Serif"; margin: 0; font-size: 24px;'>{item['title']}</h3>
                            <p style='color: #555; font-size: 14px;'>{item['year']}</p>
                            <p style='color: #aaa; font-size: 13px; margin-top: 8px;'>{item['desc'][:150]}...</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Pill-shaped Like Button (inherits CSS from theme.css)
                    if st.button("Add to Vault", key=f"btn_{item['external_id']}"):
                        try:
                            save_user_like(user['id'], item)
                            st.toast(f"Saved {item['title']} to your vault.")
                        except Exception as e:
                            st.error(f"Vault error: {e}")

    # --- TAB 2: MY VAULT ---
    with tab_vault:
        st.markdown("<h2 style='font-family: Instrument Serif;'>Your Collection</h2>", unsafe_allow_html=True)
        likes = get_user_likes(user['id'])
        
        if not likes:
            st.info("Your personal vault is empty. Search to add items.")
        else:
            for item in likes:
                # Clean, minimal list entry
                st.markdown(f"""
                    <div style='border-bottom: 1px solid #1a1a1a; padding: 20px 0; display: flex; align-items: center;'>
                        <span style='color: #f7b3d3; margin-right: 15px;'>✦</span> 
                        <div>
                            <span style='font-family: "Inter"; font-weight: 500; font-size: 18px;'>{item['title']}</span><br>
                            <span style='color: #666; font-size: 12px; letter-spacing: 1px;'>{item['type_name'].upper()} &nbsp; | &nbsp; {item['release_year']}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    # --- TAB 3: ANALYTICS ---
    with tab_analytics:
        st.markdown("<h2 style='font-family: Instrument Serif;'>Insights</h2>", unsafe_allow_html=True)
        st.write("Coming soon: Data-driven recommendations for your specific taste profile.")
        # This aligns with Goal 03: Provides admin monitoring & analytics [cite: 45]
