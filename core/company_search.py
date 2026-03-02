"""
Company search core module
Refactored from serper_company_search.py for web interface
"""
import json
import os
import time
import csv
import re
import random
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure output directories exist
OUTPUT_DIR = "output"
COMPANY_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "company")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
if not os.path.exists(COMPANY_OUTPUT_DIR):
    os.makedirs(COMPANY_OUTPUT_DIR)

class CompanySearcher:
    """Company search class with improved API handling"""
    
    MAX_RETRIES = 3  # Maximum retry attempts
    
    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        if not self.api_key:
            raise ValueError("SERPER_API_KEY not found in environment variables")
        
        self.base_url = "https://google.serper.dev/search"
        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Use requests session for connection pooling and set default headers
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def search_companies(
        self,
        search_mode: str = "general",
        industry: Optional[str] = None,
        region: Optional[str] = None,
        custom_query: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        gl: str = "us",
        num_results: int = 30
    ) -> Dict:
        """
        Unified company search interface
        Returns: {"success": bool, "data": list, "error": str, "output_file": str}
        """
        try:
            if search_mode == "linkedin":
                results = self._search_linkedin_companies(
                    industry, region, keywords, gl, num_results
                )
            else:
                results = self._search_general_companies(
                    industry, region, keywords, custom_query, gl, num_results
                )
            
            # Save results to file (maintain original behavior)
            output_file = self._save_results(results, search_mode, industry, region, custom_query, gl)
            
            return {
                "success": True,
                "data": results,
                "error": None,
                "output_file": output_file
            }
        except Exception as e:
            return {
                "success": False,
                "data": [],
                "error": str(e),
                "output_file": None
            }
    
    def _extract_domain(self, url):
        """Extract domain from URL"""
        domain_pattern = r'https?://(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        match = re.search(domain_pattern, url)
        if match:
            return match.group(1)
        return ""
    
    def _search_linkedin_companies(self, industry, region, keywords, gl, num_results):
        """Search for companies on LinkedIn"""
        # Construct the search query
        query_parts = ["site:linkedin.com/company"]
        
        if industry:
            query_parts.append(f'"{industry}"')
        # Only add region if it's different from gl (to avoid redundancy)
        if region and region.lower() != gl.lower():
            query_parts.append(f'"{region}"')
        elif region and region.lower() == gl.lower():
            # For country codes matching gl, skip to avoid redundancy
            pass
        if keywords:
            query_parts.extend(keywords)
        
        query = " ".join(query_parts)
        
        # Serper API limitation: num must be <= 20 for certain queries
        # to avoid "Query not allowed" error
        safe_num_results = min(num_results, 20)
        
        payload = json.dumps({
            "q": query,
            "gl": gl,
            "num": safe_num_results
        })
        
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.post(self.base_url, data=payload)
                response.raise_for_status()
                results = response.json()
                
                # Process results
                companies = self._extract_linkedin_companies(results, query)
                return companies
                
            except requests.exceptions.RequestException as e:
                if attempt < self.MAX_RETRIES - 1:
                    backoff_time = (2 ** attempt) * random.uniform(1, 3)
                    time.sleep(backoff_time)
                else:
                    raise Exception(f"Failed after {self.MAX_RETRIES} retries: {str(e)}")
    
    def _search_general_companies(self, industry, region, keywords, custom_query, gl, num_results):
        """Search for companies on Google"""
        if custom_query:
            # Input validation for custom query
            custom_query = custom_query[:500]  # Limit length
            query = custom_query
        else:
            # Construct the search query
            query_parts = ["company", "business"]
            if industry:
                query_parts.append(f'"{industry}"')
            # Only add region if it's different from gl (to avoid redundancy)
            if region and region.lower() != gl.lower():
                query_parts.append(f'"{region}"')
            elif region and region.lower() == gl.lower():
                # If region matches gl, add a more specific context
                if gl.lower() in ["us", "uk", "cn", "de", "fr", "jp", "au", "ca", "in", "br"]:
                    # For country codes, don't add redundant country name
                    pass
                else:
                    query_parts.append(f'"{region}"')
            if keywords:
                query_parts.extend(keywords)
            query = " ".join(query_parts)
        
        # Serper API limitation: num must be <= 20 for certain queries
        # to avoid "Query not allowed" error
        safe_num_results = min(num_results, 20)
        
        payload = json.dumps({
            "q": query,
            "gl": gl,
            "num": safe_num_results
        })
        
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.post(self.base_url, data=payload)
                response.raise_for_status()
                results = response.json()
                
                # Extract company information
                companies = self._extract_general_companies(results, query, custom_query)
                return companies
                
            except requests.exceptions.RequestException as e:
                if attempt < self.MAX_RETRIES - 1:
                    backoff_time = (2 ** attempt) * random.uniform(1, 3)
                    time.sleep(backoff_time)
                else:
                    raise Exception(f"Failed after {self.MAX_RETRIES} retries: {str(e)}")
    
    def _extract_linkedin_companies(self, search_results, query):
        """Extract company information from LinkedIn search results"""
        companies = []
        
        if not search_results or 'organic' not in search_results:
            return companies
        
        for result in search_results.get('organic', []):
            link = result.get('link', '')
            
            if 'linkedin.com/company/' in link:
                # Extract company name from URL
                company_name_match = re.search(r'linkedin\.com/company/([^/]+)', link)
                company_name = company_name_match.group(1).replace('-', ' ').title() if company_name_match else ""
                
                if not company_name and result.get('title'):
                    company_name = result.get('title').split('|')[0].split('-')[0].strip()
                
                company_info = {
                    'name': company_name,
                    'query': query,
                    'url': link,
                    'title': result.get('title', ''),
                    'description': result.get('snippet', ''),
                    'domain': '',
                    'linkedin': link,
                    'type': 'linkedin_search'
                }
                companies.append(company_info)
        
        return companies
    
    def _extract_general_companies(self, search_results, query, custom_query=None):
        """Extract company information from general search results"""
        companies = []
        
        if not search_results or 'organic' not in search_results:
            return companies
        
        for result in search_results.get('organic', []):
            link = result.get('link', '')
            title = result.get('title', '')
            description = result.get('snippet', '')
            
            # Skip non-company results
            skip_domains = ['wikipedia.org', 'youtube.com', 'linkedin.com/in/', 'twitter.com/hashtag']
            if any(domain in link for domain in skip_domains):
                continue
            
            # Check if result appears to be a company
            company_indicators = [
                'company', 'corporation', 'inc', 'ltd', 'limited', 'gmbh', 'co.', 'corp',
                'business', 'enterprise', 'industry', 'manufacturer', 'supplier', 'service'
            ]
            
            is_likely_company = (
                any(indicator in title.lower() or indicator in description.lower() 
                    for indicator in company_indicators) or
                self._extract_domain(link)
            )
            
            if is_likely_company:
                company_name = title.split('-')[0].split('|')[0].strip()
                
                company_info = {
                    'name': company_name,
                    'query': query,
                    'url': link,
                    'title': title,
                    'description': description,
                    'domain': self._extract_domain(link),
                    'type': "general_search"
                }
                
                if custom_query:
                    company_info['custom_query'] = custom_query
                
                if 'linkedin.com/company' in link:
                    company_info['linkedin'] = link
                else:
                    company_info['linkedin'] = ""
                
                companies.append(company_info)
        
        return companies
    
    def _save_results(self, companies, search_mode, industry, region, custom_query, gl):
        """Save search results to CSV and JSON files"""
        timestamp = int(time.time())
        
        # Generate filename based on search parameters
        if custom_query:
            # Process custom query for filename
            query_str = custom_query.replace('/', '').replace('\\', '').replace('..', '')
            query_str = query_str.replace(' ', '_').replace('"', '').lower()
            query_str = ''.join(c for c in query_str if c.isalnum() or c in '_-')[:40]
            filename = f"{search_mode}_custom_{query_str}_{gl}_{timestamp}"
        else:
            industry_str = industry.replace(' ', '_').lower() if industry else 'no_industry'
            region_str = region.replace(' ', '_').lower() if region else 'no_region'
            filename = f"{search_mode}_{industry_str}_{region_str}_{gl}_{timestamp}"
        
        csv_file = os.path.join(COMPANY_OUTPUT_DIR, f"{filename}.csv")
        json_file = os.path.join(COMPANY_OUTPUT_DIR, f"{filename}.json")
        
        # Save to CSV
        if companies:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=companies[0].keys())
                writer.writeheader()
                writer.writerows(companies)
        
        # Save to JSON
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(companies, f, indent=2, ensure_ascii=False)
        
        return csv_file
    
    def batch_search(
        self,
        keywords: List[str],
        gl: str = "us",
        num_results: int = 10,
        delay: float = 1.5,
    ) -> Dict:
        """
        Run company search for multiple keywords sequentially and merge results.
        Deduplicates by domain so the same company doesn't appear twice.

        Args:
            keywords: List of search keyword strings (e.g. from keyword_generator.py)
            gl: Geographic locale code (default "us")
            num_results: Results per keyword (default 10, lower = faster + fewer API credits)
            delay: Seconds to wait between requests (default 1.5)

        Returns:
            {"success": bool, "data": list, "error": str, "output_file": str,
             "stats": {"keywords_searched": int, "total_raw": int, "after_dedup": int}}
        """
        if not keywords:
            return {"success": False, "data": [], "error": "No keywords provided", "output_file": None, "stats": {}}

        all_companies: List[Dict] = []
        errors: List[str] = []

        for i, kw in enumerate(keywords):
            try:
                companies = self._search_general_companies(
                    industry=None,
                    region=None,
                    keywords=None,
                    custom_query=kw,
                    gl=gl,
                    num_results=num_results,
                )
                all_companies.extend(companies)
            except Exception as e:
                errors.append(f"[{kw}] {e}")

            if i < len(keywords) - 1:
                time.sleep(delay)

        total_raw = len(all_companies)

        # Deduplicate: prefer entries with a domain; keep first occurrence per domain
        seen_domains: set = set()
        seen_urls: set = set()
        deduped: List[Dict] = []
        no_domain: List[Dict] = []

        for c in all_companies:
            domain = (c.get("domain") or "").strip().lower()
            url = (c.get("url") or "").strip().lower()
            if domain:
                if domain not in seen_domains:
                    seen_domains.add(domain)
                    deduped.append(c)
            else:
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    no_domain.append(c)

        merged = deduped + no_domain

        # Save merged results
        timestamp = int(time.time())
        filename = f"batch_keywords_{gl}_{timestamp}"
        csv_file = os.path.join(COMPANY_OUTPUT_DIR, f"{filename}.csv")
        json_file = os.path.join(COMPANY_OUTPUT_DIR, f"{filename}.json")

        if merged:
            with open(csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=merged[0].keys())
                writer.writeheader()
                writer.writerows(merged)

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)

        stats = {
            "keywords_searched": len(keywords),
            "total_raw": total_raw,
            "after_dedup": len(merged),
            "errors": errors,
        }

        return {
            "success": True,
            "data": merged,
            "error": "; ".join(errors) if errors else None,
            "output_file": csv_file,
            "stats": stats,
        }

    def __del__(self):
        """Close session when object is destroyed"""
        if hasattr(self, 'session'):
            self.session.close()