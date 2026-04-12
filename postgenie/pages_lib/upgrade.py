"""Paddle subscription upgrade page — inline checkout via components.html."""
import streamlit as st
import streamlit.components.v1 as components

from lib.config import (
    PADDLE_PRICE_BASIC_MONTHLY,
    PADDLE_PRICE_PRO_MONTHLY,
    PADDLE_PRICE_AGENCY_MONTHLY,
)
from lib.paddle import create_checkout_url


PADDLE_CLIENT_TOKEN = "live_1a8fd1443de5064e970587e81c9"


def render(user: dict):
    st.markdown("#### Upgrade Your Plan")
    current_plan = user.get("plan", "free")
    if current_plan == "admin":
        st.success("**ADMIN** — You have unlimited access to all features.")
    else:
        st.info(f"Current plan: **{current_plan.title()}**")

    st.markdown("---")

    plans = [
        {"name": "Free", "price": "$0", "period": "",
         "features": ["1 blog", "1 post/week", "Basic topics"], "price_id": None},
        {"name": "Basic", "price": "$9", "period": "/mo",
         "features": ["1 blog", "1 post/day", "All categories"], "price_id": PADDLE_PRICE_BASIC_MONTHLY},
        {"name": "Pro", "price": "$29", "period": "/mo",
         "features": ["3 blogs", "3 posts/day", "Custom topics"], "price_id": PADDLE_PRICE_PRO_MONTHLY, "popular": True},
        {"name": "Agency", "price": "$99", "period": "/mo",
         "features": ["10 blogs", "30 posts/day", "API access"], "price_id": PADDLE_PRICE_AGENCY_MONTHLY},
    ]

    cols = st.columns(4)
    for col, plan in zip(cols, plans):
        with col:
            is_popular = plan.get("popular", False)
            st.markdown(f"##### {plan['name']}" + (" :star:" if is_popular else ""))
            st.markdown(
                f'<div style="font-size:2rem;font-weight:900;color:#8b5cf6;margin:8px 0;">'
                f'{plan["price"]}<span style="font-size:0.9rem;color:#64748b;">{plan["period"]}</span></div>',
                unsafe_allow_html=True,
            )
            for feat in plan["features"]:
                st.markdown(f"- {feat}")

            if plan["price_id"]:
                btn_type = "primary" if is_popular else "secondary"
                if st.button(f"Upgrade to {plan['name']}",
                             key=f"upgrade_{plan['name'].lower()}",
                             use_container_width=True, type=btn_type):
                    with st.spinner("Creating checkout..."):
                        txn_id = create_checkout_url(
                            price_id=plan["price_id"],
                            customer_email=user.get("email", ""),
                        )
                    if txn_id:
                        st.session_state["active_checkout_txn"] = txn_id
                        st.session_state["active_checkout_plan"] = plan["name"]
                    else:
                        st.error("Failed. Contact admin@trytimeback.com")

    # Show inline Paddle checkout if a transaction is active
    txn_id = st.session_state.get("active_checkout_txn")
    checkout_plan = st.session_state.get("active_checkout_plan", "")
    if txn_id:
        st.markdown("---")
        st.markdown(f"### Complete {checkout_plan} Payment")

        # Paddle inline checkout rendered inside components.html iframe
        # This works because Paddle.js runs INSIDE the iframe (no window.top needed)
        checkout_html = f"""
        <div id="checkout-container" style="min-height:500px;"></div>
        <script src="https://cdn.paddle.com/paddle/v2/paddle.js"></script>
        <script>
            Paddle.Initialize({{ token: '{PADDLE_CLIENT_TOKEN}', environment: 'production' }});
            Paddle.Checkout.open({{
                transactionId: '{txn_id}',
                settings: {{
                    displayMode: "inline",
                    frameTarget: "checkout-container",
                    frameInitialHeight: 500,
                    frameStyle: "width: 100%; min-width: 312px; background-color: transparent; border: none;"
                }}
            }});
        </script>
        """
        components.html(checkout_html, height=600, scrolling=True)

        if st.button("Cancel checkout", key="cancel_checkout"):
            st.session_state.pop("active_checkout_txn", None)
            st.session_state.pop("active_checkout_plan", None)
            st.rerun()

    st.markdown("---")
    st.caption("Secure payment powered by Paddle. Cancel anytime. 7-day money back guarantee.")
