import streamlit as st

def landing_page():
    # Center everything
    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)



    # --- TITLE ---
    st.markdown("""
        <h1 style='font-family: Instrument Serif;'>
            VAULT
        </h1>
        <p style='font-size: 18px;'>
            Your Personalized Media Recommendation System
        </p>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # --- BUTTON ---
    if st.button("Get Started"):
        st.session_state.page = "auth"
        st.rerun()
