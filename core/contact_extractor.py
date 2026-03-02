"""
Contact Extractor Core Module
Refactored from extract_contact_info.py for web interface
"""
import os
import sys
import re
import json
import csv
import time
import requests
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, urljoin
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.llm_client import is_llm_available, get_llm_model

# Ensure output directories exist
OUTPUT_DIR = "output"
CONTACT_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "contact")
if not os.path.exists(CONTACT_OUTPUT_DIR):
    os.makedirs(CONTACT_OUTPUT_DIR, exist_ok=True)


class ContactExtractor:
    """Enhanced contact information extractor with web interface support"""
    
    def __init__(self, headless: bool = True, timeout: int = 15000, 
                 visit_contact_page: bool = False, use_llm: bool = False):
        """
        Initialize contact extractor
        
        Args:
            headless: Run browser in headless mode
            timeout: Page load timeout in milliseconds
            visit_contact_page: Whether to visit contact pages
            use_llm: Whether to use LLM for enhanced extraction
        """
        self.headless = headless
        self.timeout = timeout
        self.visit_contact_page = visit_contact_page
        self.use_llm = use_llm and self._check_llm_available()
        self.browser = None
        self.context = None
        self.playwright = None
        
        # Session for HTTP requests
        self.session = requests.Session()
        
    def _check_llm_available(self) -> bool:
        """Check if LLM is configured and available via core/llm_client."""
        return is_llm_available()
    
    def initialize_browser(self):
        """Initialize browser instance if not already created"""
        if self.browser is None:
            from playwright.sync_api import sync_playwright
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.context = self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
    
    def close_browser(self):
        """Close browser instance and playwright"""
        if self.browser:
            self.browser.close()
            self.browser = None
            self.context = None
        if self.playwright:
            self.playwright.stop()
            self.playwright = None
    
    def extract_from_url(self, url: str) -> Dict[str, Any]:
        """
        Extract contact information from a single URL
        
        Args:
            url: Website URL to extract from
            
        Returns:
            Dictionary containing extracted contact information
        """
        try:
            # Ensure URL has protocol
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Initialize browser if needed
            if not self.browser:
                self.initialize_browser()
            
            # Create new page
            page = self.context.new_page()
            page.set_default_navigation_timeout(self.timeout)
            
            result = {
                'url': url,
                'domain': self._extract_domain(url),
                'emails': [],
                'phones': [],
                'addresses': [],
                'social_media': {},
                'contact_page': None,
                'extraction_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            try:
                # Load main page
                page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
                page.wait_for_timeout(2000)  # Wait for dynamic content
                
                # Get page content
                content = page.content()
                
                # Extract from main page
                self._extract_contact_info(content, result)
                
                # Visit contact page if enabled
                if self.visit_contact_page:
                    contact_url = self._find_contact_page(page, url)
                    if contact_url:
                        try:
                            page.goto(contact_url, wait_until="domcontentloaded", timeout=self.timeout)
                            page.wait_for_timeout(2000)
                            contact_content = page.content()
                            self._extract_contact_info(contact_content, result)
                            result['contact_page'] = contact_url
                        except:
                            pass
                
                # Use LLM for enhanced extraction if enabled
                if self.use_llm and content:
                    llm_results = self._extract_with_llm(content, url)
                    if llm_results:
                        self._merge_llm_results(result, llm_results)
                
            finally:
                page.close()
            
            return result
            
        except Exception as e:
            print(f"Error extracting from {url}: {str(e)}")
            return {
                'url': url,
                'error': str(e),
                'extraction_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def extract_from_urls(self, urls: List[str], progress_callback=None) -> List[Dict]:
        """
        Extract contact information from multiple URLs
        
        Args:
            urls: List of URLs to process
            progress_callback: Optional callback function for progress updates
            
        Returns:
            List of extraction results
        """
        results = []
        
        try:
            self.initialize_browser()
            
            for i, url in enumerate(urls):
                if progress_callback:
                    progress_callback(i + 1, len(urls), url)
                
                result = self.extract_from_url(url)
                results.append(result)
                
                # Small delay between requests
                if i < len(urls) - 1:
                    time.sleep(1)
        
        finally:
            self.close_browser()
        
        return results
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.replace('www.', '')
        except:
            return ""
    
    def _extract_contact_info(self, content: str, result: Dict):
        """Extract contact information from HTML content"""
        # Email extraction
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, content)
        result['emails'].extend(emails)
        
        # Phone extraction
        phone_patterns = [
            r'(\+\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}',
            r'\+\d{1,3}\s?\d{2,4}\s?\d{6,10}',
            r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'
        ]
        for pattern in phone_patterns:
            phones = re.findall(pattern, content)
            result['phones'].extend(phones)
        
        # Social media extraction
        social_patterns = {
            'linkedin': r'linkedin\.com/company/([^/"\s]+)',
            'twitter': r'twitter\.com/([^/"\s]+)',
            'facebook': r'facebook\.com/([^/"\s]+)',
            'instagram': r'instagram\.com/([^/"\s]+)'
        }
        
        for platform, pattern in social_patterns.items():
            matches = re.findall(pattern, content)
            if matches and platform not in result['social_media']:
                result['social_media'][platform] = f"https://{platform}.com/{matches[0]}"
        
        # Clean up duplicates
        result['emails'] = list(set(result['emails']))[:5]  # Limit to 5 unique emails
        result['phones'] = list(set(result['phones']))[:5]  # Limit to 5 unique phones
    
    def _find_contact_page(self, page, base_url: str) -> Optional[str]:
        """Find and return contact page URL"""
        contact_selectors = [
            'a[href*="contact"]',
            'a[href*="Contact"]',
            'a:text("Contact")',
            'a:text("Contact Us")',
            'a[href*="about"]',
            'a:text("About")'
        ]
        
        for selector in contact_selectors:
            try:
                links = page.query_selector_all(selector)
                if links:
                    href = links[0].get_attribute('href')
                    if href:
                        if not href.startswith(('http', 'https')):
                            href = urljoin(base_url, href)
                        return href
            except:
                continue
        
        return None
    
    def _extract_with_llm(self, content: str, url: str) -> Optional[Dict]:
        """Use LLM to extract contact information"""
        # This is a placeholder - implement based on your LLM provider
        # The existing extract_contact_info.py has the full implementation
        return None
    
    def _merge_llm_results(self, result: Dict, llm_results: Dict):
        """Merge LLM extraction results with existing results"""
        if 'emails' in llm_results:
            result['emails'].extend(llm_results['emails'])
            result['emails'] = list(set(result['emails']))[:5]
        
        if 'phones' in llm_results:
            result['phones'].extend(llm_results['phones'])
            result['phones'] = list(set(result['phones']))[:5]
    
    def save_results(self, results: List[Dict], filename: Optional[str] = None) -> str:
        """
        Save extraction results to CSV and JSON files
        
        Args:
            results: List of extraction results
            filename: Optional filename (without extension)
            
        Returns:
            Path to saved CSV file
        """
        if not filename:
            timestamp = int(time.time())
            filename = f"contact_extraction_{timestamp}"
        
        csv_path = os.path.join(CONTACT_OUTPUT_DIR, f"{filename}.csv")
        json_path = os.path.join(CONTACT_OUTPUT_DIR, f"{filename}.json")
        
        # Save to CSV
        if results:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                # Flatten the results for CSV
                flat_results = []
                for r in results:
                    flat_result = {
                        'url': r.get('url', ''),
                        'domain': r.get('domain', ''),
                        'emails': ', '.join(r.get('emails', [])),
                        'phones': ', '.join(r.get('phones', [])),
                        'linkedin': r.get('social_media', {}).get('linkedin', ''),
                        'twitter': r.get('social_media', {}).get('twitter', ''),
                        'facebook': r.get('social_media', {}).get('facebook', ''),
                        'instagram': r.get('social_media', {}).get('instagram', ''),
                        'contact_page': r.get('contact_page', ''),
                        'extraction_time': r.get('extraction_time', '')
                    }
                    flat_results.append(flat_result)
                
                writer = csv.DictWriter(f, fieldnames=flat_results[0].keys())
                writer.writeheader()
                writer.writerows(flat_results)
        
        # Save to JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return csv_path
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close_browser()
        if hasattr(self, 'session'):
            self.session.close()