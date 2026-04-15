# como-tag-audit

> **Static Google Consent Mode audit for GTM containers.** Finds every tag that fires without respecting user consent — from a URL, a GTM ID, or a raw `gtm.js` body. No browser required.

[![CI](https://github.com/kb223/como-tag-audit/actions/workflows/ci.yml/badge.svg)](https://github.com/kb223/como-tag-audit/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Why this exists

Google Consent Mode (CoMo) only covers **Google's own tags**. Every non-Google tag in your GTM container — Meta Pixel, TikTok, Hotjar, Klaviyo, a Custom HTML snippet — fires whatever you told the user, *unless* you configured per-tag consent settings in GTM.

Most teams don't. Most teams don't realize they don't.

This tool reads the raw `gtm.js` container off the wire and tells you, per tag, whether it will fire regardless of consent. Ten seconds, no browser install, no account.

It's the static half of a forensic audit. The live half — what *actually* fires after a user denies consent, which cookies are set, which vendors are hit, and what the legal exposure is — lives in the [full RSC audit](https://consent-api.roseskyconsulting.com).

## Install

```bash
pip install como-tag-audit
```

## Usage

### CLI

```bash
# Audit a live site
como-tag-audit https://example.com

# Audit a container by ID
como-tag-audit --gtm-id GTM-ABC1234

# Audit a local gtm.js you've already captured
como-tag-audit --file ./gtm.js

# Machine-readable output
como-tag-audit https://example.com --json
como-tag-audit https://example.com --md
```

Exit code is `1` if any violations are found, `0` if clean, `2` on fetch error — so you can wire it into CI.

### Library

```python
from como_tag_audit import audit_url

result = audit_url("https://example.com")

print(result.gtm_id)                      # "GTM-ABC1234"
print(result.summary.cmp_detected)        # "OneTrust"
print(result.summary.violations)          # 4

for tag in result.violations:
    print(f"{tag.tag_name} ({tag.vendor}) — {tag.reason}")
```

## What it actually checks

For every tag in the GTM container:

| Tag type | Has `consent_settings`? | Verdict |
|---|---|---|
| Google (`__ga4`, `__awct`, `__googtag`, …) | — | `ok` (covered by Advanced Consent Mode) |
| Google | yes, required | `ok` |
| Non-Google | no | **`missing_consent_config`** — fires regardless of consent |
| Non-Google | yes, required (`consent >= 2`) | `ok` |
| Any | yes, optional (`consent == 1`) | `optional_consent` |

Plus:

- CMP detection from page HTML (OneTrust, Cookiebot, Ketch, Didomi, TrustArc, Osano, Usercentrics, Termly, Quantcast, Sourcepoint, Iubenda, Shopify Consent).
- Consent Mode initialization detection (does the container call `gtag('consent', 'default', ...)`?).
- Vendor lookup against a curated starter library of 50+ common tag patterns.

## What it deliberately does **not** check

This is a static analysis tool. It cannot tell you:

- What network requests actually fire after a user denies consent
- Which cookies are set, and by whom
- Whether your CMP is correctly forwarding signals to GTM
- Whether server-side GTM is bypassing client-side consent (it often is)
- GPC (`Sec-GPC`) respect in practice
- Post-denial pixel firing (the CIPA §631 exposure angle)
- Legal exposure grading against CPRA, CIPA, VCDPA, GDPR, etc.

If you need any of that, run a [full live audit](https://consent-api.roseskyconsulting.com).

## How it works

1. **Fetch the page.** Plain HTTP GET — no browser.
2. **Extract the GTM ID** with a regex (`GTM-[A-Z0-9]+`).
3. **Fetch `gtm.js`** directly from `googletagmanager.com`.
4. **Parse the embedded container JSON** by brace-counting through the minified JS.
5. **Classify each tag** against the Advanced Consent Mode rule.

No JavaScript execution, no headless browser, no cookies, no fingerprinting.

## Limitations

- **Server-side GTM containers are not client-accessible.** If a site uses SSGTM, the client `gtm.js` only shows what's routed through the server — the server container itself is invisible to any client-side audit tool. This is flagged, not solved.
- **The `gtm.js` format is Google's private internal structure.** It has been stable for years but could change without notice. A parse failure is surfaced as a warning, not an exception.
- **Corporate networks that block `googletagmanager.com`** will get a `FetchError`. Use `--file` with a container you've captured locally instead.

## Development

```bash
git clone git@github.com:kb223/como-tag-audit.git
cd como-tag-audit
pip install -e ".[dev]"
pytest
ruff check src tests
mypy src
```

## Credit

The parser logic is extracted from the GTM tool in the [RSC consent-compliance-agent](https://consent-api.roseskyconsulting.com) — a forensic audit pipeline used for enterprise privacy-lawsuit defense work. This open-source package is the piece every team should be able to run for free.

## License

MIT — see [LICENSE](LICENSE).
