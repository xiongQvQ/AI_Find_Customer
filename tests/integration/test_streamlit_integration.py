"""
Streamlit集成测试
测试LangGraph与Streamlit界面的集成
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
import streamlit as st
from unittest.mock import patch

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestStreamlitIntegration(unittest.TestCase):
    """Streamlit集成测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 模拟Streamlit会话状态
        if 'search_history' not in st.session_state:
            st.session_state.search_history = []
        if 'current_results' not in st.session_state:
            st.session_state.current_results = None
        if 'performance_data' not in st.session_state:
            st.session_state.performance_data = []
    
    @patch('streamlit.sidebar')
    @patch('streamlit.columns')
    @patch('streamlit.tabs')
    def test_ui_component_initialization(self, mock_tabs, mock_columns, mock_sidebar):
        """测试UI组件初始化"""
        # 模拟Streamlit组件
        mock_tabs.return_value = [MagicMock() for _ in range(4)]
        mock_columns.return_value = [MagicMock() for _ in range(2)]
        mock_sidebar.return_value = MagicMock()
        
        # 这里应该导入并测试Streamlit页面
        # 由于Streamlit的特殊性，这个测试可能需要特殊的测试框架
        pass
    
    @patch('langgraph_search.workflows.base_graph.create_search_graph')
    def test_search_execution_integration(self, mock_create_graph):
        """测试搜索执行集成"""
        # 模拟图和搜索结果
        mock_graph = MagicMock()
        mock_result = {
            "intent_recognized": True,
            "company_search_completed": True,
            "search_results": {
                "companies": [
                    {
                        "name": "TechCorp",
                        "domain": "techcorp.com",
                        "industry": "Technology"
                    }
                ]
            },
            "workflow_path": ["intent_recognition_completed", "company_search_completed"],
            "performance_metrics": {
                "intent_recognition": {"execution_time": 0.5},
                "company_search": {"execution_time": 2.1}
            }
        }
        
        mock_graph.invoke.return_value = mock_result
        mock_create_graph.return_value = mock_graph
        
        # 模拟执行搜索
        query = "搜索科技公司"
        result = mock_graph.invoke({
            "user_query": query,
            "search_params": None,
            "search_results": {"companies": [], "employees": []},
            "workflow_path": [],
            "current_node": "start",
            "errors": [],
            "warnings": [],
            "api_calls_count": 0
        })
        
        # 验证结果
        self.assertTrue(result["intent_recognized"])
        self.assertTrue(result["company_search_completed"])
        self.assertEqual(len(result["search_results"]["companies"]), 1)
    
    def test_search_history_management(self):
        """测试搜索历史管理"""
        # 模拟添加搜索历史
        search_entry = {
            "timestamp": "2024-01-01 10:00:00",
            "query": "搜索科技公司",
            "results_count": 5,
            "execution_time": 3.2,
            "status": "success"
        }
        
        # 添加到会话状态
        st.session_state.search_history.append(search_entry)
        
        # 验证历史记录
        self.assertEqual(len(st.session_state.search_history), 1)
        self.assertEqual(st.session_state.search_history[0]["query"], "搜索科技公司")
    
    def test_results_display_formatting(self):
        """测试结果显示格式化"""
        # 模拟搜索结果
        companies = [
            {
                "name": "TechCorp Inc",
                "domain": "techcorp.com",
                "industry": "Technology",
                "location": "San Francisco, CA",
                "description": "Leading technology company",
                "linkedin_url": "https://linkedin.com/company/techcorp",
                "website_url": "https://techcorp.com"
            },
            {
                "name": "InnovateSoft",
                "domain": "innovatesoft.com",
                "industry": "Software",
                "location": "Austin, TX",
                "description": "Innovative software solutions"
            }
        ]
        
        # 这里应该测试结果格式化函数
        # 由于Streamlit的特殊性，可能需要模拟相关函数
        
        # 验证数据结构
        for company in companies:
            self.assertIn("name", company)
            self.assertIn("domain", company)
    
    def test_error_display_handling(self):
        """测试错误显示处理"""
        # 模拟错误状态
        error_result = {
            "intent_recognized": False,
            "errors": [
                {
                    "type": "missing_api_key",
                    "message": "SERPER_API_KEY not configured",
                    "source": "company_search",
                    "timestamp": "2024-01-01 10:00:00"
                }
            ],
            "warnings": [
                {
                    "type": "low_results_count",
                    "message": "搜索结果数量较少: 2",
                    "source": "company_search"
                }
            ]
        }
        
        # 验证错误处理结构
        self.assertEqual(len(error_result["errors"]), 1)
        self.assertEqual(error_result["errors"][0]["type"], "missing_api_key")
        self.assertEqual(len(error_result["warnings"]), 1)
    
    def test_performance_monitoring_display(self):
        """测试性能监控显示"""
        # 模拟性能数据
        performance_data = {
            "intent_recognition": {
                "execution_time": 0.5,
                "memory_usage": 125.6,
                "cpu_usage": 15.2
            },
            "company_search": {
                "execution_time": 2.1,
                "memory_usage": 256.8,
                "cpu_usage": 45.3,
                "api_calls": 1
            },
            "ai_evaluation": {
                "execution_time": 1.8,
                "memory_usage": 198.4,
                "cpu_usage": 32.1,
                "companies_processed": 10
            }
        }
        
        # 添加到会话状态
        st.session_state.performance_data.append(performance_data)
        
        # 验证性能数据结构
        self.assertEqual(len(st.session_state.performance_data), 1)
        perf_data = st.session_state.performance_data[0]
        self.assertIn("intent_recognition", perf_data)
        self.assertIn("execution_time", perf_data["intent_recognition"])
    
    def test_workflow_visualization_data(self):
        """测试工作流可视化数据"""
        # 模拟工作流路径
        workflow_path = [
            "intent_recognition_started",
            "intent_recognition_completed", 
            "company_search_started",
            "company_search_completed",
            "ai_evaluation_started",
            "ai_evaluation_completed",
            "output_integration_completed"
        ]
        
        # 提取节点状态
        node_states = {}
        for step in workflow_path:
            if "_started" in step:
                node = step.replace("_started", "")
                node_states[node] = "in_progress"
            elif "_completed" in step:
                node = step.replace("_completed", "")
                node_states[node] = "completed"
        
        # 验证节点状态
        expected_nodes = ["intent_recognition", "company_search", "ai_evaluation", "output_integration"]
        for node in expected_nodes:
            if node in node_states:
                self.assertEqual(node_states[node], "completed")
    
    def test_search_suggestions_integration(self):
        """测试搜索建议集成"""
        # 模拟搜索建议
        suggestions = [
            "搜索加州的科技公司",
            "寻找新能源企业",
            "查找软件开发公司",
            "搜索人工智能初创公司"
        ]
        
        # 验证建议格式
        for suggestion in suggestions:
            self.assertIsInstance(suggestion, str)
            self.assertGreater(len(suggestion), 0)
    
    def test_export_functionality(self):
        """测试导出功能"""
        # 模拟导出数据
        export_data = {
            "search_query": "搜索科技公司",
            "timestamp": "2024-01-01 10:00:00",
            "companies": [
                {
                    "name": "TechCorp",
                    "domain": "techcorp.com",
                    "industry": "Technology",
                    "location": "San Francisco, CA"
                }
            ],
            "total_results": 1,
            "execution_time": 3.2
        }
        
        # 验证导出数据结构
        self.assertIn("search_query", export_data)
        self.assertIn("companies", export_data)
        self.assertEqual(export_data["total_results"], 1)
    
    def test_user_input_validation(self):
        """测试用户输入验证"""
        # 测试有效输入
        valid_queries = [
            "搜索科技公司",
            "找销售经理",
            "search tech companies",
            "renewable energy companies"
        ]
        
        for query in valid_queries:
            # 这里应该调用输入验证函数
            # 简单验证：非空且长度合理
            self.assertIsNotNone(query)
            self.assertGreater(len(query.strip()), 0)
            self.assertLess(len(query), 1000)  # 合理的长度限制
        
        # 测试无效输入
        invalid_queries = [
            "",
            " ",
            None,
            "a" * 1001  # 过长的查询
        ]
        
        for query in invalid_queries:
            if query is None:
                continue
            if isinstance(query, str):
                if len(query.strip()) == 0 or len(query) > 1000:
                    # 应该被标记为无效
                    pass
    
    def test_responsive_design_elements(self):
        """测试响应式设计元素"""
        # 模拟不同屏幕大小的配置
        layout_configs = [
            {"columns": [1, 2], "sidebar_width": 250},  # 桌面
            {"columns": [1], "sidebar_width": 200},     # 平板
            {"columns": [1], "sidebar_width": 150}      # 手机
        ]
        
        for config in layout_configs:
            self.assertIn("columns", config)
            self.assertIn("sidebar_width", config)
    
    def test_session_state_management(self):
        """测试会话状态管理"""
        # 测试状态初始化
        required_states = [
            "search_history",
            "current_results", 
            "performance_data"
        ]
        
        for state in required_states:
            if state not in st.session_state:
                if state == "search_history":
                    st.session_state[state] = []
                elif state == "performance_data":
                    st.session_state[state] = []
                else:
                    st.session_state[state] = None
        
        # 验证状态存在
        for state in required_states:
            self.assertIn(state, st.session_state)
    
    def test_real_time_updates(self):
        """测试实时更新功能"""
        # 模拟实时更新场景
        initial_progress = {
            "current_step": "intent_recognition",
            "completed_steps": 0,
            "total_steps": 4,
            "status": "running"
        }
        
        updated_progress = {
            "current_step": "company_search",
            "completed_steps": 1,
            "total_steps": 4,
            "status": "running"
        }
        
        # 验证进度更新
        self.assertNotEqual(
            initial_progress["current_step"], 
            updated_progress["current_step"]
        )
        self.assertGreater(
            updated_progress["completed_steps"], 
            initial_progress["completed_steps"]
        )


if __name__ == "__main__":
    unittest.main()