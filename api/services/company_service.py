"""
公司搜索服务层
专门处理公司搜索相关的业务逻辑
"""
import os
import json
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models.requests import CompanySearchRequest
from ..models.responses import CompanyInfo, CompanySearchResponse

# 导入核心搜索模块
try:
    from core.company_search import CompanySearcher
    COMPANY_SEARCH_AVAILABLE = True
except ImportError as e:
    print(f"警告: 公司搜索模块不可用: {e}")
    COMPANY_SEARCH_AVAILABLE = False

# 导入公司分析服务
try:
    from .company_analyzer import get_company_analyzer
    COMPANY_ANALYZER_AVAILABLE = True
except ImportError as e:
    print(f"警告: 公司分析服务不可用: {e}")
    COMPANY_ANALYZER_AVAILABLE = False

logger = logging.getLogger(__name__)


class CompanySearchService:
    """公司搜索服务类"""
    
    def __init__(self):
        """初始化公司搜索服务"""
        self.searcher = None
        self.analyzer = None
        
        if COMPANY_SEARCH_AVAILABLE:
            try:
                self.searcher = CompanySearcher()
                logger.info("✅ 公司搜索器初始化成功")
            except Exception as e:
                logger.error(f"❌ 公司搜索器初始化失败: {e}")
                self.searcher = None
        
        if COMPANY_ANALYZER_AVAILABLE:
            try:
                self.analyzer = get_company_analyzer()
                logger.info("✅ 公司分析器初始化成功")
            except Exception as e:
                logger.error(f"❌ 公司分析器初始化失败: {e}")
                self.analyzer = None
    
    async def search_companies(self, request: CompanySearchRequest) -> CompanySearchResponse:
        """
        执行公司搜索
        
        Args:
            request: 公司搜索请求
            
        Returns:
            CompanySearchResponse: 搜索结果
        """
        search_id = f"company_search_{int(time.time())}"
        start_time = time.time()
        
        try:
            # 验证搜索器可用性
            if not self.searcher:
                raise ValueError("公司搜索服务不可用，请检查配置")
            
            # 验证请求参数
            self._validate_request(request)
            
            # 执行搜索
            logger.info(f"开始公司搜索: {search_id}")
            logger.info(f"搜索参数: 行业={request.industry}, 地区={request.region}, 类型={request.search_type}")
            
            search_result = self.searcher.search_companies(
                search_mode=request.search_type,
                industry=request.industry,
                region=request.region,
                custom_query=request.custom_query,
                keywords=request.keywords,
                gl=request.country_code,
                num_results=request.max_results
            )
            
            execution_time = time.time() - start_time
            
            if search_result["success"]:
                # 原始搜索结果
                raw_companies = search_result["data"]
                
                # LLM分析（如果可用）
                analyzed_companies = raw_companies
                if self.analyzer and raw_companies:
                    try:
                        logger.info(f"🤖 开始LLM分析 {len(raw_companies)} 家公司")
                        analyzed_companies = await self.analyzer.analyze_companies(
                            companies=raw_companies,
                            search_industry=request.industry,
                            search_region=request.region
                        )
                        logger.info(f"✅ LLM分析完成")
                    except Exception as e:
                        logger.error(f"❌ LLM分析失败: {e}")
                        # 分析失败，继续使用原始数据
                        analyzed_companies = raw_companies
                
                # 转换数据格式
                companies = self._convert_to_company_info(analyzed_companies, request)
                
                # 构建优化信息
                optimization_info = None
                if request.use_llm_optimization and hasattr(self.searcher, 'llm_available'):
                    optimization_info = {
                        "llm_enabled": self.searcher.llm_available,
                        "optimization_applied": True if self.searcher.llm_available else False,
                        "method": "llm" if self.searcher.llm_available else "fallback",
                        "analysis_enabled": self.analyzer is not None,
                        "companies_analyzed": len(analyzed_companies) if analyzed_companies else 0
                    }
                
                return CompanySearchResponse(
                    success=True,
                    message=f"搜索完成，找到 {len(companies)} 家公司",
                    search_id=search_id,
                    total_found=len(companies),
                    companies=companies,
                    execution_time=execution_time,
                    search_params={
                        "industry": request.industry,
                        "region": request.region,
                        "search_type": request.search_type,
                        "country_code": request.country_code,
                        "max_results": request.max_results
                    },
                    optimization_info=optimization_info
                )
            else:
                # 搜索失败
                return CompanySearchResponse(
                    success=False,
                    message="公司搜索失败",
                    search_id=search_id,
                    total_found=0,
                    companies=[],
                    execution_time=execution_time,
                    error=search_result.get("error", "未知错误"),
                    search_params={
                        "industry": request.industry,
                        "region": request.region,
                        "search_type": request.search_type,
                        "country_code": request.country_code
                    }
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"公司搜索异常: {str(e)}")
            
            return CompanySearchResponse(
                success=False,
                message="公司搜索服务异常",
                search_id=search_id,
                total_found=0,
                companies=[],
                execution_time=execution_time,
                error=str(e)
            )
    
    def _validate_request(self, request: CompanySearchRequest):
        """验证搜索请求参数"""
        if not request.industry and not request.region and not request.custom_query:
            raise ValueError("请至少提供行业、地区或自定义查询中的一个")
        
        if request.search_type not in ["general", "linkedin"]:
            raise ValueError("搜索类型必须是 'general' 或 'linkedin'")
        
        if request.max_results < 1 or request.max_results > 100:
            raise ValueError("结果数量必须在1-100之间")
    
    def _convert_to_company_info(self, raw_data: List[Dict], request: CompanySearchRequest) -> List[CompanyInfo]:
        """将原始搜索数据转换为CompanyInfo模型"""
        companies = []
        
        for item in raw_data:
            try:
                company = CompanyInfo(
                    name=item.get("name", "未知公司"),
                    domain=item.get("domain", ""),
                    website_url=item.get("url", ""),
                    linkedin_url=item.get("linkedin", ""),
                    industry=request.industry or "未知行业",
                    location=item.get("matched_location") or request.region or "未知位置",
                    description=item.get("description") or item.get("title", ""),
                    confidence_score=self._calculate_confidence_score(item),
                    source=f"{request.search_type}_search",
                    search_query=item.get("query", ""),
                    # AI分析字段
                    is_company=item.get("is_company"),
                    ai_score=item.get("ai_score"),
                    ai_reason=item.get("ai_reason"),
                    relevance_score=item.get("relevance_score"),
                    analysis_confidence=item.get("analysis_confidence")
                )
                companies.append(company)
                
            except Exception as e:
                logger.warning(f"转换公司信息失败: {e}, 数据: {item}")
                continue
        
        return companies
    
    def _calculate_confidence_score(self, item: Dict) -> float:
        """计算匹配置信度分数"""
        score = 0.5  # 基础分数
        
        # 有域名加分
        if item.get("domain"):
            score += 0.2
            
        # 有LinkedIn加分  
        if item.get("linkedin"):
            score += 0.1
            
        # 地理位置匹配加分
        if item.get("location_match"):
            score += 0.2
            
        # 确保分数在0-1范围内
        return min(max(score, 0.0), 1.0)
    
    async def get_search_suggestions(self, partial_query: str) -> List[str]:
        """获取搜索建议"""
        # 基础的搜索建议逻辑
        suggestions = []
        
        industry_suggestions = [
            "新能源汽车", "人工智能", "生物技术", "金融科技", "区块链",
            "电子商务", "医疗健康", "教育科技", "软件开发", "清洁能源"
        ]
        
        if partial_query:
            query_lower = partial_query.lower()
            suggestions = [s for s in industry_suggestions if query_lower in s.lower()]
        
        return suggestions[:5]  # 返回前5个建议
    
    async def get_search_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取搜索历史（简单实现）"""
        # 这里可以实现数据库查询逻辑
        # 目前返回空列表
        return []


# 全局服务实例
_company_service = None

def get_company_service() -> CompanySearchService:
    """获取公司搜索服务实例"""
    global _company_service
    if _company_service is None:
        _company_service = CompanySearchService()
    return _company_service