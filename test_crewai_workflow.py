#!/usr/bin/env python3
"""
CrewAI工作流综合测试脚本
测试完整的智能搜索多智能体工作流
"""

import os
import sys
import json
import time
import traceback
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

# 加载环境变量
load_dotenv()

class CrewAIWorkflowTester:
    """CrewAI工作流测试器"""
    
    def __init__(self):
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': [],
            'start_time': time.time()
        }
        
        print("🧪 CrewAI智能搜索工作流综合测试")
        print("=" * 60)
    
    def run_test(self, test_name: str, test_func, *args, **kwargs) -> bool:
        """运行单个测试"""
        self.test_results['total_tests'] += 1
        print(f"\n📋 测试 {self.test_results['total_tests']}: {test_name}")
        
        try:
            start_time = time.time()
            result = test_func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            if result:
                print(f"✅ 通过 (耗时: {execution_time:.2f}秒)")
                self.test_results['passed_tests'] += 1
                self.test_results['test_details'].append({
                    'name': test_name,
                    'status': 'PASSED',
                    'execution_time': execution_time,
                    'error': None
                })
                return True
            else:
                print(f"❌ 失败 (耗时: {execution_time:.2f}秒)")
                self.test_results['failed_tests'] += 1
                self.test_results['test_details'].append({
                    'name': test_name,
                    'status': 'FAILED',
                    'execution_time': execution_time,
                    'error': 'Test returned False'
                })
                return False
                
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"❌ 异常: {str(e)} (耗时: {execution_time:.2f}秒)")
            self.test_results['failed_tests'] += 1
            self.test_results['test_details'].append({
                'name': test_name,
                'status': 'ERROR',
                'execution_time': execution_time,
                'error': str(e)
            })
            if hasattr(e, '__traceback__'):
                traceback.print_exc()
            return False
    
    def test_environment_setup(self) -> bool:
        """测试环境配置"""
        print("  检查环境变量...")
        
        required_vars = ['SERPER_API_KEY']
        optional_vars = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY']
        
        for var in required_vars:
            if not os.getenv(var):
                print(f"    ❌ 缺少必需环境变量: {var}")
                return False
            else:
                print(f"    ✅ {var}: 已配置")
        
        for var in optional_vars:
            if os.getenv(var):
                print(f"    ✅ {var}: 已配置")
            else:
                print(f"    ⚠️ {var}: 未配置 (可选)")
        
        return True
    
    def test_tools_import(self) -> bool:
        """测试工具导入"""
        print("  导入CrewAI工具模块...")
        
        try:
            from crewai_tools import SearchTools, AnalysisTools, get_all_tools
            print("    ✅ 工具模块导入成功")
            
            # 测试工具实例化
            search_tools = SearchTools()
            analysis_tools = AnalysisTools()
            all_tools = get_all_tools()
            
            print(f"    ✅ 获取到 {len(all_tools)} 个工具")
            return True
            
        except ImportError as e:
            print(f"    ❌ 工具导入失败: {e}")
            return False
    
    def test_agents_import(self) -> bool:
        """测试智能体导入"""
        print("  导入CrewAI智能体模块...")
        
        try:
            from crewai_agents import IntelligentSearchAgents, AgentOrchestrator
            print("    ✅ 智能体模块导入成功")
            
            # 测试智能体创建
            orchestrator = AgentOrchestrator()
            validation = orchestrator.validate_agents()
            
            if validation['validation_passed']:
                print(f"    ✅ {validation['total_agents']} 个智能体验证通过")
                return True
            else:
                print(f"    ❌ 智能体验证失败: {validation}")
                return False
                
        except ImportError as e:
            print(f"    ❌ 智能体导入失败: {e}")
            return False
    
    def test_tasks_import(self) -> bool:
        """测试任务导入"""
        print("  导入CrewAI任务模块...")
        
        try:
            from crewai_tasks import IntelligentSearchTasks, TaskOrchestrator
            print("    ✅ 任务模块导入成功")
            
            # 测试任务编排器
            orchestrator = TaskOrchestrator()
            sequence = orchestrator.get_task_sequence()
            
            print(f"    ✅ 任务序列包含 {len(sequence)} 个步骤")
            for i, task_name in enumerate(sequence, 1):
                print(f"      {i}. {task_name}")
            
            return True
            
        except ImportError as e:
            print(f"    ❌ 任务导入失败: {e}")
            return False
    
    def test_main_crew_import(self) -> bool:
        """测试主程序导入"""
        print("  导入CrewAI主程序模块...")
        
        try:
            from crewai_main import IntelligentSearchCrew, SearchCrewManager
            print("    ✅ 主程序模块导入成功")
            
            return True
            
        except ImportError as e:
            print(f"    ❌ 主程序导入失败: {e}")
            return False
    
    def test_crew_initialization(self) -> bool:
        """测试Crew初始化"""
        print("  测试Crew初始化...")
        
        try:
            from crewai_main import IntelligentSearchCrew
            
            # 创建Crew实例
            crew = IntelligentSearchCrew(
                llm_model="gpt-4",
                verbose=False  # 减少输出
            )
            print("    ✅ Crew实例创建成功")
            
            # 健康检查
            health = crew.health_check()
            print(f"    ✅ 健康检查: {health['overall_status']}")
            
            if health['overall_status'] != 'healthy':
                print(f"    ⚠️ 健康检查警告: {health}")
            
            # 获取Crew信息
            info = crew.get_crew_info()
            print(f"    ✅ Crew信息获取成功 - {info['agents_info']['total_agents']} 个智能体")
            
            return True
            
        except Exception as e:
            print(f"    ❌ Crew初始化失败: {e}")
            return False
    
    def test_tools_functionality(self) -> bool:
        """测试工具功能"""
        print("  测试工具基础功能...")
        
        try:
            from crewai_tools import SearchTools, AnalysisTools
            
            # 测试关键词生成工具
            keyword_tool = SearchTools.keyword_generator_tool()
            test_requirement = "我想找卖数位板的公司，要求支持4K分辨率，价格1000-3000元，深圳地区"
            
            print(f"    测试需求: {test_requirement}")
            keywords_result = keyword_tool._run(user_requirement=test_requirement, max_keywords=5)
            
            if keywords_result.get('success'):
                keywords = keywords_result.get('keywords', [])
                print(f"    ✅ 关键词生成成功: {keywords}")
            else:
                print(f"    ⚠️ 关键词生成警告: {keywords_result.get('error')}")
            
            # 测试需求解析工具
            parser_tool = AnalysisTools.requirement_parser_tool()
            parsing_result = parser_tool._run(user_requirement=test_requirement)
            
            if parsing_result.get('success'):
                parsed_req = parsing_result.get('parsed_requirement', {})
                print(f"    ✅ 需求解析成功 - 产品: {parsed_req.get('product')}")
            else:
                print(f"    ⚠️ 需求解析警告: {parsing_result.get('error')}")
            
            return True
            
        except Exception as e:
            print(f"    ❌ 工具功能测试失败: {e}")
            return False
    
    def test_streamlit_app_structure(self) -> bool:
        """测试Streamlit应用结构"""
        print("  检查Streamlit应用文件...")
        
        streamlit_file = Path(__file__).parent / "streamlit_intelligent_search.py"
        
        if not streamlit_file.exists():
            print("    ❌ Streamlit应用文件不存在")
            return False
        
        print("    ✅ Streamlit应用文件存在")
        
        # 检查文件内容结构
        try:
            with open(streamlit_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_functions = [
                'main()',
                'intelligent_search_interface()',
                'search_results_interface()',
                'system_status_interface()'
            ]
            
            missing_functions = []
            for func in required_functions:
                if func.replace('()', '') not in content:
                    missing_functions.append(func)
            
            if missing_functions:
                print(f"    ⚠️ 缺少函数: {missing_functions}")
            else:
                print("    ✅ Streamlit应用结构完整")
            
            return len(missing_functions) == 0
            
        except Exception as e:
            print(f"    ❌ Streamlit应用检查失败: {e}")
            return False
    
    def test_file_structure(self) -> bool:
        """测试文件结构"""
        print("  检查项目文件结构...")
        
        required_files = [
            'crewai_tools.py',
            'crewai_agents.py', 
            'crewai_tasks.py',
            'crewai_main.py',
            'streamlit_intelligent_search.py'
        ]
        
        project_root = Path(__file__).parent
        missing_files = []
        
        for file in required_files:
            file_path = project_root / file
            if file_path.exists():
                print(f"    ✅ {file}")
            else:
                print(f"    ❌ {file} (缺失)")
                missing_files.append(file)
        
        return len(missing_files) == 0
    
    def test_integration_compatibility(self) -> bool:
        """测试集成兼容性"""
        print("  测试组件集成兼容性...")
        
        try:
            # 测试组件间的基础集成
            from crewai_agents import AgentOrchestrator
            from crewai_tasks import TaskOrchestrator
            from crewai_tools import get_all_tools
            
            # 创建组件实例
            agent_orch = AgentOrchestrator()
            task_orch = TaskOrchestrator()
            tools = get_all_tools()
            
            print(f"    ✅ 智能体编排器: {len(agent_orch.agents)} 个智能体")
            print(f"    ✅ 任务编排器: {len(task_orch.task_sequence)} 个任务")
            print(f"    ✅ 工具集合: {len(tools)} 个工具")
            
            # 测试任务链创建的基本结构
            agents_dict = {
                'requirement_analyzer': agent_orch.get_agent('requirement_analyzer'),
                'search_strategist': agent_orch.get_agent('search_strategist'),
                'search_executor': agent_orch.get_agent('search_executor'),
                'scoring_analyst': agent_orch.get_agent('scoring_analyst'),
                'result_optimizer': agent_orch.get_agent('result_optimizer')
            }
            
            # 验证所有智能体都存在
            for name, agent in agents_dict.items():
                if agent is None:
                    print(f"    ❌ 智能体 {name} 不存在")
                    return False
            
            print("    ✅ 所有智能体都可正常获取")
            return True
            
        except Exception as e:
            print(f"    ❌ 集成兼容性测试失败: {e}")
            return False
    
    def generate_test_report(self):
        """生成测试报告"""
        total_time = time.time() - self.test_results['start_time']
        
        print("\n" + "=" * 60)
        print("📊 测试报告")
        print("=" * 60)
        
        print(f"总测试数: {self.test_results['total_tests']}")
        print(f"通过测试: {self.test_results['passed_tests']} ✅")
        print(f"失败测试: {self.test_results['failed_tests']} ❌")
        print(f"成功率: {self.test_results['passed_tests']/self.test_results['total_tests']*100:.1f}%")
        print(f"总耗时: {total_time:.2f}秒")
        
        print(f"\n📋 详细结果:")
        for detail in self.test_results['test_details']:
            status_icon = "✅" if detail['status'] == 'PASSED' else "❌"
            print(f"{status_icon} {detail['name']} ({detail['execution_time']:.2f}秒)")
            if detail['error']:
                print(f"    错误: {detail['error']}")
        
        # 保存测试报告
        try:
            report_file = Path(__file__).parent / 'output' / 'test_report.json'
            report_file.parent.mkdir(exist_ok=True)
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\n💾 测试报告已保存: {report_file}")
            
        except Exception as e:
            print(f"\n⚠️ 测试报告保存失败: {e}")
        
        # 总结
        if self.test_results['failed_tests'] == 0:
            print(f"\n🎉 所有测试通过！CrewAI智能搜索工作流已准备就绪。")
            print("💡 下一步: 运行 'streamlit run streamlit_intelligent_search.py' 启动Web界面")
        else:
            print(f"\n⚠️ 有 {self.test_results['failed_tests']} 个测试失败，请检查配置和依赖。")


def main():
    """主测试函数"""
    tester = CrewAIWorkflowTester()
    
    # 执行测试套件
    test_suite = [
        ("环境配置检查", tester.test_environment_setup),
        ("文件结构检查", tester.test_file_structure),
        ("工具模块导入", tester.test_tools_import),
        ("智能体模块导入", tester.test_agents_import),
        ("任务模块导入", tester.test_tasks_import),
        ("主程序模块导入", tester.test_main_crew_import),
        ("Crew初始化测试", tester.test_crew_initialization),
        ("工具功能测试", tester.test_tools_functionality),
        ("Streamlit应用结构", tester.test_streamlit_app_structure),
        ("集成兼容性测试", tester.test_integration_compatibility)
    ]
    
    # 运行所有测试
    for test_name, test_func in test_suite:
        tester.run_test(test_name, test_func)
    
    # 生成测试报告
    tester.generate_test_report()
    
    return tester.test_results['failed_tests'] == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)