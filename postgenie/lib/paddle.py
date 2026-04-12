"""Paddle API integration for creating checkout sessions."""
import requests

from lib.config import get_secret


PADDLE_API_KEY = get_secret("PADDLE_API_KEY", "")
PADDLE_API_URL = "https://api.paddle.com"


def create_checkout_url(price_id: str, customer_email: str = "") -> str | None:
    """Create a Paddle transaction and return the TRANSACTION ID."""
    if not PADDLE_API_KEY:
        return None

    payload = {
        "items": [{"price_id": price_id, "quantity": 1}],
    }

    if customer_email:
        payload["customer"] = {"email": customer_email}

    try:
        resp = requests.post(
            f"{PADDLE_API_URL}/transactions",
            headers={
                "Authorization": f"Bearer {PADDLE_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        # Return the transaction ID (not the overlay URL)
        txn_id = data.get("data", {}).get("id", "")
        return txn_id if txn_id else None
    except Exception as e:
        print(f"[Paddle] Error creating transaction: {e}")
        return None
