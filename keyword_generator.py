#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
B2B Keyword Generator
Generates search keywords for B2B company discovery based on product description and target regions.
Keywords cover 7 dimensions: buyer role, industry, value proposition, buyer type,
region+trade terms, B2B platforms, and certifications.

Usage:
    python keyword_generator.py --product "solar inverter" --region "Germany,Poland"
    python keyword_generator.py --product "hydraulic pump" --region "USA" --count 20
    python keyword_generator.py --product "LED lighting" --region "France" --output my_keywords.json
"""

import os
import sys
import json
import argparse
import time
from dotenv import load_dotenv

load_dotenv()

import sys, os as _os
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from core.llm_client import call_llm, is_llm_available, get_llm_model, parse_json_response

OUTPUT_DIR = "output"
KEYWORD_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "keywords")
for d in [OUTPUT_DIR, KEYWORD_OUTPUT_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

# ── LLM provider setup ────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert B2B keyword strategist specializing in international trade and export sales.
Your task is to generate high-quality search keywords that help exporters find potential B2B buyers,
distributors, importers, and wholesalers for their products.

Each batch of keywords MUST cover multiple dimensions — do NOT generate all from the same dimension:

1. **Product + buyer role** — e.g. "solar inverter distributor Germany", "hydraulic pump importer Poland"
2. **Industry + application** — e.g. "renewable energy wholesaler Europe", "construction equipment dealer Italy"
3. **Value proposition** — e.g. "CE certified solar panel supplier", "OEM hydraulic components buyer"
4. **Buyer type** — e.g. "electrical equipment wholesale company", "industrial parts reseller"
5. **Region + trade term** — e.g. "solar products import export Spain", "photovoltaic dealer Eastern Europe"
6. **B2B platform** — e.g. "site:europages.com solar inverter", "site:kompass.com hydraulic pump"
7. **Certification/standard** — e.g. "CE certified inverter buyer", "ISO 9001 supplier distributor"

Rules:
- Generate exactly {count} keywords as a JSON array of strings
- Each keyword must be a specific, search-ready phrase (3-8 words)
- Every keyword MUST target the specified regions
- Spread keywords across at least 5 different dimensions
- Prefer long-tail specific phrases over generic ones
- {local_language_instruction}

Output MUST be valid JSON:
{{"keywords": ["keyword 1", "keyword 2", ...]}}"""

USER_PROMPT_TEMPLATE = """Generate {count} B2B search keywords for the following:

Product/Service: {product}
Target Regions: {regions}
{extra_context}

Generate keywords that help find distributors, importers, wholesalers, and B2B buyers for this product in the specified regions."""


# ── Language instructions per region ─────────────────────────────────────

_REGION_LANGUAGE_MAP = {
    "germany": ("German", "de"),
    "deutschland": ("German", "de"),
    "france": ("French", "fr"),
    "spain": ("Spanish", "es"),
    "espana": ("Spanish", "es"),
    "italy": ("Italian", "it"),
    "italia": ("Italian", "it"),
    "netherlands": ("Dutch", "nl"),
    "poland": ("Polish", "pl"),
    "polska": ("Polish", "pl"),
    "portugal": ("Portuguese", "pt"),
    "russia": ("Russian", "ru"),
    "japan": ("Japanese", "ja"),
    "korea": ("Korean", "ko"),
    "china": ("Chinese", "zh"),
    "brazil": ("Portuguese", "pt"),
    "mexico": ("Spanish", "es"),
    "turkey": ("Turkish", "tr"),
    "ukraine": ("Ukrainian", "uk"),
}


def _get_language_instruction(regions: list[str]) -> str:
    """Build a language instruction string based on target regions."""
    detected = {}
    for region in regions:
        key = region.strip().lower()
        for region_key, (lang_name, lang_code) in _REGION_LANGUAGE_MAP.items():
            if region_key in key:
                detected[lang_code] = lang_name
                break

    if not detected:
        return "Generate all keywords in English."

    langs = list(detected.values())
    lang_str = " and ".join(langs)
    pct_per_lang = 60 // len(langs)
    return (
        f"The target region(s) primarily use {lang_str}. "
        f"Generate approximately {pct_per_lang}% of keywords in each local language "
        f"and the remainder in English. Local-language keywords find SMEs who may not have English websites."
    )


# ── LLM helpers ──────────────────────────────────────────────────────────

def _parse_keywords(raw: str) -> list[str]:
    """Parse keywords from LLM JSON output via core/llm_client.parse_json_response."""
    parsed = parse_json_response(raw)
    if parsed is None:
        return []
    if isinstance(parsed, list):
        return [k for k in parsed if isinstance(k, str)]
    if isinstance(parsed, dict):
        for key in ("keywords", "keyword_list", "results", "data"):
            if key in parsed and isinstance(parsed[key], list):
                return [k for k in parsed[key] if isinstance(k, str)]
    return []


# ── Core generator function ───────────────────────────────────────────────

def generate_keywords(
    product: str,
    regions: list[str],
    count: int = 20,
    extra_context: str = "",
) -> list[str]:
    """
    Generate B2B search keywords using LLM.

    Args:
        product: Product or service description (e.g. "solar inverter", "hydraulic pump")
        regions: List of target regions (e.g. ["Germany", "Poland"])
        count: Number of keywords to generate (default 20)
        extra_context: Optional extra context (buyer type, use case, etc.)

    Returns:
        List of keyword strings

    Raises:
        ValueError: If LLM_MODEL is not configured
    """
    lang_instruction = _get_language_instruction(regions)
    system = SYSTEM_PROMPT.format(count=count, local_language_instruction=lang_instruction)

    extra_str = f"Additional context: {extra_context}" if extra_context else ""
    user = USER_PROMPT_TEMPLATE.format(
        count=count,
        product=product,
        regions=", ".join(regions),
        extra_context=extra_str,
    )

    print(f"Generating {count} keywords for: {product} → {', '.join(regions)}")
    raw = call_llm(system, user, temperature=0.6, max_tokens=2048)
    keywords = _parse_keywords(raw)

    if not keywords:
        print("Warning: LLM returned no parseable keywords")
        return []

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for kw in keywords:
        kl = kw.lower()
        if kl not in seen:
            seen.add(kl)
            unique.append(kw)

    return unique[:count]


def save_keywords(keywords: list[str], product: str, regions: list[str], output_file: str = "") -> str:
    """Save keywords to JSON file and print them. Returns the output file path."""
    if not output_file:
        ts = int(time.time())
        product_str = product.replace(" ", "_").lower()[:30]
        product_str = "".join(c for c in product_str if c.isalnum() or c == "_")
        region_str = "_".join(r.replace(" ", "").lower() for r in regions[:2])
        output_file = os.path.join(KEYWORD_OUTPUT_DIR, f"keywords_{product_str}_{region_str}_{ts}.json")

    data = {
        "product": product,
        "regions": regions,
        "count": len(keywords),
        "keywords": keywords,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nKeywords saved to: {output_file}")
    return output_file


def print_keywords(keywords: list[str], product: str, regions: list[str]) -> None:
    """Print keywords in a formatted way."""
    print(f"\n{'='*60}")
    print(f"Generated {len(keywords)} keywords for: {product}")
    print(f"Target regions: {', '.join(regions)}")
    print(f"{'='*60}")
    for i, kw in enumerate(keywords, 1):
        print(f"  {i:2d}. {kw}")
    print(f"{'='*60}")
    print("\nTip: Use these keywords with serper_company_search.py --custom-query")
    print("Example:")
    if keywords:
        print(f'  python serper_company_search.py --general-search --custom-query "{keywords[0]}" --gl us')


# ── CLI ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate B2B search keywords using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python keyword_generator.py --product "solar inverter" --region "Germany,Poland"
  python keyword_generator.py --product "hydraulic pump" --region "USA" --count 20
  python keyword_generator.py --product "LED lighting" --region "France,Spain" --context "wholesalers only"
  python keyword_generator.py --product "solar panel" --region "Germany" --output my_keywords.json
        """
    )
    parser.add_argument("--product", "-p", required=True,
                        help="Product or service description (e.g. 'solar inverter')")
    parser.add_argument("--region", "-r", required=True,
                        help="Target regions, comma-separated (e.g. 'Germany,Poland,France')")
    parser.add_argument("--count", "-n", type=int, default=20,
                        help="Number of keywords to generate (default: 20)")
    parser.add_argument("--context", "-c", default="",
                        help="Additional context: buyer type, use case, etc.")
    parser.add_argument("--output", "-o", default="",
                        help="Output JSON file path (auto-generated if not specified)")
    parser.add_argument("--no-save", action="store_true",
                        help="Print keywords only, do not save to file")

    args = parser.parse_args()

    regions = [r.strip() for r in args.region.split(",") if r.strip()]
    if not regions:
        print("Error: at least one region is required")
        sys.exit(1)

    if not is_llm_available():
        model = get_llm_model()
        if not model:
            print("Error: LLM_MODEL is not configured.")
            print("Please set LLM_MODEL in your .env file, e.g.:")
            print("  LLM_MODEL=openai/gpt-4o-mini")
            print("  LLM_MODEL=deepseek/deepseek-chat")
            print("  LLM_MODEL=volcengine/doubao-1-5-pro-256k-250115")
        else:
            print(f"Error: LLM_MODEL is set to '{model}' but the required API key is missing.")
        sys.exit(1)

    try:
        keywords = generate_keywords(
            product=args.product,
            regions=regions,
            count=args.count,
            extra_context=args.context,
        )
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error generating keywords: {e}")
        sys.exit(1)

    if not keywords:
        print("No keywords were generated. Please check your LLM configuration.")
        sys.exit(1)

    print_keywords(keywords, args.product, regions)

    if not args.no_save:
        save_keywords(keywords, args.product, regions, args.output)


if __name__ == "__main__":
    main()
