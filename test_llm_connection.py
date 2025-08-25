#!/usr/bin/env python3
"""简单的LLM连接测试脚本"""

import os
from dotenv import load_dotenv
load_dotenv()

def test_huoshan_llm():
    """测试火山引擎LLM"""
    try:
        import requests
        
        api_key = os.getenv("ARK_API_KEY")
        base_url = os.getenv("ARK_BASE_URL")
        model = os.getenv("ARK_MODEL")
        
        if not all([api_key, base_url, model]):
            return False, "配置不完整"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 20
        }
        
        response = requests.post(
            f"{base_url}/chat/completions",
            json=data,
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            return True, "连接成功"
        else:
            return False, f"HTTP {response.status_code}: {response.text[:100]}"
            
    except Exception as e:
        return False, f"错误: {e}"

if __name__ == "__main__":
    success, message = test_huoshan_llm()
    print(f"🧪 LLM连接测试: {'✅ 成功' if success else '❌ 失败'}")
    print(f"   详情: {message}")
