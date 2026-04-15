"""Tests for the deck + CSV reporters."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from como_tag_audit import audit_js
from como_tag_audit.reporters import render_csv, render_deck
from como_tag_audit.reporters.spreadsheet import CSV_COLUMNS

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_JS = (FIXTURES / "sample_gtm.js").read_text()


def _fixed_ts() -> datetime:
    return datetime(2026, 4, 15, 12, 0, tzinfo=timezone.utc)


def test_render_csv_has_header_and_one_row_per_tag() -> None:
    result = audit_js(SAMPLE_JS, gtm_id="GTM-TEST123")
    csv_text = render_csv(result, audited_at=_fixed_ts())
    lines = csv_text.strip().splitlines()
    # Header + one row per audited tag (listeners excluded upstream)
    assert len(lines) == 1 + result.summary.total_tags
    header = lines[0].split(",")
    assert tuple(header) == CSV_COLUMNS


def test_render_csv_rows_include_audit_context() -> None:
    result = audit_js(SAMPLE_JS, gtm_id="GTM-TEST123")
    csv_text = render_csv(result, audited_at=_fixed_ts())
    # Every data row repeats the gtm id so pivots work without joins
    for line in csv_text.strip().splitlines()[1:]:
        assert "GTM-TEST123" in line


def test_render_deck_has_marp_frontmatter_and_slides() -> None:
    result = audit_js(SAMPLE_JS, gtm_id="GTM-TEST123")
    deck = render_deck(result, audited_at=_fixed_ts())
    # Marp frontmatter
    assert deck.startswith("---\nmarp: true\n")
    # At least 7 slides expected (cover through next-steps)
    assert deck.count("\n---\n\n") >= 6
    # Must include the site summary numbers
    assert str(result.summary.total_tags) in deck
    assert str(result.summary.violations) in deck
    # Must link to the full audit upgrade path
    assert "kennethjbuchanan.com/audit" in deck
    # Theme comes from robonuggets dark template
    assert "Outfit" in deck
    assert "Raleway" in deck


def test_render_deck_handles_zero_violations() -> None:
    # Construct a clean deck by overriding the violation count via a fresh audit
    # on a container where every tag is google or has consent
    gtm_clean_js = (FIXTURES / "sample_gtm.js").read_text()
    result = audit_js(gtm_clean_js, gtm_id="GTM-TEST123")
    # Force the no-violation branch by clearing the list post-parse
    result.tags[:] = [t for t in result.tags if t.is_google_tag]
    result.summary.violations = 0
    result.summary.non_google_tags = 0
    deck = render_deck(result, audited_at=_fixed_ts())
    assert "No violations" in deck
