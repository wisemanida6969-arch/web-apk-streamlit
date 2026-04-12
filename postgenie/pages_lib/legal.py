"""
Legal pages for PostGenie
- Terms of Service
- Privacy Policy
- Cookie Policy
- Refund Policy
"""
import streamlit as st


LEGAL_PAGE_CSS = """
<style>
    .legal-container {
        max-width: 800px;
        margin: 40px auto;
        padding: 40px;
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
    }
    .legal-container h1 {
        color: #f1f5f9;
        font-size: 2rem;
        font-weight: 900;
        margin-bottom: 8px;
        background: linear-gradient(135deg, #8b5cf6, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .legal-container .updated {
        color: #64748b;
        font-size: 0.85rem;
        margin-bottom: 30px;
        padding-bottom: 20px;
        border-bottom: 1px solid rgba(255,255,255,0.08);
    }
    .legal-container h2 {
        color: #e2e8f0;
        font-size: 1.3rem;
        font-weight: 700;
        margin: 28px 0 12px;
    }
    .legal-container h3 {
        color: #cbd5e1;
        font-size: 1.05rem;
        font-weight: 600;
        margin: 18px 0 8px;
    }
    .legal-container p {
        color: #94a3b8;
        line-height: 1.8;
        margin-bottom: 14px;
        font-size: 0.95rem;
    }
    .legal-container ul {
        color: #94a3b8;
        line-height: 1.8;
        margin: 8px 0 16px 20px;
        font-size: 0.95rem;
    }
    .legal-container li { margin-bottom: 6px; }
    .legal-container strong { color: #e2e8f0; }
    .legal-container a { color: #8b5cf6; text-decoration: none; }
    .legal-container a:hover { text-decoration: underline; }
</style>
"""


def render_terms():
    st.markdown(LEGAL_PAGE_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class="legal-container">
        <h1>Terms of Service</h1>
        <div class="updated">Last updated: April 12, 2026</div>

        <h2>1. Acceptance of Terms</h2>
        <p>PostGenie ("the Service") is an AI-powered blog automation SaaS platform. By accessing or using the Service, you agree to be bound by these Terms. If you do not agree, you may not use the Service.</p>
        <p>You must be at least 14 years of age to use this Service.</p>

        <h2>2. Account</h2>
        <ul>
            <li>Accounts are created via Google OAuth. Only one account per Google account is permitted.</li>
            <li>Account information (email, name, profile picture) must be accurate. You are responsible for all activity under your account.</li>
            <li>Sharing, transferring, or selling accounts is strictly prohibited.</li>
            <li>If you believe your account security has been compromised, contact admin@trytimeback.com immediately.</li>
        </ul>

        <h2>3. AI-Generated Content Responsibility</h2>
        <p>PostGenie uses Claude AI to automatically generate blog posts. Users must note the following:</p>
        <ul>
            <li><strong>You are ultimately responsible</strong> for all AI-generated content published to your blog.</li>
            <li>You must ensure generated content does not infringe on <strong>copyrights, trademarks, privacy, or other third-party rights</strong>.</li>
            <li>AI may occasionally produce inaccurate or misleading information. Expert review is required for sensitive topics (medical, legal, financial, etc.).</li>
            <li>PostGenie is not liable for any legal disputes, damages, or defamation resulting from generated content.</li>
            <li>Generating or publishing illegal content (copyright infringement, hate speech, spam, etc.) is prohibited.</li>
        </ul>

        <h2>4. Billing & Subscription</h2>
        <ul>
            <li>Paid plans (Basic, Pro, Agency) are billed monthly on a recurring basis.</li>
            <li>Payments are processed securely via Paddle. Paddle's terms of service also apply.</li>
            <li>Subscriptions can be cancelled at any time. You will retain access until the end of the current billing period.</li>
            <li>Refunds are subject to our <a href="?page=refund">Refund Policy</a>.</li>
            <li>Prices may change with prior notice, effective from the next billing cycle.</li>
        </ul>

        <h2>5. Termination</h2>
        <ul>
            <li>You may delete your account at any time by contacting admin@trytimeback.com.</li>
            <li>PostGenie may restrict or terminate your access without prior notice if:
                <ul>
                    <li>You violate these Terms</li>
                    <li>You generate or publish illegal content</li>
                    <li>You abuse the Service or attempt system attacks</li>
                    <li>You infringe on the rights of others</li>
                </ul>
            </li>
            <li>Upon termination, data will be handled according to our <a href="?page=privacy">Privacy Policy</a>.</li>
        </ul>

        <h2>6. Disclaimer</h2>
        <p>The Service is provided "as-is" without any express or implied warranties. PostGenie is not liable for any direct or indirect damages arising from service interruptions, data loss, AI generation errors, or any other cause.</p>

        <h2>7. Governing Law</h2>
        <p>These Terms shall be governed by and construed in accordance with the laws of the Republic of Korea. Any disputes shall be subject to the jurisdiction of the courts of the Republic of Korea.</p>

        <h2>8. Contact</h2>
        <p>Questions about these Terms: <a href="mailto:admin@trytimeback.com">admin@trytimeback.com</a></p>
    </div>
    """, unsafe_allow_html=True)


def render_privacy():
    st.markdown(LEGAL_PAGE_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class="legal-container">
        <h1>Privacy Policy</h1>
        <div class="updated">Last updated: April 12, 2026</div>

        <p>PostGenie ("the Service") values your privacy and protects your information in compliance with applicable laws. This Privacy Policy explains what information we collect, how we use it, and how long we retain it.</p>

        <h2>1. Information We Collect</h2>

        <h3>A. Google Account Information</h3>
        <p>When you sign in via Google OAuth, we collect:</p>
        <ul>
            <li>Email address</li>
            <li>Name</li>
            <li>Profile picture URL</li>
        </ul>

        <h3>B. Blog Platform Information</h3>
        <p>When you connect a blog, we securely store:</p>
        <ul>
            <li>Blog ID and name (Blogger, WordPress, etc.)</li>
            <li>OAuth refresh token (for Blogger connection)</li>
            <li>Application Password (for WordPress connection)</li>
        </ul>

        <h3>C. Usage Data</h3>
        <ul>
            <li>Generated blog post content and metadata</li>
            <li>Schedule settings (topics, language, frequency, etc.)</li>
            <li>Posting success/failure records</li>
            <li>Daily AI usage (token count, generation count)</li>
        </ul>

        <h2>2. How We Use Information</h2>
        <ul>
            <li>Providing the PostGenie service (auto blog generation and publishing)</li>
            <li>User account management and authentication</li>
            <li>Payment processing and subscription management</li>
            <li>Applying plan-based usage limits</li>
            <li>Service quality improvement and analytics</li>
            <li>Customer support and inquiry response</li>
            <li>Legal compliance</li>
        </ul>

        <h2>3. Third-Party Services</h2>
        <p>PostGenie uses the following third-party services:</p>
        <ul>
            <li><strong>Google (OAuth, Blogger API)</strong>: Login and Blogger blog connection.
                <a href="https://policies.google.com/privacy" target="_blank">Google Privacy Policy</a></li>
            <li><strong>Anthropic Claude API</strong>: AI blog post generation. Content requests (topics, categories) are sent to Anthropic servers.
                <a href="https://www.anthropic.com/privacy" target="_blank">Anthropic Privacy Policy</a></li>
            <li><strong>Paddle</strong>: Payment processing. Payment information is stored directly by Paddle; PostGenie does not store payment details.
                <a href="https://www.paddle.com/legal/privacy" target="_blank">Paddle Privacy Policy</a></li>
            <li><strong>Supabase</strong>: Database hosting. All user data is stored encrypted on Supabase.</li>
        </ul>

        <h2>4. Data Retention & Deletion</h2>
        <ul>
            <li>Data is securely retained while your account is active.</li>
            <li>Upon account deletion request, all personal data will be <strong>permanently deleted within 30 days</strong>.</li>
            <li>Some data may be retained per legal obligations (tax records, etc.) for the period required by law.</li>
            <li>Deletion requests: <a href="mailto:admin@trytimeback.com">admin@trytimeback.com</a></li>
        </ul>

        <h2>5. Your Rights</h2>
        <p>You have the following rights regarding your data:</p>
        <ul>
            <li><strong>Right to Access</strong>: View your stored personal information.</li>
            <li><strong>Right to Rectification</strong>: Request correction of inaccurate information.</li>
            <li><strong>Right to Erasure</strong>: Request deletion of your account and personal data.</li>
            <li><strong>Right to Restrict Processing</strong>: Request suspension of specific processing.</li>
            <li><strong>Right to Portability</strong>: Transfer your data to another service.</li>
        </ul>

        <h2>6. Data Security</h2>
        <ul>
            <li>All communication is encrypted via HTTPS.</li>
            <li>OAuth tokens and passwords are stored encrypted.</li>
            <li>Supabase Row Level Security (RLS) ensures data isolation between users.</li>
            <li>Regular security audits are conducted.</li>
        </ul>

        <h2>7. Cookies</h2>
        <p>For details on cookie usage, please refer to our <a href="?page=cookies">Cookie Policy</a>.</p>

        <h2>8. Contact</h2>
        <p>Privacy inquiries: <a href="mailto:admin@trytimeback.com">admin@trytimeback.com</a></p>
    </div>
    """, unsafe_allow_html=True)


def render_cookies():
    st.markdown(LEGAL_PAGE_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class="legal-container">
        <h1>Cookie Policy</h1>
        <div class="updated">Last updated: April 12, 2026</div>

        <p>PostGenie ("the Service") uses cookies to improve service quality and enhance user experience. This Cookie Policy explains the types, purposes, and management of cookies used.</p>

        <h2>1. What Are Cookies?</h2>
        <p>Cookies are small text files stored on your device when you visit a website. They are used to identify users, maintain login sessions, and analyze usage patterns.</p>

        <h2>2. Essential Cookies</h2>
        <p>The following cookies are required for the Service to function and are used without consent:</p>
        <ul>
            <li><strong>Session Cookies</strong>: Maintain login sessions and identify users. Deleted when the browser is closed.</li>
            <li><strong>Authentication Cookies</strong>: Maintain Google OAuth login status.</li>
            <li><strong>Security Cookies</strong>: CSRF protection and security token management.</li>
            <li><strong>Preference Cookies</strong>: Store user settings such as language and theme.</li>
        </ul>

        <h2>3. Analytics Cookies</h2>
        <p>These cookies anonymously analyze usage patterns for service improvement. They do not identify individuals and are used for statistical purposes only:</p>
        <ul>
            <li><strong>Usage Statistics</strong>: Pages visited, time spent, feature usage frequency</li>
            <li><strong>Performance Metrics</strong>: Page load times, error rates</li>
            <li><strong>A/B Testing</strong>: Feature comparison tests for service improvement</li>
        </ul>

        <h2>4. Third-Party Cookies</h2>
        <p>Some cookies may be set by third-party services (Google OAuth, Paddle payments, etc.). These cookies are subject to the respective third-party privacy policies.</p>

        <h2>5. Managing Cookies</h2>
        <p>You can manage cookies through your browser settings:</p>
        <ul>
            <li>Block all cookies</li>
            <li>Block cookies from specific sites</li>
            <li>Delete stored cookies</li>
            <li>Receive notifications when cookies are stored</li>
        </ul>
        <p><strong>Note</strong>: Blocking essential cookies may cause some Service features (such as login) to not function properly.</p>

        <h3>Browser Cookie Settings</h3>
        <ul>
            <li><a href="https://support.google.com/chrome/answer/95647" target="_blank">Chrome</a></li>
            <li><a href="https://support.mozilla.org/en-US/kb/enhanced-tracking-protection-firefox-desktop" target="_blank">Firefox</a></li>
            <li><a href="https://support.apple.com/guide/safari/manage-cookies-sfri11471/mac" target="_blank">Safari</a></li>
            <li><a href="https://support.microsoft.com/en-us/microsoft-edge" target="_blank">Edge</a></li>
        </ul>

        <h2>6. Changes to This Policy</h2>
        <p>This Cookie Policy may be updated as the Service evolves. Significant changes will be communicated via email or in-service notification.</p>

        <h2>7. Contact</h2>
        <p>Cookie policy inquiries: <a href="mailto:admin@trytimeback.com">admin@trytimeback.com</a></p>
    </div>
    """, unsafe_allow_html=True)


def render_refund():
    st.markdown(LEGAL_PAGE_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class="legal-container">
        <h1>Refund Policy</h1>
        <div class="updated">Last updated: April 12, 2026</div>

        <p>PostGenie wants you to be satisfied with our service. This Refund Policy explains the conditions and procedures for refunds on paid subscriptions.</p>

        <h2>1. 7-Day Refund Guarantee</h2>
        <p>First-time paid plan subscribers may request a refund <strong>within 7 days</strong> of the initial payment, provided all of the following conditions are met:</p>
        <ul>
            <li>Refund requested within <strong>7 days</strong> of the first payment</li>
            <li><strong>No blog posts have been published</strong> since the payment</li>
            <li>No violation of the Terms of Service</li>
        </ul>

        <h2>2. Non-Refundable Cases</h2>
        <p>Refunds are not available in the following situations:</p>
        <ul>
            <li><strong>If even one blog post has been automatically published</strong> (AI usage has been consumed)</li>
            <li>More than 7 days have passed since payment</li>
            <li>Renewal payments (2nd cycle onwards) -- the refund guarantee applies to the first payment only</li>
            <li>Account suspension due to fraud, abuse, or Terms of Service violation</li>
            <li>Service interruptions due to scheduled maintenance or temporary outages</li>
        </ul>

        <h2>3. How to Request a Refund</h2>
        <p>To request a refund, send an email to <a href="mailto:admin@trytimeback.com">admin@trytimeback.com</a> with the following information:</p>
        <ul>
            <li>Account email (Google login email)</li>
            <li>Payment date and amount</li>
            <li>Paddle order number (found in your payment confirmation email)</li>
            <li>Reason for refund</li>
        </ul>
        <p>Requests are processed within <strong>3-5 business days</strong>. Approved refunds will be returned to the original payment method. Please allow an additional 3-10 business days for the refund to appear on your statement, depending on your card issuer or bank.</p>

        <h2>4. Cancellation</h2>
        <p>You can cancel your subscription at any time:</p>
        <ul>
            <li>Cancel directly via the Paddle customer portal (link in your payment email)</li>
            <li>Or email admin@trytimeback.com to request cancellation</li>
            <li>After cancellation, you will retain access until the end of the current billing period</li>
            <li>Automatic billing will stop from the next billing cycle</li>
            <li>Cancellation is not a refund -- already paid amounts require a separate refund request</li>
        </ul>

        <h2>5. Partial Refunds</h2>
        <p>Partial refunds are generally not provided. If you cancel mid-month, no refund will be issued for the remaining period, but you may continue using the Service until the end of the billing period.</p>

        <h2>6. Service Outage Refunds</h2>
        <p>If a <strong>continuous service outage of 48 hours or more</strong> occurs due to PostGenie's fault, you may request a proportional refund or service extension for the affected period.</p>

        <h2>7. Payment Disputes</h2>
        <p>If you believe there is an issue with a payment, please contact us before filing a dispute with your card issuer. Most issues can be resolved quickly via email.</p>

        <h2>8. Changes to This Policy</h2>
        <p>This Refund Policy may change. Changes will be communicated via email or in-service notification and will apply to payments made after the change.</p>

        <h2>9. Contact</h2>
        <p>Refund and billing inquiries: <a href="mailto:admin@trytimeback.com">admin@trytimeback.com</a></p>
    </div>
    """, unsafe_allow_html=True)


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
    <style>
        .legal-footer {
            text-align: center;
            padding: 30px 20px 20px;
            margin-top: 50px;
            border-top: 1px solid rgba(255,255,255,0.05);
        }
        .legal-footer a {
            color: #64748b;
            font-size: 0.82rem;
            text-decoration: none;
            margin: 0 10px;
            transition: color 0.2s;
        }
        .legal-footer a:hover { color: #94a3b8; }
        .legal-footer .separator { color: #334155; margin: 0 4px; }
        .legal-footer .copyright {
            color: #475569;
            font-size: 0.75rem;
            margin-top: 12px;
        }
    </style>
    <div class="legal-footer">
        <a href="?page=terms">Terms of Service</a>
        <span class="separator">|</span>
        <a href="?page=privacy">Privacy Policy</a>
        <span class="separator">|</span>
        <a href="?page=cookies">Cookie Policy</a>
        <span class="separator">|</span>
        <a href="?page=refund">Refund Policy</a>
        <div class="copyright">&copy; 2026 PostGenie. AI-Powered Blog Automation.</div>
    </div>
    """, unsafe_allow_html=True)
