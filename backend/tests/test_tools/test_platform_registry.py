"""Tests for tools/platform_registry.py — platform matching, query building."""

import pytest

from tools.platform_registry import B2BPlatform, PlatformRegistryTool


class TestB2BPlatform:
    def test_build_query_default_format(self):
        p = B2BPlatform(name="Alibaba", domain="alibaba.com")
        assert p.build_query("solar inverter") == "site:alibaba.com solar inverter"

    def test_build_query_custom_format(self):
        p = B2BPlatform(
            name="LinkedIn",
            domain="linkedin.com",
            search_format="site:{domain}/company {keyword}",
        )
        assert p.build_query("solar") == "site:linkedin.com/company solar"


class TestPlatformRegistryMatch:
    def test_default_registry_not_empty(self):
        reg = PlatformRegistryTool()
        assert len(reg.all_platforms) > 0

    def test_match_all_when_no_filters(self):
        reg = PlatformRegistryTool()
        matched = reg.match()
        assert len(matched) == len(reg.all_platforms)

    def test_match_by_region_europe(self):
        reg = PlatformRegistryTool()
        matched = reg.match(regions=["europe"])
        names = [p.name for p in matched]
        assert "Europages" in names
        assert "Kompass" in names
        # Global platforms should also match
        assert "LinkedIn" in names

    def test_match_by_region_asia(self):
        reg = PlatformRegistryTool()
        matched = reg.match(regions=["asia"])
        names = [p.name for p in matched]
        assert "Alibaba" in names
        assert "IndiaMART" in names

    def test_match_by_industry(self):
        reg = PlatformRegistryTool()
        matched = reg.match(industries=["electronics"])
        names = [p.name for p in matched]
        assert "Alibaba" in names
        assert "Made-in-China" in names
        assert "GlobalSources" in names

    def test_match_by_region_and_industry(self):
        reg = PlatformRegistryTool()
        matched = reg.match(regions=["north_america"], industries=["manufacturing"])
        names = [p.name for p in matched]
        assert "ThomasNet" in names

    def test_match_min_weight(self):
        reg = PlatformRegistryTool()
        matched = reg.match(min_weight=0.9)
        for p in matched:
            assert p.weight >= 0.9

    def test_match_sorted_by_weight_desc(self):
        reg = PlatformRegistryTool()
        matched = reg.match()
        weights = [p.weight for p in matched]
        assert weights == sorted(weights, reverse=True)

    def test_match_custom_platforms(self):
        custom = [
            B2BPlatform(name="TestPlatform", domain="test.com", regions=["test_region"]),
        ]
        reg = PlatformRegistryTool(platforms=custom)
        assert len(reg.all_platforms) == 1
        matched = reg.match(regions=["test_region"])
        assert len(matched) == 1
        assert matched[0].name == "TestPlatform"

    def test_match_no_results(self):
        custom = [
            B2BPlatform(name="X", domain="x.com", regions=["mars"], industries=["alien_tech"]),
        ]
        reg = PlatformRegistryTool(platforms=custom)
        matched = reg.match(regions=["earth"])
        assert len(matched) == 0


class TestPlatformRegistryBuildQueries:
    def test_build_queries(self):
        reg = PlatformRegistryTool()
        queries = reg.build_queries("solar inverter", regions=["europe"])
        assert len(queries) > 0
        for q in queries:
            assert "platform" in q
            assert "domain" in q
            assert "query" in q
            assert "solar inverter" in q["query"]

    def test_build_queries_contain_site_prefix(self):
        reg = PlatformRegistryTool()
        queries = reg.build_queries("test keyword")
        for q in queries:
            assert "site:" in q["query"]

    def test_build_queries_empty_when_no_match(self):
        custom = [
            B2BPlatform(name="X", domain="x.com", regions=["mars"]),
        ]
        reg = PlatformRegistryTool(platforms=custom)
        queries = reg.build_queries("test", regions=["earth"])
        assert queries == []
