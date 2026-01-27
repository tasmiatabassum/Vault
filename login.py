import streamlit as st
from backend.auth import get_user_by_email, create_user

def login_page():
    st.title("Vault Authentication")

    mode = st.radio(
        "Select an option:",
        ["Login", "Sign Up"],
        horizontal=True,
        key="auth_mode"
    )

    # ---------------- LOGIN -----------------
    if mode == "Login":
        st.subheader("Log In")

        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Log In", key="login_button"):
            user = get_user_by_email(email)

            if user and user[3] == password:
                st.success("Login successful!")

                # store user in session
                st.session_state.user = {
                    "id": user[0],
                    "name": user[1],
                    "email": user[2],
                    "role": user[4]
                }
            else:
                st.error("Invalid email or password.")


    # ---------------- SIGN UP -----------------
    else:
        st.subheader("Create New Account")

        name = st.text_input("Full Name", key="signup_name")
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")

        if st.button("Sign Up", key="signup_button"):
            existing = get_user_by_email(email)

            if existing:
                st.error("An account with this email already exists.")
            else:
                uid = create_user(name, email, password)
                st.success(f"Account created successfully! Welcome, {name}.")
                st.info("You can now switch to Login and sign in.")

            
    if st.button("Back to Home"):
        st.session_state.page = "home"
        st.rerun()
