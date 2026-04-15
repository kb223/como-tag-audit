# como-tag-audit

> **Point it at a URL. Get back a boardroom-ready Consent Mode audit — deck, spreadsheet, JSON — in ten seconds.**

[![CI](https://github.com/kb223/como-tag-audit/actions/workflows/ci.yml/badge.svg)](https://github.com/kb223/como-tag-audit/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## What you get

One command produces a complete audit bundle:

```bash
como-tag-audit https://example.com --report ./out
```

- **`report.md`** — a nine-slide Marp deck, auto-composed from the audit data.
  Metric cards, composition chart, top offenders bar chart, sample violations,
  context on the June 15, 2026 `ad_storage` consolidation, recommended next
  steps. Render to PDF, PNG carousel, or PPTX.
- **`report.csv`** — one row per tag, with verdict, vendor, consent types,
  and audit context repeated on every row for zero-join pivoting in Excel.
- **`report.json`** — raw audit data for pipelines and CI.

The deck uses the [robonuggets/marp-slides](https://github.com/robonuggets/marp-slides)
dark dashboard theme (Outfit + Raleway, `#080808` cards, gradient-edge metric
tiles) — ready to show a client, drop in a LinkedIn carousel, or attach to a
legal memo.

## Why it exists

Google Consent Mode covers **only Google's own tags**. Every non-Google tag in
your GTM container — Meta Pixel, TikTok, Hotjar, Klaviyo, a Custom HTML
snippet — fires whatever you told the user, *unless* each tag has explicit
`consent_settings` configured in GTM.

Most teams don't. Effective **June 15, 2026**, Google Ads will rely solely on
`ad_storage` — which makes the gap between "Google thinks you're compliant"
and "your container is actually gated" the whole ballgame.

This tool surfaces that gap in a format an exec will read.

## Install

```bash
pip install como-tag-audit
```

Rendering the deck to PDF or PNG uses Marp. Either install it once —

```bash
npm install -g @marp-team/marp-cli
```

— or run ad-hoc with `npx @marp-team/marp-cli …`.

## Usage

### Generate a report bundle

```bash
como-tag-audit https://example.com --report ./out
cd ./out

# Boardroom PDF
npx @marp-team/marp-cli report.md --html --pdf --allow-local-files

# LinkedIn carousel — one PNG per slide
npx @marp-team/marp-cli report.md --html --images png --allow-local-files

# PPTX for enterprise stakeholders
npx @marp-team/marp-cli report.md --html --pptx --allow-local-files
```

The `--html` flag is required so Marp honors the inline SVG charts and card
layouts in the auto-generated deck.

### Other output modes

```bash
como-tag-audit https://example.com                 # rich terminal report
como-tag-audit https://example.com --json          # machine-readable JSON
como-tag-audit https://example.com --md            # Markdown table
como-tag-audit --gtm-id GTM-ABC1234                # audit a container by ID
como-tag-audit --file ./gtm.js                     # audit a captured container
```

Exit code is `1` on violations, `0` clean, `2` fetch error — wire it into CI.

### Library

```python
from como_tag_audit import audit_url
from como_tag_audit.reporters import render_csv, render_deck

result = audit_url("https://example.com")

print(result.summary.cmp_detected)        # "OneTrust"
print(result.summary.violations)          # 64

deck_md = render_deck(result)             # full Marp deck string
csv_text = render_csv(result)             # full CSV string
```

## What it actually checks

For every tag in the GTM container:

| Tag type | Has `consent_settings`? | Verdict |
|---|---|---|
| Google (`__ga4`, `__awct`, `__googtag`, `__gaawe`, `__cvt_*`, …) | — | `ok` — covered by Advanced Consent Mode |
| Google | yes, required | `ok` |
| Non-Google | no | **`missing_consent_config`** — fires regardless of consent |
| Non-Google | yes, required (`consent >= 2`) | `ok` |
| Any | yes, optional (`consent == 1`) | `optional_consent` |
| Paused / listener (`__paused`, `__cl`, `__fsl`, `__sdl`, `__evl`, …) | — | excluded — does not fire |

Plus:

- CMP detection from page HTML (OneTrust, Cookiebot, Ketch, Didomi, TrustArc,
  Osano, Usercentrics, Termly, Quantcast, Sourcepoint, Iubenda, Shopify Consent).
- Consent Mode initialization detection — does the container itself call
  `gtag('consent', 'default', ...)`?
- Vendor lookup against a curated library of 50+ common tag patterns.

## What it deliberately does **not** check

This is static analysis. It cannot tell you:

- What network requests actually fire after a user denies consent
- Which cookies are set, and by whom
- Whether your CMP is correctly forwarding signals to GTM at runtime
- Whether server-side GTM is bypassing client-side consent (it often is)
- GPC (`Sec-GPC`) respect in practice
- Post-denial pixel firing (the CIPA §631 exposure angle)
- Legal exposure grading against CPRA, CIPA, VCDPA, GDPR

If you need any of that — [book a live audit](https://kennethjbuchanan.com/audit#get-audit).

## How it works

1. Plain HTTP GET of the page.
2. Regex the GTM ID (`GTM-[A-Z0-9]+`) out of the HTML.
3. Fetch `gtm.js` from `googletagmanager.com`.
4. Brace-count through the minified JS to extract the embedded container JSON
   (handles both `({"resource":...})` and `var data = {"resource":...}` shapes).
5. Classify each tag against the Advanced Consent Mode rule.
6. Hand the result to the deck + CSV reporters.

No JavaScript execution. No headless browser. No cookies.

## Limitations

- **Server-side GTM is invisible to any client-side tool.** The web container
  only shows what ships through the server; the server container itself is a
  black box. Flagged, not solved.
- **The `gtm.js` format is Google's private structure.** It has been stable for
  years but could change. Parse failures surface as warnings, not exceptions.
- **Corporate networks that block `googletagmanager.com`** will fail with a
  fetch error. Use `--file` with a locally captured container instead.

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

The parser is extracted from the GTM tool in the
[RSC consent-compliance-agent](https://kennethjbuchanan.com/audit#get-audit)
— a forensic audit pipeline used for enterprise privacy-lawsuit defense work.
The deck theme follows
[robonuggets/marp-slides](https://github.com/robonuggets/marp-slides).

## License

MIT — see [LICENSE](LICENSE).
