import streamlit as st
import os
from backend.media_service import search_external_media
from backend.db_operations import (
    save_user_like, 
    get_user_likes, 
    submit_rating, 
    get_search_gallery
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
        <h1 style='font-family: "Instrument Serif"; font-size: 64px; font-weight: 400; margin-bottom: 0;'>
            Hello, {user['name']}.
        </h1>
        <div class='rainbow-bar' style='width: 100%; height: 4px; margin: 10px 0 40px 0;'></div>
    """, unsafe_allow_html=True)

    tab_search, tab_vault, tab_analytics = st.tabs(["DISCOVER", "MY VAULT", "ANALYTICS"])

    # --- TAB 1: SEARCH & DISCOVER ---
    with tab_search:
        
        # 1. GENRE PILLS 
        st.markdown("### 🏷️ Browse by Genre")
        genres = ["Action", "Sci-Fi", "Comedy", "Drama", "Horror", "Fantasy", "Romance"]
        
        selected_genre = st.pills(
            "Select a Genre", 
            genres, 
            selection_mode="single", 
            label_visibility="collapsed"
        )

        if selected_genre:
            st.markdown(f"## Top {selected_genre} Discoveries")
            col_m, col_b = st.columns(2)

            with col_m:
                st.markdown(f"#### 🎬 {selected_genre.upper()} MOVIES")
                m_results = search_external_media(selected_genre, "movie", is_genre_search=True)
                if m_results:
                    for item in m_results:
                        render_media_card(item, user, "gen_m")
                else:
                    st.caption("No movies found.")

            with col_b:
                st.markdown(f"#### 📚 {selected_genre.upper()} BOOKS")
                b_results = search_external_media(selected_genre, "book", is_genre_search=True)
                if b_results:
                    for item in b_results:
                        render_media_card(item, user, "gen_b")
                else:
                    st.caption("No books found.")

        st.markdown("<br><hr><br>", unsafe_allow_html=True)

        # 2. GLOBAL DISCOVERY 
        st.markdown("### 🌍 Global Search")
        col1, col2 = st.columns([3, 1])
        with col1:
            query = st.text_input("SEARCH", placeholder="Search by title...", label_visibility="collapsed", key="g_search")
        with col2:
            m_type = st.selectbox("TYPE", ["movie", "book", "music"], label_visibility="collapsed", key="g_type")

        if query:
            results = search_external_media(query, m_type, is_genre_search=False)
            for item in results:
                render_media_card(item, user, "global")

    # --- TAB 2: MY VAULT ---
    with tab_vault:
        st.markdown("<h2 style='font-family: Instrument Serif;'>Your Collection</h2>", unsafe_allow_html=True)
        likes = get_user_likes(user['id'])
        if not likes:
            st.info("Your vault is empty.")
        else:
            for item in likes:
                st.markdown(f"""
                    <div style='border-bottom: 1px solid #1a1a1a; padding: 15px 0;'>
                        <span style='font-weight: 500; font-size: 18px;'>{item['title']}</span><br>
                        <span style='color: #666; font-size: 12px;'>{item['type_name'].upper()} • {item['release_year']}</span>
                    </div>
                """, unsafe_allow_html=True)

    # --- TAB 3: ANALYTICS ---
    with tab_analytics:
        st.subheader("Data Archive")
        gallery = get_search_gallery()
        if gallery:
            import pandas as pd
            st.dataframe(pd.DataFrame(gallery), use_container_width=True)

def render_media_card(item, user, key_prefix):
    """Renders a card with fix for potential non-string genres"""
    # Defensive fix: Convert genre to string and default to empty if None
    genre_display = str(item.get('genre', '')).upper()
    
    with st.container():
        st.markdown(f"""
            <div style='background: #111; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #f7b3d3;'>
                <p style='color: #f7b3d3; font-size: 10px; margin: 0;'>{genre_display}</p>
                <h4 style='margin: 5px 0; font-family: "Instrument Serif";'>{item['title']}</h4>
                <p style='color: #666; font-size: 12px; margin: 0;'>{item['year']}</p>
            </div>
        """, unsafe_allow_html=True)
        
        save_key = f"saved_{item['external_id']}"
        if save_key in st.session_state:
            st.caption("✅ Added")
        else:
            if st.button("Add to Vault", key=f"{key_prefix}_{item['external_id']}"):
                st.session_state[save_key] = save_user_like(user['id'], item)
                st.rerun()