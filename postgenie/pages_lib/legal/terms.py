"""Terms of Service for PostGenie (access.trytimeback.com)."""
import streamlit as st


def render_terms():
    st.markdown("# Terms of Service")
    st.caption("Last updated: April 22, 2026")
    st.divider()

    st.markdown("""
**This service is operated by Trytimeback.**

## 1. Acceptance of Terms

PostGenie ("the Service") is an AI-powered blog automation SaaS platform. By accessing or using the Service, you agree to be bound by these Terms. If you do not agree, you may not use the Service.

You must be at least 14 years of age to use this Service.

## 2. Account

- Accounts are created via Google OAuth. Only one account per Google account is permitted.
- Account information (email, name, profile picture) must be accurate. You are responsible for all activity under your account.
- Sharing, transferring, or selling accounts is strictly prohibited.
- If you believe your account security has been compromised, contact admin@trytimeback.com immediately.

## 3. AI-Generated Content Responsibility

PostGenie uses Claude AI to automatically generate blog posts. Users must note the following:

- **You are ultimately responsible** for all AI-generated content published to your blog.
- You must ensure generated content does not infringe on **copyrights, trademarks, privacy, or other third-party rights**.
- AI may occasionally produce inaccurate or misleading information. Expert review is required for sensitive topics (medical, legal, financial, etc.).
- PostGenie is not liable for any legal disputes, damages, or defamation resulting from generated content.
- Generating or publishing illegal content (copyright infringement, hate speech, spam, etc.) is prohibited.

## 4. Billing & Subscription

- Paid plans (Basic, Pro, Agency) are billed monthly on a recurring basis.
- Payments are processed securely via Paddle. Paddle's terms of service also apply.
- Subscriptions can be cancelled at any time. You will retain access until the end of the current billing period.
- Refunds are subject to our Refund Policy.
- Prices may change with prior notice, effective from the next billing cycle.

## 5. Termination

- You may delete your account at any time by contacting admin@trytimeback.com.
- PostGenie may restrict or terminate your access without prior notice if you violate these Terms, generate illegal content, abuse the Service, or infringe on the rights of others.
- Upon termination, data will be handled according to our Privacy Policy.

## 6. Disclaimer

The Service is provided "as-is" without any express or implied warranties. PostGenie is not liable for any direct or indirect damages arising from service interruptions, data loss, AI generation errors, or any other cause.

## 7. Governing Law

These Terms shall be governed by and construed in accordance with the laws of the Republic of Korea.

## 8. Contact

Questions about these Terms: **admin@trytimeback.com**
    """)
