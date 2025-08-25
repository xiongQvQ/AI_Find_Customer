
# 在应用启动时添加以下代码确保环境变量正确加载
import os
from dotenv import load_dotenv
from pathlib import Path

def ensure_env_loaded():
    """确保环境变量正确加载"""
    # 加载.env文件
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)
    
    # 验证关键变量
    required_vars = ["SERPER_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️ 缺少环境变量: {', '.join(missing_vars)}")
        return False
    
    return True

# 调用检查
if not ensure_env_loaded():
    print("❌ 环境变量加载失败，请检查.env文件")
