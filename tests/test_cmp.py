"""Tests for CMP detection."""

from __future__ import annotations

from pathlib import Path

import pytest

from como_tag_audit.cmp import detect_cmp

FIXTURES = Path(__file__).parent / "fixtures"


def test_detects_onetrust_from_fixture() -> None:
    html = (FIXTURES / "sample_page.html").read_text()
    assert detect_cmp(html) == "OneTrust"


@pytest.mark.parametrize(
    ("html", "expected"),
    [
        ("<script src='https://consent.cookiebot.com/uc.js'></script>", "Cookiebot"),
        ("<script src='https://global.ketchcdn.com/tag.js'></script>", "Ketch"),
        ("<script src='https://cdn.didomi.io/loader.js'></script>", "Didomi"),
        ("<script src='https://app.termly.io/embed.min.js'></script>", "Termly"),
        ("<html><body>no cmp here</body></html>", None),
        ("", None),
    ],
)
def test_detects_various_cmps(html: str, expected: str | None) -> None:
    assert detect_cmp(html) == expected
