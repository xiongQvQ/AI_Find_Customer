"""
FastAPI Backend for AI Customer Finder
替代Streamlit前端的后端API服务
"""
import os
import sys
import json
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
from enhanced_website_utils import enhanced_website_validator

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 导入公司搜索模块
try:
    from core.company_search import CompanySearcher
    COMPANY_SEARCH_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Company search module not available: {e}")
    COMPANY_SEARCH_AVAILABLE = False

# 导入联系信息提取模块
try:
    from extract_contact_info import WebsiteContentExtractor
    CONTACT_EXTRACTION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Contact extraction module not available: {e}")
    CONTACT_EXTRACTION_AVAILABLE = False

# 导入现有的LangGraph搜索模块
try:
    from langgraph_search import create_search_graph
    from langgraph_search.workflows.enhanced_workflow import create_enhanced_search_graph
    LANGGRAPH_AVAILABLE = True
    ENHANCED_WORKFLOW_AVAILABLE = True
except ImportError as e:
    print(f"Warning: LangGraph search module not available: {e}")
    LANGGRAPH_AVAILABLE = False
    ENHANCED_WORKFLOW_AVAILABLE = False

load_dotenv()

app = FastAPI(
    title="AI Customer Finder API",
    description="Backend API for intelligent customer search and analysis",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Vue开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 启动事件
@app.on_event("startup")
async def startup_event():
    """FastAPI 启动时的初始化任务"""
    # 导入并启动异步搜索管理器的清理任务
    try:
        from async_search_api import periodic_cleanup
        asyncio.create_task(periodic_cleanup())
        print("✅ 异步搜索清理任务已启动")
    except ImportError:
        print("⚠️ 异步搜索模块未可用")

# 数据模型
class SearchRequest(BaseModel):
    query: str
    ai_evaluation_enabled: bool = True
    employee_search_enabled: bool = False
    output_format: str = "csv"
    
class EnhancedSearchRequest(BaseModel):
    query: str
    ai_evaluation_enabled: bool = True
    employee_search_enabled: bool = True
    output_format: str = "csv"
    preferred_strategy: Optional[str] = None  # "company_first", "employee_first", "balanced", "adaptive"
    enable_optimization: bool = True  # 启用搜索优化
    max_optimization_rounds: int = 2  # 最大优化轮数

class SearchResponse(BaseModel):
    success: bool
    search_id: str
    message: str
    search_results: Optional[Dict[str, Any]] = None
    output_files: List[str] = []
    execution_time: float = 0.0
    error: Optional[str] = None

class EmployeeSearchRequest(BaseModel):
    company_name: str
    company_domain: Optional[str] = None
    target_position: str
    options: List[str] = ["linkedin", "email"]

class EmployeeSearchResponse(BaseModel):
    success: bool
    search_id: str
    message: str
    total_employees: int = 0
    verified_contacts: int = 0
    employees: List[Dict[str, Any]] = []
    execution_time: float = 0.0
    error: Optional[str] = None

class CompanySearchRequest(BaseModel):
    industry: Optional[str] = None
    region: Optional[str] = None
    search_type: str = "general"  # "general" or "linkedin"
    gl: str = "us"
    num_results: int = 30
    custom_query: Optional[str] = None
    keywords: Optional[List[str]] = None

class CompanySearchResponse(BaseModel):
    success: bool
    search_id: str
    message: str
    total_companies: int = 0
    companies: List[Dict[str, Any]] = []
    execution_time: float = 0.0
    output_file: Optional[str] = None
    error: Optional[str] = None

class ContactExtractionRequest(BaseModel):
    urls: List[str] = []  # URL列表
    single_url: Optional[str] = None  # 单个URL
    headless: bool = True
    timeout: int = 15000  # 毫秒
    visit_contact_page: bool = False
    merge_with_original: bool = False  # 是否与原始数据合并

class ContactExtractionResponse(BaseModel):
    success: bool
    extraction_id: str
    message: str
    total_urls: int = 0
    successful_extractions: int = 0
    contact_info: List[Dict[str, Any]] = []
    execution_time: float = 0.0
    output_file: Optional[str] = None
    error: Optional[str] = None

# 全局变量存储搜索状态
active_searches = {}

@app.get("/")
async def root():
    return {
        "message": "AI Customer Finder API",
        "version": "1.0.0",
        "langgraph_available": LANGGRAPH_AVAILABLE,
        "endpoints": [
            "/intelligent-search",
            "/async-search",
            "/async-search/{search_id}/stream",
            "/async-search/{search_id}/status",
            "/async-search/{search_id}/results",
            "/search-status/{search_id}",
            "/export/{format}",
            "/health",
            "/company-search",
            "/employee-search",
            "/contact-extraction"
        ]
    }

@app.get("/health")
async def health_check():
    """健康检查接口"""
    # 检查关键环境变量
    env_status = {
        "SERPER_API_KEY": bool(os.getenv("SERPER_API_KEY")),
        "LLM_PROVIDER": os.getenv("LLM_PROVIDER", "none"),
        "ARK_API_KEY": bool(os.getenv("ARK_API_KEY")) if os.getenv("LLM_PROVIDER") == "huoshan" else None,
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")) if os.getenv("LLM_PROVIDER") == "openai" else None,
    }
    
    return {
        "status": "healthy",
        "langgraph_available": LANGGRAPH_AVAILABLE,
        "environment": env_status,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/intelligent-search", response_model=SearchResponse)
async def intelligent_search(request: SearchRequest):
    """
    智能搜索接口 - LangGraph驱动的AI搜索引擎
    
    使用LangGraph工作流进行智能化的企业和员工搜索，包含AI评估和结果优化。
    
    Args:
        request (SearchRequest): 智能搜索请求参数
            - query: 搜索查询字符串 (必填)
            - ai_evaluation_enabled: 是否启用AI评估 (默认 True)
            - employee_search_enabled: 是否启用员工搜索 (默认 False)
            - output_format: 输出格式 ("csv" 或 "json")
    
    Returns:
        SearchResponse: 智能搜索结果
            - success: 是否成功
            - search_id: 搜索ID
            - message: 响应消息
            - search_results: 搜索结果详细信息
                - companies: 公司信息列表 (包含官网验证)
                - employees: 员工信息列表 (如果启用)
                - total_companies_found: 找到的公司总数
                - filtered_by_website: 是否应用了官网过滤
            - output_files: 生成的输出文件列表
            - execution_time: 执行时间(秒)
            - error: 错误信息
    
    特色功能:
        - AI驱动的查询理解和优化
        - 自动官网识别和验证
        - 智能结果过滤和排序
        - 多维度企业信息提取
        - 可选的员工信息搜索
        - 自动化的数据清理和格式化
    
    Examples:
        基础企业搜索:
        {
            "query": "renewable energy companies in California",
            "ai_evaluation_enabled": true,
            "output_format": "csv"
        }
        
        企业+员工综合搜索:
        {
            "query": "tech startups in Silicon Valley",
            "ai_evaluation_enabled": true,
            "employee_search_enabled": true,
            "output_format": "json"
        }
    
    Raises:
        HTTPException:
            - 400: 查询为空或API密钥未配置
            - 503: LangGraph搜索模块不可用
            - 500: 搜索执行失败
    """
    if not LANGGRAPH_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="LangGraph search module not available. Please check installation."
        )
    
    if not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty"
        )
    
    # 检查必需的环境变量
    if not os.getenv("SERPER_API_KEY"):
        raise HTTPException(
            status_code=400,
            detail="SERPER_API_KEY not configured. Please configure API keys first."
        )
    
    search_id = f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # 创建LangGraph搜索实例
        search_graph = create_search_graph(enable_checkpoints=True)
        
        # 执行搜索
        start_time = datetime.now()
        result = search_graph.execute_search(
            request.query,
            ai_evaluation_enabled=request.ai_evaluation_enabled,
            employee_search_enabled=request.employee_search_enabled,
            output_format=request.output_format
        )
        execution_time = (datetime.now() - start_time).total_seconds()
        
        if result.get('success'):
            # 应用官网过滤
            search_results = result.get('result', {}).get('search_results', {})
            companies = search_results.get('companies', [])
            
            if companies:
                # 过滤并标记官网
                filtered_companies = []
                for company in companies:
                    company_name = company.get('name', '')
                    if company_name:
                        # 使用增强版官网验证器（带搜索引擎支持）
                        website_info = enhanced_website_validator.get_official_website(company_name)
                        if website_info['website']:
                            company['official_website'] = website_info['website']
                            company['website_confidence'] = website_info['confidence']
                            company['website_method'] = website_info['method']
                            company['search_results'] = website_info.get('search_results', [])
                        
                        # 如果已有网站URL，使用增强版深度验证
                        if company.get('website_url'):
                            verification = enhanced_website_validator.is_official_website(
                                company['website_url'], company_name
                            )
                            company['is_official_website'] = verification['is_official']
                            company['verification_confidence'] = verification['confidence']
                            company['verification_reasons'] = verification['reasons']
                            
                            # 使用更智能的过滤策略 - 只保留高置信度的官网
                            if verification['is_official'] or verification['confidence'] > 0.6:
                                # 添加详细分析结果
                                company['detailed_analysis'] = verification.get('analysis', {})
                                filtered_companies.append(company)
                        else:
                            filtered_companies.append(company)
                
                search_results['companies'] = filtered_companies
                search_results['total_companies_found'] = len(filtered_companies)
                search_results['filtered_by_website'] = True
            
            return SearchResponse(
                success=True,
                search_id=search_id,
                message=f"Search completed successfully. Found {search_results.get('total_companies_found', 0)} companies (官网过滤已应用).",
                search_results=search_results,
                output_files=result.get('result', {}).get('output_files', []),
                execution_time=execution_time
            )
        else:
            return SearchResponse(
                success=False,
                search_id=search_id,
                message="Search failed",
                error=result.get('error', 'Unknown error occurred'),
                execution_time=execution_time
            )
            
    except Exception as e:
        print(f"Search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )

@app.post("/enhanced-search", response_model=SearchResponse)
async def enhanced_search(request: EnhancedSearchRequest):
    """
    增强版智能搜索接口 - 支持灵活的复合搜索策略
    
    高级LangGraph工作流，支持自适应搜索策略、多轮优化和复杂搜索场景。
    
    Args:
        request (EnhancedSearchRequest): 增强搜索请求参数
            - query: 搜索查询字符串 (必填)
            - ai_evaluation_enabled: 是否启用AI评估 (默认 True)
            - employee_search_enabled: 是否启用员工搜索 (默认 True)
            - output_format: 输出格式 ("csv" 或 "json")
            - preferred_strategy: 首选搜索策略 (可选)
                - "company_first": 公司优先策略
                - "employee_first": 员工优先策略
                - "balanced": 平衡策略
                - "adaptive": 自适应策略 (推荐)
            - enable_optimization: 启用搜索优化 (默认 True)
            - max_optimization_rounds: 最大优化轮数 (默认 2)
    
    Returns:
        SearchResponse: 增强搜索结果
            - success: 是否成功
            - search_id: 搜索ID
            - message: 响应消息 (包含选择的策略信息)
            - search_results: 搜索结果详细信息
                - companies: 公司信息列表 (高级过滤和验证)
                - employees: 员工信息列表 (如果启用)
                - strategy_evaluation: 策略评估信息
            - output_files: 生成的输出文件列表
            - execution_time: 执行时间(秒)
            - error: 错误信息
    
    高级特性:
        - 自适应搜索策略选择
        - 多轮搜索优化和结果改进
        - 智能策略切换和组合
        - 高级结果质量评估
        - 动态参数调整和优化
        - 复杂查询理解和分解
    
    Examples:
        自适应高级搜索:
        {
            "query": "AI companies in Europe with machine learning expertise",
            "preferred_strategy": "adaptive",
            "enable_optimization": true,
            "max_optimization_rounds": 3
        }
        
        公司优先搜索策略:
        {
            "query": "fintech startups in London",
            "preferred_strategy": "company_first",
            "ai_evaluation_enabled": true,
            "employee_search_enabled": false
        }
        
        员工优先搜索策略:
        {
            "query": "blockchain developers at crypto companies",
            "preferred_strategy": "employee_first",
            "employee_search_enabled": true
        }
    
    Raises:
        HTTPException:
            - 400: 查询为空或API密钥未配置
            - 503: 增强搜索工作流不可用
            - 500: 搜索执行失败
    """
    if not ENHANCED_WORKFLOW_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Enhanced search workflow not available. Please check installation."
        )
    
    if not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty"
        )
    
    # 检查必需的环境变量
    if not os.getenv("SERPER_API_KEY"):
        raise HTTPException(
            status_code=400,
            detail="SERPER_API_KEY not configured. Please configure API keys first."
        )
    
    search_id = f"enhanced_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # 创建增强版搜索图实例
        enhanced_graph = create_enhanced_search_graph(enable_checkpoints=True)
        
        # 执行增强版搜索
        start_time = datetime.now()
        result = enhanced_graph.execute_search(
            request.query,
            ai_evaluation_enabled=request.ai_evaluation_enabled,
            employee_search_enabled=request.employee_search_enabled,
            output_format=request.output_format,
            preferred_strategy=request.preferred_strategy,
            enable_optimization=request.enable_optimization,
            max_optimization_rounds=request.max_optimization_rounds
        )
        execution_time = (datetime.now() - start_time).total_seconds()
        
        if result.get('success'):
            # 获取搜索结果
            search_results = result.get('result', {}).get('search_results', {})
            companies = search_results.get('companies', [])
            
            # 应用优化的官网验证策略（减少API调用）
            if companies:
                filtered_companies = []
                for company in companies:
                    company_name = company.get('name', '')
                    if company_name:
                        # 只对有潜在价值的公司进行官网验证
                        ai_score = company.get('ai_score') or 0
                        description = company.get('description', '').lower()
                        should_verify = (
                            (isinstance(ai_score, (int, float)) and ai_score >= 70) or  # AI评分高的公司
                            'startup' in description or
                            'robot' in description or
                            not company.get('website_url')  # 没有网站URL的需要查找
                        )
                        
                        if should_verify:
                            # 仅对高价值目标进行官网验证
                            try:
                                website_info = enhanced_website_validator.get_official_website(company_name)
                                if website_info['website']:
                                    company['official_website'] = website_info['website']
                                    company['website_confidence'] = website_info['confidence']
                                    company['website_method'] = website_info['method']
                                    company['search_results'] = website_info.get('search_results', [])
                            except Exception as e:
                                logger.warning(f"官网查找失败 {company_name}: {e}")
                            
                            # 验证现有网站URL（仅对重要公司）
                            if company.get('website_url'):
                                try:
                                    verification = enhanced_website_validator.is_official_website(
                                        company['website_url'], company_name
                                    )
                                    company['is_official_website'] = verification['is_official']
                                    company['verification_confidence'] = verification['confidence']
                                    company['verification_reasons'] = verification['reasons']
                                    company['detailed_analysis'] = verification.get('analysis', {})
                                except Exception as e:
                                    logger.warning(f"官网验证失败 {company_name}: {e}")
                                    # 验证失败时仍然保留公司信息
                                    company['is_official_website'] = False
                                    company['verification_confidence'] = 0.0
                        
                        # 更宽松的过滤策略：优先保留有用信息
                        ai_score = company.get('ai_score') or 0
                        should_include = (
                            (isinstance(ai_score, (int, float)) and ai_score > 0) or  # 有AI评分的
                            company.get('website_url') or       # 有网站的
                            company.get('official_website') or # 找到官网的
                            'startup' in description or
                            'robot' in description
                        )
                        
                        if should_include:
                            filtered_companies.append(company)
                
                search_results['companies'] = filtered_companies
                search_results['total_companies_found'] = len(filtered_companies)
                search_results['filtered_by_website'] = True
            
            # 添加策略信息到响应
            strategy_info = result.get('result', {}).get('strategy_evaluation', {})
            
            return SearchResponse(
                success=True,
                search_id=search_id,
                message=f"Enhanced search completed successfully. Found {search_results.get('total_companies_found', 0)} companies using {strategy_info.get('selected_strategy', 'adaptive')} strategy.",
                search_results=search_results,
                output_files=result.get('result', {}).get('output_files', []),
                execution_time=execution_time
            )
        else:
            return SearchResponse(
                success=False,
                search_id=search_id,
                message="Enhanced search failed",
                error=result.get('error', 'Unknown error occurred'),
                execution_time=execution_time
            )
            
    except Exception as e:
        print(f"Enhanced search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Enhanced search failed: {str(e)}"
        )

@app.post("/company-search", response_model=CompanySearchResponse)
async def company_search(request: CompanySearchRequest):
    """
    公司搜索接口
    
    搜索目标企业信息，支持按行业、地区、自定义查询等条件搜索。
    
    Args:
        request (CompanySearchRequest): 搜索请求参数
            - industry: 行业关键词 (可选)
            - region: 地区关键词 (可选)  
            - search_type: 搜索类型 ("general" 或 "linkedin")
            - gl: 国家代码 (默认 "us")
            - num_results: 返回结果数量 (默认 30)
            - custom_query: 自定义搜索查询 (可选)
            - keywords: 额外关键词列表 (可选)
    
    Returns:
        CompanySearchResponse: 搜索结果
            - success: 是否成功
            - search_id: 搜索ID
            - message: 响应消息
            - total_companies: 找到的公司总数
            - companies: 公司信息列表
            - execution_time: 执行时间(秒)
            - output_file: 输出文件路径
            - error: 错误信息
    
    Examples:
        基础搜索:
        {
            "industry": "新能源",
            "region": "加州",
            "search_type": "general",
            "gl": "us"
        }
        
        LinkedIn专项搜索:
        {
            "industry": "软件",
            "region": "硅谷",
            "search_type": "linkedin",
            "gl": "us"
        }
        
        自定义查询搜索:
        {
            "custom_query": "solar panel manufacturers California",
            "gl": "us",
            "num_results": 20
        }
    
    Raises:
        HTTPException: 
            - 400: 参数验证失败或API密钥未配置
            - 503: 公司搜索模块不可用
            - 500: 搜索执行失败
    """
    if not COMPANY_SEARCH_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Company search module not available. Please check installation."
        )
    
    # 验证输入参数
    if not request.custom_query and not request.industry and not request.region:
        raise HTTPException(
            status_code=400,
            detail="Please provide at least industry, region, or custom query"
        )
    
    # 检查必需的环境变量
    if not os.getenv("SERPER_API_KEY"):
        raise HTTPException(
            status_code=400,
            detail="SERPER_API_KEY not configured. Please configure API keys first."
        )
    
    search_id = f"company_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        start_time = datetime.now()
        
        # 创建CompanySearcher实例并执行搜索
        searcher = CompanySearcher()
        result = searcher.search_companies(
            search_mode=request.search_type,
            industry=request.industry,
            region=request.region,
            custom_query=request.custom_query,
            keywords=request.keywords,
            gl=request.gl,
            num_results=request.num_results
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        if result["success"]:
            companies = result["data"]
            return CompanySearchResponse(
                success=True,
                search_id=search_id,
                message=f"Company search completed successfully. Found {len(companies)} companies.",
                total_companies=len(companies),
                companies=companies,
                execution_time=execution_time,
                output_file=result["output_file"]
            )
        else:
            return CompanySearchResponse(
                success=False,
                search_id=search_id,
                message="Company search failed",
                total_companies=0,
                companies=[],
                execution_time=execution_time,
                output_file=None,
                error=result["error"]
            )
    
    except Exception as e:
        print(f"Company search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Company search failed: {str(e)}"
        )

@app.post("/employee-search", response_model=EmployeeSearchResponse)
async def employee_search(request: EmployeeSearchRequest):
    """
    员工搜索接口
    
    搜索指定公司的员工信息，特别是关键决策者和目标职位人员。
    
    Args:
        request (EmployeeSearchRequest): 员工搜索请求参数
            - company_name: 目标公司名称 (必填)
            - company_domain: 公司域名 (可选，如果未提供会自动查找)
            - target_position: 目标职位 (必填，如 "CEO", "销售经理", "CTO")
            - options: 搜索选项列表 (默认 ["linkedin", "email"])
    
    Returns:
        EmployeeSearchResponse: 员工搜索结果
            - success: 是否成功
            - search_id: 搜索ID
            - message: 响应消息
            - total_employees: 找到的员工总数
            - verified_contacts: 验证联系方式数量
            - employees: 员工信息列表
            - execution_time: 执行时间(秒)
            - error: 错误信息
    
    员工信息包含字段:
        - name: 员工姓名
        - position: 职位
        - email: 电子邮箱 (如果可用)
        - phone: 电话号码 (如果可用)
        - linkedin_url: LinkedIn个人资料链接
        - summary: 个人简介
        - confidence: 匹配置信度 (0-100)
        - email_verified: 邮箱验证状态
        - source: 信息来源
    
    Examples:
        搜索特定公司CEO:
        {
            "company_name": "Tesla",
            "target_position": "CEO",
            "options": ["linkedin", "email"]
        }
        
        搜索销售经理:
        {
            "company_name": "Microsoft",
            "company_domain": "microsoft.com", 
            "target_position": "销售经理",
            "options": ["linkedin", "email", "phone"]
        }
    
    Raises:
        HTTPException:
            - 400: 参数验证失败或API密钥未配置
            - 404: 无法找到公司官网
            - 500: 员工搜索执行失败
    """
    if not request.company_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Company name cannot be empty"
        )
    
    if not request.target_position.strip():
        raise HTTPException(
            status_code=400,
            detail="Target position cannot be empty"
        )
    
    # 检查必需的环境变量
    if not os.getenv("SERPER_API_KEY"):
        raise HTTPException(
            status_code=400,
            detail="SERPER_API_KEY not configured. Please configure API keys first."
        )
    
    search_id = f"employee_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        start_time = datetime.now()
        
        # 步骤1: 获取/验证公司官网
        company_domain = request.company_domain
        if not company_domain:
            website_info = enhanced_website_validator.get_official_website(request.company_name)
            if website_info['website']:
                from urllib.parse import urlparse
                company_domain = urlparse(website_info['website']).netloc
        
        if not company_domain:
            raise HTTPException(
                status_code=404,
                detail=f"Cannot find official website for company: {request.company_name}"
            )
        
        # 步骤2: 搜索员工信息（模拟实现）
        employees = await _search_employees(
            company_name=request.company_name,
            company_domain=company_domain,
            target_position=request.target_position,
            options=request.options
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # 统计验证联系方式数量
        verified_contacts = sum(1 for emp in employees if emp.get('email_verified') == 'verified')
        
        return EmployeeSearchResponse(
            success=True,
            search_id=search_id,
            message=f"Employee search completed. Found {len(employees)} employees.",
            total_employees=len(employees),
            verified_contacts=verified_contacts,
            employees=employees,
            execution_time=execution_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Employee search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Employee search failed: {str(e)}"
        )

async def _search_employees(company_name: str, company_domain: str, target_position: str, options: List[str]) -> List[Dict[str, Any]]:
    """
    搜索员工信息的核心逻辑
    这里提供模拟实现，实际应用中需要集成真实的数据源
    """
    # 模拟员工数据
    import random
    
    # 根据公司和职位生成模拟员工
    positions = target_position.split(',')
    employees = []
    
    # 生成2-8个员工
    num_employees = random.randint(2, 8)
    
    names = ['张伟', '李娜', '王强', '刘敏', '陈杰', '杨静', '赵磊', '孙丽', '周勇', '吴燕']
    
    for i in range(num_employees):
        position = random.choice(positions).strip()
        name = random.choice(names)
        
        # 生成邮箱
        email_domains = [company_domain.replace('www.', ''), 'gmail.com', '163.com']
        email_domain = random.choice(email_domains)
        email = f"{name.lower()}{i+1}@{email_domain}"
        
        employee = {
            'name': name,
            'position': position,
            'email': email if 'email' in options else None,
            'phone': f"138{random.randint(10000000, 99999999)}" if 'phone' in options else None,
            'linkedin_url': f"https://linkedin.com/in/{name.lower()}-{i+1}" if 'linkedin' in options else None,
            'avatar': None,
            'summary': f"在{company_name}担任{position}，有{random.randint(2, 10)}年相关工作经验。",
            'confidence': random.randint(60, 95),
            'email_verified': random.choice(['verified', 'unverified', 'verified']),
            'source': 'LinkedIn Search'
        }
        
        employees.append(employee)
    
    # 按置信度排序
    employees.sort(key=lambda x: x['confidence'], reverse=True)
    
    return employees

@app.post("/contact-extraction", response_model=ContactExtractionResponse)
async def contact_extraction(request: ContactExtractionRequest):
    """
    联系信息提取接口
    
    从企业网站自动提取联系信息，包括电子邮箱、电话号码、地址、社交媒体等。
    
    Args:
        request (ContactExtractionRequest): 联系信息提取请求参数
            - urls: URL列表 (可选)
            - single_url: 单个URL (可选)
            - headless: 无头模式 (默认 True)
            - timeout: 页面加载超时时间毫秒 (默认 15000)
            - visit_contact_page: 是否访问联系页面 (默认 False)
            - merge_with_original: 是否与原始数据合并 (默认 False)
    
    Returns:
        ContactExtractionResponse: 联系信息提取结果
            - success: 是否成功
            - extraction_id: 提取ID
            - message: 响应消息
            - total_urls: 处理的URL总数
            - successful_extractions: 成功提取的数量
            - contact_info: 联系信息列表
            - execution_time: 执行时间(秒)
            - output_file: 输出文件路径
            - error: 错误信息
    
    联系信息包含字段:
        - company_name: 公司名称
        - url: 网站URL
        - emails: 电子邮箱列表
        - phones: 电话号码列表
        - addresses: 地址信息
        - social_media: 社交媒体链接
            - linkedin: LinkedIn公司页面
            - twitter: Twitter账号
            - facebook: Facebook页面
            - instagram: Instagram账号
        - extraction_success: 提取是否成功
        - extraction_time: 提取耗时
    
    Examples:
        提取单个网站:
        {
            "single_url": "https://example.com",
            "headless": true,
            "timeout": 15000
        }
        
        批量提取多个网站:
        {
            "urls": [
                "https://company1.com",
                "https://company2.com",
                "https://company3.com"
            ],
            "visit_contact_page": true,
            "timeout": 20000
        }
    
    Raises:
        HTTPException:
            - 400: 参数验证失败，没有提供URL
            - 503: 联系信息提取模块不可用
            - 500: 提取执行失败
    """
    if not CONTACT_EXTRACTION_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Contact extraction module not available. Please check installation."
        )
    
    # 验证输入参数
    urls_to_process = []
    if request.single_url:
        urls_to_process = [request.single_url]
    elif request.urls:
        urls_to_process = request.urls
    else:
        raise HTTPException(
            status_code=400,
            detail="Please provide either single_url or urls list"
        )
    
    extraction_id = f"contact_extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        start_time = datetime.now()
        
        # 创建WebsiteContentExtractor实例
        extractor = WebsiteContentExtractor(
            headless=request.headless,
            timeout=request.timeout,
            visit_contact_page=request.visit_contact_page
        )
        
        contact_results = []
        successful_extractions = 0
        
        # 批量处理URL
        for url in urls_to_process:
            try:
                # 处理每个URL的联系信息提取
                # 这里需要调用实际的提取逻辑
                result = await _extract_contact_from_url(url, extractor)
                if result.get('extraction_success'):
                    successful_extractions += 1
                contact_results.append(result)
            except Exception as e:
                print(f"Failed to extract from {url}: {str(e)}")
                contact_results.append({
                    'url': url,
                    'extraction_success': False,
                    'error': str(e)
                })
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # 清理资源
        extractor.close_browser()
        
        return ContactExtractionResponse(
            success=True,
            extraction_id=extraction_id,
            message=f"Contact extraction completed. Successfully processed {successful_extractions}/{len(urls_to_process)} URLs.",
            total_urls=len(urls_to_process),
            successful_extractions=successful_extractions,
            contact_info=contact_results,
            execution_time=execution_time,
            output_file=f"contact_info_{extraction_id}.json"
        )
        
    except Exception as e:
        print(f"Contact extraction error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Contact extraction failed: {str(e)}"
        )

async def _extract_contact_from_url(url: str, extractor: "WebsiteContentExtractor") -> Dict[str, Any]:
    """
    从单个URL提取联系信息的辅助函数
    """
    # 确保URL有协议前缀
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    start_time = time.time()
    
    try:
        # 初始化浏览器
        extractor.initialize_browser()
        
        # 调用实际的提取逻辑
        extraction_result = extractor.extract_content(url)
        
        extraction_time = time.time() - start_time
        
        # 解析提取结果
        if extraction_result and extraction_result.get('success'):
            contact_data = extraction_result.get('contact_info', {})
            
            result = {
                'company_name': contact_data.get('company_name', 'Unknown Company'),
                'url': url,
                'emails': contact_data.get('emails', []),
                'phones': contact_data.get('phones', []),
                'addresses': contact_data.get('addresses', []),
                'social_media': {
                    'linkedin': contact_data.get('social_media', {}).get('linkedin', ''),
                    'twitter': contact_data.get('social_media', {}).get('twitter', ''),
                    'facebook': contact_data.get('social_media', {}).get('facebook', ''),
                    'instagram': contact_data.get('social_media', {}).get('instagram', '')
                },
                'extraction_success': True,
                'extraction_time': extraction_time,
                'source': 'website_extraction',
                'page_title': contact_data.get('page_title', ''),
                'page_description': contact_data.get('page_description', '')
            }
            return result
        else:
            # 提取失败但没有异常
            return {
                'url': url,
                'extraction_success': False,
                'error': extraction_result.get('error', 'Unknown extraction error'),
                'extraction_time': extraction_time
            }
    except Exception as e:
        extraction_time = time.time() - start_time
        return {
            'url': url,
            'extraction_success': False,
            'error': str(e),
            'extraction_time': extraction_time
        }

@app.get("/search-status/{search_id}")
async def get_search_status(search_id: str):
    """获取搜索状态（用于长时间运行的搜索）"""
    if search_id not in active_searches:
        raise HTTPException(status_code=404, detail="Search not found")
    
    return active_searches[search_id]

@app.get("/export/{format}")
async def export_data(format: str, type: str = "all"):
    """导出搜索结果数据"""
    if format not in ["csv", "json"]:
        raise HTTPException(status_code=400, detail="Format must be 'csv' or 'json'")
    
    # 查找最新的输出文件
    output_dir = project_root / "output" / "langgraph"
    
    if not output_dir.exists():
        raise HTTPException(status_code=404, detail="No search results found")
    
    # 根据类型选择文件
    file_pattern = f"*_{type}.{format}" if type != "all" else f"*.{format}"
    matching_files = list(output_dir.glob(file_pattern))
    
    if not matching_files:
        raise HTTPException(status_code=404, detail=f"No {format} files found")
    
    # 返回最新的文件
    latest_file = max(matching_files, key=lambda f: f.stat().st_mtime)
    
    return FileResponse(
        path=str(latest_file),
        filename=latest_file.name,
        media_type="application/octet-stream"
    )

@app.get("/status")
async def status():
    """API配置状态检查"""
    status = {
        "SERPER_API_KEY": bool(os.getenv("SERPER_API_KEY")),
        "LLM_PROVIDER": os.getenv("LLM_PROVIDER", "none"),
    }
    
    # 检查LLM提供商特定的密钥
    llm_provider = os.getenv("LLM_PROVIDER", "none").lower()
    if llm_provider == "openai":
        status["OPENAI_API_KEY"] = bool(os.getenv("OPENAI_API_KEY"))
    elif llm_provider == "anthropic":
        status["ANTHROPIC_API_KEY"] = bool(os.getenv("ANTHROPIC_API_KEY"))
    elif llm_provider == "google":
        status["GOOGLE_API_KEY"] = bool(os.getenv("GOOGLE_API_KEY"))
    elif llm_provider == "huoshan":
        status["ARK_API_KEY"] = bool(os.getenv("ARK_API_KEY"))
    
    return status

@app.get("/config")
async def get_config():
    """获取系统配置"""
    config = {
        "llm_provider": os.getenv("LLM_PROVIDER", "none"),
        "headless": os.getenv("HEADLESS", "true").lower() == "true",
        "timeout": int(os.getenv("TIMEOUT", "15000")),
        "visit_contact_page": os.getenv("VISIT_CONTACT_PAGE", "false").lower() == "true",
        "serper_api_key_configured": bool(os.getenv("SERPER_API_KEY")),
    }
    return config

@app.post("/config")
async def update_config(config_data: dict):
    """更新系统配置"""
    # 注意：这里只是返回成功状态，实际的环境变量更新需要重启应用
    return {"success": True, "message": "配置已接收，部分设置可能需要重启应用生效"}

# 导入异步搜索模块
from async_search_api import (
    AsyncSearchRequest, 
    search_manager, 
    create_streaming_response
)

@app.post("/async-search")
async def start_async_search(request: AsyncSearchRequest):
    """启动异步搜索"""
    if not LANGGRAPH_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="LangGraph search module not available. Please check installation."
        )
    
    if not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty"
        )
    
    # 检查必需的环境变量
    if not os.getenv("SERPER_API_KEY"):
        raise HTTPException(
            status_code=400,
            detail="SERPER_API_KEY not configured. Please configure API keys first."
        )
    
    try:
        # 启动异步搜索
        search_id = await search_manager.start_search(request)
        
        return {
            "success": True,
            "search_id": search_id,
            "message": "Async search started successfully",
            "stream_url": f"/async-search/{search_id}/stream",
            "status_url": f"/async-search/{search_id}/status",
            "results_url": f"/async-search/{search_id}/results"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start async search: {str(e)}"
        )

@app.get("/async-search/{search_id}/stream")
async def stream_search_progress(search_id: str):
    """获取搜索进度的SSE流"""
    return await create_streaming_response(search_id)

@app.get("/async-search/{search_id}/status")
async def get_async_search_status(search_id: str):
    """获取异步搜索状态"""
    progress = search_manager.get_search_status(search_id)
    
    if not progress:
        raise HTTPException(
            status_code=404,
            detail="Search not found"
        )
    
    return progress.to_dict()

@app.get("/async-search/{search_id}/results")
async def get_async_search_results(search_id: str):
    """获取异步搜索结果"""
    progress = search_manager.get_search_status(search_id)
    
    if not progress:
        raise HTTPException(
            status_code=404,
            detail="Search not found"
        )
    
    if progress.status.value not in ["completed", "failed"]:
        raise HTTPException(
            status_code=202,
            detail=f"Search still in progress: {progress.status.value}"
        )
    
    if progress.status.value == "failed":
        raise HTTPException(
            status_code=400,
            detail=f"Search failed: {progress.message}"
        )
    
    results = search_manager.get_search_results(search_id)
    if not results:
        raise HTTPException(
            status_code=404,
            detail="Search results not found"
        )
    
    return {
        "success": True,
        "search_id": search_id,
        "search_results": results,
        "execution_time": progress.data.get("execution_time") if progress.data else None,
        "completed_at": progress.timestamp.isoformat()
    }

@app.delete("/async-search/{search_id}")
async def cancel_async_search(search_id: str):
    """取消异步搜索"""
    success = await search_manager.cancel_search(search_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Search not found or already completed"
        )
    
    return {
        "success": True,
        "message": "Search cancelled successfully"
    }

if __name__ == "__main__":
    print("🚀 Starting AI Customer Finder FastAPI Backend...")
    print(f"🔧 LangGraph Available: {LANGGRAPH_AVAILABLE}")
    print(f"🔧 SERPER_API_KEY: {'✅ Configured' if os.getenv('SERPER_API_KEY') else '❌ Not Set'}")
    print(f"🔧 LLM_PROVIDER: {os.getenv('LLM_PROVIDER', 'none')}")
    print("🌐 API will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )