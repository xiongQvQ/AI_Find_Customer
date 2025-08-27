#!/usr/bin/env python3
"""
测试员工搜索API的完整功能
"""
import requests
import json

def test_employee_search():
    """测试员工搜索API是否包含AI分析"""
    
    print("🚀 测试员工搜索API - 包含AI分析")
    
    # API请求数据
    search_data = {
        "company_name": "特斯拉",
        "company_domain": "tesla.com",
        "target_positions": ["CTO", "技术总监", "软件工程师"],
        "search_options": ["linkedin", "email", "phone"],
        "country_code": "us",
        "max_results": 5,
        "use_llm_optimization": True
    }
    
    api_url = "http://localhost:8000/api/employee/search"
    
    try:
        print(f"📡 发送请求到: {api_url}")
        print(f"📋 请求参数: {json.dumps(search_data, ensure_ascii=False, indent=2)}")
        
        response = requests.post(
            api_url,
            json=search_data,
            timeout=60
        )
        
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ API调用成功!")
            print(f"🔍 搜索ID: {result.get('search_id')}")
            print(f"📈 找到员工数量: {result.get('total_found')}")
            print(f"✅ 验证联系方式数: {result.get('verified_contacts')}")
            print(f"⏱️ 执行时间: {result.get('execution_time', 0):.2f}秒")
            
            # 检查员工结果
            employees = result.get('employees', [])
            if employees:
                print(f"\n👥 员工列表:")
                for i, employee in enumerate(employees, 1):
                    print(f"  {i}. {employee.get('name')} - {employee.get('position')}")
                    print(f"     📧 邮箱: {employee.get('email', 'N/A')} ({employee.get('email_verified', 'unknown')})")
                    print(f"     📞 电话: {employee.get('phone', 'N/A')}")
                    print(f"     🔗 LinkedIn: {'是' if employee.get('linkedin_url') else '否'}")
                    print(f"     📍 位置: {employee.get('location', 'N/A')}")
                    print(f"     💼 经验: {employee.get('experience_years', 'N/A')}年")
                    
                    # 检查AI分析字段
                    if employee.get('ai_score') is not None:
                        print(f"     🤖 AI评分: {employee.get('ai_score', 0):.2f}")
                        print(f"     💭 AI分析: {employee.get('ai_reason', 'N/A')}")
                        print(f"     📊 相关性: {employee.get('relevance_score', 0):.2f}")
                        print(f"     🎯 分析置信度: {employee.get('analysis_confidence', 0):.2f}")
                        print(f"     ✨ AI分析: ✅ 已包含")
                    else:
                        print(f"     ❌ AI分析: 未包含")
                    
                    print(f"     📋 数据源: {employee.get('source', 'N/A')}")
                    print()
                
                # 检查AI分析覆盖率
                ai_analyzed = sum(1 for emp in employees if emp.get('ai_score') is not None)
                print(f"🧠 AI分析覆盖率: {ai_analyzed}/{len(employees)} ({ai_analyzed/len(employees)*100:.1f}%)")
                
                if ai_analyzed > 0:
                    print(f"✅ 员工搜索AI分析功能正常工作!")
                    return True
                else:
                    print(f"❌ 员工搜索缺少AI分析功能")
                    return False
            else:
                print(f"❌ 没有找到任何员工")
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
    success = test_employee_search()
    if success:
        print(f"\n🎉 员工搜索API（包含AI分析）工作正常!")
    else:
        print(f"\n💥 员工搜索API有问题，需要进一步调试")