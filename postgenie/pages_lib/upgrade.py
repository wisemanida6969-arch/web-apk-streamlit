"""Paddle subscription upgrade page."""
import streamlit as st
import streamlit.components.v1 as components

from lib.config import (
    PADDLE_PRICE_BASIC_MONTHLY,
    PADDLE_PRICE_PRO_MONTHLY,
    PADDLE_PRICE_AGENCY_MONTHLY,
    PLAN_LIMITS,
)


def render(user: dict):
    st.markdown("#### 💎 Upgrade Your Plan")
    current_plan = user.get("plan", "free")
    st.info(f"Current plan: **{current_plan.title()}**")

    plans_html = f"""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * {{ font-family: 'Inter', sans-serif; box-sizing: border-box; }}
        .plans {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            padding: 20px;
        }}
        .plan {{
            background: linear-gradient(145deg, #1e293b, #0f172a);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 24px;
            color: #e2e8f0;
            text-align: center;
        }}
        .plan.popular {{
            border-color: #8b5cf6;
            box-shadow: 0 0 32px rgba(139,92,246,0.2);
        }}
        .plan h3 {{ margin: 0 0 8px; color: #f1f5f9; }}
        .plan .price {{ font-size: 2rem; font-weight: 900; color: #8b5cf6; margin: 12px 0; }}
        .plan ul {{ list-style: none; padding: 0; margin: 16px 0; text-align: left; }}
        .plan li {{ padding: 6px 0; color: #94a3b8; font-size: 0.85rem; }}
        .plan li::before {{ content: "✓ "; color: #22c55e; font-weight: 700; }}
        .btn {{
            width: 100%;
            background: linear-gradient(135deg, #8b5cf6, #3b82f6);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 12px;
            font-weight: 700;
            cursor: pointer;
            font-size: 0.95rem;
        }}
        .btn:hover {{ opacity: 0.9; }}
        .btn.current {{ background: rgba(255,255,255,0.1); cursor: default; }}
    </style>
    <script>
        // Inject Paddle.js into the TOP window (escape iframe)
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
                    customer: {{ email: '{user.get("email", "")}' }},
                }});
            }} else {{
                setTimeout(function() {{
                    if (top.Paddle) {{
                        top.Paddle.Checkout.open({{
                            items: [{{ priceId: priceId, quantity: 1 }}],
                            customer: {{ email: '{user.get("email", "")}' }},
                        }});
                    }} else {{
                        alert('Payment system is loading. Please try again in a moment.');
                    }}
                }}, 1500);
            }}
        }}
        }}
    </script>
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
            <button class="btn current" disabled>Current Plan</button>
        </div>
        <div class="plan">
            <h3>Basic</h3>
            <div class="price">$9<span style="font-size:0.9rem; color:#64748b;">/mo</span></div>
            <ul>
                <li>1 blog connection</li>
                <li>1 post per day</li>
                <li>All categories</li>
                <li>Email support</li>
            </ul>
            <button class="btn" onclick="openCheckout('{PADDLE_PRICE_BASIC_MONTHLY}')">Upgrade</button>
        </div>
        <div class="plan popular">
            <h3>Pro 👑</h3>
            <div class="price">$29<span style="font-size:0.9rem; color:#64748b;">/mo</span></div>
            <ul>
                <li>3 blog connections</li>
                <li>3 posts per day</li>
                <li>Custom topics</li>
                <li>Priority support</li>
            </ul>
            <button class="btn" onclick="openCheckout('{PADDLE_PRICE_PRO_MONTHLY}')">Upgrade</button>
        </div>
        <div class="plan">
            <h3>Agency</h3>
            <div class="price">$99<span style="font-size:0.9rem; color:#64748b;">/mo</span></div>
            <ul>
                <li>10 blog connections</li>
                <li>30 posts per day</li>
                <li>API access</li>
                <li>Dedicated support</li>
            </ul>
            <button class="btn" onclick="openCheckout('{PADDLE_PRICE_AGENCY_MONTHLY}')">Upgrade</button>
        </div>
    </div>
    """
    components.html(plans_html, height=520, scrolling=False)

    st.caption("💡 Payments are processed securely by Paddle. Cancel anytime.")
