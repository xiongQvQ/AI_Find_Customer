"""B2B Platform Registry — match ICP to relevant vertical platforms for site: searches."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class B2BPlatform:
    """A B2B platform entry with metadata for search targeting."""

    name: str
    domain: str
    regions: list[str] = field(default_factory=list)
    industries: list[str] = field(default_factory=list)
    search_format: str = "site:{domain} {keyword}"
    weight: float = 1.0
    tags: list[str] = field(default_factory=list)

    def build_query(self, keyword: str) -> str:
        """Build a site:-scoped search query for this platform."""
        return self.search_format.format(domain=self.domain, keyword=keyword)


# ── Default registry ────────────────────────────────────────────────────

_DEFAULT_PLATFORMS: list[B2BPlatform] = [
    B2BPlatform(
        name="Alibaba",
        domain="alibaba.com",
        regions=["global", "asia"],
        industries=["manufacturing", "electronics", "machinery"],
        weight=1.0,
        tags=["marketplace"],
    ),
    B2BPlatform(
        name="Made-in-China",
        domain="made-in-china.com",
        regions=["global", "asia"],
        industries=["manufacturing", "electronics"],
        weight=0.8,
        tags=["marketplace"],
    ),
    B2BPlatform(
        name="Europages",
        domain="europages.com",
        regions=["europe"],
        industries=["manufacturing", "industrial"],
        weight=0.9,
        tags=["directory"],
    ),
    B2BPlatform(
        name="ThomasNet",
        domain="thomasnet.com",
        regions=["north_america"],
        industries=["manufacturing", "industrial"],
        weight=0.9,
        tags=["directory"],
    ),
    B2BPlatform(
        name="IndiaMART",
        domain="indiamart.com",
        regions=["asia", "india"],
        industries=["manufacturing", "chemicals"],
        weight=0.7,
        tags=["marketplace"],
    ),
    B2BPlatform(
        name="Kompass",
        domain="kompass.com",
        regions=["europe", "global"],
        industries=["manufacturing", "services"],
        weight=0.7,
        tags=["directory"],
    ),
    B2BPlatform(
        name="GlobalSources",
        domain="globalsources.com",
        regions=["asia", "global"],
        industries=["electronics", "fashion", "gifts"],
        weight=0.8,
        tags=["marketplace"],
    ),
    B2BPlatform(
        name="TradeIndia",
        domain="tradeindia.com",
        regions=["asia", "india"],
        industries=["manufacturing", "agriculture"],
        weight=0.6,
        tags=["marketplace"],
    ),
    B2BPlatform(
        name="LinkedIn",
        domain="linkedin.com",
        regions=["global"],
        industries=[],
        search_format="site:{domain}/company {keyword}",
        weight=1.0,
        tags=["social", "professional"],
    ),
]


class PlatformRegistryTool:
    """Match target regions and industries to relevant B2B platforms.

    Used by SearchAgent to determine which platforms to include in site: searches.
    """

    def __init__(self, platforms: list[B2BPlatform] | None = None) -> None:
        self._platforms = platforms if platforms is not None else _DEFAULT_PLATFORMS

    @property
    def all_platforms(self) -> list[B2BPlatform]:
        return list(self._platforms)

    def match(
        self,
        *,
        regions: list[str] | None = None,
        industries: list[str] | None = None,
        min_weight: float = 0.0,
    ) -> list[B2BPlatform]:
        """Return platforms matching the given regions and/or industries.

        Args:
            regions: Target regions (e.g. ["europe", "asia"]). Empty = match all.
            industries: Target industries. Empty = match all.
            min_weight: Minimum platform weight to include.

        Returns:
            Sorted list of matching platforms (highest weight first).
        """
        matched = []
        for p in self._platforms:
            if p.weight < min_weight:
                continue

            region_match = True
            if regions:
                region_match = any(
                    r.lower() in [pr.lower() for pr in p.regions]
                    for r in regions
                ) or "global" in [pr.lower() for pr in p.regions]

            industry_match = True
            if industries and p.industries:
                industry_match = any(
                    i.lower() in [pi.lower() for pi in p.industries]
                    for i in industries
                )

            if region_match and industry_match:
                matched.append(p)

        return sorted(matched, key=lambda p: p.weight, reverse=True)

    def build_queries(
        self,
        keyword: str,
        *,
        regions: list[str] | None = None,
        industries: list[str] | None = None,
    ) -> list[dict]:
        """Build search queries for all matching platforms.

        Returns:
            List of dicts with keys: platform, domain, query.
        """
        platforms = self.match(regions=regions, industries=industries)
        return [
            {
                "platform": p.name,
                "domain": p.domain,
                "query": p.build_query(keyword),
            }
            for p in platforms
        ]
