import streamlit as st

def dashboard():
    user = st.session_state.user
    st.title(f"Welcome, {user['name']} 👋")

    st.write("Here are your recommendations:")
    # TODO: Show recommendations

    if st.button("Log Out"):
        st.session_state.clear()
        st.rerun()
