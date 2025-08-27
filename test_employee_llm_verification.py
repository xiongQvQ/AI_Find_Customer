#!/usr/bin/env python3
"""
员工搜索LLM关键词生成功能验证脚本
"""
import os
import sys
import asyncio
import traceback
from pathlib import Path

# 添加项目根目录到系统路径
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

async def test_employee_llm_keyword_generation():
    """测试员工搜索的LLM关键词生成功能"""
    print("🧪 测试员工搜索LLM关键词生成功能...")
    
    try:
        # 导入LLM关键词生成器
        from core.llm_keyword_generator import LLMKeywordGenerator
        
        # 创建生成器实例
        generator = LLMKeywordGenerator()
        print(f"✅ LLM提供商: {generator.llm_provider}")
        print(f"✅ 客户端状态: {'可用' if generator.client else '不可用'}")
        
        # 测试员工搜索关键词生成
        test_cases = [
            {
                "context": "CEO at Tesla",
                "country": "us",
                "description": "在美国搜索Tesla的CEO"
            },
            {
                "context": "销售经理 at 比亚迪",
                "country": "cn", 
                "description": "在中国搜索比亚迪的销售经理"
            },
            {
                "context": "Software Engineer at Microsoft",
                "country": "ca",
                "description": "在加拿大搜索微软的软件工程师"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📋 测试用例 {i}: {test_case['description']}")
            print(f"   搜索上下文: {test_case['context']}")
            print(f"   目标国家: {test_case['country']}")
            
            try:
                # 调用关键词生成
                result = generator.generate_search_keywords(
                    industry=test_case['context'],
                    target_country=test_case['country'],
                    search_type="linkedin"
                )
                
                if result.get('success'):
                    print(f"   ✅ 生成成功")
                    print(f"   🎯 主关键词: {result.get('primary_keywords', [])[:3]}")
                    print(f"   🔄 备选关键词: {result.get('alternative_keywords', [])[:3]}")
                    print(f"   📡 生成方式: {result.get('generated_by', 'unknown')}")
                    print(f"   🌍 国家参数: {result.get('serper_params', {}).get('gl', 'N/A')}")
                    
                    if result.get('explanation'):
                        print(f"   💡 策略说明: {result.get('explanation')[:100]}...")
                else:
                    print(f"   ❌ 生成失败: {result.get('error', '未知错误')}")
                    
            except Exception as e:
                print(f"   ❌ 测试异常: {str(e)}")
                traceback.print_exc()
    
    except ImportError as e:
        print(f"❌ 导入LLM关键词生成器失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试过程异常: {e}")
        traceback.print_exc()
        return False
    
    return True

async def test_employee_service_integration():
    """测试员工搜索服务的LLM集成"""
    print("\n🔧 测试员工搜索服务LLM集成...")
    
    try:
        # 导入员工搜索服务
        from api.services.employee_service import EmployeeSearchService
        from api.models.requests import EmployeeSearchRequest
        
        # 创建服务实例
        service = EmployeeSearchService()
        print(f"✅ 员工搜索器状态: {'可用' if service.searcher else '不可用(使用模拟数据)'}")
        print(f"✅ LLM关键词生成器状态: {'可用' if service.keyword_generator else '不可用'}")
        
        # 创建测试请求
        test_request = EmployeeSearchRequest(
            company_name="Tesla",
            target_positions=["CEO", "CTO"],
            country_code="us",
            max_results=5,
            search_options=["linkedin", "email"],
            verify_emails=False
        )
        
        print(f"\n📋 测试员工搜索请求:")
        print(f"   公司名称: {test_request.company_name}")
        print(f"   目标职位: {test_request.target_positions}")
        print(f"   国家代码: {test_request.country_code}")
        
        # 执行搜索
        result = await service.search_employees(test_request)
        
        if result.success:
            print(f"   ✅ 搜索成功")
            print(f"   👥 找到员工数量: {result.total_found}")
            print(f"   📧 验证联系数量: {result.verified_contacts}")
            print(f"   ⏱️ 执行时间: {result.execution_time:.2f}秒")
            
            # 显示前3个员工信息
            for i, employee in enumerate(result.employees[:3], 1):
                print(f"   员工 {i}: {employee.name} - {employee.position}")
                print(f"      LinkedIn: {employee.linkedin_url or 'N/A'}")
                print(f"      邮箱: {employee.email or 'N/A'}")
                print(f"      置信度: {employee.confidence_score:.2f}")
        else:
            print(f"   ❌ 搜索失败: {result.message}")
            if result.error:
                print(f"   错误详情: {result.error}")
                
    except Exception as e:
        print(f"❌ 服务集成测试异常: {e}")
        traceback.print_exc()
        return False
    
    return True

async def test_llm_keyword_optimization():
    """测试LLM关键词优化功能"""
    print("\n🧠 测试LLM关键词优化功能...")
    
    try:
        from api.services.employee_service import EmployeeSearchService
        from api.models.requests import EmployeeSearchRequest
        
        service = EmployeeSearchService()
        
        # 测试不同的优化场景
        test_cases = [
            {
                "company": "Apple", 
                "positions": ["VP of Engineering"],
                "country": "us"
            },
            {
                "company": "阿里巴巴",
                "positions": ["产品经理", "技术总监"], 
                "country": "cn"
            },
            {
                "company": "SAP",
                "positions": ["Sales Director"],
                "country": "de"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📋 优化测试 {i}: {test_case['company']} in {test_case['country'].upper()}")
            
            # 创建请求对象
            request = EmployeeSearchRequest(
                company_name=test_case['company'],
                target_positions=test_case['positions'],
                country_code=test_case['country'],
                max_results=10,
                search_options=["linkedin"],
                verify_emails=False
            )
            
            # 调用内部优化方法
            optimized_params = await service._optimize_search_params(request)
            
            print(f"   ✅ 优化完成")
            print(f"   🎯 增强职位: {optimized_params.get('enhanced_positions', [])}")
            print(f"   🔑 生成关键词: {optimized_params.get('keywords', [])}")
            print(f"   🌍 国家代码: {optimized_params.get('country_code', 'N/A')}")
            print(f"   📍 位置信息: {optimized_params.get('location', 'N/A')}")
            
    except Exception as e:
        print(f"❌ 关键词优化测试异常: {e}")
        traceback.print_exc()
        return False
        
    return True

async def main():
    """主测试函数"""
    print("🚀 开始员工搜索LLM功能全面验证...")
    
    # 检查环境变量
    print(f"📊 环境信息:")
    print(f"   LLM_PROVIDER: {os.getenv('LLM_PROVIDER', 'none')}")
    print(f"   API配置状态:")
    
    api_keys = {
        'OPENAI_API_KEY': bool(os.getenv('OPENAI_API_KEY')),
        'ANTHROPIC_API_KEY': bool(os.getenv('ANTHROPIC_API_KEY')), 
        'GOOGLE_API_KEY': bool(os.getenv('GOOGLE_API_KEY')),
        'ARK_API_KEY': bool(os.getenv('ARK_API_KEY'))
    }
    
    for key, status in api_keys.items():
        print(f"   {key}: {'✅ 已配置' if status else '❌ 未配置'}")
    
    success_count = 0
    total_tests = 3
    
    # 执行测试
    if await test_employee_llm_keyword_generation():
        success_count += 1
    
    if await test_employee_service_integration():
        success_count += 1
        
    if await test_llm_keyword_optimization():
        success_count += 1
    
    print(f"\n📈 测试完成统计:")
    print(f"   总测试数: {total_tests}")
    print(f"   成功数: {success_count}")
    print(f"   失败数: {total_tests - success_count}")
    print(f"   成功率: {success_count/total_tests*100:.1f}%")
    
    if success_count == total_tests:
        print("🎉 所有测试通过! 员工搜索LLM功能正常")
    else:
        print("⚠️ 部分测试失败，请检查配置和代码")
    
    return success_count == total_tests

if __name__ == "__main__":
    asyncio.run(main())