#!/usr/bin/env python3
"""
LangGraph基础功能测试
测试Phase 1完成的核心组件
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langgraph_search import create_search_graph, SearchState

def test_intent_recognition():
    """测试意图识别功能"""
    print("=" * 50)
    print("测试意图识别功能")
    print("=" * 50)
    
    test_queries = [
        "找一些太阳能公司",
        "搜索北京的销售经理联系方式", 
        "我想找新能源公司的CEO和CTO",
        "帮我找一下软件开发公司",
        "查找美国的制造商",
        "这是一个不明确的查询"
    ]
    
    # 创建图实例
    graph = create_search_graph(enable_checkpoints=False)
    
    for query in test_queries:
        print(f"\n查询: {query}")
        
        result = graph.execute_search(query)
        
        if result["success"]:
            state = result["result"]
            print(f"意图: {state['detected_intent']}")
            print(f"置信度: {state['intent_confidence']:.2f}")
            print(f"推理: {state['intent_reasoning'][:100]}...")
            print(f"工作流路径: {' -> '.join(state['workflow_path'])}")
        else:
            print(f"执行失败: {result['error']}")

def test_workflow_execution():
    """测试完整工作流执行"""
    print("\n" + "=" * 50)
    print("测试完整工作流执行") 
    print("=" * 50)
    
    # 创建图实例
    graph = create_search_graph(enable_checkpoints=True)
    
    # 测试不同意图的查询
    test_cases = [
        {"query": "找新能源公司", "expected_intent": "company"},
        {"query": "搜索销售经理", "expected_intent": "employee"},
        {"query": "找科技公司的CEO", "expected_intent": "composite"}
    ]
    
    for case in test_cases:
        query = case["query"]
        expected_intent = case["expected_intent"]
        
        print(f"\n测试查询: {query}")
        print(f"预期意图: {expected_intent}")
        
        result = graph.execute_search(query)
        
        if result["success"]:
            state = result["result"]
            actual_intent = state["detected_intent"]
            
            print(f"实际意图: {actual_intent}")
            print(f"意图匹配: {'✅' if actual_intent == expected_intent else '❌'}")
            print(f"最终节点: {state['current_node']}")
            print(f"执行路径: {' -> '.join(state['workflow_path'])}")
            
            # 检查结果数据
            results = state["search_results"]
            print(f"公司数量: {results['total_companies_found']}")
            print(f"员工数量: {results['total_employees_found']}")
            print(f"符合条件公司: {results['qualified_companies_count']}")
            print(f"符合条件员工: {results['qualified_employees_count']}")
            
        else:
            print(f"❌ 执行失败: {result['error']}")

def test_graph_visualization():
    """测试图可视化"""
    print("\n" + "=" * 50)
    print("图结构可视化")
    print("=" * 50)
    
    graph = create_search_graph(enable_checkpoints=False)
    mermaid_graph = graph.get_graph_visualization()
    print(mermaid_graph)

def main():
    """主测试函数"""
    print("LangGraph基础功能测试开始")
    print("测试Phase 1完成的组件")
    
    try:
        # 测试意图识别
        test_intent_recognition()
        
        # 测试工作流执行
        test_workflow_execution()
        
        # 测试图可视化
        test_graph_visualization()
        
        print("\n" + "=" * 50)
        print("✅ 所有测试完成!")
        print("Phase 1 基础组件运行正常")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()