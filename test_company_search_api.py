#!/usr/bin/env python3
"""
测试公司搜索API是否返回正确的加拿大结果
"""
import requests
import json

def test_company_search_canada():
    """测试搜索新能源汽车+加拿大是否返回加拿大公司"""
    
    print("🚀 测试公司搜索API - 新能源汽车 + 加拿大")
    
    # API请求数据
    search_data = {
        "industry": "新能源汽车",
        "region": "加拿大", 
        "search_type": "general",
        "use_llm_optimization": True,
        "max_results": 10
    }
    
    api_url = "http://localhost:8000/api/company/search"
    
    try:
        print(f"📡 发送请求到: {api_url}")
        print(f"📋 请求参数: {json.dumps(search_data, ensure_ascii=False)}")
        
        response = requests.post(
            api_url,
            json=search_data,
            timeout=60  # 增加到60秒
        )
        
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ API调用成功!")
            print(f"🔍 搜索ID: {result.get('search_id')}")
            print(f"📈 找到公司数量: {result.get('total_found')}")
            print(f"⏱️ 执行时间: {result.get('execution_time', 0):.2f}秒")
            
            # 检查搜索参数优化
            if 'search_params' in result:
                params = result['search_params']
                print(f"🌍 国家代码: {params.get('country_code')}")
                print(f"🏷️ 行业: {params.get('industry')}")
                print(f"📍 地区: {params.get('region')}")
            
            # 检查优化信息
            if 'optimization_info' in result:
                opt_info = result['optimization_info']
                print(f"🧠 LLM优化: {opt_info.get('optimization_applied')}")
                print(f"🔧 优化方式: {opt_info.get('method')}")
                print(f"🤖 分析公司数: {opt_info.get('companies_analyzed', 0)}")
            
            # 检查公司结果
            companies = result.get('companies', [])
            if companies:
                print(f"\n🏢 公司列表:")
                canada_count = 0
                for i, company in enumerate(companies[:5], 1):  # 只显示前5个
                    location = company.get('location', '')
                    name = company.get('name', '未知公司')
                    
                    # 检查是否是加拿大公司
                    is_canada = any(keyword in location.lower() for keyword in ['canada', 'canadian', 'toronto', 'vancouver', 'montreal', 'calgary', 'ottawa'])
                    if is_canada:
                        canada_count += 1
                        location_flag = "🇨🇦"
                    else:
                        location_flag = "🌍"
                    
                    print(f"     {i}. {location_flag} {name}")
                    print(f"        📍 位置: {location}")
                    
                    # AI分析信息
                    if company.get('ai_score') is not None:
                        print(f"        🤖 AI评分: {company.get('ai_score', 0):.2f}")
                        print(f"        💭 AI原因: {company.get('ai_reason', 'N/A')[:80]}...")
                    
                    print()
                
                print(f"🇨🇦 加拿大公司数量: {canada_count}/{len(companies)}")
                
                if canada_count > 0:
                    print(f"✅ 成功返回加拿大公司!")
                    return True
                else:
                    print(f"❌ 未找到加拿大公司，可能需要调整搜索策略")
                    return False
            else:
                print(f"❌ 没有找到任何公司")
                return False
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
    success = test_company_search_canada()
    if success:
        print(f"\n🎉 公司搜索API工作正常，能够返回加拿大公司!")
    else:
        print(f"\n💥 公司搜索API有问题，需要进一步调试")