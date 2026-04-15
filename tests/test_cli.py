"""Tests for the CLI entry point."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import respx

from como_tag_audit.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


def test_cli_file_flag_returns_violation_exit_code(capsys) -> None:
    exit_code = main(["--file", str(FIXTURES / "sample_gtm.js"), "--json"])
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["summary"]["violations"] == 2
    assert exit_code == 1


def test_cli_md_output(capsys) -> None:
    main(["--file", str(FIXTURES / "sample_gtm.js"), "--md"])
    out = capsys.readouterr().out
    assert "CoMo Tag Audit" in out
    assert "| Vendor |" in out


@respx.mock
def test_cli_url_mode_success(capsys) -> None:
    respx.get("https://example.com").mock(
        return_value=httpx.Response(
            200, text=(FIXTURES / "sample_page.html").read_text()
        )
    )
    respx.get("https://www.googletagmanager.com/gtm.js?id=GTM-ABC1234").mock(
        return_value=httpx.Response(200, text=(FIXTURES / "sample_gtm.js").read_text())
    )
    exit_code = main(["https://example.com", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["cmp_detected"] == "OneTrust"
    assert exit_code == 1  # has violations


@respx.mock
def test_cli_fetch_error_returns_2(capsys) -> None:
    respx.get("https://example.com").mock(return_value=httpx.Response(500))
    exit_code = main(["https://example.com"])
    assert exit_code == 2


def test_cli_invalid_gtm_id_returns_2() -> None:
    exit_code = main(["--gtm-id", "not-valid"])
    assert exit_code == 2
