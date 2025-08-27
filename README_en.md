# AI Business and Contact Intelligence Search Tool

[中文版本](README.md) | [Web Interface Guide](README_WEB.md) | [Docker Deployment](DOCKER_DEPLOY.md)

A powerful set of Python tools for automating the customer development process in international trade and B2B sales. This tool uses search engine APIs and AI technology to help you quickly find target companies, extract contact information, and identify key decision-makers. Supports both command-line and web interface usage.

> **Recommended Reading**: If you're not familiar with advanced search engine techniques, we recommend reading this [Advanced Search Engine Usage Tutorial](https://zhuanlan.zhihu.com/p/1908208213234554242) first. It will help you build more effective search queries.

## Project Features

### Core Features

This project provides **two usage methods**:

#### 1. Command-Line Tools (For Technical Users)
Contains three main Python scripts, each addressing different stages of the sales process:

- **Company Search** (`serper_company_search.py`)
  - Search for target companies based on industry, region, and keywords
  - Support custom search queries with full control over search content
  - Automatically extract company websites, domains, and basic information
  - Support for both general search and LinkedIn company-specific search

- **Contact Information Extraction** (`extract_contact_info.py`)
  - Automatically extract contact information from company websites
  - Identify email addresses, phone numbers, and physical addresses
  - Collect social media accounts (LinkedIn, Twitter, Facebook, Instagram)
  - Support for batch processing of multiple URLs while optimizing browser resources
  - Option to merge results with input CSV files for data integration

- **Employee and Decision-Maker Search** (`serper_employee_search.py`)
  - Search for employees of target companies based on company name and position
  - Identify key decision-makers and potential contacts
  - Extract information from employee LinkedIn profiles

#### 2. Web Interface (For Non-Technical Users)
Modern Streamlit-based web interface providing:

- **Visual Operation Interface** - Use without command-line knowledge
- **Real-time Result Display** - View search and extraction results instantly
- **Batch Processing Management** - Easily manage multiple batch tasks
- **Data Export Function** - One-click download of CSV/JSON format results
- **Docker Deployment Support** - Quick deployment to any server

## Problems Solved

- **Reduce Customer Development Costs**: Decrease manual search and data collection time, improve sales team efficiency
- **Increase Customer Accuracy**: Precisely target companies that match industry and regional criteria
- **Simplify Contact Process**: Directly obtain effective contact information without switching between multiple platforms
- **Identify Key Decision-Makers**: Directly find key personnel in companies, shortening the sales cycle

## Technical Implementation

- **Search Technology**: Uses Serper.dev API for efficient search engine queries
- **Web Content Extraction**: Uses Playwright for automated browser rendering and website content extraction
- **AI Content Analysis**: Analyzes web content through various LLM models (OpenAI, Volcano Engine, Anthropic, Google) to extract structured information
- **Parallel Processing**: Optimizes browser instance management for efficient batch processing
- **Fault Tolerance**: Includes timeout handling, content cleaning, and error recovery features

## Installation Guide

### Prerequisites

- Python 3.8+
- Serper.dev API key ([Apply for free key](https://serper.dev/))
- (Optional) LLM API key (Volcano Engine API recommended for users in China)
- (Optional) Docker and Docker Compose (for containerized deployment)

### Method 1: Local Installation

1. Clone or download the project files

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright browser (for website content extraction):
```bash
playwright install chromium
```

4. Create `.env` configuration file (in the project root directory):
```
# Required: Serper API key
SERPER_API_KEY=your_serper_api_key_here

# LLM Configuration (choose one)
LLM_PROVIDER=huoshan  # Options: openai, anthropic, google, huoshan, none

# Volcano Engine Configuration (recommended for users in China)
ARK_API_KEY=your_ark_api_key_here
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ARK_MODEL=doubao-seed-1-6-250615

# Or use other LLM services
# OPENAI_API_KEY=your_openai_api_key_here
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# GOOGLE_API_KEY=your_google_api_key_here

# Website extraction configuration
HEADLESS=true
TIMEOUT=15000
VISIT_CONTACT_PAGE=false
```

### Method 2: Docker Quick Deployment (Recommended)

Using Docker avoids environment configuration issues and is especially suitable for production deployment:

```bash
# 1. Configure environment variables
cp .env.example .env
# Edit .env file to add your API keys

# 2. Use deployment script (recommended)
chmod +x docker_deploy.sh
./docker_deploy.sh

# Or manually use docker-compose
docker-compose up -d
```

After deployment, visit `http://localhost:8501` to use the web interface.

For detailed Docker deployment instructions, please refer to [Docker Deployment Guide](DOCKER_DEPLOY.md).

## Usage Guide

### Web Interface Usage (Recommended for Beginners)

1. **Start Web Service**:
```bash
# Local startup
streamlit run streamlit_app.py

# Or use Docker
docker-compose up -d
```

2. **Access Interface**: Open `http://localhost:8501` in your browser

3. **Use Features**:
   - Select function from left menu (Company Search, Contact Extraction, Employee Search)
   - Fill in search criteria
   - Click execute and view results
   - Download data in CSV or JSON format

For detailed web interface instructions, please refer to [Web Interface Guide](README_WEB.md).

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

## Advanced Usage Tips

### Complete Sales Process Automation:

1. Search for target companies using a custom query:
```bash
python serper_company_search.py --general-search --custom-query "renewable energy companies Texas usa" --gl "us" --output texas_renewable.csv
```

2. Extract and merge contact information from search results:
```bash
python extract_contact_info.py --csv output/company/texas_renewable.csv --url-column Domain --headless --merge-results
```

3. Find key decision-makers:
```bash
python serper_employee_search.py --input-file texas_renewable.csv --position "purchasing manager" --country "United States"
```

### Batch Processing Scripts:

The project provides batch processing scripts for automating multiple file processing:

- **`process_all_companies.py`** - Batch process all company CSV files (Chinese version)
- **`process_all_companies_en.py`** - Batch process all company CSV files (English version)

```bash
# Batch process all CSV files in output/company/ directory
python process_all_companies_en.py

# Will automatically:
# 1. Read all CSV files from output/company/ directory
# 2. Extract contact information for each file
# 3. Generate corresponding contact info files to output/contact/
```

### Optimize Contact Extraction:

- For slow-loading websites, increase timeout:
```bash
python extract_contact_info.py --url slowwebsite.com --timeout 30000
```

- For special website structures, enable contact page visiting:
```bash
python extract_contact_info.py --url example.com --visit-contact
```

- Performance optimization for batch processing multiple URLs:
```bash
# Script automatically reuses browser instances for improved efficiency
python extract_contact_info.py --url-list many_urls.txt --headless --timeout 10000
```


## Notes and Limitations

- Serper.dev API has free usage limits; please control query frequency reasonably
- Some websites may block automated access; you may need to adjust request headers or use proxies
- Contact information extraction accuracy depends on website structure and content quality
- Please comply with relevant laws, regulations, and platform terms of use
- For large-scale batch processing, it's recommended to control concurrency and add sufficient delays

## Frequently Asked Questions

**Q: Unable to extract contact information from certain websites**  
A: Try using the `--visit-contact` parameter to enable contact page visiting, or adjust the `--timeout` parameter to increase loading time.

**Q: Browser windows frequently open and close**  
A: Add the `--headless` parameter to use headless mode for improved efficiency. When batch processing multiple URLs, the system automatically optimizes browser instance usage.

**Q: How to process contact information in CSV data**  
A: Use the `--merge-results` parameter to merge extracted contact information with the original CSV, generating a new file containing all data.

**Q: API key configuration issues**  
A: Ensure the API keys in the `.env` file are correctly formatted and do not contain quotes or extra spaces.

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