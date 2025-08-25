#!/usr/bin/env python3
"""
快速修复LLM连接问题
将鲁棒性客户端集成到现有系统中
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

def apply_llm_fixes():
    """应用LLM连接修复"""
    print("🔧 正在应用LLM连接修复...")
    
    # 方案1: 修改LLM客户端以增加重试机制
    llm_client_path = Path(__file__).parent / "langgraph_search" / "llm" / "llm_client.py"
    
    if llm_client_path.exists():
        print("📝 更新LLM客户端...")
        
        # 读取现有内容
        with open(llm_client_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已经有重试机制
        if "import time" not in content:
            # 添加重试导入
            import_section = "import time\nimport random\nfrom functools import wraps\n"
            content = import_section + content
        
        # 添加重试装饰器
        if "def with_retry" not in content:
            retry_code = '''
def with_retry(max_retries=3, base_delay=1.0, max_delay=30.0):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    error_msg = str(e).lower()
                    
                    # 检查是否是可重试的错误
                    retryable_errors = [
                        "connection error", "timeout", "connection aborted",
                        "connection refused", "network is unreachable",
                        "temporary failure", "service unavailable",
                        "rate limit", "too many requests"
                    ]
                    
                    is_retryable = any(error in error_msg for error in retryable_errors)
                    
                    if attempt == max_retries or not is_retryable:
                        break
                    
                    # 指数退避
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    delay = delay * (0.5 + random.random() * 0.5)  # 添加抖动
                    
                    print(f"🔄 LLM调用失败，{delay:.1f}秒后重试 (第{attempt+1}次): {e}")
                    time.sleep(delay)
            
            print(f"❌ LLM调用最终失败: {last_error}")
            raise last_error
        return wrapper
    return decorator

'''
            # 在类定义之前插入重试装饰器
            if "class LLMClient" in content:
                content = content.replace("class LLMClient", retry_code + "class LLMClient")
        
        # 为关键方法添加重试装饰器
        if "@with_retry" not in content:
            content = content.replace(
                "def call_llm(",
                "@with_retry(max_retries=5, base_delay=1.0, max_delay=16.0)\n    def call_llm("
            )
            content = content.replace(
                "def generate_response(",  
                "@with_retry(max_retries=3, base_delay=2.0)\n    def generate_response("
            )
        
        # 写回文件
        with open(llm_client_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ LLM客户端已更新，添加重试机制")
    else:
        print("⚠️ LLM客户端文件未找到")
    
    print("\n🔧 应用环境变量检查...")
    
    # 方案2: 创建环境变量检查函数
    env_check_code = '''
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
'''
    
    # 写入配置检查文件
    config_check_path = Path(__file__).parent / "check_llm_config.py"
    with open(config_check_path, 'w', encoding='utf-8') as f:
        f.write(env_check_code)
    
    print("✅ 创建了LLM配置检查工具")
    
    print("\n🚀 修复应用完成！")
    print("建议：重启Streamlit应用以应用修复")

if __name__ == "__main__":
    apply_llm_fixes()