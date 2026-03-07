"""SearchAgent — Google Maps-only discovery with concurrency and dedup."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from config.settings import get_settings
from graph.state import HuntState
from tools.google_maps_search import GoogleMapsSearchTool
from tools.platform_registry import PlatformRegistryTool  # backward-compatible patch target
from tools.web_search import WebSearchTool  # backward-compatible patch target

logger = logging.getLogger(__name__)

# ── Region → Serper geo params mapping ───────────────────────────────────
# Kept here because KeywordGenAgent imports _REGION_GEO for language hints.
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
    """Convert target_regions list to Serper gl/hl params using first match."""
    for region in target_regions:
        key = region.strip().lower()
        if key in _REGION_GEO:
            return _REGION_GEO[key]
    return {}


_CHINA_KEYWORDS = {"china", "中国", "cn", "大陆", "mainland china"}


def _is_china_region(target_regions: list[str]) -> bool:
    """Backward-compatible helper kept for tests and external imports."""
    for region in target_regions:
        if region.strip().lower() in _CHINA_KEYWORDS:
            return True
    return False


def _build_maps_snippet(place: dict) -> str:
    """Build a compact snippet from Maps place data."""
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


def _result_identity_key(item: dict) -> str:
    """Stable dedupe key for a search result, including Maps-only rows without website."""
    link = (item.get("link") or "").strip().lower()
    if link:
        return f"url:{link}"

    maps_data = item.get("maps_data") or {}
    place_id = (maps_data.get("place_id") or maps_data.get("cid") or "").strip().lower()
    if place_id:
        return f"place:{place_id}"

    title = (item.get("title") or "").strip().lower()
    address = (maps_data.get("address") or "").strip().lower()
    if title or address:
        return f"maps:{title}|{address}"

    return ""


async def _maps_search_keyword(
    keyword: str,
    maps_tool: GoogleMapsSearchTool,
    semaphore: asyncio.Semaphore,
    *,
    gl: str = "",
    hl: str = "",
) -> dict:
    """Search Google Maps for a keyword and return normalized rows."""
    async with semaphore:
        try:
            logger.info("[GoogleMaps] query=%r gl=%s hl=%s", keyword, gl or "(none)", hl or "(none)")
            places = await maps_tool.search(keyword, gl=gl, hl=hl)
            results = []
            for place in places:
                maps_data = {
                    "title": place.get("title", ""),
                    "address": place.get("address", ""),
                    "type": place.get("type", ""),
                    "types": place.get("types", []),
                    "website": place.get("website", ""),
                    "phone_number": place.get("phone_number", ""),
                    "phoneNumber": place.get("phone_number", ""),
                    "description": place.get("description", ""),
                    "email": place.get("email", ""),
                    "rating": place.get("rating", 0),
                    "rating_count": place.get("rating_count", 0),
                    "latitude": place.get("latitude", 0),
                    "longitude": place.get("longitude", 0),
                    "cid": place.get("cid", ""),
                    "place_id": place.get("place_id", ""),
                }
                results.append({
                    "title": place.get("title", ""),
                    "link": place.get("website", ""),
                    "snippet": _build_maps_snippet(place),
                    "position": 0,
                    "source": "google_maps",
                    "maps_data": maps_data,
                })

            logger.info("[GoogleMaps] query=%r → %d places", keyword, len(results))
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


async def search_node(state: HuntState) -> dict:
    """LangGraph node: Google Maps-only search for all round keywords."""
    settings = get_settings()
    keywords = state.get("keywords", [])
    target_regions = state.get("target_regions", [])

    logger.info("[SearchAgent] Starting — %d keywords, regions=%s", len(keywords), target_regions)

    if not keywords:
        logger.info("[SearchAgent] No keywords to search, skipping")
        return {"current_stage": "search"}

    geo = _resolve_geo_params(target_regions)
    gl = geo.get("gl", "")
    hl = geo.get("hl", "")
    if geo:
        logger.info("[SearchAgent] Resolved regions %s → gl=%s, hl=%s", target_regions, gl, hl)
    else:
        logger.info("[SearchAgent] No geo params resolved from regions=%s, searching globally", target_regions)

    semaphore = asyncio.Semaphore(settings.search_concurrency)
    maps_tool = GoogleMapsSearchTool(settings)

    search_tasks = [
        _maps_search_keyword(kw, maps_tool, semaphore, gl=gl, hl=hl)
        for kw in keywords
    ]
    logger.info(
        "[SearchAgent] Tool routing: regions=%s → %s",
        target_regions,
        ["google_maps(serper)"],
    )
    logger.info("[SearchAgent] Launching %d maps tasks (concurrency=%d)", len(search_tasks), settings.search_concurrency)

    raw_results = []
    for future in asyncio.as_completed(search_tasks):
        try:
            raw_results.append(await future)
        except Exception as e:
            logger.error("[SearchAgent] Task failed: %s", e)

    all_results = state.get("search_results", [])
    keyword_stats: dict[str, Any] = dict(state.get("keyword_search_stats", {}))

    # seen_urls now stores generic dedupe identities (URL or Maps place key).
    state_seen = state.get("seen_urls") or []
    seen_keys: set[str] = set(state_seen)
    if not seen_keys:
        for r in all_results:
            key = _result_identity_key(r)
            if key:
                seen_keys.add(key)

    initial_new_results = []
    for r in raw_results:
        base_kw = r["keyword"]
        if base_kw not in keyword_stats:
            keyword_stats[base_kw] = {"result_count": 0, "leads_found": 0}

        for item in r["results"]:
            item["source_keyword"] = base_kw
            item_key = _result_identity_key(item)
            if not item_key or item_key in seen_keys:
                continue
            seen_keys.add(item_key)
            initial_new_results.append(item)
            keyword_stats[base_kw]["result_count"] = keyword_stats[base_kw].get("result_count", 0) + 1

    hunt_id = state.get("hunt_id", "")
    if hunt_id:
        try:
            from observability.cost_tracker import get_tracker

            tracker = get_tracker(hunt_id)
            for r in raw_results:
                tracker.record_search_call(provider=r.get("source", "google_maps"), result_count=r.get("result_count", 0))
        except Exception:
            pass

    try:
        await maps_tool.close()
    except Exception as e:
        logger.warning("[SearchAgent] Error closing tools: %s", e)

    logger.info(
        "[SearchAgent] Completed — %d new results (total: %d)",
        len(initial_new_results),
        len(all_results) + len(initial_new_results),
    )

    return {
        "search_results": all_results + initial_new_results,
        "seen_urls": list(seen_keys),
        "matched_platforms": [],
        "keyword_search_stats": keyword_stats,
        "current_stage": "search",
    }
