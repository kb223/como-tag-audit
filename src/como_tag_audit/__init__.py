"""Static Google Consent Mode audit for GTM containers.

Finds every tag that fires without respecting user consent — from a URL,
a GTM ID, or a raw ``gtm.js`` body. No browser required.

Public API:
    audit_url(url)          -> AuditResult
    audit_gtm_id(gtm_id)    -> AuditResult
    audit_js(js_body)       -> AuditResult

See README for the upgrade path to a live audit (what actually fires
after a user denies consent).
"""

from __future__ import annotations

from como_tag_audit.audit import audit_gtm_id, audit_js, audit_url
from como_tag_audit.models import AuditResult, TagEntry, Verdict

__all__ = [
    "AuditResult",
    "TagEntry",
    "Verdict",
    "audit_gtm_id",
    "audit_js",
    "audit_url",
]

__version__ = "0.1.0"
