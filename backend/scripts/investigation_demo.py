#!/usr/bin/env python3
"""
外贸深度背调智能体 (B2B Foreign Trade Investigation Agent) — Standalone Demo
============================================================================

Architecture:
  - TRUE ReAct loop: the LLM DECIDES which tools to call, when to call them,
    and when to stop. No hard-coded "Step 1 / Step 2" flow.
  - Tools:
      1. search_web(query)       — Google Search via Serper (covers YouTube too with site: filter)
      2. scrape_website(url)     — Jina Reader for full text of any page
      3. customs_lookup(company) — 52wmb-style customs data (mock for demo, API-ready)
  - LLM: reads API keys from backend/.env via python-dotenv
  - Output: structured JSON investigation report

Usage:
  cd /Users/xiongbojian/work/ai_hunter/backend
  python scripts/investigation_demo.py

  Or with a custom target:
  python scripts/investigation_demo.py --company "Joybuy" --domain "joybuy.com"
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Awaitable, Callable

import httpx
import litellm
from dotenv import load_dotenv

# ─── Setup ───────────────────────────────────────────────────────────────────

# Load .env from the backend directory
ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# Silence noisy litellm / httpx logs unless debug
logging.getLogger("litellm").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
litellm.set_verbose = False

# Fix: Anthropic-compatible APIs (incl. MiniMax) require tools= even on final
# answer turns. With modify_params=True, litellm injects a dummy no-op tool
# so the last "force final answer" call doesn't blow up.
litellm.modify_params = True

# ─── LLM Config ──────────────────────────────────────────────────────────────

TEMPERATURE = float(os.getenv("REASONING_TEMPERATURE", "0.2"))
MAX_TOKENS = int(os.getenv("REASONING_MAX_TOKENS", "4096"))
MAX_ITERATIONS = int(os.getenv("REACT_MAX_ITERATIONS", "10"))

# Inject API keys for litellm
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
MINIMAX_KEY = os.getenv("MINIMAX_API_KEY", "")
MINIMAX_BASE = os.getenv("MINIMAX_API_BASE", "")

# Smart model selection: MiniMax first (as requested), then OpenRouter, then Anthropic native
if MINIMAX_KEY and MINIMAX_BASE:
    MODEL = os.getenv("REASONING_MODEL", "anthropic/MiniMax-M2.5")
    os.environ["ANTHROPIC_API_KEY"] = MINIMAX_KEY
    os.environ["ANTHROPIC_API_BASE"] = MINIMAX_BASE
    logger.info(f"Using MiniMax M2.5 via Anthropic-compatible endpoint")
elif OPENROUTER_KEY:
    MODEL = "openrouter/google/gemini-flash-1.5-8b"
    os.environ["OPENROUTER_API_KEY"] = OPENROUTER_KEY
    logger.info(f"Using OpenRouter (gemini-flash-1.5-8b) as fallback")
elif ANTHROPIC_KEY:
    MODEL = "claude-3-5-haiku-20241022"
    os.environ["ANTHROPIC_API_KEY"] = ANTHROPIC_KEY
    logger.info(f"Using native Anthropic (claude-3-5-haiku) as final fallback")
else:
    MODEL = os.getenv("REASONING_MODEL", "anthropic/MiniMax-M2.5")
    logger.warning("No recognized API key found. Will attempt with env defaults.")

SERPER_KEY = os.getenv("SERPER_API_KEY", "")
JINA_KEY = os.getenv("JINA_API_KEY", "")

# ─── System Prompt ────────────────────────────────────────────────────────────

INVESTIGATION_SYSTEM_PROMPT = """你是一位顶级的外贸尽职调查专家和企业情报分析师。你的唯一任务是对一家 B2B 企业进行深度、多维度的背景调查，并生成结构化的 JSON 调查报告。

**重要语言要求：所有 JSON 字段的值（value）必须使用中文填写。**

你有以下五个工具可以使用：

1. **search_web(query)** — 执行 Google 搜索，适用于：
   - 查询海关/提单记录：`"[公司名]" "bill of lading" OR "customs records"`
   - 查找 YouTube 展会视频：`"[公司名]" exhibition site:youtube.com`
   - 查询风险/负面信息：`"[公司名]" sanctions OR lawsuit OR fraud`
   - 域名/身份核验：`"[domain]" whois history company founded`

2. **scrape_website(url)** — 抓取任意 URL 的完整内容，适用于：
   - 公司官网主页（了解产品定位）
   - LinkedIn 公司主页
   - 搜索结果中发现的任意有价值 URL

3. **customs_lookup(company_name)** — 查询 52wmb 海关数据库，返回：
   - 进出口提单总数、HS 编码、目标市场、出口趋势

4. **find_key_contacts(company_name, domain)** — 搜索公司关键决策人，返回：
   - CEO/创始人/采购总监/外贸负责人的姓名、职位
   - LinkedIn 主页链接（可进一步抓取）
   - 猜测邮箱格式

5. **analyze_website_traffic(domain)** — 分析公司网站流量，返回：
   - 月均访客量级（估算）
   - 主要流量来源国（前3位）
   - 主要流量渠道（搜索/直接/社媒）
   - 核心关键词（判断真实目标市场）

## 调查策略

请按"思考 → 行动 → 观察"的 ReAct 模式逐步推进，工具调用顺序由你根据结果自主决定。
目标是从以下**七个维度**收集证据：

1. **贸易维度 (Trade)** — 调用 customs_lookup → 若无数据则 search_web 查提单记录
2. **身份维度 (Identity)** — scrape_website 官网 + search_web 查成立年份/Whois
3. **声誉维度 (Reputation)** — search_web 查制裁/诉讼/负面新闻
4. **市场存在度 (Market Presence)** — search_web 查 YouTube/展会记录
5. **采购意向 (Intent Signals)** — search_web 查 LinkedIn 招聘信号
6. **关键联系人 (Key Contacts)** — 调用 find_key_contacts 获取决策人姓名和职位 ← **必须执行**
7. **网站流量 (Web Traffic)** — 调用 analyze_website_traffic 判断真实目标市场 ← **必须执行**

## 推理规则
- 不要固定顺序，根据每次工具返回结果灵活调整。
- 如果海关数据为空，这不是终点——立即切换到其他维度。
- **find_key_contacts 和 analyze_website_traffic 必须在每次调查中执行**。
- 收集足够信息后（通常 6-8 次工具调用），立即停止并生成最终 JSON。

## 最终输出格式
调查完成后，只输出原始 JSON 对象（不要用 markdown 代码块包裹），所有字段值用中文：
{
  "company_name": "目标公司名称",
  "domain": "官网域名",
  "investigation_date": "调查日期",
  "overall_score": <1-10的整数>,
  "overall_rating": "高潜力 | 中等 | 低优先级 | 高风险",
  "dimensions": {
    "trade": {
      "has_customs_record": true/false,
      "shipment_volume": "提单数量描述",
      "top_hs_codes": ["HS编码及品类说明"],
      "major_buyers": ["主要采购商或目标国"],
      "trend": "趋势描述",
      "risk_flags": []
    },
    "identity": {
      "founded_year": "成立年份",
      "website_quality": "专业 | 一般 | 可疑",
      "office_location": "办公地点",
      "company_type": "制造商 | 分销商 | 代理商 | 未知"
    },
    "reputation": {
      "sanctions_found": false,
      "legal_issues": [],
      "media_sentiment": "正面 | 中性 | 负面"
    },
    "market_presence": {
      "exhibitions_found": [],
      "youtube_videos": [],
      "social_media_active": true/false
    },
    "intent_signals": {
      "hiring_procurement": true/false,
      "new_market_expansion": true/false,
      "signals": []
    },
    "key_contacts": [
      {
        "name": "姓名",
        "title": "职位",
        "linkedin_url": "LinkedIn链接或空字符串",
        "guessed_email": "猜测的邮箱格式，如 john@company.com"
      }
    ],
    "web_traffic": {
      "monthly_visitors": "月均访客量（如：5万-10万）",
      "top_source_countries": ["来源国1", "来源国2", "来源国3"],
      "top_channels": ["直接访问", "搜索引擎", "社交媒体"],
      "top_keywords": ["核心关键词1", "核心关键词2"]
    }
  },
  "expert_triggers": [
    "专家触发洞察（用中文写出关键发现和其对外贸开发的意义）"
  ],
  "killer_pitch": "基于调查结果，为冷启动邮件撰写的2句中文开场白，突出你能解决的具体痛点。",
  "recommended_approach": "给外贸销售的具体建议，用中文。",
  "investigation_notes": "其他补充说明，用中文。"
}
"""

# ─── Tools Implementation ─────────────────────────────────────────────────────

class SearchTool:
    """Real Google Search via Serper API."""
    SERPER_URL = "https://google.serper.dev/search"

    async def search(self, query: str, num: int = 8) -> dict:
        if not SERPER_KEY:
            return {"error": "SERPER_API_KEY not configured", "results": []}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                self.SERPER_URL,
                headers={"X-API-KEY": SERPER_KEY, "Content-Type": "application/json"},
                json={"q": query, "num": num},
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get("organic", []):
                results.append({
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                })
            return {"query": query, "results": results[:8]}


class ScrapeTool:
    """Website scraper via Jina Reader API."""
    JINA_BASE = "https://r.jina.ai/"

    async def scrape(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"Accept": "text/markdown"}
            if JINA_KEY:
                headers["Authorization"] = f"Bearer {JINA_KEY}"
            try:
                resp = await client.get(f"{self.JINA_BASE}{url}", headers=headers)
                resp.raise_for_status()
                content = resp.text
                # Truncate to 4000 chars to save tokens
                return content[:4000] + ("...[truncated]" if len(content) > 4000 else "")
            except Exception as e:
                return f"[Failed to scrape {url}: {e}]"


class CustomsLookupTool:
    """
    52wmb (外贸邦) Customs Data Lookup.

    INTEGRATION NOTE:
    ─────────────────
    The 52wmb API is NOT publicly documented — it is sold via their enterprise
    sales team. To integrate for real:
      1. Contact 52wmb at libin@52wmb.com or +86-021-64033526
      2. Request the "API 接口权限" package
      3. Replace the mock below with real HTTP calls to their endpoint

    Alternative open APIs with similar data:
      - api.trademo.com  (global, English, $20k/yr)
      - api.volza.com    (covers 70+ countries)
      - api.tendata.cn   (Chinese domestic provider, easier access)

    For this DEMO: we simulate what the API would return based on real
    data found via Google Search earlier.
    """

    async def lookup(self, company_name: str) -> dict:
        logger.info(f"[Customs] Looking up: {company_name}")

        # In production: make real API call here
        # Example (Tendata API pattern):
        # async with httpx.AsyncClient() as client:
        #     resp = await client.get(
        #         "https://api.tendata.cn/v1/company/search",
        #         params={"name": company_name, "apikey": TENDATA_KEY},
        #     )
        #     return resp.json()

        # --- DEMO MOCK ---
        name_lower = company_name.lower()

        if "topband" in name_lower:
            return {
                "source": "52wmb Customs Database (Mock — Contact 52wmb for real API)",
                "company": company_name,
                "total_shipments": 797,
                "trend": "Increasing (+15% YoY)",
                "top_hs_codes": [
                    {"code": "850440", "description": "Static converters (power supply)"},
                    {"code": "853710", "description": "Control panels for electrical devices"},
                    {"code": "847990", "description": "Industrial machinery"},
                ],
                "major_import_markets": ["USA", "Germany", "Netherlands", "Japan"],
                "major_buyers": [
                    "Multiple US distributors",
                    "European electronics wholesalers"
                ],
                "last_shipment_date": "2026-02-15",
                "note": "Active exporter. Replace this mock with real 52wmb API response."
            }

        if "joybuy" in name_lower:
            return {
                "source": "52wmb Mock",
                "company": company_name,
                "total_shipments": 8,
                "trend": "Stable",
                "top_hs_codes": [],
                "major_import_markets": ["UK", "France"],
                "note": "Low volume. Company is primarily a B2C retail brand, not a manufacturer."
            }

        # Generic empty result
        return {
            "source": "52wmb Mock",
            "company": company_name,
            "total_shipments": 0,
            "trend": "Unknown",
            "note": "No customs records found. Company may import via agents or be a B2C-only entity."
        }

class FindContactsTool:
    """
    Find key decision-makers (CEO, Procurement Director, etc.) at a company.
    Uses Google Search with LinkedIn site: filter to surface real people.
    In production, could be replaced with Apollo.io or Hunter.io API.
    """

    async def find(self, company_name: str, domain: str) -> dict:
        logger.info(f"[Contacts] Finding key contacts at: {company_name}")
        search = SearchTool()

        # Search for key decision makers on LinkedIn
        results = await search.search(
            f'"{company_name}" CEO OR "Procurement Director" OR "Purchasing Manager" '
            f'OR "Supply Chain" OR "外贸" site:linkedin.com',
            num=8
        )

        # Also try to find email patterns
        email_results = await search.search(
            f'"@{domain}" email contact',
            num=5
        )

        return {
            "source": "Google Search (LinkedIn filter)",
            "note": "生产环境建议接入 Apollo.io 或 Hunter.io API 获取验证邮箱",
            "linkedin_results": results.get("results", [])[:5],
            "email_hints": email_results.get("results", [])[:3],
        }


class WebTrafficTool:
    """
    Analyze website traffic using SimilarWeb (scraped) and Google Search signals.
    Helps understand the company's real target market and audience geography.
    In production, use SimilarWeb API (~$199/mo) for structured data.
    """

    async def analyze(self, domain: str) -> dict:
        logger.info(f"[Traffic] Analyzing web traffic for: {domain}")
        scraper = ScrapeTool()
        search = SearchTool()

        # Try SimilarWeb
        sw_content = await scraper.scrape(f"https://www.similarweb.com/website/{domain}/")

        # Also get Alexa/traffic signals from search
        traffic_signals = await search.search(
            f'"{domain}" site:similarweb.com OR "monthly visitors" OR "web traffic"',
            num=5
        )

        return {
            "source": "SimilarWeb scrape + Google signals",
            "note": "生产环境建议接入 SimilarWeb API 获取结构化月度数据",
            "similarweb_content": sw_content[:2000],
            "traffic_signals": traffic_signals.get("results", [])[:4],
        }



# ─── Tool Definitions (OpenAI Function Calling Schema) ───────────────────────

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": (
                "执行 Google 搜索。可用于查询海关记录、YouTube展会、LinkedIn招聘信号、"
                "新闻风险、Whois历史等。可加 site: 过滤器定向平台。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "精准的 Google 搜索查询字符串。"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scrape_website",
            "description": (
                "抓取指定 URL 的完整内容，返回 Markdown 文本。"
                "适用于公司官网、LinkedIn主页、详情页等。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "要抓取的完整 HTTP/HTTPS URL。"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "customs_lookup",
            "description": (
                "查询 52wmb 海关数据库，获取公司的进出口记录。"
                "返回：提单总数、主要买家、HS编码、出口趋势。"
                "请优先调用此工具，再考虑 search_web 搜索海关数据。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "要查询海关记录的公司官方名称。"
                    }
                },
                "required": ["company_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_key_contacts",
            "description": (
                "搜索公司关键决策人（CEO、采购总监、外贸负责人等）。"
                "返回 LinkedIn 搜索结果和邮箱线索。每次调查必须调用此工具。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "公司名称。"
                    },
                    "domain": {
                        "type": "string",
                        "description": "公司域名，用于推断邮箱格式。"
                    }
                },
                "required": ["company_name", "domain"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_website_traffic",
            "description": (
                "分析公司网站的流量数据（通过 SimilarWeb）。"
                "返回月均访客、主要来源国、核心流量渠道。"
                "用于判断该公司真实的目标销售市场。每次调查必须调用此工具。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "公司网站域名，如 joybuy.com。"
                    }
                },
                "required": ["domain"]
            }
        }
    }
]


# ─── ReAct Loop ───────────────────────────────────────────────────────────────

async def run_react_investigation(
    company_name: str,
    domain: str,
    extra_context: str = "",
) -> str:
    """
    Run the true ReAct investigation loop.
    The LLM autonomously decides which tools to call and in what order.
    """
    search = SearchTool()
    scraper = ScrapeTool()
    customs = CustomsLookupTool()
    contacts = FindContactsTool()
    traffic = WebTrafficTool()

    # Build the initial user prompt
    user_prompt = f"""
Conduct a full background investigation on the following B2B company:

- **Company Name**: {company_name}
- **Domain / Website**: {domain}
{f'- **Additional Context**: {extra_context}' if extra_context else ''}

Use your tools to gather evidence across all 5 dimensions (Trade, Identity, Reputation, 
Market Presence, Intent Signals). Then synthesize your findings into the JSON report format 
specified in your instructions.

Begin the investigation now.
"""

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": INVESTIGATION_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt.strip()},
    ]

    print(f"\n{'='*70}")
    print(f"  🔍 外贸背调智能体 — {company_name} ({domain})")
    print(f"  Model: {MODEL} | Max iterations: {MAX_ITERATIONS}")
    print(f"{'='*70}\n")

    for iteration in range(1, MAX_ITERATIONS + 1):
        is_last = iteration == MAX_ITERATIONS

        kwargs: dict[str, Any] = {
            "model": MODEL,
            "messages": messages,
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS,
            "tools": TOOL_DEFINITIONS,
        }

        # On last iteration: don't offer tools, force a final answer
        if is_last:
            kwargs.pop("tools")
            messages.append({
                "role": "user",
                "content": (
                    "⚠️ This is your LAST chance to respond. Stop using tools. "
                    "Output your FINAL JSON investigation report NOW based on everything gathered so far. "
                    "Output ONLY the raw JSON object."
                )
            })
            logger.info(f"[ReAct] Iteration {iteration}/{MAX_ITERATIONS} — forcing final answer")
        else:
            logger.info(f"[ReAct] Iteration {iteration}/{MAX_ITERATIONS}")

        try:
            response = await litellm.acompletion(**kwargs)
        except Exception as e:
            logger.error(f"[ReAct] LLM call failed: {e}")
            return json.dumps({"error": str(e)})

        choice = response.choices[0]
        msg = choice.message

        # ── No tool calls → this is the final answer ──────────────────────────
        if not getattr(msg, "tool_calls", None):
            content = msg.content or ""
            print(f"\n{'='*70}")
            print("  ✅ Investigation Complete — Final Report")
            print(f"{'='*70}")
            return content

        # ── Execute tool calls ─────────────────────────────────────────────────
        messages.append(msg.model_dump())

        for tool_call in msg.tool_calls:
            fn_name = tool_call.function.name
            try:
                fn_args = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                fn_args = {}

            print(f"  🔧 [{fn_name}] {json.dumps(fn_args, ensure_ascii=False)}")

            try:
                if fn_name == "search_web":
                    result = await search.search(fn_args.get("query", ""))
                    result_str = json.dumps(result, ensure_ascii=False)
                elif fn_name == "scrape_website":
                    result_str = await scraper.scrape(fn_args.get("url", ""))
                elif fn_name == "customs_lookup":
                    result = await customs.lookup(fn_args.get("company_name", ""))
                    result_str = json.dumps(result, ensure_ascii=False)
                elif fn_name == "find_key_contacts":
                    result = await contacts.find(
                        fn_args.get("company_name", ""),
                        fn_args.get("domain", ""),
                    )
                    result_str = json.dumps(result, ensure_ascii=False)
                elif fn_name == "analyze_website_traffic":
                    result = await traffic.analyze(fn_args.get("domain", ""))
                    result_str = json.dumps(result, ensure_ascii=False)
                else:
                    result_str = json.dumps({"error": f"Unknown tool: {fn_name}"})
            except Exception as e:
                logger.warning(f"  ❌ Tool {fn_name} failed: {e}")
                result_str = json.dumps({"error": str(e)})

            # Show a brief preview of the result
            preview = result_str[:200].replace("\n", " ")
            print(f"     → {preview}{'...' if len(result_str) > 200 else ''}")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_str,
            })

    logger.warning("[ReAct] Exhausted max iterations without a final answer")
    return json.dumps({"error": "Max iterations reached without final answer"})


# ─── Entry Point ──────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(
        description="外贸背调智能体 — ReAct-based B2B Investigation Agent Demo"
    )
    parser.add_argument(
        "--company", "-c",
        default="Shenzhen Topband Co Ltd",
        help="Company name to investigate"
    )
    parser.add_argument(
        "--domain", "-d",
        default="topband.com.cn",
        help="Company website domain"
    )
    parser.add_argument(
        "--context", "-x",
        default="",
        help="Optional additional context (e.g. the product category you sell)"
    )
    args = parser.parse_args()

    start = time.time()
    result_text = await run_react_investigation(
        company_name=args.company,
        domain=args.domain,
        extra_context=args.context,
    )
    elapsed = time.time() - start

    # Try to parse and pretty-print JSON
    try:
        parsed = json.loads(result_text)
        print(json.dumps(parsed, indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        print(result_text)

    print(f"\n⏱  Investigation completed in {elapsed:.1f}s")


if __name__ == "__main__":
    import warnings
    # Suppress harmless SSL/asyncio cleanup errors from httpx
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
