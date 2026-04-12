"""Legal pages for PostGenie — using native Streamlit markdown for reliable rendering."""
import streamlit as st


def render_terms():
    st.markdown("# Terms of Service")
    st.caption("Last updated: April 12, 2026")
    st.divider()

    st.markdown("""
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


def render_privacy():
    st.markdown("# Privacy Policy")
    st.caption("Last updated: April 12, 2026")
    st.divider()

    st.markdown("""
PostGenie values your privacy and protects your information in compliance with applicable laws.

## 1. Information We Collect

**A. Google Account Information**: Email address, Name, Profile picture URL

**B. Blog Platform Information**: Blog ID and name, OAuth refresh token (Blogger), Application Password (WordPress)

**C. Usage Data**: Generated blog post content, Schedule settings, Posting records, Daily AI usage

## 2. How We Use Information

- Providing the PostGenie service (auto blog generation and publishing)
- User account management and authentication
- Payment processing and subscription management
- Applying plan-based usage limits
- Service quality improvement and analytics
- Customer support and legal compliance

## 3. Third-Party Services

- **Google (OAuth, Blogger API)**: Login and blog connection. [Google Privacy Policy](https://policies.google.com/privacy)
- **Anthropic Claude API**: AI blog post generation. [Anthropic Privacy Policy](https://www.anthropic.com/privacy)
- **Paddle**: Payment processing. PostGenie does not store payment details. [Paddle Privacy Policy](https://www.paddle.com/legal/privacy)
- **Supabase**: Database hosting. All data stored encrypted.

## 4. Data Retention & Deletion

- Data is securely retained while your account is active.
- Upon account deletion request, all personal data will be **permanently deleted within 30 days**.
- Some data may be retained per legal obligations for the period required by law.
- Deletion requests: **admin@trytimeback.com**

## 5. Your Rights

- **Right to Access**: View your stored personal information.
- **Right to Rectification**: Request correction of inaccurate information.
- **Right to Erasure**: Request deletion of your account and personal data.
- **Right to Restrict Processing**: Request suspension of specific processing.
- **Right to Portability**: Transfer your data to another service.

## 6. Data Security

- All communication encrypted via HTTPS.
- OAuth tokens and passwords stored encrypted.
- Supabase Row Level Security (RLS) ensures data isolation between users.

## 7. Contact

Privacy inquiries: **admin@trytimeback.com**
    """)


def render_cookies():
    st.markdown("# Cookie Policy")
    st.caption("Last updated: April 12, 2026")
    st.divider()

    st.markdown("""
PostGenie uses cookies to improve service quality and enhance user experience.

## 1. What Are Cookies?

Cookies are small text files stored on your device when you visit a website. They identify users, maintain login sessions, and analyze usage patterns.

## 2. Essential Cookies

Required for the Service to function (used without consent):

- **Session Cookies**: Maintain login sessions. Deleted when browser closes.
- **Authentication Cookies**: Maintain Google OAuth login status.
- **Security Cookies**: CSRF protection and security token management.
- **Preference Cookies**: Store user settings (language, theme).

## 3. Analytics Cookies

Anonymously analyze usage patterns for service improvement:

- **Usage Statistics**: Pages visited, time spent, feature usage frequency
- **Performance Metrics**: Page load times, error rates
- **A/B Testing**: Feature comparison tests

## 4. Third-Party Cookies

Some cookies may be set by third-party services (Google OAuth, Paddle). These follow the respective third-party privacy policies.

## 5. Managing Cookies

You can manage cookies through your browser settings:
- Block all or specific cookies
- Delete stored cookies
- Receive notifications when cookies are stored

**Note**: Blocking essential cookies may cause some features (login, etc.) to not function properly.

## 6. Contact

Cookie policy inquiries: **admin@trytimeback.com**
    """)


def render_refund():
    st.markdown("# Refund Policy")
    st.caption("Last updated: April 12, 2026")
    st.divider()

    st.markdown("""
PostGenie wants you to be satisfied with our service.

## 1. 7-Day Refund Guarantee

First-time paid subscribers may request a refund **within 7 days** of initial payment if:

- Refund requested within **7 days** of the first payment
- **No blog posts have been published** since payment
- No violation of Terms of Service

## 2. Non-Refundable Cases

- **If even one blog post has been published** (AI usage consumed)
- More than 7 days since payment
- Renewal payments (2nd cycle onwards)
- Account suspension due to fraud or abuse
- Scheduled maintenance or temporary outages

## 3. How to Request a Refund

Email **admin@trytimeback.com** with:
- Account email (Google login email)
- Payment date and amount
- Paddle order number (from payment confirmation email)
- Reason for refund

Requests processed within **3-5 business days**. Refunds returned to original payment method (allow 3-10 additional business days).

## 4. Cancellation

- Cancel via Paddle customer portal (link in payment email)
- Or email admin@trytimeback.com
- Access continues until end of current billing period
- Automatic billing stops from next cycle
- Cancellation is not a refund -- separate request needed

## 5. Partial Refunds

Generally not provided. If cancelled mid-month, you may continue using the Service until the end of the billing period.

## 6. Service Outage Refunds

If a **continuous outage of 48+ hours** occurs due to PostGenie's fault, you may request a proportional refund or service extension.

## 7. Contact

Refund and billing inquiries: **admin@trytimeback.com**
    """)


def render_legal_page(page_name: str):
    """Render a legal page based on query param."""
    renderers = {
        "terms": render_terms,
        "privacy": render_privacy,
        "cookies": render_cookies,
        "refund": render_refund,
    }
    renderer = renderers.get(page_name)
    if renderer:
        renderer()
        return True
    return False


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
