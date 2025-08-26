"""
增强版网站识别工具
使用Serper搜索引擎API进行真实的官网验证和识别
"""
import os
import re
import json
import requests
from typing import Optional, Dict, List, Tuple
from urllib.parse import urlparse, urljoin
import time
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()


class EnhancedWebsiteValidator:
    """增强版官网验证和识别工具类 - 使用搜索引擎API"""
    
    def __init__(self):
        self.cache = {}  # 内存缓存
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        
    def get_official_website(self, company_name: str) -> Dict[str, any]:
        """
        获取公司官网地址 - 使用搜索引擎API
        Args:
            company_name: 公司名称
        Returns:
            dict: {'website': url, 'confidence': float, 'method': str, 'search_results': list}
        """
        # 检查缓存
        cache_key = f"website_{company_name.lower()}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # 方法1: 使用Serper搜索引擎API
            website, search_results = self._serper_search_method(company_name)
            if website:
                result = {
                    'website': website,
                    'confidence': 0.90,
                    'method': 'serper_search',
                    'search_results': search_results
                }
                self.cache[cache_key] = result
                return result
            
            # 方法2: 使用官网搜索查询
            website, search_results = self._official_search_method(company_name)
            if website:
                result = {
                    'website': website,
                    'confidence': 0.85,
                    'method': 'official_search',
                    'search_results': search_results
                }
                self.cache[cache_key] = result
                return result
            
            # 方法3: 域名猜测（备用方法）
            website = self._domain_guess_method(company_name)
            if website:
                result = {
                    'website': website,
                    'confidence': 0.60,
                    'method': 'domain_guess',
                    'search_results': []
                }
                self.cache[cache_key] = result
                return result
            
            return {
                'website': None,
                'confidence': 0.0,
                'method': 'not_found',
                'search_results': []
            }
            
        except Exception as e:
            print(f"官网识别错误: {e}")
            return {
                'website': None,
                'confidence': 0.0,
                'method': 'error',
                'error': str(e),
                'search_results': []
            }
    
    def _serper_search_method(self, company_name: str) -> Tuple[Optional[str], List[Dict]]:
        """使用Serper API搜索公司官网"""
        if not self.serper_api_key:
            return None, []
        
        try:
            # 构建搜索查询
            query = f'"{company_name}" 官网 site:*.com OR site:*.cn'
            
            # 调用Serper API
            url = "https://google.serper.dev/search"
            payload = {
                "q": query,
                "num": 10,
                "gl": "cn",  # 地理位置
                "hl": "zh"   # 语言
            }
            headers = {
                "X-API-KEY": self.serper_api_key,
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                organic_results = data.get("organic", [])
                
                # 分析搜索结果，寻找官网
                best_website = self._analyze_search_results(organic_results, company_name)
                
                return best_website, organic_results[:5]  # 返回前5个结果用于缓存
            
        except Exception as e:
            print(f"Serper搜索失败: {e}")
        
        return None, []
    
    def _official_search_method(self, company_name: str) -> Tuple[Optional[str], List[Dict]]:
        """使用"官方网站"关键词搜索"""
        if not self.serper_api_key:
            return None, []
        
        try:
            # 构建官方搜索查询
            query = f'"{company_name}" 官方网站 OR official website'
            
            url = "https://google.serper.dev/search"
            payload = {
                "q": query,
                "num": 5,
                "gl": "cn",
                "hl": "zh"
            }
            headers = {
                "X-API-KEY": self.serper_api_key,
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                organic_results = data.get("organic", [])
                
                # 分析结果
                best_website = self._analyze_search_results(organic_results, company_name)
                
                return best_website, organic_results
            
        except Exception as e:
            print(f"官方搜索失败: {e}")
        
        return None, []
    
    def _analyze_search_results(self, results: List[Dict], company_name: str) -> Optional[str]:
        """分析搜索结果，找出最可能的官网"""
        scored_results = []
        
        for result in results:
            url = result.get("link", "")
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            
            if not url:
                continue
            
            score = self._score_search_result(url, title, snippet, company_name)
            if score > 0.3:  # 最低阈值
                scored_results.append((url, score, result))
        
        # 按得分排序
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        if scored_results:
            best_url = scored_results[0][0]
            # 进一步验证最佳结果
            if self._verify_website_content(best_url, company_name):
                return best_url
        
        return None
    
    def _score_search_result(self, url: str, title: str, snippet: str, company_name: str) -> float:
        """为搜索结果打分"""
        score = 0.0
        
        # 解析URL
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # 清理公司名称
        clean_company = self._clean_company_name(company_name)
        
        # 1. 域名相关性 (40%)
        if clean_company in domain.replace("-", "").replace(".", ""):
            score += 0.4
        elif any(word in domain for word in clean_company.split() if len(word) > 2):
            score += 0.2
        
        # 2. 排除不相关域名 (负分)
        excluded_domains = [
            'linkedin.com', 'facebook.com', 'twitter.com', 'weibo.com',
            'zhipin.com', 'lagou.com', 'zhaopin.com', '51job.com',
            'baidu.com', 'wikipedia.org', 'qichacha.com', 'tianyancha.com',
            'sohu.com', 'sina.com', 'qq.com', 'douban.com', 'zhihu.com'
        ]
        
        for excluded in excluded_domains:
            if excluded in domain:
                score -= 0.8
                break
        
        # 3. 标题相关性 (30%)
        if company_name in title:
            score += 0.3
        elif clean_company in title.lower():
            score += 0.2
        
        # 4. 官网关键词 (20%)
        official_keywords = ['官网', '官方', '首页', 'official', 'homepage', 'home']
        title_snippet = (title + " " + snippet).lower()
        for keyword in official_keywords:
            if keyword in title_snippet:
                score += 0.1
                break
        
        # 5. 域名特征 (10%)
        if parsed.netloc.startswith("www."):
            score += 0.05
        if any(ext in domain for ext in ['.com', '.cn', '.com.cn']):
            score += 0.05
        
        return min(score, 1.0)  # 最高1.0分
    
    def _verify_website_content(self, url: str, company_name: str) -> bool:
        """验证网站内容是否与公司匹配"""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return False
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 检查title和meta信息
            title = soup.find('title')
            if title and company_name in title.get_text():
                return True
            
            # 检查页面主要内容
            page_text = soup.get_text()[:2000]  # 只检查前2000字符
            
            # 简单的公司名称匹配
            if company_name in page_text:
                return True
            
            return False
            
        except Exception:
            return False
    
    def _domain_guess_method(self, company_name: str) -> Optional[str]:
        """通过域名猜测方法查找官网（备用方法）"""
        clean_name = self._clean_company_name(company_name)
        possible_domains = self._generate_domain_candidates(clean_name)
        
        for domain in possible_domains:
            if self._test_domain_accessibility(domain):
                return f"https://www.{domain}"
        
        return None
    
    def _clean_company_name(self, name: str) -> str:
        """清理公司名称，提取核心部分"""
        suffixes = [
            '有限公司', '股份有限公司', '科技有限公司', '集团有限公司', '集团', '公司',
            'Limited', 'Ltd', 'Inc', 'Corp', 'Corporation', 'LLC', 'Co.', 'Company'
        ]
        
        clean_name = name.strip()
        
        for suffix in suffixes:
            if clean_name.endswith(suffix):
                clean_name = clean_name[:-len(suffix)].strip()
        
        # 移除特殊字符，只保留字母数字和中文
        clean_name = re.sub(r'[^\w\u4e00-\u9fff\s]', '', clean_name)
        clean_name = re.sub(r'\s+', '', clean_name)
        
        return clean_name.lower()
    
    def _generate_domain_candidates(self, clean_name: str) -> List[str]:
        """生成可能的域名候选"""
        candidates = []
        extensions = ['.com', '.cn', '.com.cn', '.net', '.org']
        
        for ext in extensions:
            candidates.append(f"{clean_name}{ext}")
            
            # 添加常见变体
            if len(clean_name) > 3:
                # 缩写形式
                candidates.append(f"{clean_name[:3]}{ext}")
                # 添加数字变体
                candidates.append(f"{clean_name}123{ext}")
                candidates.append(f"{clean_name}tech{ext}")
        
        return candidates[:8]  # 限制候选数量
    
    def _test_domain_accessibility(self, domain: str) -> bool:
        """测试域名是否可访问"""
        for protocol in ["https://www.", "http://www.", "https://", "http://"]:
            try:
                url = f"{protocol}{domain}"
                response = self.session.head(url, timeout=5)
                if response.status_code == 200:
                    return True
            except:
                continue
        return False
    
    def is_official_website(self, url: str, company_name: str) -> Dict[str, any]:
        """
        判断URL是否为公司官网 - 增强版
        Args:
            url: 网站URL
            company_name: 公司名称
        Returns:
            dict: {'is_official': bool, 'confidence': float, 'reasons': list, 'analysis': dict}
        """
        try:
            reasons = []
            confidence = 0.0
            analysis = {}
            
            # 解析URL
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            analysis['domain'] = domain
            
            # 检查1: 域名相关性分析
            clean_company = self._clean_company_name(company_name)
            domain_score = self._analyze_domain_relevance(domain, clean_company)
            confidence += domain_score * 0.4
            analysis['domain_score'] = domain_score
            
            if domain_score > 0.5:
                reasons.append(f"域名高度相关 (得分: {domain_score:.2f})")
            elif domain_score > 0.2:
                reasons.append(f"域名部分相关 (得分: {domain_score:.2f})")
            
            # 检查2: 排除社交媒体和平台网站
            excluded_domains = [
                'linkedin.com', 'facebook.com', 'twitter.com', 'instagram.com',
                'weibo.com', 'zhipin.com', 'lagou.com', 'zhaopin.com', '51job.com',
                'baidu.com', 'wikipedia.org', 'qichacha.com', 'tianyancha.com',
                'sohu.com', 'sina.com', 'qq.com', 'douban.com', 'zhihu.com'
            ]
            
            for excluded in excluded_domains:
                if excluded in domain:
                    confidence = 0.1
                    reasons.append(f"属于平台网站: {excluded}")
                    analysis['excluded'] = excluded
                    return {
                        'is_official': False,
                        'confidence': confidence,
                        'reasons': reasons,
                        'analysis': analysis
                    }
            
            # 检查3: 页面内容深度分析
            try:
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    content_analysis = self._analyze_page_content(response.content, company_name)
                    confidence += content_analysis['score'] * 0.6
                    reasons.extend(content_analysis['reasons'])
                    analysis['content'] = content_analysis
                    
            except Exception as e:
                reasons.append(f"页面分析失败: {str(e)}")
                analysis['content_error'] = str(e)
            
            # 检查4: 使用搜索引擎验证
            if self.serper_api_key and confidence > 0.4:
                search_verification = self._verify_with_search_engine(url, company_name)
                if search_verification['verified']:
                    confidence += 0.2
                    reasons.append("搜索引擎验证通过")
                    analysis['search_verified'] = True
            
            # 最终判断
            is_official = confidence >= 0.6
            
            return {
                'is_official': is_official,
                'confidence': round(confidence, 2),
                'reasons': reasons,
                'analysis': analysis
            }
            
        except Exception as e:
            return {
                'is_official': False,
                'confidence': 0.0,
                'reasons': [f"分析错误: {str(e)}"],
                'analysis': {'error': str(e)}
            }
    
    def _analyze_domain_relevance(self, domain: str, clean_company: str) -> float:
        """分析域名与公司名称的相关性"""
        score = 0.0
        domain_clean = domain.replace("www.", "").replace("-", "").replace(".", "")
        
        # 完全匹配
        if clean_company == domain_clean.split('.')[0]:
            score = 1.0
        # 包含关系
        elif clean_company in domain_clean:
            score = 0.8
        # 部分匹配（单词级别）
        else:
            words = clean_company.split()
            matched_words = sum(1 for word in words if len(word) > 2 and word in domain_clean)
            if words:
                score = matched_words / len(words) * 0.6
        
        return score
    
    def _analyze_page_content(self, content: bytes, company_name: str) -> Dict:
        """深度分析页面内容"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            reasons = []
            score = 0.0
            
            # 检查title标签
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                if company_name in title_text:
                    score += 0.4
                    reasons.append("页面标题包含公司名称")
                elif any(word in title_text for word in company_name.split() if len(word) > 2):
                    score += 0.2
                    reasons.append("页面标题包含公司关键词")
            
            # 检查meta描述
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                desc_content = meta_desc.get('content', '')
                if company_name in desc_content:
                    score += 0.2
                    reasons.append("Meta描述包含公司名称")
            
            # 检查H1标签
            h1_tags = soup.find_all('h1')
            for h1 in h1_tags[:3]:  # 只检查前3个H1
                if company_name in h1.get_text():
                    score += 0.1
                    reasons.append("H1标题包含公司名称")
                    break
            
            # 检查官网特征关键词
            official_keywords = ['官网', '官方网站', 'official', 'homepage', '首页', '企业官网']
            page_text = soup.get_text()[:3000].lower()  # 前3000字符
            
            for keyword in official_keywords:
                if keyword in page_text:
                    score += 0.1
                    reasons.append(f"页面包含官网关键词: {keyword}")
                    break
            
            # 检查联系方式和版权信息
            contact_keywords = ['联系我们', '关于我们', 'contact', 'about', '版权所有', 'copyright']
            for keyword in contact_keywords:
                if keyword in page_text:
                    score += 0.05
                    reasons.append("页面包含企业网站特征")
                    break
            
            return {
                'score': min(score, 1.0),
                'reasons': reasons,
                'title': title.get_text() if title else None
            }
            
        except Exception as e:
            return {
                'score': 0.0,
                'reasons': [f"内容分析失败: {str(e)}"],
                'error': str(e)
            }
    
    def _verify_with_search_engine(self, url: str, company_name: str) -> Dict:
        """使用搜索引擎验证网站是否为官网"""
        try:
            # 搜索 "公司名称 + 官网" 看是否包含目标URL
            query = f'"{company_name}" 官网'
            
            search_url = "https://google.serper.dev/search"
            payload = {
                "q": query,
                "num": 10,
                "gl": "cn"
            }
            headers = {
                "X-API-KEY": self.serper_api_key,
                "Content-Type": "application/json"
            }
            
            response = requests.post(search_url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                organic_results = data.get("organic", [])
                
                # 检查前5个结果中是否包含目标URL的域名
                target_domain = urlparse(url).netloc.lower().replace("www.", "")
                
                for i, result in enumerate(organic_results[:5]):
                    result_url = result.get("link", "")
                    result_domain = urlparse(result_url).netloc.lower().replace("www.", "")
                    
                    if target_domain == result_domain:
                        return {
                            'verified': True,
                            'rank': i + 1,
                            'result': result
                        }
            
            return {'verified': False}
            
        except Exception:
            return {'verified': False}
    
    def batch_verify_websites(self, companies_with_urls: List[Dict]) -> List[Dict]:
        """
        批量验证网站是否为官网
        Args:
            companies_with_urls: 包含company_name和website_url的字典列表
        Returns:
            添加了验证结果的字典列表
        """
        results = []
        
        for company_data in companies_with_urls:
            company_name = company_data.get('name', '')
            website_url = company_data.get('website_url', '')
            
            if company_name and website_url:
                verification = self.is_official_website(website_url, company_name)
                
                # 添加验证结果到原始数据
                enhanced_data = company_data.copy()
                enhanced_data.update({
                    'is_official_website': verification['is_official'],
                    'website_confidence': verification['confidence'],
                    'verification_reasons': verification['reasons'],
                    'detailed_analysis': verification['analysis']
                })
                
                results.append(enhanced_data)
            else:
                results.append(company_data)
        
        return results


# 全局实例
enhanced_website_validator = EnhancedWebsiteValidator()