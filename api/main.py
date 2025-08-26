"""
AI Customer Finder - 重构版FastAPI后端
清晰的模块化架构：公司搜索 | 员工搜索 | 智能搜索
"""
import os
import sys
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 导入路由模块
from api.routers import company_router, employee_router, intelligent_router
from api.models.responses import HealthResponse

load_dotenv()

# 创建FastAPI应用
app = FastAPI(
    title="AI Customer Finder API",
    description="模块化的客户发现API - 公司搜索 | 员工搜索 | 智能搜索",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由模块
app.include_router(company_router.router, prefix="/api/company", tags=["公司搜索"])
app.include_router(employee_router.router, prefix="/api/employee", tags=["员工搜索"]) 
app.include_router(intelligent_router.router, prefix="/api/intelligent", tags=["智能搜索"])

@app.get("/", response_model=dict)
async def root():
    """API根路径"""
    return {
        "message": "AI Customer Finder API v2.0",
        "version": "2.0.0",
        "architecture": "模块化架构",
        "modules": {
            "company_search": "/api/company",
            "employee_search": "/api/employee", 
            "intelligent_search": "/api/intelligent"
        },
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查接口"""
    # 检查环境变量
    env_status = {
        "SERPER_API_KEY": bool(os.getenv("SERPER_API_KEY")),
        "LLM_PROVIDER": os.getenv("LLM_PROVIDER", "none"),
    }
    
    # 检查LLM提供商配置
    llm_provider = os.getenv("LLM_PROVIDER", "none").lower()
    if llm_provider == "openai":
        env_status["OPENAI_API_KEY"] = bool(os.getenv("OPENAI_API_KEY"))
    elif llm_provider == "anthropic":
        env_status["ANTHROPIC_API_KEY"] = bool(os.getenv("ANTHROPIC_API_KEY"))
    elif llm_provider == "google":
        env_status["GOOGLE_API_KEY"] = bool(os.getenv("GOOGLE_API_KEY"))
    elif llm_provider == "huoshan":
        env_status["ARK_API_KEY"] = bool(os.getenv("ARK_API_KEY"))
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        environment=env_status,
        modules={
            "company_search": "available",
            "employee_search": "available", 
            "intelligent_search": "available"
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": f"Internal server error: {str(exc)}",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 启动 AI Customer Finder API v2.0...")
    print(f"🔧 SERPER_API_KEY: {'✅ 已配置' if os.getenv('SERPER_API_KEY') else '❌ 未设置'}")
    print(f"🔧 LLM_PROVIDER: {os.getenv('LLM_PROVIDER', 'none')}")
    print("🏗️ 架构模块:")
    print("   📁 /api/company - 公司搜索")
    print("   📁 /api/employee - 员工搜索") 
    print("   📁 /api/intelligent - 智能搜索")
    print("🌐 API文档: http://localhost:8000/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )