"""
性能基准测试
测试系统在不同负载和场景下的性能表现
"""

import unittest
import sys
import os
import time
import statistics
import psutil
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langgraph_search.workflows.base_graph import create_search_graph


class TestPerformanceBenchmarks(unittest.TestCase):
    """性能基准测试类"""
    
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
        
        # 性能基准阈值
        self.performance_thresholds = {
            "intent_recognition": {
                "max_execution_time": 1.0,  # 1秒
                "max_memory_mb": 100
            },
            "company_search": {
                "max_execution_time": 10.0,  # 10秒
                "max_memory_mb": 200
            },
            "ai_evaluation": {
                "max_execution_time": 5.0,   # 5秒
                "max_memory_mb": 150
            },
            "overall": {
                "max_total_time": 30.0,      # 30秒
                "max_memory_mb": 500
            }
        }
    
    def measure_performance(self, test_function, *args, **kwargs):
        """性能测量辅助函数"""
        process = psutil.Process()
        
        # 记录开始状态
        start_time = time.time()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        start_cpu = process.cpu_percent()
        
        # 执行测试函数
        result = test_function(*args, **kwargs)
        
        # 记录结束状态
        end_time = time.time()
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        end_cpu = process.cpu_percent()
        
        # 计算性能指标
        performance_data = {
            "execution_time": end_time - start_time,
            "memory_usage_mb": end_memory - start_memory,
            "peak_memory_mb": end_memory,
            "cpu_usage_percent": max(start_cpu, end_cpu),
            "result": result
        }
        
        return performance_data
    
    @patch.dict(os.environ, {"SERPER_API_KEY": "test_key"})
    @patch("langgraph_search.nodes.company_search.SerperCompanySearch")
    def test_intent_recognition_performance(self, mock_serper):
        """测试意图识别性能"""
        # 准备测试查询
        test_queries = [
            "搜索科技公司",
            "找销售经理联系方式",
            "寻找新能源企业的CEO",
            "search tech companies in California",
            "find renewable energy companies"
        ]
        
        execution_times = []
        memory_usages = []
        
        for query in test_queries:
            with self.subTest(query=query):
                def execute_intent_recognition():
                    from langgraph_search.nodes.intent_recognition import intent_recognition_node
                    input_state = self.base_input.copy()
                    input_state["user_query"] = query
                    return intent_recognition_node.execute(input_state)
                
                perf_data = self.measure_performance(execute_intent_recognition)
                
                # 验证性能阈值
                self.assertLess(
                    perf_data["execution_time"],
                    self.performance_thresholds["intent_recognition"]["max_execution_time"],
                    f"Intent recognition too slow for query: {query}"
                )
                
                execution_times.append(perf_data["execution_time"])
                memory_usages.append(perf_data["memory_usage_mb"])
        
        # 统计分析
        avg_execution_time = statistics.mean(execution_times)
        max_execution_time = max(execution_times)
        avg_memory_usage = statistics.mean(memory_usages)
        
        print(f"\n意图识别性能统计:")
        print(f"平均执行时间: {avg_execution_time:.3f}s")
        print(f"最大执行时间: {max_execution_time:.3f}s")
        print(f"平均内存使用: {avg_memory_usage:.2f}MB")
        
        # 验证整体性能
        self.assertLess(avg_execution_time, 0.5, "Average intent recognition should be under 0.5s")
    
    @patch.dict(os.environ, {"SERPER_API_KEY": "test_key"})
    @patch("langgraph_search.nodes.company_search.SerperCompanySearch")
    def test_company_search_performance(self, mock_serper):
        """测试公司搜索性能"""
        # 模拟不同大小的搜索结果
        test_scenarios = [
            {"name": "small_results", "count": 5},
            {"name": "medium_results", "count": 20},
            {"name": "large_results", "count": 50}
        ]
        
        for scenario in test_scenarios:
            with self.subTest(scenario=scenario["name"]):
                # 生成模拟结果
                mock_results = []
                for i in range(scenario["count"]):
                    mock_results.append({
                        "name": f"Company{i}",
                        "domain": f"company{i}.com",
                        "industry": "Technology",
                        "location": f"City{i}",
                        "description": f"Company {i} description"
                    })
                
                mock_instance = MagicMock()
                mock_instance.search_general_companies.return_value = mock_results
                mock_serper.return_value = mock_instance
                
                def execute_company_search():
                    from langgraph_search.nodes.company_search import company_search_node
                    from langgraph_search.state import SearchParams
                    
                    input_state = self.base_input.copy()
                    input_state["user_query"] = "搜索科技公司"
                    input_state["search_params"] = SearchParams(
                        search_type="company",
                        industry="科技",
                        region="",
                        gl="us",
                        max_results=scenario["count"]
                    )
                    input_state["intent_recognized"] = True
                    
                    return company_search_node.execute(input_state)
                
                perf_data = self.measure_performance(execute_company_search)
                
                # 验证性能阈值（根据结果数量调整）
                expected_time = min(10.0, scenario["count"] * 0.1 + 2.0)
                self.assertLess(
                    perf_data["execution_time"],
                    expected_time,
                    f"Company search too slow for {scenario['name']}"
                )
                
                print(f"\n公司搜索性能 ({scenario['name']}):")
                print(f"结果数量: {scenario['count']}")
                print(f"执行时间: {perf_data['execution_time']:.3f}s")
                print(f"内存使用: {perf_data['memory_usage_mb']:.2f}MB")
    
    @patch.dict(os.environ, {"SERPER_API_KEY": "test_key"})
    @patch("langgraph_search.nodes.company_search.SerperCompanySearch")
    def test_full_workflow_performance(self, mock_serper):
        """测试完整工作流性能"""
        # 模拟搜索结果
        mock_results = [
            {
                "name": "TechCorp",
                "domain": "techcorp.com",
                "industry": "Technology",
                "location": "San Francisco",
                "description": "Leading tech company"
            },
            {
                "name": "InnovateSoft",
                "domain": "innovatesoft.com",
                "industry": "Software",
                "location": "Austin",
                "description": "Innovative software solutions"
            }
        ]
        
        mock_instance = MagicMock()
        mock_instance.search_general_companies.return_value = mock_results
        mock_serper.return_value = mock_instance
        
        def execute_full_workflow():
            input_state = self.base_input.copy()
            input_state["user_query"] = "搜索美国的科技公司"
            return self.graph.invoke(input_state)
        
        perf_data = self.measure_performance(execute_full_workflow)
        result = perf_data["result"]
        
        # 验证工作流完成
        self.assertTrue(result["intent_recognized"], "Workflow should complete successfully")
        
        # 验证性能阈值
        self.assertLess(
            perf_data["execution_time"],
            self.performance_thresholds["overall"]["max_total_time"],
            "Full workflow execution too slow"
        )
        
        # 验证内存使用
        self.assertLess(
            perf_data["peak_memory_mb"],
            self.performance_thresholds["overall"]["max_memory_mb"],
            "Memory usage too high"
        )
        
        print(f"\n完整工作流性能:")
        print(f"总执行时间: {perf_data['execution_time']:.3f}s")
        print(f"内存使用: {perf_data['memory_usage_mb']:.2f}MB")
        print(f"峰值内存: {perf_data['peak_memory_mb']:.2f}MB")
        print(f"CPU使用率: {perf_data['cpu_usage_percent']:.1f}%")
    
    @patch.dict(os.environ, {"SERPER_API_KEY": "test_key"})
    @patch("langgraph_search.nodes.company_search.SerperCompanySearch")
    def test_concurrent_execution_performance(self, mock_serper):
        """测试并发执行性能"""
        mock_results = [{"name": "TestCorp", "domain": "test.com"}]
        
        mock_instance = MagicMock()
        mock_instance.search_general_companies.return_value = mock_results
        mock_serper.return_value = mock_instance
        
        def single_execution():
            input_state = self.base_input.copy()
            input_state["user_query"] = f"搜索科技公司 {time.time()}"  # 唯一查询
            return self.graph.invoke(input_state)
        
        # 测试不同并发级别
        concurrency_levels = [1, 3, 5, 10]
        
        for level in concurrency_levels:
            with self.subTest(concurrency=level):
                start_time = time.time()
                
                # 并发执行
                with ThreadPoolExecutor(max_workers=level) as executor:
                    futures = [executor.submit(single_execution) for _ in range(level)]
                    results = [future.result() for future in as_completed(futures)]
                
                total_time = time.time() - start_time
                avg_time_per_request = total_time / level
                
                # 验证所有请求成功
                successful_results = sum(1 for r in results if r.get("intent_recognized", False))
                success_rate = successful_results / level
                
                print(f"\n并发执行性能 (并发级别: {level}):")
                print(f"总时间: {total_time:.3f}s")
                print(f"平均每请求时间: {avg_time_per_request:.3f}s")
                print(f"成功率: {success_rate:.2%}")
                
                # 验证性能要求
                self.assertGreater(success_rate, 0.8, "Success rate should be > 80%")
                self.assertLess(total_time, level * 15, "Concurrent execution should have reasonable scaling")
    
    def test_memory_leak_detection(self):
        """测试内存泄漏检测"""
        process = psutil.Process()
        
        # 记录初始内存
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 执行多次工作流
        iterations = 10
        memory_readings = []
        
        for i in range(iterations):
            input_state = self.base_input.copy()
            input_state["user_query"] = f"测试内存泄漏 {i}"
            
            # 执行意图识别（轻量级测试）
            from langgraph_search.nodes.intent_recognition import intent_recognition_node
            result = intent_recognition_node.execute(input_state)
            
            # 记录内存使用
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_readings.append(current_memory)
            
            # 强制垃圾收集
            import gc
            gc.collect()
        
        # 分析内存趋势
        final_memory = memory_readings[-1]
        memory_growth = final_memory - initial_memory
        
        print(f"\n内存泄漏检测:")
        print(f"初始内存: {initial_memory:.2f}MB")
        print(f"最终内存: {final_memory:.2f}MB")
        print(f"内存增长: {memory_growth:.2f}MB")
        print(f"平均每次迭代内存增长: {memory_growth/iterations:.3f}MB")
        
        # 验证内存泄漏阈值（每次迭代不应该增长超过1MB）
        self.assertLess(
            memory_growth / iterations, 1.0,
            "Potential memory leak detected"
        )
    
    @patch.dict(os.environ, {"SERPER_API_KEY": "test_key"})
    @patch("langgraph_search.nodes.company_search.SerperCompanySearch")
    def test_caching_performance_impact(self, mock_serper):
        """测试缓存性能影响"""
        mock_results = [{"name": "CachedCorp", "domain": "cached.com"}]
        
        mock_instance = MagicMock()
        mock_instance.search_general_companies.return_value = mock_results
        mock_serper.return_value = mock_instance
        
        query = "测试缓存性能"
        
        # 第一次执行（无缓存）
        def first_execution():
            input_state = self.base_input.copy()
            input_state["user_query"] = query
            return self.graph.invoke(input_state)
        
        perf_data_1 = self.measure_performance(first_execution)
        
        # 第二次执行（可能有缓存）
        def second_execution():
            input_state = self.base_input.copy()
            input_state["user_query"] = query
            return self.graph.invoke(input_state)
        
        perf_data_2 = self.measure_performance(second_execution)
        
        # 分析缓存效果
        time_improvement = (perf_data_1["execution_time"] - perf_data_2["execution_time"]) / perf_data_1["execution_time"]
        
        print(f"\n缓存性能影响:")
        print(f"首次执行时间: {perf_data_1['execution_time']:.3f}s")
        print(f"二次执行时间: {perf_data_2['execution_time']:.3f}s")
        print(f"时间改善: {time_improvement:.2%}")
        
        # 如果有缓存命中，应该有性能提升
        if perf_data_2["result"]["cache_hits"] > perf_data_1["result"]["cache_hits"]:
            self.assertGreaterEqual(
                time_improvement, -0.1,  # 允许10%的性能波动
                "Caching should not significantly worsen performance"
            )
    
    def test_large_dataset_processing_performance(self):
        """测试大数据集处理性能"""
        # 创建大型测试数据集
        from langgraph_search.state import CompanyInfo
        
        large_dataset = []
        for i in range(1000):
            company = CompanyInfo(
                name=f"Company{i}",
                domain=f"company{i}.com",
                industry="Technology",
                size="100-500",
                location=f"City{i}",
                description=f"Large dataset company {i}",
                linkedin_url=f"https://linkedin.com/company/company{i}",
                website_url=f"https://company{i}.com"
            )
            large_dataset.append(company)
        
        def process_large_dataset():
            from langgraph_search.nodes.ai_evaluation import ai_evaluation_node
            
            input_state = self.base_input.copy()
            input_state["user_query"] = "处理大数据集测试"
            input_state["search_results"]["companies"] = large_dataset
            input_state["search_results"]["total_companies_found"] = len(large_dataset)
            input_state["company_search_completed"] = True
            
            return ai_evaluation_node.execute(input_state)
        
        perf_data = self.measure_performance(process_large_dataset)
        
        # 验证大数据集处理性能
        self.assertLess(
            perf_data["execution_time"], 60,
            "Large dataset processing should complete within 60 seconds"
        )
        
        self.assertLess(
            perf_data["peak_memory_mb"], 1000,
            "Memory usage should stay under 1GB for large datasets"
        )
        
        print(f"\n大数据集处理性能 (1000家公司):")
        print(f"执行时间: {perf_data['execution_time']:.3f}s")
        print(f"内存使用: {perf_data['memory_usage_mb']:.2f}MB")
        print(f"处理速度: {len(large_dataset)/perf_data['execution_time']:.1f} 公司/秒")
    
    def test_error_handling_performance_impact(self):
        """测试错误处理对性能的影响"""
        # 测试正常执行
        def normal_execution():
            from langgraph_search.nodes.intent_recognition import intent_recognition_node
            input_state = self.base_input.copy()
            input_state["user_query"] = "正常查询测试"
            return intent_recognition_node.execute(input_state)
        
        normal_perf = self.measure_performance(normal_execution)
        
        # 测试错误执行
        def error_execution():
            from langgraph_search.nodes.intent_recognition import intent_recognition_node
            input_state = self.base_input.copy()
            input_state["user_query"] = None  # 触发错误
            return intent_recognition_node.execute(input_state)
        
        error_perf = self.measure_performance(error_execution)
        
        # 分析错误处理的性能影响
        performance_overhead = (error_perf["execution_time"] - normal_perf["execution_time"]) / normal_perf["execution_time"]
        
        print(f"\n错误处理性能影响:")
        print(f"正常执行时间: {normal_perf['execution_time']:.3f}s")
        print(f"错误执行时间: {error_perf['execution_time']:.3f}s")
        print(f"性能开销: {performance_overhead:.2%}")
        
        # 验证错误处理不应该显著影响性能
        self.assertLess(
            performance_overhead, 2.0,  # 错误处理开销不应该超过200%
            "Error handling should not cause excessive performance overhead"
        )


if __name__ == "__main__":
    # 运行性能测试时可能需要更长的超时时间
    unittest.main(verbosity=2)