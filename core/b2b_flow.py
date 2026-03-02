"""
B2B Discovery Flow
==================
Full automated pipeline:
  1. Generate keywords (via LLM) from product + regions
  2. Search each keyword (Serper or Tavily)
  3. Search preset B2B platform site: queries (Alibaba, Made-in-China, GlobalSources, etc.)
  4. Deduplicate results by domain
  5. LLM scoring: is_company (bool) + is_relevant (bool) + score (0-10) + reason (str)
  6. Return ranked, filtered results

Configuration (.env):
    LLM_MODEL=deepseek/deepseek-chat        # required for keyword gen + scoring
    SEARCH_PROVIDER=serper                  # or tavily
    SERPER_API_KEY=...                      # if SEARCH_PROVIDER=serper
    TAVILY_API_KEY=...                      # if SEARCH_PROVIDER=tavily
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Preset B2B platform site: queries ─────────────────────────────────────
# Each entry: (platform_label, site_prefix_template)
# {keyword} will be replaced with the user's product keyword

B2B_PLATFORM_SITES: List[tuple] = [
    ("Alibaba",          "site:alibaba.com {keyword}"),
    ("Made-in-China",    "site:made-in-china.com {keyword}"),
    ("GlobalSources",    "site:globalsources.com {keyword}"),
    ("TradeIndia",       "site:tradeindia.com {keyword}"),
    ("EC21",             "site:ec21.com {keyword}"),
    ("Europages",        "site:europages.com {keyword}"),
    ("Kompass",          "site:kompass.com {keyword}"),
    ("ThomasNet",        "site:thomasnet.com {keyword}"),
]

# ── Data model ─────────────────────────────────────────────────────────────

@dataclass
class FlowResult:
    title: str = ""
    url: str = ""
    domain: str = ""
    snippet: str = ""
    search_score: float = 0.0       # raw relevance from search engine
    source_keyword: str = ""        # which keyword produced this result
    source_type: str = ""           # "keyword_search" | "b2b_platform"
    platform: str = ""              # e.g. "Alibaba" (for b2b_platform type)
    provider: str = ""              # "serper" | "tavily"

    # LLM scoring (filled by _llm_score_batch)
    is_company: bool = False
    is_relevant: bool = False
    llm_score: float = 0.0          # 0-10
    llm_reason: str = ""
    llm_scored: bool = False        # whether LLM scoring was attempted

    def to_dict(self) -> Dict:
        return asdict(self)


# ── Main flow class ────────────────────────────────────────────────────────

class B2BFlow:
    """
    Full B2B discovery pipeline.

    Usage::

        flow = B2BFlow(product="solar inverter", regions=["Germany", "Poland"])
        results = flow.run(
            keyword_count=10,
            num_search_results=10,
            gl="de",
            run_b2b_platforms=True,
            llm_filter=True,
            min_llm_score=5,
        )
    """

    def __init__(self, product: str, regions: List[str]):
        self.product = product.strip()
        self.regions = [r.strip() for r in regions if r.strip()]

    # ── Public entry point ─────────────────────────────────────────────────

    def run(
        self,
        keyword_count: int = 10,
        num_search_results: int = 10,
        gl: str = "us",
        search_delay: float = 1.2,
        run_b2b_platforms: bool = True,
        b2b_platforms: Optional[List[str]] = None,
        llm_filter: bool = True,
        min_llm_score: float = 5.0,
        extra_keywords: Optional[List[str]] = None,
        progress_cb=None,         # callable(step: str, pct: float) for UI
    ) -> Dict:
        """
        Execute the full B2B flow.

        Args:
            keyword_count:       Number of AI keywords to generate.
            num_search_results:  Results per keyword search.
            gl:                  Geographic locale for search.
            search_delay:        Seconds between search calls.
            run_b2b_platforms:   Whether to run B2B platform site: queries.
            b2b_platforms:       List of platform labels to use (None = all).
            llm_filter:          Whether to run LLM scoring.
            min_llm_score:       Minimum LLM score (0-10) to include in output.
            extra_keywords:      Additional manually specified keywords.
            progress_cb:         Optional callback for progress updates.

        Returns:
            {
                "success": bool,
                "error":   str | None,
                "keywords": List[str],
                "all_results": List[Dict],        # all deduplicated, before scoring
                "scored_results": List[Dict],     # LLM-scored, sorted by score desc
                "filtered_results": List[Dict],   # scored_results with score >= min
                "stats": Dict,
            }
        """
        def _cb(step: str, pct: float):
            if progress_cb:
                try:
                    progress_cb(step, pct)
                except Exception:
                    pass

        stats: Dict = {
            "keywords_generated": 0,
            "searches_run": 0,
            "raw_results": 0,
            "after_dedup": 0,
            "llm_scored": 0,
            "filtered": 0,
        }

        try:
            # ── Step 1: Generate keywords ──────────────────────────────────
            _cb("Generating keywords…", 0.05)
            keywords = self._generate_keywords(keyword_count)
            if extra_keywords:
                keywords = list(dict.fromkeys(keywords + extra_keywords))
            stats["keywords_generated"] = len(keywords)
            _cb(f"Generated {len(keywords)} keywords", 0.15)

            # ── Step 2: Keyword searches ───────────────────────────────────
            raw: List[FlowResult] = []
            kw_total = len(keywords)
            for i, kw in enumerate(keywords):
                _cb(f"Searching: {kw[:50]}…", 0.15 + 0.30 * (i / max(kw_total, 1)))
                try:
                    hits = self._search(kw, num_search_results, gl)
                    for h in hits:
                        h.source_keyword = kw
                        h.source_type = "keyword_search"
                    raw.extend(hits)
                    stats["searches_run"] += 1
                except Exception as exc:
                    logger.warning("Search failed for keyword '%s': %s", kw, exc)
                if i < kw_total - 1:
                    time.sleep(search_delay)

            # ── Step 3: B2B platform site: queries ─────────────────────────
            if run_b2b_platforms:
                _cb("Searching B2B platforms…", 0.46)
                platforms = self._get_platforms(b2b_platforms)
                for j, (label, tmpl) in enumerate(platforms):
                    _cb(f"B2B: {label}", 0.46 + 0.14 * (j / max(len(platforms), 1)))
                    query = tmpl.format(keyword=self.product)
                    try:
                        hits = self._search(query, num_search_results, gl)
                        for h in hits:
                            h.source_keyword = query
                            h.source_type = "b2b_platform"
                            h.platform = label
                        raw.extend(hits)
                        stats["searches_run"] += 1
                    except Exception as exc:
                        logger.warning("B2B platform search failed (%s): %s", label, exc)
                    if j < len(platforms) - 1:
                        time.sleep(search_delay)

            stats["raw_results"] = len(raw)

            # ── Step 4: Deduplicate by domain ──────────────────────────────
            _cb("Deduplicating results…", 0.62)
            deduped = self._dedup(raw)
            stats["after_dedup"] = len(deduped)

            # ── Step 5: LLM scoring ────────────────────────────────────────
            scored: List[FlowResult] = deduped
            if llm_filter:
                _cb("LLM scoring results…", 0.65)
                scored = self._llm_score_batch(deduped, progress_cb=_cb)
                scored.sort(key=lambda r: r.llm_score, reverse=True)
                stats["llm_scored"] = sum(1 for r in scored if r.llm_scored)

            # ── Step 6: Filter ─────────────────────────────────────────────
            if llm_filter:
                filtered = [r for r in scored if r.llm_scored and r.llm_score >= min_llm_score]
            else:
                filtered = scored

            stats["filtered"] = len(filtered)
            _cb("Done!", 1.0)

            return {
                "success": True,
                "error": None,
                "keywords": keywords,
                "all_results": [r.to_dict() for r in deduped],
                "scored_results": [r.to_dict() for r in scored],
                "filtered_results": [r.to_dict() for r in filtered],
                "stats": stats,
            }

        except Exception as exc:
            logger.error("B2BFlow.run failed: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "keywords": [],
                "all_results": [],
                "scored_results": [],
                "filtered_results": [],
                "stats": stats,
            }

    # ── Internal helpers ───────────────────────────────────────────────────

    def _generate_keywords(self, count: int) -> List[str]:
        """Generate keywords via keyword_generator (uses LLM)."""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from keyword_generator import generate_keywords
        return generate_keywords(self.product, self.regions, count=count)

    def _search(self, query: str, num: int, gl: str) -> List[FlowResult]:
        """Execute a single search and return FlowResult list."""
        from core.search_client import search as _search
        hits = _search(query, num_results=num, gl=gl)
        return [
            FlowResult(
                title=h["title"],
                url=h["url"],
                domain=h["domain"],
                snippet=h["snippet"],
                search_score=h["score"],
                provider=h["provider"],
            )
            for h in hits
        ]

    def _get_platforms(self, selected: Optional[List[str]]) -> List[tuple]:
        if not selected:
            return B2B_PLATFORM_SITES
        labels = {l.lower() for l in selected}
        return [(l, t) for l, t in B2B_PLATFORM_SITES if l.lower() in labels]

    def _dedup(self, results: List[FlowResult]) -> List[FlowResult]:
        """Deduplicate by domain (keep first occurrence), fallback by URL."""
        seen_domains: set = set()
        seen_urls: set = set()
        out: List[FlowResult] = []
        no_domain: List[FlowResult] = []
        for r in results:
            d = r.domain.strip().lower()
            u = r.url.strip().lower()
            if d:
                if d not in seen_domains:
                    seen_domains.add(d)
                    out.append(r)
            else:
                if u and u not in seen_urls:
                    seen_urls.add(u)
                    no_domain.append(r)
        return out + no_domain

    def _llm_score_batch(
        self,
        results: List[FlowResult],
        batch_size: int = 5,
        progress_cb=None,
    ) -> List[FlowResult]:
        """
        Score each result using LLM.
        Sends results in small batches to stay within token limits.
        """
        from core.llm_client import is_llm_available, call_llm, parse_json_response

        if not is_llm_available():
            logger.warning("LLM not available — skipping scoring")
            return results

        total = len(results)
        batches = [results[i:i + batch_size] for i in range(0, total, batch_size)]

        system = (
            "You are a B2B lead qualification expert. "
            "For each search result, decide:\n"
            "1. is_company: Is this result a real business/company? (true/false)\n"
            "2. is_relevant: Is this company potentially a buyer or distributor of the given product? (true/false)\n"
            "3. score: Rate the relevance 0-10 (10 = perfect B2B lead)\n"
            "4. reason: One short sentence explaining the score.\n\n"
            "Return ONLY a JSON array, one object per result, in the same order.\n"
            "Schema: [{\"is_company\": bool, \"is_relevant\": bool, \"score\": float, \"reason\": str}]"
        )

        for bi, batch in enumerate(batches):
            if progress_cb:
                pct = 0.65 + 0.30 * (bi / max(len(batches), 1))
                progress_cb(f"Scoring batch {bi + 1}/{len(batches)}…", pct)

            items_text = "\n".join(
                f"{i + 1}. Title: {r.title}\n   URL: {r.url}\n   Snippet: {r.snippet[:200]}"
                for i, r in enumerate(batch)
            )
            user = (
                f"Product being sold: {self.product}\n"
                f"Target regions: {', '.join(self.regions)}\n\n"
                f"Search results to evaluate:\n{items_text}"
            )

            try:
                raw = call_llm(system, user, temperature=0.2, max_tokens=1024)
                parsed = parse_json_response(raw)

                if isinstance(parsed, list) and len(parsed) == len(batch):
                    for result, item in zip(batch, parsed):
                        result.is_company = bool(item.get("is_company", False))
                        result.is_relevant = bool(item.get("is_relevant", False))
                        result.llm_score = float(item.get("score", 0.0))
                        result.llm_reason = str(item.get("reason", ""))
                        result.llm_scored = True
                else:
                    logger.warning(
                        "LLM returned %s items for batch of %s",
                        len(parsed) if isinstance(parsed, list) else "?",
                        len(batch),
                    )
                    # Mark as scored-but-neutral so they stay in results
                    for result in batch:
                        result.llm_score = 5.0
                        result.llm_scored = True

            except Exception as exc:
                logger.error("LLM scoring batch %d failed: %s", bi, exc)
                # Don't discard — just leave llm_scored=False

        return results


# ── Convenience: get available platform labels ─────────────────────────────

def get_platform_labels() -> List[str]:
    """Return list of preset B2B platform labels."""
    return [label for label, _ in B2B_PLATFORM_SITES]
