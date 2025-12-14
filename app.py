import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
from backend.db_connect import get_connection

st.title("Vault")

try:
    conn = get_connection()
    st.success("Connected to PostgreSQL!")
except Exception as e:
    st.error(f"Connection failed: {e}")
