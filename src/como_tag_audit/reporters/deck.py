"""Generate a boardroom-ready Marp deck from an audit result.

The theme follows the `robonuggets/marp-slides` dark dashboard conventions
(Outfit 800 headings + Raleway 100 body, `#ff6b1a` accent, `#000` background,
`#080808` cards). Export to PDF or PNG with:

    npx @marp-team/marp-cli report.md --pdf --allow-local-files
    npx @marp-team/marp-cli report.md --images png --allow-local-files

Every slide is auto-composed from an ``AuditResult``; nothing here is
boilerplate — open the deck, share it, done.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urlparse

from como_tag_audit.models import AuditResult, TagEntry, Verdict

# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

_THEME_CSS = """
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&family=Raleway:wght@100;200;300;400&display=swap');

  :root {
    --a: #ff6b1a; --a2: #ff8c4a;
    --bg: #000; --s: #080808; --b: #111;
    --body: #999; --label: #666; --m: #555; --t: #fff;
    --g: #22c55e; --r: #ef4444; --y: #f5a623;
  }

  section {
    background: var(--bg); color: var(--t);
    font-family: 'Raleway', sans-serif; font-weight: 200;
    padding: 56px 72px; line-height: 1.5; font-size: 24px;
  }

  h1 { font-family: 'Outfit'; font-weight: 800; font-size: 3em;
       color: var(--t); letter-spacing: -0.03em; line-height: 1; margin: 0 0 6px; }
  h2 { font-family: 'Raleway'; font-weight: 100; font-size: 1.3em;
       color: #888; margin: 0 0 24px; }
  h3 { font-family: 'Outfit'; font-weight: 600; font-size: 0.6em;
       color: var(--m); text-transform: uppercase; letter-spacing: 0.2em; margin: 0 0 6px; }
  strong { color: var(--a); font-weight: 400; }
  code { font-family: 'IBM Plex Mono', monospace; font-size: 0.85em;
         color: var(--a2); background: #0a0a0a; padding: 1px 7px;
         border-radius: 4px; border: 1px solid var(--b); }

  section.lead { display: flex; flex-direction: column;
                 justify-content: center; align-items: center; text-align: center; }
  section.lead h1 { font-size: 3.8em; }

  section::after { font-family: 'Outfit'; font-size: 0.55em; color: #222; }

  .tag { font-family: 'Outfit'; font-weight: 600; font-size: 0.55em;
         letter-spacing: 0.12em; text-transform: uppercase;
         padding: 3px 10px; border-radius: 4px; display: inline-block; }

  .card { background: var(--s); border: 1px solid var(--b);
          border-radius: 10px; padding: 18px 20px;
          position: relative; overflow: hidden; }
  .card .edge { position: absolute; top: 0; left: 0; width: 100%;
                height: 2px; background: linear-gradient(90deg, var(--a), transparent); }
  .card .edge.g { background: linear-gradient(90deg, var(--g), transparent); }
  .card .edge.r { background: linear-gradient(90deg, var(--r), transparent); }
  .card .edge.y { background: linear-gradient(90deg, var(--y), transparent); }

  .row { display: flex; align-items: center; gap: 14px;
         padding: 10px 12px; border-radius: 6px;
         border-bottom: 1px solid #0a0a0a; }

  abbr { text-decoration: none; border-bottom: 1px dotted #333; cursor: help; }
""".strip()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _domain(ref: str) -> str:
    try:
        p = urlparse(ref if "://" in ref else f"https://{ref}")
        return (p.netloc or p.path or ref).replace("www.", "")
    except Exception:
        return ref


def _pct(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(100 * numerator / denominator, 1)


def _verdict_tag(verdict: Verdict) -> str:
    style_ok = "background:#22c55e14; color:var(--g); border:1px solid #22c55e33;"
    style_missing = "background:#ef444414; color:var(--r); border:1px solid #ef444433;"
    style_optional = "background:#f5a62314; color:var(--y); border:1px solid #f5a62333;"
    label, style = {
        Verdict.OK: ("OK", style_ok),
        Verdict.MISSING_CONSENT_CONFIG: ("VIOLATION", style_missing),
        Verdict.OPTIONAL_CONSENT: ("OPTIONAL", style_optional),
    }[verdict]
    return f'<span class="tag" style="{style}">{label}</span>'


def _frontmatter(domain: str, audited_at: datetime) -> str:
    date = audited_at.strftime("%b %d, %Y")
    return (
        "---\n"
        "marp: true\n"
        "theme: default\n"
        "paginate: true\n"
        "style: |\n"
        + "\n".join("  " + line for line in _THEME_CSS.splitlines())
        + "\n"
        f"footer: '{domain}  ·  {date}'\n"
        "---\n"
    )


# ---------------------------------------------------------------------------
# Slides
# ---------------------------------------------------------------------------


def _slide_cover(result: AuditResult, audited_at: datetime) -> str:
    s = result.summary
    domain = _domain(result.source_ref)
    vio_pct = _pct(s.violations, s.total_tags)
    return f"""
<!-- _class: lead -->
<!-- _paginate: false -->
<!-- _footer: '' -->

### Consent Mode audit

# {domain}

<div style="font-family:'Raleway'; font-weight:100; font-size:1em; color:#ffffff55; margin-top:6px;">
{audited_at.strftime('%B %d, %Y')} &nbsp;·&nbsp; {s.gtm_id or 'no GTM container'}
</div>

<div style="display:flex; gap:10px; margin-top:28px;">
  <span style="background:#ff6b1a15; border:1px solid #ff6b1a33; border-radius:20px; padding:5px 16px; font-family:'Outfit'; font-size:0.55em; color:#ff8c4a; font-weight:400;">{s.total_tags} tags</span>
  <span style="background:#ef444415; border:1px solid #ef444433; border-radius:20px; padding:5px 16px; font-family:'Outfit'; font-size:0.55em; color:#ef4444; font-weight:400;">{s.violations} violations ({vio_pct}%)</span>
  <span style="background:#22c55e15; border:1px solid #22c55e33; border-radius:20px; padding:5px 16px; font-family:'Outfit'; font-size:0.55em; color:#22c55e; font-weight:400;">CMP: {s.cmp_detected or 'unknown'}</span>
</div>
""".strip()


def _metric_card(label: str, value: str, edge: str, sub: str = "") -> str:
    sub_div = (
        f'<div style="font-size:0.65em; color:var(--body); margin-top:8px;">{sub}</div>'
        if sub
        else ""
    )
    return (
        f'<div class="card" style="flex:1;">'
        f'<div class="edge {edge}"></div>'
        f'<div style="font-family:\'Outfit\'; font-weight:600; font-size:0.5em; color:var(--m); letter-spacing:0.15em; text-transform:uppercase; margin-bottom:10px;">{label}</div>'
        f'<div style="font-family:\'Outfit\'; font-size:2.2em; font-weight:800; color:var(--t); line-height:1;">{value}</div>'
        f'{sub_div}'
        f'</div>'
    )


def _slide_summary(result: AuditResult) -> str:
    s = result.summary
    vio_pct = _pct(s.violations, s.total_tags)
    google_pct = _pct(s.google_tags, s.total_tags)
    cards = "".join(
        [
            _metric_card("Total tags", str(s.total_tags), "", "in the GTM container"),
            _metric_card(
                "Google-owned",
                str(s.google_tags),
                "g",
                f"{google_pct}% — covered by Advanced CoMo",
            ),
            _metric_card(
                "Non-Google",
                str(s.non_google_tags),
                "y",
                "outside Google's consent scope",
            ),
            _metric_card(
                "Violations",
                str(s.violations),
                "r",
                f"{vio_pct}% fire without consent config",
            ),
        ]
    )
    return (
        "### At a glance\n\n"
        "## How consent is distributed across this container\n\n"
        f'<div style="display:flex; gap:14px; margin-top:18px;">{cards}</div>\n\n'
        '<div style="margin-top:32px; color:var(--body); font-size:0.78em; line-height:1.7;">'
        "Violations are non-Google tags with no <code>consent_settings</code> in the "
        "container. They fire on every pageview regardless of what the CMP signals to "
        "<code>ad_storage</code> or any other consent type."
        "</div>"
    )


def _slide_composition(result: AuditResult) -> str:
    s = result.summary
    total = max(s.total_tags, 1)
    google_ok = s.google_tags
    non_google_ok = s.non_google_tags - s.violations
    # Count optional-consent tags (amber) separately if any.
    optional = sum(1 for t in result.tags if t.verdict == Verdict.OPTIONAL_CONSENT)
    non_google_ok = max(non_google_ok - optional, 0)
    violations = s.violations

    segs = [
        ("#22c55e", google_ok, "Google-owned (Advanced CoMo)"),
        ("#15803d", non_google_ok, "Non-Google, declared consent"),
        ("#f5a623", optional, "Non-Google, optional consent"),
        ("#ef4444", violations, "Non-Google, no consent config"),
    ]

    bar_html = "".join(
        f'<div style="background:{color}; width:{_pct(count, total)}%;"></div>'
        for color, count, _ in segs
        if count > 0
    )

    legend_rows = []
    for color, count, label in segs:
        pct = _pct(count, total)
        legend_rows.append(
            f'<div style="display:flex; align-items:center; gap:14px; padding:8px 0; border-bottom:1px solid #0a0a0a;">'
            f'<div style="width:10px; height:10px; background:{color}; border-radius:2px;"></div>'
            f'<div style="flex:1; font-size:0.8em; color:var(--body);">{label}</div>'
            f'<div style="font-family:\'Outfit\'; font-size:0.9em; color:var(--t); font-weight:600;">{count}</div>'
            f'<div style="font-family:\'Outfit\'; font-size:0.7em; color:var(--label); min-width:50px; text-align:right;">{pct}%</div>'
            f'</div>'
        )

    return (
        "### Composition\n\n"
        "## Where consent coverage lives — and doesn't\n\n"
        f'<div style="display:flex; height:22px; border-radius:6px; overflow:hidden; margin-top:16px; background:#0a0a0a;">{bar_html}</div>\n\n'
        f'<div style="margin-top:22px;">{"".join(legend_rows)}</div>'
    )


def _slide_cmp_status(result: AuditResult) -> str:
    s = result.summary
    cmp = s.cmp_detected or "none detected"
    init = "yes" if s.consent_mode_initialized else "no"
    init_color = "var(--g)" if s.consent_mode_initialized else "var(--y)"

    cmp_note = (
        f"A {cmp} integration was detected on the page. That tells you a consent "
        "UI exists — not that it is correctly wired to the GTM container."
        if s.cmp_detected
        else "No known CMP integration was detected on the landing page. "
        "Consent may be handled by a custom script, or not at all."
    )
    init_note = (
        "A default <code>gtag('consent', 'default', ...)</code> call was found in "
        "the container itself."
        if s.consent_mode_initialized
        else "No default <code>gtag('consent', 'default', ...)</code> call was found "
        "in the container. The default state likely lives in the CMP loader — "
        "which means a live audit is required to confirm signal flow."
    )

    edge2 = "g" if s.consent_mode_initialized else "y"
    card_cmp = (
        f'<div class="card" style="flex:1;">'
        f'<div class="edge"></div>'
        f'<div style="font-family:\'Outfit\'; font-size:0.5em; color:var(--m); letter-spacing:0.15em; text-transform:uppercase; margin-bottom:12px;">CMP detected</div>'
        f'<div style="font-family:\'Outfit\'; font-size:1.8em; font-weight:800; color:var(--t); line-height:1;">{cmp}</div>'
        f'<div style="font-size:0.72em; color:var(--body); margin-top:12px; line-height:1.6;">{cmp_note}</div>'
        f'</div>'
    )
    card_init = (
        f'<div class="card" style="flex:1;">'
        f'<div class="edge {edge2}"></div>'
        f'<div style="font-family:\'Outfit\'; font-size:0.5em; color:var(--m); letter-spacing:0.15em; text-transform:uppercase; margin-bottom:12px;">Default consent state in container</div>'
        f'<div style="font-family:\'Outfit\'; font-size:1.8em; font-weight:800; color:{init_color}; line-height:1;">{init}</div>'
        f'<div style="font-size:0.72em; color:var(--body); margin-top:12px; line-height:1.6;">{init_note}</div>'
        f'</div>'
    )
    return (
        "### Consent plumbing\n\n"
        "## What the container tells us about the wiring\n\n"
        f'<div style="display:flex; gap:18px; margin-top:16px;">{card_cmp}{card_init}</div>'
    )


_TYPE_LABELS = {
    "__html": "Custom HTML",
    "__img": "Custom Image pixel",
    "__c": "Custom template",
    "__baut": "Microsoft Advertising (Bing UET)",
    "__bzi": "LinkedIn Insight",
    "__twitter_website_tag": "Twitter / X Pixel",
}


def _offender_label(tag: TagEntry) -> str:
    if tag.vendor:
        return tag.vendor
    return _TYPE_LABELS.get(tag.tag_type, tag.tag_type)


def _top_offenders(result: AuditResult, n: int = 6) -> list[tuple[str, int]]:
    counts: Counter[str] = Counter()
    for t in result.violations:
        counts[_offender_label(t)] += 1
    return counts.most_common(n)


def _slide_top_offenders(result: AuditResult) -> str:
    offenders = _top_offenders(result, 6)
    if not offenders:
        return """
### Top offenders

## No violations in this container

<div style="margin-top:40px; color:var(--body); font-size:0.9em;">
Every non-Google tag in the container has declared <code>consent_settings</code>.
That doesn't guarantee the CMP is forwarding signals correctly at runtime —
but the static configuration is clean.
</div>
""".strip()
    max_count = max(c for _, c in offenders)
    rows = []
    for name, count in offenders:
        width = int(100 * count / max_count)
        rows.append(
            f'<div style="margin-bottom:14px;">'
            f'<div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:6px;">'
            f'<span style="font-family:\'Outfit\'; font-weight:600; font-size:0.8em; color:var(--t);">{name}</span>'
            f'<span style="font-family:\'Outfit\'; font-size:0.75em; color:var(--a);">{count}</span>'
            f'</div>'
            f'<div style="height:10px; background:#0a0a0a; border-radius:3px; overflow:hidden;">'
            f'<div style="height:100%; width:{width}%; background:linear-gradient(90deg, var(--a), #cc5515);"></div>'
            f'</div>'
            f'</div>'
        )

    return (
        "### Top offenders\n\n"
        "## Vendors driving the violation count\n\n"
        f'<div style="margin-top:18px;">{"".join(rows)}</div>\n\n'
        '<div style="margin-top:18px; color:var(--body); font-size:0.72em; line-height:1.6;">'
        "Each bar counts tags in the container that name this vendor and fire "
        "without consent configuration. Custom HTML tags are grouped under "
        "<code>__html</code> when a specific vendor cannot be inferred."
        "</div>"
    )


def _violation_row(tag: TagEntry) -> str:
    # Fall back to a friendly type label when GTM strips instance names.
    raw_name = tag.tag_name
    if raw_name == tag.tag_type:
        display_name = _TYPE_LABELS.get(tag.tag_type, tag.tag_type)
    else:
        display_name = raw_name
    sub = tag.vendor or _TYPE_LABELS.get(tag.tag_type, tag.tag_type)
    return (
        '<div class="row" style="padding:8px 12px;">'
        f'<div style="font-family:\'Outfit\'; font-size:0.65em; color:var(--label); min-width:48px;">#{tag.tag_id}</div>'
        '<div style="flex:2; overflow:hidden;">'
        f'<div style="font-family:\'Outfit\'; font-weight:600; font-size:0.78em; color:var(--t); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{display_name}</div>'
        f'<div style="font-size:0.6em; color:var(--label); margin-top:2px;">{sub}</div>'
        '</div>'
        f'<div style="flex:1;"><code>{tag.tag_type}</code></div>'
        f'<div>{_verdict_tag(tag.verdict)}</div>'
        '</div>'
    )


def _slide_violation_sample(result: AuditResult) -> str:
    sample = result.violations[:6]
    if not sample:
        return ""
    rows = "".join(_violation_row(t) for t in sample)
    more = (
        f'<div style="margin-top:14px; color:var(--label); font-size:0.72em;">'
        f"...and {len(result.violations) - len(sample)} more in the CSV export."
        "</div>"
        if len(result.violations) > len(sample)
        else ""
    )
    return (
        "### Sample violations\n\n"
        f"## The first {len(sample)} tags that fire regardless of consent\n\n"
        f'<div style="margin-top:14px;">{rows}</div>\n\n'
        f"{more}"
    )


def _slide_context() -> str:
    covered = (
        '<div class="card" style="flex:1;">'
        '<div class="edge g"></div>'
        '<div style="font-family:\'Outfit\'; font-size:0.5em; color:var(--m); letter-spacing:0.15em; text-transform:uppercase; margin-bottom:12px;">Covered</div>'
        '<div style="color:var(--body); font-size:0.78em; line-height:1.7;">'
        "<strong>Google-owned tag types only</strong> &mdash; GA4, Google Ads "
        "conversion/remarketing, gtag, Floodlight, Ads Enhanced Conversions. "
        "These respect <code>ad_storage</code> and <code>analytics_storage</code> automatically."
        "</div>"
        "</div>"
    )
    not_covered = (
        '<div class="card" style="flex:1;">'
        '<div class="edge r"></div>'
        '<div style="font-family:\'Outfit\'; font-size:0.5em; color:var(--m); letter-spacing:0.15em; text-transform:uppercase; margin-bottom:12px;">NOT covered</div>'
        '<div style="color:var(--body); font-size:0.78em; line-height:1.7;">'
        "<strong>Everything else</strong> &mdash; Meta Pixel, TikTok, Pinterest, "
        "Bing UET, Hotjar, Klaviyo, Custom HTML snippets. These only respect "
        "consent if each tag declares <code>consent_settings</code> in the container."
        "</div>"
        "</div>"
    )
    return (
        "### Context\n\n"
        "## What Advanced Consent Mode does — and what it doesn't\n\n"
        f'<div style="display:flex; gap:18px; margin-top:16px;">{covered}{not_covered}</div>\n\n'
        '<div style="margin-top:24px; color:var(--body); font-size:0.78em; line-height:1.7;">'
        "Effective <strong>June 15, 2026</strong>, Google Ads will rely solely on "
        "<code>ad_storage</code>. Cleaner policy, but it does nothing for the "
        "non-Google tags &mdash; those have always been, and remain, the operator's responsibility."
        "</div>"
    )


def _slide_next_steps(result: AuditResult) -> str:
    violations = result.summary.violations
    if violations == 0:
        headline = "Static audit clean &mdash; recommend a live audit to confirm runtime behavior"
    else:
        headline = f"{violations} static violations &mdash; confirm runtime exposure with a live audit"

    def step(idx: str, edge: str, title: str, body: str) -> str:
        return (
            '<div class="card" style="flex:1;">'
            f'<div class="edge {edge}"></div>'
            f'<div style="font-family:\'Outfit\'; font-size:0.5em; color:var(--m); letter-spacing:0.15em; text-transform:uppercase; margin-bottom:10px;">{idx}. {title}</div>'
            f'<div style="color:var(--body); font-size:0.76em; line-height:1.6;">{body}</div>'
            "</div>"
        )

    cards = (
        step(
            "1",
            "",
            "Triage",
            "Open the CSV export. Sort by <code>verdict</code>. Every row marked "
            "<strong>missing_consent_config</strong> is a candidate for removal, "
            "replacement with a Google-native tag, or addition of explicit "
            "<code>consent_settings</code>.",
        )
        + step(
            "2",
            "y",
            "Verify wiring",
            "Static analysis cannot see whether the CMP actually forwards "
            "<code>update</code> calls to the container at runtime, or what GCS "
            "state appears on network requests after denial. A live audit "
            "closes that gap.",
        )
        + step(
            "3",
            "g",
            "Gate the next tag",
            "Add <code>como-tag-audit</code> to CI against the production container. "
            "Exit code <code>1</code> on new violations &mdash; catch the problem "
            "when it is small.",
        )
    )

    cta = (
        '<div style="margin-top:28px; text-align:center;">'
        '<a href="https://kennethjbuchanan.com/audit#get-audit" '
        'style="color:var(--a); text-decoration:none; font-family:\'Outfit\'; '
        "font-weight:600; font-size:0.9em; border:1px solid var(--a); "
        'padding:10px 22px; border-radius:6px; display:inline-block;">'
        "Book the full audit &rarr;"
        "</a>"
        "</div>"
    )

    return (
        "### Next steps\n\n"
        f"## {headline}\n\n"
        f'<div style="display:flex; gap:14px; margin-top:18px;">{cards}</div>\n\n'
        f"{cta}"
    )


def _slide_colophon(audited_at: datetime) -> str:
    return f"""
<!-- _class: lead -->
<!-- _paginate: false -->
<!-- _footer: '' -->

### Generated by

# como-tag-audit

<div style="color:var(--body); font-family:'Raleway'; font-weight:100; font-size:0.9em; margin-top:12px; max-width:600px; text-align:center;">
Static Consent Mode audit for GTM containers.
Open source, <code>pip install</code>-able, CI-ready.
</div>

<div style="margin-top:30px; font-family:'Outfit'; font-size:0.7em; color:var(--label); letter-spacing:0.12em;">
github.com/kb223/como-tag-audit &nbsp;·&nbsp; {audited_at.strftime('%Y-%m-%d')}
</div>
""".strip()


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------


def render_deck(
    result: AuditResult,
    *,
    audited_at: datetime | None = None,
) -> str:
    """Return a full Marp deck as a markdown string."""
    ts = audited_at or datetime.now(timezone.utc)
    domain = _domain(result.source_ref)

    slides = [
        _slide_cover(result, ts),
        _slide_summary(result),
        _slide_composition(result),
        _slide_cmp_status(result),
        _slide_top_offenders(result),
        _slide_violation_sample(result),
        _slide_context(),
        _slide_next_steps(result),
        _slide_colophon(ts),
    ]
    body = "\n\n---\n\n".join(s for s in slides if s)
    return _frontmatter(domain, ts) + "\n" + body + "\n"
