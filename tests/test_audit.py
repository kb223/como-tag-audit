"""End-to-end tests for the audit orchestrator."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx

from como_tag_audit import audit_gtm_id, audit_js, audit_url
from como_tag_audit.fetcher import FetchError
from como_tag_audit.models import Verdict

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_JS = (FIXTURES / "sample_gtm.js").read_text()
SAMPLE_HTML = (FIXTURES / "sample_page.html").read_text()


def test_audit_js_offline() -> None:
    result = audit_js(SAMPLE_JS, gtm_id="GTM-TEST123")
    assert result.source == "js"
    # 10 entries - 2 listeners = 8 audited tags
    assert result.summary.total_tags == 8
    assert result.summary.violations == 2
    assert result.summary.google_tags == 4  # __ga4, __awct, __cvt_12345, __gaawe
    assert result.summary.non_google_tags == 4
    # No page HTML, so no CMP
    assert result.summary.cmp_detected is None


def test_audit_result_to_json_is_valid() -> None:
    result = audit_js(SAMPLE_JS)
    data = json.loads(result.to_json())
    assert data["summary"]["violations"] == 2
    assert len(data["tags"]) == 8
    # Verdicts serialized as strings
    verdicts = {t["verdict"] for t in data["tags"]}
    assert Verdict.MISSING_CONSENT_CONFIG.value in verdicts


def test_audit_result_to_markdown_contains_summary() -> None:
    md = audit_js(SAMPLE_JS).to_markdown()
    assert "CoMo Tag Audit" in md
    assert "Violations:" in md
    assert "Meta Pixel fbq init" in md


def test_audit_js_empty_container_warns() -> None:
    result = audit_js("")
    assert result.summary.total_tags == 0
    assert any("No GTM container JS" in w for w in result.warnings)


@respx.mock
def test_audit_url_fetches_page_and_container() -> None:
    respx.get("https://example.com").mock(
        return_value=httpx.Response(200, text=SAMPLE_HTML)
    )
    respx.get("https://www.googletagmanager.com/gtm.js?id=GTM-ABC1234").mock(
        return_value=httpx.Response(200, text=SAMPLE_JS)
    )

    result = audit_url("https://example.com")
    assert result.gtm_id == "GTM-ABC1234"
    assert result.summary.cmp_detected == "OneTrust"
    assert result.summary.consent_mode_initialized is True
    assert result.summary.violations == 2


@respx.mock
def test_audit_url_handles_missing_gtm() -> None:
    respx.get("https://example.com").mock(
        return_value=httpx.Response(200, text="<html><body>no gtm</body></html>")
    )
    result = audit_url("https://example.com")
    assert result.gtm_id is None
    assert result.summary.total_tags == 0
    assert any("No GTM ID" in w for w in result.warnings)


@respx.mock
def test_audit_url_raises_on_page_error() -> None:
    respx.get("https://example.com").mock(return_value=httpx.Response(500))
    with pytest.raises(FetchError):
        audit_url("https://example.com")


@respx.mock
def test_audit_gtm_id_fetches_container_directly() -> None:
    respx.get("https://www.googletagmanager.com/gtm.js?id=GTM-ABC1234").mock(
        return_value=httpx.Response(200, text=SAMPLE_JS)
    )
    result = audit_gtm_id("GTM-ABC1234")
    assert result.summary.violations == 2
    # No page fetch -> no CMP detection
    assert result.summary.cmp_detected is None


def test_audit_gtm_id_rejects_invalid_id() -> None:
    with pytest.raises(ValueError):
        audit_gtm_id("not-a-gtm-id")


def test_violations_property_only_returns_missing_consent() -> None:
    result = audit_js(SAMPLE_JS)
    for tag in result.violations:
        assert tag.verdict == Verdict.MISSING_CONSENT_CONFIG
    assert len(result.violations) == result.summary.violations
