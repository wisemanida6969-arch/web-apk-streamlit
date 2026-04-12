"""Paddle subscription upgrade page — uses server-side API for checkout URLs."""
import streamlit as st

from lib.config import (
    PADDLE_PRICE_BASIC_MONTHLY,
    PADDLE_PRICE_PRO_MONTHLY,
    PADDLE_PRICE_AGENCY_MONTHLY,
)
from lib.paddle import create_checkout_url


def render(user: dict):
    st.markdown("#### Upgrade Your Plan")
    current_plan = user.get("plan", "free")
    if current_plan == "admin":
        st.success("**ADMIN** — You have unlimited access to all features.")
    else:
        st.info(f"Current plan: **{current_plan.title()}**")

    st.markdown("---")

    plans = [
        {
            "name": "Free",
            "price": "$0",
            "period": "",
            "features": ["1 blog connection", "1 post per week", "Basic topics", "Community support"],
            "price_id": None,
        },
        {
            "name": "Basic",
            "price": "$9",
            "period": "/mo",
            "features": ["1 blog connection", "1 post per day", "All categories", "Email support"],
            "price_id": PADDLE_PRICE_BASIC_MONTHLY,
        },
        {
            "name": "Pro",
            "price": "$29",
            "period": "/mo",
            "features": ["3 blog connections", "3 posts per day", "Custom topics", "Priority support"],
            "price_id": PADDLE_PRICE_PRO_MONTHLY,
            "popular": True,
        },
        {
            "name": "Agency",
            "price": "$99",
            "period": "/mo",
            "features": ["10 blog connections", "30 posts per day", "API access", "Dedicated support"],
            "price_id": PADDLE_PRICE_AGENCY_MONTHLY,
        },
    ]

    cols = st.columns(4)

    for col, plan in zip(cols, plans):
        with col:
            is_popular = plan.get("popular", False)

            if is_popular:
                st.markdown("##### " + plan["name"] + " :star:")
            else:
                st.markdown("##### " + plan["name"])

            st.markdown(
                f'<div style="font-size:2rem;font-weight:900;color:#8b5cf6;margin:8px 0;">'
                f'{plan["price"]}<span style="font-size:0.9rem;color:#64748b;">{plan["period"]}</span></div>',
                unsafe_allow_html=True,
            )

            for feat in plan["features"]:
                st.markdown(f"- {feat}")

            if plan["price_id"]:
                btn_type = "primary" if is_popular else "secondary"
                if st.button(
                    f"Upgrade to {plan['name']}",
                    key=f"upgrade_{plan['name'].lower()}",
                    use_container_width=True,
                    type=btn_type,
                ):
                    with st.spinner("Creating checkout..."):
                        checkout_url = create_checkout_url(
                            price_id=plan["price_id"],
                            customer_email=user.get("email", ""),
                        )
                    if checkout_url:
                        st.success("Checkout ready!")
                        st.link_button(
                            f"Complete {plan['name']} Payment",
                            checkout_url,
                            use_container_width=True,
                            type="primary",
                        )
                    else:
                        st.error("Failed to create checkout. Please try again or contact admin@trytimeback.com")
            else:
                st.markdown(
                    '<div style="text-align:center;color:#64748b;padding:8px;">Current Tier</div>',
                    unsafe_allow_html=True,
                )

    st.markdown("---")
    st.caption("Secure payment powered by Paddle. Cancel anytime. 7-day money back guarantee.")
