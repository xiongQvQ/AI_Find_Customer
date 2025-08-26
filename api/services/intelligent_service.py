"""
智能搜索服务层
基于自然语言的智能搜索，整合公司和员工搜索
"""
import os
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models.requests import IntelligentSearchRequest, CompanySearchRequest, EmployeeSearchRequest
from ..models.responses import (
    IntelligentSearchResponse, 
    IntelligentSearchResult,
    SearchInsight,
    CompanyInfo,
    EmployeeInfo
)
from .company_service import get_company_service
from .employee_service import get_employee_service

logger = logging.getLogger(__name__)


class IntelligentSearchService:
    """智能搜索服务类"""
    
    def __init__(self):
        """初始化智能搜索服务"""
        self.company_service = get_company_service()
        self.employee_service = get_employee_service()
        self.llm_available = self._check_llm_availability()
        logger.info(f"智能搜索服务初始化: LLM可用={self.llm_available}")
    
    def _check_llm_availability(self) -> bool:
        """检查LLM服务可用性"""
        llm_provider = os.getenv("LLM_PROVIDER", "none").lower()
        if llm_provider == "none":
            return False
        
        # 检查对应的API密钥
        key_mapping = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY", 
            "google": "GOOGLE_API_KEY",
            "huoshan": "ARK_API_KEY"
        }
        
        required_key = key_mapping.get(llm_provider)
        return bool(os.getenv(required_key)) if required_key else False
    
    async def intelligent_search(self, request: IntelligentSearchRequest) -> IntelligentSearchResponse:
        """
        执行智能搜索
        
        Args:
            request: 智能搜索请求
            
        Returns:
            IntelligentSearchResponse: 智能搜索结果
        """
        search_id = f"intelligent_search_{int(time.time())}"
        start_time = time.time()
        
        try:
            # 验证请求参数
            self._validate_request(request)
            
            logger.info(f"开始智能搜索: {search_id}")
            logger.info(f"查询: {request.query}")
            
            # 分析查询意图
            query_analysis = await self._analyze_query(request.query)
            
            # 根据分析结果执行搜索
            search_results = await self._execute_intelligent_search(request, query_analysis)
            
            # 生成搜索洞察
            search_insights = self._generate_search_insights(
                request.query, 
                query_analysis, 
                search_results
            )
            
            execution_time = time.time() - start_time
            
            return IntelligentSearchResponse(
                success=True,
                message=f"智能搜索完成，找到 {search_results.total_companies} 家公司，{search_results.total_employees} 名员工",
                search_id=search_id,
                original_query=request.query,
                processed_query=query_analysis.get("processed_query", request.query),
                results=search_results,
                execution_time=execution_time,
                performance_metrics={
                    "query_analysis_time": query_analysis.get("analysis_time", 0),
                    "search_execution_time": execution_time - query_analysis.get("analysis_time", 0),
                    "llm_enabled": self.llm_available,
                    "strategy_used": query_analysis.get("strategy", "default")
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"智能搜索异常: {str(e)}")
            
            return IntelligentSearchResponse(
                success=False,
                message="智能搜索失败",
                search_id=search_id,
                original_query=request.query,
                processed_query=request.query,
                results=IntelligentSearchResult(
                    companies=[],
                    employees=[],
                    total_companies=0,
                    total_employees=0,
                    search_insights=SearchInsight(
                        query_analysis="搜索失败",
                        search_strategy="error",
                        optimization_applied=[],
                        confidence_level="low",
                        suggestions=["请检查查询参数并重试"]
                    )
                ),
                execution_time=execution_time,
                error=str(e)
            )
    
    async def _analyze_query(self, query: str) -> Dict[str, Any]:
        """分析自然语言查询"""
        start_time = time.time()
        
        if self.llm_available:
            # TODO: 使用LLM分析查询意图
            analysis = await self._llm_query_analysis(query)
        else:
            # 使用规则基础的查询分析
            analysis = self._rule_based_query_analysis(query)
        
        analysis["analysis_time"] = time.time() - start_time
        return analysis
    
    async def _llm_query_analysis(self, query: str) -> Dict[str, Any]:
        """使用LLM分析查询（待实现）"""
        # TODO: 集成LLM进行查询意图分析
        # 目前使用规则基础分析
        return self._rule_based_query_analysis(query)
    
    def _rule_based_query_analysis(self, query: str) -> Dict[str, Any]:
        """基于规则的查询分析"""
        query_lower = query.lower()
        
        # 识别行业关键词
        industry_keywords = {
            "ai": ["人工智能", "ai", "artificial intelligence", "机器学习", "深度学习"],
            "tech": ["科技", "技术", "software", "互联网", "it"],
            "energy": ["能源", "新能源", "renewable", "solar", "清洁能源"],
            "finance": ["金融", "银行", "投资", "fintech", "支付"],
            "biotech": ["生物", "医疗", "制药", "biotechnology", "healthcare"],
            "automotive": ["汽车", "automotive", "electric vehicle", "ev"]
        }
        
        detected_industry = None
        for industry, keywords in industry_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_industry = industry
                break
        
        # 识别地理位置
        location_keywords = {
            "us": ["美国", "us", "usa", "america", "california", "silicon valley", "纽约", "加州"],
            "cn": ["中国", "china", "北京", "上海", "深圳", "杭州"],
            "uk": ["英国", "uk", "london", "伦敦"],
            "europe": ["欧洲", "europe", "德国", "法国"]
        }
        
        detected_location = None
        for location, keywords in location_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_location = location
                break
        
        # 识别搜索类型
        search_type_keywords = {
            "company_focused": ["公司", "企业", "company", "business", "startup"],
            "employee_focused": ["员工", "人员", "ceo", "manager", "engineer", "销售"],
            "comprehensive": ["全面", "comprehensive", "详细", "complete"]
        }
        
        search_focus = "comprehensive"  # 默认综合搜索
        for focus_type, keywords in search_type_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                search_focus = focus_type
                break
        
        # 识别职位关键词
        position_keywords = ["ceo", "cto", "manager", "engineer", "销售", "经理", "总裁"]
        detected_positions = [
            pos for pos in position_keywords 
            if pos in query_lower
        ]
        
        return {
            "processed_query": query,
            "detected_industry": detected_industry,
            "detected_location": detected_location,
            "search_focus": search_focus,
            "detected_positions": detected_positions,
            "strategy": "rule_based",
            "confidence": 0.7
        }
    
    async def _execute_intelligent_search(
        self, 
        request: IntelligentSearchRequest, 
        query_analysis: Dict[str, Any]
    ) -> IntelligentSearchResult:
        """执行智能搜索"""
        
        companies = []
        employees = []
        
        # 根据搜索范围决定执行哪些搜索
        if request.search_scope in ["company_only", "comprehensive"]:
            companies = await self._search_companies_intelligently(request, query_analysis)
        
        if request.search_scope in ["employee_only", "comprehensive"]:
            employees = await self._search_employees_intelligently(request, query_analysis)
        
        # 生成搜索洞察
        search_insights = SearchInsight(
            query_analysis=f"识别到行业: {query_analysis.get('detected_industry', '未识别')}, "
                          f"地区: {query_analysis.get('detected_location', '未识别')}, "
                          f"搜索重点: {query_analysis.get('search_focus', '综合')}",
            search_strategy=query_analysis.get('strategy', 'rule_based'),
            optimization_applied=self._get_applied_optimizations(request, query_analysis),
            confidence_level=self._calculate_confidence_level(query_analysis, companies, employees),
            suggestions=self._generate_suggestions(query_analysis, companies, employees)
        )
        
        return IntelligentSearchResult(
            companies=companies,
            employees=employees,
            total_companies=len(companies),
            total_employees=len(employees),
            search_insights=search_insights
        )
    
    async def _search_companies_intelligently(
        self, 
        request: IntelligentSearchRequest,
        query_analysis: Dict[str, Any]
    ) -> List[CompanyInfo]:
        """智能公司搜索"""
        try:
            # 构建公司搜索请求
            company_request = CompanySearchRequest(
                industry=self._extract_industry_keyword(query_analysis, request.query),
                region=self._extract_region_keyword(query_analysis, request.query),
                search_type="linkedin",
                country_code=self._determine_country_code(query_analysis),
                max_results=request.max_companies,
                use_llm_optimization=request.enable_optimization
            )
            
            # 执行公司搜索
            company_response = await self.company_service.search_companies(company_request)
            
            if company_response.success:
                return company_response.companies
            else:
                logger.warning(f"公司搜索失败: {company_response.error}")
                return []
                
        except Exception as e:
            logger.error(f"智能公司搜索异常: {e}")
            return []
    
    async def _search_employees_intelligently(
        self,
        request: IntelligentSearchRequest,
        query_analysis: Dict[str, Any]
    ) -> List[EmployeeInfo]:
        """智能员工搜索"""
        try:
            # 从查询中提取公司名称（简化实现）
            companies_to_search = self._extract_company_names(request.query, query_analysis)
            
            if not companies_to_search:
                logger.info("未从查询中识别出具体公司名称，跳过员工搜索")
                return []
            
            all_employees = []
            
            # 搜索每个公司的员工
            for company_name in companies_to_search[:3]:  # 限制搜索公司数量
                try:
                    # 构建员工搜索请求
                    employee_request = EmployeeSearchRequest(
                        company_name=company_name,
                        target_positions=self._extract_target_positions(query_analysis, request.query),
                        country_code=self._determine_country_code(query_analysis),
                        max_results=min(request.max_employees_per_company, 10),
                        search_options=["linkedin", "email"]
                    )
                    
                    # 执行员工搜索
                    employee_response = await self.employee_service.search_employees(employee_request)
                    
                    if employee_response.success:
                        all_employees.extend(employee_response.employees)
                    
                except Exception as e:
                    logger.warning(f"搜索公司 {company_name} 员工失败: {e}")
                    continue
            
            # 按置信度排序并限制总数
            all_employees.sort(key=lambda x: x.confidence_score or 0, reverse=True)
            return all_employees[:request.max_employees_per_company * 3]
            
        except Exception as e:
            logger.error(f"智能员工搜索异常: {e}")
            return []
    
    def _extract_industry_keyword(self, query_analysis: Dict[str, Any], original_query: str) -> Optional[str]:
        """提取行业关键词"""
        detected_industry = query_analysis.get('detected_industry')
        if detected_industry:
            industry_mapping = {
                "ai": "人工智能",
                "tech": "科技",
                "energy": "新能源", 
                "finance": "金融科技",
                "biotech": "生物技术",
                "automotive": "汽车"
            }
            return industry_mapping.get(detected_industry, detected_industry)
        
        # 尝试从原始查询中提取
        for word in original_query.split():
            if len(word) > 2:  # 简单的关键词过滤
                return word
        
        return None
    
    def _extract_region_keyword(self, query_analysis: Dict[str, Any], original_query: str) -> Optional[str]:
        """提取地区关键词"""
        detected_location = query_analysis.get('detected_location')
        if detected_location:
            location_mapping = {
                "us": "美国加利福尼亚",
                "cn": "中国北京",
                "uk": "英国伦敦",
                "europe": "德国柏林"
            }
            return location_mapping.get(detected_location)
        
        return None
    
    def _determine_country_code(self, query_analysis: Dict[str, Any]) -> str:
        """确定国家代码"""
        detected_location = query_analysis.get('detected_location', 'us')
        location_to_code = {
            "us": "us",
            "cn": "cn", 
            "uk": "uk",
            "europe": "de"
        }
        return location_to_code.get(detected_location, "us")
    
    def _extract_company_names(self, query: str, query_analysis: Dict[str, Any]) -> List[str]:
        """从查询中提取公司名称"""
        # 简单的公司名称提取逻辑
        known_companies = [
            "Tesla", "Apple", "Google", "Microsoft", "Amazon",
            "Facebook", "Netflix", "Uber", "Airbnb", "SpaceX",
            "腾讯", "阿里巴巴", "百度", "字节跳动", "华为"
        ]
        
        companies = []
        query_lower = query.lower()
        
        for company in known_companies:
            if company.lower() in query_lower:
                companies.append(company)
        
        return companies
    
    def _extract_target_positions(self, query_analysis: Dict[str, Any], original_query: str) -> List[str]:
        """提取目标职位"""
        detected_positions = query_analysis.get('detected_positions', [])
        
        if detected_positions:
            return detected_positions
        
        # 默认职位列表
        return ["CEO", "CTO", "销售经理"]
    
    def _get_applied_optimizations(self, request: IntelligentSearchRequest, query_analysis: Dict[str, Any]) -> List[str]:
        """获取应用的优化措施"""
        optimizations = []
        
        if request.ai_evaluation:
            optimizations.append("AI评估和过滤")
        
        if request.enable_optimization:
            optimizations.append("关键词优化")
        
        if query_analysis.get('strategy') == 'llm_based':
            optimizations.append("LLM查询分析")
        
        return optimizations
    
    def _calculate_confidence_level(self, query_analysis: Dict[str, Any], companies: List[CompanyInfo], employees: List[EmployeeInfo]) -> str:
        """计算置信度级别"""
        analysis_confidence = query_analysis.get('confidence', 0.5)
        result_count = len(companies) + len(employees)
        
        if analysis_confidence > 0.8 and result_count > 10:
            return "high"
        elif analysis_confidence > 0.6 and result_count > 5:
            return "medium"
        else:
            return "low"
    
    def _generate_suggestions(self, query_analysis: Dict[str, Any], companies: List[CompanyInfo], employees: List[EmployeeInfo]) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        if not companies and not employees:
            suggestions.append("尝试使用更具体的行业或公司关键词")
            suggestions.append("检查地理位置是否正确")
        elif len(companies) < 5:
            suggestions.append("尝试扩大搜索范围或使用相关关键词")
        
        if not query_analysis.get('detected_industry'):
            suggestions.append("明确指定行业类别可能会获得更精准的结果")
            
        if not query_analysis.get('detected_location'):
            suggestions.append("添加地理位置信息可以提高结果的相关性")
        
        return suggestions
    
    def _generate_search_insights(self, original_query: str, query_analysis: Dict[str, Any], search_results: IntelligentSearchResult) -> SearchInsight:
        """生成搜索洞察（已在上面实现）"""
        return search_results.search_insights
    
    def _validate_request(self, request: IntelligentSearchRequest):
        """验证智能搜索请求参数"""
        if len(request.query.strip()) < 5:
            raise ValueError("查询内容至少需要5个字符")
        
        if request.search_scope not in ["company_only", "employee_only", "comprehensive"]:
            raise ValueError("搜索范围必须是 'company_only', 'employee_only' 或 'comprehensive'")
        
        if request.max_companies < 1 or request.max_companies > 100:
            raise ValueError("公司数量必须在1-100之间")
            
        if request.max_employees_per_company < 1 or request.max_employees_per_company > 20:
            raise ValueError("每公司员工数量必须在1-20之间")


# 全局服务实例
_intelligent_service = None

def get_intelligent_service() -> IntelligentSearchService:
    """获取智能搜索服务实例"""
    global _intelligent_service
    if _intelligent_service is None:
        _intelligent_service = IntelligentSearchService()
    return _intelligent_service