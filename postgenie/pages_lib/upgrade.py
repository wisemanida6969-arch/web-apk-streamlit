"""Paddle subscription upgrade page — Paddle.js overlay checkout via window.top."""
import streamlit as st
import streamlit.components.v1 as components

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

    user_email = user.get("email", "")

    # Paddle checkout with window.top injection (works on Railway, same as Trytimeback)
    plans_html = f"""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
    <script>
        // Inject Paddle.js into TOP window (escape iframe)
        (function() {{
            var top = window.top;
            if (top._paddleReady) return;

            if (!top.document.getElementById('pg-paddle-sdk')) {{
                var s = top.document.createElement('script');
                s.id = 'pg-paddle-sdk';
                s.src = 'https://cdn.paddle.com/paddle/v2/paddle.js';
                s.onload = function() {{
                    top.Paddle.Initialize({{
                        token: 'live_1a8fd1443de5064e970587e81c9',
                        environment: 'production'
                    }});
                    top._paddleReady = true;
                    console.log('[PostGenie] Paddle initialized on TOP window');
                }};
                top.document.head.appendChild(s);
            }}
        }})();

        function openCheckout(priceId) {{
            var top = window.top;
            if (top.Paddle && top._paddleReady) {{
                top.Paddle.Checkout.open({{
                    items: [{{ priceId: priceId, quantity: 1 }}],
                    customer: {{ email: '{user_email}' }},
                }});
            }} else {{
                setTimeout(function() {{
                    if (top.Paddle) {{
                        top.Paddle.Checkout.open({{
                            items: [{{ priceId: priceId, quantity: 1 }}],
                            customer: {{ email: '{user_email}' }},
                        }});
                    }} else {{
                        alert('Payment system is loading. Please try again.');
                    }}
                }}, 1500);
            }}
        }}
    </script>
    <style>
        * {{ font-family: 'Inter', sans-serif; box-sizing: border-box; margin: 0; padding: 0; }}
        .plans {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 14px;
            padding: 10px;
        }}
        .plan {{
            background: linear-gradient(145deg, #1e293b, #0f172a);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 14px;
            padding: 22px 16px;
            color: #e2e8f0;
            text-align: center;
        }}
        .plan.popular {{
            border-color: #8b5cf6;
            box-shadow: 0 0 24px rgba(139,92,246,0.2);
        }}
        .plan h3 {{ margin: 0 0 6px; color: #f1f5f9; font-size: 1rem; }}
        .plan .price {{ font-size: 1.8rem; font-weight: 900; color: #8b5cf6; margin: 10px 0; }}
        .plan .period {{ font-size: 0.85rem; color: #64748b; }}
        .plan ul {{ list-style: none; padding: 0; margin: 14px 0; text-align: left; }}
        .plan li {{ padding: 5px 0; color: #94a3b8; font-size: 0.82rem; }}
        .plan li::before {{ content: "✓ "; color: #22c55e; font-weight: 700; }}
        .btn {{
            width: 100%;
            padding: 10px;
            border: none;
            border-radius: 8px;
            font-weight: 700;
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.2s;
            margin-top: 8px;
        }}
        .btn-primary {{
            background: linear-gradient(135deg, #8b5cf6, #3b82f6);
            color: white;
        }}
        .btn-primary:hover {{ opacity: 0.9; transform: translateY(-1px); }}
        .btn-secondary {{
            background: rgba(255,255,255,0.08);
            color: #94a3b8;
            border: 1px solid rgba(255,255,255,0.12);
        }}
        .btn-secondary:hover {{ background: rgba(255,255,255,0.12); color: #e2e8f0; }}
        .btn-disabled {{ background: rgba(255,255,255,0.05); color: #475569; cursor: default; }}
        .secure {{ text-align: center; color: #475569; font-size: 0.75rem; padding: 16px 0 4px; }}
        @media (max-width: 768px) {{
            .plans {{ grid-template-columns: 1fr 1fr; }}
        }}
        @media (max-width: 480px) {{
            .plans {{ grid-template-columns: 1fr; }}
        }}
    </style>

    <div class="plans">
        <div class="plan">
            <h3>Free</h3>
            <div class="price">$0</div>
            <ul>
                <li>1 blog connection</li>
                <li>1 post per week</li>
                <li>Basic topics</li>
                <li>Community support</li>
            </ul>
            <button class="btn btn-disabled" disabled>Current Tier</button>
        </div>
        <div class="plan">
            <h3>Basic</h3>
            <div class="price">$9<span class="period">/mo</span></div>
            <ul>
                <li>1 blog connection</li>
                <li>1 post per day</li>
                <li>All categories</li>
                <li>Email support</li>
            </ul>
            <button class="btn btn-secondary" onclick="openCheckout('{PADDLE_PRICE_BASIC_MONTHLY}')">Upgrade to Basic</button>
        </div>
        <div class="plan popular">
            <h3>Pro ⭐</h3>
            <div class="price">$29<span class="period">/mo</span></div>
            <ul>
                <li>3 blog connections</li>
                <li>3 posts per day</li>
                <li>Custom topics</li>
                <li>Priority support</li>
            </ul>
            <button class="btn btn-primary" onclick="openCheckout('{PADDLE_PRICE_PRO_MONTHLY}')">Upgrade to Pro</button>
        </div>
        <div class="plan">
            <h3>Agency</h3>
            <div class="price">$99<span class="period">/mo</span></div>
            <ul>
                <li>10 blog connections</li>
                <li>30 posts per day</li>
                <li>API access</li>
                <li>Dedicated support</li>
            </ul>
            <button class="btn btn-secondary" onclick="openCheckout('{PADDLE_PRICE_AGENCY_MONTHLY}')">Upgrade to Agency</button>
        </div>
    </div>
    <div class="secure">🔒 Secure payment powered by Paddle · Cancel anytime · 14-day money back guarantee</div>
    """
    components.html(plans_html, height=520, scrolling=False)
