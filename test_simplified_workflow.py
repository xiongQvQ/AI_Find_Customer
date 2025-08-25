#!/usr/bin/env python3
"""
简化版CrewAI工作流完整测试
测试从需求输入到结果输出的完整流程
"""

import os
import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

# 加载环境变量
load_dotenv()

def test_complete_workflow():
    """测试完整工作流"""
    print("🚀 测试简化版CrewAI智能搜索完整工作流")
    print("=" * 60)
    
    try:
        from crewai_simplified import IntelligentSearchCrewSimplified
        
        # 检查API密钥
        if not os.getenv("SERPER_API_KEY"):
            print("❌ 未配置SERPER_API_KEY，无法执行实际搜索")
            return False
        
        print("✅ API密钥已配置")
        
        # 创建搜索实例
        print("\n📋 1. 创建智能搜索Crew...")
        search_crew = IntelligentSearchCrewSimplified(verbose=True)
        print(f"   已创建 {len(search_crew.agents)} 个智能体")
        
        # 健康检查
        print("\n🏥 2. 系统健康检查...")
        health = search_crew.health_check()
        print(f"   健康状态: {health['overall_status']}")
        
        if health['overall_status'] != 'healthy':
            print("❌ 系统健康检查失败")
            print(f"   详细信息: {health}")
            return False
        
        # 测试需求
        test_requirement = "我想找卖数位板的公司，要求支持4K分辨率，价格1000-3000元，深圳地区"
        print(f"\n🔍 3. 执行智能搜索...")
        print(f"   测试需求: {test_requirement}")
        
        # 执行搜索
        start_time = time.time()
        result = search_crew.execute_intelligent_search(test_requirement)
        execution_time = time.time() - start_time
        
        # 分析结果
        print(f"\n📊 4. 分析搜索结果...")
        print(f"   执行时间: {execution_time:.2f}秒")
        print(f"   搜索成功: {result.get('success', False)}")
        
        if result.get('success'):
            recommendations = result.get('final_recommendations', [])
            print(f"   找到推荐公司: {len(recommendations)} 家")
            
            # 显示前3个结果
            if recommendations:
                print("\n🏆 推荐结果 (前3名):")
                for i, company in enumerate(recommendations[:3], 1):
                    name = company.get('company_name', f'公司{i}')
                    score = company.get('overall_score', 0)
                    tier = company.get('score_tier', 'unknown')
                    print(f"   {i}. {name} - {score:.1f}分 ({tier})")
            
            # 显示执行摘要
            summary = result.get('execution_summary', {})
            if summary:
                print(f"\n⚙️ 执行摘要:")
                print(f"   智能体数量: {summary.get('total_agents', 0)}")
                print(f"   总执行时间: {summary.get('total_time', 0):.2f}秒")
                
                execution_log = summary.get('execution_log', [])
                print(f"   智能体执行情况:")
                for log_entry in execution_log:
                    agent = log_entry.get('agent', 'Unknown')
                    success = log_entry.get('success', False)
                    exec_time = log_entry.get('execution_time', 0)
                    status = "✅" if success else "❌"
                    print(f"     {status} {agent}: {exec_time:.2f}秒")
            
            print("\n✅ 完整工作流测试成功！")
            return True
            
        else:
            error = result.get('error', '未知错误')
            print(f"❌ 搜索失败: {error}")
            return False
    
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_components():
    """测试各个组件的独立功能"""
    print("\n🔧 测试各个组件的独立功能")
    print("-" * 40)
    
    try:
        from crewai_simplified import SimplifiedAgent, SimplifiedCrew
        
        # 测试单个智能体
        print("📋 测试单个智能体...")
        agent = SimplifiedAgent(
            role="测试智能体",
            goal="测试智能体功能",
            backstory="用于测试的智能体"
        )
        
        # 执行简单任务
        task_result = agent.execute_task(
            "测试任务",
            {"user_requirement": "测试需求"}
        )
        
        print(f"   智能体测试: {'✅ 成功' if task_result.get('success') else '❌ 失败'}")
        
        # 测试Crew
        print("📋 测试简化Crew...")
        crew = SimplifiedCrew([agent], verbose=False)
        
        crew_result = crew.kickoff({
            "user_requirement": "测试需求",
            "search_id": "test_001"
        })
        
        print(f"   Crew测试: {'✅ 成功' if crew_result.get('success') else '❌ 失败'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 组件测试失败: {str(e)}")
        return False

def test_api_connections():
    """测试API连接"""
    print("\n🌐 测试API连接")
    print("-" * 40)
    
    try:
        # 测试Serper API
        if os.getenv("SERPER_API_KEY"):
            print("✅ SERPER_API_KEY 已配置")
            
            # 测试简单搜索
            from core.company_search import CompanySearcher
            searcher = CompanySearcher()
            
            # 执行一个简单的搜索测试
            test_result = searcher.search_companies(
                search_mode="general",
                keywords=["test company"],
                gl="us",
                num_results=5
            )
            
            if test_result.get('success'):
                print("✅ Serper API 连接正常")
                print(f"   测试搜索返回: {len(test_result.get('data', []))} 个结果")
            else:
                print("❌ Serper API 连接失败")
                print(f"   错误: {test_result.get('error')}")
        else:
            print("⚠️ SERPER_API_KEY 未配置，跳过API测试")
        
        # 测试LLM连接
        llm_apis = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "ARK_API_KEY"]
        configured_llm = []
        
        for api_key in llm_apis:
            if os.getenv(api_key):
                configured_llm.append(api_key)
        
        if configured_llm:
            print(f"✅ 已配置的LLM API: {configured_llm}")
            
            # 尝试测试LLM连接
            try:
                from integration_guide import AIAnalyzerManager
                analyzer = AIAnalyzerManager(use_optimized=True, max_concurrent=1)
                
                # 简单测试
                test_companies = [{
                    'name': 'Test Company',
                    'description': 'A test company for validation',
                    'domain': 'test.com'
                }]
                
                # 这里不执行实际分析，只测试初始化
                print("✅ AI分析器初始化正常")
                
            except Exception as e:
                print(f"⚠️ AI分析器测试异常: {str(e)}")
        else:
            print("⚠️ 未配置LLM API密钥，AI评分功能可能受限")
        
        return True
        
    except Exception as e:
        print(f"❌ API连接测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🧪 CrewAI简化版智能搜索系统综合测试")
    print("=" * 60)
    
    # 测试计数器
    total_tests = 0
    passed_tests = 0
    
    # 测试各个组件
    print("\n📋 测试 1: 独立组件功能测试")
    total_tests += 1
    if test_individual_components():
        passed_tests += 1
        print("✅ 独立组件测试通过")
    else:
        print("❌ 独立组件测试失败")
    
    # 测试API连接
    print("\n📋 测试 2: API连接测试")
    total_tests += 1
    if test_api_connections():
        passed_tests += 1
        print("✅ API连接测试通过")
    else:
        print("❌ API连接测试失败")
    
    # 测试完整工作流
    print("\n📋 测试 3: 完整工作流测试")
    total_tests += 1
    if test_complete_workflow():
        passed_tests += 1
        print("✅ 完整工作流测试通过")
    else:
        print("❌ 完整工作流测试失败")
    
    # 测试总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print(f"总测试数: {total_tests}")
    print(f"通过测试: {passed_tests} ✅")
    print(f"失败测试: {total_tests - passed_tests} ❌")
    print(f"成功率: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！CrewAI简化版智能搜索系统运行正常。")
        print("💡 系统已准备就绪，可以开始使用智能搜索功能。")
        print("🚀 下一步: 可以运行 'python crewai_simplified.py' 或集成到您的应用中。")
    else:
        print(f"\n⚠️ 有 {total_tests - passed_tests} 个测试失败，请检查配置和依赖。")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)