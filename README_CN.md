# AI Hunter — 多 Agent 协同 B2B 客户挖掘系统

> **基于 LangGraph 多智能体流水线的自动化 B2B 客户开发工具**

AI Hunter 是一个开源系统，帮助外贸企业自动发现潜在的 B2B 买家和分销商。输入公司官网（或上传产品文档）和目标地区，系统自动完成：深度公司分析、关键字生成、多渠道搜索、客户信息提取、联系方式发现，以及用目标客户母语撰写个性化开发信。

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-green)](https://github.com/langchain-ai/langgraph)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-red)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-blue)](https://react.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-443%20passing-brightgreen)](https://github.com/your-org/ai-hunter)

[English README](README.md)

---


## ✨ 核心特性

- **双模型 ReAct 架构** — 推理模型（如 `gpt-4o`）驱动 InsightAgent 和 LeadExtractAgent 的多步工具调用决策；快速模型（如 `gpt-4o-mini`）处理数据提取、关键字生成和邮件撰写
- **5 个专业 Agent** — Insight → KeywordGen → Search → LeadExtract → EmailCraft 分工协作
- **灵活输入** — 支持官网 URL、上传文件（PDF/Excel）或仅关键字三种输入模式
- **自适应挖掘循环** — per-keyword 效果反馈驱动关键字迭代优化，直到达到目标客户数或收益递减
- **多渠道搜索** — Google Search + Google Maps + 9 大 B2B 平台定向搜索（阿里巴巴、中国制造网、环球资源等）
- **智能抓取** — ReAct Agent 根据 URL 类型（公司官网/B2B 平台/LinkedIn/内容页）自主决定抓取策略
- **多 LLM 支持** — 通过 [litellm](https://github.com/BerriAI/litellm) 统一接入 OpenAI、Anthropic、OpenRouter、Groq、智谱 Z.AI、Moonshot（Kimi）、MiniMax
- **多搜索后端** — Serper（Google）→ Brave → Tavily 自动降级链
- **多语言邮件 + ReAct 验证** — 起草、验证（语言/正式程度/称谓/语法）并修订 14+ 语言的 3 封邮件序列
- **SSE 实时推送** — 实时流水线进度 + 每阶段可展开的详细数据面板
- **成本追踪** — 通过 [Langfuse](https://langfuse.com) 的 litellm 回调追踪每次 LLM 调用的 Token 消耗、费用和延迟
- **邮箱验证** — MX 记录检查，过滤无效邮箱地址
- **443 个测试** — 完整的单元测试 + 集成测试套件

---

## 系统架构

```text
输入：官网 URL / 上传文件（PDF、Excel）/ 产品关键字 + 目标地区
    │
    ▼
┌─────────────────────── LangGraph StateGraph ───────────────────────────┐
│                                                                         │
│  InsightAgent  [ReAct · 推理模型]  （仅首轮执行）                         │
│  ├── scrape_page       → 抓取官网 + 关键子页面（最多 4 页）               │
│  ├── read_uploaded_file → 读取 PDF / Excel 文档                         │
│  └── search_web        → 补充市场背景信息                                │
│       │                                                                 │
│       ▼                                                                 │
│  ┌──── 挖掘循环 ────────────────────────────────────────────────────┐   │
│  │  KeywordGenAgent  [快速模型]                                     │   │
│  │      │  每轮 5-8 个关键字，基于 per-keyword 反馈优化              │   │
│  │      ▼                                                           │   │
│  │  SearchAgent  [并发 · Serper/Brave/Tavily + Maps + B2B 平台]    │   │
│  │      │  asyncio.Semaphore(search_concurrency)                   │   │
│  │      ▼                                                           │   │
│  │  LeadExtractAgent  [ReAct · 推理模型 · 并发]                     │   │
│  │  ├── scrape_page       （提取邮箱/电话/社交账号）                  │   │
│  │  ├── google_search     （查找官网）                               │   │
│  │  └── extract_lead_info （结构化 JSON 提取）                       │   │
│  │      │                                                           │   │
│  │      ▼                                                           │   │
│  │  Evaluate  （per-keyword 反馈 · 停止条件判断）                    │   │
│  │      │  未达标 → 带反馈重新生成关键字                              │   │
│  │      └──────────────────────────────────────────────────────────┘   │
│       │  达标：目标数量 / 超轮次 / 收益递减                               │
│       ▼                                                                 │
│  EmailCraftAgent  [ReAct · 快速模型 · 并发]  （可选）                   │
│  ├── 用目标语言起草 3 封邮件                                             │
│  ├── validate_emails  （语言 · 正式程度 · 称谓 · 语法）                  │
│  └── 根据反馈修订（最多 2 轮修订）                                        │
└─────────────────────────────────────────────────────────────────────────┘
    │
    ▼
FastAPI + SSE 实时推送 → React 前端（实时进度 + 可展开的阶段详情面板）
```

### Agent 模型分配

| Agent | 模型 | 模式 | 用途 |
| ----- | ---- | ---- | ---- |
| InsightAgent | `reasoning_model` | ReAct 多工具 | 深度分析公司/产品 |
| KeywordGenAgent | `llm_model` | 单次 LLM 调用 | 基于反馈生成关键字 |
| SearchAgent | — | 并发异步 | Google + Maps + B2B 平台搜索 |
| LeadExtractAgent（决策） | `reasoning_model` | ReAct 多工具 | 抓取策略 + 客户资质判断 |
| LeadExtractAgent（提取） | `llm_model` | 单次 LLM 调用 | 结构化数据提取 |
| EmailCraftAgent | `reasoning_model` | ReAct + 验证 | 起草 → 验证 → 修订邮件 |

---

## 项目结构

```text
ai_hunter/
├── README.md                    # 英文文档
├── README_CN.md                 # 中文文档（本文件）
├── LICENSE
├── CONTRIBUTING.md
├── backend/
│   ├── .env.example             # 环境变量模板
│   ├── requirements.txt
│   ├── config/
│   │   └── settings.py          # pydantic-settings（双模型 + 并发 + Langfuse）
│   ├── graph/
│   │   ├── builder.py           # LangGraph StateGraph 构建
│   │   ├── state.py             # HuntState TypedDict
│   │   └── evaluate.py          # 循环评估 + per-keyword 反馈 + 停止条件
│   ├── agents/
│   │   ├── insight_agent.py     # 公司/产品分析（ReAct）
│   │   ├── keyword_gen_agent.py # 关键字生成（基于反馈迭代）
│   │   ├── search_agent.py      # 并发搜索（Google + Maps + B2B 平台）
│   │   ├── lead_extract_agent.py# 客户提取（ReAct，并发，MX 邮箱验证）
│   │   └── email_craft_agent.py # 多语言邮件生成（ReAct + 验证）
│   ├── tools/
│   │   ├── llm_client.py        # 统一 LLM 客户端（litellm，双模型）
│   │   ├── react_runner.py      # 轻量 ReAct 循环引擎
│   │   ├── llm_output.py        # LLM 输出验证（JSON 解析 + 字段校验）
│   │   ├── google_search.py     # Google Search（Serper API）
│   │   ├── brave_search.py      # Brave Search（备用）
│   │   ├── tavily_search.py     # Tavily Search（备用）
│   │   ├── google_maps_search.py# Google Maps Search（Serper）
│   │   ├── amap_search.py       # 高德地图（中国地区搜索）
│   │   ├── jina_reader.py       # 网页抓取（Jina Reader）
│   │   ├── platform_registry.py # B2B 平台注册表（9 大平台）
│   │   ├── contact_extractor.py # 正则提取邮箱/电话/社交账号
│   │   ├── email_finder.py      # 邮箱发现（Hunter.io + 正则）
│   │   ├── email_verifier.py    # 邮箱验证（MX 记录检查）
│   │   ├── pdf_parser.py        # PDF 解析（pymupdf4llm）
│   │   ├── excel_parser.py      # Excel 解析（pandas）
│   │   └── url_filter.py        # URL 分类与过滤
│   ├── api/
│   │   ├── app.py               # FastAPI 应用入口 + Langfuse 初始化
│   │   ├── routes.py            # REST 路由 + SSE 阶段详情广播
│   │   └── hunt_store.py        # Hunt 持久化（JSON 文件）
│   ├── observability/
│   │   └── setup.py             # Langfuse 集成（litellm callback）
│   └── tests/                   # 443 个测试用例
└── frontend/
    ├── package.json             # Bun / npm
    ├── vite.config.ts
    └── src/
        ├── api/client.ts        # API 客户端 + TypeScript 类型定义
        └── routes/
            ├── dashboard.tsx    # 任务列表 Dashboard
            ├── new-hunt.tsx     # 创建任务表单
            └── hunt-detail.tsx  # 实时流水线 + 可展开阶段详情面板
```

---

## 快速开始

### 环境要求

- **Python 3.11 或 3.12**（**不支持** 3.10 及以下版本 — 代码使用了 `match` 语句和现代类型标注）
  - 检查版本：`python3 --version`
  - 通过 [pyenv](https://github.com/pyenv/pyenv) 安装：`pyenv install 3.12.4 && pyenv local 3.12.4`
- **Node.js >= 18** 或 [Bun](https://bun.sh) >= 1.0（前端所需）
  - 检查版本：`node --version` 或 `bun --version`
- 至少一个 LLM 提供商的 API Key（首次运行推荐 OpenAI）
- 至少一个搜索 API Key（推荐 Serper）

### 1. 克隆项目

```bash
git clone https://github.com/your-org/ai-hunter.git
cd ai-hunter
```

### 2. 后端配置

```bash
cd backend

# 创建并激活虚拟环境（Python 3.11+）
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate.bat    # Windows CMD
# .venv\Scripts\Activate.ps1    # Windows PowerShell

# 安装所有依赖
pip install --upgrade pip
pip install -r requirements.txt

# 复制环境变量模板并填写 API Key
cp .env.example .env
```

编辑 `.env`，填入必要的 API Key：

```bash
# 快速模型（数据提取、关键字生成、邮件撰写）
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-xxx

# 推理模型（ReAct Agent 决策）
REASONING_MODEL=gpt-4o

# 搜索（至少填一个；优先级：Serper > Brave > Tavily）
SERPER_API_KEY=xxx

# 网页抓取（推荐）
JINA_API_KEY=xxx

# 邮箱发现（可选）
HUNTER_API_KEY=xxx
```

#### 支持的 LLM 提供商

| 提供商 | 模型格式示例 | API Key 环境变量 |
| ------ | ------------ | ---------------- |
| OpenAI | `gpt-4o` / `gpt-4o-mini` | `OPENAI_API_KEY` |
| Anthropic | `anthropic/claude-3-5-sonnet-20241022` | `ANTHROPIC_API_KEY` |
| OpenRouter | `openrouter/google/gemini-2.5-flash` | `OPENROUTER_API_KEY` |
| Groq | `groq/llama-3.3-70b-versatile` | `GROQ_API_KEY` |
| 智谱 Z.AI | `zai/glm-4.7` | `ZAI_API_KEY` |
| Moonshot（Kimi） | `moonshot/moonshot-v1-128k` | `MOONSHOT_API_KEY` |
| MiniMax | `minimax/MiniMax-Text-01` | `MINIMAX_API_KEY` |

> `LLM_MODEL` 和 `REASONING_MODEL` 可以使用不同提供商，例如 `LLM_MODEL=groq/llama-3.3-70b-versatile` + `REASONING_MODEL=gpt-4o`。

### 3. 启动后端

```bash
cd backend
source .venv/bin/activate   # 如果尚未激活
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

API 文档：[http://localhost:8000/docs](http://localhost:8000/docs)

### 4. 启动前端

```bash
cd frontend
bun install && bun dev    # 或：npm install && npm run dev
```

前端地址：[http://localhost:3000](http://localhost:3000)（自动代理 `/api` 请求到后端）

### 5. 验证安装

```bash
curl http://localhost:8000/api/v1/health
# {"status":"ok","service":"ai-hunter"}
```

> **常见问题**：若出现 `ModuleNotFoundError`，请确认虚拟环境已激活（`source backend/.venv/bin/activate`）并已安装依赖（`pip install -r backend/requirements.txt`）。


---

## 成本追踪 — Langfuse 可观测性

AI Hunter 通过 **litellm 内置的 Langfuse 回调**自动追踪每次 LLM 调用的：

- Token 消耗（prompt / completion / total）
- 费用（litellm 根据模型定价自动计算，单位：美元）
- 响应延迟
- 完整的输入/输出内容

### 方式一：Langfuse Cloud（推荐，免费额度）

1. 注册 [https://cloud.langfuse.com](https://cloud.langfuse.com)（免费，每月 50k observations）
2. 创建项目，获取 **Public Key** 和 **Secret Key**
3. 在 `.env` 中配置：

```bash
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=https://cloud.langfuse.com
```

4. 重启后端，运行一次 Hunt。
5. 打开 Langfuse 项目 → **Traces** 页面即可看到所有 LLM 调用。 <!-- markdownlint-disable-line MD029 -->

**Langfuse Dashboard 可查看：**

- **Traces** — 每次 Hunt 的完整调用链
- **Generations** — 每次 LLM 调用详情（输入、输出、Token、费用）
- **Dashboard** — 总费用、Token 消耗趋势、模型分布、延迟统计

### 方式二：自部署 Langfuse

```bash
# Docker 一键部署（参考 https://langfuse.com/docs/deployment/self-host）
docker compose up -d

LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=http://localhost:3001   # 注意避免与前端 3000 端口冲突
```

---

## API 接口

| 方法 | 路径 | 说明 |
| ---- | ---- | ---- |
| `POST` | `/api/v1/hunts` | 创建新的挖掘任务 |
| `GET` | `/api/v1/hunts` | 列出所有任务 |
| `GET` | `/api/v1/hunts/{id}/status` | 查询任务状态 |
| `GET` | `/api/v1/hunts/{id}/result` | 获取完整结果（insight、leads、emails、keyword_search_stats） |
| `GET` | `/api/v1/hunts/{id}/stream` | SSE 实时进度推送（含每阶段详情事件） |
| `GET` | `/api/v1/health` | 健康检查 |

### 创建任务示例

```bash
curl -X POST http://localhost:8000/api/v1/hunts \
  -H "Content-Type: application/json" \
  -d '{
    "website_url": "https://your-company.com",
    "product_keywords": ["太阳能逆变器", "光伏组件"],
    "target_regions": ["欧洲", "东欧"],
    "target_lead_count": 100,
    "max_rounds": 5,
    "enable_email_craft": true
  }'
# 返回：{"hunt_id": "...", "status": "pending"}
```

不提供 `website_url` 时，可上传 PDF/Excel 文件，InsightAgent 会自动从文档中提取公司信息。

### SSE 事件类型

| 事件 | 数据 | 触发时机 |
| ---- | ---- | -------- |
| `stage_change` | `{stage, hunt_round, leads_count}` | 每次流水线阶段切换 |
| `stage_data` | 各阶段详细数据 | 每个阶段完成后 |
| `lead_progress` | `{url, status, lead}` | 每个 URL 提取进度 |
| `round_change` | `{hunt_round}` | 每轮挖掘开始 |
| `progress` | `{leads_count, stage, hunt_round}` | 周期性进度更新 |
| `completed` | `{leads_count, email_sequences_count}` | 任务完成 |
| `failed` | `{error}` | 任务失败 |

---

## 前端功能

- **Dashboard** — 任务列表，显示状态、轮次、leads 数量、创建时间
- **创建任务** — 官网 URL / 上传文件 + 关键字 + 目标地区
- **任务详情** — 实时流水线进度条，**每个阶段可点击展开查看详情**：
  - **Analyzing Company** → 洞察结果（公司名、产品、行业、推荐关键字、目标客户画像）
  - **Generating Keywords** → 每轮生成的关键字列表
  - **Searching Web** → 搜索结果数 + 每个关键字效果表格（结果数/leads 数/效果评级）
  - **Evaluating Progress** → 每轮评估（新增 leads、最佳/最差关键字）
  - **Crafting Emails** → 生成的邮件序列数
- **Leads 列表** — 公司信息、联系方式、匹配度，支持 CSV 导出
- **邮件序列** — 查看每个 lead 的个性化开发信

---

## 运行测试

```bash
cd backend

# 运行全部 443 个测试（约 8 秒，无需真实 API Key）
python -m pytest tests/ -q

# 按模块运行
python -m pytest tests/test_tools/ -v          # 工具层
python -m pytest tests/test_agents/ -v         # Agent 层
python -m pytest tests/test_evaluate.py -v     # 评估逻辑

# 带覆盖率报告
python -m pytest tests/ --cov=. --cov-report=term-missing
```

---

## 配置参考

所有配置项均可通过 `.env` 文件或环境变量覆盖：

| 配置项 | 默认值 | 说明 |
| ------ | ------ | ---- |
| `LLM_MODEL` | `gpt-4o-mini` | 快速模型（提取、关键字、邮件） |
| `REASONING_MODEL` | `gpt-4o` | 推理模型（ReAct 决策） |
| `LLM_TEMPERATURE` | `0.3` | 快速模型温度 |
| `REASONING_TEMPERATURE` | `0.2` | 推理模型温度 |
| `REACT_MAX_ITERATIONS` | `5` | 每次 ReAct 循环最大迭代次数 |
| `DEFAULT_TARGET_LEAD_COUNT` | `200` | 默认目标客户数 |
| `DEFAULT_MAX_ROUNDS` | `10` | 默认最大挖掘轮次 |
| `DEFAULT_KEYWORDS_PER_ROUND` | `8` | 每轮生成关键字数 |
| `MIN_NEW_LEADS_THRESHOLD` | `5` | 收益递减停止阈值（每轮新增 leads 低于此值则停止） |
| `SEARCH_CONCURRENCY` | `10` | 搜索 API 最大并发数 |
| `SCRAPE_CONCURRENCY` | `5` | Jina Reader 最大并发数 |
| `EMAIL_GEN_CONCURRENCY` | `3` | 邮件生成最大并发数 |
| `LANGFUSE_ENABLED` | `false` | 启用 Langfuse 成本追踪 |
| `LANGFUSE_HOST` | `http://localhost:3000` | Langfuse 服务地址 |
| `HUNTS_DIR` | `data/hunts` | Hunt JSON 持久化目录 |
| `UPLOAD_DIR` | `uploads` | 文件上传目录 |
| `MAX_UPLOAD_SIZE_MB` | `50` | 最大上传文件大小 |

---

## 技术栈

### 后端

- Python 3.11+ · FastAPI · Uvicorn
- LangGraph — 多 Agent 状态图编排
- litellm — 多 LLM 提供商统一接口 + Langfuse 回调
- httpx — 异步 HTTP 客户端
- pydantic-settings — 类型安全的配置管理
- pymupdf4llm · pandas — 文档解析

### 前端

- Vite · React 18 · TypeScript
- TanStack Router — 类型安全路由
- TanStack Query — 数据请求与缓存
- Tailwind CSS 3 — 原子化样式
- shadcn/ui — 组件库
- Lucide React — 图标库

---

## 路线图 / TODO

- [ ] **EmailCraftAgent ReAct** — 完整的验证→修订循环，含逐语言语法 LLM 检查 *（进行中）*
- [ ] **Docker Compose** — 一键全栈部署
- [ ] **身份认证** — API Key 或 OAuth，支持多用户部署
- [ ] **Lead 去重** — 跨任务按域名/邮箱去重
- [ ] **导出格式** — Excel / HubSpot CSV / Salesforce CSV
- [ ] **Webhook 支持** — 任务完成后推送结果到外部 CRM
- [ ] **限流处理** — 搜索 API 自动退避重试

---

## 参与贡献

欢迎提交 PR！详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

```bash
# 提交 PR 前请确保测试全部通过
cd backend && python -m pytest tests/ -q
```

## 开源协议

MIT — 详见 [LICENSE](LICENSE)。
