#!/usr/bin/env python3
"""
LangGraph Phase 2功能测试
测试公司搜索和AI评估节点
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langgraph_search import create_search_graph

def test_company_search_integration():
    """测试公司搜索集成"""
    print("=" * 60)
    print("测试公司搜索节点集成")
    print("=" * 60)
    
    # 检查API密钥
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        print("⚠️  SERPER_API_KEY未配置，将跳过实际搜索测试")
        return False
    
    # 创建图实例
    graph = create_search_graph(enable_checkpoints=False)
    
    # 测试查询
    test_query = "找北京的新能源公司"
    print(f"测试查询: {test_query}")
    
    try:
        result = graph.execute_search(test_query)
        
        if result["success"]:
            state = result["result"]
            
            print(f"✅ 执行成功")
            print(f"意图识别: {state['detected_intent']} (置信度: {state['intent_confidence']:.2f})")
            print(f"工作流路径: {' -> '.join(state['workflow_path'])}")
            print(f"当前节点: {state['current_node']}")
            
            # 检查搜索结果
            companies = state["search_results"]["companies"]
            qualified_companies = state["search_results"]["qualified_companies"]
            
            print(f"找到公司数量: {len(companies)}")
            print(f"符合条件公司: {len(qualified_companies)}")
            
            if companies:
                print("\n前3家公司信息:")
                for i, company in enumerate(companies[:3]):
                    print(f"  {i+1}. {company.name}")
                    print(f"     行业: {company.industry}")
                    print(f"     地址: {company.location}")
                    if hasattr(company, 'ai_score') and company.ai_score:
                        print(f"     AI评分: {company.ai_score}")
                        print(f"     评估结果: {company.ai_reason}")
            
            # 检查错误和警告
            errors = state.get("errors", [])
            warnings = state.get("warnings", [])
            
            if errors:
                print(f"\n❌ 发现 {len(errors)} 个错误:")
                for error in errors:
                    print(f"   - {error['type']}: {error['message']}")
            
            if warnings:
                print(f"\n⚠️  发现 {len(warnings)} 个警告:")
                for warning in warnings:
                    print(f"   - {warning['type']}: {warning['message']}")
            
            return True
            
        else:
            print(f"❌ 执行失败: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_evaluation_functionality():
    """测试AI评估功能"""
    print("\n" + "=" * 60)
    print("测试AI评估节点功能")
    print("=" * 60)
    
    # 检查LLM API密钥
    llm_providers = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"]
    available_provider = None
    
    for provider_key in llm_providers:
        if os.getenv(provider_key):
            available_provider = provider_key
            break
    
    if not available_provider:
        print("⚠️  未配置LLM API密钥，将使用模拟AI评估")
        return False
    
    print(f"使用 {available_provider} 进行AI评估测试")
    
    # 创建图实例 
    graph = create_search_graph(enable_checkpoints=False)
    
    # 测试带AI评估的查询
    test_query = "找做太阳能发电的科技公司"
    print(f"测试查询: {test_query}")
    
    try:
        result = graph.execute_search(test_query, ai_evaluation_enabled=True)
        
        if result["success"]:
            state = result["result"]
            
            print(f"✅ AI评估测试成功")
            print(f"AI评估完成: {state.get('ai_evaluation_completed', False)}")
            
            # 检查评估结果
            companies = state["search_results"]["companies"]
            qualified_companies = state["search_results"]["qualified_companies"]
            
            print(f"评估公司数量: {len(companies)}")
            print(f"符合条件公司: {len(qualified_companies)}")
            
            if qualified_companies:
                print("\n符合条件的公司:")
                for i, company in enumerate(qualified_companies[:3]):
                    print(f"  {i+1}. {company.name}")
                    print(f"     AI评分: {company.ai_score}")
                    print(f"     评估原因: {company.ai_reason}")
                    print(f"     符合条件: {company.is_qualified}")
            
            return True
        else:
            print(f"❌ AI评估测试失败: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ AI评估测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_different_search_intents():
    """测试不同搜索意图的处理"""
    print("\n" + "=" * 60)
    print("测试不同搜索意图")
    print("=" * 60)
    
    test_cases = [
        {"query": "找深圳的电子制造公司", "expected_intent": "company"},
        {"query": "搜索华为的销售经理联系方式", "expected_intent": "employee"}, 
        {"query": "找新能源公司的技术总监", "expected_intent": "composite"}
    ]
    
    graph = create_search_graph(enable_checkpoints=False)
    
    success_count = 0
    for i, case in enumerate(test_cases):
        query = case["query"]
        expected = case["expected_intent"]
        
        print(f"\n测试用例 {i+1}: {query}")
        print(f"预期意图: {expected}")
        
        try:
            result = graph.execute_search(query, ai_evaluation_enabled=False)
            
            if result["success"]:
                state = result["result"]
                actual_intent = state["detected_intent"]
                confidence = state["intent_confidence"]
                
                print(f"实际意图: {actual_intent} (置信度: {confidence:.2f})")
                print(f"意图匹配: {'✅' if actual_intent == expected else '❌'}")
                print(f"最终节点: {state['current_node']}")
                
                if actual_intent == expected:
                    success_count += 1
                    
            else:
                print(f"❌ 执行失败: {result['error']}")
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
    
    print(f"\n意图识别准确率: {success_count}/{len(test_cases)} ({success_count/len(test_cases)*100:.1f}%)")
    return success_count == len(test_cases)

def main():
    """主测试函数"""
    print("LangGraph Phase 2 功能测试")
    print("测试公司搜索和AI评估节点集成")
    
    test_results = []
    
    # 测试公司搜索集成
    try:
        result1 = test_company_search_integration()
        test_results.append(("公司搜索集成", result1))
    except Exception as e:
        print(f"公司搜索测试失败: {e}")
        test_results.append(("公司搜索集成", False))
    
    # 测试AI评估功能  
    try:
        result2 = test_ai_evaluation_functionality()
        test_results.append(("AI评估功能", result2))
    except Exception as e:
        print(f"AI评估测试失败: {e}")
        test_results.append(("AI评估功能", False))
    
    # 测试不同意图处理
    try:
        result3 = test_different_search_intents()
        test_results.append(("意图处理", result3))
    except Exception as e:
        print(f"意图处理测试失败: {e}")
        test_results.append(("意图处理", False))
    
    # 输出测试总结
    print("\n" + "=" * 60)
    print("Phase 2 测试结果总结")
    print("=" * 60)
    
    success_count = 0
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n总体通过率: {success_count}/{len(test_results)} ({success_count/len(test_results)*100:.1f}%)")
    
    if success_count == len(test_results):
        print("🎉 Phase 2 所有测试通过！")
    else:
        print("⚠️  部分测试未通过，请检查配置和实现")

if __name__ == "__main__":
    main()