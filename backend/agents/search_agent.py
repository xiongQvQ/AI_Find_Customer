"""SearchAgent — concurrent search across keywords + B2B platforms using asyncio.Semaphore."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any
from urllib.parse import urljoin, urlparse

from config.settings import Settings, get_settings
from graph.state import HuntState
from tools.amap_search import AmapSearchTool
from tools.baidu_search import BaiduSearchTool
from tools.google_maps_search import GoogleMapsSearchTool
from tools.jina_reader import JinaReaderTool
from tools.platform_registry import PlatformRegistryTool
from tools.url_filter import classify_url
from tools.web_search import WebSearchTool

logger = logging.getLogger(__name__)

# ── Link extraction helper ────────────────────────────────────────────────

def _extract_links_from_markdown(content: str, source_url: str) -> list[str]:
    """Extract valid external links from Jina Markdown content."""
    # Pattern for markdown links: [text](url)
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    
    source_domain = urlparse(source_url).netloc
    extracted = []
    
    for _, href in link_pattern.findall(content):
        # Normalize
        full_url = urljoin(source_url, href)
        try:
            parsed = urlparse(full_url)
            if parsed.scheme not in ("http", "https"):
                continue
                
            # Skip internal links
            if parsed.netloc == source_domain:
                continue
                
            # Skip likely irrelevant (social share, login, etc - rudimentary check)
            if any(x in full_url.lower() for x in ["share=", "login", "signup", "signin"]):
                continue
                
            extracted.append(full_url)
        except Exception:
            continue
            
    return extracted

async def _expand_directory_entry(
    result_item: dict,
    jina: JinaReaderTool,
    semaphore: asyncio.Semaphore,
) -> list[dict]:
    """Scrape a content/listicle page and extract external company links."""
    url = result_item.get("link", "")
    if not url:
        return []
        
    async with semaphore:
        try:
            logger.info("[SearchExpansion] Scraping directory/listicle: %s", url)
            content = await jina.read(url)
            if not content or len(content) < 200:
                return []
                
            links = _extract_links_from_markdown(content, url)
            
            # Filter and format as search results
            # Only keep actionable URL types; skip irrelevant and content_page
            # (content_page would cause recursive expansion loops)
            _EXPANSION_ALLOWED = {"company_site", "platform_listing", "linkedin_company"}
            expanded_results = []
            for link in list(set(links))[:15]:  # Limit to 15 links per directory to avoid spam
                if not link:
                    continue
                if classify_url(link) not in _EXPANSION_ALLOWED:
                    continue
                    
                expanded_results.append({
                    "title": f"Extracted from {result_item.get('title', 'directory')}",
                    "link": link,
                    "snippet": f"Discovered via {url}",
                    "position": 0,
                    "source": "directory_expansion",
                    "source_keyword": result_item.get("source_keyword", ""),
                })
            
            if expanded_results:
                logger.info("[SearchExpansion] Found %d links in %s", len(expanded_results), url)
            return expanded_results
            
        except Exception as e:
            logger.warning("[SearchExpansion] Failed to expand %s: %s", url, e)
            return []


# ── Region → Serper geo params mapping ───────────────────────────────────
# Maps user-friendly region names (EN/CN) to Serper gl (country) and hl (language).
# When multiple countries belong to a region, we pick the dominant market.
_REGION_GEO: dict[str, dict[str, str]] = {
    # English — Countries
    "germany": {"gl": "de", "hl": "de"},
    "france": {"gl": "fr", "hl": "fr"},
    "uk": {"gl": "uk", "hl": "en"},
    "united kingdom": {"gl": "uk", "hl": "en"},
    "italy": {"gl": "it", "hl": "it"},
    "spain": {"gl": "es", "hl": "es"},
    "netherlands": {"gl": "nl", "hl": "nl"},
    "poland": {"gl": "pl", "hl": "pl"},
    "czech republic": {"gl": "cz", "hl": "cs"},
    "czechia": {"gl": "cz", "hl": "cs"},
    "romania": {"gl": "ro", "hl": "ro"},
    "hungary": {"gl": "hu", "hl": "hu"},
    "turkey": {"gl": "tr", "hl": "tr"},
    "russia": {"gl": "ru", "hl": "ru"},
    "ukraine": {"gl": "ua", "hl": "uk"},
    "sweden": {"gl": "se", "hl": "sv"},
    "norway": {"gl": "no", "hl": "no"},
    "denmark": {"gl": "dk", "hl": "da"},
    "finland": {"gl": "fi", "hl": "fi"},
    "portugal": {"gl": "pt", "hl": "pt"},
    "austria": {"gl": "at", "hl": "de"},
    "switzerland": {"gl": "ch", "hl": "de"},
    "belgium": {"gl": "be", "hl": "nl"},
    "greece": {"gl": "gr", "hl": "el"},
    "usa": {"gl": "us", "hl": "en"},
    "united states": {"gl": "us", "hl": "en"},
    "canada": {"gl": "ca", "hl": "en"},
    "australia": {"gl": "au", "hl": "en"},
    "new zealand": {"gl": "nz", "hl": "en"},
    "japan": {"gl": "jp", "hl": "ja"},
    "south korea": {"gl": "kr", "hl": "ko"},
    "india": {"gl": "in", "hl": "en"},
    "brazil": {"gl": "br", "hl": "pt"},
    "mexico": {"gl": "mx", "hl": "es"},
    "china": {"gl": "cn", "hl": "zh-cn"},
    "singapore": {"gl": "sg", "hl": "en"},
    "thailand": {"gl": "th", "hl": "th"},
    "vietnam": {"gl": "vn", "hl": "vi"},
    "indonesia": {"gl": "id", "hl": "id"},
    "malaysia": {"gl": "my", "hl": "en"},
    "philippines": {"gl": "ph", "hl": "en"},
    "south africa": {"gl": "za", "hl": "en"},
    "uae": {"gl": "ae", "hl": "en"},
    "saudi arabia": {"gl": "sa", "hl": "ar"},
    # English — Composite regions
    "europe": {"gl": "de", "hl": "en"},
    "western europe": {"gl": "de", "hl": "en"},
    "eastern europe": {"gl": "pl", "hl": "en"},
    "central europe": {"gl": "de", "hl": "en"},
    "northern europe": {"gl": "se", "hl": "en"},
    "southern europe": {"gl": "it", "hl": "en"},
    "nordic": {"gl": "se", "hl": "en"},
    "scandinavia": {"gl": "se", "hl": "en"},
    "north america": {"gl": "us", "hl": "en"},
    "south america": {"gl": "br", "hl": "pt"},
    "latin america": {"gl": "br", "hl": "es"},
    "southeast asia": {"gl": "sg", "hl": "en"},
    "east asia": {"gl": "jp", "hl": "en"},
    "south asia": {"gl": "in", "hl": "en"},
    "middle east": {"gl": "ae", "hl": "en"},
    "africa": {"gl": "za", "hl": "en"},
    "oceania": {"gl": "au", "hl": "en"},
    # Chinese — Countries
    "德国": {"gl": "de", "hl": "de"},
    "法国": {"gl": "fr", "hl": "fr"},
    "英国": {"gl": "uk", "hl": "en"},
    "意大利": {"gl": "it", "hl": "it"},
    "西班牙": {"gl": "es", "hl": "es"},
    "荷兰": {"gl": "nl", "hl": "nl"},
    "波兰": {"gl": "pl", "hl": "pl"},
    "捷克": {"gl": "cz", "hl": "cs"},
    "罗马尼亚": {"gl": "ro", "hl": "ro"},
    "匈牙利": {"gl": "hu", "hl": "hu"},
    "土耳其": {"gl": "tr", "hl": "tr"},
    "俄罗斯": {"gl": "ru", "hl": "ru"},
    "乌克兰": {"gl": "ua", "hl": "uk"},
    "瑞典": {"gl": "se", "hl": "sv"},
    "挪威": {"gl": "no", "hl": "no"},
    "丹麦": {"gl": "dk", "hl": "da"},
    "芬兰": {"gl": "fi", "hl": "fi"},
    "葡萄牙": {"gl": "pt", "hl": "pt"},
    "奥地利": {"gl": "at", "hl": "de"},
    "瑞士": {"gl": "ch", "hl": "de"},
    "比利时": {"gl": "be", "hl": "nl"},
    "希腊": {"gl": "gr", "hl": "el"},
    "美国": {"gl": "us", "hl": "en"},
    "加拿大": {"gl": "ca", "hl": "en"},
    "澳大利亚": {"gl": "au", "hl": "en"},
    "新西兰": {"gl": "nz", "hl": "en"},
    "日本": {"gl": "jp", "hl": "ja"},
    "韩国": {"gl": "kr", "hl": "ko"},
    "印度": {"gl": "in", "hl": "en"},
    "巴西": {"gl": "br", "hl": "pt"},
    "墨西哥": {"gl": "mx", "hl": "es"},
    "中国": {"gl": "cn", "hl": "zh-cn"},
    "新加坡": {"gl": "sg", "hl": "en"},
    "泰国": {"gl": "th", "hl": "th"},
    "越南": {"gl": "vn", "hl": "vi"},
    "印尼": {"gl": "id", "hl": "id"},
    "印度尼西亚": {"gl": "id", "hl": "id"},
    "马来西亚": {"gl": "my", "hl": "en"},
    "菲律宾": {"gl": "ph", "hl": "en"},
    "南非": {"gl": "za", "hl": "en"},
    "阿联酋": {"gl": "ae", "hl": "en"},
    "沙特": {"gl": "sa", "hl": "ar"},
    "沙特阿拉伯": {"gl": "sa", "hl": "ar"},
    # Chinese — Composite regions
    "欧洲": {"gl": "de", "hl": "en"},
    "西欧": {"gl": "de", "hl": "en"},
    "东欧": {"gl": "pl", "hl": "en"},
    "中欧": {"gl": "de", "hl": "en"},
    "北欧": {"gl": "se", "hl": "en"},
    "南欧": {"gl": "it", "hl": "en"},
    "北美": {"gl": "us", "hl": "en"},
    "南美": {"gl": "br", "hl": "pt"},
    "拉丁美洲": {"gl": "br", "hl": "es"},
    "东南亚": {"gl": "sg", "hl": "en"},
    "东亚": {"gl": "jp", "hl": "en"},
    "南亚": {"gl": "in", "hl": "en"},
    "中东": {"gl": "ae", "hl": "en"},
    "非洲": {"gl": "za", "hl": "en"},
    "大洋洲": {"gl": "au", "hl": "en"},
}


def _resolve_geo_params(target_regions: list[str]) -> dict[str, str]:
    """Convert target_regions list to Serper gl/hl params.

    Uses the first matched region. Returns empty dict if no match.
    """
    for region in target_regions:
        key = region.strip().lower()
        if key in _REGION_GEO:
            return _REGION_GEO[key]
    return {}



_CHINA_KEYWORDS = {"china", "中国", "cn", "大陆", "mainland china"}


def _is_china_region(target_regions: list[str]) -> bool:
    """Check if any target region refers to China."""
    for region in target_regions:
        if region.strip().lower() in _CHINA_KEYWORDS:
            return True
    return False


def _get_amap_region(target_regions: list[str]) -> str:
    """Extract a Chinese city/region name for Amap's region param.

    Returns the first region that looks like a Chinese city name,
    or empty string for nationwide search.
    """
    for region in target_regions:
        r = region.strip()
        # Skip generic "China" / "中国" — search nationwide
        if r.lower() in _CHINA_KEYWORDS:
            continue
        # If it looks like a Chinese city name, use it
        if r:
            return r
    return ""


async def _search_keyword(
    keyword: str,
    search_tool: WebSearchTool,
    semaphore: asyncio.Semaphore,
    *,
    gl: str = "",
    hl: str = "",
) -> dict:
    """Search a single keyword with semaphore-controlled concurrency.

    Returns:
        Dict with keyword, results list, and result_count.
    """
    async with semaphore:
        try:
            logger.info("[WebSearch] query=%r gl=%s hl=%s via=%s",
                        keyword, gl or '(none)', hl or '(none)',
                        search_tool.__class__.__name__)
            results = await search_tool.search(keyword, gl=gl, hl=hl)
            logger.info("[WebSearch] query=%r → %d results", keyword, len(results))
            return {
                "keyword": keyword,
                "results": results,
                "result_count": len(results),
                "source": "web_search",
                "error": None,
            }
        except Exception as e:
            logger.warning("[WebSearch] FAILED query=%r: %s", keyword, e)
            return {
                "keyword": keyword,
                "results": [],
                "result_count": 0,
                "source": "web_search",
                "error": str(e),
            }


async def _maps_search_keyword(
    keyword: str,
    maps_tool: GoogleMapsSearchTool,
    semaphore: asyncio.Semaphore,
    *,
    gl: str = "",
    hl: str = "",
) -> dict:
    """Search Google Maps for a keyword with semaphore-controlled concurrency.

    Converts Maps place results into the same link-based format used by
    Google Search results so they can be merged seamlessly.

    Returns:
        Dict with keyword, results list, and result_count.
    """
    async with semaphore:
        try:
            logger.info("[GoogleMaps] query=%r gl=%s hl=%s", keyword, gl or '(none)', hl or '(none)')
            places = await maps_tool.search(keyword, gl=gl, hl=hl)
            results = []
            for place in places:
                website = place.get("website", "")
                if not website:
                    continue
                results.append({
                    "title": place.get("title", ""),
                    "link": website,
                    "snippet": _build_maps_snippet(place),
                    "position": 0,
                    "maps_data": {
                        "address": place.get("address", ""),
                        "phone_number": place.get("phone_number", ""),
                        "rating": place.get("rating", 0),
                        "rating_count": place.get("rating_count", 0),
                        "type": place.get("type", ""),
                        "latitude": place.get("latitude", 0),
                        "longitude": place.get("longitude", 0),
                        "place_id": place.get("place_id", ""),
                    },
                })
            logger.info("[GoogleMaps] query=%r → %d places (%d with website)",
                        keyword, len(places), len(results))
            return {
                "keyword": keyword,
                "results": results,
                "result_count": len(results),
                "source": "google_maps",
                "error": None,
            }
        except Exception as e:
            logger.warning("[GoogleMaps] FAILED query=%r: %s", keyword, e)
            return {
                "keyword": keyword,
                "results": [],
                "result_count": 0,
                "source": "google_maps",
                "error": str(e),
            }


async def _baidu_search_keyword(
    keyword: str,
    baidu_tool: BaiduSearchTool,
    semaphore: asyncio.Semaphore,
) -> dict:
    """Search Baidu (百度) for a keyword.

    Returns results in the same format as _search_keyword so they can be
    merged seamlessly with Google Search results.
    """
    async with semaphore:
        try:
            refs = await baidu_tool.search(keyword)
            results = [
                {
                    "title": r.get("title", ""),
                    "link": r.get("link", ""),
                    "snippet": r.get("snippet", ""),
                    "position": r.get("position", 0),
                    "source": "baidu",
                }
                for r in refs
                if r.get("link")
            ]
            logger.info("[BaiduSearch] query=%r → %d results", keyword, len(results))
            return {
                "keyword": keyword,
                "results": results,
                "result_count": len(results),
                "source": "baidu",
                "error": None,
            }
        except Exception as e:
            logger.warning("[BaiduSearch] FAILED query=%r: %s", keyword, e)
            return {
                "keyword": keyword,
                "results": [],
                "result_count": 0,
                "source": "baidu",
                "error": str(e),
            }


async def _amap_search_keyword(
    keyword: str,
    amap_tool: AmapSearchTool,
    semaphore: asyncio.Semaphore,
    *,
    region: str = "",
) -> dict:
    """Search Amap (高德地图) for a keyword.

    Converts Amap POI results into the same link-based format used by
    Google Search results so they can be merged seamlessly.
    """
    async with semaphore:
        try:
            places = await amap_tool.search(keyword, region=region)
            results = []
            for place in places:
                # Amap doesn't return website URLs, but we keep the company info
                # in maps_data so LeadExtract can use company name to find website
                name = place.get("name", "")
                if not name:
                    continue
                results.append({
                    "title": name,
                    "link": "",  # No website from Amap — will be resolved later
                    "snippet": _build_amap_snippet(place),
                    "position": 0,
                    "maps_data": {
                        "address": place.get("address", ""),
                        "phone_number": place.get("phone", ""),
                        "type": place.get("type", ""),
                        "latitude": place.get("latitude", 0),
                        "longitude": place.get("longitude", 0),
                        "province": place.get("province", ""),
                        "city": place.get("city", ""),
                        "district": place.get("district", ""),
                        "source": "amap",
                    },
                    "amap_company_name": name,
                })
            logger.info("[AmapSearch] query=%r → %d POIs", keyword, len(results))
            return {
                "keyword": keyword,
                "results": results,
                "result_count": len(results),
                "source": "amap",
                "error": None,
            }
        except Exception as e:
            logger.warning("[AmapSearch] FAILED query=%r: %s", keyword, e)
            return {
                "keyword": keyword,
                "results": [],
                "result_count": 0,
                "source": "amap",
                "error": str(e),
            }


def _build_amap_snippet(place: dict) -> str:
    """Build a descriptive snippet from Amap POI data."""
    parts = []
    if place.get("type"):
        parts.append(place["type"])
    if place.get("province") or place.get("city"):
        parts.append(f"{place.get('province', '')}{place.get('city', '')}{place.get('district', '')}")
    if place.get("address"):
        parts.append(place["address"])
    if place.get("phone"):
        parts.append(place["phone"])
    return " | ".join(parts)


def _build_maps_snippet(place: dict) -> str:
    """Build a descriptive snippet from Maps place data."""
    parts = []
    if place.get("type"):
        parts.append(place["type"])
    if place.get("address"):
        parts.append(place["address"])
    if place.get("phone_number"):
        parts.append(place["phone_number"])
    if place.get("rating"):
        parts.append(f"Rating: {place['rating']}/5 ({place.get('rating_count', 0)} reviews)")
    return " | ".join(parts)


async def search_node(state: HuntState) -> dict:
    """LangGraph node: concurrent search for all current-round keywords.

    For each keyword:
    1. Run a general Google search
    2. Run platform-specific site: searches for matched B2B platforms
    3. (New) Expand high-potential content/listicle pages to find more links

    All searches are concurrent with asyncio.Semaphore(search_concurrency).

    Returns:
        Dict with accumulated search_results, matched_platforms, keyword_search_stats.
    """
    settings = get_settings()
    keywords = state.get("keywords", [])
    target_regions = state.get("target_regions", [])
    insight = state.get("insight")
    insight = insight if isinstance(insight, dict) else {}
    industries = insight.get("industries", [])

    logger.info("[SearchAgent] Starting — %d keywords, regions=%s", len(keywords), target_regions)

    if not keywords:
        logger.info("[SearchAgent] No keywords to search, skipping")
        return {"current_stage": "search"}

    # ── Resolve geo params from target regions ────────────────────────
    geo = _resolve_geo_params(target_regions)
    gl = geo.get("gl", "")
    hl = geo.get("hl", "")
    if geo:
        logger.info("[SearchAgent] Resolved regions %s → gl=%s, hl=%s", target_regions, gl, hl)
    else:
        logger.info("[SearchAgent] No geo params resolved from regions=%s, searching globally", target_regions)

    # ── Determine market type → tool routing ───────────────────────────────
    # Rule-based (no LLM needed):
    #   China regions → Google Search + 百度搜索 + 高德地图 (Amap)
    #   Other regions → Google Search + Google Maps
    is_china = _is_china_region(target_regions)

    semaphore = asyncio.Semaphore(settings.search_concurrency)
    expand_semaphore = asyncio.Semaphore(3)  # Independent limit for directory expansion
    search_tool = WebSearchTool(settings)
    maps_tool = GoogleMapsSearchTool(settings)
    amap_tool = AmapSearchTool() if is_china else None
    baidu_tool = (
        BaiduSearchTool(api_key=settings.baidu_api_key)
        if is_china and settings.baidu_api_key
        else None
    )
    platform_reg = PlatformRegistryTool()
    jina_tool = JinaReaderTool()  # For directory expansion

    # Log active tool set so operators can verify routing
    active_tools = [f"web_search({search_tool.backend})"]
    if is_china:
        if amap_tool:
            active_tools.append("amap")
        if baidu_tool:
            active_tools.append("baidu_search")
    else:
        active_tools.append("google_maps(serper)")
    logger.info(
        "[SearchAgent] Tool routing: regions=%s → %s",
        target_regions, active_tools,
    )

    # ── Build all search tasks ──────────────────────────────────────────
    search_tasks = []
    amap_count = 0
    baidu_count = 0

    for kw in keywords:
        # General Google/Brave/Tavily search (always active)
        search_tasks.append(_search_keyword(kw, search_tool, semaphore, gl=gl, hl=hl))

        if is_china:
            # 内贸模式: 百度搜索 + 高德地图
            if baidu_tool is not None:
                search_tasks.append(_baidu_search_keyword(kw, baidu_tool, semaphore))
                baidu_count += 1
            if amap_tool is not None:
                amap_region = _get_amap_region(target_regions)
                search_tasks.append(_amap_search_keyword(kw, amap_tool, semaphore, region=amap_region))
                amap_count += 1
        else:
            # 外贸模式: Google Maps
            search_tasks.append(_maps_search_keyword(kw, maps_tool, semaphore, gl=gl, hl=hl))

        # Platform-specific site: searches (always active)
        platform_queries = platform_reg.build_queries(
            kw, regions=target_regions, industries=industries,
        )
        for pq in platform_queries:
            search_tasks.append(_search_keyword(
                pq["query"], search_tool, semaphore, gl=gl, hl=hl,
            ))

    logger.info(
        "[SearchAgent] Launching %d search tasks (concurrency=%d, baidu=%d, amap=%d)",
        len(search_tasks), settings.search_concurrency, baidu_count, amap_count,
    )

    # ── Execute searches with as_completed ────────────────────────────
    raw_results = []
    for future in asyncio.as_completed(search_tasks):
        try:
            res = await future
            raw_results.append(res)
        except Exception as e:
            logger.error("[SearchAgent] Task failed: %s", e)

    # ── Aggregate initial results ──────────────────────────────────────
    all_results = state.get("search_results", [])
    # Carry forward stats from previous rounds so evaluate sees ALL history
    keyword_stats: dict[str, Any] = dict(state.get("keyword_search_stats", {}))
    # seen_urls in state survives resume compression (search_results may be cleared).
    # Prefer state["seen_urls"] over rebuilding from search_results to avoid
    # re-visiting URLs already processed in prior hunt sessions.
    state_seen = state.get("seen_urls") or []
    seen_urls: set[str] = set(state_seen) if state_seen else {
        r.get("link", "") for r in all_results
    }
    
    # We will build a list of potential directories for expansion
    potential_directories = []
    
    initial_new_results = []

    for r in raw_results:
        kw = r["keyword"]
        # Track stats per original keyword (not site: queries)
        base_kw = kw
        for prefix_kw in keywords:
            if prefix_kw in kw:
                base_kw = prefix_kw
                break

        if base_kw not in keyword_stats:
            keyword_stats[base_kw] = {"result_count": 0, "leads_found": 0}

        for item in r["results"]:
            url = item.get("link", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                item["source_keyword"] = base_kw
                initial_new_results.append(item)
                keyword_stats[base_kw]["result_count"] += 1
                
                # Check for expansion candidacy (Content Page + Title keywords)
                # "Top 10", "List of", "Directory", "Companies"
                title_lower = item.get("title", "").lower()
                if classify_url(url) == "content_page" and any(x in title_lower for x in ["top", "list", "directory", "manufacturers", "suppliers", "companies", "providers"]):
                     # Avoid re-expanding the same URL or expansion loops
                     item["source_keyword"] = base_kw # ensure source keyword is set
                     potential_directories.append(item)

    # ── Directory Expansion (Scrape Lists) ─────────────────────────────
    # Pick top 3 most promising directories to save time
    expansion_candidates = potential_directories[:3]
    if expansion_candidates:
        logger.info("[SearchAgent] Expanding %d directory/listicle pages...", len(expansion_candidates))
        expansion_tasks = [
            _expand_directory_entry(item, jina_tool, expand_semaphore)
            for item in expansion_candidates
        ]
        
        expansion_results = []
        for future in asyncio.as_completed(expansion_tasks):
            try:
                res = await future
                expansion_results.extend(res)
            except Exception as e:
                logger.warning("[SearchAgent] Expansion task failed: %s", e)
        
        # Add expanded results
        expanded_count = 0
        for item in expansion_results:
            url = item.get("link", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                initial_new_results.append(item)
                # Attribute stats to the original keyword of the directory
                src_kw = item.get("source_keyword", "")
                if src_kw and src_kw in keyword_stats:
                    keyword_stats[src_kw]["result_count"] += 1
                expanded_count += 1
        
        if expanded_count > 0:
            logger.info("[SearchAgent] Expansion added %d new URLs", expanded_count)

    # ── Matched platforms ───────────────────────────────────────────────
    matched = platform_reg.match(regions=target_regions, industries=industries)
    matched_platforms = [
        {"name": p.name, "domain": p.domain, "weight": p.weight}
        for p in matched
    ]

    # ── Record search API call counts to CostTracker ────────────────────
    hunt_id = state.get("hunt_id", "")
    if hunt_id:
        try:
            from observability.cost_tracker import get_tracker
            tracker = get_tracker(hunt_id)
            # Count by source from raw_results
            from collections import Counter
            source_counts: Counter = Counter()
            for r in raw_results:
                src = r.get("source", "google")
                source_counts[src] += r.get("result_count", 0)
            for src, count in source_counts.items():
                tracker.record_search_call(provider=src, result_count=count)
        except Exception:
            pass

    try:
        await search_tool.close()
        await maps_tool.close()
        if amap_tool is not None:
            await amap_tool.close()
        if baidu_tool is not None:
            await baidu_tool.close()
        await jina_tool.close()
    except Exception as e:
        logger.warning("[SearchAgent] Error closing tools: %s", e)

    logger.info("[SearchAgent] Completed — %d new URLs found (total), %d combined results",
                len(initial_new_results), len(all_results) + len(initial_new_results))

    return {
        "search_results": all_results + initial_new_results,
        "seen_urls": list(seen_urls),
        "matched_platforms": matched_platforms,
        "keyword_search_stats": keyword_stats,
        "current_stage": "search",
    }
