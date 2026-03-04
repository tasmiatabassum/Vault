import streamlit as st
import pandas as pd
import os
from backend.media_service import search_external_media
from backend.db_operations import (
    save_user_like,
    like_existing_media,
    get_user_likes,
    get_user_list_items,
    add_to_list_workflow,
    add_existing_to_list,
    submit_rating,
    get_search_gallery,
    get_top_rated_genres,
    get_user_activity_level,
    get_format_popularity,
    get_hidden_gems,
    get_audit_stats,
    add_tag_to_media,
    get_similar_media,
    get_user_recommendations,
    get_user_theme_weights,
    refresh_all_recommendations,
    get_advanced_analytics,
    get_db_stats,
    get_full_audit_log,
    generate_recommendations_for_user,
)


def dashboard():
    # --- SIDEBAR ---
    with st.sidebar:
        logo_path = os.path.join("frontend", "assets", "logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, width=150)

        st.markdown("<br><br>", unsafe_allow_html=True)

        user = st.session_state.user
        if user['role'] == 'admin':
            st.markdown("---")
            st.caption("ADMIN TOOLS")
            if st.button("🔧 Admin Panel", use_container_width=True):
                st.session_state.show_admin = True
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Log Out", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # --- MAIN CONTENT ---
    user = st.session_state.user

    # Show admin panel if flagged
    if st.session_state.get('show_admin', False) and user['role'] == 'admin':
        show_admin_panel()
        return

    st.markdown(f"""
        <h1 style='font-family: "Instrument Serif", serif; font-size: 64px; font-weight: 400; margin-bottom: 0;'>
            Hello, {user['name']}.
        </h1>
        <div class='rainbow-bar' style='width: 100%; height: 4px; margin: 10px 0 40px 0;'></div>
    """, unsafe_allow_html=True)

    tab_search, tab_vault, tab_recs = st.tabs([
        "SEARCH LIBRARY", "MY VAULT", "FOR YOU"
    ])

    # --- TAB 1: SEARCH & DISCOVER ---
    with tab_search:
        col1, col2 = st.columns([3, 1])
        with col1:
            query = st.text_input("DISCOVER", placeholder="e.g. Inception, 1984, After Hours",
                                  label_visibility="collapsed")
        with col2:
            m_type = st.selectbox("TYPE", ["movie", "book", "music"], label_visibility="collapsed")

        if query:
            results = search_external_media(query, m_type)
            for item in results:
                with st.container():
                    st.markdown(f"""
                        <div class='media-card'>
                            <p style='color: #f7b3d3; font-size: 11px; margin-bottom: 2px;'>{item.get('genre', 'General').upper()}</p>
                            <h3 style='font-family: "Instrument Serif"; margin: 0;'>{item['title']}</h3>
                            <p style='color: #555; font-size: 14px;'>{item['year']}</p>
                        </div>
                    """, unsafe_allow_html=True)

                    save_key = f"saved_{item['external_id']}"
                    list_map = {"movie": "watchlist", "book": "readlist", "music": "playlist"}
                    target_list = list_map.get(item['type'], "watchlist")

                    if save_key in st.session_state:
                        st.success("Saved to Favorites!")
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            new_rating = st.selectbox("Rate this:", [1, 2, 3, 4, 5],
                                                      key=f"rate_val_{item['external_id']}")
                        with col2:
                            if st.button("Submit", key=f"rate_btn_{item['external_id']}"):
                                internal_id = st.session_state[save_key]
                                res = submit_rating(user['id'], internal_id, new_rating)
                                if res is True:
                                    st.toast(f"Rated {new_rating} stars!")
                                else:
                                    st.error(f"Error: {res}")
                    else:
                        c1, c2 = st.columns([1, 1])
                        with c1:
                            if st.button("♥ Favorites", key=f"fav_{item['external_id']}"):
                                try:
                                    internal_id = save_user_like(user['id'], item)
                                    st.session_state[save_key] = internal_id
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                        with c2:
                            if st.button(f"+ {target_list.capitalize()}", key=f"list_{item['external_id']}"):
                                res = add_to_list_workflow(user['id'], item, target_list)
                                if res is True:
                                    st.success(f"Added to {target_list}!")
                                else:
                                    st.error(res)

    # --- TAB 2: MY VAULT ---
    with tab_vault:
        st.markdown("<h2 style='font-family: Instrument Serif;'>Your Collection</h2>", unsafe_allow_html=True)

        view_mode = st.radio(
            "Filter",
            ["Favorites", "Watchlist", "Readlist", "Playlist"],
            horizontal=True,
            label_visibility="collapsed"
        )
        st.markdown("<br>", unsafe_allow_html=True)

        if view_mode == "Favorites":
            items = get_user_likes(user['id'])
        else:
            items = get_user_list_items(user['id'], view_mode.lower())

        if not items:
            st.info(f"Your {view_mode} is empty.")
        else:
            for idx, item in enumerate(items):
                m_type = item.get('type_name', 'Media')
                unique_key = f"{view_mode}_{idx}_{item['media_id']}"

                st.markdown(f"""
                    <div style='border-bottom: 1px solid #1a1a1a; padding: 20px 0; display: flex; align-items: center;'>
                        <span style='color: #f7b3d3; margin-right: 15px; font-size: 20px;'>•</span>
                        <div>
                            <span style='font-family: "Inter"; font-weight: 500; font-size: 18px;'>{item['title']}</span><br>
                            <span style='color: #666; font-size: 12px; letter-spacing: 1px;'>{m_type.upper()} | {item.get('year', 'N/A')}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                with st.expander(f"Actions & Details for {item['title']}"):
                    t_col1, t_col2 = st.columns([1, 1])

                    with t_col1:
                        st.caption("Add a custom tag:")
                        new_tag = st.text_input(
                            "Tag Name",
                            label_visibility="collapsed",
                            key=f"tag_in_{unique_key}",
                            placeholder="e.g. Dystopian"
                        )
                        if st.button("Add Tag", key=f"tag_btn_{unique_key}"):
                            res = add_tag_to_media(user['id'], item['media_id'], new_tag)
                            if res is True:
                                st.success(f"Tagged as '{new_tag}'!")
                            else:
                                st.error("Error adding tag.")

                    with t_col2:
                        st.caption("More like this:")
                        if 'media_id' in item:
                            similar_items = get_similar_media(item['media_id'])
                            if similar_items:
                                for s in similar_items:
                                    st.markdown(f"**{s['title']}** <span style='color:#666'>({s['type_name']})</span>",
                                                unsafe_allow_html=True)
                            else:
                                st.write("No similar items found yet.")

    # --- TAB 3: FOR YOU (RECOMMENDATIONS) ---
    with tab_recs:
        st.markdown("<h2 style='font-family: Instrument Serif;'>Recommended For You</h2>", unsafe_allow_html=True)

        with st.expander("📊 Your Taste Profile"):
            themes = get_user_theme_weights(user['id'])
            if themes:
                col1, col2 = st.columns(2)
                with col1:
                    genres = [t for t in themes if t['category'] == 'Genre']
                    if genres:
                        st.caption("**Top Genres**")
                        for g in genres[:5]:
                            st.markdown(f"• **{g['theme']}** ({g['weight']} items)")
                with col2:
                    tags = [t for t in themes if t['category'] == 'Tag']
                    if tags:
                        st.caption("**Top Tags**")
                        for t in tags[:5]:
                            st.markdown(f"• **{t['theme']}** ({t['weight']} items)")
            else:
                st.info("Like some media to build your taste profile!")

        st.markdown("<br>", unsafe_allow_html=True)

        recs = get_user_recommendations(user['id'])

        if not recs:
            st.info("🎯 No recommendations yet. Like some media to get started!")
            if st.button("🔄 Generate Recommendations Now"):
                result = generate_recommendations_for_user(user['id'])
                if result is True:
                    st.success("Recommendations generated!")
                    st.rerun()
                else:
                    st.error(f"Error: {result}")
        else:
            st.caption(f"Found {len(recs)} recommendations based on your preferences")

            for rec in recs:
                st.markdown(f"""
                    <div class='media-card'>
                        <p style='color: #c6f7d4; font-size: 11px; margin-bottom: 2px;'>
                            MATCH SCORE: {rec['score']:.1f} | {rec['genres'].upper()}
                        </p>
                        <h3 style='font-family: "Instrument Serif"; margin: 0;'>{rec['title']}</h3>
                        <p style='color: #555; font-size: 14px;'>{rec['type_name']} • {rec['year']}</p>
                        <p style='color: #999; font-size: 13px;'>{rec['desc'][:150]}...</p>
                    </div>
                """, unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                with c1:
                    # Use like_existing_media — the item is already in the DB
                    if st.button("♥ Add to Favorites", key=f"fav_rec_{rec['media_id']}"):
                        result = like_existing_media(user['id'], rec['media_id'])
                        if result is True:
                            st.success("Added to Favorites!")
                            st.rerun()
                        else:
                            st.error(result)

                with c2:
                    list_map = {"movie": "watchlist", "book": "readlist", "music": "playlist"}
                    target_list = list_map.get(rec['type_name'], "watchlist")
                    if st.button(f"+ {target_list.capitalize()}", key=f"list_rec_{rec['media_id']}"):
                        res = add_existing_to_list(user['id'], rec['media_id'], target_list)
                        if res is True:
                            st.success(f"Added to {target_list}!")
                        else:
                            st.error(res)


def show_admin_panel():
    """Admin-only panel for system management."""
    st.markdown("<h1 style='font-family: Instrument Serif;'>Admin Dashboard</h1>", unsafe_allow_html=True)

    if st.button("← Back to Main Dashboard"):
        # Clear the flag so the dashboard renders correctly on return
        st.session_state.show_admin = False
        st.rerun()

    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "System Control", "Basic Analytics", "Advanced Analytics", "Audit Logs"
    ])

    # TAB 1: System Control
    with tab1:
        st.subheader("🔧 System Maintenance")

        col1, col2 = st.columns(2)

        with col1:
            st.caption("**Recommendation Engine**")
            if st.button("🔄 Refresh All User Recommendations", use_container_width=True):
                with st.spinner("Regenerating recommendations for all users..."):
                    result = refresh_all_recommendations()
                    if result is True:
                        st.success("✅ All recommendations refreshed successfully!")
                    else:
                        st.error(f"❌ Error: {result}")

        with col2:
            st.caption("**Database Statistics**")
            stats = get_db_stats()
            st.metric("Total Users", stats["users"])
            st.metric("Total Media", stats["media"])
            st.metric("Total Likes", stats["likes"])
            st.metric("Total Ratings", stats["ratings"])

    # TAB 2: Basic Analytics
    with tab2:
        st.subheader("📊 Basic Analytics")

        col1, col2 = st.columns(2)
        with col1:
            st.caption("★ Top Rated Genres")
            data = get_top_rated_genres()
            if data:
                st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True)
            else:
                st.caption("Not enough data.")

        with col2:
            st.caption("📊 Format Popularity")
            data = get_format_popularity()
            if data:
                df_format = pd.DataFrame(data).set_index("Format")
                st.bar_chart(df_format)
            else:
                st.caption("No data.")

        st.markdown("<br>", unsafe_allow_html=True)
        col3, col4 = st.columns(2)
        with col3:
            st.caption("👥 User Leaderboard")
            data = get_user_activity_level()
            if data:
                st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True)

        with col4:
            st.caption("💎 Hidden Gems")
            data = get_hidden_gems()
            if data:
                st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True)

    # TAB 3: Advanced Analytics
    with tab3:
        st.subheader("🔬 Advanced Analytics")

        adv_tab1, adv_tab2, adv_tab3 = st.tabs([
            "Media Distribution", "User Activity Cube", "Genre Hierarchy"
        ])

        with adv_tab1:
            st.caption("Multi-dimensional analysis using GROUPING SETS")
            data = get_advanced_analytics('distribution')
            if data:
                st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
            else:
                st.info("No data available yet.")

        with adv_tab2:
            st.caption("User activity analysis using CUBE")
            data = get_advanced_analytics('activity_cube')
            if data:
                st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
            else:
                st.info("No data available yet.")

        with adv_tab3:
            st.caption("Hierarchical genre statistics using ROLLUP")
            data = get_advanced_analytics('genre_hierarchy')
            if data:
                st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
            else:
                st.info("No data available yet.")

    # TAB 4: Audit Logs
    with tab4:
        st.subheader("📋 System Audit Logs")

        with st.expander("Media Search Gallery (SQL View)"):
            gallery_data = get_search_gallery()
            if gallery_data:
                st.dataframe(pd.DataFrame(gallery_data), hide_index=True, use_container_width=True)

        logs = get_full_audit_log()
        if logs:
            st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)
        else:
            st.info("No audit logs yet.")