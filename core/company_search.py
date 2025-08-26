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
from typing import List, Dict, Optional, Tuple, Any
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
    """Company search class with improved API handling and location filtering"""
    
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
        
        # 导入LLM关键词生成器
        try:
            from .llm_keyword_generator import get_keyword_generator
            self.llm_keyword_generator = get_keyword_generator()
            self.llm_available = True
            print("✅ LLM关键词生成器初始化成功")
        except ImportError as e:
            print(f"⚠️ LLM关键词生成器不可用: {e}")
            self.llm_keyword_generator = None
            self.llm_available = False
        
        # Location mapping for better region matching
        self.location_mapping = {
            # 美国州名和城市 - 支持规范化地区选择
            '美国加利福尼亚': ['california', 'ca', 'san francisco', 'los angeles', 'silicon valley', 'bay area', 'palo alto', 'mountain view', 'san jose', 'oakland', 'calif'],
            '美国纽约': ['new york', 'ny', 'nyc', 'manhattan', 'brooklyn', 'new york state'],
            '美国德州': ['texas', 'tx', 'dallas', 'houston', 'austin', 'san antonio'],
            '美国佛罗里达': ['florida', 'fl', 'miami', 'orlando', 'tampa', 'jacksonville'],
            '美国华盛顿': ['washington', 'wa', 'seattle', 'portland', 'washington state'],
            '美国马萨诸塞': ['massachusetts', 'ma', 'boston', 'cambridge', 'worcester'],
            '美国伊利诺伊': ['illinois', 'il', 'chicago', 'springfield'],
            
            # 兼容旧格式
            '加利福尼亚': ['california', 'ca', 'san francisco', 'los angeles', 'silicon valley', 'bay area', 'palo alto', 'mountain view', 'san jose', 'oakland'],
            'california': ['california', 'ca', 'san francisco', 'los angeles', 'silicon valley', 'bay area', 'palo alto', 'mountain view', 'san jose', 'oakland'],
            '纽约': ['new york', 'ny', 'nyc', 'manhattan', 'brooklyn'],
            '德州': ['texas', 'tx', 'dallas', 'houston', 'austin'],
            '佛罗里达': ['florida', 'fl', 'miami', 'orlando', 'tampa'],
            '华盛顿': ['washington', 'wa', 'seattle', 'portland'],
            
            # 中国省市 - 支持规范化地区选择
            '中国北京': ['beijing', 'beijing china', '北京市', '北京'],
            '中国上海': ['shanghai', 'shanghai china', '上海市', '上海'],
            '中国深圳': ['shenzhen', 'shenzhen china', '深圳市', '深圳'],
            '中国广州': ['guangzhou', 'guangzhou china', '广州市', '广州'],
            '中国杭州': ['hangzhou', 'hangzhou china', '杭州市', '杭州'],
            '中国苏州': ['suzhou', 'suzhou china', '苏州市', '苏州'],
            '中国南京': ['nanjing', 'nanjing china', '南京市', '南京'],
            '中国成都': ['chengdu', 'chengdu china', '成都市', '成都'],
            
            # 兼容旧格式
            '北京': ['beijing', 'beijing china', '北京市'],
            '上海': ['shanghai', 'shanghai china', '上海市'],
            '深圳': ['shenzhen', 'shenzhen china', '深圳市'],
            '广州': ['guangzhou', 'guangzhou china', '广州市'],
            '广东': ['guangdong', 'guangdong province', '广东省', 'shenzhen', 'guangzhou'],
            '江苏': ['jiangsu', 'jiangsu province', '江苏省', 'nanjing', 'suzhou'],
            '浙江': ['zhejiang', 'zhejiang province', '浙江省', 'hangzhou'],
            
            # 其他国家和地区 - 支持新的格式
            '英国': ['united kingdom', 'uk', 'london', 'manchester', 'birmingham', 'great britain'],
            '英国伦敦': ['london', 'uk', 'united kingdom'],
            '英国曼彻斯特': ['manchester', 'uk', 'united kingdom'],
            '英国伯明翰': ['birmingham', 'uk', 'united kingdom'],
            '英国爱丁堡': ['edinburgh', 'scotland', 'uk'],
            '英国利物浦': ['liverpool', 'uk', 'united kingdom'],
            
            '德国': ['germany', 'berlin', 'munich', 'hamburg', 'deutschland'],
            '德国柏林': ['berlin', 'germany', 'deutschland'],
            '德国慕尼黑': ['munich', 'germany', 'münchen'],
            '德国汉堡': ['hamburg', 'germany'],
            '德国法兰克福': ['frankfurt', 'germany'],
            '德国科隆': ['cologne', 'germany', 'köln'],
            
            '日本': ['japan', 'tokyo', 'osaka', 'kyoto', 'yokohama'],
            '日本东京': ['tokyo', 'japan'],
            '日本大阪': ['osaka', 'japan'],
            '日本名古屋': ['nagoya', 'japan'],
            '日本横滨': ['yokohama', 'japan'],
            '日本京都': ['kyoto', 'japan'],
            
            '新加坡': ['singapore'],
            
            '澳大利亚': ['australia', 'sydney', 'melbourne', 'brisbane', 'perth'],
            '澳大利亚悉尼': ['sydney', 'australia'],
            '澳大利亚墨尔本': ['melbourne', 'australia'],
            '澳大利亚布里斯班': ['brisbane', 'australia'],
            '澳大利亚珀斯': ['perth', 'australia'],
            
            '加拿大': ['canada', 'toronto', 'vancouver', 'montreal', 'ottawa'],
            '加拿大多伦多': ['toronto', 'canada'],
            '加拿大温哥华': ['vancouver', 'canada'],
            '加拿大蒙特利尔': ['montreal', 'canada'],
            '加拿大卡尔加里': ['calgary', 'canada'],
            
            '台湾': ['taiwan', 'taipei', 'taichung', 'kaohsiung'],
            '台湾台北': ['taipei', 'taiwan'],
            '台湾台中': ['taichung', 'taiwan'],
            '台湾高雄': ['kaohsiung', 'taiwan'],
            '台湾新竹': ['hsinchu', 'taiwan'],
        }
    
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
    
    def _extract_location_from_text(self, text: str) -> List[str]:
        """
        从文本中提取地理位置信息，支持中文复合地名
        返回找到的地理位置列表
        """
        if not text:
            return []
        
        text_lower = text.lower()
        locations_found = []
        
        # 增强的地理位置模式 - 优先匹配复合地名
        location_patterns = [
            # 中文复合地名模式（优先级最高）
            r'美国.*?加利福尼亚.*?州?',  # 匹配"美国加利福尼亚州"等
            r'美国.*?(加州|加利福尼亚)',  # 匹配"美国加州"等
            r'中国.*?(北京|上海|广东|深圳|广州|杭州|苏州).*?[市省]?',  # 中国地名
            r'(台湾|台北|台中|高雄).*?[市县]?',  # 台湾地名
            
            # 英文复合地名
            r'united states.*?california',
            r'usa.*?california', 
            r'us.*?california',
            r'california.*?usa?',
            
            # 美国州名和城市（移除word boundary限制）
            r'(california|ca)(?!\w)',  # 避免匹配到care等词
            r'(san francisco|los angeles|silicon valley|bay area|palo alto|mountain view|san jose|oakland)',
            r'(new york|ny|nyc|manhattan|brooklyn)',
            r'(texas|tx|dallas|houston|austin)',
            r'(florida|fl|miami|orlando|tampa)',
            r'(washington|wa|seattle|portland|oregon|or)',
            r'(massachusetts|ma|boston|cambridge)',
            
            # 中国省市（移除word boundary）
            r'(beijing|北京|shanghai|上海|shenzhen|深圳|guangzhou|广州)',
            r'(guangdong|广东|jiangsu|江苏|zhejiang|浙江|shandong|山东)',
            r'(chengdu|成都|hangzhou|杭州|nanjing|南京|suzhou|苏州)',
            
            # 其他国家
            r'(united kingdom|uk|london|manchester|birmingham|scotland)',
            r'(germany|berlin|munich|hamburg|frankfurt)',
            r'(japan|tokyo|osaka|kyoto|yokohama)',
            r'(singapore|australia|sydney|melbourne|canada|toronto|vancouver)',
            
            # 通用地址模式
            r'\w+,\s*[A-Z]{2}(?!\w)',  # City, State format
            r'\d+\s+[A-Za-z\s]+(?:street|st|avenue|ave|road|rd|blvd|boulevard)',  # Street addresses
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                # 如果匹配是元组（分组匹配），取第一个非空组
                for match in matches:
                    if isinstance(match, tuple):
                        location = next((m for m in match if m), '')
                    else:
                        location = match
                    if location:
                        locations_found.append(location.strip())
        
        return list(set(locations_found))  # 去重
    
    def _match_location_with_region(self, extracted_locations: List[str], target_region: str) -> Tuple[bool, str]:
        """
        将提取的地理位置与目标地区进行匹配，支持中文复合地名
        返回 (是否匹配, 匹配的具体位置)
        """
        if not extracted_locations or not target_region:
            return False, ""
        
        target_lower = target_region.lower()
        
        # 1. 直接匹配（完全匹配或包含匹配）
        for location in extracted_locations:
            location_lower = location.lower()
            if target_lower in location_lower or location_lower in target_lower:
                return True, location
        
        # 2. 中文复合地名特殊匹配
        for location in extracted_locations:
            location_lower = location.lower()
            # 匹配"美国加利福尼亚"类型的复合地名
            if '美国' in target_region and '加利福尼亚' in target_region:
                if ('美国' in location_lower and '加利福尼亚' in location_lower) or \
                   ('california' in location_lower):
                    return True, location
            if '美国' in target_region and '加州' in target_region:
                if ('美国' in location_lower and '加州' in location_lower) or \
                   ('california' in location_lower):
                    return True, location
        
        # 3. 通过映射表匹配
        for chinese_region, english_variants in self.location_mapping.items():
            if target_region in chinese_region or chinese_region in target_region:
                # 检查提取的位置是否与英文变体匹配
                for location in extracted_locations:
                    location_lower = location.lower()
                    for variant in english_variants:
                        if variant.lower() in location_lower or location_lower in variant.lower():
                            return True, location
        
        # 4. 反向检查：目标地区是英文时
        for location in extracted_locations:
            location_lower = location.lower()
            for chinese_region, english_variants in self.location_mapping.items():
                for variant in english_variants:
                    if (target_lower in variant.lower() or variant.lower() in target_lower) and \
                       (location_lower in variant.lower() or variant.lower() in location_lower):
                        return True, location
        
        # 5. 模糊匹配：检查关键词
        location_keywords = {
            '加利福尼亚': ['california', 'ca', 'calif'],
            '加州': ['california', 'ca', 'calif'],
            '美国加利福尼亚': ['california', 'ca', 'calif', 'united states', 'usa'],
            '美国加州': ['california', 'ca', 'calif', 'united states', 'usa'],
            '北京': ['beijing'],
            '上海': ['shanghai'],
            '台北': ['taipei', 'taiwan'],
            '台湾': ['taiwan', 'taipei']
        }
        
        for keyword, variants in location_keywords.items():
            if keyword in target_region:
                for location in extracted_locations:
                    location_lower = location.lower()
                    for variant in variants:
                        if variant in location_lower:
                            return True, location
        
        return False, ""
    
    def _generate_optimized_keywords(
        self, 
        industry: Optional[str], 
        region: Optional[str], 
        gl: str, 
        search_mode: str
    ) -> Dict[str, Any]:
        """
        使用LLM生成优化的搜索关键词
        
        Args:
            industry: 原始行业关键词
            region: 地区信息
            gl: 国家代码
            search_mode: 搜索模式
        
        Returns:
            Dict包含优化后的关键词和搜索参数
        """
        result = {
            "optimized_keywords": [],
            "serper_params": {},
            "search_strategy": "",
            "success": False,
            "method": "fallback"
        }
        
        if not industry:
            result["optimized_keywords"] = []
            return result
        
        # 尝试使用LLM生成关键词
        if self.llm_available and self.llm_keyword_generator:
            try:
                print(f"🤖 使用LLM生成关键词: {industry} -> {gl.upper()}")
                
                # 调用LLM关键词生成器
                llm_result = self.llm_keyword_generator.generate_search_keywords(
                    industry=industry,
                    target_country=gl,
                    search_type=search_mode
                )
                
                if llm_result.get("success"):
                    primary_keywords = llm_result.get("primary_keywords", [])
                    alternative_keywords = llm_result.get("alternative_keywords", [])
                    
                    # 合并主要关键词和备选关键词
                    all_keywords = primary_keywords + alternative_keywords
                    result["optimized_keywords"] = list(set(all_keywords))[:5]  # 去重并限制数量
                    
                    # 获取优化的Serper参数
                    result["serper_params"] = llm_result.get("serper_params", {})
                    result["search_strategy"] = llm_result.get("search_strategy", "")
                    result["success"] = True
                    result["method"] = "llm"
                    
                    print(f"✅ LLM关键词生成成功: {result['optimized_keywords']}")
                    return result
                else:
                    print("⚠️ LLM关键词生成失败，使用回退方案")
                    
            except Exception as e:
                print(f"❌ LLM关键词生成异常: {str(e)}")
        
        # LLM不可用或失败，使用原始关键词
        result["optimized_keywords"] = [industry] if industry else []
        result["success"] = True
        result["method"] = "original"
        result["search_strategy"] = f"使用原始关键词在{gl.upper()}进行搜索"
        
        return result
    
    def _search_linkedin_companies(self, industry, region, keywords, gl, num_results):
        """Search for companies on LinkedIn with intelligent keyword optimization"""
        
        # 使用LLM生成优化的关键词
        keyword_result = self._generate_optimized_keywords(
            industry=industry,
            region=region, 
            gl=gl,
            search_mode="linkedin"
        )
        
        # 构建搜索查询
        query_parts = ["site:linkedin.com/company"]
        
        # 使用优化后的关键词
        optimized_keywords = keyword_result.get("optimized_keywords", [])
        if optimized_keywords:
            # 使用第一个主要关键词作为核心搜索词
            primary_keyword = optimized_keywords[0]
            query_parts.append(f'"{primary_keyword}"')
            print(f"🎯 使用主要关键词: {primary_keyword}")
        elif industry:
            # 回退到原始行业关键词
            query_parts.append(f'"{industry}"')
            print(f"🔄 回退到原始关键词: {industry}")
        
        # 地区信息通过gl参数处理，避免混合语言查询
        # 不再添加原始region到查询字符串，防止中英文混合导致搜索结果混乱
        
        # 添加额外关键词
        if keywords:
            query_parts.extend(keywords)
        
        query = " ".join(query_parts)
        print(f"🔍 LinkedIn搜索查询: {query}")
        
        # Serper API limitation: num must be <= 20 for certain queries
        # to avoid "Query not allowed" error
        safe_num_results = min(num_results, 20)
        
        # 构建基础payload
        payload_dict = {
            "q": query,
            "gl": gl,
            "num": safe_num_results
        }
        
        # 添加LLM建议的优化参数
        serper_params = keyword_result.get("serper_params", {})
        if serper_params:
            print(f"📡 使用优化的Serper参数: {serper_params}")
            for key, value in serper_params.items():
                if key not in payload_dict:  # 避免覆盖已有参数
                    payload_dict[key] = value
        
        payload = json.dumps(payload_dict)
        
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.post(self.base_url, data=payload)
                response.raise_for_status()
                results = response.json()
                
                # Process results with location filtering
                companies = self._extract_linkedin_companies(results, query, region)
                return companies
                
            except requests.exceptions.RequestException as e:
                if attempt < self.MAX_RETRIES - 1:
                    backoff_time = (2 ** attempt) * random.uniform(1, 3)
                    time.sleep(backoff_time)
                else:
                    raise Exception(f"Failed after {self.MAX_RETRIES} retries: {str(e)}")
    
    def _search_general_companies(self, industry, region, keywords, custom_query, gl, num_results):
        """Search for companies on Google with intelligent keyword optimization"""
        
        if custom_query:
            # 对于自定义查询，仍然使用原始逻辑
            custom_query = custom_query[:500]  # Limit length
            query = custom_query
            keyword_result = {"serper_params": {}}  # 空的优化参数
        else:
            # 使用LLM生成优化的关键词
            keyword_result = self._generate_optimized_keywords(
                industry=industry,
                region=region,
                gl=gl,
                search_mode="general"
            )
            
            # 构建搜索查询
            query_parts = ["company", "business"]
            
            # 使用优化后的关键词
            optimized_keywords = keyword_result.get("optimized_keywords", [])
            if optimized_keywords:
                # 使用第一个主要关键词
                primary_keyword = optimized_keywords[0]
                query_parts.append(f'"{primary_keyword}"')
                print(f"🎯 通用搜索使用主要关键词: {primary_keyword}")
            elif industry:
                # 回退到原始行业关键词
                query_parts.append(f'"{industry}"')
                print(f"🔄 通用搜索回退到原始关键词: {industry}")
            
            # 地区信息通过gl参数和LLM本地化关键词处理
            # 移除直接添加region到查询的逻辑，防止中英文混合查询
            
            if keywords:
                query_parts.extend(keywords)
                
            query = " ".join(query_parts)
            print(f"🔍 通用搜索查询: {query}")
        
        # Serper API limitation: num must be <= 20 for certain queries
        # to avoid "Query not allowed" error
        safe_num_results = min(num_results, 20)
        
        # 构建基础payload
        payload_dict = {
            "q": query,
            "gl": gl,
            "num": safe_num_results
        }
        
        # 添加LLM建议的优化参数
        serper_params = keyword_result.get("serper_params", {})
        if serper_params:
            print(f"📡 通用搜索使用优化的Serper参数: {serper_params}")
            for key, value in serper_params.items():
                if key not in payload_dict:  # 避免覆盖已有参数
                    payload_dict[key] = value
        
        payload = json.dumps(payload_dict)
        
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.post(self.base_url, data=payload)
                response.raise_for_status()
                results = response.json()
                
                # Extract company information with location filtering
                companies = self._extract_general_companies(results, query, custom_query, region)
                return companies
                
            except requests.exceptions.RequestException as e:
                if attempt < self.MAX_RETRIES - 1:
                    backoff_time = (2 ** attempt) * random.uniform(1, 3)
                    time.sleep(backoff_time)
                else:
                    raise Exception(f"Failed after {self.MAX_RETRIES} retries: {str(e)}")
    
    def _extract_linkedin_companies(self, search_results, query, target_region=None):
        """Extract company information from LinkedIn search results with location filtering"""
        companies = []
        filtered_out = []  # 记录被过滤掉的公司
        
        if not search_results or 'organic' not in search_results:
            return companies
        
        for result in search_results.get('organic', []):
            link = result.get('link', '')
            
            if 'linkedin.com/company/' in link:
                # Extract company name from URL and decode it
                company_name_match = re.search(r'linkedin\.com/company/([^/]+)', link)
                company_name = ""
                if company_name_match:
                    import urllib.parse
                    encoded_name = company_name_match.group(1)
                    # URL decode the company name
                    try:
                        company_name = urllib.parse.unquote(encoded_name).replace('-', ' ').title()
                    except Exception:
                        company_name = encoded_name.replace('-', ' ').title()
                
                # If still no name, extract from title
                if not company_name and result.get('title'):
                    company_name = result.get('title').split('|')[0].split('-')[0].strip()
                
                title = result.get('title', '')
                description = result.get('snippet', '')
                
                # 从搜索结果中提取地理位置信息
                text_to_analyze = f"{title} {description}"
                extracted_locations = self._extract_location_from_text(text_to_analyze)
                
                # 地理位置匹配检查
                location_match = True
                matched_location = ""
                if target_region:
                    location_match, matched_location = self._match_location_with_region(extracted_locations, target_region)
                    # 调试信息
                    if not location_match:
                        print(f"❌ 过滤公司: {company_name}")
                        print(f"   目标地区: {target_region}")
                        print(f"   提取的位置: {extracted_locations}")
                        print(f"   文本内容: {text_to_analyze[:100]}...")
                        print()
                    else:
                        print(f"✅ 保留公司: {company_name}")
                        print(f"   匹配位置: {matched_location}")
                        print(f"   提取的位置: {extracted_locations}")
                        print()
                
                company_info = {
                    'name': company_name,
                    'query': query,
                    'url': link,
                    'title': title,
                    'description': description,
                    'domain': '',
                    'linkedin': link,
                    'type': 'linkedin_search',
                    'extracted_locations': extracted_locations,
                    'location_match': location_match,
                    'matched_location': matched_location
                }
                
                if location_match or not target_region:
                    companies.append(company_info)
                else:
                    filtered_out.append(company_info)
        
        # 输出过滤统计信息
        if target_region and filtered_out:
            print(f"地理位置过滤: 保留 {len(companies)} 家公司，过滤掉 {len(filtered_out)} 家不符合地区要求的公司")
        
        return companies
    
    def _extract_general_companies(self, search_results, query, custom_query=None, target_region=None):
        """Extract company information from general search results with location filtering"""
        companies = []
        filtered_out = []  # 记录被过滤掉的公司
        
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
                
                # 从搜索结果中提取地理位置信息
                text_to_analyze = f"{title} {description}"
                extracted_locations = self._extract_location_from_text(text_to_analyze)
                
                # 地理位置匹配检查
                location_match = True
                matched_location = ""
                if target_region:
                    location_match, matched_location = self._match_location_with_region(extracted_locations, target_region)
                    # 调试信息
                    if not location_match:
                        print(f"❌ 过滤公司: {company_name}")
                        print(f"   目标地区: {target_region}")
                        print(f"   提取的位置: {extracted_locations}")
                        print(f"   文本内容: {text_to_analyze[:100]}...")
                        print()
                    else:
                        print(f"✅ 保留公司: {company_name}")
                        print(f"   匹配位置: {matched_location}")
                        print(f"   提取的位置: {extracted_locations}")
                        print()
                
                company_info = {
                    'name': company_name,
                    'query': query,
                    'url': link,
                    'title': title,
                    'description': description,
                    'domain': self._extract_domain(link),
                    'type': "general_search",
                    'extracted_locations': extracted_locations,
                    'location_match': location_match,
                    'matched_location': matched_location
                }
                
                if custom_query:
                    company_info['custom_query'] = custom_query
                
                if 'linkedin.com/company' in link:
                    company_info['linkedin'] = link
                else:
                    company_info['linkedin'] = ""
                
                if location_match or not target_region:
                    companies.append(company_info)
                else:
                    filtered_out.append(company_info)
        
        # 输出过滤统计信息
        if target_region and filtered_out:
            print(f"地理位置过滤: 保留 {len(companies)} 家公司，过滤掉 {len(filtered_out)} 家不符合地区要求的公司")
        
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
    
    def __del__(self):
        """Close session when object is destroyed"""
        if hasattr(self, 'session'):
            self.session.close()