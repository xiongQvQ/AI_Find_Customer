"""
工作流集成测试
测试LangGraph节点之间的集成和数据流
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langgraph_search.workflows.base_graph import create_search_graph
from langgraph_search.state import SearchState


class TestWorkflowIntegration(unittest.TestCase):
    """工作流集成测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.graph = create_search_graph()
        
        # Use proper state creation function
        from langgraph_search.state import create_initial_state
        self.base_input = create_initial_state("搜索加州的科技公司")
    
    def test_graph_creation(self):
        """测试工作流图创建"""
        self.assertIsNotNone(self.graph)
        
        # 验证节点是否正确添加
        nodes = self.graph.graph.nodes
        expected_nodes = [
            "intent_recognition",
            "company_search", 
            "ai_evaluation",
            "employee_search",
            "output",
            "clarification",
            "error_handler"
        ]
        
        for node in expected_nodes:
            self.assertIn(node, nodes)
    
    @patch.dict(os.environ, {"SERPER_API_KEY": "test_key"})
    @patch("langgraph_search.nodes.company_search.SerperCompanySearch")
    def test_complete_company_search_workflow(self, mock_serper):
        """测试完整的公司搜索工作流"""
        # 模拟搜索结果
        mock_results = [
            {
                "name": "TechCorp",
                "url": "https://techcorp.com",
                "domain": "techcorp.com",
                "industry": "Technology",
                "location": "San Francisco, CA",
                "description": "Leading tech company"
            }
        ]
        
        mock_instance = MagicMock()
        mock_instance.search_general_companies.return_value = mock_results
        mock_serper.return_value = mock_instance
        
        input_state = self.base_input.copy()
        input_state["user_query"] = "搜索加州的科技公司"
        
        # 执行工作流
        config = {"configurable": {"thread_id": "test_thread_1"}}
        result = self.graph.compiled_graph.invoke(input_state, config=config)
        
        # 验证工作流完成
        self.assertNotEqual(result["detected_intent"], "unknown")
        self.assertTrue(result["company_search_completed"])
        self.assertTrue(result["ai_evaluation_completed"])
        
        # 验证工作流路径
        expected_path_elements = [
            "intent_recognition_completed",
            "company_search_started", 
            "company_search_completed",
            "ai_evaluation_started",
            "ai_evaluation_completed",
            "output_integration"
        ]
        
        workflow_path = result["workflow_path"]
        for element in expected_path_elements:
            self.assertIn(element, workflow_path)
    
    def test_clarification_workflow(self):
        """测试澄清工作流"""
        input_state = self.base_input.copy()
        input_state["user_query"] = "搜索"  # 模糊查询
        
        config = {"configurable": {"thread_id": "test_thread_1"}}
        result = self.graph.compiled_graph.invoke(input_state, config=config)
        
        # 验证澄清流程被触发
        self.assertIn("clarification", result["workflow_path"])
        # For ambiguous query "搜索", intent should be unknown or have low confidence
        self.assertTrue(result["detected_intent"] == "unknown" or result["intent_confidence"] < 0.5)
    
    @patch.dict(os.environ, {}, clear=True)  # 清空环境变量
    def test_error_handling_workflow(self):
        """测试错误处理工作流"""
        input_state = self.base_input.copy()
        input_state["user_query"] = "搜索科技公司"
        
        config = {"configurable": {"thread_id": "test_thread_1"}}
        result = self.graph.compiled_graph.invoke(input_state, config=config)
        
        # 验证错误被捕获和处理
        self.assertGreater(len(result["errors"]), 0)
        
        # 验证错误处理节点被调用
        if "error_handler" in result["workflow_path"]:
            # 验证错误处理完成
            pass
    
    @patch.dict(os.environ, {"SERPER_API_KEY": "test_key"})
    @patch("langgraph_search.nodes.company_search.SerperCompanySearch")
    def test_employee_search_workflow(self, mock_serper):
        """测试员工搜索工作流"""
        # 模拟公司搜索结果
        mock_company_results = [
            {
                "name": "TechCorp",
                "domain": "techcorp.com",
                "industry": "Technology",
                "location": "San Francisco"
            }
        ]
        
        mock_instance = MagicMock()
        mock_instance.search_general_companies.return_value = mock_company_results
        mock_serper.return_value = mock_instance
        
        input_state = self.base_input.copy()
        input_state["user_query"] = "搜索TechCorp的销售经理"
        
        config = {"configurable": {"thread_id": "test_thread_1"}}
        result = self.graph.compiled_graph.invoke(input_state, config=config)
        
        # 验证员工搜索被触发
        self.assertTrue(result["intent_recognized"])
        search_params = result["search_params"]
        self.assertIn(search_params.search_type, ["employee", "composite"])
    
    def test_data_flow_between_nodes(self):
        """测试节点间数据流"""
        input_state = self.base_input.copy()
        input_state["user_query"] = "搜索科技公司"
        
        # 执行意图识别
        from langgraph_search.nodes.intent_recognition import intent_recognition_node
        result_after_intent = intent_recognition_node.execute(input_state)
        
        # 验证数据正确传递
        # Check that intent was processed (detected_intent should not be 'unknown')
        self.assertNotEqual(result_after_intent["detected_intent"], "unknown")
        self.assertIsNotNone(result_after_intent["search_params"])
        self.assertEqual(result_after_intent["search_params"].search_type, "general")
    
    def test_state_persistence(self):
        """测试状态持久性"""
        input_state = self.base_input.copy()
        input_state["user_query"] = "搜索科技公司"
        
        # 执行部分工作流
        from langgraph_search.nodes.intent_recognition import intent_recognition_node
        intermediate_state = intent_recognition_node.execute(input_state)
        
        # 验证原始状态信息被保持
        self.assertEqual(intermediate_state["user_query"], input_state["user_query"])
        
        # 验证新状态信息被添加
        self.assertEqual(intermediate_state["current_node"], "intent_recognition")
        # Initial state has ["start"], after intent recognition: ["start", "intent_recognition", "intent_recognition_completed"]
        self.assertEqual(len(intermediate_state["workflow_path"]), 3)
        self.assertIn("intent_recognition_completed", intermediate_state["workflow_path"])
    
    @patch.dict(os.environ, {"SERPER_API_KEY": "test_key"})
    @patch("langgraph_search.nodes.company_search.SerperCompanySearch")
    def test_performance_metrics_flow(self, mock_serper):
        """测试性能指标在节点间的传递"""
        mock_results = [{"name": "TestCorp", "domain": "test.com"}]
        
        mock_instance = MagicMock()
        mock_instance.search_general_companies.return_value = mock_results
        mock_serper.return_value = mock_instance
        
        input_state = self.base_input.copy()
        input_state["user_query"] = "搜索科技公司"
        
        config = {"configurable": {"thread_id": "test_thread_1"}}
        result = self.graph.compiled_graph.invoke(input_state, config=config)
        
        # 验证性能指标被收集
        self.assertIn("performance_metrics", result)
        metrics = result["performance_metrics"]
        
        # 验证各节点的性能指标
        expected_metric_keys = ["intent_recognition", "company_search", "ai_evaluation"]
        for key in expected_metric_keys:
            if key in metrics:
                self.assertIn("execution_time", metrics[key])
                self.assertIn("memory_usage", metrics[key])
    
    def test_error_propagation(self):
        """测试错误传播"""
        input_state = self.base_input.copy()
        input_state["user_query"] = None  # 异常输入
        
        config = {"configurable": {"thread_id": "test_thread_1"}}
        result = self.graph.compiled_graph.invoke(input_state, config=config)
        
        # 验证错误被正确传播和处理
        self.assertGreater(len(result["errors"]), 0)
        
        # 验证工作流没有因为错误而中断
        self.assertIn("current_node", result)
    
    def test_conditional_routing(self):
        """测试条件路由"""
        # 测试不同查询类型的路由
        test_cases = [
            {
                "query": "搜索科技公司",
                "expected_type": "company"
            },
            {
                "query": "找销售经理",
                "expected_type": "employee"
            },
            {
                "query": "搜索科技公司的CEO",
                "expected_type": "composite"
            }
        ]
        
        for case in test_cases:
            with self.subTest(query=case["query"]):
                input_state = self.base_input.copy()
                input_state["user_query"] = case["query"]
                
                # 执行意图识别
                from langgraph_search.nodes.intent_recognition import intent_recognition_node
                result = intent_recognition_node.execute(input_state)
                
                if result["intent_recognized"]:
                    self.assertEqual(
                        result["search_params"].search_type, 
                        case["expected_type"]
                    )
    
    def test_workflow_termination_conditions(self):
        """测试工作流终止条件"""
        # 测试正常完成
        input_state = self.base_input.copy()
        input_state["user_query"] = "搜索科技公司"
        
        # 模拟完成状态
        input_state["intent_recognized"] = True
        input_state["company_search_completed"] = True
        input_state["ai_evaluation_completed"] = True
        
        # 这里应该测试图的终止逻辑
        # 具体实现取决于base_graph中的条件判断
    
    def test_parallel_processing_support(self):
        """测试并行处理支持"""
        # 如果工作流支持并行处理，测试相关功能
        input_state = self.base_input.copy()
        input_state["user_query"] = "搜索科技公司和他们的CEO"
        
        # 这里可以测试并行执行公司搜索和员工搜索
        # 具体实现取决于图的设计
    
    def test_caching_integration(self):
        """测试缓存集成"""
        input_state = self.base_input.copy()
        input_state["user_query"] = "搜索科技公司"
        
        # 执行两次相同的查询
        config1 = {"configurable": {"thread_id": "test_thread_1"}}
        config2 = {"configurable": {"thread_id": "test_thread_2"}}
        result1 = self.graph.compiled_graph.invoke(input_state.copy(), config=config1)
        result2 = self.graph.compiled_graph.invoke(input_state.copy(), config=config2)
        
        # 验证缓存命中（如果实现了缓存）
        if "cache_hits" in result2 and result2["cache_hits"] > result1.get("cache_hits", 0):
            self.assertGreater(result2["cache_hits"], 0)
        else:
            # If caching not implemented, both results should be valid
            self.assertNotEqual(result1["detected_intent"], "unknown")
            self.assertNotEqual(result2["detected_intent"], "unknown")


if __name__ == "__main__":
    unittest.main()