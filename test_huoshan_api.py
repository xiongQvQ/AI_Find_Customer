#!/usr/bin/env python3
"""
测试火山引擎API调用
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_huoshan_api():
    """测试火山引擎API是否可用"""
    
    api_key = os.getenv("ARK_API_KEY")
    base_url = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    model = os.getenv("ARK_MODEL", "doubao-seed-1-6-250615")
    
    print(f"🚀 测试火山引擎API")
    print(f"   API Key: {api_key[:20]}..." if api_key else "未配置")
    print(f"   Base URL: {base_url}")
    print(f"   Model: {model}")
    
    if not api_key:
        print("❌ 未配置ARK_API_KEY")
        return False
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user", 
                "content": "你好，请用中文回答：什么是人工智能？"
            }
        ],
        "temperature": 0.3,
        "max_tokens": 100
    }
    
    try:
        print(f"📡 发送请求到: {base_url}/chat/completions")
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            print(f"✅ API调用成功!")
            print(f"🤖 响应内容: {content[:100]}...")
            return True
        else:
            print(f"❌ API调用失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except Exception as e:
        print(f"❌ API调用异常: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_huoshan_api()
    if success:
        print(f"\n🎉 火山引擎API配置正确，可以使用!")
    else:
        print(f"\n💥 火山引擎API配置有问题，需要检查")