"""Public audit orchestration.

Three entry points, same shape out:
    audit_url(url)         - fetch page, find GTM ID, fetch gtm.js, classify
    audit_gtm_id(gtm_id)   - skip page, fetch gtm.js directly
    audit_js(js_body)      - offline: classify a gtm.js body you already have
"""

from __future__ import annotations

from como_tag_audit.cmp import detect_cmp
from como_tag_audit.fetcher import fetch_gtm_js, fetch_url
from como_tag_audit.models import AuditResult, AuditSummary, TagEntry, Verdict
from como_tag_audit.parser import detects_consent_mode_init, parse_container


def _build_result(
    *,
    gtm_id: str | None,
    source: str,
    source_ref: str,
    gtm_js: str,
    page_html: str,
    warnings: list[str],
) -> AuditResult:
    tags: list[TagEntry] = parse_container(gtm_js)
    cmp_name = detect_cmp(page_html) if page_html else None
    como_init = detects_consent_mode_init(gtm_js) if gtm_js else False

    summary = AuditSummary(
        total_tags=len(tags),
        google_tags=sum(1 for t in tags if t.is_google_tag),
        non_google_tags=sum(1 for t in tags if not t.is_google_tag),
        violations=sum(1 for t in tags if t.verdict == Verdict.MISSING_CONSENT_CONFIG),
        cmp_detected=cmp_name,
        consent_mode_initialized=como_init,
        gtm_id=gtm_id,
    )

    if not gtm_js:
        warnings.append("No GTM container JS — container not found or not fetched.")
    elif not tags:
        warnings.append(
            "Container JS was fetched but no tags parsed. The format may have "
            "changed, or this is a server-side container (not client-accessible)."
        )

    return AuditResult(
        gtm_id=gtm_id,
        source=source,
        source_ref=source_ref,
        tags=tags,
        summary=summary,
        warnings=warnings,
    )


def audit_url(url: str, *, timeout: float = 15.0) -> AuditResult:
    """Audit the GTM container referenced on ``url``."""
    warnings: list[str] = []
    fetched = fetch_url(url, timeout=timeout)
    if not fetched.gtm_id:
        warnings.append(f"No GTM ID found on {url}. Page may not use GTM.")
    return _build_result(
        gtm_id=fetched.gtm_id,
        source="url",
        source_ref=url,
        gtm_js=fetched.gtm_js,
        page_html=fetched.page_html,
        warnings=warnings,
    )


def audit_gtm_id(gtm_id: str, *, timeout: float = 15.0) -> AuditResult:
    """Audit a GTM container by ID. Skips the page fetch — no CMP detection."""
    gtm_js = fetch_gtm_js(gtm_id, timeout=timeout)
    return _build_result(
        gtm_id=gtm_id,
        source="gtm_id",
        source_ref=gtm_id,
        gtm_js=gtm_js,
        page_html="",
        warnings=["No page fetched — CMP detection skipped."],
    )


def audit_js(js_body: str, *, gtm_id: str | None = None) -> AuditResult:
    """Audit a ``gtm.js`` body you already have (offline)."""
    return _build_result(
        gtm_id=gtm_id,
        source="js",
        source_ref="<inline>",
        gtm_js=js_body,
        page_html="",
        warnings=["Offline mode — CMP detection skipped."],
    )
