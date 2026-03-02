# AI Customer Finder - Web Interface

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Serper API Key (get from [serper.dev](https://serper.dev))

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/xiongQvQ/AI_Find_Customer.git
cd AI_Find_Customer
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
playwright install chromium
```

3. **Configure API keys**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

4. **Run the application**
```bash
streamlit run streamlit_app.py
```

The application will open in your browser at `http://localhost:8501`

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)
```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

### Using Docker directly
```bash
# Build the image
docker build -t ai-customer-finder .

# Run the container
docker run -d \
  -p 8501:8501 \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/.env:/app/.env:ro \
  --name ai-customer-finder \
  ai-customer-finder
```

## 📱 Features

### 1. Company Search
- Search by industry and region
- LinkedIn company search
- Custom search queries
- Export to CSV/JSON

### 2. Contact Extraction
- Extract emails, phones from websites
- Batch processing from CSV
- AI-enhanced extraction (optional)
- Contact page crawling

### 3. Employee Search
- Find decision makers by title
- Search across multiple companies
- LinkedIn profile discovery
- Export employee data

## 🔧 Configuration

### Required Environment Variables
```env
# Serper API (Required)
SERPER_API_KEY=your_serper_api_key

# LLM Provider (Optional - for enhanced extraction)
LLM_PROVIDER=openai  # or anthropic, google, huoshan
OPENAI_API_KEY=your_openai_key  # if using OpenAI
```

### Optional Settings
```env
# Browser settings
HEADLESS=true
TIMEOUT=15000

# Feature flags
VISIT_CONTACT_PAGE=false
```

## 📁 Project Structure

```
AI_Find_Customer/
├── streamlit_app.py          # Main web application
├── pages/                    # Streamlit pages
│   ├── 1_🔍_Company_Search.py
│   ├── 2_📧_Contact_Extraction.py
│   └── 3_👥_Employee_Search.py
├── core/                     # Core business logic
│   ├── company_search.py
│   ├── contact_extractor.py
│   └── employee_search.py
├── components/               # UI components
│   └── common.py
├── output/                   # Data output directory
│   ├── company/
│   ├── contact/
│   └── employee/
└── .env                      # Configuration file
```

## 💻 Usage Guide

### Company Search
1. Select search mode (General/LinkedIn/Custom)
2. Enter industry keywords and/or region
3. Adjust advanced options if needed
4. Click "Start Search"
5. View results and download data

### Contact Extraction
1. Choose input method:
   - Single URL for quick extraction
   - CSV file for batch processing
   - Use results from Company Search
2. Enable options:
   - Visit Contact Pages for better results
   - Use AI for enhanced accuracy
3. Click "Start Extraction"
4. Download extracted contact data

### Employee Search
1. Specify target companies:
   - Single company name
   - Select from previous searches
2. Enter job position/title to search
3. Add location filters (optional)
4. Click "Search Employees"
5. Export employee profiles

## 🛠️ Advanced Usage

### Batch Processing
The application supports batch processing for all features:
- Upload CSV files with multiple companies
- Process multiple URLs simultaneously
- Search employees across company lists

### API Rate Limiting
The application includes:
- Automatic retry with exponential backoff
- Connection pooling for efficiency
- Rate limiting protection

### Data Export
All results can be exported in:
- CSV format for spreadsheets
- JSON format for programmatic use
- Automatic saving to output directory

## 🔒 Security Features

- Input validation and sanitization
- Secure API key management
- Resource leak prevention
- Path injection protection

## 📊 Performance

- HTTP connection pooling
- Browser instance reuse
- Parallel processing support
- Efficient memory management

## 🐛 Troubleshooting

### Common Issues

1. **API Key Error**
   - Verify SERPER_API_KEY in .env file
   - Check API credits at serper.dev

2. **Browser Error**
   - Run `playwright install chromium`
   - Check system requirements

3. **No Results Found**
   - Try broader search terms
   - Check geographic location setting
   - Verify internet connection

### Debug Mode
Set in .env:
```env
STREAMLIT_SERVER_ENABLE_CORS=false
STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
```

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📧 Support

- GitHub Issues: [Report bugs](https://github.com/xiongQvQ/AI_Find_Customer/issues)
- Documentation: [Wiki](https://github.com/xiongQvQ/AI_Find_Customer/wiki)

## 🚀 Roadmap

- [ ] Add data visualization charts
- [ ] Support more search engines
- [ ] Email campaign integration
- [ ] CRM system integration
- [ ] Advanced filtering options
- [ ] Export to Excel format
- [ ] Multi-language support
- [ ] API endpoint creation