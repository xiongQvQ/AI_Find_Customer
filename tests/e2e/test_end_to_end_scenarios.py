"""
端到端测试场景
测试完整的用户使用场景
"""

import unittest
import sys
import os
import time
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langgraph_search.workflows.base_graph import create_search_graph


class TestEndToEndScenarios(unittest.TestCase):
    """端到端测试场景类"""
    
    def setUp(self):
        """测试前准备"""
        self.graph = create_search_graph()
        
        self.base_input = {
            "user_query": "",
            "search_params": None,
            "search_results": {"companies": [], "employees": []},
            "workflow_path": [],
            "current_node": "start",
            "errors": [],
            "warnings": [],
            "api_calls_count": 0,
            "intent_recognized": False,
            "company_search_completed": False,
            "employee_search_completed": False,
            "clarification_needed": False,
            "clarification_suggestions": [],
            "performance_metrics": {},
            "cache_hits": 0
        }
    
    @patch.dict(os.environ, {"SERPER_API_KEY": "test_key"})
    @patch("langgraph_search.nodes.company_search.SerperCompanySearch")
    def test_successful_company_discovery_scenario(self, mock_serper):
        """测试成功的公司发现场景"""
        # 场景：用户搜索科技公司
        mock_results = [
            {
                "name": "TechCorp Inc",
                "url": "https://techcorp.com",
                "domain": "techcorp.com",
                "industry": "Technology",
                "location": "San Francisco, CA",
                "description": "Leading AI technology company",
                "snippet": "Leading AI technology company"
            },
            {
                "name": "InnovateSoft LLC",
                "url": "https://innovatesoft.com",
                "domain": "innovatesoft.com", 
                "industry": "Software Development",
                "location": "Austin, TX",
                "description": "Innovative software solutions provider"
            }
        ]
        
        mock_instance = MagicMock()
        mock_instance.search_general_companies.return_value = mock_results
        mock_serper.return_value = mock_instance
        
        # 执行完整场景
        input_state = self.base_input.copy()
        input_state["user_query"] = "搜索美国的人工智能科技公司"
        
        start_time = time.time()
        result = self.graph.invoke(input_state)
        execution_time = time.time() - start_time
        
        # 验证场景完成
        self.assertTrue(result["intent_recognized"], "Intent should be recognized")
        self.assertTrue(result["company_search_completed"], "Company search should be completed")
        self.assertTrue(result["ai_evaluation_completed"], "AI evaluation should be completed")
        
        # 验证结果质量
        companies = result["search_results"]["companies"]
        self.assertGreater(len(companies), 0, "Should find companies")
        self.assertLessEqual(len(companies), 2, "Should not exceed mock data")
        
        # 验证公司信息完整性
        for company in companies:
            self.assertIsNotNone(company.name, "Company should have name")
            self.assertTrue(
                company.domain or company.linkedin_url or company.website_url,
                "Company should have at least one contact method"
            )
        
        # 验证性能指标
        self.assertLess(execution_time, 30, "Execution should complete within 30 seconds")
        self.assertIn("performance_metrics", result)
        
        # 验证工作流完整性
        expected_workflow_steps = [
            "intent_recognition_started",
            "intent_recognition_completed",
            "company_search_started", 
            "company_search_completed",
            "ai_evaluation_started",
            "ai_evaluation_completed"
        ]
        
        for step in expected_workflow_steps:
            self.assertIn(step, result["workflow_path"], f"Missing workflow step: {step}")
    
    @patch.dict(os.environ, {"SERPER_API_KEY": "test_key"})
    @patch("langgraph_search.nodes.employee_search.SerperEmployeeSearch")
    @patch("langgraph_search.nodes.company_search.SerperCompanySearch")
    def test_composite_search_scenario(self, mock_company_serper, mock_employee_serper):
        """测试复合搜索场景"""
        # 场景：用户搜索公司及其员工
        mock_company_results = [
            {
                "name": "TechCorp Inc",
                "url": "https://techcorp.com",
                "domain": "techcorp.com",
                "industry": "Technology",
                "location": "San Francisco, CA",
                "description": "Leading technology company"
            }
        ]
        
        mock_employee_results = [
            {
                "name": "John Doe",
                "position": "CEO",
                "company": "TechCorp Inc",
                "linkedin": "https://linkedin.com/in/johndoe",
                "location": "San Francisco, CA"
            }
        ]
        
        mock_company_instance = MagicMock()
        mock_company_instance.search_general_companies.return_value = mock_company_results
        mock_company_serper.return_value = mock_company_instance
        
        mock_employee_instance = MagicMock()
        mock_employee_instance.search_employees.return_value = mock_employee_results
        mock_employee_serper.return_value = mock_employee_instance
        
        # 执行复合搜索
        input_state = self.base_input.copy()
        input_state["user_query"] = "搜索科技公司TechCorp的CEO联系方式"
        
        result = self.graph.invoke(input_state)
        
        # 验证复合搜索完成
        self.assertTrue(result["intent_recognized"])
        search_params = result["search_params"]
        self.assertEqual(search_params.search_type, "composite")
        
        # 如果员工搜索被执行，验证结果
        if result.get("employee_search_completed", False):
            employees = result["search_results"].get("employees", [])
            self.assertGreater(len(employees), 0, "Should find employees")
    
    def test_error_recovery_scenario(self):
        """测试错误恢复场景"""
        # 场景：API密钥缺失的错误恢复
        with patch.dict(os.environ, {}, clear=True):
            input_state = self.base_input.copy()
            input_state["user_query"] = "搜索科技公司"
            
            result = self.graph.invoke(input_state)
            
            # 验证错误被捕获
            self.assertGreater(len(result["errors"]), 0, "Should capture errors")
            
            # 验证错误类型
            error_types = [error["type"] for error in result["errors"]]
            self.assertIn("missing_api_key", error_types, "Should detect missing API key")
            
            # 验证错误处理节点被调用
            if "error_handler" in result["workflow_path"]:
                # 验证恢复建议
                pass
    
    def test_clarification_scenario(self):
        """测试澄清场景"""
        # 场景：模糊查询需要澄清
        ambiguous_queries = [
            "搜索",
            "找一些公司",
            "help me search",
            "find something"
        ]
        
        for query in ambiguous_queries:
            with self.subTest(query=query):
                input_state = self.base_input.copy()
                input_state["user_query"] = query
                
                result = self.graph.invoke(input_state)
                
                # 验证澄清被触发
                self.assertTrue(
                    result["clarification_needed"], 
                    f"Query '{query}' should trigger clarification"
                )
                
                # 验证澄清建议
                suggestions = result["clarification_suggestions"]
                self.assertGreater(
                    len(suggestions), 0, 
                    "Should provide clarification suggestions"
                )
                
                # 验证建议质量
                for suggestion in suggestions:
                    self.assertIsInstance(suggestion, str)
                    self.assertGreater(len(suggestion), 0)
    
    @patch.dict(os.environ, {"SERPER_API_KEY": "test_key"})
    @patch("langgraph_search.nodes.company_search.SerperCompanySearch")
    def test_low_results_scenario(self, mock_serper):
        """测试低结果数量场景"""
        # 场景：搜索返回很少或没有结果
        mock_instance = MagicMock()
        mock_instance.search_general_companies.return_value = []  # 空结果
        mock_serper.return_value = mock_instance
        
        input_state = self.base_input.copy()
        input_state["user_query"] = "搜索非常特殊的行业公司"
        
        result = self.graph.invoke(input_state)
        
        # 验证低结果处理
        self.assertTrue(result["company_search_completed"], "Search should complete even with no results")
        self.assertEqual(len(result["search_results"]["companies"]), 0, "Should have no companies")
        
        # 验证警告
        warnings = result["warnings"]
        warning_types = [warning["type"] for warning in warnings]
        self.assertIn("low_results_count", warning_types, "Should warn about low results")
    
    @patch.dict(os.environ, {"SERPER_API_KEY": "test_key"})
    @patch("langgraph_search.nodes.company_search.SerperCompanySearch")
    def test_performance_intensive_scenario(self, mock_serper):
        """测试性能密集型场景"""
        # 场景：大量搜索结果的处理
        # 创建大量模拟结果
        large_results = []
        for i in range(50):
            company = {
                "name": f"Company{i}",
                "url": f"https://company{i}.com",
                "domain": f"company{i}.com",
                "industry": "Technology",
                "location": f"City{i}, State{i}",
                "description": f"Technology company {i}"
            }
            large_results.append(company)
        
        mock_instance = MagicMock()
        mock_instance.search_general_companies.return_value = large_results
        mock_serper.return_value = mock_instance
        
        input_state = self.base_input.copy()
        input_state["user_query"] = "搜索所有科技公司"
        
        start_time = time.time()
        result = self.graph.invoke(input_state)
        execution_time = time.time() - start_time
        
        # 验证性能
        self.assertLess(execution_time, 60, "Should handle large results within 60 seconds")
        
        # 验证结果处理
        companies = result["search_results"]["companies"]
        self.assertLessEqual(
            len(companies), 50, 
            "Should limit processed companies for performance"
        )
        
        # 验证性能指标记录
        self.assertIn("performance_metrics", result)
        metrics = result["performance_metrics"]
        
        if "ai_evaluation" in metrics:
            eval_metrics = metrics["ai_evaluation"]
            self.assertIn("companies_processed", eval_metrics)
    
    def test_multilingual_scenario(self):
        """测试多语言场景"""
        # 场景：不同语言的查询处理
        multilingual_queries = [
            ("搜索科技公司", "chinese"),
            ("search tech companies", "english"),
            ("buscar empresas tecnológicas", "spanish"),
            ("技術会社を探す", "japanese")
        ]
        
        for query, language in multilingual_queries:
            with self.subTest(query=query, language=language):
                input_state = self.base_input.copy()
                input_state["user_query"] = query
                
                result = self.graph.invoke(input_state)
                
                # 对于支持的语言，应该能识别意图
                if language in ["chinese", "english"]:
                    self.assertTrue(
                        result["intent_recognized"] or result["clarification_needed"],
                        f"Should handle {language} query"
                    )
                else:
                    # 未支持的语言可能需要澄清
                    self.assertTrue(
                        result["intent_recognized"] or result["clarification_needed"],
                        f"Should handle or request clarification for {language}"
                    )
    
    @patch.dict(os.environ, {"SERPER_API_KEY": "test_key"})
    @patch("langgraph_search.nodes.company_search.SerperCompanySearch")
    def test_caching_effectiveness_scenario(self, mock_serper):
        """测试缓存效果场景"""
        # 场景：重复查询的缓存效果
        mock_results = [
            {
                "name": "CachedCorp",
                "domain": "cached.com",
                "industry": "Technology"
            }
        ]
        
        mock_instance = MagicMock()
        mock_instance.search_general_companies.return_value = mock_results
        mock_serper.return_value = mock_instance
        
        query = "搜索缓存测试公司"
        
        # 第一次查询
        input_state1 = self.base_input.copy()
        input_state1["user_query"] = query
        
        start_time1 = time.time()
        result1 = self.graph.invoke(input_state1)
        execution_time1 = time.time() - start_time1
        
        # 第二次相同查询
        input_state2 = self.base_input.copy()
        input_state2["user_query"] = query
        
        start_time2 = time.time()
        result2 = self.graph.invoke(input_state2)
        execution_time2 = time.time() - start_time2
        
        # 验证缓存效果（如果实现了缓存）
        if result2["cache_hits"] > result1["cache_hits"]:
            # 缓存命中应该提高性能
            self.assertLessEqual(
                execution_time2, execution_time1 * 1.1,  # 允许10%的性能差异
                "Cached query should be faster or similar"
            )
    
    def test_user_journey_scenario(self):
        """测试用户使用旅程场景"""
        # 场景：完整的用户使用流程
        user_journey = [
            {
                "step": "initial_search",
                "query": "搜索科技公司", 
                "expected_intent": "company"
            },
            {
                "step": "refine_search",
                "query": "搜索加州的人工智能公司",
                "expected_intent": "company"
            },
            {
                "step": "employee_search", 
                "query": "找TechCorp的销售经理",
                "expected_intent": "employee"
            }
        ]
        
        session_history = []
        
        for journey_step in user_journey:
            with self.subTest(step=journey_step["step"]):
                input_state = self.base_input.copy()
                input_state["user_query"] = journey_step["query"]
                
                result = self.graph.invoke(input_state)
                
                # 记录会话历史
                session_entry = {
                    "query": journey_step["query"],
                    "intent_recognized": result["intent_recognized"],
                    "search_type": result["search_params"].search_type if result.get("search_params") else None,
                    "results_count": len(result["search_results"]["companies"])
                }
                session_history.append(session_entry)
                
                # 验证每步的期望结果
                if result["intent_recognized"]:
                    self.assertEqual(
                        result["search_params"].search_type,
                        journey_step["expected_intent"],
                        f"Wrong intent for step {journey_step['step']}"
                    )
        
        # 验证用户旅程完整性
        self.assertEqual(len(session_history), 3, "Should complete all journey steps")


if __name__ == "__main__":
    unittest.main()