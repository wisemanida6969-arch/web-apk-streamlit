"""Refund Policy for PostGenie (access.trytimeback.com)."""
import streamlit as st


def render_refund():
    st.markdown("# Refund Policy")
    st.caption("Last updated: April 22, 2026")
    st.divider()

    st.markdown("""
**This service is operated by Trytimeback.**

We offer a 14-day refund policy in accordance with Paddle's terms of service.

Customers may request a full refund within 14 days of purchase by contacting us at admin@trytimeback.com.

Refund requests after 14 days will be reviewed on a case-by-case basis.
    """)
