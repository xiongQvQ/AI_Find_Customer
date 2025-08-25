"""
pytest配置文件
提供测试的全局配置、fixtures和工具函数
"""

import pytest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph_search.state import SearchState, SearchParams, CompanyInfo
from langgraph_search.workflows.base_graph import create_search_graph


@pytest.fixture(scope="session")
def test_api_key():
    """提供测试用的API密钥"""
    return "test_serper_api_key_for_testing"


@pytest.fixture(autouse=True)
def mock_api_environment(test_api_key):
    """自动模拟API环境变量"""
    with patch.dict(os.environ, {"SERPER_API_KEY": test_api_key}):
        yield


@pytest.fixture
def base_search_state():
    """基础搜索状态fixture"""
    return {
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
        "cache_hits": 0,
        "ai_evaluation_completed": False,
        "evaluation_results": {}
    }


@pytest.fixture
def sample_search_params():
    """示例搜索参数fixture"""
    return SearchParams(
        search_type="company",
        industry="科技",
        region="加州",
        gl="us",
        max_results=10,
        use_custom_query=False,
        query="",
        position="",
        company_name="",
        size_filter="",
        location_filter=""
    )


@pytest.fixture
def sample_companies():
    """示例公司数据fixture"""
    return [
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
            name="InnovateSoft LLC",
            domain="innovatesoft.com",
            industry="Software Development",
            size="200-1000",
            location="Seattle, WA", 
            description="Innovative software development company",
            linkedin_url="https://linkedin.com/company/innovatesoft",
            website_url="https://innovatesoft.com"
        )
    ]


@pytest.fixture
def mock_serper_company_search():
    """模拟Serper公司搜索fixture"""
    with patch("langgraph_search.nodes.company_search.SerperCompanySearch") as mock_serper:
        mock_instance = MagicMock()
        
        # 默认搜索结果
        mock_instance.search_general_companies.return_value = [
            {
                "name": "MockCorp",
                "url": "https://mockcorp.com",
                "domain": "mockcorp.com",
                "industry": "Technology",
                "location": "Mock City",
                "description": "Mock company for testing"
            }
        ]
        
        mock_instance.search_linkedin_companies.return_value = [
            {
                "name": "LinkedInMockCorp",
                "linkedin": "https://linkedin.com/company/linkedinmockcorp",
                "industry": "Social Media",
                "location": "Mock Valley",
                "description": "LinkedIn mock company"
            }
        ]
        
        mock_serper.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_serper_employee_search():
    """模拟Serper员工搜索fixture"""
    with patch("langgraph_search.nodes.employee_search.SerperEmployeeSearch") as mock_serper:
        mock_instance = MagicMock()
        
        mock_instance.search_employees.return_value = [
            {
                "name": "John Doe",
                "position": "CEO",
                "company": "MockCorp",
                "linkedin": "https://linkedin.com/in/johndoe",
                "location": "Mock City"
            }
        ]
        
        mock_serper.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def search_graph():
    """搜索工作流图fixture"""
    return create_search_graph()


@pytest.fixture
def temp_output_dir():
    """临时输出目录fixture"""
    temp_dir = tempfile.mkdtemp(prefix="langgraph_test_")
    yield temp_dir
    # 清理临时目录
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def performance_monitor():
    """性能监控fixture"""
    import time
    import psutil
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.start_memory = None
            self.process = psutil.Process()
        
        def start_monitoring(self):
            self.start_time = time.time()
            self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        def get_metrics(self):
            if self.start_time is None:
                raise ValueError("Monitoring not started")
            
            end_time = time.time()
            end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            
            return {
                "execution_time": end_time - self.start_time,
                "memory_usage_mb": end_memory - self.start_memory,
                "peak_memory_mb": end_memory,
                "cpu_percent": self.process.cpu_percent()
            }
    
    return PerformanceMonitor()


@pytest.fixture
def mock_llm_response():
    """模拟LLM响应fixture"""
    def _mock_response(content="Mock LLM response"):
        return {
            "content": content,
            "role": "assistant",
            "model": "mock-model"
        }
    
    return _mock_response


class TestHelpers:
    """测试辅助工具类"""
    
    @staticmethod
    def assert_search_state_valid(state: Dict[str, Any]):
        """验证搜索状态的有效性"""
        required_keys = [
            "user_query", "search_params", "search_results",
            "workflow_path", "current_node", "errors", "warnings",
            "api_calls_count", "intent_recognized"
        ]
        
        for key in required_keys:
            assert key in state, f"Missing required key: {key}"
        
        # 验证数据类型
        assert isinstance(state["user_query"], str)
        assert isinstance(state["search_results"], dict)
        assert isinstance(state["workflow_path"], list)
        assert isinstance(state["errors"], list)
        assert isinstance(state["warnings"], list)
        assert isinstance(state["api_calls_count"], int)
        assert isinstance(state["intent_recognized"], bool)
    
    @staticmethod
    def assert_company_info_valid(company: CompanyInfo):
        """验证公司信息的有效性"""
        assert hasattr(company, "name"), "Company must have name"
        assert hasattr(company, "domain"), "Company must have domain"
        assert company.name.strip() != "", "Company name cannot be empty"
        
        # 至少要有一种联系方式
        has_contact = any([
            company.domain,
            company.linkedin_url,
            company.website_url
        ])
        assert has_contact, "Company must have at least one contact method"
    
    @staticmethod
    def create_mock_search_result(count: int = 1, result_type: str = "company"):
        """创建模拟搜索结果"""
        if result_type == "company":
            return [
                {
                    "name": f"TestCorp{i}",
                    "url": f"https://testcorp{i}.com",
                    "domain": f"testcorp{i}.com",
                    "industry": "Technology",
                    "location": f"Test City {i}",
                    "description": f"Test company {i} description"
                }
                for i in range(count)
            ]
        elif result_type == "employee":
            return [
                {
                    "name": f"Test Person {i}",
                    "position": "Test Position",
                    "company": f"TestCorp{i}",
                    "linkedin": f"https://linkedin.com/in/testperson{i}",
                    "location": f"Test City {i}"
                }
                for i in range(count)
            ]
        else:
            raise ValueError(f"Unknown result type: {result_type}")


@pytest.fixture
def test_helpers():
    """测试辅助工具fixture"""
    return TestHelpers


# 性能测试配置
def pytest_configure(config):
    """pytest配置"""
    # 添加自定义标记
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )


# 测试收集钩子
def pytest_collection_modifyitems(config, items):
    """修改测试收集项"""
    for item in items:
        # 为性能测试添加标记
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        
        # 为集成测试添加标记
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # 为端到端测试添加标记
        if "e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)


# 测试会话开始
def pytest_sessionstart(session):
    """测试会话开始时执行"""
    print("\n=== LangGraph智能搜索测试套件 ===")
    print("开始执行测试...")


# 测试会话结束
def pytest_sessionfinish(session, exitstatus):
    """测试会话结束时执行"""
    print("\n=== 测试执行完成 ===")
    if exitstatus == 0:
        print("所有测试通过! ✅")
    else:
        print(f"测试失败，退出状态: {exitstatus} ❌")


# 命令行选项
def pytest_addoption(parser):
    """添加命令行选项"""
    parser.addoption(
        "--run-slow", action="store_true", default=False,
        help="run slow tests"
    )
    parser.addoption(
        "--run-performance", action="store_true", default=False,
        help="run performance tests"
    )


def pytest_runtest_setup(item):
    """测试运行前设置"""
    # 检查慢速测试
    if "slow" in item.keywords and not item.config.getoption("--run-slow"):
        pytest.skip("need --run-slow option to run slow tests")
    
    # 检查性能测试
    if "performance" in item.keywords and not item.config.getoption("--run-performance"):
        pytest.skip("need --run-performance option to run performance tests")