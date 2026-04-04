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
import re
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
from tools.llm_output import parse_json
from tools.customs_router import find_customs_data as route_customs_data
from tools.react_runner import ToolDef, react_loop
from tools.url_filter import classify_url

logger = logging.getLogger(__name__)

# ── Progress callback registry ────────────────────────────────────────────
# Set by _run_hunt before invoking the graph so lead_extract_node can
# broadcast per-URL progress via SSE without changing the LangGraph signature.
_progress_callback: Callable[[dict], None] | None = None


def _candidate_budget(target_lead_count: int, scrape_concurrency: int) -> int:
    """Return a bounded candidate budget for deep extraction.

    Search often returns far more URLs than a hunt round actually needs. A
    modest multiple of the requested lead count keeps recall acceptable while
    avoiding LLM bursts that can trip provider rate limits.
    """
    target = max(1, int(target_lead_count or 0))
    concurrency = max(1, int(scrape_concurrency or 0))
    return max(12, target * 4, concurrency * 4)


def set_progress_callback(cb: Callable[[dict], None] | None) -> None:
    """Set the module-level progress callback (called from routes._run_hunt)."""
    global _progress_callback
    _progress_callback = cb


def _emit_progress(event: str, **data: Any) -> None:
    """Emit a progress event if a callback is registered."""
    if _progress_callback:
        _progress_callback({"event": event, **data})


def _derive_priority_tier(fit_score: float, contactability_score: float) -> str:
    """Derive a stable priority tier from fit and contactability."""
    if fit_score < 0.1:
        return "reject"
    if fit_score >= 0.7 and contactability_score >= 0.55:
        return "high"
    if fit_score >= 0.45 and contactability_score >= 0.35:
        return "medium"
    return "low"


def _has_concrete_customs_data(value: str | None) -> bool:
    """Return True only when customs_data contains positive, concrete trade evidence."""
    text = str(value or "").strip().lower()
    if not text:
        return False
    negative_markers = [
        "no data found",
        "no concrete customs data found",
        "no detailed customs data available",
        "no data available",
        "no public customs data",
        "not an importer/exporter",
        "not an importer",
        "not an exporter",
        "not an importer/exporter of goods",
        "not an importer/exporter of physical goods",
        "service-based",
        "engineering services provider",
        "not applicable",
    ]
    return not any(marker in text for marker in negative_markers)


def _split_person_name(name: str) -> tuple[str, str]:
    parts = [p for p in re.findall(r"[a-zA-Z]+", (name or "").lower()) if p]
    if not parts:
        return "", ""
    first = parts[0]
    last = parts[-1] if len(parts) > 1 else ""
    return first, last


_GENERIC_MAILBOX_LOCALS = {
    "info", "sales", "contact", "support", "office", "hello", "admin",
    "marketing", "service", "services", "team", "enquiry", "enquiries",
    "inquiry", "inquiries", "export", "exports", "import", "imports",
    "cs", "customerservice",
}


def _is_generic_mailbox(email: str) -> bool:
    """Return True when an email is clearly a shared/company inbox."""
    normalized = str(email or "").strip().lower()
    if not normalized or "@" not in normalized:
        return False
    local, _, _ = normalized.partition("@")
    local = local.replace("(inferred)", "").strip()
    compact = re.sub(r"[\W_]+", "", local)
    if local in _GENERIC_MAILBOX_LOCALS or compact in _GENERIC_MAILBOX_LOCALS:
        return True
    generic_tokens = {
        "info", "sales", "contact", "support", "office", "team", "admin",
        "marketing", "service", "customer", "export", "import",
    }
    return any(token in generic_tokens for token in re.split(r"[\W_]+", local) if token)


def _classify_email_pattern(name: str, email: str, domain: str) -> str | None:
    first, last = _split_person_name(name)
    if not first:
        return None
    normalized = str(email or "").strip().lower()
    if not normalized or "@" not in normalized:
        return None
    local, email_domain = normalized.split("@", 1)
    if email_domain != domain:
        return None
    if local in {"info", "sales", "contact", "support", "office", "hello", "admin"}:
        return None
    candidates = {
        "first.last": f"{first}.{last}" if last else "",
        "first_last": f"{first}_{last}" if last else "",
        "firstlast": f"{first}{last}" if last else "",
        "f.last": f"{first[:1]}.{last}" if last else "",
        "flast": f"{first[:1]}{last}" if last else "",
        "first": first,
        "last": last,
    }
    for pattern, value in candidates.items():
        if value and local == value:
            return pattern
    return None


def _render_email_pattern(name: str, pattern: str, domain: str) -> str | None:
    first, last = _split_person_name(name)
    if not first:
        return None
    local_map = {
        "first.last": f"{first}.{last}" if last else "",
        "first_last": f"{first}_{last}" if last else "",
        "firstlast": f"{first}{last}" if last else "",
        "f.last": f"{first[:1]}.{last}" if last else "",
        "flast": f"{first[:1]}{last}" if last else "",
        "first": first,
        "last": last,
    }
    local = local_map.get(pattern, "")
    if not local:
        return None
    return f"{local}@{domain}"


def _normalize_decision_maker_emails(lead: dict) -> dict:
    """Keep only person-level decision-maker emails and safe inferences."""
    decision_makers = lead.get("decision_makers", [])
    if not isinstance(decision_makers, list) or not decision_makers:
        return lead

    website_domain = _normalized_domain(str(lead.get("website", "") or ""))
    if not website_domain:
        return lead

    exact_patterns: list[str] = []
    for item in decision_makers:
        if not isinstance(item, dict):
            continue
        email = str(item.get("email", "") or "").strip().lower()
        if not email or "(inferred)" in email or email == "inferred":
            continue
        if _is_generic_mailbox(email):
            item["email"] = ""
            continue
        pattern = _classify_email_pattern(str(item.get("name", "") or ""), email, website_domain)
        if pattern:
            exact_patterns.append(pattern)

    chosen_pattern = exact_patterns[0] if exact_patterns else None

    for item in decision_makers:
        if not isinstance(item, dict):
            continue
        email = str(item.get("email", "") or "").strip()
        if not email:
            continue
        lower = email.lower()
        if _is_generic_mailbox(lower):
            item["email"] = ""
            continue
        if "(inferred)" not in lower and lower != "inferred":
            continue
        if chosen_pattern:
            inferred = _render_email_pattern(str(item.get("name", "") or ""), chosen_pattern, website_domain)
            item["email"] = f"{inferred} (inferred)" if inferred else ""
        else:
            item["email"] = ""

    lead["decision_makers"] = decision_makers
    return lead


def _apply_evidence_to_scores(lead: dict) -> dict:
    """Adjust contactability/priority using concrete contact and customs evidence.

    This is a bounded post-process step. It should improve ranking when we have
    verifiable data, but not override a genuinely poor fit.
    """
    fit_score = min(max(float(lead.get("fit_score", lead.get("match_score", 0.0)) or 0.0), 0.0), 1.0)
    contactability = min(max(float(lead.get("contactability_score", 0.0) or 0.0), 0.0), 1.0)
    customs_score = min(max(float(lead.get("customs_score", 0.0) or 0.0), 0.0), 1.0)

    if lead.get("emails"):
        contactability += 0.12
    if lead.get("phone_numbers"):
        contactability += 0.06

    decision_makers = lead.get("decision_makers", [])
    if isinstance(decision_makers, list) and decision_makers:
        contactability += 0.12
        if any(isinstance(item, dict) and str(item.get("email", "")).strip() for item in decision_makers):
            contactability += 0.08

    customs_text = str(lead.get("customs_data", "") or "").strip().lower()
    customs_evidence = [
        item for item in lead.get("evidence", [])
        if isinstance(item, dict) and "customs" in str(item.get("claim", "")).lower()
    ]
    has_customs_data = _has_concrete_customs_data(customs_text)
    if has_customs_data:
        customs_score += 0.45
    if customs_evidence:
        customs_score += min(0.35, 0.12 * len(customs_evidence))
    customs_score = min(max(customs_score, 0.0), 1.0)
    if has_customs_data:
        contactability += 0.08
    if customs_evidence:
        contactability += min(0.08, 0.03 * len(customs_evidence))

    contactability = min(max(contactability, 0.0), 1.0)
    lead["fit_score"] = fit_score
    lead["contactability_score"] = contactability
    lead["customs_score"] = customs_score

    current_priority = str(lead.get("priority_tier", "low") or "low")
    derived_priority = _derive_priority_tier(fit_score, contactability)
    if current_priority == "reject" and fit_score >= 0.1:
        lead["priority_tier"] = derived_priority
    elif current_priority in {"", "low"}:
        lead["priority_tier"] = derived_priority
    else:
        order = {"reject": 0, "low": 1, "medium": 2, "high": 3}
        lead["priority_tier"] = current_priority if order.get(current_priority, 1) >= order.get(derived_priority, 1) else derived_priority
    return lead


# ── Prompts ──────────────────────────────────────────────────────────────

LEAD_EXTRACT_PROMPT = """You are a B2B lead extraction expert. Given scraped web page content, extract ALL available company and contact information as factual data — do NOT score or judge fit here.

Output MUST be valid JSON with this structure:
{
  "is_valid_lead": true/false,
  "company_name": "...",
  "website": "...",
  "industry": "...",
  "business_types": ["manufacturer", "distributor", "importer", "wholesaler", "retailer", "agent", "installer", "integrator", "other"],
  "description": "2-3 sentence Simplified Chinese summary of what the company does, its main products, and markets served",
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
  "key_products": ["product1", "product2"],
  "decision_makers": [
    {"name": "...", "title": "...", "email": "...", "linkedin": "..."}
  ],
  "customs_data": "Simplified Chinese summary of import/export activity, top trading partners, or 'No data found'"
}

Rules:
- is_valid_lead = true only if this page represents or belongs to a real B2B company
- If the page is not a company page (article, search engine, social feed), set is_valid_lead = false
- "website" should be the company's own official website URL if visible, otherwise use the page URL
- "business_types": list ALL that apply (e.g. a company can be both "distributor" and "installer").
- "description": 2-3 sentence description in Simplified Chinese for end users. Keep company names, product names, certifications, and proper nouns in their original form when needed.
- Extract ALL contact information you can find: emails, phone numbers, social media links, physical address
- For social_media, only include platforms where you find an actual URL or ID; omit keys with empty values
- Phone numbers should include country code when available (e.g. "+49 30 12345678")
- Look carefully for contact info in headers, footers, sidebars, and "Contact Us" sections
- key_products: list the specific products/services this company offers (max 8)
- customs_data: if positive evidence exists, summarize it in Simplified Chinese; otherwise output exactly "No data found"."""


LEAD_ASSESS_PROMPT = """You are a B2B sales qualification analyst. Your job is to decide whether a prospect is a plausible CUSTOMER, CHANNEL PARTNER, or END-USER buyer of the seller's products.

## PRIMARY DECISION
Do NOT ask whether the prospect is merely industry-related. Ask:
"Would this company plausibly buy, specify, integrate, import, distribute, or use our products?"

Valid customer roles include:
- distributor, importer, wholesaler, trader, reseller
- OEM / equipment maker / appliance maker / panel builder that buys components
- end-user manufacturer or factory that uses the product category in operations
- system integrator or installer with a clear procurement role

Not every related company is a customer. Industry media, directories, schools, associations, recruiters, and pure content pages are not customers.

## Competitor rule
Only disqualify as a direct competitor when the evidence clearly shows the prospect MANUFACTURES or owns a brand of the same core product as the seller.
Do NOT auto-reject a company just because it sells related products. A distributor, importer, OEM, integrator, or reseller of similar products may still be a valid customer.

## You will be given
- Company Profile: factual data extracted from the prospect website and research
- Seller Context: seller products, industries, value propositions, ICP
- Negative Criteria: specific knockout rules

## Output MUST be valid JSON
{
  "match_score": 0.0,
  "fit_score": 0.0,
  "contactability_score": 0.0,
  "priority_tier": "high|medium|low|reject",
  "customer_role": "distributor|importer|wholesaler|oem|integrator|end_user|service|retailer|manufacturer|unknown",
  "competitor_risk": "low|medium|high",
  "evidence_strength": "low|medium|high",
  "score_breakdown": {
    "product_fit": 0.0,
    "industry_fit": 0.0,
    "business_type_fit": 0.0
  },
  "fit_reasons": [],
  "disqualify_reasons": [],
  "risk_flags": [],
  "recommended_approach": ""
}

## Reject only in these cases
1. The prospect is clearly a direct competitor manufacturing the same core product.
2. The prospect matches explicit negative criteria.
3. The prospect is clearly not a company customer at all: media, directory, association, school, recruiter, government page, or pure content page.
4. There is zero plausible path for them to buy, use, integrate, import, or distribute our products.

If uncertain, do NOT over-reject. Keep moderate scores and explain uncertainty in risk_flags.

## Scoring Dimensions
Only score after the reject check.

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
- 0.80-1.0: Strong buyer candidate with clear role, product fit, and buying path
- 0.55-0.79: Good fit with real customer evidence
- 0.30-0.54: Plausible customer, but weaker or incomplete evidence
- 0.10-0.29: Related company but weak buying path; low priority
- 0.00-0.09: Reject only for true competitor, non-company entity, or no plausible buying path

Prefer false positives over false negatives at this stage, but never hallucinate a buying role. If the evidence only shows "related company", keep scores modest and explain why."""


QUICK_GATE_PROMPT = """You are a high-recall B2B lead pre-qualification filter.

Goal: remove only clearly wrong candidates before expensive deep research.

Do NOT ask "is this company related to our industry?"
Ask:
"Is this a real company with a plausible role to buy, use, integrate, import, or distribute our products?"

## Output MUST be valid JSON
{
  "pass_gate": true,
  "entity_type": "company|directory|media|association|school|government|recruiter|unknown",
  "customer_role_guess": "distributor|importer|wholesaler|oem|integrator|end_user|service|retailer|manufacturer|unknown",
  "competitor_risk": "low|medium|high",
  "confidence": 0.0,
  "reason": "",
  "risk_flags": []
}

## Gate policy
Set pass_gate=false only for clear mismatch:
- not a real company entity page
- obvious direct competitor manufacturing the same core product
- obvious B2C-only business with no B2B or procurement signal
- clearly unrelated business with no plausible buy/use/distribute path

If uncertain, keep it.

## Critical rules
- "Related company" is not enough. Look for a plausible buyer/channel/end-user role.
- Do NOT reject a distributor/importer/OEM/integrator just because it sells related products.
- Only classify competitor_risk=high when the evidence clearly shows same-core-product manufacturing or own-brand production.
- confidence must be 0-1.
- reason must be one concise English sentence.
- risk_flags should be short tags like: competitor, directory, media, b2c_only, unrelated_industry, insufficient_data, possible_competitor.
"""


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


def _quick_gate_fallback(search_result: dict, insight: dict) -> tuple[bool, dict]:
    """Rule fallback when quick-gate LLM is unavailable."""
    maps = search_result.get("maps_data", {}) or {}
    text = " ".join([
        str(search_result.get("title", "")),
        str(maps.get("type", "")),
        " ".join(maps.get("types", []) if isinstance(maps.get("types"), list) else []),
        str(maps.get("description", "")),
    ]).lower()

    b2c_markers = ["restaurant", "cafe", "bar", "salon", "spa", "hotel", "tourist", "bakery"]
    if any(m in text for m in b2c_markers):
        return False, {
            "pass_gate": False,
            "reason": "Likely B2C-only business with weak B2B procurement signal.",
            "risk_flags": ["b2c_only"],
            "confidence": 0.75,
            "entity_type": "company",
            "customer_role_guess": "retailer",
            "competitor_risk": "low",
        }

    product_tokens = {
        tok.strip().lower()
        for p in insight.get("products", []) if isinstance(p, str)
        for tok in p.split()
        if len(tok.strip()) >= 4
    }
    competitor_markers = ["manufacturer", "factory", "producer", "oem"]
    if any(m in text for m in competitor_markers) and any(t in text for t in product_tokens):
        return False, {
            "pass_gate": False,
            "reason": "Likely direct competitor (same product family manufacturer).",
            "risk_flags": ["competitor"],
            "confidence": 0.7,
            "entity_type": "company",
            "customer_role_guess": "manufacturer",
            "competitor_risk": "high",
        }

    return True, {
        "pass_gate": True,
        "reason": "Insufficient disqualifying evidence at pre-filter stage.",
        "risk_flags": [],
        "confidence": 0.5,
        "entity_type": "company",
        "customer_role_guess": "unknown",
        "competitor_risk": "low",
    }


async def _quick_gate_candidate(search_result: dict, llm: LLMTool, insight: dict) -> tuple[bool, dict]:
    """Low-cost pre-filter before deep ReAct enrichment."""
    maps = search_result.get("maps_data", {}) or {}
    prompt = (
        "## Candidate (Google Maps / URL)\n"
        f"title: {search_result.get('title', '')}\n"
        f"website: {search_result.get('link', '') or maps.get('website', '')}\n"
        f"address: {maps.get('address', '')}\n"
        f"type: {maps.get('type', '')}\n"
        f"types: {maps.get('types', [])}\n"
        f"description: {maps.get('description', '')}\n\n"
        "## Seller context\n"
        f"products: {insight.get('products', [])}\n"
        f"target industries: {insight.get('industries', [])}\n"
        f"target customer profile: {insight.get('target_customer_profile', '')}\n"
        f"negative criteria: {insight.get('negative_targeting_criteria', [])}\n"
    )
    try:
        raw = await llm.generate(
            prompt,
            system=QUICK_GATE_PROMPT,
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        if not isinstance(raw, str):
            return _quick_gate_fallback(search_result, insight)
        parsed = parse_json(raw, context="QuickGate")
        if not isinstance(parsed, dict):
            return _quick_gate_fallback(search_result, insight)

        passed = bool(parsed.get("pass_gate", True))
        competitor_risk = str(parsed.get("competitor_risk", "")).lower().strip()
        entity_type = str(parsed.get("entity_type", "")).lower().strip()
        customer_role_guess = str(parsed.get("customer_role_guess", "")).lower().strip()
        if bool(parsed.get("suspected_competitor", False)):
            passed = False
        if competitor_risk == "high" and customer_role_guess not in {"distributor", "importer", "wholesaler", "oem", "integrator", "end_user"}:
            passed = False
        if entity_type and entity_type not in {"company", "unknown"}:
            passed = False

        return passed, {
            "pass_gate": passed,
            "reason": str(parsed.get("reason", "")) or "No reason provided",
            "risk_flags": parsed.get("risk_flags", []) if isinstance(parsed.get("risk_flags"), list) else [],
            "confidence": float(parsed.get("confidence", 0.0) or 0.0),
            "entity_type": entity_type or "unknown",
            "customer_role_guess": customer_role_guess or "unknown",
            "competitor_risk": competitor_risk or "low",
        }
    except Exception as e:
        logger.debug("[LeadExtract][QuickGate] fallback due to error: %s", e)
        return _quick_gate_fallback(search_result, insight)


def _normalized_domain(url: str) -> str:
    """Normalize URL netloc for stable dedupe keys."""
    domain = urlparse(url or "").netloc.lower().strip()
    if domain.startswith("www."):
        domain = domain[4:]
    if ":" in domain:
        domain = domain.split(":", 1)[0]
    return domain


def _official_website_domain(url: str) -> str:
    """Return domain only for official company-site URLs.

    Platform/profile/content URLs (LinkedIn, Thomasnet, etc.) are excluded
    from dedupe keys to avoid false deduplication across different companies.
    """
    if classify_url(url or "") != "company_site":
        return ""
    return _normalized_domain(url)


# ── ReAct system prompt for per-URL lead extraction ──────────────────────

REACT_LEAD_SYSTEM = """You are a B2B lead research agent. Your goal: research a candidate company, extract company + contact info, find key decision makers, verify contact channels, collect concrete customs/trade data, score their fit, and output a structured JSON lead.

Tools available: scrape_page, google_search, find_customs_data, extract_lead_info, assess_lead_fit.

## Enrichment Strategy
Beyond the initial Maps record/URL, you MUST use `google_search` to find:
1. **Official Website**: If website is missing, search by company name + address and identify the most likely official site.
2. **Decision Makers**: Search for CEO / owner / purchasing manager / sales director and capture name + title.
3. **Decision-Maker Email Inference**: Only infer a decision-maker email if you found a real same-domain employee email and can identify the company's naming pattern (e.g. first.last@, f.last@). Generic inboxes like info@ or sales@ are NOT enough to infer a person's email.
4. **Customs Data (concrete, not generic)**: Search customs/import-export datasets (e.g. Panjiva, ImportGenius, Volza, customs portals). Include specific facts when available: period, trade direction, major partner countries, and product keywords/HS-related clues.
5. **Contact Verification**: If no direct email found, search for contact page, distributor form, or procurement mailbox.

## Strategy by URL type
... (keep existing type logic)

## CRITICAL RULES:
- Maximum 8 tool-call rounds.
- ALWAYS call assess_lead_fit after extract_lead_info.
- MUST attempt to find at least one decision maker and check customs data.
- Use `find_customs_data` for customs/trade evidence before writing the final answer.
- Customs data must be tool-grounded. If `find_customs_data` does not return positive evidence, output exactly "No data found".
- Do NOT write explanatory negative customs sentences such as "no public data", "not an importer/exporter", or "service company so no customs data". Use exactly "No data found".
- For decision makers, include title and best-available email. If inferred, add "(inferred)" in email string.
- Never infer a personal email from domain alone. You must have same-domain employee email evidence plus a recognizable pattern first.
- For customs data, include at least: period, trade direction, partner countries, and source URL when available.
- Directly disqualify competitors (manufacturers of the same product).
- Use the match_score returned by assess_lead_fit in your final JSON.
- Use Simplified Chinese for user-facing summary fields such as description, customs_data, and evidence.claim. Keep names, product model numbers, HS codes, and URLs unchanged.

## Final Answer
When done, output ONLY valid JSON:
{"company_name":"...","website":"...","industry":"...","description":"...","contact_person":null,"country_code":"","address":"","emails":[],"phone_numbers":[],"social_media":{},"match_score":0.0,"fit_score":0.0,"contactability_score":0.0,"priority_tier":"high|medium|low|reject","decision_makers":[{"name":"","title":"","email":"","linkedin":"","source_url":""}],"customs_data":"","evidence":[{"claim":"","source_url":""}]}
"""


def _build_react_tools(
    jina: JinaReaderTool,
    llm: LLMTool,
    google: GoogleSearchTool,
    insight: dict,
    *,
    _collected_contacts: dict | None = None,
    _collected_customs: dict | None = None,
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

    async def tool_find_customs_data(
        company_name: str = "",
        website: str = "",
        country: str = "",
        product_keywords: list[str] | None = None,
    ) -> str:
        """Find concrete customs/trade evidence using provider-aware routing."""
        if not company_name.strip():
            return json.dumps({"error": "company_name is required"})
        try:
            payload = await route_customs_data(
                company_name=company_name,
                website=website,
                country=country,
                product_keywords=product_keywords or list(insight.get("products", [])),
                google_search=google,
                jina_reader=jina,
            )
            if _collected_customs is not None and payload.get("status") == "ok":
                _collected_customs["result"] = payload
            return json.dumps(payload)
        except Exception as e:
            return json.dumps({"error": f"Customs lookup failed: {e}"})

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
            name="find_customs_data",
            description="Find concrete customs/import-export evidence for a company using provider-specific search and fetch logic. Use this before finalizing customs_data. Returns structured JSON with summary and evidence URLs.",
            parameters={
                "type": "object",
                "properties": {
                    "company_name": {"type": "string", "description": "The company legal or trading name"},
                    "website": {"type": "string", "description": "Official website URL if known"},
                    "country": {"type": "string", "description": "Country hint such as Germany"},
                    "product_keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional product keywords to improve HS/product matching",
                    },
                },
                "required": ["company_name"],
            },
            fn=tool_find_customs_data,
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
    maps_data = search_result.get("maps_data", {}) or {}
    maps_title = (search_result.get("title") or maps_data.get("title") or "").strip()
    if not url and not maps_title:
        return None

    domain = urlparse(url).netloc if url else maps_title
    url_type = classify_url(url) if url else "maps_place"

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
        collected_customs: dict = {"result": None}

        tools = _build_react_tools(
            jina, llm, google_search, insight,
            _collected_contacts=collected_contacts,
            _collected_customs=collected_customs,
        )

        products = ", ".join(insight.get("products", []))

        # Build URL type hint for the agent
        type_hints = {
            "company_site": "This appears to be a company's own website.",
            "platform_listing": "This is a B2B platform listing (e.g. Alibaba, Europages). The page may not be scrapable — if scrape fails, search for the company's official website.",
            "linkedin_company": "This is a LinkedIn company page. Do NOT try to scrape it — LinkedIn blocks scrapers. Instead, extract the company name from the URL slug and google_search for their official website.",
            "content_page": "This is a content page (article, blog, directory). Scrape it and look for a specific company featured in the content.",
            "maps_place": "This is a Google Maps business place record. If website exists, prioritize that site. If website is missing, use google_search with company name + address to find official website and contacts first.",
        }
        type_hint = type_hints.get(url_type, "")
        maps_context = ""
        if maps_title or maps_data:
            maps_context = (
                "## Google Maps Context\n"
                f"title: {maps_title or '(none)'}\n"
                f"address: {maps_data.get('address', '')}\n"
                f"type: {maps_data.get('type', '')}\n"
                f"types: {maps_data.get('types', [])}\n"
                f"website: {maps_data.get('website', '') or url}\n"
                f"phone: {maps_data.get('phoneNumber', '') or maps_data.get('phone_number', '')}\n"
                f"description: {maps_data.get('description', '')}\n"
                f"email: {maps_data.get('email', '')}\n"
            )

        user_prompt = (
            f"## Target URL\n{url}\n\n"
            f"## URL Type\n{type_hint}\n\n"
            f"{maps_context}\n"
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
                    "match_score", "decision_makers",
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

        existing_phones = sanitize_phone_list([str(p) for p in validated.get("phone_numbers", []) if p])
        maps_phone = str(maps_data.get("phone_number", "") or maps_data.get("phoneNumber", "")).strip()
        if maps_phone:
            existing_phones = sanitize_phone_list(existing_phones + [maps_phone])

        existing_emails = list(set(validated.get("emails", [])))
        maps_email = str(maps_data.get("email", "")).strip()
        if maps_email:
            existing_emails = list(set(existing_emails + [maps_email]))

        lead = {
            "company_name": validated.get("company_name") or domain,
            "website": validated.get("website") or url or maps_data.get("website", ""),
            "industry": validated.get("industry", ""),
            "business_types": validated.get("business_types", []),
            "description": validated.get("description", "") or maps_data.get("description", ""),
            "emails": existing_emails,
            "phone_numbers": existing_phones,
            "contact_person": validated.get("contact_person"),
            "address": validated.get("address", "") or maps_data.get("address", ""),
            "social_media": llm_social,
            "match_score": min(max(float(validated.get("match_score", 0.0)), 0.0), 1.0),
            "fit_score": min(max(float(validated.get("fit_score", validated.get("match_score", 0.0))), 0.0), 1.0),
            "contactability_score": min(max(float(validated.get("contactability_score", 0.0)), 0.0), 1.0),
            "customs_score": min(max(float(validated.get("customs_score", 0.0)), 0.0), 1.0),
            "priority_tier": str(validated.get("priority_tier", "low") or "low"),
            "customer_role": str(validated.get("customer_role", "unknown") or "unknown"),
            "competitor_risk": str(validated.get("competitor_risk", "low") or "low"),
            "evidence_strength": str(validated.get("evidence_strength", "low") or "low"),
            "risk_flags": validated.get("risk_flags", []) if isinstance(validated.get("risk_flags", []), list) else [],
            "source": domain,
            "country_code": validated.get("country_code", ""),
            "source_keyword": search_result.get("source_keyword", ""),
            "decision_makers": validated.get("decision_makers", []),
            "customs_records": validated.get("customs_records", []) if isinstance(validated.get("customs_records", []), list) else [],
            "customs_data": validated.get("customs_data", ""),
            "evidence": validated.get("evidence", []) if isinstance(validated.get("evidence", []), list) else [],
            "maps_data": maps_data,
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
        customs_result = collected_customs.get("result") if isinstance(collected_customs, dict) else None
        if isinstance(customs_result, dict) and customs_result.get("status") == "ok":
            customs_summary = str(customs_result.get("summary", "")).strip()
            current_customs = str(lead.get("customs_data", "") or "").strip()
            if customs_summary and current_customs.lower() in {"", "no data found", "no concrete customs data found"}:
                lead["customs_data"] = customs_summary
            lead["customs_records"] = [
                item for item in customs_result.get("evidence", [])
                if isinstance(item, dict)
            ]
            existing_urls = {
                str(item.get("source_url", ""))
                for item in lead.get("evidence", [])
                if isinstance(item, dict)
            }
            for item in customs_result.get("evidence", []):
                if not isinstance(item, dict):
                    continue
                source_url = str(item.get("source_url", ""))
                if not source_url or source_url in existing_urls:
                    continue
                parts = []
                if item.get("provider"):
                    parts.append(str(item["provider"]))
                if item.get("trade_direction"):
                    parts.append(str(item["trade_direction"]).replace("_", "/"))
                if item.get("period"):
                    parts.append(f"period {item['period']}")
                if item.get("partner_countries"):
                    parts.append(f"partners {', '.join(item['partner_countries'])}")
                lead["evidence"].append({
                    "claim": "Customs evidence: " + "; ".join(parts) if parts else "Customs evidence",
                    "source_url": source_url,
                })
                existing_urls.add(source_url)
        elif not _has_concrete_customs_data(lead.get("customs_data", "")):
            lead["customs_data"] = "No data found"
            lead["customs_records"] = []

        lead = _normalize_decision_maker_emails(lead)
        lead = _apply_evidence_to_scores(lead)

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

    # Determine which URLs to process (skip only by official website domain).
    existing_domains = {
        d for d in (_official_website_domain(l.get("website", "")) for l in existing_leads)
        if d
    }
    to_process = []
    seen_candidate_domains: set[str] = set(existing_domains)
    for r in search_results:
        link = r.get("link", "")
        maps_title = (r.get("title") or (r.get("maps_data") or {}).get("title") or "").strip()
        if not link and not maps_title:
            continue
        link_official_domain = _official_website_domain(link)
        if link_official_domain and link_official_domain in existing_domains:
            continue
        if link_official_domain and link_official_domain in seen_candidate_domains:
            continue
        if link_official_domain:
            seen_candidate_domains.add(link_official_domain)
        to_process.append(r)

    # Filter out truly irrelevant URLs (search engines, entertainment)
    processable = [
        r for r in to_process
        if (not r.get("link")) or classify_url(r.get("link", "")) != "irrelevant"
    ]

    logger.info(
        "[LeadExtractAgent] %d URLs to process (%d irrelevant filtered out)",
        len(processable), len(to_process) - len(processable),
    )

    if not processable:
        logger.info("[LeadExtractAgent] No processable URLs, skipping")
        return {"current_stage": "lead_extract"}

    candidate_budget = _candidate_budget(
        state.get("target_lead_count", 0),
        settings.scrape_concurrency,
    )
    if len(processable) > candidate_budget:
        logger.info(
            "[LeadExtractAgent] Trimming candidates from %d to %d based on target_lead_count=%s",
            len(processable),
            candidate_budget,
            state.get("target_lead_count", 0),
        )
        processable = processable[:candidate_budget]

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
        # ── Quick Gate: low-cost pre-filter before deep ReAct ───────────
        async def _run_gate(r: dict) -> tuple[dict, bool, dict]:
            async with semaphore:
                try:
                    passed, gate = await _quick_gate_candidate(r, llm, insight)
                    return r, passed, gate
                except Exception as e:
                    logger.warning("[LeadExtract][QuickGate] gate failed, fallback keep: %s", e)
                    return r, True, {"reason": "gate_error_fallback_keep", "risk_flags": ["insufficient_data"], "confidence": 0.0}

        gated_candidates: list[dict] = []
        filtered_count = 0
        gate_tasks = [_run_gate(r) for r in processable]
        for future in asyncio.as_completed(gate_tasks):
            row, passed, gate = await future
            if passed:
                row["quick_gate"] = gate
                gated_candidates.append(row)
            else:
                filtered_count += 1
                _emit_progress(
                    "gate_filtered",
                    domain=(urlparse(row.get("link", "")).netloc or row.get("title", "unknown")),
                    reason=gate.get("reason", ""),
                    risk_flags=gate.get("risk_flags", []),
                    confidence=gate.get("confidence", 0.0),
                )

        logger.info(
            "[LeadExtractAgent] QuickGate kept %d / %d candidates (filtered=%d)",
            len(gated_candidates), len(processable), filtered_count,
        )
        _emit_progress("deep_scrape_start", total_urls=len(gated_candidates), filtered_by_gate=filtered_count)

        if not gated_candidates:
            logger.info("[LeadExtractAgent] All candidates filtered by quick gate, skipping ReAct extraction")
            return {"current_stage": "lead_extract"}

        scrape_tasks = [
            _scrape_and_extract(
                r, jina, llm, semaphore,
                insight=insight, google_search=google,
                hunt_id=hunt_id, hunt_round=hunt_round,
            )
            for r in gated_candidates
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
        official_domain = _official_website_domain(lead.get("website", ""))
        if official_domain and official_domain in seen_domains:
            continue
        if official_domain:
            seen_domains.add(official_domain)
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
