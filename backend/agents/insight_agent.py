"""InsightAgent — Universal multi-input insight generation via a single ReAct loop.

Design principle:
  1. PRE-COLLECT all inputs in code (no LLM needed for this):
     - URL  → passed as tool target for ReAct to scrape
     - Documents (PDF / Word / Excel / CSV / MD / TXT) → parsed to text, injected into prompt
     - Product keywords → injected into prompt
  2. SINGLE ReAct loop with reasoning_model gets full context upfront and can:
     - Scrape the website (and subpages) if URL provided
     - Search web for market context
     - Ask for more document content if needed
  3. Output: unified JSON insight

Why pre-parse documents instead of using a tool?
  Document parsing is deterministic (no LLM decision needed). Pre-parsing and
  injecting into the prompt is faster, cheaper, and more reliable than having
  the LLM call a tool for each file. The ReAct tool is kept for on-demand
  access to large files that exceed the initial context budget.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

from config.settings import get_settings
from graph.state import HuntState
from tools.google_search import GoogleSearchTool
from tools.jina_reader import JinaReaderTool
from tools.pdf_parser import PDFParserTool
from tools.excel_parser import ExcelParserTool
from tools.react_runner import ToolDef, react_loop

logger = logging.getLogger(__name__)

# Maximum characters of pre-parsed document content to inject per file
_MAX_DOC_CHARS_PER_FILE = 6000
# Maximum total pre-parsed document chars across all files
_MAX_TOTAL_DOC_CHARS = 16000

# ── ReAct system prompt ───────────────────────────────────────────────────

INSIGHT_REACT_SYSTEM = """You are an expert B2B market analyst. Your goal is to produce a comprehensive
insight report for B2B lead hunting by analyzing ALL available inputs.

## Available Tools
1. **scrape_page(url)** — Scrape a URL, get markdown content + discovered subpage links
2. **search_web(query)** — Search Google for market/competitor/company information
3. **read_uploaded_file(file_index)** — Read the FULL content of a large uploaded file by index
   (use this only if the pre-parsed excerpt in the prompt is insufficient)

## Strategy

You will receive a user message containing ALL pre-collected inputs:
- Document excerpts (already parsed from uploaded files)
- Website URL (if provided)
- Product keywords (if provided)
- Target regions (if provided)

**Your job is to synthesize ALL of this into one insight JSON.**

### Execution order (adapt based on what inputs are present):

1. **If a website URL is given** → scrape_page(url) first, then explore up to 3 important subpages
   (About, Products, Services pages). Combine with any document content already in the prompt.

2. **If documents were provided but NO website URL** → the document content is already in your
   prompt. Use it as primary source. Then search_web for the company name or product to find
   market context and verify/enrich the information.

3. **If only product keywords** → search_web to understand the market landscape, competitors,
   and typical buyer profiles for these products.

4. **If multiple inputs** → synthesize ALL of them. Website + documents + keywords together
   produce the richest insight. Do NOT ignore any input source.

5. **If a large file needs more content** → use read_uploaded_file(file_index) to get the full text.

## Output Format
Your FINAL output MUST be a raw JSON object (no markdown fences):
{{
  "company_name": "...",
  "products": ["specific product name 1", "specific product name 2"],
  "industries": ["industry1", "industry2"],
  "value_propositions": ["concrete differentiator 1", "concrete differentiator 2"],
  "target_customer_profile": "detailed paragraph describing ideal B2B buyer",
  "negative_targeting_criteria": ["criteria 1", "criteria 2"],
  "recommended_regions": ["region1", "region2"],
  "recommended_keywords_seed": ["keyword1", "keyword2"],
  "summary": "3-5 sentence summary of the company, its products, and market position"
}}

## Field Requirements

### products
List SPECIFIC product names/model lines — not generic terms.
- BAD: "solar products", "inverters"
- GOOD: "3-phase string inverters 5-50kW", "hybrid solar inverters with battery storage"

### value_propositions
List 3-6 CONCRETE differentiators. Each must be a complete sentence with a real advantage.
- BAD: "high quality", "good price"
- GOOD: "CE and IEC 62109 certified inverters with 10-year warranty, reducing buyer compliance risk"
- GOOD: "Factory-direct pricing with MOQ as low as 10 units, enabling small distributors to start"

### target_customer_profile
Detailed paragraph (3-5 sentences) describing the IDEAL B2B buyer:
- Business types: distributor / importer / wholesaler / retailer / installer / integrator / agent
- Company size, what they currently sell, why they need our products, geographic focus
- BAD: "B2B distributors in Europe"
- GOOD: "Mid-sized electrical equipment distributors in Germany and Poland expanding into solar.
  Typically 10-200 employees with 50+ installer clients. Need CE-certified products with after-sales support."

### negative_targeting_criteria
Specific DISQUALIFICATION criteria:
- "Exclude other manufacturers of [product]"
- "No B2C retailers or end-users"
- "No installers with < 5 employees"

### recommended_keywords_seed
10-15 search-ready phrases covering all dimensions:
1. Product + buyer role: "[product] distributor [region]"
2. Industry + application: "[industry] wholesaler [region]"
3. Value proposition: "[certification] [product] buyer"
4. Buyer type: "electrical equipment wholesale [region]"
5. Region + trade: "[product] importer [country]"
6. B2B platform: "site:europages.com [product]"
7. Certification/standard: "[cert] certified [product] distributor"

## Rules
- Scrape at most 4 pages total (homepage + up to 3 subpages)
- Do NOT make more than 2 Google searches total
- Output ALL text fields in ENGLISH regardless of source language
- Be specific and evidence-based — only state what you actually found
- After gathering sufficient information, output your final JSON immediately
"""

# ── Subpage link discovery ────────────────────────────────────────────────

_IMPORTANT_PATH_KEYWORDS = {
    # English
    "about", "company", "products", "services", "solutions",
    "industries", "partners", "portfolio", "capabilities",
    "what-we-do", "our-products", "our-services",
    # German (DE)
    "ueber-uns", "ueber", "produkte", "leistungen", "loesungen",
    "unternehmen", "dienstleistungen", "sortiment",
    # French (FR)
    "a-propos", "apropos", "produits", "services", "solutions",
    "entreprise", "societe", "qui-sommes-nous",
    # Spanish (ES)
    "nosotros", "sobre", "productos", "servicios", "soluciones",
    "empresa", "quienes-somos",
    # Italian (IT)
    "chi-siamo", "prodotti", "servizi", "azienda", "soluzioni",
    # Dutch (NL)
    "over-ons", "producten", "diensten", "oplossingen", "bedrijf",
    # Polish (PL)
    "o-nas", "produkty", "uslugi", "rozwiazania", "firma",
    # Portuguese (PT/BR)
    "sobre", "produtos", "servicos", "solucoes", "empresa",
    # Russian (RU)
    "o-kompanii", "produkty", "uslugi", "resheniya",
    # Japanese (JA) — romanized
    "kaisha", "seihin", "service",
    # Chinese (ZH) — romanized pinyin
    "guanyu", "chanpin", "fuwu", "jiejue",
}


def _discover_important_links(content: str, base_url: str) -> list[dict]:
    """Find important subpage links (About, Products, etc.) from page content."""
    base_domain = urlparse(base_url).netloc
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)', re.IGNORECASE)
    results = []
    seen = set()

    for text, href in link_pattern.findall(content):
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        if parsed.netloc != base_domain:
            continue
        path_lower = parsed.path.lower().strip("/")
        path_parts = set(path_lower.replace("_", "-").split("/"))
        if path_parts & _IMPORTANT_PATH_KEYWORDS:
            if absolute not in seen:
                seen.add(absolute)
                results.append({"url": absolute, "text": text.strip()})
                if len(results) >= 5:
                    break

    return results


# ── File parsing ──────────────────────────────────────────────────────

# Supported file extensions and their human-readable type names
_FILE_TYPE_LABELS: dict[str, str] = {
    ".pdf": "PDF document",
    ".docx": "Word document",
    ".doc": "Word document (legacy)",
    ".xlsx": "Excel spreadsheet",
    ".xls": "Excel spreadsheet (legacy)",
    ".csv": "CSV data",
    ".tsv": "TSV data",
    ".md": "Markdown document",
    ".txt": "Plain text",
    ".rtf": "Rich text",
    ".json": "JSON data",
}


def _parse_uploaded_file(file_path: str) -> str:
    """Parse an uploaded file based on its extension.

    Supported formats:
    - PDF (.pdf) — via pymupdf4llm, preserves structure as Markdown
    - Word (.docx) — via python-docx, converts to Markdown
    - Excel/CSV (.xlsx, .xls, .csv, .tsv) — via pandas, as Markdown table
    - Markdown (.md) — read directly (already Markdown)
    - Plain text / JSON / RTF (.txt, .json, .rtf) — read as UTF-8 text
    - Unknown extensions — attempt UTF-8 text read
    """
    ext = Path(file_path).suffix.lower()
    try:
        if ext == ".pdf":
            return PDFParserTool().parse(file_path)

        elif ext == ".docx":
            from tools.docx_parser import DocxParserTool
            return DocxParserTool().parse(file_path)

        elif ext == ".doc":
            # Legacy .doc: try python-docx (works for some), fallback to text
            try:
                from tools.docx_parser import DocxParserTool
                return DocxParserTool().parse(file_path)
            except Exception:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()[:10000]

        elif ext in {".xlsx", ".xls", ".csv", ".tsv"}:
            return ExcelParserTool().parse_to_markdown(file_path, max_rows=200)

        elif ext in {".md", ".txt", ".rtf", ".json"}:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()[:10000]

        else:
            # Unknown extension — attempt plain text read
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()[:10000]

    except Exception as e:
        logger.warning("Failed to parse uploaded file %s: %s", file_path, e)
        return f"[Failed to parse {Path(file_path).name}: {e}]"


def _pre_parse_documents(uploaded_files: list[str]) -> list[dict]:
    """Pre-parse all uploaded documents into text before the ReAct loop.

    Returns a list of dicts with keys:
      - index: int (0-based, for read_uploaded_file tool)
      - name: str (filename)
      - type: str (human-readable file type)
      - content: str (parsed text, truncated to _MAX_DOC_CHARS_PER_FILE)
      - full_length: int (total parsed length before truncation)
      - truncated: bool
    """
    parsed: list[dict] = []
    total_chars = 0

    for i, fp in enumerate(uploaded_files):
        ext = Path(fp).suffix.lower()
        file_type = _FILE_TYPE_LABELS.get(ext, f"file ({ext or 'unknown'}")
        content = _parse_uploaded_file(fp)
        full_len = len(content)

        # Apply per-file cap, then check total budget
        remaining_budget = max(0, _MAX_TOTAL_DOC_CHARS - total_chars)
        cap = min(_MAX_DOC_CHARS_PER_FILE, remaining_budget)
        truncated_content = content[:cap]
        total_chars += len(truncated_content)

        parsed.append({
            "index": i,
            "name": Path(fp).name,
            "type": file_type,
            "content": truncated_content,
            "full_length": full_len,
            "truncated": full_len > cap,
        })

        if total_chars >= _MAX_TOTAL_DOC_CHARS:
            # Budget exhausted — remaining files listed but not pre-parsed
            for j, remaining_fp in enumerate(uploaded_files[i + 1:], start=i + 1):
                r_ext = Path(remaining_fp).suffix.lower()
                r_type = _FILE_TYPE_LABELS.get(r_ext, f"file ({r_ext or 'unknown'}")
                parsed.append({
                    "index": j,
                    "name": Path(remaining_fp).name,
                    "type": r_type,
                    "content": "",
                    "full_length": 0,
                    "truncated": True,
                })
            break

    return parsed


# ── ReAct tool builders ───────────────────────────────────────────────────

def _build_insight_tools(
    jina: JinaReaderTool,
    google: GoogleSearchTool,
    uploaded_files: list[str],
) -> list[ToolDef]:
    """Build the ReAct tool definitions for insight generation.

    Tools provided:
    - scrape_page: scrape any URL, returns content + subpage links
    - search_web: Google search for market context
    - read_uploaded_file: on-demand full content of large files
      (only added when uploaded_files is non-empty)
    """

    async def tool_scrape_page(url: str = "") -> str:
        """Scrape a web page and return its content as markdown, plus discovered subpage links."""
        if not url.strip():
            return json.dumps({"error": "url is required"})
        try:
            content = await jina.read(url)
            if not content or len(content.strip()) < 50:
                return json.dumps({"error": "Page returned no content", "url": url})
            sublinks = _discover_important_links(content, url)
            result: dict[str, Any] = {
                "content": content[:8000],
                "content_length": len(content),
            }
            if sublinks:
                result["important_subpage_links"] = sublinks
            return json.dumps(result)
        except Exception as e:
            return json.dumps({"error": f"Failed to scrape: {e}", "url": url})

    async def tool_search_web(query: str = "") -> str:
        """Search Google for additional market/competitor information."""
        if not query.strip():
            return json.dumps({"error": "query is required"})
        try:
            results = await google.search(query, num=5)
            return json.dumps({
                "results": [
                    {"title": r.get("title", ""), "link": r.get("link", ""), "snippet": r.get("snippet", "")}
                    for r in results[:5]
                ],
            })
        except Exception as e:
            return json.dumps({"error": f"Search failed: {e}"})

    async def tool_read_uploaded_file(file_index: int = -1) -> str:
        """Read the FULL content of an uploaded file by its 0-based index.

        Use this when the pre-parsed excerpt in the prompt is truncated and
        you need more content from a specific file.
        """
        if not uploaded_files:
            return json.dumps({"error": "No uploaded files available"})
        if file_index < 0 or file_index >= len(uploaded_files):
            return json.dumps({
                "error": f"Invalid file_index {file_index}. Valid range: 0-{len(uploaded_files) - 1}",
                "available_files": [
                    {"index": i, "name": Path(f).name, "type": _FILE_TYPE_LABELS.get(Path(f).suffix.lower(), "file")}
                    for i, f in enumerate(uploaded_files)
                ],
            })
        fp = uploaded_files[file_index]
        content = _parse_uploaded_file(fp)
        return json.dumps({
            "file_index": file_index,
            "file_name": Path(fp).name,
            "content": content[:12000],
            "content_length": len(content),
            "truncated": len(content) > 12000,
        })

    tools: list[ToolDef] = [
        ToolDef(
            name="scrape_page",
            description=(
                "Scrape a web page URL and return its markdown content plus "
                "discovered subpage links (About, Products, Services, etc.)"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The full URL to scrape"},
                },
                "required": ["url"],
            },
            fn=tool_scrape_page,
        ),
        ToolDef(
            name="search_web",
            description="Search Google for company, market, competitor, or product information",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query string"},
                },
                "required": ["query"],
            },
            fn=tool_search_web,
        ),
    ]

    # Only expose read_uploaded_file tool when there are uploaded files
    if uploaded_files:
        tools.append(ToolDef(
            name="read_uploaded_file",
            description=(
                "Read the full content of an uploaded file by its index. "
                "Use only when the pre-parsed excerpt in the prompt is insufficient."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "file_index": {
                        "type": "integer",
                        "description": "0-based index of the file (shown in the prompt)",
                    },
                },
                "required": ["file_index"],
            },
            fn=tool_read_uploaded_file,
        ))

    return tools


def _build_user_prompt(
    website_url: str,
    product_keywords: list[str],
    target_regions: list[str],
    parsed_docs: list[dict],
    description: str = "",
    description_insight: str = "",
) -> str:
    """Build the rich user prompt that pre-injects ALL collected inputs.

    This is the key design decision: all deterministic inputs (documents,
    keywords, regions) are injected upfront so the ReAct loop starts with
    maximum context and only needs tools for non-deterministic exploration
    (website scraping, web search).
    """
    parts: list[str] = []

    # ── 0. User description (free-form hunt goal) ──────────────────────
    if description:
        desc_lines = [f"## User Hunt Goal (original description)\n{description}"]
        if description_insight:
            desc_lines.append(f"*AI interpretation: {description_insight}*")
        parts.append("\n".join(desc_lines))

    # ── 1. Pre-parsed document content ────────────────────────────────
    if parsed_docs:
        doc_section = [f"## Uploaded Documents ({len(parsed_docs)} file(s) — already parsed)"]
        for doc in parsed_docs:
            header = f"### [{doc['index']}] {doc['name']} ({doc['type']})"
            if doc["content"]:
                truncation_note = (
                    f"\n*(truncated — use read_uploaded_file({doc['index']}) for full content)*"
                    if doc["truncated"] else ""
                )
                doc_section.append(f"{header}\n{doc['content']}{truncation_note}")
            else:
                doc_section.append(
                    f"{header}\n*(content budget exhausted — use "
                    f"read_uploaded_file({doc['index']}) to read this file)*"
                )
        parts.append("\n\n".join(doc_section))

    # ── 2. Website URL ───────────────────────────────────────────────
    if website_url:
        parts.append(
            f"## Company Website\n{website_url}\n"
            f"Scrape this URL first, then explore important subpages (About, Products, etc.)."
        )

    # ── 3. Product keywords ──────────────────────────────────────────
    if product_keywords:
        parts.append(
            f"## Product Keywords (user-provided)\n{', '.join(product_keywords)}"
        )

    # ── 4. Target regions ────────────────────────────────────────────
    if target_regions:
        parts.append(
            f"## Target Regions (user-specified — MUST appear first in recommended_regions)\n"
            f"{', '.join(target_regions)}"
        )

    # ── 5. Strategy hint based on input combination ───────────────────
    has_docs = bool(parsed_docs)
    has_url = bool(website_url)
    has_kw = bool(product_keywords)

    if has_url and has_docs:
        hint = (
            "## Your Task\n"
            "You have BOTH a website URL and uploaded documents. "
            "Scrape the website first, then synthesize with the document content above. "
            "The documents may contain product catalogs, specs, or company profiles — use them."
        )
    elif has_url and not has_docs:
        hint = (
            "## Your Task\n"
            "Scrape the website URL above. Explore up to 3 important subpages. "
            "Optionally search_web for market context."
        )
    elif has_docs and not has_url:
        hint = (
            "## Your Task\n"
            "No website URL was provided. The document content above is your primary source. "
            "Use search_web to find the company's website or market context, then synthesize."
        )
    elif has_kw and not has_url and not has_docs:
        hint = (
            "## Your Task\n"
            "No website or documents provided. Use search_web with the product keywords above "
            "to research the market landscape and build a comprehensive insight."
        )
    else:
        hint = "## Your Task\nAnalyze all available inputs and produce the insight JSON."

    parts.append(hint)

    return "\n\n".join(parts)


# ── Main node ─────────────────────────────────────────────────────────────

async def insight_node(state: HuntState) -> dict:
    """LangGraph node: Universal multi-input insight generation via a single ReAct loop.

    Pipeline:
    1. Collect all inputs from state (URL, uploaded files, product keywords, regions)
    2. Pre-parse ALL uploaded documents in code (deterministic, no LLM needed)
    3. Build a rich user_prompt that injects all pre-parsed content upfront
    4. Run ONE ReAct loop — the reasoning model can then scrape/search as needed
    5. Parse + validate the JSON output

    Supported input combinations (any subset works):
    - URL only
    - Documents only (PDF / Word / Excel / CSV / MD / TXT)
    - Keywords only
    - URL + Documents
    - URL + Keywords
    - Documents + Keywords
    - URL + Documents + Keywords (richest insight)
    - No input → minimal fallback

    Returns:
        Dict with 'insight' key containing the parsed JSON insight,
        plus 'current_stage' update.
    """
    # ── Skip if insight already exists (resume mode) ─────────────────────
    if state.get("insight"):
        logger.info("[InsightAgent] Insight already present — skipping (resume mode)")
        return {"current_stage": "insight"}

    website_url = state.get("website_url", "") or ""
    uploaded_files = state.get("uploaded_files", []) or []
    product_keywords = state.get("product_keywords", []) or []
    target_regions = state.get("target_regions", []) or []
    description = state.get("description", "") or ""
    description_insight = state.get("description_insight", "") or ""

    logger.info(
        "[InsightAgent] Starting — url=%s, files=%d, keywords=%s, regions=%s",
        website_url or "(none)",
        len(uploaded_files),
        product_keywords,
        target_regions,
    )

    from tools.llm_output import (
        parse_json, validate_dict, INSIGHT_REQUIRED, INSIGHT_DEFAULTS,
    )

    fallback_insight = {
        **INSIGHT_DEFAULTS,
        "products": product_keywords or [],
        "recommended_regions": target_regions or [],
        "recommended_keywords_seed": product_keywords or [],
    }

    # No input at all — return minimal insight immediately (no LLM call)
    if not website_url and not uploaded_files and not product_keywords and not description:
        logger.info("[InsightAgent] No inputs provided — returning minimal fallback")
        return {
            "insight": {**fallback_insight, "summary": "No website or documents provided."},
            "current_stage": "insight",
        }

    # ── Step 1: Pre-parse all uploaded documents (pure code, no LLM) ──
    parsed_docs: list[dict] = []
    if uploaded_files:
        logger.info("[InsightAgent] Pre-parsing %d uploaded file(s)...", len(uploaded_files))
        parsed_docs = _pre_parse_documents(uploaded_files)
        for doc in parsed_docs:
            logger.info(
                "[InsightAgent] Parsed [%d] %s (%s) — %d chars%s",
                doc["index"], doc["name"], doc["type"],
                len(doc["content"]),
                " [truncated]" if doc["truncated"] else "",
            )

    # ── Step 2: Build rich user prompt with all pre-collected inputs ───
    user_prompt = _build_user_prompt(
        website_url=website_url,
        product_keywords=product_keywords,
        target_regions=target_regions,
        parsed_docs=parsed_docs,
        description=description,
        description_insight=description_insight,
    )

    # ── Step 3: Build tools and run single ReAct loop ──────────────────
    jina = JinaReaderTool()
    google = GoogleSearchTool()

    try:
        tools = _build_insight_tools(jina, google, uploaded_files)
        settings = get_settings()

        logger.info(
            "[InsightAgent] Launching ReAct loop (max_iterations=%d, model=%s)",
            settings.react_max_iterations,
            settings.reasoning_model,
        )

        raw_result = await react_loop(
            system=INSIGHT_REACT_SYSTEM,
            user_prompt=user_prompt,
            tools=tools,
            settings=settings,
            max_iterations=settings.react_max_iterations,
            hunt_id=state.get("hunt_id", ""),
            agent="insight",
            hunt_round=state.get("hunt_round", 0),
        )

        # ── Step 4: Parse + validate output ───────────────────────────
        parsed = parse_json(raw_result, context="InsightAgent")
        if parsed is None:
            raise RuntimeError(
                f"InsightAgent returned unparseable output: {raw_result[:200]}"
            )
        # Check if react_loop itself returned an error dict
        if isinstance(parsed, dict) and parsed.get("error"):
            raise RuntimeError(f"InsightAgent ReAct failed: {parsed['error']}")

        insight = validate_dict(
            parsed, INSIGHT_REQUIRED,
            defaults={**INSIGHT_DEFAULTS, **fallback_insight},
            context="InsightAgent",
        ) or fallback_insight

        # Ensure user-specified regions appear first
        if target_regions and isinstance(insight.get("recommended_regions"), list):
            existing = insight["recommended_regions"]
            merged = list(target_regions)
            for r in existing:
                if r not in merged:
                    merged.append(r)
            insight["recommended_regions"] = merged

        logger.info(
            "[InsightAgent] Completed — company=%s, products=%d, regions=%s",
            insight.get("company_name", "?"),
            len(insight.get("products", [])),
            insight.get("recommended_regions", [])[:3],
        )

    except Exception as e:
        logger.error("[InsightAgent] Failed: %s", e, exc_info=True)
        try:
            await jina.close()
            await google.close()
        except Exception as close_err:
            logger.warning("[InsightAgent] Error closing tools: %s", close_err)
        # Re-raise so the graph/hunt runner catches it and marks the hunt as failed
        raise RuntimeError(f"InsightAgent failed — aborting hunt: {e}") from e
    finally:
        try:
            await jina.close()
            await google.close()
        except Exception:
            pass

    return {
        "insight": insight,
        "current_stage": "insight",
    }
