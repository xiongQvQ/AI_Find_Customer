#!/usr/bin/env python3
"""
直接测试火山引擎API连接
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_huoshan_api():
    """测试火山引擎API是否可以正常调用"""
    
    print("🔥 测试火山引擎API连接")
    
    # 从环境变量获取配置
    api_key = os.getenv("ARK_API_KEY")
    base_url = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    model_name = os.getenv("ARK_MODEL", "doubao-seed-1-6-250615")
    
    print(f"🔧 配置信息:")
    print(f"   API Key: {api_key[:10]}...{api_key[-4:] if api_key else 'None'}")
    print(f"   Base URL: {base_url}")
    print(f"   Model: {model_name}")
    
    if not api_key:
        print("❌ ARK_API_KEY 未配置")
        return False
    
    # 构建请求
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": "请生成3个关于新能源汽车在美国的搜索关键词，用JSON格式返回"}
        ],
        "temperature": 0.3,
        "max_tokens": 200
    }
    
    url = f"{base_url}/chat/completions"
    
    print(f"\n📡 发送请求到: {url}")
    print(f"📋 请求负载: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    
    try:
        # 使用较短的超时时间测试
        print("⏱️ 开始调用API (超时10秒)...")
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=10  # 短超时
        )
        
        print(f"📊 响应状态码: {response.status_code}")
        print(f"📄 响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API调用成功!")
            print(f"📝 响应内容:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return True
        else:
            print(f"❌ API调用失败: {response.status_code}")
            print(f"错误响应: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时 (10秒)")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 连接错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

if __name__ == "__main__":
    success = test_huoshan_api()
    if success:
        print("\n🎉 火山引擎API连接正常!")
    else:
        print("\n💥 火山引擎API连接失败，需要检查配置或网络")