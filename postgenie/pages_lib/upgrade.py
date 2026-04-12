"""Paddle subscription upgrade page."""
import streamlit as st

from lib.config import (
    PADDLE_PRICE_BASIC_MONTHLY,
    PADDLE_PRICE_PRO_MONTHLY,
    PADDLE_PRICE_AGENCY_MONTHLY,
)


def render(user: dict):
    st.markdown("#### Upgrade Your Plan")
    current_plan = user.get("plan", "free")
    if current_plan == "admin":
        st.success("**ADMIN** — You have unlimited access to all features.")
    else:
        st.info(f"Current plan: **{current_plan.title()}**")

    st.markdown("---")

    # Pricing cards using native Streamlit columns
    cols = st.columns(4)

    plans = [
        {
            "name": "Free",
            "price": "$0",
            "period": "",
            "features": ["1 blog connection", "1 post per week", "Basic topics", "Community support"],
            "btn": None,
        },
        {
            "name": "Basic",
            "price": "$9",
            "period": "/mo",
            "features": ["1 blog connection", "1 post per day", "All categories", "Email support"],
            "btn": "basic",
        },
        {
            "name": "Pro",
            "price": "$29",
            "period": "/mo",
            "features": ["3 blog connections", "3 posts per day", "Custom topics", "Priority support"],
            "btn": "pro",
            "popular": True,
        },
        {
            "name": "Agency",
            "price": "$99",
            "period": "/mo",
            "features": ["10 blog connections", "30 posts per day", "API access", "Dedicated support"],
            "btn": "agency",
        },
    ]

    for col, plan in zip(cols, plans):
        with col:
            is_popular = plan.get("popular", False)

            if is_popular:
                st.markdown(
                    '<div style="background:linear-gradient(135deg,#8b5cf6,#3b82f6);'
                    'padding:2px;border-radius:14px;">'
                    '<div style="background:#1e293b;border-radius:12px;padding:20px;">',
                    unsafe_allow_html=True,
                )
                st.markdown("##### " + plan["name"] + " ⭐")
            else:
                st.markdown(
                    '<div style="background:#1e293b;border:1px solid rgba(255,255,255,0.08);'
                    'border-radius:14px;padding:20px;">',
                    unsafe_allow_html=True,
                )
                st.markdown("##### " + plan["name"])

            st.markdown(
                f'<div style="font-size:2rem;font-weight:900;color:#8b5cf6;margin:8px 0;">'
                f'{plan["price"]}<span style="font-size:0.9rem;color:#64748b;">{plan["period"]}</span></div>',
                unsafe_allow_html=True,
            )

            for feat in plan["features"]:
                st.markdown(f"- {feat}")

            if plan["btn"] and current_plan not in ("admin",):
                email = user.get("email", "")
                subject = f"PostGenie Upgrade to {plan['name']} Plan"
                body = f"Hi, I would like to upgrade to the {plan['name']} plan (${plan['price']}/mo).\n\nAccount email: {email}\n\nThank you!"
                mailto = f"mailto:admin@trytimeback.com?subject={subject}&body={body}"
                st.link_button(
                    f"Upgrade to {plan['name']}",
                    mailto,
                    use_container_width=True,
                    type="primary" if is_popular else "secondary",
                )
            elif not plan["btn"]:
                st.markdown(
                    '<div style="text-align:center;color:#64748b;padding:8px;">Current Tier</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("</div>", unsafe_allow_html=True)
            if is_popular:
                st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("""
    **How to upgrade:**
    1. Click the **Upgrade** button for your desired plan
    2. An email will open to **admin@trytimeback.com**
    3. We'll set up your subscription and activate your plan within 24 hours

    **Payment methods:** Credit card, PayPal (processed securely via Paddle)

    **Questions?** Contact [admin@trytimeback.com](mailto:admin@trytimeback.com)
    """)

    st.caption("Secure payment powered by Paddle. Cancel anytime. 7-day money back guarantee.")
