"""CSV export of an audit's per-tag inventory."""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone

from como_tag_audit.models import AuditResult

CSV_COLUMNS = (
    "audited_at",
    "source_ref",
    "gtm_id",
    "cmp_detected",
    "consent_mode_initialized",
    "tag_id",
    "tag_name",
    "tag_type",
    "vendor",
    "is_google_tag",
    "consent_types",
    "verdict",
    "reason",
)


def render_csv(result: AuditResult, *, audited_at: datetime | None = None) -> str:
    """Render one row per tag, including audit-level context on each row.

    The duplicated header columns (``audited_at``, ``source_ref``, ``gtm_id``,
    ``cmp_detected``, ``consent_mode_initialized``) make the file trivially
    filterable and pivot-able in Excel/Sheets without joins.
    """
    ts = (audited_at or datetime.now(timezone.utc)).isoformat(timespec="seconds")
    s = result.summary
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(CSV_COLUMNS)
    for t in result.tags:
        writer.writerow(
            [
                ts,
                result.source_ref,
                s.gtm_id or "",
                s.cmp_detected or "",
                "yes" if s.consent_mode_initialized else "no",
                t.tag_id,
                t.tag_name,
                t.tag_type,
                t.vendor or "",
                "yes" if t.is_google_tag else "no",
                "|".join(t.consent_types),
                t.verdict.value,
                t.reason,
            ]
        )
    return buf.getvalue()
