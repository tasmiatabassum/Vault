import streamlit as st
import pandas as pd
import os
from backend.media_service import search_external_media
from backend.db_operations import (
    save_user_like, 
    get_user_likes,
    get_user_list_items, 
    add_to_list_workflow,
    submit_rating, 
    get_search_gallery,
    get_top_rated_genres, 
    get_user_activity_level, 
    get_format_popularity, 
    get_hidden_gems, 
    get_audit_stats,
    add_tag_to_media,
    get_similar_media
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
    
    st.markdown(f"""
        <h1 style='font-family: "Instrument Serif", serif; font-size: 64px; font-weight: 400; margin-bottom: 0;'>
            Hello, {user['name']}.
        </h1>
        <div class='rainbow-bar' style='width: 100%; height: 4px; margin: 10px 0 40px 0;'></div>
    """, unsafe_allow_html=True)

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
                    
                    save_key = f"saved_{item['external_id']}"
                    
                    # Determine List Type based on Media Type
                    list_map = {"movie": "watchlist", "book": "readlist", "music": "playlist"}
                    target_list = list_map.get(item['type'], "watchlist")
                    
                    if save_key in st.session_state:
                        # --- STATE B: Item Saved -> Show Rating UI ---
                        st.success("Saved to Favorites!")
                        
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
                        # --- STATE A: Not Saved -> Show Action Buttons ---
                        c1, c2 = st.columns([1, 1])
                        
                        with c1:
                            # Primary Action: Add to Favorites (The 'Like' workflow)
                            if st.button("♥ Favorites", key=f"fav_{item['external_id']}"):
                                try:
                                    # This now only adds to Favorites table
                                    internal_id = save_user_like(user['id'], item)
                                    st.session_state[save_key] = internal_id
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                        
                        with c2:
                            # Secondary Action: Add to specific List (Watchlist/Readlist/Playlist)
                            if st.button(f"+ {target_list.capitalize()}", key=f"list_{item['external_id']}"):
                                # Logic change: Pass item directly to workflow
                                # This avoids the 'save_user_like' side effect
                                res = add_to_list_workflow(user['id'], item, target_list)
                                if res is True:
                                    st.success(f"Added to {target_list}!")
                                else:
                                    # Displays the warning for duplicates or the error for type mismatch
                                    st.error(res)

    # --- TAB 2: MY VAULT ---
    with tab_vault:
        st.markdown("<h2 style='font-family: Instrument Serif;'>Your Collection</h2>", unsafe_allow_html=True)
        
        # Filter Selection
        view_mode = st.radio(
            "Filter", 
            ["Favorites", "Watchlist", "Readlist", "Playlist"], 
            horizontal=True,
            label_visibility="collapsed"
        )
        st.markdown("<br>", unsafe_allow_html=True)

        # Fetch Data based on Filter
        if view_mode == "Favorites":
            items = get_user_likes(user['id'])
        else:
            items = get_user_list_items(user['id'], view_mode.lower())
        
        if not items:
            st.info(f"Your {view_mode} is empty.")
        else:
            for item in items:
                m_type = item.get('type_name', 'Media')
                st.markdown(f"""
                    <div style='border-bottom: 1px solid #1a1a1a; padding: 20px 0; display: flex; align-items: center;'>
                        <span style='color: #f7b3d3; margin-right: 15px; font-size: 20px;'>•</span> 
                        <div>
                            <span style='font-family: "Inter"; font-weight: 500; font-size: 18px;'>{item['title']}</span><br>
                            <span style='color: #666; font-size: 12px; letter-spacing: 1px;'>{m_type.upper()} | {item.get('year', 'N/A')}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                # --- ACTIONS & DETAILS EXPANDER ---
                with st.expander(f"Actions & Details for {item['title']}"):
                    t_col1, t_col2 = st.columns([1, 1])
                    
                    # 1. Custom Tagging (Stored Procedure)
                    with t_col1:
                        st.caption("Add a custom tag:")
                        new_tag = st.text_input("Tag Name", label_visibility="collapsed", key=f"tag_in_{item['media_id']}", placeholder="e.g. Dystopian")
                        if st.button("Add Tag", key=f"tag_btn_{item['media_id']}"):
                            res = add_tag_to_media(user['id'], item['media_id'], new_tag)
                            if res is True:
                                st.success(f"Tagged as '{new_tag}'!")
                            else:
                                st.error("Error adding tag.")

                    # 2. Similarity Search (Self-Join Function)
                    with t_col2:
                        st.caption("More like this:")
                        if 'media_id' in item:
                            similar_items = get_similar_media(item['media_id'])
                            if similar_items:
                                for s in similar_items:
                                    st.markdown(f"**{s['title']}** <span style='color:#666'>({s['type_name']})</span>", unsafe_allow_html=True)
                            else:
                                st.write("No similar items found yet.")

    # --- TAB 3: ANALYTICS ---
    with tab_analytics:
        st.markdown("<h2 style='font-family: Instrument Serif;'>Vault Analytics</h2>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("★ Top Rated Genres")
            data = get_top_rated_genres()
            if data:
                st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True)
            else:
                st.caption("Not enough data.")

        with col2:
            st.subheader("📊 Format Popularity")
            data = get_format_popularity()
            if data:
                df_format = pd.DataFrame(data).set_index("Format")
                st.bar_chart(df_format)
            else:
                st.caption("No data.")

        st.markdown("<br>", unsafe_allow_html=True)
        col3, col4 = st.columns(2)
        with col3:
            st.subheader("👥 User Leaderboard")
            data = get_user_activity_level()
            if data:
                 st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True)

        with col4:
            st.subheader("💎 Hidden Gems")
            data = get_hidden_gems()
            if data:
                st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🗄️ Deep Archive (SQL View)")
        gallery_data = get_search_gallery()
        if gallery_data:
            st.dataframe(pd.DataFrame(gallery_data), hide_index=True, use_container_width=True)
            
        with st.expander("View System Audit Logs"):
            data = get_audit_stats()
            if data:
                st.table(pd.DataFrame(data))