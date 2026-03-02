# AI Business and Contact Intelligence Search Tool

[中文版本](README.md) | [Web Interface Guide](README_WEB.md) | [Docker Deployment](DOCKER_DEPLOY.md)

A powerful set of Python tools for automating the customer development process in international trade and B2B sales. This tool uses search engine APIs and AI technology to help you quickly find target companies, extract contact information, and identify key decision-makers. Supports both command-line and web interface usage.

> **Looking for a fully managed solution?** Check out **[B2BInsights.io](https://b2binsights.io)** — the AI-powered B2B intelligence platform built on top of these open-source capabilities, with no setup required.

> **Recommended Reading**: If you're not familiar with advanced search engine techniques, we recommend reading this [Advanced Search Engine Usage Tutorial](https://zhuanlan.zhihu.com/p/1908208213234554242) first. It will help you build more effective search queries.

## Project Features

### Core Features

This project provides **two usage methods**:

#### 1. Command-Line Tools (For Technical Users)

- **AI Keyword Generator** (`keyword_generator.py`)
  - Generate 10-30 targeted B2B search keywords using AI
  - Covers 7 keyword dimensions: buyer role, industry, value proposition, buyer type, region+trade terms, B2B platforms, certifications
  - Auto-detects local language for non-English target regions (German, French, Spanish, etc.)

- **Company Search** (`serper_company_search.py`)
  - Search for target companies based on industry, region, and keywords
  - Support custom search queries with full control over search content
  - Automatically extract company websites, domains, and basic information
  - Support for both general search and LinkedIn company-specific search

- **Contact Information Extraction** (`extract_contact_info.py`)
  - Automatically extract contact information from company websites
  - Identify email addresses, phone numbers, and physical addresses
  - Collect social media accounts (LinkedIn, Twitter, Facebook, Instagram)
  - Support for batch processing of multiple URLs

- **Employee and Decision-Maker Search** (`serper_employee_search.py`)
  - Search for employees of target companies based on company name and position
  - Identify key decision-makers and potential contacts

#### 2. Web Interface (For Non-Technical Users)

Modern Streamlit-based web interface providing:

- **🚀 B2B Discovery Flow** - Fully automated: Keyword Generation → Search → B2B Platform site: queries → LLM scoring & filtering
- **🎯 Keyword Generator** - AI-powered keyword generation, feeds directly into Company Search
- **Visual Operation Interface** - Use without command-line knowledge
- **Real-time Result Display** - View search and extraction results instantly
- **Data Export Function** - One-click download of CSV/JSON format results
- **Docker Deployment Support** - Quick deployment to any server

## Problems Solved

- **Reduce Customer Development Costs**: Decrease manual search and data collection time, improve sales team efficiency
- **Increase Customer Accuracy**: Precisely target companies that match industry and regional criteria
- **Simplify Contact Process**: Directly obtain effective contact information without switching between multiple platforms
- **Identify Key Decision-Makers**: Directly find key personnel in companies, shortening the sales cycle

## Technical Implementation

- **Search Technology**: Supports [Serper.dev](https://serper.dev) and [Tavily](https://app.tavily.com) — switch providers with one env var
- **LLM Integration**: Uses [litellm](https://github.com/BerriAI/litellm) to call any major LLM provider with a single unified interface
- **B2B Flow Engine**: `core/b2b_flow.py` — fully automated pipeline with B2B platform site: queries and LLM relevance scoring
- **Web Content Extraction**: Uses Playwright for automated browser rendering and website content extraction
- **Parallel Processing**: Optimizes browser instance management for efficient batch processing
- **Fault Tolerance**: Includes timeout handling, content cleaning, and error recovery features

## Installation Guide

### Prerequisites

- Python 3.8+
- Search API key (Serper.dev or Tavily — choose one)
- (Optional) LLM API key — required for keyword generation, contact AI extraction, and B2B scoring
- (Optional) Docker and Docker Compose (for containerized deployment)

### Method 1: Local Installation

1. Clone the repository:

```bash
git clone https://github.com/xiongQvQ/AI_Find_Customer.git
cd AI_Find_Customer
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Install Playwright browser (for website content extraction):

```bash
playwright install chromium
```

4. Copy the config template and fill in your keys:

```bash
cp .env.example .env
```

Then edit `.env` — see the **Configuration** section below.

---

## Configuration

### Search Provider (choose one)

**Option A — Serper.dev (default, recommended)**

```
SEARCH_PROVIDER=serper
SERPER_API_KEY=your_serper_api_key_here
```

Get a free key at [serper.dev](https://serper.dev) (2,500 free searches/month)

**Option B — Tavily**

```
SEARCH_PROVIDER=tavily
TAVILY_API_KEY=tvly-your_tavily_api_key_here
```

Get a free key at [app.tavily.com](https://app.tavily.com/home) (1,000 free searches/month)

---

### LLM Configuration (via litellm)

The project uses [litellm](https://github.com/BerriAI/litellm) to call any LLM provider through a unified interface. Set `LLM_MODEL` in your `.env` file.

**Format:** `LLM_MODEL=<provider>/<model-name>`

#### International Providers

| Provider | Example | API Key Var | Sign Up |
|----------|---------|-------------|--------|
| OpenAI | `LLM_MODEL=openai/gpt-4o-mini` | `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) |
| Anthropic | `LLM_MODEL=anthropic/claude-3-haiku-20240307` | `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |
| Google | `LLM_MODEL=gemini/gemini-1.5-flash` | `GOOGLE_API_KEY` | [aistudio.google.com](https://aistudio.google.com) |
| OpenRouter | `LLM_MODEL=openrouter/google/gemma-3-27b-it:free` | `OPENROUTER_API_KEY` | [openrouter.ai](https://openrouter.ai) |
| Grok / xAI | `LLM_MODEL=xai/grok-3-mini-beta` | `XAI_API_KEY` | [console.x.ai](https://console.x.ai) |

#### China-based Providers

| Provider | Example | API Key Var | Sign Up |
|----------|---------|-------------|--------|
| DeepSeek | `LLM_MODEL=deepseek/deepseek-chat` | `DEEPSEEK_API_KEY` | [platform.deepseek.com](https://platform.deepseek.com) |
| Zhipu GLM | `LLM_MODEL=zhipuai/glm-4-flash` | `ZHIPUAI_API_KEY` | [open.bigmodel.cn](https://open.bigmodel.cn) |
| MiniMax | `LLM_MODEL=minimax/abab6.5s-chat` | `MINIMAX_API_KEY` | [platform.minimaxi.com](https://platform.minimaxi.com) |
| Volcano/Doubao | `LLM_MODEL=volcengine/doubao-1-5-pro-256k-250115` | `VOLCENGINE_API_KEY` | [console.volcengine.com](https://console.volcengine.com/ark) |

#### Example `.env`

```bash
# Search
SEARCH_PROVIDER=serper
SERPER_API_KEY=your_serper_key

# LLM — pick one
LLM_MODEL=openai/gpt-4o-mini
OPENAI_API_KEY=your_openai_key

# Website extraction
HEADLESS=true
TIMEOUT=15000
VISIT_CONTACT_PAGE=false
```

> **Note:** LLM is optional. Without it, keyword generation, AI contact extraction, and B2B scoring are unavailable, but company search works normally.

### Method 2: Docker Quick Deployment (Recommended)

```bash
cp .env.example .env
# Edit .env with your API keys
chmod +x docker_deploy.sh
./docker_deploy.sh
```

After deployment, visit `http://localhost:8501`. See [Docker Deployment Guide](DOCKER_DEPLOY.md) for details.

## Usage Guide

### Web Interface (Recommended for Beginners)

```bash
streamlit run streamlit_app.py
```

Open `http://localhost:8501` in your browser.

| Page | Function |
|------|----------|
| 🚀 B2B Flow | **Full automated pipeline**: Keywords → Search → B2B Platforms → LLM Scoring |
| 🎯 Keyword Generator | AI-generated targeted B2B search keywords |
| 🔍 Company Search | Search by industry / region / keywords |
| 📧 Contact Extraction | Extract emails, phones, social media from websites |
| 👥 Employee Search | Find key decision-makers at target companies |

### Command-Line Usage

#### 1. Company Search

Use the `serper_company_search.py` script to search for company information:

#### Search companies based on industry and region:
```bash
python serper_company_search.py --general-search --industry "solar energy" --region "California" --gl "us"
```

#### Use custom queries (full control over query content):
```bash
python serper_company_search.py --general-search --custom-query "top solar panel manufacturers California renewable energy" --gl "us"
```

#### Parameter Description:
- `--general-search`: Use general search mode
- `--linkedin-search`: Use LinkedIn company-specific search mode
- `--industry`: Target industry keywords
- `--region`: Target region/city
- `--custom-query`: Fully customized search query (overrides industry, region, and default keywords)
- `--gl`: Region code (e.g., "us", "uk", "cn", etc.)
- `--num`: Number of results to return (default 30)
- `--keywords`: Additional keywords (comma-separated)
- `--output`: Custom output filename

#### Results:
Results will be saved in the `output/company/` directory in CSV and JSON formats. Filenames are automatically generated based on search parameters. The CSV files include the following columns:
- Company Name: Name of the company
- Search Query: The search query used
- URL: Company website link
- Domain: Company domain
- LinkedIn: LinkedIn link (if available)
- GL: Region code parameter
- And other detailed information

#### 2. Contact Information Extraction

Use the `extract_contact_info.py` script to extract contact information from websites:

#### Process a single website:
```bash
python extract_contact_info.py --url example.com --headless
```

#### Process multiple websites (from a text file):
```bash
python extract_contact_info.py --url-list urls.txt --timeout 15000
```

#### Process company search results:
```bash
python extract_contact_info.py --csv output/company/general_solar_energy_california_us_1234567890.csv --url-column Domain
```

> **Note**: When using the `--csv` parameter without specifying `--output`, the output file will be automatically named "contact_info_" plus the original CSV filename. For example, input `general_custom_project_us_1234567890.csv` will generate `contact_info_general_custom_project_us_1234567890.csv`.

#### Process CSV and merge results:
```bash
python extract_contact_info.py --csv companies.csv --url-column Domain --merge-results
```

#### Parameter Description:
- `--url`: Single website URL
- `--url-list`: Text file containing multiple URLs (one per line)
- `--csv`: CSV file containing a URL column
- `--url-column`: Name of the URL column in the CSV file (default "URL")
- `--domain-column`: Alternative domain column name (default "Domain")
- `--output`: Custom output filename
- `--headless`: Run browser in headless mode (no UI)
- `--timeout`: Page load timeout in milliseconds
- `--visit-contact`: Enable contact page visit (more comprehensive but slower)
- `--merge-results`: Merge extracted contact information with the input CSV (only applicable with the `--csv` option)

#### Results:
- Basic contact information results are saved in the `output/contact/` directory, including:
  - Company name
  - Email addresses
  - Phone numbers
  - Physical addresses
  - Social media links (LinkedIn, Twitter, Facebook, Instagram)
  
- When using `--merge-results`, an additional `*_merged.csv` file is generated, containing the original CSV data plus the extracted contact information.

#### 3. Employee Search

Use the `serper_employee_search.py` script to find company employees and decision-makers:

#### Search for employees of a specific company:
```bash
python serper_employee_search.py --company "Tesla" --position "sales manager" --location "California"
```

#### Process a list of companies (from search results):
```bash
python serper_employee_search.py --input-file general_solar_energy_california_us_1234567890.csv --position "CEO" --country "United States"
```

> **Note**: When using the `--input-file` parameter, the CSV file must contain a `Company Name` column, which the script will use to search for employees. The CSV file can also contain an optional `Location` column for localizing employees.

#### Parameter Description:
- `--company`: Target company name
- `--input-file`: CSV file containing company information (located in the output directory)
- `--position`: Target position/title
- `--location`: Location/city
- `--country`: Country
- `--keywords`: Additional keywords (comma-separated)
- `--output`: Custom output filename
- `--gl`: Region code (e.g., "us", "uk", etc.)
- `--num`: Number of results to return (default 30)

#### Results:
Results will be saved in the `output/employee/` directory, containing employee names, positions, LinkedIn links, and other available information.

## Advanced Usage

### 🚀 B2B Discovery Flow (New)

`core/b2b_flow.py` is the project's core new feature — fully automated pipeline:

1. **AI Keyword Generation** — LLM generates multi-dimensional keywords for your product + regions
2. **Web Search** — Each keyword searched via Serper or Tavily
3. **B2B Platform site: queries** — Automatic dedicated searches on:
   - Alibaba · Made-in-China · GlobalSources · TradeIndia · EC21
   - Europages · Kompass · ThomasNet
4. **Deduplication** — Merge by domain, one entry per company
5. **LLM Scoring** — Each result scored 0-10 for company fit and relevance
6. **Filtered output** — Only leads above your minimum score threshold

**Python API:**

```python
from core.b2b_flow import B2BFlow

flow = B2BFlow(product="solar inverter", regions=["Germany", "Poland"])
result = flow.run(
    keyword_count=10,
    num_search_results=10,
    gl="de",
    run_b2b_platforms=True,
    llm_filter=True,
    min_llm_score=6.0,
)
print(f"Found {len(result['filtered_results'])} qualified leads")
```

**Web UI:** Start the app and open the **🚀 B2B Flow** page in the sidebar.

---

### Full CLI Pipeline (Keywords → Companies → Contacts → Decision Makers)

1. Generate keywords with AI:

```bash
python keyword_generator.py --product "solar inverter" --region "Germany,Poland" --count 20
```

2. Batch search all keywords:

```bash
python serper_company_search.py --general-search --custom-query "solar inverter distributor Germany" --gl de
```

3. Extract contact info from all company results:

```bash
python process_all_companies_en.py
```

4. Find decision makers:

```bash
python serper_employee_search.py --input-file batch_keywords_de_1234567890.csv --position "purchasing manager"
```

## Notes and Limitations

- Search APIs have free usage limits; please control query frequency reasonably
- Some websites may block automated access; you may need to adjust request headers or use proxies
- Contact information extraction accuracy depends on website structure and content quality
- Please comply with relevant laws, regulations, and platform terms of use
- For large-scale batch processing, it's recommended to control concurrency and add sufficient delays

## Frequently Asked Questions

**Q: Which search provider should I choose?**

A: Serper.dev offers 2,500 free searches/month with fast, high-quality results — recommended as the default. Tavily offers 1,000 free searches/month with relevance scores included in results. Switch by setting `SEARCH_PROVIDER=serper` or `SEARCH_PROVIDER=tavily` in `.env`.

**Q: Which LLM is recommended?**

A: For international users, `openai/gpt-4o-mini` or `openrouter/google/gemma-3-27b-it:free` (free). For China-based users, `deepseek/deepseek-chat` offers excellent quality at very low cost.

**Q: Unable to extract contact information from certain websites**

A: Try the `--visit-contact` parameter to enable contact page visiting, or increase `--timeout`.

**Q: B2B Flow scores are all low — what to do?**

A: Lower the `min_llm_score` threshold (e.g. from 6 to 4), or make the product description more specific. A precise product description significantly improves scoring quality.

**Q: API key configuration issues**

A: Ensure API keys in `.env` are correctly formatted with no quotes or extra spaces. Verify LLM config with: `python -c "from core.llm_client import is_llm_available; print(is_llm_available())"`

## Contact Information

<div style="display: flex; justify-content: space-between;">
  <div style="text-align: center; margin-right: 20px;">
    <h3>Personal WeChat</h3>
    <img src="img/me_code.jpg" width="200" alt="Personal WeChat QR Code">
  </div>
  <div style="text-align: center; margin-right: 20px;">
    <h3>WeChat Group</h3>
    <img src="img/group_code.jpg" width="200" alt="WeChat Group QR Code">
  </div>
  <div style="text-align: center;">
    <h3>Telegram Group</h3>
    <a href="https://t.me/+jjmdspjqpbcwOGFl">Join Telegram Group</a>
  </div>
</div>

---

**Want a ready-to-use hosted version?** Visit [B2BInsights.io](https://b2binsights.io) for the AI agent platform that automates B2B customer discovery at scale.