"""Best-effort vendor lookup for GTM tag function codes and names.

This is a curated starter list. The full RSC audit uses the Open Cookie
Database (3,200+ entries) plus a legally-annotated custom library; the
subset here covers the most common tags seen on Ecommerce properties.
"""

from __future__ import annotations

# GTM function code → vendor display name.
_BY_FUNCTION: dict[str, str] = {
    "__ua": "Google Analytics (Universal)",
    "__ga4": "Google Analytics 4",
    "__ga4event": "Google Analytics 4",
    "__googtag": "Google Tag",
    "__awct": "Google Ads",
    "__awdc": "Google Ads",
    "__awud": "Google Ads",
    "__gaawe": "Google Ads",
    "__gclidw": "Google Ads",
    "__flc": "Google Floodlight",
    "__flsd": "Google Floodlight",
    "__cvt": "Google Conversion Linker",
    "__tg": "Google Tag",
    "__sp": "Google Surveys",
    "__asp": "Google AdSense",
    "__asr": "Google AdSense",
    "__baut": "Microsoft Advertising (Bing UET)",
    "__bzi": "LinkedIn Insight",
}

# Substring → vendor (matched against tag name or custom HTML function
# names). Checked only when function code lookup misses. Order matters
# for overlap: more specific entries come first.
_BY_NAME_SUBSTRING: tuple[tuple[str, str], ...] = (
    ("facebook", "Meta / Facebook"),
    ("meta pixel", "Meta / Facebook"),
    ("fbq", "Meta / Facebook"),
    ("tiktok", "TikTok"),
    ("ttq", "TikTok"),
    ("pinterest", "Pinterest"),
    ("pintrk", "Pinterest"),
    ("snapchat", "Snap"),
    ("snap pixel", "Snap"),
    ("reddit", "Reddit"),
    ("rdt", "Reddit"),
    ("linkedin", "LinkedIn"),
    ("lintrk", "LinkedIn"),
    ("twitter", "X / Twitter"),
    ("twq", "X / Twitter"),
    ("hotjar", "Hotjar"),
    ("clarity", "Microsoft Clarity"),
    ("bing", "Microsoft Advertising"),
    ("uetq", "Microsoft Advertising"),
    ("klaviyo", "Klaviyo"),
    ("attentive", "Attentive"),
    ("postscript", "Postscript"),
    ("criteo", "Criteo"),
    ("taboola", "Taboola"),
    ("outbrain", "Outbrain"),
    ("mixpanel", "Mixpanel"),
    ("segment", "Segment"),
    ("amplitude", "Amplitude"),
    ("heap", "Heap"),
    ("fullstory", "FullStory"),
    ("intercom", "Intercom"),
    ("drift", "Drift"),
    ("gorgias", "Gorgias"),
    ("zendesk", "Zendesk"),
    ("yotpo", "Yotpo"),
    ("trustpilot", "Trustpilot"),
    ("bazaarvoice", "Bazaarvoice"),
    ("rakuten", "Rakuten"),
    ("impact", "Impact"),
    ("awin", "Awin"),
    ("commission junction", "Commission Junction"),
    ("cj affiliate", "Commission Junction"),
)


def lookup_vendor(function_code: str, tag_name: str) -> str | None:
    """Return a vendor display name for a GTM tag, or ``None`` if unknown."""
    if function_code in _BY_FUNCTION:
        return _BY_FUNCTION[function_code]
    haystack = f"{tag_name} {function_code}".lower()
    for needle, vendor in _BY_NAME_SUBSTRING:
        if needle in haystack:
            return vendor
    return None
