"""
Website utilities for AI Customer Finder
官网识别和判断工具函数
"""
import re
import requests
from typing import Optional, Dict, List
from urllib.parse import urlparse, urljoin
import time
from bs4 import BeautifulSoup

class WebsiteValidator:
    """官网验证和识别工具类"""
    
    def __init__(self):
        self.cache = {}  # 简单的内存缓存
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_official_website(self, company_name: str) -> Dict[str, any]:
        """
        获取公司官网地址
        Args:
            company_name: 公司名称
        Returns:
            dict: {'website': url, 'confidence': float, 'method': str}
        """
        # 检查缓存
        cache_key = f"website_{company_name.lower()}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # 方法1: 使用搜索引擎API（这里模拟）
            website = self._search_engine_method(company_name)
            if website:
                result = {
                    'website': website,
                    'confidence': 0.85,
                    'method': 'search_engine'
                }
                self.cache[cache_key] = result
                return result
            
            # 方法2: 域名猜测
            website = self._domain_guess_method(company_name)
            if website:
                result = {
                    'website': website,
                    'confidence': 0.60,
                    'method': 'domain_guess'
                }
                self.cache[cache_key] = result
                return result
            
            return {
                'website': None,
                'confidence': 0.0,
                'method': 'not_found'
            }
            
        except Exception as e:
            print(f"官网识别错误: {e}")
            return {
                'website': None,
                'confidence': 0.0,
                'method': 'error',
                'error': str(e)
            }
    
    def _search_engine_method(self, company_name: str) -> Optional[str]:
        """使用搜索引擎方法查找官网"""
        # TODO: 集成实际的搜索引擎API（Google Custom Search, Bing等）
        # 这里使用简化的模拟逻辑
        
        # 常见的公司-域名映射（可以扩展）
        domain_mappings = {
            '腾讯': 'tencent.com',
            '阿里巴巴': 'alibaba.com',
            '百度': 'baidu.com',
            '华为': 'huawei.com',
            '小米': 'mi.com',
            '字节跳动': 'bytedance.com',
            '美团': 'meituan.com',
            '滴滴': 'didiglobal.com',
            '京东': 'jd.com',
            '网易': 'netease.com'
        }
        
        for keyword, domain in domain_mappings.items():
            if keyword in company_name:
                return f"https://www.{domain}"
        
        return None
    
    def _domain_guess_method(self, company_name: str) -> Optional[str]:
        """通过域名猜测方法查找官网"""
        # 清理公司名称
        clean_name = self._clean_company_name(company_name)
        
        # 生成可能的域名
        possible_domains = self._generate_domain_candidates(clean_name)
        
        # 测试域名是否可访问
        for domain in possible_domains:
            if self._test_domain_accessibility(domain):
                return f"https://www.{domain}"
        
        return None
    
    def _clean_company_name(self, name: str) -> str:
        """清理公司名称，提取核心部分"""
        # 移除常见的公司后缀
        suffixes = ['有限公司', '股份有限公司', '科技有限公司', '集团', '公司', 'Ltd', 'Inc', 'Corp', 'LLC', 'Co.']
        clean_name = name
        
        for suffix in suffixes:
            if clean_name.endswith(suffix):
                clean_name = clean_name[:-len(suffix)].strip()
        
        # 移除特殊字符，只保留字母数字
        clean_name = re.sub(r'[^\w\s]', '', clean_name)
        clean_name = re.sub(r'\s+', '', clean_name)
        
        return clean_name.lower()
    
    def _generate_domain_candidates(self, clean_name: str) -> List[str]:
        """生成可能的域名候选"""
        candidates = []
        
        # 添加不同的域名后缀
        extensions = ['.com', '.cn', '.com.cn', '.net', '.org']
        
        for ext in extensions:
            candidates.append(f"{clean_name}{ext}")
            
            # 添加常见的变体
            if len(clean_name) > 3:
                candidates.append(f"{clean_name[:3]}{ext}")  # 缩写形式
        
        return candidates[:5]  # 限制候选数量
    
    def _test_domain_accessibility(self, domain: str) -> bool:
        """测试域名是否可访问"""
        try:
            url = f"https://www.{domain}"
            response = self.session.head(url, timeout=5)
            return response.status_code == 200
        except:
            try:
                url = f"http://www.{domain}"
                response = self.session.head(url, timeout=5)
                return response.status_code == 200
            except:
                return False
    
    def is_official_website(self, url: str, company_name: str) -> Dict[str, any]:
        """
        判断URL是否为公司官网
        Args:
            url: 网站URL
            company_name: 公司名称
        Returns:
            dict: {'is_official': bool, 'confidence': float, 'reasons': list}
        """
        try:
            reasons = []
            confidence = 0.0
            
            # 解析URL
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # 检查1: 域名相关性
            clean_company = self._clean_company_name(company_name)
            if clean_company in domain:
                confidence += 0.4
                reasons.append("域名包含公司名称")
            
            # 检查2: 排除社交媒体和平台网站
            excluded_domains = [
                'linkedin.com', 'facebook.com', 'twitter.com', 'weibo.com',
                'zhipin.com', 'lagou.com', 'zhaopin.com', '51job.com',
                'baidu.com', 'wikipedia.org', 'qichacha.com', 'tianyancha.com'
            ]
            
            for excluded in excluded_domains:
                if excluded in domain:
                    confidence = 0.1
                    reasons.append(f"属于平台网站: {excluded}")
                    return {
                        'is_official': False,
                        'confidence': confidence,
                        'reasons': reasons
                    }
            
            # 检查3: 获取页面内容进行分析
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # 检查title标签
                    title = soup.find('title')
                    if title and company_name in title.get_text():
                        confidence += 0.3
                        reasons.append("页面标题包含公司名称")
                    
                    # 检查meta描述
                    meta_desc = soup.find('meta', attrs={'name': 'description'})
                    if meta_desc and company_name in meta_desc.get('content', ''):
                        confidence += 0.2
                        reasons.append("页面描述包含公司名称")
                    
                    # 检查是否有官网特征
                    official_keywords = ['官网', '官方网站', 'official', 'homepage', '首页']
                    page_text = soup.get_text().lower()
                    for keyword in official_keywords:
                        if keyword in page_text:
                            confidence += 0.1
                            reasons.append(f"页面包含官网关键词: {keyword}")
                            break
                            
            except Exception as e:
                reasons.append(f"页面分析失败: {str(e)}")
            
            # 最终判断
            is_official = confidence >= 0.6
            
            return {
                'is_official': is_official,
                'confidence': round(confidence, 2),
                'reasons': reasons
            }
            
        except Exception as e:
            return {
                'is_official': False,
                'confidence': 0.0,
                'reasons': [f"分析错误: {str(e)}"]
            }
    
    def filter_official_websites(self, results: List[Dict], company_name: str) -> List[Dict]:
        """
        过滤搜索结果，只保留官网
        Args:
            results: 搜索结果列表
            company_name: 公司名称
        Returns:
            过滤后的结果列表
        """
        filtered_results = []
        
        for result in results:
            url = result.get('website_url') or result.get('url')
            if not url:
                continue
            
            # 判断是否为官网
            website_check = self.is_official_website(url, company_name)
            
            if website_check['is_official']:
                # 添加官网验证信息
                result['is_official_website'] = True
                result['website_confidence'] = website_check['confidence']
                result['verification_reasons'] = website_check['reasons']
                filtered_results.append(result)
            else:
                # 标记为非官网但保留（用户可以选择是否显示）
                result['is_official_website'] = False
                result['website_confidence'] = website_check['confidence']
                result['verification_reasons'] = website_check['reasons']
                # filtered_results.append(result)  # 取消注释以保留非官网结果
        
        return filtered_results

# 全局实例
website_validator = WebsiteValidator()