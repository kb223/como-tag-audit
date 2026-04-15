"""Tests for the GTM container parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from como_tag_audit.models import Verdict
from como_tag_audit.parser import (
    detects_consent_mode_init,
    extract_container_json,
    parse_container,
)

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_js() -> str:
    return (FIXTURES / "sample_gtm.js").read_text()


def test_extract_container_json_finds_resource(sample_js: str) -> None:
    container = extract_container_json(sample_js)
    assert container is not None
    assert "resource" in container
    assert len(container["resource"]["tags"]) == 10


def test_extract_container_json_handles_assigned_form() -> None:
    # Modern gtm.js uses `var data = {"resource": ...}` rather than the
    # classic parenthesized form.
    js = 'var data = {"resource": {"tags": [{"function":"__ga4","tag_id":1}]}};'
    container = extract_container_json(js)
    assert container is not None
    assert container["resource"]["tags"][0]["function"] == "__ga4"


def test_extract_container_json_returns_none_on_garbage() -> None:
    assert extract_container_json("this is not gtm.js") is None


def test_extract_container_json_tolerates_malformed_json() -> None:
    # Opening pattern present but JSON unclosed
    assert extract_container_json('var x = ({"resource": {"tags": [') is None


def test_parse_container_classifies_all_tags(sample_js: str) -> None:
    tags = parse_container(sample_js)
    # 10 raw entries - 2 built-in listeners (__cl, __fsl) = 8 audited tags
    assert len(tags) == 8
    by_id = {t.tag_id: t for t in tags}
    assert 7 not in by_id  # __cl listener excluded
    assert 8 not in by_id  # __fsl listener excluded

    # GA4 with no consent settings -> OK (ACM-managed)
    assert by_id[1].is_google_tag
    assert by_id[1].verdict == Verdict.OK
    assert "Consent Mode" in by_id[1].reason

    # Google Ads with required consent -> OK
    assert by_id[2].verdict == Verdict.OK
    assert "ad_storage" in by_id[2].consent_types

    # Custom HTML Meta Pixel, no consent -> violation
    assert not by_id[3].is_google_tag
    assert by_id[3].verdict == Verdict.MISSING_CONSENT_CONFIG
    assert by_id[3].vendor == "Meta / Facebook"

    # Custom HTML TikTok with required consent -> OK
    assert by_id[4].verdict == Verdict.OK
    assert by_id[4].vendor == "TikTok"

    # Pinterest with optional consent (consent=1) -> OPTIONAL_CONSENT
    assert by_id[5].verdict == Verdict.OPTIONAL_CONSENT
    assert by_id[5].vendor == "Pinterest"

    # Hotjar with no consent -> violation
    assert by_id[6].verdict == Verdict.MISSING_CONSENT_CONFIG
    assert by_id[6].vendor == "Hotjar"

    # __cvt_12345 (prefix-matched Google tag) -> OK
    assert by_id[9].is_google_tag
    assert by_id[9].verdict == Verdict.OK

    # __gaawe (Google Ads Enhanced Conversions) -> OK
    assert by_id[10].is_google_tag
    assert by_id[10].verdict == Verdict.OK
    assert by_id[10].vendor == "Google Ads"


def test_parse_container_empty_input_returns_empty_list() -> None:
    assert parse_container("") == []


def test_parse_container_unparseable_returns_empty_list() -> None:
    assert parse_container("total garbage") == []


def test_detects_consent_mode_init_positive(sample_js: str) -> None:
    assert detects_consent_mode_init(sample_js) is True


def test_detects_consent_mode_init_negative() -> None:
    assert detects_consent_mode_init("no consent call here") is False
