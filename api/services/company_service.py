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

# 导入LLM关键词生成器
try:
    from core.llm_keyword_generator import LLMKeywordGenerator
    LLM_KEYWORD_AVAILABLE = True
except ImportError as e:
    print(f"警告: LLM关键词生成器不可用: {e}")
    LLM_KEYWORD_AVAILABLE = False

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
        self.keyword_generator = None
        
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
                
        if LLM_KEYWORD_AVAILABLE:
            try:
                self.keyword_generator = LLMKeywordGenerator()
                logger.info("✅ LLM关键词生成器初始化成功")
            except Exception as e:
                logger.error(f"❌ LLM关键词生成器初始化失败: {e}")
                self.keyword_generator = None
    
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
            
            # 步骤1: LLM关键词生成和国家代码转换
            optimized_params = await self._optimize_search_params(request)
            
            # 执行搜索
            logger.info(f"开始公司搜索: {search_id}")
            logger.info(f"👥 用户搜索请求: 行业={request.industry}, 地区={request.region}, 类型={request.search_type}, 国家={request.country_code}")
            logger.info(f"优化搜索参数: 关键词={optimized_params.get('keywords')}, 国家代码={optimized_params.get('gl')}")
            
            # 执行多关键词搜索策略
            companies = await self._execute_company_search(request, optimized_params)
            logger.info(f"✅ 公司搜索完成，找到 {len(companies)} 家公司")
            
            # AI分析和评分（如果有公司结果）
            if companies and self.analyzer:
                try:
                    logger.info(f"🤖 开始LLM分析 {len(companies)} 家公司")
                    analyzed_companies = await self.analyzer.analyze_companies(
                        companies=[self._company_info_to_dict(company) for company in companies],
                        search_industry=request.industry,
                        search_region=request.region
                    )
                    logger.info(f"✅ LLM分析完成")
                    
                    # 更新companies的AI分析字段
                    for i, analyzed in enumerate(analyzed_companies):
                        if i < len(companies):
                            companies[i].ai_score = analyzed.get('ai_score')
                            companies[i].ai_reason = analyzed.get('ai_reason')
                            companies[i].relevance_score = analyzed.get('relevance_score')
                            companies[i].analysis_confidence = analyzed.get('analysis_confidence')
                            companies[i].is_company = analyzed.get('is_company')
                except Exception as e:
                    logger.error(f"❌ LLM分析失败: {e}")
            
            execution_time = time.time() - start_time
            
            # 构建优化信息
            optimization_info = None
            if request.use_llm_optimization and hasattr(self.searcher, 'llm_available'):
                optimization_info = {
                    "llm_enabled": self.searcher.llm_available,
                    "optimization_applied": True if self.searcher.llm_available else False,
                    "method": "llm" if self.searcher.llm_available else "fallback",
                    "analysis_enabled": self.analyzer is not None,
                    "companies_analyzed": len(companies) if companies else 0
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
    
    async def _optimize_search_params(self, request: CompanySearchRequest) -> Dict[str, Any]:
        """
        优化搜索参数：LLM关键词生成 + 国家代码转换
        
        Args:
            request: 原始搜索请求
            
        Returns:
            Dict: 优化后的搜索参数
        """
        result = {
            'industry': request.industry,
            'region': request.region,
            'keywords': request.keywords,
            'gl': request.country_code
        }
        
        try:
            # 步骤1: 国家代码转换
            if request.region and self.keyword_generator:
                converted_country = self.keyword_generator._resolve_country_code(request.region)
                if converted_country:
                    result['gl'] = converted_country
                    logger.info(f"🌍 国家转换: {request.region} → {converted_country}")
            
            # 步骤2: LLM关键词生成
            if request.use_llm_optimization and self.keyword_generator and request.industry:
                target_country = result['gl'] or 'us'  # 默认美国
                
                logger.info(f"🧠 开始LLM关键词生成: 行业={request.industry}, 国家={target_country}")
                
                try:
                    keyword_result = self.keyword_generator.generate_search_keywords(
                        industry=request.industry,
                        target_country=target_country,
                        search_type=request.search_type
                    )
                    
                    if keyword_result.get('success'):
                        # 获取LLM生成的多样化查询变体
                        if 'query_variants' in keyword_result:
                            queries = []
                            logger.info(f"🔍 发现 {len(keyword_result['query_variants'])} 个查询变体")
                            for i, variant in enumerate(keyword_result['query_variants'][:3], 1):  # 取前3个变体
                                query = variant.get('query', '')
                                variant_type = variant.get('type', 'unknown')
                                if query:
                                    queries.append(query)
                                    logger.info(f"📝 公司关键词变体{i}({variant_type}): {query}")
                            result['keywords'] = queries
                            result['query_variants'] = keyword_result['query_variants'][:3]
                            logger.info(f"✅ LLM公司关键词生成成功: {queries}")
                            logger.info(f"🎯 将使用分别搜索策略，逐个关键词执行搜索")
                        else:
                            # 回退到primary_keywords
                            primary_keywords = keyword_result.get('primary_keywords', [])
                            if primary_keywords:
                                result['keywords'] = primary_keywords[:3]
                                logger.info(f"✅ 使用主关键词: {primary_keywords[:3]}")
                                # 为主关键词创建query_variants结构
                                result['query_variants'] = [
                                    {"query": keyword, "type": "primary"} 
                                    for keyword in primary_keywords[:3]
                                ]
                                for i, keyword in enumerate(primary_keywords[:3], 1):
                                    logger.info(f"📝 主关键词{i}: {keyword}")
                            logger.info(f"🎯 将使用分别搜索策略，逐个关键词执行搜索")
                        
                        # 更新行业和地区描述（如果LLM提供了优化的版本）
                        if keyword_result.get('optimized_industry'):
                            result['industry'] = keyword_result['optimized_industry']
                        if keyword_result.get('optimized_region'):
                            result['region'] = keyword_result['optimized_region']
                            
                    else:
                        logger.warning("❌ LLM关键词生成失败，使用原始参数")
                
                except Exception as llm_error:
                    # LLM关键词生成出现严重错误
                    logger.error(f"❌ LLM关键词生成严重错误: {llm_error}")
                    # 判断是否为超时错误，如果是超时则继续使用基础关键词，如果是其他错误则抛出异常
                    if "timed out" in str(llm_error).lower() or "timeout" in str(llm_error).lower():
                        logger.warning("⚠️ LLM调用超时，将使用基础关键词继续搜索")
                    else:
                        # 对于非超时错误，按用户要求直接抛出异常
                        raise Exception(f"LLM关键词生成失败，请检查并修复: {llm_error}")
            
            # 步骤3: 兜底处理
            if not result.get('keywords'):
                # 如果没有生成关键词，使用基础关键词策略
                fallback_keywords = []
                if request.industry:
                    # 基础关键词：行业本身
                    fallback_keywords.append(request.industry)
                    # 如果有地区信息，添加地区+行业组合
                    if request.region:
                        fallback_keywords.append(f"{request.region} {request.industry}")
                    # 添加"companies"后缀增强
                    if "company" not in request.industry.lower() and "companies" not in request.industry.lower():
                        fallback_keywords.append(f"{request.industry} companies")
                else:
                    # 如果没有行业，使用通用关键词
                    fallback_keywords = ["companies", "business", "corporation"]
                
                result['keywords'] = fallback_keywords[:3]  # 最多3个关键词
                result['query_variants'] = [
                    {"query": keyword, "type": "fallback"} 
                    for keyword in result['keywords']
                ]
                logger.info(f"🔧 使用回退关键词策略: {result['keywords']}")
                logger.info(f"🔧 使用回退查询变体: {result['query_variants']}")
                logger.info(f"🎯 将使用分别搜索策略，逐个关键词执行搜索")
                
        except Exception as e:
            logger.error(f"❌ 搜索参数优化失败: {e}")
            # 发生错误时返回原始参数
            
        return result
    
    async def _execute_company_search(self, request: CompanySearchRequest, optimized_params: Dict[str, Any]) -> List[CompanyInfo]:
        """执行公司搜索的核心逻辑 - 多关键词策略"""
        
        if not self.searcher:
            # 没有搜索器时使用模拟数据
            logger.warning("🔧 公司搜索器不可用，使用模拟数据")
            return self._generate_mock_companies(request, optimized_params)
        
        logger.info(f"✅ 公司搜索器可用，开始实际搜索")
        
        try:
            # 获取LLM生成的关键词
            keywords = optimized_params.get('keywords', [])
            query_variants = optimized_params.get('query_variants', [])
            
            if not keywords:
                # 回退到基础查询
                keywords = [request.industry] if request.industry else ["company"]
                query_variants = [{"query": keywords[0], "type": "basic"}]
                logger.info(f"📝 使用基础查询关键词: {keywords}")
            else:
                logger.info(f"📝 使用LLM优化关键词: {keywords}")
            
            # 🔄 执行多关键词公司搜索策略
            logger.info(f"🔄 执行多关键词公司搜索策略，共 {len(keywords)} 个关键词")
            
            all_companies = []
            company_urls_seen = set()  # 用于去重
            search_stats = []  # 记录每轮搜索统计
            
            for i, keyword in enumerate(keywords, 1):
                try:
                    logger.info(f"🎯 第{i}轮搜索 - 关键词: {keyword}")
                    
                    # 获取当前关键词的类型信息
                    current_variant = query_variants[i-1] if i-1 < len(query_variants) else {"type": "unknown"}
                    keyword_type = current_variant.get('type', 'unknown')
                    
                    # 调用真实搜索器 - 使用已生成的关键词，避免额外LLM调用
                    if request.search_type == "linkedin":
                        # 对于LinkedIn搜索，直接调用内部方法避免重复的LLM关键词生成
                        search_result = await self._call_linkedin_search_directly(
                            keyword=keyword,
                            gl=optimized_params.get('gl', request.country_code),
                            num_results=min(10, request.max_results),
                            region=optimized_params.get('region', request.region)
                        )
                    else:
                        # 对于通用搜索，使用关键词参数避免重复LLM调用
                        search_result = self.searcher.search_companies(
                            search_mode=request.search_type,
                            industry=None,  # 不传递industry避免LLM调用
                            region=optimized_params.get('region', request.region),
                            custom_query=keyword,  # 使用custom_query直接搜索
                            keywords=None,
                            gl=optimized_params.get('gl', request.country_code),
                            num_results=min(10, request.max_results)
                        )
                    
                    # 处理搜索结果并去重
                    round_companies = []
                    raw_results = search_result.get('data', []) if isinstance(search_result, dict) else []
                    
                    # 详细记录原始搜索数据
                    logger.info(f"📊 第{i}轮原始搜索结果数据:")
                    logger.info(f"   - 搜索结果类型: {type(search_result)}")
                    logger.info(f"   - 原始结果条数: {len(raw_results)}")
                    if raw_results:
                        logger.info(f"   - 示例结果结构: {list(raw_results[0].keys()) if raw_results[0] else 'Empty result'}")
                        logger.info(f"   - 前3个结果预览:")
                        for idx, result in enumerate(raw_results[:3], 1):
                            name = result.get('name', 'Unknown')
                            domain = result.get('domain', '')
                            url = result.get('url', '')
                            logger.info(f"     {idx}. {name} - {domain} ({url[:50]}...)")
                    
                    for result in raw_results:
                        # 使用公司URL作为去重键
                        company_url = result.get('url', '') or result.get('linkedin', '')
                        if company_url and company_url not in company_urls_seen:
                            company = CompanyInfo(
                                name=result.get('name', 'Unknown Company'),
                                domain=result.get('domain', ''),
                                website_url=result.get('url', ''),
                                linkedin_url=result.get('linkedin', ''),
                                industry=request.industry or "未知行业",
                                location=result.get('matched_location') or request.region or "未知位置",
                                description=result.get('description') or result.get('title', ''),
                                confidence_score=self._calculate_confidence_score(result),
                                source=f"{request.search_type}_search_round_{i}",
                                search_query=result.get('query', ''),
                                # 新增关键词来源信息
                                source_keyword=keyword,
                                keyword_type=keyword_type,
                                search_round=i,
                                # AI分析字段
                                is_company=result.get('is_company'),
                                ai_score=result.get('ai_score'),
                                ai_reason=result.get('ai_reason'),
                                relevance_score=result.get('relevance_score'),
                                analysis_confidence=result.get('analysis_confidence')
                            )
                            round_companies.append(company)
                            company_urls_seen.add(company_url)
                    
                    all_companies.extend(round_companies)
                    
                    # 记录详细的搜索统计
                    round_stat = {
                        "round": i,
                        "keyword": keyword,
                        "keyword_type": keyword_type,
                        "raw_count": len(raw_results),
                        "valid_count": len(round_companies),
                        "cumulative_total": len(all_companies)
                    }
                    search_stats.append(round_stat)
                    
                    logger.info(f"✅ 第{i}轮搜索完成:")
                    logger.info(f"   🔍 关键词: {keyword} ({keyword_type})")
                    logger.info(f"   📊 原始结果: {len(raw_results)} 个")
                    logger.info(f"   ✨ 有效结果: {len(round_companies)} 个（去重后）")
                    logger.info(f"   🎯 累计总数: {len(all_companies)} 家公司")
                    
                except Exception as e:
                    logger.error(f"❌ 第{i}轮公司搜索失败: {e}")
                    continue
            
            logger.info(f"🎉 多关键词公司搜索完成，总共找到 {len(all_companies)} 家去重后的公司")
            
            # 按置信度排序并限制结果数量
            all_companies.sort(key=lambda x: x.confidence_score or 0, reverse=True)
            return all_companies[:request.max_results]
            
        except Exception as e:
            logger.error(f"❌ 公司搜索完全失败，使用模拟数据: {e}")
            import traceback
            logger.error(f"❌ 详细错误信息: {traceback.format_exc()}")
            return self._generate_mock_companies(request, optimized_params)
    
    def _generate_mock_companies(self, request: CompanySearchRequest, optimized_params: Dict[str, Any]) -> List[CompanyInfo]:
        """生成模拟公司数据"""
        import random
        companies = []
        
        # 模拟公司名称
        mock_companies = [
            {"name": "Tesla Inc", "domain": "tesla.com", "industry": "Electric Vehicles"},
            {"name": "Microsoft Corporation", "domain": "microsoft.com", "industry": "Technology"},
            {"name": "Google LLC", "domain": "google.com", "industry": "Technology"},
            {"name": "Apple Inc", "domain": "apple.com", "industry": "Technology"},
            {"name": "Amazon.com Inc", "domain": "amazon.com", "industry": "E-commerce"},
        ]
        
        num_companies = min(random.randint(2, 5), request.max_results)
        
        for i in range(num_companies):
            mock_company = random.choice(mock_companies)
            company = CompanyInfo(
                name=mock_company["name"],
                domain=mock_company["domain"],
                website_url=f"https://{mock_company['domain']}",
                linkedin_url=f"https://linkedin.com/company/{mock_company['name'].lower().replace(' ', '-').replace('.', '')}",
                industry=request.industry or mock_company["industry"],
                location=request.region or "United States",
                description=f"{mock_company['name']} is a leading company in {mock_company['industry']}.",
                confidence_score=random.uniform(0.7, 0.95),
                source="mock_search",
                search_query=request.industry or "mock query"
            )
            companies.append(company)
        
        return companies
    
    async def _call_linkedin_search_directly(
        self, 
        keyword: str, 
        gl: str, 
        num_results: int, 
        region: str = None
    ) -> Dict[str, Any]:
        """
        直接调用LinkedIn搜索，避免内部的重复LLM关键词生成
        
        Args:
            keyword: 已生成的搜索关键词
            gl: 国家代码
            num_results: 结果数量
            region: 地区信息
            
        Returns:
            Dict: 搜索结果
        """
        try:
            # 构建LinkedIn搜索查询
            linkedin_query = f"site:linkedin.com/company {keyword}"
            logger.info(f"🔍 LinkedIn纯净搜索查询 {keyword}: {linkedin_query}")
            
            # 构建优化的Serper参数
            serper_params = {
                'gl': gl,
                'location': gl  # 使用国家代码作为位置
            }
            logger.info(f"📡 使用优化的Serper参数: {serper_params}")
            
            # 直接调用底层LinkedIn搜索方法，避免重复LLM调用
            if hasattr(self.searcher, '_execute_single_linkedin_search'):
                # 直接调用底层LinkedIn搜索方法
                companies = self.searcher._execute_single_linkedin_search(
                    query=linkedin_query,
                    gl=gl,
                    num_results=num_results,
                    serper_params=serper_params,
                    region=region
                )
                # 包装成标准格式
                search_result = {"data": companies}
            else:
                # 回退到使用custom_query参数，但这可能仍会触发一些LLM调用
                search_result = self.searcher.search_companies(
                    search_mode="linkedin",
                    industry=None,
                    region=region,
                    custom_query=linkedin_query,  # 使用构建好的查询
                    keywords=None,
                    gl=gl,
                    num_results=num_results
                )
            
            logger.info(f"✅ LinkedIn搜索完成，查询: {linkedin_query}")
            return search_result
            
        except Exception as e:
            logger.error(f"❌ LinkedIn直接搜索失败: {e}")
            # 返回空结果结构
            return {"data": [], "error": str(e)}
    
    def _company_info_to_dict(self, company: CompanyInfo) -> Dict[str, Any]:
        """将CompanyInfo转换为字典格式"""
        return {
            "name": company.name,
            "domain": company.domain,
            "website_url": company.website_url,
            "linkedin_url": company.linkedin_url,
            "industry": company.industry,
            "location": company.location,
            "description": company.description,
            "confidence_score": company.confidence_score,
            "source": company.source,
            "search_query": company.search_query,
            "source_keyword": company.source_keyword,
            "keyword_type": company.keyword_type,
            "search_round": company.search_round
        }


# 全局服务实例
_company_service = None

def get_company_service() -> CompanySearchService:
    """获取公司搜索服务实例"""
    global _company_service
    if _company_service is None:
        _company_service = CompanySearchService()
    return _company_service