"""Result types for a GTM Consent Mode audit."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum


class Verdict(str, Enum):
    """Per-tag verdict.

    - ``ok``: Google tag covered by Advanced Consent Mode, or non-Google
      tag with explicit consent settings configured.
    - ``missing_consent_config``: Non-Google tag with no consent settings.
      Fires regardless of user consent state. Confirmed violation.
    - ``optional_consent``: Tag has consent settings but they are optional
      (will fire even if consent is denied).
    """

    OK = "ok"
    MISSING_CONSENT_CONFIG = "missing_consent_config"
    OPTIONAL_CONSENT = "optional_consent"


@dataclass(frozen=True)
class TagEntry:
    """One tag from a GTM container, classified for Consent Mode compliance."""

    tag_id: int
    tag_name: str
    tag_type: str
    is_google_tag: bool
    vendor: str | None
    consent_types: tuple[str, ...]
    verdict: Verdict
    reason: str


@dataclass
class AuditSummary:
    total_tags: int
    google_tags: int
    non_google_tags: int
    violations: int
    cmp_detected: str | None
    consent_mode_initialized: bool
    gtm_id: str | None


@dataclass
class AuditResult:
    """Audit result for a single GTM container."""

    gtm_id: str | None
    source: str  # "url" | "gtm_id" | "js"
    source_ref: str  # the URL, the GTM ID, or "<inline>"
    tags: list[TagEntry]
    summary: AuditSummary
    warnings: list[str] = field(default_factory=list)

    @property
    def violations(self) -> list[TagEntry]:
        return [t for t in self.tags if t.verdict == Verdict.MISSING_CONSENT_CONFIG]

    def to_json(self, indent: int | None = 2) -> str:
        payload = {
            "gtm_id": self.gtm_id,
            "source": self.source,
            "source_ref": self.source_ref,
            "summary": asdict(self.summary),
            "tags": [
                {
                    **asdict(t),
                    "verdict": t.verdict.value,
                    "consent_types": list(t.consent_types),
                }
                for t in self.tags
            ],
            "warnings": self.warnings,
        }
        return json.dumps(payload, indent=indent)

    def to_markdown(self) -> str:
        s = self.summary
        lines = [
            f"# CoMo Tag Audit — {self.source_ref}",
            "",
            f"- **GTM ID:** `{s.gtm_id or 'not found'}`",
            f"- **CMP detected:** {s.cmp_detected or 'none / unknown'}",
            f"- **Consent Mode initialized:** {'yes' if s.consent_mode_initialized else 'no'}",
            f"- **Tags:** {s.total_tags} "
            f"({s.google_tags} Google, {s.non_google_tags} non-Google)",
            f"- **Violations:** {s.violations}",
            "",
            "| # | Tag | Type | Vendor | Google? | Consent | Verdict |",
            "|---|-----|------|--------|---------|---------|---------|",
        ]
        for t in self.tags:
            consent = ", ".join(t.consent_types) if t.consent_types else "—"
            vendor = t.vendor or "—"
            lines.append(
                f"| {t.tag_id} | {t.tag_name} | `{t.tag_type}` | {vendor} | "
                f"{'yes' if t.is_google_tag else 'no'} | {consent} | **{t.verdict.value}** |"
            )
        if self.warnings:
            lines += ["", "## Warnings", ""]
            lines += [f"- {w}" for w in self.warnings]
        return "\n".join(lines)
