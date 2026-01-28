# frontend/app.py
import sys
import os
import streamlit as st

# Fix import paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Page imports
from homepage import landing_page
from login import login_page
from dashboard import dashboard

# ---------------- PAGE ROUTING ---------------------

# If no page is set yet → go to landing page
if "page" not in st.session_state:
    st.session_state.page = "home"

# If user is logged in → always route to dashboard
if "user" in st.session_state:
    st.session_state.page = "dashboard"


# Router
if st.session_state.page == "home":
    landing_page()

elif st.session_state.page == "auth":
    login_page()

elif st.session_state.page == "dashboard":
    dashboard()

# ---------------------------------------------------

