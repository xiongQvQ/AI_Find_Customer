"""
公司搜索节点
集成现有serper_company_search功能，支持LangGraph工作流
"""

import os
import sys
import json
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from serper_company_search import SerperCompanySearch
from ..state import SearchState, CompanyInfo, add_error_to_state, add_warning_to_state
from ..utils.performance_manager import get_performance_manager, performance_cache, performance_monitor

@dataclass 
class CompanySearchConfig:
    """公司搜索配置"""
    max_results: int = 20  # 降低到20个结果，避免前端显示问题
    gl: str = "us"
    search_type: str = "general"  # "general" or "linkedin" 
    timeout: int = 30
    max_retries: int = 3
    enable_cache: bool = True
    cache_ttl: int = 3600  # 缓存1小时

class CompanySearchNode:
    """
    公司搜索节点
    
    负责根据搜索参数执行公司搜索：
    - 支持通用搜索和LinkedIn搜索
    - 集成现有SerperCompanySearch功能
    - 提供结果标准化和缓存机制
    - 支持并行搜索和错误恢复
    """
    
    def __init__(self, config: Optional[CompanySearchConfig] = None):
        """初始化公司搜索节点"""
        self.config = config or CompanySearchConfig()
        self.logger = logging.getLogger(__name__)
        self.search_cache = {}  # 简单内存缓存
        
        # 验证API密钥
        self.api_key = os.getenv("SERPER_API_KEY")
        if not self.api_key:
            self.logger.error("SERPER_API_KEY not found in environment variables")
            
    @performance_monitor("company_search")
    def execute(self, state: SearchState) -> SearchState:
        """
        执行公司搜索节点
        
        Args:
            state: 当前搜索状态
            
        Returns:
            更新后的状态
        """
        try:
            self.logger.info("开始执行公司搜索")
            
            # 更新当前节点
            state["current_node"] = "company_search"
            state["workflow_path"].append("company_search_started")
            
            # 检查API密钥
            if not self.api_key:
                return add_error_to_state(
                    state,
                    "missing_api_key",
                    "SERPER_API_KEY not configured",
                    "company_search"
                )
            
            # 解析搜索参数
            search_params = state["search_params"]
            search_config = self._prepare_search_config(search_params, state)
            
            # 执行搜索
            search_results = self._perform_company_search(search_config)
            
            if search_results is None:
                return add_error_to_state(
                    state,
                    "search_failed",
                    "公司搜索执行失败",
                    "company_search"
                )
            
            # 标准化搜索结果
            standardized_companies = self._standardize_search_results(search_results, state)
            
            # 更新状态
            state["search_results"]["companies"] = standardized_companies
            state["search_results"]["total_companies_found"] = len(standardized_companies)
            state["company_search_completed"] = True
            state["workflow_path"].append("company_search_completed")
            
            # 记录API调用
            state["api_calls_count"] += 1
            
            self.logger.info(f"公司搜索完成，找到 {len(standardized_companies)} 家公司")
            
            # 如果结果数量较少，添加警告
            if len(standardized_companies) < 5:
                state = add_warning_to_state(
                    state,
                    "low_results_count",
                    f"公司搜索结果数量较少: {len(standardized_companies)}",
                    "company_search"
                )
            
            return state
            
        except Exception as e:
            self.logger.error(f"公司搜索过程中发生错误: {e}")
            return add_error_to_state(
                state,
                "company_search_exception",
                f"公司搜索执行异常: {str(e)}",
                "company_search"
            )
    
    def _prepare_search_config(self, search_params, state: SearchState) -> Dict[str, Any]:
        """准备搜索配置"""
        
        # 从意图识别结果和搜索参数构建配置
        config = {
            "industry": search_params.industry or "",
            "region": search_params.region or "",
            "gl": search_params.gl or self.config.gl,
            "num_results": min(search_params.max_results, self.config.max_results),
            "search_type": search_params.search_type,
            "custom_query": None
        }
        
        # 如果使用自定义查询
        if search_params.use_custom_query and search_params.query:
            config["custom_query"] = search_params.query
        else:
            # 从用户查询中提取关键词
            user_query = state["user_query"]
            extracted_keywords = self._extract_keywords_from_query(user_query)
            if extracted_keywords:
                config["additional_keywords"] = extracted_keywords
        
        return config
    
    def _extract_keywords_from_query(self, query: str) -> List[str]:
        """从用户查询中提取搜索关键词"""
        keywords = []
        
        # 移除常见的停用词和搜索词
        stop_words = {"找", "搜索", "查找", "寻找", "的", "公司", "企业", "厂商", "制造商"}
        
        # 简单的关键词提取
        words = query.replace("，", " ").replace(",", " ").split()
        for word in words:
            word = word.strip()
            if len(word) > 1 and word not in stop_words:
                keywords.append(word)
        
        return keywords[:5]  # 限制关键词数量
    
    @performance_cache(ttl=1800)  # 缓存30分钟
    def _perform_company_search(self, config: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """执行公司搜索"""
        
        try:
            # 创建搜索实例
            searcher = SerperCompanySearch(
                output_file=f"langgraph_search_{int(time.time())}.csv",
                gl=config["gl"],
                num_results=config["num_results"]
            )
            
            # 根据搜索类型执行搜索
            if config["search_type"] == "linkedin":
                results = searcher.search_linkedin_companies(
                    industry=config.get("industry"),
                    region=config.get("region"),
                    additional_keywords=config.get("additional_keywords")
                )
            else:
                results = searcher.search_general_companies(
                    industry=config.get("industry"),
                    region=config.get("region"), 
                    additional_keywords=config.get("additional_keywords"),
                    custom_query=config.get("custom_query")
                )
            
            return results
            
        except Exception as e:
            self.logger.error(f"搜索执行失败: {e}")
            return None
    
    
    def _standardize_search_results(self, raw_results: List[Dict[str, Any]], 
                                  state: SearchState) -> List[Dict[str, Any]]:
        """将搜索结果标准化为字典格式（兼容LangGraph序列化）"""
        standardized_companies = []
        
        for raw_company in raw_results:
            try:
                # 提取域名
                domain = self._extract_domain_from_result(raw_company)
                
                # 创建标准化的公司信息字典
                company_dict = {
                    "name": raw_company.get("name", "").strip(),
                    "domain": domain,
                    "industry": raw_company.get("industry", ""),
                    "size": raw_company.get("size", ""),
                    "location": raw_company.get("location", raw_company.get("region", "")),
                    "description": raw_company.get("description", raw_company.get("snippet", "")),
                    "linkedin_url": raw_company.get("linkedin", ""),
                    "website_url": raw_company.get("url", ""),
                    # AI评估相关字段初始化
                    "ai_score": None,
                    "ai_reason": None,
                    "is_qualified": None
                }
                
                # 只添加有效的公司信息
                name = company_dict.get("name")
                if name and (company_dict.get("domain") or company_dict.get("linkedin_url") or company_dict.get("website_url")):
                    standardized_companies.append(company_dict)
                
            except Exception as e:
                self.logger.warning(f"标准化公司信息失败: {e}")
                continue
        
        return standardized_companies
    
    def _extract_domain_from_result(self, raw_company: Dict[str, Any]) -> str:
        """从搜索结果中提取域名"""
        
        # 首先检查是否直接有domain字段
        if raw_company.get("domain"):
            return raw_company["domain"]
        
        # 从URL中提取域名
        url = raw_company.get("url", "")
        if url:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                return parsed.netloc.replace("www.", "") if parsed.netloc else ""
            except:
                pass
        
        # 从LinkedIn URL中提取 (如果有的话)
        linkedin_url = raw_company.get("linkedin", "")
        if linkedin_url and "linkedin.com/company/" in linkedin_url:
            # LinkedIn公司页面不能直接提供公司域名
            return ""
        
        return ""
    
    def batch_search_companies(self, search_configs: List[Dict[str, Any]], 
                             max_workers: int = 3) -> List[List[CompanyInfo]]:
        """
        批量并行搜索多个公司查询
        
        Args:
            search_configs: 搜索配置列表
            max_workers: 最大并行工作线程数
            
        Returns:
            每个配置对应的公司搜索结果列表
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有搜索任务
            future_to_config = {
                executor.submit(self._perform_company_search, config): config 
                for config in search_configs
            }
            
            # 收集结果
            for future in as_completed(future_to_config):
                config = future_to_config[future]
                try:
                    search_result = future.result(timeout=self.config.timeout)
                    if search_result:
                        # 创建临时状态用于标准化
                        temp_state = {"user_query": "", "search_params": config}
                        standardized = self._standardize_search_results(search_result, temp_state)
                        results.append(standardized)
                    else:
                        results.append([])
                except Exception as e:
                    self.logger.error(f"批量搜索失败: {e}")
                    results.append([])
        
        return results
    
    def get_search_suggestions(self, failed_query: str) -> List[str]:
        """
        为失败的搜索提供建议
        
        Args:
            failed_query: 失败的查询
            
        Returns:
            搜索建议列表
        """
        suggestions = []
        
        # 基本建议
        suggestions.append("尝试使用更通用的行业关键词")
        suggestions.append("减少地区限制，扩大搜索范围")
        suggestions.append("使用英文关键词进行搜索")
        
        # 基于查询内容的具体建议
        if "科技" in failed_query or "技术" in failed_query:
            suggestions.append("尝试搜索 'technology company' 或 'tech startup'")
        elif "制造" in failed_query:
            suggestions.append("尝试搜索 'manufacturing company' 或 'factory'")
        elif "服务" in failed_query:
            suggestions.append("尝试搜索 'service company' 或 'consulting'")
        
        return suggestions

# 创建节点实例
company_search_node = CompanySearchNode()