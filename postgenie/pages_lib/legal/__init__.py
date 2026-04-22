"""Legal pages for PostGenie (access.trytimeback.com).

Each policy lives in its own module for clarity and independent editing:
- terms.py    — Terms of Service
- privacy.py  — Privacy Policy
- cookies.py  — Cookie Policy
- refund.py   — Refund Policy
- footer.py   — Shared footer with legal links
"""
from .terms import render_terms
from .privacy import render_privacy
from .cookies import render_cookies
from .refund import render_refund
from .footer import render_footer


def render_legal_page(page_name: str) -> bool:
    """Render a legal page based on query param. Returns True if handled."""
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


__all__ = [
    "render_terms",
    "render_privacy",
    "render_cookies",
    "render_refund",
    "render_footer",
    "render_legal_page",
]
