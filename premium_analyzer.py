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
#  Terms of Service Page (v4.6 Formal)
# ─────────────────────────────────────────────
def show_terms_page():
    st.markdown('<div class="legal-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="legal-title">Terms of Service</h1>', unsafe_allow_html=True)
    st.markdown("<p style='color:#94A3B8; margin-bottom:2rem;'>Last Updated: April 4, 2026</p>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="legal-section">
        <p>Welcome to Trytimeback.com. By using our AI-powered YouTube analysis and summary service, you agree to the following terms.</p>
    </div>
    
    <div class="legal-section">
        <h2 class="legal-h2">1. Nature of Service</h2>
        <p>Trytimeback.com is an independent AI tool that provides transformative summaries and analysis of public YouTube content. We do not provide video hosting or downloading services.</p>
    </div>
    
    <div class="legal-section">
        <h2 class="legal-h2">2. Intellectual Property & Copyright</h2>
        <p>• <b>Original Content:</b> All rights, titles, and interests in the original video content belong to the respective copyright owners (YouTube creators). Trytimeback does not claim any ownership over the source material.<br>
        • <b>Fair Use:</b> Our service is designed for educational and informational purposes, consistent with the principles of "Fair Use" (Section 107 of the U.S. Copyright Act). We transform long-form video data into concise insights.<br>
        • <b>Attribution:</b> We encourage users to visit the original creator's channel. Each summary includes a link to the original source video.</p>
    </div>
    
    <div class="legal-section">
        <h2 class="legal-h2">3. User Responsibility</h2>
        <p>Users are responsible for ensuring that their use of the AI-generated summaries complies with their local laws and regulations. You agree not to use this service for any illegal purposes.</p>
    </div>
    
    <div class="legal-section">
        <h2 class="legal-h2">4. Subscription and Credits</h2>
        <p>Trytimeback provides summaries based on a credit system (Minutes). Refunds are processed according to our Refund Policy, provided the credits have not been significantly consumed.</p>
    </div>
    
    <div class="legal-section">
        <h2 class="legal-h2">5. Limitation of Liability</h2>
        <p>Trytimeback provides AI-generated content "as is." While we strive for high accuracy, we are not responsible for any inaccuracies in the AI's summaries or any decisions made based on them.</p>
    </div>
    
    <div class="legal-section">
        <h2 class="legal-h2">6. Takedown Requests (DMCA)</h2>
        <p>We respect intellectual property. If you are a copyright owner and wish to have a specific video excluded from our analysis, please contact us at <b>admin@trytimeback.com</b>.</p>
    </div>
    
    <div class="legal-section">
        <h2 class="legal-h2">7. Contact Us</h2>
        <p>For any legal inquiries, please reach out to: <a href="mailto:admin@trytimeback.com" class="footer-link">admin@trytimeback.com</a></p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("← Return to Learning Hub", key="back_from_terms"):
        st.query_params.clear()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  Privacy Policy Page (v4.6 Formal)
# ─────────────────────────────────────────────
def show_privacy_page():
    st.markdown('<div class="legal-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="legal-title">Privacy Policy</h1>', unsafe_allow_html=True)
    st.markdown("<p style='color:#94A3B8; margin-bottom:2rem;'>Effective Date: April 4, 2026</p>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="legal-section">
        <p>Trytimeback.com ("we," "our," or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, and safeguard your information when you use our AI summary service.</p>
    </div>
    
    <div class="legal-section">
        <h2 class="legal-h2">1. Information We Collect</h2>
        <p>• <b>Account Information:</b> When you sign in via Google, we receive your email address, name, and profile picture to create your account and manage your summary credits.<br>
        • <b>Usage Data:</b> We collect information on how you interact with our service, such as the YouTube URLs you summarize and the remaining minutes in your account.<br>
        • <b>Payment Information:</b> Payment processing is handled by our third-party provider (e.g., Paddle). We do not store your full credit card details on our servers.</p>
    </div>
    
    <div class="legal-section">
        <h2 class="legal-h2">2. How We Use Your Information</h2>
        <p>• To provide and maintain our AI summary service.<br>
        • To manage your user account and track your usage credits.<br>
        • To communicate with you regarding service updates or customer support (admin@trytimeback.com).<br>
        • To prevent fraudulent activity and ensure the security of our platform.</p>
    </div>
    
    <div class="legal-section">
        <h2 class="legal-h2">3. Data Storage and Security</h2>
        <p>We use industry-standard security measures (including Supabase for database management and Cloudflare for network security) to protect your data. However, no method of transmission over the internet is 100% secure.</p>
    </div>
    
    <div class="legal-section">
        <h2 class="legal-h2">4. Third-Party Services</h2>
        <p>We may share limited data with trusted third-party providers only to facilitate our service:<br>
        • <b>Google OAuth:</b> For secure user authentication.<br>
        • <b>Payment Processors:</b> To handle secure transactions.<br>
        • <b>AI Models:</b> To process summaries (data sent is anonymous and does not include your personal profile).</p>
    </div>
    
    <div class="legal-section">
        <h2 class="legal-h2">5. Your Rights</h2>
        <p>You have the right to access, update, or delete your personal information at any time. You can request data deletion by contacting us at <b>admin@trytimeback.com</b>.</p>
    </div>
    
    <div class="legal-section">
        <h2 class="legal-h2">6. Cookies</h2>
        <p>We use cookies to keep you logged in and to analyze our website traffic to improve user experience.</p>
    </div>
    
    <div class="legal-section">
        <h2 class="legal-h2">7. Changes to This Policy</h2>
        <p>We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new policy on this page.</p>
    </div>
    
    <div class="legal-section">
        <h2 class="legal-h2">8. Contact Us</h2>
        <p>If you have any questions about this Privacy Policy, please contact us: <a href="mailto:admin@trytimeback.com" class="footer-link">admin@trytimeback.com</a></p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("← Return to Learning Hub", key="back_from_privacy"):
        st.query_params.clear()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  Main Execution Logic
# ─────────────────────────────────────────────
apply_platinum_design()

if page == "terms":
    show_terms_page()
elif page == "privacy":
    show_privacy_page()
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
#  Footer 2.0 (The Legal Shield v4.6)
# ─────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:4rem 2rem; border-top:1px solid rgba(255,255,255,0.05); margin-top:6rem;">
    <p style='color:#475569; font-size:0.85rem; margin-bottom:0.7rem;'>
        <b>Legal Disclaimer:</b> AI-powered educational analyzer. Content ownership belongs to original creators.
    </p>
    <p style='color:#64748B; font-size:0.8rem;'>
        Contact: <a href="mailto:admin@trytimeback.com" class="footer-link">admin@trytimeback.com</a> | 
        <a href="?page=terms" target="_self" class="footer-link">Terms of Service</a> | 
        <a href="?page=privacy" target="_self" class="footer-link">Privacy Policy</a>
    </p>
    <p style='color:#475569; font-size:0.75rem; margin-top:10px;'>
        © 2026 YouTube Insight Analyzer • PLATINUM GLOBAL ATOMIC v4.6
    </p>
</div>
""", unsafe_allow_html=True)
