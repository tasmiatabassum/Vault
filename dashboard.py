import streamlit as st
from backend.media_service import search_external_media
from backend.db_operations import save_user_like, get_user_likes # This will now find the name

def dashboard():
    user = st.session_state.user
    st.title(f"Welcome, {user['name']} 👋")

    # --- TABBED NAVIGATION ---
    tab1, tab2, tab3 = st.tabs(["Search Library", "My Vault", "Analytics"])

    # --- TAB 1: SEARCH & DISCOVER ---
    with tab1:
        st.subheader("Discover New Media")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            query = st.text_input("Search for movies or books...", placeholder="e.g. Inception, 1984")
        with col2:
            m_type = st.selectbox("Media Type", ["movie", "book", "music"])

        if query:
            st.write(f"Searching for '{query}'...")
            results = search_external_media(query, m_type)
            
            if not results:
                st.warning("No results found.")
            
            for item in results:
                with st.container():
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.markdown(f"**{item['title']}** ({item['year']})")
                        st.caption(item['desc'][:150] + "...")
                    with c2:
                        # Logic to save to database
                        if st.button("Like", key=f"search_{item['external_id']}"):
                            try:
                                save_user_like(user['id'], item)
                                st.toast(f"Added {item['title']} to your vault!")
                            except Exception as e:
                                st.error(f"Error saving: {e}")

    # --- TAB 2: USER'S PERSONAL LIBRARY ---
    with tab2:
        st.subheader("Your Liked Media")
        liked_items = get_user_likes(user['id'])
        
        if not liked_items:
            st.info("Your vault is empty. Go to the Search tab to add some favorites!")
        else:
            for item in liked_items:
                # Displays items from the Media table
                with st.expander(f"{item['title']} ({item['release_year']})"):
                    st.write(f"**Description:** {item['description']}")
                    st.write(f"**Category:** {item['type_name']}")

    # --- TAB 3: ANALYTICS ---
    with tab3:
        st.subheader("Vault Insights")
        st.write("Coming soon: Personalized recommendations based on your taste.")
        # This is where Nashat's recommendation procedure output will go

    # --- SIDEBAR / LOGOUT ---
    st.sidebar.divider()
    if st.sidebar.button("Log Out"):
        st.session_state.clear()
        st.rerun()
