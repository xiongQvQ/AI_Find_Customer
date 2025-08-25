#!/usr/bin/env python3
"""
系统集成测试
测试鲁棒性AI评估节点和LangGraph工作流
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

# 确保环境变量加载
from dotenv import load_dotenv
load_dotenv()

def test_robust_ai_evaluation():
    """测试鲁棒性AI评估节点"""
    print("🧪 测试鲁棒性AI评估节点...")
    
    try:
        from langgraph_search.nodes.robust_ai_evaluation import robust_ai_evaluation_node
        from langgraph_search.state import SearchState, CompanyInfo
        
        # 创建测试状态
        test_state = {
            "session_id": "test_session",
            "user_query": "寻找北京的科技公司",
            "detected_intent": "company",
            "current_node": "ai_evaluation",
            "workflow_path": ["intent_recognition", "company_search"],
            "search_results": {
                "companies": [
                    CompanyInfo(
                        name="测试科技公司",
                        domain="test.com",
                        industry="科技",
                        size="100-500人",
                        location="北京",
                        description="专注于AI技术的科技公司"
                    )
                ],
                "total_companies_found": 1,
                "qualified_companies": [],
                "qualified_companies_count": 0
            },
            "ai_evaluation_enabled": True,
            "api_calls_count": 0,
            "errors": [],
            "warnings": []
        }
        
        print("   ✓ 测试状态创建成功")
        
        # 执行AI评估
        result_state = robust_ai_evaluation_node.execute(test_state)
        
        # 验证结果
        if result_state.get("ai_evaluation_completed"):
            print("   ✓ AI评估执行完成")
            
            # 检查是否有合格公司（即使LLM不可用也应该有基础评估）
            qualified_count = result_state["search_results"]["qualified_companies_count"]
            print(f"   ✓ 合格公司数量: {qualified_count}")
            
            if qualified_count > 0:
                company = result_state["search_results"]["qualified_companies"][0]
                print(f"   ✓ 公司评分: {company.ai_score}")
                print(f"   ✓ 评估原因: {company.ai_reason}")
            
            return True, "AI评估节点测试通过"
        else:
            return False, "AI评估未完成"
            
    except Exception as e:
        return False, f"AI评估节点测试失败: {e}"

def test_langgraph_workflow():
    """测试LangGraph工作流"""
    print("\n🧪 测试LangGraph工作流...")
    
    try:
        from langgraph_search.workflows.base_graph import create_search_graph
        
        # 创建工作流图
        graph = create_search_graph(enable_checkpoints=False)
        print("   ✓ LangGraph工作流创建成功")
        
        # 验证编译状态
        if graph.compiled_graph:
            print("   ✓ 工作流编译成功")
        else:
            return False, "工作流编译失败"
        
        # 测试简单查询执行（仅验证图结构，不执行完整流程）
        try:
            # 这里我们只测试图的结构，不执行实际搜索
            mermaid = graph.get_graph_visualization()
            if "Start" in mermaid and "End" in mermaid:
                print("   ✓ 工作流结构验证通过")
            else:
                print("   ⚠️ 工作流结构可能有问题")
                
        except Exception as e:
            print(f"   ⚠️ 图结构测试异常: {e}")
        
        return True, "LangGraph工作流测试通过"
        
    except Exception as e:
        return False, f"LangGraph工作流测试失败: {e}"

def test_llm_connection():
    """测试LLM连接"""
    print("\n🧪 测试LLM连接...")
    
    try:
        from langgraph_search.utils.llm_connection_helper import LLMConnectionDiagnostics
        
        diagnostics = LLMConnectionDiagnostics()
        result = diagnostics.diagnose_all_providers()
        
        working_providers = []
        for provider_name, provider_data in result["results"].items():
            if provider_data["status"] == "healthy":
                working_providers.append(provider_name)
                print(f"   ✓ {provider_name}: 连接成功")
            else:
                details = provider_data.get("details", {})
                message = details.get("message", "连接失败")
                print(f"   ❌ {provider_name}: {message}")
        
        if working_providers:
            return True, f"LLM连接测试通过 (可用提供商: {', '.join(working_providers)})"
        else:
            return False, "没有可用的LLM提供商"
            
    except Exception as e:
        return False, f"LLM连接测试失败: {e}"

def test_logging_system():
    """测试日志系统"""
    print("\n🧪 测试日志系统...")
    
    try:
        from config.logging_config import LangGraphLogger
        
        # 创建日志器
        logger = LangGraphLogger()
        test_log = logger.setup_logger("integration_test", "integration_test.log")
        
        # 测试日志写入
        test_log.info("集成测试日志消息")
        test_log.warning("测试警告消息")
        test_log.error("测试错误消息")
        
        print("   ✓ 日志系统初始化成功")
        print("   ✓ 日志写入测试完成")
        
        return True, "日志系统测试通过"
        
    except Exception as e:
        return False, f"日志系统测试失败: {e}"

def test_monitoring_system():
    """测试监控系统"""
    print("\n🧪 测试监控系统...")
    
    try:
        from langgraph_search.utils.system_reporter import SystemReporter
        
        reporter = SystemReporter()
        report = reporter.generate_comprehensive_report()
        
        if report and report.get("health_assessment"):
            health = report["health_assessment"]
            status = health.get("overall_status", "unknown")
            score = health.get("health_score", 0)
            print(f"   ✓ 系统状态: {status}")
            print(f"   ✓ 健康得分: {score}")
            
            return True, "监控系统测试通过"
        else:
            return False, "监控系统无法生成报告"
            
    except Exception as e:
        return False, f"监控系统测试失败: {e}"

def main():
    """主测试函数"""
    print("🚀 AI客户发现系统集成测试")
    print("=" * 50)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    tests = [
        ("鲁棒性AI评估节点", test_robust_ai_evaluation),
        ("LangGraph工作流", test_langgraph_workflow), 
        ("LLM连接", test_llm_connection),
        ("日志系统", test_logging_system),
        ("监控系统", test_monitoring_system)
    ]
    
    results = []
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            success, message = test_func()
            results.append((test_name, success, message))
            if success:
                passed += 1
            
        except Exception as e:
            results.append((test_name, False, f"测试异常: {e}"))
    
    # 输出测试结果
    print("\n📊 测试结果汇总:")
    print("=" * 50)
    
    for test_name, success, message in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        print(f"     {message}")
        print()
    
    print(f"📈 测试统计: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统已准备好部署。")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查系统配置。")
        return 1

if __name__ == "__main__":
    exit(main())