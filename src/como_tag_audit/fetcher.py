"""HTTP fetching for URL-mode audits.

Given a URL, find the GTM container ID on the page and fetch the
corresponding ``gtm.js``. All HTTP is plain GET — no browser, no
JavaScript execution.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import httpx

GTM_ID_RE = re.compile(r"GTM-[A-Z0-9]{4,10}")
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 "
    "como-tag-audit/0.1"
)
GTM_JS_URL = "https://www.googletagmanager.com/gtm.js?id={gtm_id}"
DEFAULT_TIMEOUT = 15.0


@dataclass(frozen=True)
class FetchResult:
    url: str
    page_html: str
    gtm_id: str | None
    gtm_js: str


class FetchError(RuntimeError):
    """Raised when a network fetch fails in a way the caller needs to know about."""


def _client(timeout: float) -> httpx.Client:
    return httpx.Client(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": _USER_AGENT, "Accept": "*/*"},
    )


def extract_gtm_id(html: str) -> str | None:
    """Return the first GTM container ID found in ``html``, or ``None``."""
    match = GTM_ID_RE.search(html)
    return match.group(0) if match else None


def fetch_gtm_js(gtm_id: str, *, timeout: float = DEFAULT_TIMEOUT) -> str:
    """Fetch the ``gtm.js`` body for a given GTM container ID."""
    if not GTM_ID_RE.fullmatch(gtm_id):
        raise ValueError(f"Not a valid GTM ID: {gtm_id!r}")
    url = GTM_JS_URL.format(gtm_id=gtm_id)
    with _client(timeout) as client:
        resp = client.get(url)
        if resp.status_code != 200:
            raise FetchError(
                f"gtm.js fetch for {gtm_id} returned HTTP {resp.status_code}"
            )
        return resp.text


def fetch_url(url: str, *, timeout: float = DEFAULT_TIMEOUT) -> FetchResult:
    """Fetch ``url``, extract its GTM ID, and fetch the container JS."""
    with _client(timeout) as client:
        try:
            page = client.get(url)
        except httpx.HTTPError as exc:
            raise FetchError(f"Failed to fetch {url}: {exc}") from exc

    if page.status_code >= 400:
        raise FetchError(f"Page fetch for {url} returned HTTP {page.status_code}")

    html = page.text
    gtm_id = extract_gtm_id(html)
    gtm_js = fetch_gtm_js(gtm_id, timeout=timeout) if gtm_id else ""
    return FetchResult(url=str(page.url), page_html=html, gtm_id=gtm_id, gtm_js=gtm_js)
