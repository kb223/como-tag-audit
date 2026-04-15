"""Parse a GTM container JS body into classified tag entries.

This module is a focused extraction of the GTM container parser from the
RSC consent-compliance-agent (tool_01). It exists as its own package so
other auditors and learners can reuse it without pulling in the full
forensic audit pipeline.

Domain rule (Advanced Consent Mode):
    Advanced Consent Mode only applies to Google's own tag types. A
    non-Google tag (Custom HTML, Custom Image, vendor pixel) with no
    consent settings fires regardless of user consent state — a
    confirmed violation.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from como_tag_audit.models import TagEntry, Verdict
from como_tag_audit.vendors import lookup_vendor

_log = logging.getLogger(__name__)

# GTM function codes for Google-owned tags. These are covered by Advanced
# Consent Mode (cookieless pings in denied state) even without explicit
# consent_settings on the tag itself.
GOOGLE_TAG_TYPES: frozenset[str] = frozenset(
    {
        "__ua",        # Universal Analytics
        "__ga4",       # GA4 Config
        "__ga4event",  # GA4 Event
        "__gaawe",     # Google Ads Enhanced Conversions for Web
        "__flc",       # Floodlight Counter
        "__flsd",      # Floodlight Sales
        "__awct",      # Google Ads Conversion
        "__awdc",      # Google Ads Dynamic Conversion
        "__awud",      # Google Ads User Data / Remarketing
        "__gclidw",    # Google Ads Remarketing
        "__googtag",   # Google Tag (gtag.js)
        "__sp",        # Google Surveys
        "__cvt",       # Conversion Linker
        "__tg",        # Google Tag Gateway / templated Google tag
        "__asp",       # AdSense for Search (Google)
        "__asr",       # AdSense Related (Google)
        # Some GTM builds drop the double underscore.
        "ua", "ga4", "ga4event", "gaawe", "flc", "flsd",
        "awct", "awdc", "awud", "gclidw", "googtag", "sp", "cvt", "tg",
    }
)

# Google-owned ``__cvt_<id>`` variants are generated per-container. We
# match by prefix, not by exact string — see ``_is_google_tag``.
_GOOGLE_TAG_PREFIXES: tuple[str, ...] = ("__cvt_",)

# GTM built-in listeners / triggers. They appear in the ``tags`` array
# but they do not send network requests — they register DOM event
# handlers that, in turn, fire other tags. Counting them as consent
# violations would be a false positive.
#
# ``__paused`` is also excluded: GTM replaces a paused tag's function
# code with ``__paused`` so the runtime skips it. A paused tag cannot
# fire and therefore cannot violate consent.
GTM_BUILTIN_LISTENERS: frozenset[str] = frozenset(
    {
        "__cl",      # Click listener
        "__ccl",     # Core click listener
        "__lcl",     # Link click listener
        "__fsl",     # Form submit listener
        "__hl",      # History change listener
        "__sdl",     # Scroll depth listener
        "__ytl",     # YouTube video listener
        "__evl",     # Element visibility listener
        "__tl",      # Timer listener
        "__jel",     # JavaScript error listener
        "__tpm",     # Tag pause metric
        "__paused",  # Paused tag — does not fire
    }
)


def _is_google_tag(function_code: str) -> bool:
    if function_code in GOOGLE_TAG_TYPES:
        return True
    return any(function_code.startswith(prefix) for prefix in _GOOGLE_TAG_PREFIXES)

# Two shapes of container embedding are seen in the wild:
#   1. Parenthesized: ``({"resource":{...}})`` — classic, also what you see
#      when a browser intercepts the runtime.
# 2. Assigned: ``var data = {\n"resource": {...}`` — current static
#      shape served by googletagmanager.com.
_CONTAINER_OPEN_RES: tuple[re.Pattern[str], ...] = (
    re.compile(r'\(\s*\{\s*"resource"\s*:', re.DOTALL),
    re.compile(r'=\s*\{\s*"resource"\s*:', re.DOTALL),
)
_CONSENT_INIT_RE = re.compile(r"gtag\(\s*['\"]consent['\"]\s*,\s*['\"]default['\"]")


def extract_container_json(js_body: str) -> dict[str, Any] | None:
    """Pull the embedded container JSON out of a ``gtm.js`` response body.

    GTM embeds its container data either as ``({"resource":{...}})`` or
    as ``var data = {"resource":{...}}``. We locate the opening brace of
    the outer object and walk the string counting depth to find the
    matching close — brace-counting is more reliable than regexing
    minified JS that may contain ``}`` inside string literals.

    Returns ``None`` if no recognized shape is found or the JSON fails
    to parse.
    """
    start: int | None = None
    for pattern in _CONTAINER_OPEN_RES:
        match = pattern.search(js_body)
        if match:
            # Find the '{' inside the matched prefix.
            start = js_body.index("{", match.start())
            break
    if start is None:
        return None

    depth = 0
    for i in range(start, len(js_body)):
        ch = js_body[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    result: dict[str, Any] = json.loads(js_body[start : i + 1])
                except json.JSONDecodeError:
                    return None
                return result
    return None


def detects_consent_mode_init(js_body: str) -> bool:
    """Heuristic: does this gtm.js contain a Consent Mode default call?"""
    return bool(_CONSENT_INIT_RE.search(js_body))


def _classify_tag(tag: dict[str, Any]) -> TagEntry | None:
    func = str(tag.get("function", ""))
    tag_id = int(tag.get("tag_id", 0))
    tag_name = tag.get("instance_name") or func

    # Built-in listeners don't fire network requests — exclude from audit.
    if func in GTM_BUILTIN_LISTENERS:
        return None

    is_google = _is_google_tag(func)
    consent_settings = tag.get("consent_settings")
    vendor = lookup_vendor(func, tag_name)

    if consent_settings:
        consent_val = int(consent_settings.get("consent", 0))
        consent_types = tuple(
            cm_entry["string"]
            for cm_entry in consent_settings.get("cm", [])
            if isinstance(cm_entry, dict)
            and cm_entry.get("type") == 0
            and cm_entry.get("string")
        )
        if consent_val >= 2:
            verdict = Verdict.OK
            reason = "Consent required and declared."
        else:
            verdict = Verdict.OPTIONAL_CONSENT
            reason = "Consent declared but not required — tag may fire when denied."
    else:
        consent_types = ()
        if is_google:
            verdict = Verdict.OK
            reason = "Google tag — covered by Advanced Consent Mode."
        else:
            verdict = Verdict.MISSING_CONSENT_CONFIG
            reason = (
                "Non-Google tag with no consent settings. Fires regardless "
                "of user consent state."
            )

    return TagEntry(
        tag_id=tag_id,
        tag_name=str(tag_name),
        tag_type=func,
        is_google_tag=is_google,
        vendor=vendor,
        consent_types=consent_types,
        verdict=verdict,
        reason=reason,
    )


def parse_container(gtm_js: str) -> list[TagEntry]:
    """Parse a ``gtm.js`` body into a list of classified tag entries.

    Returns an empty list if the body cannot be parsed. Never raises —
    a missing or malformed container is a finding, not an error.
    """
    if not gtm_js:
        return []

    try:
        container = extract_container_json(gtm_js)
    except Exception:
        _log.warning("GTM container JSON extraction failed", exc_info=True)
        return []

    if not container:
        return []

    tags = container.get("resource", {}).get("tags", [])
    if not isinstance(tags, list):
        return []

    out: list[TagEntry] = []
    for tag in tags:
        if not isinstance(tag, dict):
            continue
        try:
            entry = _classify_tag(tag)
        except Exception:
            _log.debug("Skipping unparseable tag: %s", tag)
            continue
        if entry is not None:
            out.append(entry)
    return out
