"""Tests for tools/contact_extractor.py — phone, social media, contact page discovery."""

import pytest

from tools.contact_extractor import (
    discover_contact_pages,
    extract_phone_numbers,
    extract_social_media,
    merge_contact_info,
    sanitize_phone_list,
)


# ── Phone number extraction ────────────────────────────────────────────


class TestExtractPhoneNumbers:
    def test_international_format(self):
        text = "Call us at +49 30 12345678 or +1 (555) 123-4567"
        phones = extract_phone_numbers(text)
        assert len(phones) >= 2

    def test_local_format(self):
        text = "Phone: (555) 123-4567"
        phones = extract_phone_numbers(text)
        assert len(phones) >= 1

    def test_chinese_format(self):
        text = "联系电话: +86-10-12345678"
        phones = extract_phone_numbers(text)
        assert len(phones) >= 1

    def test_no_phones(self):
        text = "This text has no phone numbers at all."
        phones = extract_phone_numbers(text)
        assert phones == []

    def test_deduplication(self):
        text = "Call +49 30 12345678 or +49 30 12345678 again"
        phones = extract_phone_numbers(text)
        assert len(phones) == 1

    def test_year_not_matched(self):
        text = "Founded in 2024 and established in 1998"
        phones = extract_phone_numbers(text)
        # Years should not be matched as phone numbers
        for p in phones:
            digits = "".join(c for c in p if c.isdigit())
            assert len(digits) >= 7

    def test_gps_coordinate_rejected(self):
        text = "Location: 10.397715, 63.3888663"
        phones = extract_phone_numbers(text)
        assert phones == []

    def test_all_zeros_rejected(self):
        text = "Phone: (515) 000-0000"
        phones = extract_phone_numbers(text)
        assert phones == []

    def test_all_same_digit_rejected(self):
        text = "Call: +1 111-111-1111"
        phones = extract_phone_numbers(text)
        assert phones == []

    def test_iso_standard_number_rejected(self):
        text = "Certified ISO 27001-2022 and 9001-2015"
        phones = extract_phone_numbers(text)
        assert phones == []

    def test_valid_us_number(self):
        text = "Call us at (703) 848-7947"
        phones = extract_phone_numbers(text)
        assert len(phones) == 1

    def test_valid_german_number(self):
        text = "Tel: +49 30 12345678"
        phones = extract_phone_numbers(text)
        assert len(phones) == 1

    def test_dedup_same_number_different_formats(self):
        text = "(703) 848-7947 and 703-848-7947 and 703.848.7947"
        phones = extract_phone_numbers(text)
        assert len(phones) == 1

    def test_cap_at_max_per_lead(self):
        text = " ".join(
            f"+49 30 1234{i:04d}" for i in range(20)
        )
        phones = extract_phone_numbers(text)
        assert len(phones) <= 10

    def test_starts_with_000_rejected(self):
        text = "Fax: 00012345678"
        phones = extract_phone_numbers(text)
        assert phones == []


class TestSanitizePhoneList:
    def test_removes_invalid(self):
        phones = ["00000000", "10.397715", "27001-2022", "+49 30 12345678"]
        result = sanitize_phone_list(phones)
        assert result == ["+49 30 12345678"]

    def test_deduplicates(self):
        phones = ["+49 30 12345678", "+49-30-12345678", "004930 12345678"]
        result = sanitize_phone_list(phones)
        assert len(result) == 1

    def test_caps_at_10(self):
        phones = [f"+49 30 1234{i:04d}" for i in range(20)]
        result = sanitize_phone_list(phones)
        assert len(result) == 10

    def test_empty_list(self):
        assert sanitize_phone_list([]) == []

    def test_non_string_skipped(self):
        phones = [123456789, None, "+49 30 12345678"]
        result = sanitize_phone_list(phones)
        assert len(result) == 1

    def test_gps_rejected(self):
        assert sanitize_phone_list(["63.3888663", "10.397715"]) == []

    def test_all_zeros_rejected(self):
        assert sanitize_phone_list(["00000000"]) == []


# ── Social media extraction ────────────────────────────────────────────


class TestExtractSocialMedia:
    def test_linkedin_company(self):
        text = 'Visit us at https://www.linkedin.com/company/solartech-gmbh/'
        social = extract_social_media(text)
        assert "linkedin" in social
        assert "solartech-gmbh" in social["linkedin"]

    def test_facebook(self):
        text = 'Follow us: https://www.facebook.com/solartechgmbh'
        social = extract_social_media(text)
        assert "facebook" in social

    def test_twitter_x(self):
        text = 'Tweet us: https://x.com/solartech'
        social = extract_social_media(text)
        assert "twitter" in social

    def test_instagram(self):
        text = 'IG: https://www.instagram.com/solartech_official'
        social = extract_social_media(text)
        assert "instagram" in social

    def test_youtube_channel(self):
        text = 'Subscribe: https://www.youtube.com/@SolarTechOfficial'
        social = extract_social_media(text)
        assert "youtube" in social

    def test_whatsapp(self):
        text = 'WhatsApp: https://wa.me/4912345678'
        social = extract_social_media(text)
        assert "whatsapp" in social

    def test_multiple_platforms(self):
        text = """
        LinkedIn: https://www.linkedin.com/company/acme-corp
        Facebook: https://www.facebook.com/acmecorp
        Twitter: https://twitter.com/acmecorp
        """
        social = extract_social_media(text)
        assert len(social) >= 3

    def test_skip_share_links(self):
        text = 'Share: https://www.facebook.com/sharer/sharer.php?u=example.com'
        social = extract_social_media(text)
        assert "facebook" not in social

    def test_no_social(self):
        text = "This company has no social media presence listed."
        social = extract_social_media(text)
        assert social == {}


# ── Contact page discovery ─────────────────────────────────────────────


class TestDiscoverContactPages:
    def test_html_href_contact(self):
        html = '<a href="/contact">Contact Us</a>'
        urls = discover_contact_pages(html, "https://example.com")
        assert len(urls) == 1
        assert urls[0] == "https://example.com/contact"

    def test_html_href_about(self):
        html = '<a href="/about-us">About</a>'
        urls = discover_contact_pages(html, "https://example.com")
        assert len(urls) == 1
        assert urls[0] == "https://example.com/about-us"

    def test_markdown_link(self):
        md = "[Contact Us](/contact)"
        urls = discover_contact_pages(md, "https://example.com")
        assert len(urls) == 1

    def test_impressum(self):
        html = '<a href="/impressum">Impressum</a>'
        urls = discover_contact_pages(html, "https://example.com")
        assert len(urls) == 1

    def test_skip_external_links(self):
        html = '<a href="https://other-site.com/contact">Contact</a>'
        urls = discover_contact_pages(html, "https://example.com")
        assert len(urls) == 0

    def test_max_3_pages(self):
        html = """
        <a href="/contact">Contact</a>
        <a href="/about">About</a>
        <a href="/about-us">About Us</a>
        <a href="/team">Team</a>
        <a href="/impressum">Impressum</a>
        """
        urls = discover_contact_pages(html, "https://example.com")
        assert len(urls) <= 3

    def test_no_contact_pages(self):
        html = '<a href="/products">Products</a><a href="/blog">Blog</a>'
        urls = discover_contact_pages(html, "https://example.com")
        assert len(urls) == 0

    def test_deduplication(self):
        html = """
        <a href="/contact">Contact</a>
        <a href="/contact">Contact Us</a>
        """
        urls = discover_contact_pages(html, "https://example.com")
        assert len(urls) == 1


# ── Merge contact info ─────────────────────────────────────────────────


class TestMergeContactInfo:
    def test_merge_emails(self):
        base = {"emails": ["a@test.com"]}
        result = merge_contact_info(base, extra_emails=["b@test.com", "a@test.com"], extra_phones=[], extra_social={})
        assert len(result["emails"]) == 2
        assert "b@test.com" in result["emails"]

    def test_merge_phones(self):
        base = {"phone_numbers": ["+49 30 12345678"]}
        result = merge_contact_info(base, extra_emails=[], extra_phones=["+1 555 1234567"], extra_social={})
        assert len(result["phone_numbers"]) == 2

    def test_merge_phones_dedup(self):
        base = {"phone_numbers": ["+49 30 12345678"]}
        result = merge_contact_info(base, extra_emails=[], extra_phones=["+49-30-12345678"], extra_social={})
        # Same digits, should not duplicate
        assert len(result["phone_numbers"]) == 1

    def test_merge_social(self):
        base = {"social_media": {"linkedin": "https://linkedin.com/company/a"}}
        result = merge_contact_info(
            base, extra_emails=[], extra_phones=[],
            extra_social={"facebook": "https://facebook.com/a", "linkedin": "https://linkedin.com/company/b"},
        )
        # LinkedIn should not be overwritten
        assert result["social_media"]["linkedin"] == "https://linkedin.com/company/a"
        assert result["social_media"]["facebook"] == "https://facebook.com/a"

    def test_merge_address_prefer_longer(self):
        base = {"address": "Berlin"}
        result = merge_contact_info(
            base, extra_emails=[], extra_phones=[], extra_social={},
            extra_address="Musterstraße 1, 10115 Berlin, Germany",
        )
        assert "Musterstraße" in result["address"]

    def test_merge_empty_base(self):
        base = {}
        result = merge_contact_info(
            base,
            extra_emails=["a@test.com"],
            extra_phones=["+49 30 12345678"],
            extra_social={"linkedin": "https://linkedin.com/company/a"},
            extra_address="Berlin",
        )
        assert len(result["emails"]) == 1
        assert len(result["phone_numbers"]) == 1
        assert "linkedin" in result["social_media"]
        assert result["address"] == "Berlin"
