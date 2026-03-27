"""CompanyWebsiteFinder — resolve LinkedIn/platform URLs to official company websites.

Given a company name or slug (e.g. from a LinkedIn URL like
https://ca.linkedin.com/company/itc-electrical-components), this tool
searches Google to find the company's official website.

Strategy:
1. Extract company name from the URL slug
2. Google search: "{company_name} official website"
3. Return the first non-platform, non-social result as the official site
"""

from __future__ import annotations

import logging
from urllib.parse import urlparse

from tools.google_search import GoogleSearchTool
from tools.url_filter import (
    _CONTENT_DOMAINS,
    _IRRELEVANT_DOMAINS,
    _PLATFORM_DOMAINS,
    extract_linkedin_company_slug,
    slug_to_company_name,
)

logger = logging.getLogger(__name__)

# Domains to skip when looking for the "official" website —
# we want the company's *own* domain, not a directory or platform page.
_NON_OFFICIAL_DOMAINS: set[str] = (
    _IRRELEVANT_DOMAINS
    | _CONTENT_DOMAINS
    | set(_PLATFORM_DOMAINS.keys())
    | {"linkedin.com"}
)


class CompanyWebsiteFinder:
    """Resolve platform URLs (LinkedIn, Alibaba, etc.) to official company websites."""

    def __init__(self, search_tool: GoogleSearchTool | None = None) -> None:
        self._search_tool = search_tool
        self._owns_search_tool = search_tool is None

    async def _get_search_tool(self) -> GoogleSearchTool:
        if self._search_tool is None:
            self._search_tool = GoogleSearchTool()
        return self._search_tool

    async def close(self) -> None:
        if self._owns_search_tool and self._search_tool is not None:
            await self._search_tool.close()
            self._search_tool = None

    async def find_website(self, company_name: str) -> str | None:
        """Search Google for a company's official website.

        Args:
            company_name: Human-readable company name.

        Returns:
            Official website URL or None if not found.
        """
        if not company_name or not company_name.strip():
            return None

        search_tool = await self._get_search_tool()
        query = f'"{company_name}" official website'

        try:
            results = await search_tool.search(query, num=5)
        except Exception as e:
            logger.warning("[CompanyWebsiteFinder] Search failed for '%s': %s", company_name, e)
            return None

        for r in results:
            url = r.get("link", "")
            if not url:
                continue

            domain = urlparse(url).netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]

            # Skip known non-official domains
            is_non_official = any(
                domain == d or domain.endswith("." + d)
                for d in _NON_OFFICIAL_DOMAINS
            )
            if is_non_official:
                continue

            logger.info("[CompanyWebsiteFinder] '%s' → %s", company_name, url)
            return url

        logger.info("[CompanyWebsiteFinder] No official website found for '%s'", company_name)
        return None

    async def resolve_linkedin_url(self, linkedin_url: str) -> str | None:
        """Resolve a LinkedIn company URL to the company's official website.

        Args:
            linkedin_url: Full LinkedIn URL, e.g.
                "https://ca.linkedin.com/company/itc-electrical-components"

        Returns:
            Official website URL or None.
        """
        slug = extract_linkedin_company_slug(linkedin_url)
        if not slug:
            logger.debug("[CompanyWebsiteFinder] Could not extract slug from: %s", linkedin_url)
            return None

        company_name = slug_to_company_name(slug)
        return await self.find_website(company_name)

    async def resolve_platform_url(self, url: str, platform: str = "") -> str | None:
        """Resolve a B2B platform listing URL to the company's official website.

        Extracts a company name from the URL path and searches for the official site.

        Args:
            url: Platform listing URL.
            platform: Platform name hint (optional).

        Returns:
            Official website URL or None.
        """
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.strip("/").split("/") if p]

        if not path_parts:
            return None

        # Use the last meaningful path segment as company name hint
        slug = path_parts[-1]
        # Remove common suffixes like .html, numeric IDs
        slug = slug.split(".")[0]
        # Skip if it's just a number (product ID, not company name)
        if slug.isdigit():
            if len(path_parts) >= 2:
                slug = path_parts[-2].split(".")[0]
            else:
                return None

        company_name = slug_to_company_name(slug)
        if len(company_name) < 3:
            return None

        return await self.find_website(company_name)
