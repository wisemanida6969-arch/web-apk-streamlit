"""Privacy Policy for PostGenie (access.trytimeback.com)."""
import streamlit as st


def render_privacy():
    st.markdown("# Privacy Policy")
    st.caption("Last updated: April 22, 2026")
    st.divider()

    st.markdown("""
**This service is operated by Trytimeback.**

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
