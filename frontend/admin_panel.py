import streamlit as st
import pandas as pd
from backend.db_operations import (
    get_advanced_analytics,
    refresh_all_recommendations,
    get_audit_stats
)


def admin_panel():
    st.markdown("<h1 style='font-family: Instrument Serif;'>Admin Dashboard</h1>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Advanced Analytics", "System Control", "Audit Logs"])

    with tab1:
        st.subheader("Media Distribution Analysis")
        data = get_advanced_analytics('distribution')
        if data:
            st.dataframe(pd.DataFrame(data), use_container_width=True)

        st.subheader("Genre Hierarchy Stats")
        data = get_advanced_analytics('genre_hierarchy')
        if data:
            st.dataframe(pd.DataFrame(data), use_container_width=True)

    with tab2:
        st.subheader("System Maintenance")
        if st.button("🔄 Refresh All User Recommendations"):
            with st.spinner("Regenerating recommendations for all users..."):
                result = refresh_all_recommendations()
                if result is True:
                    st.success("Recommendations refreshed!")
                else:
                    st.error(f"Error: {result}")

    with tab3:
        st.subheader("System Audit Logs")
        logs = get_audit_stats()
        if logs:
            st.dataframe(pd.DataFrame(logs), use_container_width=True)