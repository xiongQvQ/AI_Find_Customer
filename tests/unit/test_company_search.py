"""
公司搜索节点单元测试
测试公司搜索功能的各种场景
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock, AsyncMock
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langgraph_search.nodes.company_search import CompanySearchNode, CompanySearchConfig
from langgraph_search.state import SearchState, CompanyInfo, SearchParams


class TestCompanySearchNode(unittest.TestCase):
    """公司搜索节点测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.config = CompanySearchConfig(
            max_results=10,
            gl="us",
            search_type="general",
            timeout=30,
            max_retries=2,
            enable_cache=True
        )
        self.node = CompanySearchNode(self.config)
        
        self.base_state = {
            "user_query": "搜索科技公司",
            "search_params": SearchParams(
                query="搜索科技公司",
                industry="科技",
                region="加州",
                gl="us",
                max_results=10,
                search_type="general",
                use_custom_query=False
            ),
            "search_results": {"companies": [], "employees": []},
            "workflow_path": [],
            "current_node": "intent_recognition",
            "errors": [],
            "warnings": [],
            "api_calls_count": 0,
            "intent_recognized": True,
            "company_search_completed": False,
            "employee_search_completed": False,
            "clarification_needed": False,
            "clarification_suggestions": [],
            "performance_metrics": {},
            "cache_hits": 0
        }
    
    @patch.dict(os.environ, {"SERPER_API_KEY": "test_key"})
    @patch("langgraph_search.nodes.company_search.SerperCompanySearch")
    def test_successful_general_search(self, mock_serper):
        """测试成功的通用搜索"""
        # 模拟搜索结果
        mock_results = [
            {
                "name": "TechCorp Inc",
                "url": "https://techcorp.com",
                "domain": "techcorp.com",
                "industry": "Technology",
                "location": "San Francisco, CA",
                "description": "Leading tech company",
                "snippet": "Leading tech company description"
            },
            {
                "name": "InnovateTech LLC",
                "url": "https://innovatetech.com", 
                "domain": "innovatetech.com",
                "industry": "Software",
                "location": "Palo Alto, CA",
                "description": "Innovative software solutions",
                "snippet": "Innovative software solutions"
            }
        ]
        
        mock_instance = MagicMock()
        mock_instance.search_general_companies.return_value = mock_results
        mock_serper.return_value = mock_instance
        
        state = self.base_state.copy()
        result_state = self.node.execute(state)
        
        # 验证搜索成功
        self.assertTrue(result_state["company_search_completed"])
        self.assertEqual(len(result_state["search_results"]["companies"]), 2)
        self.assertEqual(result_state["search_results"]["total_companies_found"], 2)
        self.assertIn("company_search_completed", result_state["workflow_path"])
        self.assertEqual(result_state["api_calls_count"], 1)
    
    @patch.dict(os.environ, {"SERPER_API_KEY": "test_key"})
    @patch("langgraph_search.nodes.company_search.SerperCompanySearch")
    def test_successful_linkedin_search(self, mock_serper):
        """测试成功的LinkedIn搜索"""
        mock_results = [
            {
                "name": "StartupX",
                "linkedin": "https://linkedin.com/company/startupx",
                "industry": "AI/ML",
                "location": "Silicon Valley",
                "description": "AI startup company"
            }
        ]
        
        mock_instance = MagicMock()
        mock_instance.search_linkedin_companies.return_value = mock_results
        mock_serper.return_value = mock_instance
        
        state = self.base_state.copy()
        state["search_params"].search_type = "linkedin"
        
        result_state = self.node.execute(state)
        
        # 验证LinkedIn搜索
        self.assertTrue(result_state["company_search_completed"])
        self.assertEqual(len(result_state["search_results"]["companies"]), 1)
        
        # 验证公司信息结构
        company = result_state["search_results"]["companies"][0]
        self.assertEqual(company.name, "StartupX")
        self.assertEqual(company.linkedin_url, "https://linkedin.com/company/startupx")
    
    def test_missing_api_key(self):
        """测试缺少API密钥的情况"""
        with patch.dict(os.environ, {}, clear=True):
            node = CompanySearchNode(self.config)
            state = self.base_state.copy()
            
            result_state = node.execute(state)
            
            # 验证错误处理
            self.assertFalse(result_state["company_search_completed"])
            self.assertEqual(len(result_state["errors"]), 1)
            self.assertEqual(result_state["errors"][0]["type"], "missing_api_key")
    
    @patch.dict(os.environ, {"SERPER_API_KEY": "test_key"})
    @patch("langgraph_search.nodes.company_search.SerperCompanySearch")
    def test_search_failure(self, mock_serper):
        """测试搜索失败的情况"""
        mock_instance = MagicMock()
        mock_instance.search_general_companies.side_effect = Exception("API Error")
        mock_serper.return_value = mock_instance
        
        state = self.base_state.copy()
        result_state = self.node.execute(state)
        
        # 验证错误处理
        self.assertFalse(result_state["company_search_completed"])
        self.assertEqual(len(result_state["errors"]), 1)
        self.assertEqual(result_state["errors"][0]["type"], "search_failed")
    
    @patch.dict(os.environ, {"SERPER_API_KEY": "test_key"})
    @patch("langgraph_search.nodes.company_search.SerperCompanySearch")
    def test_empty_search_results(self, mock_serper):
        """测试空搜索结果"""
        mock_instance = MagicMock()
        mock_instance.search_general_companies.return_value = []
        mock_serper.return_value = mock_instance
        
        state = self.base_state.copy()
        result_state = self.node.execute(state)
        
        # 验证空结果处理
        self.assertTrue(result_state["company_search_completed"])
        self.assertEqual(len(result_state["search_results"]["companies"]), 0)
        self.assertEqual(result_state["search_results"]["total_companies_found"], 0)
        
        # 应该有低结果数量警告
        self.assertEqual(len(result_state["warnings"]), 1)
        self.assertEqual(result_state["warnings"][0]["type"], "low_results_count")
    
    @patch.dict(os.environ, {"SERPER_API_KEY": "test_key"})
    @patch("langgraph_search.nodes.company_search.SerperCompanySearch")
    def test_low_results_warning(self, mock_serper):
        """测试低结果数量警告"""
        mock_results = [
            {"name": "OnlyOne Corp", "url": "https://onlyone.com", "domain": "onlyone.com"}
        ]
        
        mock_instance = MagicMock()
        mock_instance.search_general_companies.return_value = mock_results
        mock_serper.return_value = mock_instance
        
        state = self.base_state.copy()
        result_state = self.node.execute(state)
        
        # 验证低结果警告
        self.assertEqual(len(result_state["warnings"]), 1)
        self.assertEqual(result_state["warnings"][0]["type"], "low_results_count")
    
    def test_keyword_extraction(self):
        """测试关键词提取功能"""
        test_cases = [
            ("找一些人工智能公司", ["人工智能"]),
            ("搜索硅谷的软件开发企业", ["硅谷", "软件开发"]),
            ("寻找新能源汽车制造商", ["新能源", "汽车", "制造商"]),
            ("renewable energy companies", ["renewable", "energy"]),
        ]
        
        for query, expected_keywords in test_cases:
            with self.subTest(query=query):
                keywords = self.node._extract_keywords_from_query(query)
                
                # 验证提取的关键词包含期望的词语
                for expected in expected_keywords:
                    self.assertTrue(
                        any(expected.lower() in keyword.lower() for keyword in keywords),
                        f"Expected keyword '{expected}' not found in {keywords}"
                    )
    
    def test_domain_extraction(self):
        """测试域名提取功能"""
        test_cases = [
            ({"domain": "example.com"}, "example.com"),
            ({"url": "https://www.example.com/about"}, "example.com"),
            ({"url": "http://example.org"}, "example.org"),
            ({"linkedin": "https://linkedin.com/company/test"}, ""),
            ({}, "")
        ]
        
        for raw_company, expected_domain in test_cases:
            with self.subTest(raw_company=raw_company):
                domain = self.node._extract_domain_from_result(raw_company)
                self.assertEqual(domain, expected_domain)
    
    def test_search_config_preparation(self):
        """测试搜索配置准备"""
        state = self.base_state.copy()
        config = self.node._prepare_search_config(state["search_params"], state)
        
        # 验证配置
        self.assertEqual(config["industry"], "科技")
        self.assertEqual(config["region"], "加州")
        self.assertEqual(config["gl"], "us")
        self.assertEqual(config["num_results"], 10)
        self.assertEqual(config["search_type"], "general")
    
    @patch.dict(os.environ, {"SERPER_API_KEY": "test_key"})
    def test_batch_search(self):
        """测试批量搜索功能"""
        with patch("langgraph_search.nodes.company_search.SerperCompanySearch") as mock_serper:
            mock_results = [
                [{"name": "Company1", "domain": "company1.com"}],
                [{"name": "Company2", "domain": "company2.com"}]
            ]
            
            mock_instance = MagicMock()
            mock_instance.search_general_companies.side_effect = [
                [{"name": "Company1", "domain": "company1.com"}],
                [{"name": "Company2", "domain": "company2.com"}]
            ]
            mock_serper.return_value = mock_instance
            
            configs = [
                {
                    "industry": "tech", 
                    "region": "CA",
                    "gl": "us",
                    "num_results": 10,
                    "search_type": "general"
                },
                {
                    "industry": "finance", 
                    "region": "NY",
                    "gl": "us",
                    "num_results": 10,
                    "search_type": "general"
                }
            ]
            
            results = self.node.batch_search_companies(configs, max_workers=2)
            
            # 验证批量搜索结果
            self.assertEqual(len(results), 2)
            self.assertEqual(len(results[0]), 1)  # 第一个配置的结果
            self.assertEqual(len(results[1]), 1)  # 第二个配置的结果
    
    def test_search_suggestions(self):
        """测试搜索建议功能"""
        test_queries = [
            "科技公司",
            "制造业企业",
            "服务行业"
        ]
        
        for query in test_queries:
            with self.subTest(query=query):
                suggestions = self.node.get_search_suggestions(query)
                
                # 验证建议内容
                self.assertIsInstance(suggestions, list)
                self.assertGreater(len(suggestions), 0)
                
                # 基本建议应该包含
                basic_suggestions = [
                    "尝试使用更通用的行业关键词",
                    "减少地区限制，扩大搜索范围",
                    "使用英文关键词进行搜索"
                ]
                
                for basic in basic_suggestions:
                    self.assertIn(basic, suggestions)
    
    def test_performance_monitoring(self):
        """测试性能监控"""
        with patch.dict(os.environ, {"SERPER_API_KEY": "test_key"}):
            with patch("langgraph_search.nodes.company_search.SerperCompanySearch") as mock_serper:
                mock_instance = MagicMock()
                mock_instance.search_general_companies.return_value = []
                mock_serper.return_value = mock_instance
                
                state = self.base_state.copy()
                result_state = self.node.execute(state)
                
                # 验证性能指标
                self.assertIn("company_search", result_state["performance_metrics"])
                metrics = result_state["performance_metrics"]["company_search"]
                self.assertIn("execution_time", metrics)
                self.assertIn("memory_usage", metrics)
    
    def test_standardization(self):
        """测试结果标准化"""
        raw_results = [
            {
                "name": "  TestCorp Inc  ",  # 测试空格处理
                "url": "https://testcorp.com",
                "industry": "Technology",
                "location": "San Francisco",
                "description": "Test company description"
            },
            {
                "name": "",  # 测试空名称（应该被过滤）
                "url": "https://empty.com"
            },
            {
                "name": "ValidCorp",
                "domain": "validcorp.com",  # 测试直接域名
                "industry": "Software",
                "snippet": "Company snippet description"
            }
        ]
        
        state = self.base_state.copy()
        standardized = self.node._standardize_search_results(raw_results, state)
        
        # 验证标准化结果
        self.assertEqual(len(standardized), 2)  # 空名称的应该被过滤
        
        # 验证第一个结果
        self.assertEqual(standardized[0].name, "TestCorp Inc")  # 空格被清理
        self.assertEqual(standardized[0].domain, "testcorp.com")
        self.assertEqual(standardized[0].website_url, "https://testcorp.com")
        
        # 验证第二个结果
        self.assertEqual(standardized[1].name, "ValidCorp")
        self.assertEqual(standardized[1].domain, "validcorp.com")
        self.assertEqual(standardized[1].description, "Company snippet description")


if __name__ == "__main__":
    unittest.main()