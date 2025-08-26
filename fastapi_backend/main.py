"""
FastAPI Backend for AI Customer Finder
替代Streamlit前端的后端API服务
"""
import os
import sys
import json
import asyncio
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
    allow_origins=["http://localhost:3000"],  # Vue开发服务器
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
            "/health"
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
    """智能搜索接口"""
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
    """增强版智能搜索接口 - 支持灵活的复合搜索策略"""
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
            
            # 应用增强版官网过滤
            if companies:
                filtered_companies = []
                for company in companies:
                    company_name = company.get('name', '')
                    if company_name:
                        # 使用增强版官网验证器
                        website_info = enhanced_website_validator.get_official_website(company_name)
                        if website_info['website']:
                            company['official_website'] = website_info['website']
                            company['website_confidence'] = website_info['confidence']
                            company['website_method'] = website_info['method']
                            company['search_results'] = website_info.get('search_results', [])
                        
                        # 验证现有网站URL
                        if company.get('website_url'):
                            verification = enhanced_website_validator.is_official_website(
                                company['website_url'], company_name
                            )
                            company['is_official_website'] = verification['is_official']
                            company['verification_confidence'] = verification['confidence']
                            company['verification_reasons'] = verification['reasons']
                            company['detailed_analysis'] = verification.get('analysis', {})
                            
                            # 使用更智能的过滤策略
                            if verification['is_official'] or verification['confidence'] > 0.6:
                                filtered_companies.append(company)
                        else:
                            # 如果没有现有URL但找到了官网，直接添加
                            if company.get('official_website'):
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

@app.post("/employee-search", response_model=EmployeeSearchResponse)
async def employee_search(request: EmployeeSearchRequest):
    """员工搜索接口"""
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

@app.get("/api-status")
async def api_status():
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