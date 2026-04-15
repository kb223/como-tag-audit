"""Best-effort CMP (Consent Management Platform) detection from page HTML.

This is a static page-HTML sniff, not a live probe. It looks for script
src patterns that are characteristic of the major CMP vendors. The goal
is to label the container's environment, not to verify the CMP is
working — verifying behavior requires a live browser audit.
"""

from __future__ import annotations

import re

# Ordered: more specific patterns first so e.g. OneTrust's cookielaw.org
# isn't mistaken for a generic match.
_CMP_SIGNATURES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("OneTrust", re.compile(r"cookielaw\.org|onetrust", re.IGNORECASE)),
    ("Cookiebot", re.compile(r"cookiebot\.com|cookiebot", re.IGNORECASE)),
    ("Ketch", re.compile(r"ketch\.com|global\.ketchcdn\.com", re.IGNORECASE)),
    ("TrustArc", re.compile(r"trustarc\.com|truste\.com", re.IGNORECASE)),
    ("Didomi", re.compile(r"didomi\.io", re.IGNORECASE)),
    ("Usercentrics", re.compile(r"usercentrics\.eu|usercentrics\.com", re.IGNORECASE)),
    ("Osano", re.compile(r"osano\.com", re.IGNORECASE)),
    ("Iubenda", re.compile(r"iubenda\.com", re.IGNORECASE)),
    ("Termly", re.compile(r"termly\.io", re.IGNORECASE)),
    ("Quantcast Choice", re.compile(r"quantcast\.mgr\.consensu\.org|quantcast", re.IGNORECASE)),
    ("Sourcepoint", re.compile(r"sourcepoint\.com|sp-prod\.net", re.IGNORECASE)),
    ("Shopify Consent", re.compile(r"shopify.*consent|consent\.shopify", re.IGNORECASE)),
)


def detect_cmp(page_html: str) -> str | None:
    """Return the detected CMP name, or ``None`` if no match."""
    if not page_html:
        return None
    for name, pattern in _CMP_SIGNATURES:
        if pattern.search(page_html):
            return name
    return None
