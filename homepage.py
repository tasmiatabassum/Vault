import streamlit as st

def landing_page():
    # Load custom CSS
    with open("frontend/theme.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    # Main Container for centering
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    # --- TITLE ---
    st.markdown("""
        <div style='text-align:center;'>
            <h1 style='font-family: "Instrument Serif", serif; font-size: 120px; font-weight: 400; margin-bottom: 0;'>
                Vault.
            </h1>
        </div>
    """, unsafe_allow_html=True)

    # --- RAINBOW BAR ---
    st.markdown("<div class='rainbow-bar'></div>", unsafe_allow_html=True)

    # --- SUBTITLE ---
    st.markdown("""
        <div style='text-align:center;'>
            <p style='font-family: "Inter", sans-serif; font-size: 16px; font-weight: 600; letter-spacing: 0px; color: #dddddd;'>
                Your Personalized Media Recommendation System
            </p>
        </div>
        <br>
    """, unsafe_allow_html=True)

    # --- CENTERED BUTTON ---
    col1, col2, col3 = st.columns([1, 0.8, 1])
    with col2:
        if st.button("Get Started"):
            st.session_state.page = "auth"
            st.rerun()
