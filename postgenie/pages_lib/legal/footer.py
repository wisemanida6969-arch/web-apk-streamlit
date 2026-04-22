"""Shared footer with legal links for PostGenie."""
import streamlit as st


def render_footer():
    """Render shared footer with legal links."""
    st.markdown("""
    <div style="text-align:center; padding:30px 20px 20px; margin-top:50px;
                border-top:1px solid rgba(255,255,255,0.05);">
        <a href="?page=terms" style="color:#64748b; font-size:0.82rem; text-decoration:none; margin:0 10px;">Terms of Service</a>
        <span style="color:#334155;">|</span>
        <a href="?page=privacy" style="color:#64748b; font-size:0.82rem; text-decoration:none; margin:0 10px;">Privacy Policy</a>
        <span style="color:#334155;">|</span>
        <a href="?page=cookies" style="color:#64748b; font-size:0.82rem; text-decoration:none; margin:0 10px;">Cookie Policy</a>
        <span style="color:#334155;">|</span>
        <a href="?page=refund" style="color:#64748b; font-size:0.82rem; text-decoration:none; margin:0 10px;">Refund Policy</a>
        <div style="color:#475569; font-size:0.75rem; margin-top:12px;">&copy; 2026 PostGenie. AI-Powered Blog Automation.</div>
    </div>
    """, unsafe_allow_html=True)
