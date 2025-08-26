#!/usr/bin/env python3
"""
测试新架构的API
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.main import app
import uvicorn

if __name__ == "__main__":
    print("🚀 启动新架构测试服务...")
    
    # 检查环境
    serper_key = os.getenv("SERPER_API_KEY")
    print(f"SERPER_API_KEY: {'✅ 配置' if serper_key else '❌ 未配置'}")
    
    llm_provider = os.getenv("LLM_PROVIDER", "none")
    print(f"LLM_PROVIDER: {llm_provider}")
    
    print("\n🏗️ 新架构模块:")
    print("   📁 /api/company - 公司搜索") 
    print("   📁 /api/employee - 员工搜索")
    print("   📁 /api/intelligent - 智能搜索")
    print("\n🌐 服务地址: http://localhost:8002")
    print("📚 API文档: http://localhost:8002/docs")
    print("-" * 50)
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0", 
            port=8002,
            log_level="info",
            reload=False  # 测试时关闭重载
        )
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")
        sys.exit(1)