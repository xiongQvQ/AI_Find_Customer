"""Tests for tools/url_filter.py — URL classification (minimal filtering)."""

import pytest

from tools.url_filter import (
    classify_search_results,
    classify_url,
    extract_linkedin_company_slug,
    filter_search_results,
    slug_to_company_name,
)


class TestClassifyUrl:
    # ── Company sites ────────────────────────────────────────────────────
    def test_company_site(self):
        assert classify_url("https://www.solartech.de") == "company_site"
        assert classify_url("https://acme-corp.com/products") == "company_site"

    def test_company_site_with_blog_path(self):
        # Blog on a company domain is still a company_site (no path filtering)
        assert classify_url("https://acme-corp.com/blog/post") == "company_site"

    def test_company_site_with_news_path(self):
        assert classify_url("https://acme-corp.com/news/latest") == "company_site"

    # ── Content pages (articles, blogs, social, directories) ─────────────
    def test_content_news(self):
        assert classify_url("https://www.reuters.com/article/some-news") == "content_page"
        assert classify_url("https://techcrunch.com/2024/01/startup") == "content_page"

    def test_content_social(self):
        assert classify_url("https://twitter.com/someuser") == "content_page"
        assert classify_url("https://www.reddit.com/r/business") == "content_page"

    def test_content_youtube(self):
        assert classify_url("https://youtube.com/watch?v=123") == "content_page"

    def test_content_wikipedia(self):
        assert classify_url("https://en.wikipedia.org/wiki/Solar_panel") == "content_page"

    def test_content_facebook(self):
        assert classify_url("https://facebook.com/acme-corp") == "content_page"

    def test_content_medium(self):
        assert classify_url("https://medium.com/@author/top-suppliers") == "content_page"

    def test_content_crunchbase(self):
        assert classify_url("https://www.crunchbase.com/organization/acme") == "content_page"

    def test_content_glassdoor(self):
        assert classify_url("https://www.glassdoor.com/Reviews/acme") == "content_page"

    def test_content_subdomain(self):
        assert classify_url("https://news.bbc.com/article/123") == "content_page"

    # ── LinkedIn company pages ───────────────────────────────────────────
    def test_linkedin_company(self):
        assert classify_url("https://linkedin.com/company/acme-corp") == "linkedin_company"
        assert classify_url("https://ca.linkedin.com/company/itc-electrical-components") == "linkedin_company"
        assert classify_url("https://www.linkedin.com/company/some-company") == "linkedin_company"

    def test_linkedin_non_company(self):
        # LinkedIn profile (not company) → content_page
        assert classify_url("https://linkedin.com/in/john-doe") == "content_page"

    # ── Platform listings ────────────────────────────────────────────────
    def test_platform_listing(self):
        assert classify_url("https://www.alibaba.com/product/solar-panel") == "platform_listing"
        assert classify_url("https://europages.com/company/acme") == "platform_listing"
        assert classify_url("https://www.thomasnet.com/profile/12345") == "platform_listing"

    # ── Truly irrelevant ─────────────────────────────────────────────────
    def test_irrelevant_search_engines(self):
        assert classify_url("https://www.google.com/search?q=test") == "irrelevant"
        assert classify_url("https://bing.com/search?q=test") == "irrelevant"
        assert classify_url("https://duckduckgo.com/?q=test") == "irrelevant"

    def test_irrelevant_entertainment(self):
        assert classify_url("https://tiktok.com/@user") == "irrelevant"
        assert classify_url("https://spotify.com/track/123") == "irrelevant"
        assert classify_url("https://netflix.com/title/123") == "irrelevant"

    def test_irrelevant_empty_url(self):
        assert classify_url("") == "irrelevant"

    def test_irrelevant_no_domain(self):
        assert classify_url("not-a-url") == "irrelevant"


class TestExtractLinkedinCompanySlug:
    def test_standard_url(self):
        assert extract_linkedin_company_slug(
            "https://linkedin.com/company/acme-corp"
        ) == "acme-corp"

    def test_country_subdomain(self):
        assert extract_linkedin_company_slug(
            "https://ca.linkedin.com/company/itc-electrical-components"
        ) == "itc-electrical-components"

    def test_www_prefix(self):
        assert extract_linkedin_company_slug(
            "https://www.linkedin.com/company/some-company"
        ) == "some-company"

    def test_with_trailing_slash(self):
        assert extract_linkedin_company_slug(
            "https://linkedin.com/company/acme-corp/"
        ) == "acme-corp"

    def test_non_company_url(self):
        assert extract_linkedin_company_slug(
            "https://linkedin.com/in/john-doe"
        ) is None

    def test_non_linkedin_url(self):
        assert extract_linkedin_company_slug(
            "https://example.com/company/acme"
        ) is None


class TestSlugToCompanyName:
    def test_hyphen_slug(self):
        assert slug_to_company_name("itc-electrical-components") == "itc electrical components"

    def test_underscore_slug(self):
        assert slug_to_company_name("acme_corp_inc") == "acme corp inc"

    def test_mixed_slug(self):
        assert slug_to_company_name("my-company_name") == "my company name"

    def test_simple_slug(self):
        assert slug_to_company_name("acme") == "acme"


class TestClassifySearchResults:
    def test_all_categories(self):
        results = [
            {"link": "https://www.solartech.de"},
            {"link": "https://linkedin.com/company/acme-corp"},
            {"link": "https://reuters.com/article/news"},
            {"link": "https://alibaba.com/product/123"},
            {"link": "https://google.com/search?q=test"},
            {"link": "https://another-company.com"},
        ]

        buckets = classify_search_results(results)

        assert len(buckets["company_site"]) == 2  # solartech + another-company
        assert len(buckets["platform_listing"]) == 1  # alibaba
        assert len(buckets["linkedin_company"]) == 1  # linkedin/company
        assert len(buckets["content_page"]) == 1  # reuters
        assert len(buckets["irrelevant"]) == 1  # google.com

    def test_empty_results(self):
        buckets = classify_search_results([])
        for v in buckets.values():
            assert v == []

    def test_missing_link_goes_to_irrelevant(self):
        results = [{"title": "no link"}, {"link": ""}]
        buckets = classify_search_results(results)
        assert len(buckets["irrelevant"]) == 2


class TestFilterSearchResults:
    def test_content_pages_merged_into_company_sites(self):
        """Backward-compatible wrapper merges content_page into company_sites."""
        results = [
            {"link": "https://www.solartech.de"},
            {"link": "https://linkedin.com/company/acme-corp"},
            {"link": "https://reuters.com/article/top-suppliers"},
            {"link": "https://alibaba.com/product/123"},
            {"link": "https://another-company.com"},
        ]

        company, platform, linkedin = filter_search_results(results)

        # solartech + another-company + reuters (content merged in)
        assert len(company) == 3
        assert len(platform) == 1  # alibaba
        assert len(linkedin) == 1  # linkedin/company

    def test_empty_results(self):
        company, platform, linkedin = filter_search_results([])
        assert company == []
        assert platform == []
        assert linkedin == []

    def test_only_irrelevant_dropped(self):
        results = [
            {"link": "https://google.com/search?q=test"},
            {"link": "https://tiktok.com/@user"},
        ]
        company, platform, linkedin = filter_search_results(results)
        assert company == []
        assert platform == []
        assert linkedin == []
