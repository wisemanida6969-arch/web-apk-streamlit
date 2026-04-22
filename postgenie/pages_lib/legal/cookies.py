"""Cookie Policy for PostGenie (access.trytimeback.com)."""
import streamlit as st


def render_cookies():
    st.markdown("# Cookie Policy")
    st.caption("Last updated: April 22, 2026")
    st.divider()

    st.markdown("""
**This service is operated by Trytimeback.**

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
