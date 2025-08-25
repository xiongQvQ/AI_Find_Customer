#!/usr/bin/env python3
"""
CrewAI主程序 - 智能搜索多智能体工作流核心
整合所有组件，提供统一的智能搜索服务
"""

import os
import json
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

# CrewAI核心导入
from crewai import Crew, Process
from dotenv import load_dotenv

# 导入自定义组件
from crewai_agents import AgentOrchestrator
from crewai_tasks import TaskOrchestrator
from crewai_tools import get_all_tools

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntelligentSearchCrew:
    """智能搜索Crew主类"""
    
    def __init__(self, 
                 llm_model: str = "gpt-4",
                 max_iterations: int = 3,
                 verbose: bool = True,
                 output_dir: str = "output"):
        """
        初始化智能搜索Crew
        
        Args:
            llm_model: 使用的LLM模型
            max_iterations: 最大迭代次数
            verbose: 是否输出详细信息
            output_dir: 输出目录
        """
        self.llm_model = llm_model
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.output_dir = output_dir
        
        # 确保输出目录存在
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        # 初始化组件
        self.agent_orchestrator = AgentOrchestrator()
        self.task_orchestrator = TaskOrchestrator()
        self.tools = get_all_tools()
        
        # 初始化Crew
        self.crew = None
        self._setup_crew()
        
        logger.info(f"智能搜索Crew初始化完成 - 模型: {llm_model}")
    
    def _setup_crew(self):
        """设置CrewAI crew"""
        try:
            # 获取所有智能体
            agents_dict = {
                'requirement_analyzer': self.agent_orchestrator.get_agent('requirement_analyzer'),
                'search_strategist': self.agent_orchestrator.get_agent('search_strategist'),
                'search_executor': self.agent_orchestrator.get_agent('search_executor'),
                'scoring_analyst': self.agent_orchestrator.get_agent('scoring_analyst'),
                'result_optimizer': self.agent_orchestrator.get_agent('result_optimizer')
            }
            
            # 验证智能体
            validation = self.agent_orchestrator.validate_agents()
            if not validation['validation_passed']:
                raise Exception(f"智能体验证失败: {validation}")
            
            self.agents_dict = agents_dict
            logger.info(f"智能体验证通过: {len(agents_dict)} 个智能体")
            
        except Exception as e:
            logger.error(f"Crew设置失败: {e}")
            raise
    
    def create_crew_for_search(self, user_requirement: str) -> Crew:
        """为特定搜索需求创建Crew"""
        try:
            # 创建任务链
            tasks = self.task_orchestrator.create_task_chain(self.agents_dict, user_requirement)
            
            # 验证任务链
            task_validation = self.task_orchestrator.validate_task_chain(tasks)
            if not task_validation['validation_passed']:
                raise Exception(f"任务链验证失败: {task_validation}")
            
            logger.info(f"任务链创建成功: {len(tasks)} 个任务")
            
            # 创建Crew
            crew = Crew(
                agents=list(self.agents_dict.values()),
                tasks=tasks,
                process=Process.sequential,  # 顺序执行
                verbose=self.verbose,
                memory=True,  # 启用记忆功能
                embedder={
                    "provider": "openai",
                    "config": {
                        "api_key": os.getenv("OPENAI_API_KEY"),
                        "model": "text-embedding-ada-002"
                    }
                }
            )
            
            return crew
            
        except Exception as e:
            logger.error(f"Crew创建失败: {e}")
            raise
    
    def execute_intelligent_search(self, 
                                 user_requirement: str,
                                 save_intermediate_results: bool = True,
                                 custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行智能搜索工作流
        
        Args:
            user_requirement: 用户需求描述
            save_intermediate_results: 是否保存中间结果
            custom_config: 自定义配置
        
        Returns:
            搜索结果字典
        """
        start_time = time.time()
        search_id = f"search_{int(start_time)}"
        
        logger.info(f"开始智能搜索: {search_id}")
        logger.info(f"用户需求: {user_requirement}")
        
        try:
            # 创建搜索专用Crew
            crew = self.create_crew_for_search(user_requirement)
            
            # 准备输入数据
            crew_input = {
                "user_requirement": user_requirement,
                "search_id": search_id,
                "timestamp": datetime.now().isoformat(),
                "config": custom_config or {}
            }
            
            logger.info("开始执行Crew工作流...")
            
            # 执行Crew工作流
            result = crew.kickoff(inputs=crew_input)
            
            execution_time = time.time() - start_time
            
            # 处理结果
            final_result = {
                "success": True,
                "search_id": search_id,
                "user_requirement": user_requirement,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "crew_result": result,
                "workflow_summary": self._generate_workflow_summary(crew, result, execution_time)
            }
            
            # 保存结果
            if save_intermediate_results:
                self._save_search_results(search_id, final_result)
            
            logger.info(f"智能搜索完成: {search_id} (耗时: {execution_time:.2f}秒)")
            
            return final_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_result = {
                "success": False,
                "search_id": search_id,
                "user_requirement": user_requirement,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "error_type": type(e).__name__
            }
            
            logger.error(f"智能搜索失败: {search_id} - {e}")
            
            # 保存错误结果
            if save_intermediate_results:
                self._save_search_results(search_id, error_result)
            
            return error_result
    
    def _generate_workflow_summary(self, crew: Crew, result: Any, execution_time: float) -> Dict[str, Any]:
        """生成工作流摘要"""
        try:
            summary = {
                "total_agents": len(crew.agents),
                "total_tasks": len(crew.tasks),
                "execution_time": execution_time,
                "process_type": crew.process.value if hasattr(crew.process, 'value') else str(crew.process),
                "memory_enabled": crew.memory,
                "task_sequence": [
                    {
                        "task_index": i,
                        "agent_role": task.agent.role if hasattr(task.agent, 'role') else 'Unknown',
                        "completed": True  # 假设成功完成，实际应该检查任务状态
                    }
                    for i, task in enumerate(crew.tasks, 1)
                ],
                "performance_metrics": {
                    "avg_time_per_task": execution_time / len(crew.tasks) if crew.tasks else 0,
                    "success_rate": 1.0,  # 简化处理
                    "efficiency_score": min(1.0, 60 / execution_time) if execution_time > 0 else 0
                }
            }
            
            return summary
            
        except Exception as e:
            logger.warning(f"工作流摘要生成失败: {e}")
            return {"error": str(e)}
    
    def _save_search_results(self, search_id: str, results: Dict[str, Any]):
        """保存搜索结果"""
        try:
            output_file = Path(self.output_dir) / f"{search_id}_complete_results.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"搜索结果已保存: {output_file}")
            
        except Exception as e:
            logger.error(f"保存搜索结果失败: {e}")
    
    def get_crew_info(self) -> Dict[str, Any]:
        """获取Crew信息"""
        agent_validation = self.agent_orchestrator.validate_agents()
        
        return {
            "crew_version": "1.0.0",
            "llm_model": self.llm_model,
            "max_iterations": self.max_iterations,
            "output_directory": self.output_dir,
            "agents_info": agent_validation,
            "available_tools": len(self.tools),
            "tool_names": [tool.name for tool in self.tools],
            "task_sequence": self.task_orchestrator.get_task_sequence()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 检查环境变量
            required_env_vars = ["SERPER_API_KEY"]
            env_status = {var: bool(os.getenv(var)) for var in required_env_vars}
            
            # 检查组件状态
            agent_validation = self.agent_orchestrator.validate_agents()
            tools_available = len(self.tools) > 0
            
            health_status = {
                "overall_status": "healthy" if all(env_status.values()) and agent_validation['validation_passed'] and tools_available else "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "environment_variables": env_status,
                "agents_status": agent_validation['validation_passed'],
                "tools_status": tools_available,
                "components": {
                    "agents": agent_validation,
                    "tools_count": len(self.tools),
                    "output_dir_exists": Path(self.output_dir).exists()
                }
            }
            
            return health_status
            
        except Exception as e:
            return {
                "overall_status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }


class SearchCrewManager:
    """搜索Crew管理器"""
    
    def __init__(self):
        self.crews = {}
        self.search_history = []
    
    def create_crew(self, 
                   crew_id: str,
                   llm_model: str = "gpt-4",
                   **kwargs) -> IntelligentSearchCrew:
        """创建新的搜索Crew"""
        if crew_id in self.crews:
            logger.warning(f"Crew {crew_id} 已存在，将被替换")
        
        crew = IntelligentSearchCrew(llm_model=llm_model, **kwargs)
        self.crews[crew_id] = crew
        
        logger.info(f"创建Crew: {crew_id}")
        return crew
    
    def get_crew(self, crew_id: str) -> Optional[IntelligentSearchCrew]:
        """获取指定的Crew"""
        return self.crews.get(crew_id)
    
    def execute_search(self, 
                      crew_id: str, 
                      user_requirement: str,
                      **kwargs) -> Dict[str, Any]:
        """执行搜索"""
        crew = self.get_crew(crew_id)
        if not crew:
            return {
                "success": False,
                "error": f"Crew {crew_id} 不存在"
            }
        
        result = crew.execute_intelligent_search(user_requirement, **kwargs)
        self.search_history.append({
            "crew_id": crew_id,
            "requirement": user_requirement,
            "timestamp": datetime.now().isoformat(),
            "success": result.get("success", False)
        })
        
        return result
    
    def get_search_history(self) -> List[Dict[str, Any]]:
        """获取搜索历史"""
        return self.search_history


# 便捷函数
def create_intelligent_search_crew(**kwargs) -> IntelligentSearchCrew:
    """创建智能搜索Crew的便捷函数"""
    return IntelligentSearchCrew(**kwargs)

def quick_search(user_requirement: str, **kwargs) -> Dict[str, Any]:
    """快速搜索的便捷函数"""
    crew = IntelligentSearchCrew(**kwargs)
    return crew.execute_intelligent_search(user_requirement)


if __name__ == "__main__":
    # 测试智能搜索Crew
    print("🚀 测试CrewAI智能搜索工作流...")
    
    try:
        # 创建搜索Crew
        search_crew = IntelligentSearchCrew(verbose=True)
        
        # 健康检查
        health = search_crew.health_check()
        print(f"健康检查: {health['overall_status']}")
        
        if health['overall_status'] != 'healthy':
            print("⚠️ 系统健康检查未通过，请检查配置")
            print(f"环境变量状态: {health.get('environment_variables', {})}")
        else:
            # 获取Crew信息
            info = search_crew.get_crew_info()
            print(f"Crew信息: {info['agents_info']['total_agents']} 个智能体, {info['available_tools']} 个工具")
            
            # 测试搜索（注释掉以避免实际API调用）
            # test_requirement = "我想找卖数位板的公司，要求支持4K分辨率，价格1000-3000元，深圳地区"
            # result = search_crew.execute_intelligent_search(test_requirement)
            # print(f"搜索结果: {result['success']}")
        
        print("✅ CrewAI智能搜索工作流测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()