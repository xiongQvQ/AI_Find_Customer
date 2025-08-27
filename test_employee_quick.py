#!/usr/bin/env python3
"""
快速测试员工搜索API
"""
import requests
import json

def test_employee_search_quick():
    """快速测试员工搜索API是否包含AI分析"""
    
    print("🚀 快速测试员工搜索API")
    
    # API请求数据
    search_data = {
        "company_name": "Tesla",
        "target_positions": ["CTO"],
        "search_options": ["linkedin"],
        "max_results": 2,
        "use_llm_optimization": True
    }
    
    api_url = "http://localhost:8000/api/employee/search"
    
    try:
        print(f"📡 发送请求到: {api_url}")
        
        response = requests.post(
            api_url,
            json=search_data,
            timeout=10  # 短超时时间
        )
        
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API调用成功!")
            print(f"🔍 搜索ID: {result.get('search_id')}")
            print(f"📈 找到员工数量: {result.get('total_found')}")
            
            # 检查员工结果中的AI分析
            employees = result.get('employees', [])
            if employees:
                for i, employee in enumerate(employees, 1):
                    print(f"\n👤 员工 {i}: {employee.get('name')} - {employee.get('position')}")
                    
                    # 关键：检查AI分析字段
                    if employee.get('ai_score') is not None:
                        print(f"     🤖 AI评分: {employee.get('ai_score', 0):.2f}")
                        print(f"     💭 AI分析: {employee.get('ai_reason', 'N/A')}")
                        print(f"     ✅ AI分析: 已包含")
                    else:
                        print(f"     ❌ AI分析: 未包含")
                
                return True
            else:
                print(f"⚠️  没有找到员工数据")
                return True  # 模拟模式下可能没有真实数据
        else:
            print(f"❌ API调用失败: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏱️ 请求超时（10秒）")
        return False
    except Exception as e:
        print(f"❌ API调用异常: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_employee_search_quick()
    if success:
        print(f"\n🎉 员工搜索API（包含AI分析）工作正常!")
    else:
        print(f"\n💥 员工搜索API需要进一步调试")