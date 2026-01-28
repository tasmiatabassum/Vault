import streamlit as st
import os
from backend.media_service import search_external_media
from backend.db_operations import save_user_like, get_user_likes, submit_rating, get_search_gallery

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
            for item in results:
                with st.container():
                    # 1. Display Media Card (Title, Year, Genre)
                    st.markdown(f"""
                        <div class='media-card'>
                            <p style='color: #f7b3d3; font-size: 11px; margin-bottom: 2px;'>{item.get('genre', 'General').upper()}</p>
                            <h3 style='font-family: "Instrument Serif"; margin: 0;'>{item['title']}</h3>
                            <p style='color: #555; font-size: 14px;'>{item['year']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # 2. Dynamic UI: Check if we just saved this item
                    # We use the external_id as a unique key in session_state
                    save_key = f"saved_{item['external_id']}"
                    
                    if save_key in st.session_state:
                        # --- STATE B: Item is Saved -> Show Rating UI ---
                        st.success("Saved to Vault!")
                        
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            # Rating Dropdown
                            new_rating = st.selectbox("Rate this:", [1, 2, 3, 4, 5], key=f"rate_val_{item['external_id']}")
                        with col2:
                            # Submit Button
                            if st.button("Submit", key=f"rate_btn_{item['external_id']}"):
                                internal_id = st.session_state[save_key] # Get the DB ID we stored
                                res = submit_rating(user['id'], internal_id, new_rating)
                                if res is True:
                                    st.toast(f"Rated {new_rating} stars!")
                                else:
                                    st.error("Error saving rating.")
                    else:
                        # --- STATE A: Item not saved -> Show Add Button ---
                        if st.button("Add to Vault", key=f"add_{item['external_id']}"):
                            try:
                                # 1. Save to DB and get the new Internal ID
                                internal_id = save_user_like(user['id'], item)
                                
                                # 2. Store this ID in session state to "remember" it was saved
                                st.session_state[save_key] = internal_id
                                
                                # 3. Rerun to update UI (hides 'Add', shows 'Rate')
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
        st.subheader("Deep Archive (SQL View)")
        # Show your new View data in a table for the evaluators
        gallery_data = get_search_gallery()
        if gallery_data:
            import pandas as pd
            df = pd.DataFrame(gallery_data, columns=["ID", "Title", "Year", "Type", "Genres"])
            st.dataframe(df, use_container_width=True)
    


    
