import streamlit as st
import pandas as pd
import os
from backend.media_service import search_external_media
from backend.db_operations import (
    save_user_like, 
    get_user_likes, 
    submit_rating, 
    get_search_gallery,
    get_top_rated_genres, 
    get_user_activity_level, 
    get_format_popularity, 
    get_hidden_gems, 
    get_audit_stats
)

def dashboard():
    # --- SIDEBAR ---
    with st.sidebar:
        logo_path = os.path.join("frontend", "assets", "logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, width=150)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("Log Out"):
            st.session_state.clear()
            st.rerun()

    # --- MAIN CONTENT ---
    user = st.session_state.user
    
    # Hero Greeting
    st.markdown(f"""
        <h1 style='font-family: "Instrument Serif", serif; font-size: 64px; font-weight: 400; margin-bottom: 0;'>
            Hello, {user['name']}.
        </h1>
        <div class='rainbow-bar' style='width: 100%; height: 4px; margin: 10px 0 40px 0;'></div>
    """, unsafe_allow_html=True)

    # Tabs
    tab_search, tab_vault, tab_analytics = st.tabs(["SEARCH LIBRARY", "MY VAULT", "ANALYTICS"])

    # --- TAB 1: SEARCH & DISCOVER ---
    with tab_search:
        col1, col2 = st.columns([3, 1])
        with col1:
            query = st.text_input("DISCOVER", placeholder="e.g. Inception, 1984, After Hours", label_visibility="collapsed")
        with col2:
            m_type = st.selectbox("TYPE", ["movie", "book", "music"], label_visibility="collapsed")

        if query:
            results = search_external_media(query, m_type)
            for item in results:
                with st.container():
                    # Media Card
                    st.markdown(f"""
                        <div class='media-card'>
                            <p style='color: #f7b3d3; font-size: 11px; margin-bottom: 2px;'>{item.get('genre', 'General').upper()}</p>
                            <h3 style='font-family: "Instrument Serif"; margin: 0;'>{item['title']}</h3>
                            <p style='color: #555; font-size: 14px;'>{item['year']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Logic: Check if we just saved this item using session_state
                    save_key = f"saved_{item['external_id']}"
                    
                    if save_key in st.session_state:
                        # STATE B: Item Saved -> Show Rating UI
                        st.success("Saved to Vault!")
                        
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            new_rating = st.selectbox("Rate this:", [1, 2, 3, 4, 5], key=f"rate_val_{item['external_id']}")
                        with col2:
                            if st.button("Submit", key=f"rate_btn_{item['external_id']}"):
                                internal_id = st.session_state[save_key]
                                res = submit_rating(user['id'], internal_id, new_rating)
                                if res is True:
                                    st.toast(f"Rated {new_rating} stars!")
                                else:
                                    st.error(f"Error: {res}")
                    else:
                        # STATE A: Not Saved -> Show Add Button
                        if st.button("Add to Vault", key=f"add_{item['external_id']}"):
                            try:
                                internal_id = save_user_like(user['id'], item)
                                # Store ID in session state to flip the UI to 'Rate' mode
                                st.session_state[save_key] = internal_id
                                st.rerun()
                            except Exception as e:
                                st.error(f"Could not save: {e}")

    # --- TAB 2: MY VAULT ---
    with tab_vault:
        st.markdown("<h2 style='font-family: Instrument Serif;'>Your Collection</h2>", unsafe_allow_html=True)
        likes = get_user_likes(user['id'])
        
        if not likes:
            st.info("Your personal vault is empty. Search to add items.")
        else:
            for item in likes:
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
        st.markdown("<h2 style='font-family: Instrument Serif;'>Vault Analytics</h2>", unsafe_allow_html=True)
        
        # Row 1: Top Genres & Format Popularity
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("★ Top Rated Genres")
            data = get_top_rated_genres()
            if data:
                st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True)
            else:
                st.caption("Not enough rating data yet.")

        with col2:
            st.subheader("📊 Format Popularity")
            data = get_format_popularity()
            if data:
                # Simple Bar Chart for counts
                df_format = pd.DataFrame(data).set_index("Format")
                st.bar_chart(df_format)
            else:
                st.caption("No likes recorded yet.")

        # Row 2: User Activity & Hidden Gems
        st.markdown("<br>", unsafe_allow_html=True)
        col3, col4 = st.columns(2)
        with col3:
            st.subheader("👥 User Leaderboard")
            st.caption("Categorized via SQL CASE Statements")
            data = get_user_activity_level()
            if data:
                 st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True)

        with col4:
            st.subheader("💎 Hidden Gems")
            st.caption("High rated (Avg > 4.0)")
            data = get_hidden_gems()
            if data:
                st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True)

        # Row 3: Deep Archive (Existing View)
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🗄️ Deep Archive (SQL View)")
        gallery_data = get_search_gallery()
        if gallery_data:
            st.dataframe(pd.DataFrame(gallery_data), hide_index=True, use_container_width=True)
            
        # Row 4: System Health (Audit Log)
        with st.expander("View System Audit Logs"):
            st.caption("Live feed of database triggers")
            data = get_audit_stats()
            if data:
                st.table(pd.DataFrame(data))
