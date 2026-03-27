"""Contact information extraction from web page content.

Extracts:
- Phone numbers (international formats)
- Social media profile URLs (LinkedIn, Facebook, Twitter/X, Instagram, YouTube, WhatsApp)
- Contact/About page URLs for deep scraping
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse


# ── Phone number extraction ────────────────────────────────────────────

# Matches international phone formats:
#   +1 (555) 123-4567, +49 30 12345678, +86-10-12345678,
#   (555) 123-4567, 555-123-4567, 010-12345678
# Requires at least one separator (space/dash/dot/parens) to avoid matching
# plain integers embedded in text.
_PHONE_REGEX = re.compile(
    r"""(?<!\d)(?<!\.)             # no digit or decimal point before
    (?:
        \+\d{1,3}                  # international prefix +1, +49, +86 etc.
        [\s.\-]
    |
        \(\d{2,4}\)                # area code in parens: (555), (030)
        [\s.\-]?
    |
        \d{2,4}[\s\-]\d            # bare area code followed by separator then digit
    )
    [\d\s.\-\(\)]{5,20}           # rest of number
    (?!\d)(?!\.)                   # no digit or decimal point after
    """,
    re.VERBOSE,
)

_PHONE_MIN_DIGITS = 7
_PHONE_MAX_DIGITS = 15
_PHONE_MAX_PER_LEAD = 10


def _normalize_phone_digits(raw: str) -> str:
    """Return canonical digit string for deduplication.

    Strips leading 00 (IDD prefix) so that +4930... and 004930... are treated
    as the same number.  Also strips a single leading + sign before extracting.
    """
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("00"):
        digits = digits[2:]
    return digits


def _is_valid_phone(raw: str) -> bool:
    """Return True if raw string looks like a real phone number."""
    digits = _normalize_phone_digits(raw)
    n = len(digits)

    # Must have 7–15 digits (E.164 max is 15)
    if n < _PHONE_MIN_DIGITS or n > _PHONE_MAX_DIGITS:
        return False

    # Reject if the original text contains a decimal point (GPS / float)
    if re.search(r"\d\.\d", raw):
        return False

    # Reject all-same-digit strings: 00000000, 11111111, 99999999
    if len(set(digits)) == 1:
        return False

    # Reject if > 60% of digits are the same (e.g. 0001234000)
    most_common_count = max(digits.count(d) for d in set(digits))
    if most_common_count / n > 0.6:
        return False

    # Reject plain years: 1900-2099
    if re.match(r"^(19|20)\d{2}$", digits):
        return False

    # Reject ISO standard / date range patterns like "27001-2022", "9001-2015"
    # These look like NNNN-YYYY where YYYY is a year
    if re.match(r"^\d{4,6}(19|20)\d{2}$", digits):
        return False

    # Reject strings that look like version numbers: only 1–2 digit groups
    # e.g. "3.14", "10.2" — already caught by decimal check above, but belt+suspenders
    if re.match(r"^\d{1,3}$", digits):
        return False

    # Reject numbers that start with 000 (clearly invalid)
    if digits.startswith("000"):
        return False

    return True


def extract_phone_numbers(text: str) -> list[str]:
    """Extract unique, validated phone numbers from text.

    Filters out: GPS coordinates, all-zero strings, ISO standard numbers,
    year ranges, version numbers, and other non-phone digit sequences.
    Deduplicates by normalized digit string. Caps at _PHONE_MAX_PER_LEAD.
    """
    candidates = _PHONE_REGEX.findall(text)
    seen: set[str] = set()
    result: list[str] = []

    for raw in candidates:
        cleaned = raw.strip()
        if not _is_valid_phone(cleaned):
            continue
        digits = _normalize_phone_digits(cleaned)
        if digits not in seen:
            seen.add(digits)
            result.append(cleaned)
        if len(result) >= _PHONE_MAX_PER_LEAD:
            break

    return result


def sanitize_phone_list(phones: list[str]) -> list[str]:
    """Validate and deduplicate a list of phone strings (e.g. from LLM output).

    Use this to clean phone_numbers lists returned by the LLM before storing.
    """
    seen: set[str] = set()
    result: list[str] = []
    for raw in phones:
        if not isinstance(raw, str):
            continue
        cleaned = raw.strip()
        if not _is_valid_phone(cleaned):
            continue
        digits = _normalize_phone_digits(cleaned)
        if digits not in seen:
            seen.add(digits)
            result.append(cleaned)
        if len(result) >= _PHONE_MAX_PER_LEAD:
            break
    return result


# ── Social media URL extraction ────────────────────────────────────────

_SOCIAL_PATTERNS: dict[str, re.Pattern] = {
    "linkedin": re.compile(
        r"https?://(?:www\.)?linkedin\.com/(?:company|in)/[a-zA-Z0-9\-_.%]+/?",
        re.IGNORECASE,
    ),
    "facebook": re.compile(
        r"https?://(?:www\.)?facebook\.com/[a-zA-Z0-9.\-]+/?",
        re.IGNORECASE,
    ),
    "twitter": re.compile(
        r"https?://(?:www\.)?(?:twitter\.com|x\.com)/[a-zA-Z0-9_]+/?",
        re.IGNORECASE,
    ),
    "instagram": re.compile(
        r"https?://(?:www\.)?instagram\.com/[a-zA-Z0-9_.]+/?",
        re.IGNORECASE,
    ),
    "youtube": re.compile(
        r"https?://(?:www\.)?youtube\.com/(?:@|channel/|c/)[a-zA-Z0-9\-_.]+/?",
        re.IGNORECASE,
    ),
    "whatsapp": re.compile(
        r"https?://(?:wa\.me|api\.whatsapp\.com|chat\.whatsapp\.com)/[a-zA-Z0-9+]+/?",
        re.IGNORECASE,
    ),
    "wechat": re.compile(
        r"https?://(?:weixin\.qq\.com|mp\.weixin\.qq\.com)/[^\s\"'<>]+",
        re.IGNORECASE,
    ),
}

# Blacklist patterns — skip generic/share links
_SOCIAL_BLACKLIST = re.compile(
    r"(?:sharer|share|intent/tweet|dialog/share|plugins|embed|watch\?)",
    re.IGNORECASE,
)


def extract_social_media(text: str) -> dict[str, str]:
    """Extract social media profile URLs from text.

    Returns:
        Dict keyed by platform name, e.g. {"linkedin": "https://...", "facebook": "https://..."}
        Only the first URL per platform is kept.
    """
    result: dict[str, str] = {}

    for platform, pattern in _SOCIAL_PATTERNS.items():
        matches = pattern.findall(text)
        for url in matches:
            # Skip share/embed links
            if _SOCIAL_BLACKLIST.search(url):
                continue
            result[platform] = url.rstrip("/")
            break  # first valid match per platform

    return result


# ── Contact page URL discovery ─────────────────────────────────────────

_CONTACT_PAGE_PATTERNS = re.compile(
    r"""(?:href|src)\s*=\s*["']([^"']*?)["']""",
    re.IGNORECASE,
)

_CONTACT_PATH_KEYWORDS = {
    "contact", "kontakt", "contacto", "contato", "contatti",
    "about", "about-us", "about_us", "ueber-uns", "uber-uns",
    "impressum", "imprint", "legal-notice",
    "company", "team", "our-team",
    "lianxi", "guanyu",  # Chinese pinyin for 联系/关于
}


def discover_contact_pages(html_text: str, base_url: str) -> list[str]:
    """Find contact/about page URLs from page content.

    Looks for href links whose path contains contact-related keywords.

    Args:
        html_text: Raw page content (HTML or Markdown with links).
        base_url: The base URL for resolving relative links.

    Returns:
        List of absolute URLs to contact/about pages (deduplicated, max 3).
    """
    # Also match Markdown-style links: [text](url)
    md_links = re.findall(r"\[([^\]]*)\]\(([^)]+)\)", html_text)
    href_links = _CONTACT_PAGE_PATTERNS.findall(html_text)

    all_links = href_links + [url for _, url in md_links]

    seen: set[str] = set()
    result: list[str] = []

    base_domain = urlparse(base_url).netloc

    for link in all_links:
        link = link.strip()
        if not link or link.startswith("#") or link.startswith("javascript:"):
            continue

        # Resolve relative URLs
        absolute = urljoin(base_url, link)
        parsed = urlparse(absolute)

        # Must be same domain
        if parsed.netloc != base_domain:
            continue

        # Check if path contains contact-related keywords
        path_lower = parsed.path.lower().strip("/")
        path_parts = set(path_lower.replace("_", "-").split("/"))

        if path_parts & _CONTACT_PATH_KEYWORDS:
            if absolute not in seen:
                seen.add(absolute)
                result.append(absolute)
                if len(result) >= 3:
                    break

    return result


def merge_contact_info(
    base: dict,
    extra_emails: list[str],
    extra_phones: list[str],
    extra_social: dict[str, str],
    extra_address: str = "",
) -> dict:
    """Merge additional contact info into an existing lead dict.

    Deduplicates emails and phones. Social media entries are added
    only if the platform key doesn't already exist.
    """
    # Merge emails
    existing_emails = set(e.lower() for e in base.get("emails", []))
    for email in extra_emails:
        if email.lower() not in existing_emails:
            base.setdefault("emails", []).append(email)
            existing_emails.add(email.lower())

    # Merge phones
    existing_phones_digits = set(
        re.sub(r"\D", "", p) for p in base.get("phone_numbers", [])
    )
    for phone in extra_phones:
        digits = re.sub(r"\D", "", phone)
        if digits not in existing_phones_digits:
            base.setdefault("phone_numbers", []).append(phone)
            existing_phones_digits.add(digits)

    # Merge social media (don't overwrite existing)
    existing_social = base.get("social_media", {})
    for platform, url in extra_social.items():
        if platform not in existing_social:
            existing_social[platform] = url
    base["social_media"] = existing_social

    # Merge address (prefer longer / non-empty)
    if extra_address and len(extra_address) > len(base.get("address", "")):
        base["address"] = extra_address

    return base
