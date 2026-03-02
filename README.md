# AI 企业与联系人智能搜索工具

[English Version](README_en.md) | [Web 界面说明](README_WEB.md) | [Docker 部署](DOCKER_DEPLOY.md)

一套强大的Python工具集，用于自动化外贸与B2B销售中的客户开发流程。该工具通过搜索引擎API和AI技术，帮助您快速找到目标企业、提取联系方式并识别关键决策者。支持命令行和Web界面两种使用方式。

> **想要开箱即用的托管版本？** 欢迎访问 **[B2BInsights.io](https://b2binsights.io)** —— 基于本项目能力打造的AI智能体B2B客户开发平台，无需任何配置即可使用。

> **推荐阅读**: 如果您不熟悉搜索引擎的高级用法，建议先阅读这篇[搜索引擎高级使用教程](https://zhuanlan.zhihu.com/p/1908208213234554242)，它将帮助您更有效地构建搜索查询。

## 项目功能

### 核心功能

本项目提供**两种使用方式**：

#### 1. 命令行工具（适合技术用户）

- **AI关键词生成** (`keyword_generator.py`)
  - 基于产品描述和目标地区，用AI生成10-30个精准B2B搜索关键词
  - 覆盖7个关键词维度：买家角色、行业应用、价值主张、买家类型、地区+贸易词、B2B平台、认证/标准
  - 自动识别目标地区语言，生成本地化关键词（德语、法语、西班牙语等）

- **企业搜索** (`serper_company_search.py`)
  - 基于行业、地区和关键词搜索目标企业
  - 支持自定义搜索查询，完全控制搜索内容
  - 自动提取企业网站、域名和基本信息
  - 支持普通搜索和LinkedIn企业专项搜索

- **联系方式提取** (`extract_contact_info.py`)
  - 从企业网站自动提取联系信息
  - 识别电子邮箱、电话号码、实际地址
  - 收集社交媒体账号（LinkedIn、Twitter、Facebook、Instagram）
  - 支持多URL批量处理

- **员工与决策者搜索** (`serper_employee_search.py`)
  - 基于公司名称和职位搜索目标企业的员工
  - 识别关键决策者和潜在联系人

#### 2. Web界面（适合非技术用户）

基于Streamlit的现代化Web界面，提供：

- **🚀 B2B 智能流水线** - 全自动：关键词生成 → 搜索 → B2B平台 site: 查询 → LLM评分筛选
- **🎯 关键词生成器** - AI驱动的关键词生成，结果直接接入企业搜索
- **可视化操作界面** - 无需命令行知识即可使用
- **实时结果展示** - 即时查看搜索和提取结果
- **数据导出功能** - 一键下载CSV/JSON格式结果
- **Docker部署支持** - 快速部署到任何服务器

## 解决的问题

- **降低客户开发成本**：减少手动搜索和数据收集时间，提高销售团队效率
- **提高客户精准度**：精确定位符合目标行业和地区的企业客户
- **简化联系流程**：直接获取有效联系信息，无需在多个平台间切换
- **识别关键决策者**：直接找到企业中的关键职位人员，缩短销售周期

## 技术实现

- **搜索技术**：支持 [Serper.dev](https://serper.dev) 和 [Tavily](https://app.tavily.com) 双搜索服务商，可在 `.env` 中一键切换
- **LLM集成**：通过 [litellm](https://github.com/BerriAI/litellm) 统一调用所有主流LLM，国内外均支持（见下方配置说明）
- **B2B Flow引擎**：`core/b2b_flow.py` — 全自动流水线，含B2B平台 site: 查询、LLM相关性评分
- **网页内容提取**：使用Playwright自动化浏览器渲染和提取网站内容
- **并行处理**：优化浏览器实例管理，支持高效批量处理
- **容错机制**：包含超时处理、内容清理和错误恢复功能

## 安装指南

### 前提条件

- Python 3.8+
- 搜索API密钥（Serper.dev 或 Tavily，二选一）
- (可选) LLM API密钥（用于关键词生成、联系人提取和B2B评分）
- (可选) Docker和Docker Compose（用于容器化部署）

### 方法一：本地安装

1. 克隆项目

```bash
git clone https://github.com/xiongQvQ/AI_Find_Customer.git
cd AI_Find_Customer
```

2. 安装依赖包：

```bash
pip install -r requirements.txt
```

3. 安装Playwright浏览器（用于网站内容提取）：

```bash
playwright install chromium
```

4. 创建 `.env` 配置文件（复制模板）：

```bash
cp .env.example .env
```

然后编辑 `.env`，按下方说明填写配置。

---

## 参数配置说明

### 搜索服务商配置（二选一）

**选项 A：Serper.dev（默认推荐）**

```
SEARCH_PROVIDER=serper
SERPER_API_KEY=your_serper_api_key_here
```

免费申请：[serper.dev](https://serper.dev)（每月2500次免费）

**选项 B：Tavily**

```
SEARCH_PROVIDER=tavily
TAVILY_API_KEY=tvly-your_tavily_api_key_here
```

免费申请：[app.tavily.com](https://app.tavily.com/home)（每月1000次免费）

---

### LLM 配置（通过 litellm 统一接入）

项目使用 [litellm](https://github.com/BerriAI/litellm) 统一调用各家LLM，只需在 `.env` 中设置 `LLM_MODEL` 即可。

**格式：** `LLM_MODEL=<提供商>/<模型名>`

#### 国内推荐

| 提供商 | 配置示例 | API密钥变量 | 申请地址 |
|--------|----------|-------------|----------|
| DeepSeek | `LLM_MODEL=deepseek/deepseek-chat` | `DEEPSEEK_API_KEY` | [platform.deepseek.com](https://platform.deepseek.com) |
| 智谱 GLM | `LLM_MODEL=zhipuai/glm-4-flash` | `ZHIPUAI_API_KEY` | [open.bigmodel.cn](https://open.bigmodel.cn) |
| MiniMax | `LLM_MODEL=minimax/abab6.5s-chat` | `MINIMAX_API_KEY` | [platform.minimaxi.com](https://platform.minimaxi.com) |
| 火山豆包 | `LLM_MODEL=volcengine/doubao-1-5-pro-256k-250115` | `VOLCENGINE_API_KEY` | [console.volcengine.com](https://console.volcengine.com/ark) |

#### 国际推荐

| 提供商 | 配置示例 | API密钥变量 | 申请地址 |
|--------|----------|-------------|----------|
| OpenAI | `LLM_MODEL=openai/gpt-4o-mini` | `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) |
| Anthropic | `LLM_MODEL=anthropic/claude-3-haiku-20240307` | `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |
| Google | `LLM_MODEL=gemini/gemini-1.5-flash` | `GOOGLE_API_KEY` | [aistudio.google.com](https://aistudio.google.com) |
| OpenRouter（多模型聚合） | `LLM_MODEL=openrouter/google/gemma-3-27b-it:free` | `OPENROUTER_API_KEY` | [openrouter.ai](https://openrouter.ai) |
| Grok / xAI | `LLM_MODEL=xai/grok-3-mini-beta` | `XAI_API_KEY` | [console.x.ai](https://console.x.ai) |

#### 配置示例（`.env` 文件）

```bash
# 搜索服务商
SEARCH_PROVIDER=serper
SERPER_API_KEY=your_serper_key

# LLM（选一种填写）
LLM_MODEL=deepseek/deepseek-chat
DEEPSEEK_API_KEY=your_deepseek_key

# 网站提取配置
HEADLESS=true
TIMEOUT=15000
VISIT_CONTACT_PAGE=false
```

> **注意：** LLM是可选的。不配置LLM时，关键词生成、联系人AI提取和B2B评分功能不可用，但企业搜索仍可正常使用。

### 方法二：Docker 快速部署（推荐）

使用Docker可以避免环境配置问题，特别适合生产环境部署：

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑.env文件，添加您的API密钥

# 2. 使用部署脚本（推荐）
chmod +x docker_deploy.sh
./docker_deploy.sh

# 或手动使用docker-compose
docker-compose up -d
```

部署完成后，访问 `http://localhost:8501` 即可使用Web界面。

详细的Docker部署说明请参考[Docker部署指南](DOCKER_DEPLOY.md)。

## 使用指南

### Web界面使用（推荐新手）

1. **启动Web服务**：

```bash
streamlit run streamlit_app.py
```

2. **访问界面**：在浏览器中打开 `http://localhost:8501`

3. **页面说明**：

| 页面 | 功能 |
|------|------|
| 🚀 B2B Flow | **全自动流水线**：关键词→搜索→B2B平台→LLM评分 |
| 🎯 关键词生成器 | AI生成精准B2B搜索关键词 |
| 🔍 企业搜索 | 按行业/地区/关键词搜索企业 |
| 📧 联系方式提取 | 从企业网站提取邮箱、电话、社媒 |
| 👥 员工搜索 | 找到企业关键决策者 |

### 命令行使用

#### 1. 企业搜索

使用`serper_company_search.py`脚本搜索企业信息：

#### 基于行业和地区搜索企业：
```bash
python serper_company_search.py --general-search --industry "solar energy" --region "California" --gl "us"
```

#### 使用自定义查询（完全控制查询内容）：
```bash
python serper_company_search.py --general-search --custom-query "top solar panel manufacturers California renewable energy" --gl "us"
```

#### 参数说明：
- `--general-search`: 使用普通搜索模式
- `--linkedin-search`: 使用LinkedIn企业专项搜索模式
- `--industry`: 目标行业关键词
- `--region`: 目标地区/城市
- `--custom-query`: 完全自定义的搜索查询（覆盖industry、region和默认关键词）
- `--gl`: 地区代码（如"us"、"uk"、"cn"等）
- `--num`: 返回结果数量（默认30）
- `--keywords`: 附加关键词（逗号分隔）
- `--output`: 自定义输出文件名

#### 结果：
结果将保存在`output/company/`目录下，CSV和JSON格式。文件名根据搜索参数自动生成。CSV文件包含以下列：
- Company Name：企业名称
- Search Query：搜索查询
- URL：企业网站链接
- Domain：企业域名
- LinkedIn：LinkedIn链接（如果可用）
- GL：地区代码参数
- 以及其他详细信息

#### 2. 联系方式提取

使用`extract_contact_info.py`脚本从网站中提取联系信息：

#### 处理单个网站：
```bash
python extract_contact_info.py --url example.com --headless
```

#### 处理多个网站（从文本文件）：
```bash
python extract_contact_info.py --url-list urls.txt --timeout 15000
```

#### 处理企业搜索结果：
```bash
python extract_contact_info.py --csv output/company/general_solar_energy_california_us_1234567890.csv --url-column Domain
```

> **注意**：当使用`--csv`参数但不指定`--output`时，输出文件将自动命名为"contact_info_"加原始CSV文件名。例如，输入`general_custom_project_us_1234567890.csv`将生成`contact_info_general_custom_project_us_1234567890.csv`。

#### 处理CSV并合并结果：
```bash
python extract_contact_info.py --csv companies.csv --url-column Domain --merge-results
```

#### 参数说明：
- `--url`: 单个网站URL
- `--url-list`: 包含多个URL的文本文件（每行一个URL）
- `--csv`: 包含URL列的CSV文件
- `--url-column`: CSV文件中URL列的名称（默认"URL"）
- `--domain-column`: 备选域名列名（默认"Domain"）
- `--output`: 自定义输出文件名
- `--headless`: 使用无头模式运行浏览器（无界面）
- `--timeout`: 页面加载超时时间（毫秒）
- `--visit-contact`: 启用联系页面访问（更全面但更慢）
- `--merge-results`: 将提取的联系信息与输入CSV合并（仅适用于`--csv`选项）

#### 结果：
- 基本联系信息结果保存在`output/contact/`目录下，包含以下信息：
  - 公司名称
  - 电子邮件地址
  - 电话号码
  - 实际地址
  - 社交媒体链接（LinkedIn、Twitter、Facebook、Instagram）
  
- 当使用`--merge-results`时，会生成额外的`*_merged.csv`文件，其中包含原始CSV数据加上提取的联系信息。

#### 3. 员工搜索

使用`serper_employee_search.py`脚本查找企业员工和决策者：

#### 搜索特定企业的员工：
```bash
python serper_employee_search.py --company "Tesla" --position "sales manager" --location "California"
```

#### 处理企业列表（从搜索结果）：
```bash
python serper_employee_search.py --input-file general_solar_energy_california_us_1234567890.csv --position "CEO" --country "United States"
```

> **注意**：使用`--input-file`参数时，CSV文件必须包含`Company Name`列（公司名称），脚本将使用此列查找企业的员工。CSV文件也可以包含可选的`Location`列，用于定位员工。

#### 参数说明：
- `--company`: 目标公司名称
- `--input-file`: 包含公司信息的CSV文件（位于output目录）
- `--position`: 目标职位/职务
- `--location`: 地点/城市
- `--country`: 国家
- `--keywords`: 附加关键词（逗号分隔）
- `--output`: 自定义输出文件名
- `--gl`: 地区代码（如"us"、"uk"等）
- `--num`: 返回结果数量（默认30）

#### 结果：
结果将保存在`output/employee/`目录下，包含员工姓名、职位、LinkedIn链接和其他可用信息。

## 注意事项与限制

- 搜索API有免费额度限制，请合理控制查询频率
- 部分网站可能禁止自动化访问，可能需要调整请求头或使用代理
- 联系信息提取准确度取决于网站结构和内容质量
- 使用时请遵守相关法律法规和各平台使用条款
- 对于较大批量的处理，建议控制并发和添加足够的延时

## 常见问题

**Q: 如何选择搜索服务商？**

A: Serper.dev 每月2500次免费，速度快、结果质量高，推荐作为默认选择。Tavily 每月1000次免费，结果含相关性评分，适合需要结构化数据的场景。在 `.env` 中设置 `SEARCH_PROVIDER=serper` 或 `SEARCH_PROVIDER=tavily` 即可切换。

**Q: 国内用户推荐哪个LLM？**

A: 推荐 DeepSeek（价格极低、效果好）或火山豆包。配置示例：

```bash
LLM_MODEL=deepseek/deepseek-chat
DEEPSEEK_API_KEY=your_key
```

**Q: 无法提取某些网站的联系信息**

A: 尝试使用 `--visit-contact` 参数启用联系页面访问，或调整 `--timeout` 参数增加加载时间。

**Q: B2B Flow 评分都很低怎么办？**

A: 尝试调低 `min_llm_score` 阈值（如从6降到4），或检查产品描述是否足够具体，更精确的产品描述能显著提升评分质量。

**Q: API密钥配置问题**

A: 确保 `.env` 文件中的API密钥格式正确，且不包含引号或额外空格。可运行 `python -c "from core.llm_client import is_llm_available; print(is_llm_available())"` 验证LLM配置。

## 联系方式

<div style="display: flex; justify-content: space-between;">
  <div style="text-align: center; margin-right: 20px;">
    <h3>个人微信</h3>
    <img src="img/me_code.jpg" width="200" alt="个人微信二维码">
  </div>
  <div style="text-align: center; margin-right: 20px;">
    <h3>微信交流群</h3>
    <img src="img/group_code.jpg" width="200" alt="微信群二维码">
  </div>
  <div style="text-align: center;">
    <h3>电报群</h3>
    <a href="https://t.me/+jjmdspjqpbcwOGFl">加入电报群</a>
  </div>
</div>

---

**想省去部署配置的麻烦？** 欢迎体验 [B2BInsights.io](https://b2binsights.io)，AI智能体驱动的B2B客户开发SaaS平台，开箱即用。