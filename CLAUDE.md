# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment Setup

This project uses Conda for virtual environment management. The environment name is `aifinder_env`.

### Important: Always ensure you're in the correct environment before running any scripts:
```bash
conda activate aifinder_env
```

## Project Overview

This is an AI-powered B2B customer discovery tool for international trade and sales. The system automates the process of finding target companies, extracting contact information, and identifying key decision makers using search engine APIs and AI technology.

## Core Components

### Main Scripts

1. **`serper_company_search.py`** - Company Discovery Engine
   - Searches for companies by industry, region, and keywords
   - Supports both general Google search and LinkedIn-specific company search
   - Uses Serper.dev API for search operations
   - Outputs structured CSV/JSON data to `output/company/`

2. **`extract_contact_info.py`** - Website Content Extractor  
   - Extracts contact information from company websites using Playwright
   - Identifies emails, phone numbers, addresses, social media profiles
   - Supports batch processing with browser instance reuse for efficiency
   - Uses multiple LLM providers (OpenAI, Anthropic, Google, Huoshan/Volcano) for content analysis
   - Outputs to `output/contact/` with optional data merging capabilities

3. **`serper_employee_search.py`** - Employee & Decision Maker Search
   - Searches for employees and key decision makers within target companies
   - Focuses on LinkedIn profile discovery and role identification
   - Outputs structured employee data to `output/employee/`

4. **`process_all_companies.py`** / **`process_all_companies_en.py`** - Batch Processing Scripts
   - Automates processing of all company CSV files in batch
   - Orchestrates the contact extraction workflow across multiple files

## Environment Configuration

### Required API Keys
- `SERPER_API_KEY` - Required for all search operations
- LLM API keys - Optional but recommended for better content analysis:
  - `ARK_API_KEY` + `ARK_BASE_URL` + `ARK_MODEL` (Huoshan/Volcano - recommended for Chinese users)
  - `OPENAI_API_KEY` 
  - `ANTHROPIC_API_KEY`
  - `GOOGLE_API_KEY`

### Configuration Options
- `LLM_PROVIDER` - Choose between: `openai`, `anthropic`, `google`, `huoshan`, `none`
- `HEADLESS` - Browser headless mode (default: true)
- `TIMEOUT` - Page load timeout in milliseconds (default: 15000)
- `VISIT_CONTACT_PAGE` - Enable contact page crawling (default: false)

## Common Commands

### Installation & Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Configure environment (copy .env.example to .env and fill in API keys)
cp .env.example .env
```

### Company Search
```bash
# Search by industry and region
python serper_company_search.py --general-search --industry "solar energy" --region "California" --gl "us"

# Custom search query
python serper_company_search.py --general-search --custom-query "renewable energy companies Texas" --gl "us"

# LinkedIn-specific search
python serper_company_search.py --linkedin-search --industry "software" --region "San Francisco"
```

### Contact Information Extraction
```bash
# Process single website
python extract_contact_info.py --url example.com --headless

# Process CSV file with company data
python extract_contact_info.py --csv output/company/companies.csv --url-column Domain --merge-results

# Batch process all company files
python process_all_companies.py
```

### Employee Search
```bash
# Search employees at specific company
python serper_employee_search.py --company "Tesla" --position "sales manager" --location "California"

# Process company CSV file for employee search
python serper_employee_search.py --input-file company_results.csv --position "CEO"
```

## Architecture & Data Flow

### Directory Structure
```
output/
├── company/    # Company search results (CSV/JSON)
├── contact/    # Contact information extracts
└── employee/   # Employee search results
```

### Processing Pipeline
1. **Discovery**: `serper_company_search.py` → Company data in `output/company/`
2. **Enrichment**: `extract_contact_info.py` → Contact data in `output/contact/`  
3. **Personnel**: `serper_employee_search.py` → Employee data in `output/employee/`

### Key Design Patterns
- **Browser Instance Reuse**: `WebsiteContentExtractor` maintains browser sessions for batch processing efficiency
- **Multi-Provider LLM**: Configurable LLM backend with fallback support for content analysis
- **Structured Output**: Consistent CSV/JSON output format across all components with timestamp-based naming
- **Error Recovery**: Timeout handling, content cleaning, and graceful degradation for website extraction
- **Batch Operations**: Automated processing scripts for handling multiple files

## File Naming Conventions

Output files use descriptive naming with timestamps:
- Company search: `{search_type}_{industry}_{region}_{gl}_{timestamp}.csv`
- Custom queries: `{search_type}_custom_{query}_{gl}_{timestamp}.csv`
- Contact extraction: `contact_info_{original_filename}.csv`
- Merged results: `{original_filename}_merged.csv`

## Development Notes

- The codebase handles Chinese and English documentation (README.md vs README_en.md)
- Browser automation uses Playwright with Chromium for reliable website content extraction
- Search operations are rate-limited by Serper.dev API quotas
- LLM content analysis is optional but significantly improves extraction accuracy
- All scripts support headless operation for server deployment