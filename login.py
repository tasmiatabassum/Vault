import streamlit as st
from backend.auth import get_user_by_email, create_user

def login_page():
    # Load custom CSS
    with open("frontend/theme.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    # --- HEADER SECTION ---
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
        <div style='text-align:center;'>
            <h1 style='font-family: "Instrument Serif", serif; font-size: 80px; font-weight: 400; margin-bottom: 0;'>
                Vault.
            </h1>
            <div class='rainbow-bar' style='width: 300px; margin: 20px auto;'></div>
        </div>
    """, unsafe_allow_html=True)

    # --- AUTHENTICATION FORM ---
    # Center the form using columns
    _, col, _ = st.columns([1, 1.5, 1])

    with col:
        mode = st.radio(
            "SELECT ACCESS MODE",
            ["Login", "Sign Up"],
            horizontal=True,
            label_visibility="collapsed" # Keep it clean
        )
        
        st.markdown("<br>", unsafe_allow_html=True)

        if mode == "Login":
            email = st.text_input("EMAIL ADDRESS", placeholder="name@email.com")
            password = st.text_input("PASSWORD", type="password", placeholder="••••••••")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Enter Vault"):
                user = get_user_by_email(email)
                if user and user[3] == password:
                    st.session_state.user = {
                        "id": user[0],
                        "name": user[1],
                        "email": user[2],
                        "role": user[4]
                    }
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

        else:
            name = st.text_input("FULL NAME", placeholder="John Doe")
            email = st.text_input("EMAIL ADDRESS")
            password = st.text_input("SET PASSWORD", type="password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Create Account"):
                create_user(name, email, password)
                st.success("Account created! You may now login.")

        # --- NAVIGATION ---
        st.markdown("<div style='text-align:center; margin-top: 20px;'>", unsafe_allow_html=True)
        if st.button("← Back"):
            st.session_state.page = "home"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
