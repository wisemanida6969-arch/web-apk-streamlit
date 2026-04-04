import os
os.environ['TZ'] = 'UTC'

# ── SHIELD: Purge proxy env vars immediately ──
for env_key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
    if env_key in os.environ:
        del os.environ[env_key]

import streamlit as st
import re
import random
import json

# ─────────────────────────────────────────────
#  Platinum UI Styling (v4.4 Legal Shield)
# ─────────────────────────────────────────────
def apply_platinum_design():
    """Injects high-end CSS for Hero, Value Prop, and Legal Shield."""
    st.markdown("""
        <link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            /* 1. Global Reset & Typography */
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
            
            html, body, [class*="css"] {
                font-family: 'Inter', 'Pretendard', sans-serif !important;
                letter-spacing: 0.01em !important;
                color: #F8FAFC !important;
            }
            
            .main {
                background: linear-gradient(180deg, #0F172A 0%, #020617 100%) !important;
            }
            
            /* 2. Headline & UI Styling */
            .hero-headline {
                font-size: 3.8rem !important;
                font-weight: 800 !important;
                color: #FFFFFF !important;
                text-align: center;
                background: linear-gradient(to bottom, #FFFFFF 0%, #94A3B8 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            /* 3. Glowing Gold CTA */
            .stButton > button.glow-cta {
                background: linear-gradient(135deg, #FBBF24 0%, #D97706 100%) !important;
                color: #0F172A !important;
                border-radius: 14px !important;
                font-weight: 700 !important;
                transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
                box-shadow: 0 0 20px rgba(251, 191, 36, 0.3) !important;
            }
            
            /* 4. Terms Page Support */
            .legal-container {
                background: rgba(30, 41, 59, 0.4);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 20px;
                padding: 3rem;
                margin-top: 2rem;
                line-height: 1.8;
                color: #CBD5E1;
            }
            
            .legal-title { color: #FFFFFF; font-size: 2rem; font-weight: 700; margin-bottom: 2rem; }
            .legal-section { margin-bottom: 2rem; }
            .legal-h2 { color: #3B82F6; font-size: 1.2rem; font-weight: 600; margin-bottom: 1rem; }
            
            /* Footer Styling */
            .footer-link { color: #3B82F6; text-decoration: none; font-weight: 500; }
            .footer-link:hover { text-decoration: underline; color: #60A5FA; }

            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

# ── Routing Engine ──
page = st.query_params.get("page", "home")

# ─────────────────────────────────────────────
#  Terms of Service Page
# ─────────────────────────────────────────────
def show_terms_page():
    st.markdown('<div class="legal-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="legal-title">Terms of Service</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="legal-section">
        <h2 class="legal-h2">1. Educational Purpose & AI Role</h2>
        <p>Trytimeback is an AI-powered analysis tool designed strictly for educational and academic insight enhancement. Our technology transforms existing video data into concise summaries to facilitate more efficient learning.</p>
    </div>
    
    <div class="legal-section">
        <h2 class="legal-h2">2. Intellectual Property & Copyright</h2>
        <p><b>Trytimeback does not own, store, or redistribute original YouTube video content.</b> All intellectual property rights, trademarks, and copyrights belong to the respective original content creators and owners. Our summaries are derivative works intended for "Fair Use" educational transformation.</p>
    </div>
    
    <div class="legal-section">
        <h2 class="legal-h2">3. User Responsibility</h2>
        <p>Users are responsible for ensuring their use of summarized content complies with applicable copyright laws. Trytimeback is not liable for any misuse of the generated insights outside of educational contexts.</p>
    </div>
    
    <div class="legal-section">
        <h2 class="legal-h2">4. Service Limitations</h2>
        <p>As an AI-driven service, accuracy may vary based on video complexity and transcript availability. Trytimeback provides these insights on an "as-is" basis for study assistance.</p>
    </div>
    
    <div class="legal-section">
        <p style='margin-top:2rem;'>Contact for Inquiries: <a href="mailto:admin@trytimeback.com" class="footer-link">admin@trytimeback.com</a></p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("← Return to Home"):
        st.query_params.clear()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  Main Execution Logic
# ─────────────────────────────────────────────
apply_platinum_design()

if page == "terms":
    show_terms_page()
else:
    # ── [Normal Home Page Logic Starts Here] ──
    st.markdown("""
    <div style="padding: 6rem 0 3rem 0;">
        <h1 class="hero-headline">Gain Back Your Study Time.</h1>
        <p style="text-align:center; color:#94A3B8; font-size:1.3rem;">AI-Powered YouTube Analysis for Efficient Learning.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ... (Rest of v4.2 Value Propositions and Auth Logic) ...
    # This block would contain the Hero CTA and Why Trytimeback cards.
    st.markdown("<center><h3>High Performance Analysis Center Active.</h3></center>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  Footer 2.0 (The Legal Shield)
# ─────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:4rem 2rem; border-top:1px solid rgba(255,255,255,0.05); margin-top:6rem;">
    <p style='color:#475569; font-size:0.85rem; margin-bottom:0.7rem;'>
        <b>Legal Disclaimer:</b> AI-powered educational analyzer. Content ownership belongs to original creators.
    </p>
    <p style='color:#64748B; font-size:0.8rem;'>
        Contact: <a href="mailto:admin@trytimeback.com" class="footer-link">admin@trytimeback.com</a> | 
        <a href="?page=terms" target="_self" class="footer-link">Terms of Service</a>
    </p>
    <p style='color:#475569; font-size:0.75rem; margin-top:1rem;'>
        © 2026 YouTube Insight Analyzer • PLATINUM GLOBAL ATOMIC v4.4
    </p>
</div>
""", unsafe_allow_html=True)
