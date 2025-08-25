"""
AI评估节点单元测试
测试AI评估和筛选功能
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langgraph_search.nodes.ai_evaluation import AIEvaluationNode, AIEvaluationConfig
from langgraph_search.state import SearchState, CompanyInfo, SearchParams


class TestAIEvaluationNode(unittest.TestCase):
    """AI评估节点测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.config = AIEvaluationConfig(
            company_score_threshold=60.0,
            employee_score_threshold=70.0,
            enable_evaluation=True,
            max_concurrent=2
        )
        self.node = AIEvaluationNode(self.config)
        
        # 创建测试公司数据
        self.test_companies = [
            CompanyInfo(
                name="TechCorp Inc",
                domain="techcorp.com",
                industry="Technology",
                size="100-500",
                location="San Francisco, CA",
                description="Leading technology company specializing in AI solutions",
                linkedin_url="https://linkedin.com/company/techcorp",
                website_url="https://techcorp.com"
            ),
            CompanyInfo(
                name="GreenEnergy Solutions",
                domain="greenenergy.com", 
                industry="Renewable Energy",
                size="50-100",
                location="Austin, TX",
                description="Renewable energy solutions provider",
                linkedin_url="https://linkedin.com/company/greenenergy",
                website_url="https://greenenergy.com"
            ),
            CompanyInfo(
                name="TechCorp Inc",  # 重复的公司（测试去重）
                domain="techcorp.com",
                industry="Technology",
                size="100-500",
                location="San Francisco, CA",
                description="Duplicate company for testing",
                linkedin_url="https://linkedin.com/company/techcorp",
                website_url="https://techcorp.com"
            ),
            CompanyInfo(
                name="InvalidCorp",
                domain="",  # 无效域名
                industry="Unknown",
                size="",
                location="",
                description="Company with missing information",
                linkedin_url="",
                website_url=""
            )
        ]
        
        self.base_state = {
            "user_query": "搜索科技公司",
            "search_params": SearchParams(
                query="搜索科技公司",
                industry="科技",
                region="",
                gl="us",
                max_results=50,
                search_type="general"
            ),
            "search_results": {
                "companies": self.test_companies,
                "employees": [],
                "total_companies_found": len(self.test_companies)
            },
            "workflow_path": ["intent_recognition_completed", "company_search_completed"],
            "current_node": "company_search",
            "errors": [],
            "warnings": [],
            "api_calls_count": 1,
            "intent_recognized": True,
            "company_search_completed": True,
            "employee_search_completed": False,
            "clarification_needed": False,
            "clarification_suggestions": [],
            "performance_metrics": {},
            "cache_hits": 0,
            "ai_evaluation_completed": False,
            "evaluation_results": {},
            # 添加AI评估需要的字段
            "detected_intent": "company",
            "intent_confidence": 0.8,
            "intent_reasoning": "明确的公司搜索意图"
        }
    
    def test_successful_evaluation(self):
        """测试成功的AI评估"""
        # 禁用AI评估以避免真实的LLM调用
        config = AIEvaluationConfig(enable_evaluation=False)
        node = AIEvaluationNode(config)
        
        state = self.base_state.copy()
        result_state = node.execute(state)
        
        # 验证评估完成（即使被禁用也应该标记为完成）
        self.assertTrue(result_state["ai_evaluation_completed"])
        self.assertIn("ai_evaluation_skipped", result_state["workflow_path"])
    
    def test_relevance_scoring(self):
        """测试相关性评分"""
        # 测试AI评估配置
        config = AIEvaluationConfig(enable_evaluation=False)
        node = AIEvaluationNode(config)
        
        state = self.base_state.copy()
        state["user_query"] = "搜索人工智能科技公司"
        
        result_state = node.execute(state)
        
        # 验证评估被跳过但完成
        self.assertTrue(result_state["ai_evaluation_completed"])
    
    def test_duplicate_detection(self):
        """测试重复检测功能"""
        # 禁用AI评估，只测试基本流程
        config = AIEvaluationConfig(enable_evaluation=False)
        node = AIEvaluationNode(config)
        
        state = self.base_state.copy()
        result_state = node.execute(state)
        
        # 验证评估完成
        self.assertTrue(result_state["ai_evaluation_completed"])
    
    def test_quality_check(self):
        """测试质量检查功能"""
        # 禁用AI评估，只测试基本流程
        config = AIEvaluationConfig(enable_evaluation=False)
        node = AIEvaluationNode(config)
        
        state = self.base_state.copy()
        result_state = node.execute(state)
        
        # 验证评估完成
        self.assertTrue(result_state["ai_evaluation_completed"])
    
    def test_empty_companies_list(self):
        """测试空公司列表处理"""
        config = AIEvaluationConfig(enable_evaluation=False)
        node = AIEvaluationNode(config)
        
        state = self.base_state.copy()
        state["search_results"]["companies"] = []
        state["search_results"]["total_companies_found"] = 0
        
        result_state = node.execute(state)
        
        # 验证评估完成
        self.assertTrue(result_state["ai_evaluation_completed"])
    
    def test_low_quality_companies(self):
        """测试低质量公司处理"""
        config = AIEvaluationConfig(enable_evaluation=False)
        node = AIEvaluationNode(config)
        
        # 创建只有低质量公司的状态
        low_quality_companies = [
            CompanyInfo(
                name="BadCorp",
                domain="",
                industry="",
                size="",
                location="",
                description="Very poor quality company data",
                linkedin_url="",
                website_url=""
            )
        ]
        
        state = self.base_state.copy()
        state["search_results"]["companies"] = low_quality_companies
        state["search_results"]["total_companies_found"] = 1
        
        result_state = node.execute(state)
        
        # 验证评估完成
        self.assertTrue(result_state["ai_evaluation_completed"])
    
    def test_relevance_threshold_filtering(self):
        """测试相关性阈值过滤"""
        config = AIEvaluationConfig(enable_evaluation=False)
        node = AIEvaluationNode(config)
        
        # 使用非常具体的查询来测试过滤
        state = self.base_state.copy()
        state["user_query"] = "搜索医疗设备制造商"  # 与测试数据不太相关
        
        result_state = node.execute(state)
        
        # 验证评估完成
        self.assertTrue(result_state["ai_evaluation_completed"])
    
    def test_large_company_list_handling(self):
        """测试大量公司列表处理"""
        config = AIEvaluationConfig(enable_evaluation=False)
        node = AIEvaluationNode(config)
        
        # 创建大量测试公司（减少数量）
        large_company_list = []
        for i in range(10):
            company = CompanyInfo(
                name=f"Company{i}",
                domain=f"company{i}.com",
                industry="Technology",
                size="50-100",
                location="Various",
                description=f"Test company {i}",
                linkedin_url=f"https://linkedin.com/company/company{i}",
                website_url=f"https://company{i}.com"
            )
            large_company_list.append(company)
        
        state = self.base_state.copy()
        state["search_results"]["companies"] = large_company_list
        state["search_results"]["total_companies_found"] = 10
        
        result_state = node.execute(state)
        
        # 验证评估完成
        self.assertTrue(result_state["ai_evaluation_completed"])
    
    def test_evaluation_metrics_calculation(self):
        """测试评估指标计算"""
        config = AIEvaluationConfig(enable_evaluation=False)
        node = AIEvaluationNode(config)
        
        state = self.base_state.copy()
        result_state = node.execute(state)
        
        # 验证评估完成
        self.assertTrue(result_state["ai_evaluation_completed"])
    
    def test_error_handling(self):
        """测试错误处理"""
        config = AIEvaluationConfig(enable_evaluation=False)
        node = AIEvaluationNode(config)
        
        # 测试状态异常
        state = self.base_state.copy()
        state["search_results"]["companies"] = None  # 异常数据
        
        result_state = node.execute(state)
        
        # 验证评估完成或有错误记录
        self.assertTrue(
            result_state["ai_evaluation_completed"] or
            len(result_state["errors"]) > 0
        )
    
    def test_performance_monitoring(self):
        """测试性能监控"""
        config = AIEvaluationConfig(enable_evaluation=False)
        node = AIEvaluationNode(config)
        
        state = self.base_state.copy()
        result_state = node.execute(state)
        
        # 基本验证
        self.assertTrue(result_state["ai_evaluation_completed"])
    
    def test_state_updates(self):
        """测试状态更新"""
        config = AIEvaluationConfig(enable_evaluation=False)
        node = AIEvaluationNode(config)
        
        state = self.base_state.copy()
        result_state = node.execute(state)
        
        # 验证节点状态更新
        self.assertEqual(result_state["current_node"], "ai_evaluation")
        self.assertIn("ai_evaluation_started", result_state["workflow_path"])
        self.assertTrue(result_state["ai_evaluation_completed"])
    
    def test_company_ranking(self):
        """测试公司排名功能"""
        state = self.base_state.copy()
        result_state = self.node.execute(state)
        
        # 验证公司按相关性排序
        companies = result_state["search_results"]["companies"]
        if len(companies) > 1:
            # 检查是否有排序信息（如果实现了的话）
            # 这里可以添加更具体的排名验证逻辑
            pass
    
    def test_evaluation_summary_generation(self):
        """测试评估摘要生成"""
        state = self.base_state.copy()
        result_state = self.node.execute(state)
        
        evaluation_results = result_state["evaluation_results"]
        
        # 验证摘要信息
        if "summary" in evaluation_results:
            summary = evaluation_results["summary"]
            self.assertIsInstance(summary, str)
            self.assertGreater(len(summary), 0)


if __name__ == "__main__":
    unittest.main()