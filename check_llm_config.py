
def check_llm_config():
    """检查LLM配置"""
    import os
    from dotenv import load_dotenv
    
    # 确保加载环境变量
    load_dotenv()
    
    provider = os.getenv("LLM_PROVIDER", "none").lower()
    
    if provider == "huoshan":
        required = ["ARK_API_KEY", "ARK_BASE_URL", "ARK_MODEL"]
        missing = [var for var in required if not os.getenv(var)]
        if missing:
            print(f"❌ 火山引擎配置缺失: {missing}")
            return False
    elif provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ OpenAI API密钥未设置")
            return False
    
    return True
