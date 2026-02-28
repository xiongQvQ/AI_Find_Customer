"""LeadExtractAgent — ReAct-based B2B lead extraction from search results.

Each URL is processed by a ReAct agent that autonomously decides how to
gather company and contact information.  The agent has 3 tools:

- **scrape_page** — fetch a URL, return markdown + auto-extracted contacts
- **google_search** — search Google for company info / official website
- **extract_lead_info** — use a fast LLM to extract structured lead JSON

The agent handles all URL types (company sites, B2B platforms, LinkedIn,
content pages) with emergent strategies — e.g. if a platform page can't
be scraped, it searches for the company's official website instead.

Design principle: give the agent good tools and a clear goal, let it
figure out the strategy.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable
from urllib.parse import urlparse

from config.settings import get_settings
from graph.state import HuntState
from tools.contact_extractor import (
    discover_contact_pages,
    extract_phone_numbers,
    extract_social_media,
    merge_contact_info,
    sanitize_phone_list,
)
from tools.email_finder import extract_emails_from_text
from tools.email_verifier import EmailVerifierTool
from tools.google_search import GoogleSearchTool
from tools.jina_reader import JinaReaderTool
from tools.llm_client import LLMTool
from tools.react_runner import ToolDef, react_loop
from tools.url_filter import classify_url

logger = logging.getLogger(__name__)

# ── Progress callback registry ────────────────────────────────────────────
# Set by _run_hunt before invoking the graph so lead_extract_node can
# broadcast per-URL progress via SSE without changing the LangGraph signature.
_progress_callback: Callable[[dict], None] | None = None


def set_progress_callback(cb: Callable[[dict], None] | None) -> None:
    """Set the module-level progress callback (called from routes._run_hunt)."""
    global _progress_callback
    _progress_callback = cb


def _emit_progress(event: str, **data: Any) -> None:
    """Emit a progress event if a callback is registered."""
    if _progress_callback:
        _progress_callback({"event": event, **data})


# ── Prompts ──────────────────────────────────────────────────────────────

LEAD_EXTRACT_PROMPT = """You are a B2B lead extraction expert. Given scraped web page content, extract ALL available company and contact information as factual data — do NOT score or judge fit here.

Output MUST be valid JSON with this structure:
{
  "is_valid_lead": true/false,
  "company_name": "...",
  "website": "...",
  "industry": "...",
  "business_types": ["manufacturer", "distributor", "importer", "wholesaler", "retailer", "agent", "installer", "integrator", "other"],
  "description": "2-3 sentence description of what the company does, its main products, and markets served",
  "contact_person": "name of key contact person, or null",
  "country_code": "two-letter ISO code or empty",
  "address": "full company address if found, or empty string",
  "phone_numbers": ["phone1", "phone2"],
  "social_media": {
    "linkedin": "LinkedIn company page URL or empty",
    "facebook": "Facebook page URL or empty",
    "twitter": "Twitter/X URL or empty",
    "instagram": "Instagram URL or empty",
    "youtube": "YouTube channel URL or empty",
    "whatsapp": "WhatsApp link or empty",
    "wechat": "WeChat ID or link or empty"
  },
  "annual_revenue": "estimated revenue range if mentioned, or empty",
  "employee_count": "employee count or range if mentioned, or empty",
  "certifications": ["ISO 9001", "CE", ...],
  "key_products": ["product1", "product2"]
}

Rules:
- is_valid_lead = true only if this page represents or belongs to a real B2B company
- If the page is not a company page (article, search engine, social feed), set is_valid_lead = false
- "website" should be the company's own official website URL if visible, otherwise use the page URL
- "business_types": list ALL that apply (e.g. a company can be both "distributor" and "installer").
- "description": 2-3 sentence description in ENGLISH (translate if source is different).
- Extract ALL contact information you can find: emails, phone numbers, social media links, physical address
- For social_media, only include platforms where you find an actual URL or ID; omit keys with empty values
- Phone numbers should include country code when available (e.g. "+49 30 12345678")
- Look carefully for contact info in headers, footers, sidebars, and "Contact Us" sections
- key_products: list the specific products/services this company offers (max 8)"""


LEAD_ASSESS_PROMPT = """You are a B2B sales qualification analyst. Your job is to score how well a prospect company fits as a potential BUYER of the seller's products.

## FUNDAMENTAL QUESTION (answer this first)
Would this prospect company plausibly BUY, USE, or DISTRIBUTE the seller's products?
Potential buyers include:
- Distributors, importers, wholesalers, trading companies that resell our products
- End-users: factories, plants, or businesses that USE our products in operations (e.g. a food/beverage factory buying filling machines, a store buying packaging)
- Retailers or resellers who carry our product category

Only set match_score = 0.0 if the prospect is a DIRECT COMPETITOR (manufactures the same products) or has ZERO plausible connection to our products.

You will be given:
- **Company Profile**: factual data extracted from the prospect's website
- **Seller Context**: the seller's products, industries, value propositions, ideal customer profile
- **Negative Criteria**: specific rules to disqualify a lead (Knockout)

## Output MUST be valid JSON:
{
  "match_score": 0.0,
  "score_breakdown": {
    "product_fit": 0.0,
    "industry_fit": 0.0,
    "business_type_fit": 0.0
  },
  "fit_reasons": [],
  "disqualify_reasons": [],
  "recommended_approach": ""
}

## Knockout Rules (CRITICAL — any one triggers match_score = 0.0)
1. Prospect is a direct competitor: manufactures/produces the SAME type of products as the seller
2. Prospect matches any of the Negative Criteria provided
3. Prospect has ZERO plausible connection to the seller's products (completely different industry)
When knocked out: list the specific reason in "disqualify_reasons", set all score_breakdown to 0.0.
Do NOT knock out end-users — a food factory, beverage plant, cosmetics brand, or retailer is a valid potential buyer of packaging/filling equipment.

## Scoring Dimensions (each 0.0-0.34, sum ≈ match_score, max 1.0)
Only score these if the prospect passes the Knockout check.

### 1. Product Fit (0.0-0.34)
Would this company PURCHASE, USE, or DISTRIBUTE the seller's specific products?
- 0.34: Company explicitly sells, imports, distributes, or installs the SAME product category — clear reseller/distributor
- 0.28: Company is an end-user that directly USES the seller's products in their operations (e.g. food/beverage/pharma/cosmetics factory buying filling or packaging machines)
- 0.20: Company sells closely related/complementary products and would logically add ours to their portfolio
- 0.08: Company operates in the same broad sector with indirect product overlap
- 0.00: No plausible reason to buy or use our products

### 2. Industry Fit (0.0-0.33)
Is this company operating in the seller's target industries?
- 0.33: Company is in one of the seller's primary target industries
- 0.20: Company is in an adjacent industry with clear crossover
- 0.08: Tangential industry connection
- 0.00: Completely different industry

### 3. Business Type Fit (0.0-0.33)
Is this company the right type of buyer/partner?
- 0.33: Exact match: distributor, importer, wholesaler, or agent for this product type
- 0.25: End-user manufacturer or retailer (food factory, beverage plant, pharma, cosmetics, grocery chain) that buys equipment/supplies in volume
- 0.15: Service company or installer who occasionally purchases our product type
- 0.00: Direct competitor/manufacturer of the same products, or completely irrelevant business type

## CRITICAL RULES FOR fit_reasons
Each reason MUST:
1. Reference a SPECIFIC fact from the company profile (company name, specific product they sell, their business type)
2. Explain WHY that specific fact makes them a good BUYER for the seller's specific products
3. Be a complete, concrete sentence in ENGLISH.

BAD: "Company is in renewable energy" — too vague, no specific facts
GOOD: "[Company] distributes solar inverters and PV panels across Germany, directly matching our target market for solar inverter sales in Europe"

BAD: "Industry match" — not a reason, just a label
GOOD: "As an electrical equipment wholesaler with 200+ retail clients in Poland, they have the distribution infrastructure to resell our low-voltage inverters at scale"

## CRITICAL RULES FOR disqualify_reasons
- List concrete red flags with specific evidence: competitor/manufacturer of same products, completely unrelated industry
- If none, return []
- MUST be in ENGLISH.

## Scoring calibration
- 0.80-1.0: Strong buyer candidate — clear fit on all 3 dimensions
- 0.55-0.79: Good fit on 2 dimensions
- 0.30-0.54: Moderate fit, worth contacting
- 0.10-0.29: Weak fit, low priority
- 0.00-0.09: Not a viable buyer — direct competitor or completely unrelated

Be inclusive: end-users in the right industry are valid leads. A food/beverage company buying packaging machines scores high even if they are not a distributor.
A generic trading company with no product specifics scores <= 0.3.
A company in a completely unrelated industry (e.g. law firm, software company) scores 0.0."""


# ── Scrape & extract helpers ─────────────────────────────────────────────

async def _scrape_page(jina: JinaReaderTool, url: str) -> str:
    """Scrape a single page, returning content or empty string on failure."""
    try:
        content = await jina.read(url)
        return content if content and len(content.strip()) >= 50 else ""
    except Exception as e:
        logger.debug("Failed to scrape %s: %s", url, e)
        return ""


def _extract_contacts_from_text(text: str) -> tuple[list[str], list[str], dict[str, str]]:
    """Extract emails, phones, and social media from raw text."""
    emails = extract_emails_from_text(text)
    phones = extract_phone_numbers(text)
    social = extract_social_media(text)
    return emails, phones, social


# ── ReAct system prompt for per-URL lead extraction ──────────────────────

REACT_LEAD_SYSTEM = """You are a B2B lead research agent. Your goal: research a URL, extract company + contact info, score their fit as a potential buyer of our products, and output a structured JSON lead.

Tools available: scrape_page, google_search, extract_lead_info, assess_lead_fit.

## Strategy by URL type

**Company website** (e.g. solartech.de):
1. scrape_page(url) → read content + auto-extracted contacts + contact page links
2. If contact_page_links found and no emails yet → scrape ONE contact page
3. extract_lead_info with all gathered content → get structured company facts
4. assess_lead_fit with the extracted company profile → get match_score and fit analysis
5. Output final JSON

**B2B platform page** (e.g. alibaba.com/supplier/..., europages.com/...):
1. scrape_page(url) → try to read the listing
2. If scrape FAILS: google_search("<company name from URL> official website") → scrape_page(official_url)
3. extract_lead_info → assess_lead_fit → output final JSON

**LinkedIn company URL** (e.g. linkedin.com/company/acme-corp):
1. Do NOT scrape LinkedIn. google_search("acme corp official website") using the company name from the URL slug
2. scrape_page(official_website) → extract_lead_info → assess_lead_fit → output final JSON

**Content page** (article, blog, directory listing):
1. scrape_page(url) → extract_lead_info → assess_lead_fit → output final JSON

## CRITICAL RULES:
- Maximum 6 tool-call rounds.
- Maximum 2 pages scraped, maximum 1 Google search.
- ALWAYS call assess_lead_fit after extract_lead_info for any real company — this gives the accurate match_score.
- When calling assess_lead_fit, pass the FULL JSON string from extract_lead_info as company_profile — do NOT summarize or truncate it.
- scrape_page auto-extracts emails, phones, and social media.
- When scrape_page fails, ALWAYS try google_search as fallback.
- Use the match_score returned by assess_lead_fit in your final JSON — do NOT invent a score.

## Final Answer
When done, output ONLY valid JSON:
{"company_name":"...","website":"...","industry":"...","description":"...","contact_person":null,"country_code":"","address":"","emails":[],"phone_numbers":[],"social_media":{},"match_score":0.0}

Output this JSON for every real company you find. Only skip if the URL is completely inaccessible and you cannot identify any company at all."""


def _build_react_tools(
    jina: JinaReaderTool,
    llm: LLMTool,
    google: GoogleSearchTool,
    insight: dict,
    *,
    _collected_contacts: dict | None = None,
) -> list[ToolDef]:
    """Build the ReAct tool definitions for lead extraction.

    Args:
        _collected_contacts: Optional mutable dict to accumulate Regex-extracted
            contacts from scrape_page / google_search tool calls. Keys:
            'emails' (set), 'phones' (set), 'social' (dict).
    """

    async def tool_scrape_page(url: str = "") -> str:
        """Scrape a web page and return its content plus auto-extracted contacts."""
        if not url.strip():
            return json.dumps({"error": "url is required"})
        content = await _scrape_page(jina, url)
        if not content:
            return json.dumps({"error": "Failed to scrape page or page has no content", "url": url})
        # Truncate to avoid huge tool results
        truncated = content[:6000]
        # Auto-extract contacts from the FULL content (not truncated)
        emails, phones, social = _extract_contacts_from_text(content)
        # Collect into the shared accumulator for post-hoc merge (P0-3)
        if _collected_contacts is not None:
            _collected_contacts["emails"].update(emails)
            _collected_contacts["phones"].update(phones)
            for k, v in social.items():
                if k not in _collected_contacts["social"]:
                    _collected_contacts["social"][k] = v
        # Discover contact page links
        contact_links = discover_contact_pages(content, url)
        result: dict[str, Any] = {
            "content": truncated,
            "content_length": len(content),
            "extracted_emails": emails,
            "extracted_phones": phones,
            "extracted_social": social,
        }
        if contact_links:
            result["contact_page_links_found"] = contact_links
        return json.dumps(result)

    async def tool_google_search(query: str = "") -> str:
        """Search Google and return results with titles, links, and snippets."""
        if not query.strip():
            return json.dumps({"error": "query is required"})
        try:
            results = await google.search(query, num=5)
            # Also extract contacts from snippets automatically
            snippet_text = " ".join(
                r.get("snippet", "") + " " + r.get("title", "")
                for r in results
            )
            emails, phones, social = _extract_contacts_from_text(snippet_text)
            # Collect into shared accumulator (P0-3)
            if _collected_contacts is not None:
                _collected_contacts["emails"].update(emails)
                _collected_contacts["phones"].update(phones)
                for k, v in social.items():
                    if k not in _collected_contacts["social"]:
                        _collected_contacts["social"][k] = v
            return json.dumps({
                "results": [
                    {"title": r.get("title", ""), "link": r.get("link", ""), "snippet": r.get("snippet", "")}
                    for r in results[:5]
                ],
                "contacts_from_snippets": {
                    "emails": emails,
                    "phone_numbers": phones,
                    "social_media": social,
                },
            })
        except Exception as e:
            return json.dumps({"error": f"Search failed: {e}"})

    async def tool_extract_lead_info(page_content: str = "") -> str:
        """Use AI to extract structured company facts from page content (no scoring)."""
        if not page_content.strip():
            return json.dumps({"error": "page_content is required — pass the scraped text"})
        prompt = f"## Page Content\n{page_content[:5000]}"
        try:
            raw = await llm.generate(
                prompt,
                system=LEAD_EXTRACT_PROMPT,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            return raw
        except Exception as e:
            return json.dumps({"error": f"LLM extraction failed: {e}"})

    async def tool_assess_lead_fit(company_profile: str = "") -> str:
        """Score how well a company fits as a buyer/distributor using the full insight context."""
        if not company_profile.strip():
            return json.dumps({"error": "company_profile is required — pass the full extracted company JSON"})
        # Build rich seller context from insight
        products = ", ".join(insight.get("products", []))
        industries = ", ".join(insight.get("industries", []))
        value_props = "; ".join(insight.get("value_propositions", []))
        target_profile = insight.get("target_customer_profile", "B2B buyer")
        target_regions = ", ".join(insight.get("recommended_regions", []))
        summary = insight.get("summary", "")
        negative_criteria = insight.get("negative_targeting_criteria", [])
        negative_text = "\n".join(f"- {c}" for c in negative_criteria) if negative_criteria else "None"
        seller_name = insight.get("company_name", "Our Company")
        # Derive preferred buyer types from target_customer_profile if available
        buyer_type_hint = "distributor, importer, wholesaler, agent, or reseller"
        if target_profile:
            # Extract business type keywords from the ICP description
            icp_lower = target_profile.lower()
            types = []
            for t in ["distributor", "importer", "wholesaler", "reseller", "retailer", "agent", "installer", "integrator"]:
                if t in icp_lower:
                    types.append(t)
            if types:
                buyer_type_hint = ", ".join(types)
        prompt = (
            f"## Prospect Company Profile\n{company_profile[:3000]}\n\n"
            f"## Seller: {seller_name}\n"
            f"Products: {products}\n"
            f"Target industries: {industries}\n"
            f"Value propositions: {value_props}\n"
            f"Company summary: {summary}\n\n"
            f"## Ideal Customer Profile (ICP)\n{target_profile}\n\n"
            f"## Preferred Buyer Types\n{buyer_type_hint}\n\n"
            f"## Negative Criteria (Knockout)\n{negative_text}\n\n"
            f"## Target Regions\n{target_regions}\n\n"
            f"## Your Task\n"
            f"Score this prospect against the 4 dimensions. "
            f"For each fit_reason, cite SPECIFIC facts from the company profile above "
            f"(their actual products, location, business type, customer base) and explain "
            f"WHY those facts make them a good match for {seller_name}'s products ({products})."
        )
        try:
            raw = await llm.generate(
                prompt,
                system=LEAD_ASSESS_PROMPT,
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            return raw
        except Exception as e:
            return json.dumps({"error": f"LLM assessment failed: {e}", "match_score": 0.3})

    return [
        ToolDef(
            name="scrape_page",
            description="Fetch and read a web page. Returns markdown content, auto-extracted emails/phones/social media, and discovered contact page links. If the page can't be scraped (anti-bot, JS-only), returns an error — use google_search as fallback.",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to scrape"},
                },
                "required": ["url"],
            },
            fn=tool_scrape_page,
        ),
        ToolDef(
            name="google_search",
            description="Search Google for information. Use this to: (1) find a company's official website when you only have a platform/LinkedIn URL, (2) find contact emails, (3) research company details. Returns results with titles, links, snippets, and auto-extracted contacts from snippets.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                },
                "required": ["query"],
            },
            fn=tool_google_search,
        ),
        ToolDef(
            name="extract_lead_info",
            description="Use AI to extract structured company facts (name, industry, description, business type, key products, contacts, etc.) from page content. Pure extraction — no fit scoring. Call this once you have gathered enough content.",
            parameters={
                "type": "object",
                "properties": {
                    "page_content": {"type": "string", "description": "The combined page content to analyze"},
                },
                "required": ["page_content"],
            },
            fn=tool_extract_lead_info,
        ),
        ToolDef(
            name="assess_lead_fit",
            description="Score how well this company fits as a buyer/distributor for our products, using the full seller insight (products, industries, value propositions, target regions, ICP). Call this after extract_lead_info for any valid company. Pass the FULL JSON output from extract_lead_info as company_profile — do not truncate. Returns match_score (0-1), score_breakdown per dimension, evidence-based fit_reasons, and recommended_approach.",
            parameters={
                "type": "object",
                "properties": {
                    "company_profile": {
                        "type": "string",
                        "description": "The extracted company profile JSON or description to assess",
                    },
                },
                "required": ["company_profile"],
            },
            fn=tool_assess_lead_fit,
        ),
    ]


async def _scrape_and_extract(
    search_result: dict,
    jina: JinaReaderTool,
    llm: LLMTool,
    semaphore: asyncio.Semaphore,
    *,
    insight: dict,
    google_search: GoogleSearchTool,
    hunt_id: str = "",
    hunt_round: int = 0,
) -> dict | None:
    """Use a ReAct agent to scrape a URL and extract lead information.

    The reasoning model decides which tools to call (scrape, google_search,
    extract_lead_info) and in what order, adapting its strategy based on
    what it finds at each step.  The URL type is provided as a hint so the
    agent can choose the right strategy (e.g. skip scraping LinkedIn).

    Returns:
        Lead dict if valid, None otherwise.
    """
    url = search_result.get("link", "")
    if not url:
        return None

    domain = urlparse(url).netloc
    url_type = classify_url(url)

    logger.info("[LeadExtract] Processing %s (type=%s)", domain, url_type)
    _emit_progress("scraping", domain=domain, url=url)

    async with semaphore:
        # P0-3: Create a shared mutable dict to collect Regex-extracted contacts
        # during the ReAct loop. These are accumulated by scrape_page and
        # google_search tool calls and merged into the final lead afterward.
        collected_contacts: dict = {
            "emails": set(),
            "phones": set(),
            "social": {},
        }

        tools = _build_react_tools(
            jina, llm, google_search, insight,
            _collected_contacts=collected_contacts,
        )

        products = ", ".join(insight.get("products", []))

        # Build URL type hint for the agent
        type_hints = {
            "company_site": "This appears to be a company's own website.",
            "platform_listing": "This is a B2B platform listing (e.g. Alibaba, Europages). The page may not be scrapable — if scrape fails, search for the company's official website.",
            "linkedin_company": "This is a LinkedIn company page. Do NOT try to scrape it — LinkedIn blocks scrapers. Instead, extract the company name from the URL slug and google_search for their official website.",
            "content_page": "This is a content page (article, blog, directory). Scrape it and look for a specific company featured in the content.",
        }
        type_hint = type_hints.get(url_type, "")

        user_prompt = (
            f"## Target URL\n{url}\n\n"
            f"## URL Type\n{type_hint}\n\n"
            f"## Our Products\n{products}\n\n"
            f"## Target Customer Profile\n{insight.get('target_customer_profile', 'B2B buyer')}\n\n"
            f"Research this URL and extract comprehensive company and contact information. "
            f"Email addresses are critical — try hard to find them."
        )

        try:
            # Pass required_json_fields for schema validation (Fix 3.2)
            raw_result = await react_loop(
                system=REACT_LEAD_SYSTEM,
                user_prompt=user_prompt,
                tools=tools,
                required_json_fields=[
                    "company_name", "website", "emails",
                    "match_score",
                ],
                hunt_id=hunt_id,
                agent="lead_extract",
                hunt_round=hunt_round,
            )
        except Exception as e:
            logger.warning("[LeadExtract] ReAct agent failed for %s: %s", domain, e)
            _emit_progress("scrape_error", domain=domain, error=str(e))
            return None

        # Parse + validate the final JSON answer
        from tools.llm_output import parse_json, validate_dict, LEAD_REQUIRED, LEAD_DEFAULTS
        parsed = parse_json(raw_result, context=f"LeadExtract:{domain}")
        if parsed is None:
            logger.warning("[LeadExtract] Invalid JSON from %s", domain)
            _emit_progress("scrape_done", domain=domain, valid=False, reason="invalid_json")
            return None

        validated = validate_dict(parsed, LEAD_REQUIRED, defaults=LEAD_DEFAULTS, context=f"LeadExtract:{domain}")
        if validated is None:
            _emit_progress("scrape_done", domain=domain, valid=False, reason="invalid_json")
            return None

        if not validated.get("company_name", "").strip():
            _emit_progress("scrape_done", domain=domain, valid=False, reason="no_company_found")
            return None

        # Build normalized lead dict
        llm_social = {
            k: v for k, v in validated.get("social_media", {}).items()
            if v and isinstance(v, str) and v.startswith("http")
        }

        lead = {
            "company_name": validated.get("company_name") or domain,
            "website": validated.get("website") or url,
            "industry": validated.get("industry", ""),
            "business_types": validated.get("business_types", []),
            "description": validated.get("description", ""),
            "emails": list(set(validated.get("emails", []))),
            "phone_numbers": sanitize_phone_list([str(p) for p in validated.get("phone_numbers", []) if p]),
            "contact_person": validated.get("contact_person"),
            "address": validated.get("address", ""),
            "social_media": llm_social,
            "match_score": min(max(float(validated.get("match_score", 0.0)), 0.0), 1.0),
            "source": domain,
            "country_code": validated.get("country_code", ""),
            "source_keyword": search_result.get("source_keyword", ""),
        }

        # ── P0-3: Merge Regex-extracted contacts into lead ────────────
        # This ensures emails/phones found by Regex during scrape_page and
        # google_search are not lost even if the ReAct agent omits them.
        lead = merge_contact_info(
            lead,
            extra_emails=list(collected_contacts["emails"]),
            extra_phones=list(collected_contacts["phones"]),
            extra_social=collected_contacts["social"],
        )

        contact_summary = (
            f"emails={len(lead['emails'])}, phones={len(lead['phone_numbers'])}, "
            f"social={list(lead['social_media'].keys())}"
        )
        logger.info("[LeadExtract] ✓ %s → %s (%s)",
                    domain, lead['company_name'], contact_summary)
        _emit_progress(
            "lead_found", domain=domain,
            company_name=lead["company_name"],
            emails=len(lead["emails"]),
            phones=len(lead["phone_numbers"]),
            social=list(lead["social_media"].keys()),
            match_score=lead["match_score"],
            lead=lead,
        )

        return lead


# ── Email verification helper (module-level for testability) ─────────────

async def _verify_lead_emails(lead: dict, verifier: EmailVerifierTool) -> dict:
    """Verify emails in a lead dict via MX record check.

    Removes undeliverable emails (domains with no MX records).
    Module-level so it can be independently unit-tested.
    """
    emails = lead.get("emails", [])
    if not emails:
        return lead
    try:
        verification_results = await verifier.verify_batch(emails)
        verified = [r["email"] for r in verification_results if r["is_deliverable"]]
        removed = len(emails) - len(verified)
        if removed > 0:
            logger.debug(
                "[LeadExtract] Removed %d undeliverable emails from %s",
                removed, lead.get("company_name", "?"),
            )
        lead["emails"] = verified
    except Exception as e:
        logger.debug("[LeadExtract] Email verification failed for %s: %s",
                     lead.get("company_name", "?"), e)
    return lead


# ── Main node ────────────────────────────────────────────────────────────

async def lead_extract_node(state: HuntState) -> dict:
    """LangGraph node: ReAct-based B2B lead extraction.

    For each search result URL:
    1. Skip truly irrelevant URLs (search engines, entertainment)
    2. Send all other URLs to a ReAct agent that autonomously decides
       how to gather company + contact info (scrape, search, extract)

    The ReAct agent handles all URL types (company sites, B2B platforms,
    LinkedIn, content pages) with emergent strategies — no hardcoded
    pipeline steps.

    Uses asyncio.Semaphore(scrape_concurrency) to limit parallel operations.
    Deduplicates leads by website domain.

    Returns:
        Dict with accumulated 'leads' list and updated keyword_search_stats.
    """
    settings = get_settings()
    search_results = state.get("search_results", [])
    existing_leads = state.get("leads", [])
    insight = state.get("insight")
    insight = insight if isinstance(insight, dict) else {}
    keyword_stats = dict(state.get("keyword_search_stats", {}))

    # Determine which URLs to process (skip already-extracted)
    existing_domains = {urlparse(l.get("website", "")).netloc for l in existing_leads}
    to_process = [
        r for r in search_results
        if urlparse(r.get("link", "")).netloc not in existing_domains
        and r.get("link", "")
    ]

    # Filter out truly irrelevant URLs (search engines, entertainment)
    processable = [r for r in to_process if classify_url(r.get("link", "")) != "irrelevant"]

    logger.info(
        "[LeadExtractAgent] %d URLs to process (%d irrelevant filtered out)",
        len(processable), len(to_process) - len(processable),
    )
    _emit_progress("deep_scrape_start", total_urls=len(processable))

    if not processable:
        logger.info("[LeadExtractAgent] No processable URLs, skipping")
        return {"current_stage": "lead_extract"}

    semaphore = asyncio.Semaphore(settings.scrape_concurrency)
    jina = JinaReaderTool()
    hunt_id = state.get("hunt_id", "")
    hunt_round = state.get("hunt_round", 0)
    llm = LLMTool(
        hunt_id=hunt_id,
        agent="lead_extract",
        hunt_round=hunt_round,
    )
    google = GoogleSearchTool()

    try:
        scrape_tasks = [
            _scrape_and_extract(
                r, jina, llm, semaphore,
                insight=insight, google_search=google,
                hunt_id=hunt_id, hunt_round=hunt_round,
            )
            for r in processable
        ]
        
        results = []
        # Use as_completed to process results as they finish (better for logging/monitoring)
        for future in asyncio.as_completed(scrape_tasks):
            try:
                res = await future
                results.append(res)
            except Exception as e:
                logger.error("[LeadExtractAgent] Task failed: %s", e)

    finally:
        await jina.close()
        await llm.close()
        await google.close()

    # ── Collect valid leads, deduplicate ─────────────────────────────────
    new_leads = []
    seen_domains = set(existing_domains)

    for lead in results:
        if lead is None:
            continue
        domain = urlparse(lead["website"]).netloc
        if domain in seen_domains:
            continue
        seen_domains.add(domain)
        new_leads.append(lead)

    # ── Verify emails via MX record check (concurrent) ───────────────────
    # Remove emails whose domains have no MX records, indicating the domain
    # cannot receive email (likely invalid or expired).
    verifier = EmailVerifierTool()
    new_leads = list(await asyncio.gather(
        *[_verify_lead_emails(lead, verifier) for lead in new_leads]
    ))

    logger.info("[LeadExtractAgent] Completed — %d new leads extracted (total: %d)",
                len(new_leads), len(existing_leads) + len(new_leads))

    # ── Update keyword_search_stats with leads_found ─────────────────────
    for lead in new_leads:
        kw = lead.get("source_keyword", "")
        if kw and kw in keyword_stats:
            keyword_stats[kw]["leads_found"] = keyword_stats[kw].get("leads_found", 0) + 1

    return {
        "leads": existing_leads + new_leads,
        "keyword_search_stats": keyword_stats,
        "current_stage": "lead_extract",
    }
