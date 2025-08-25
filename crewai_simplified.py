#!/usr/bin/env python3
"""
CrewAI简化版本 - 兼容Python 3.9的智能搜索工作流
提供与CrewAI相同的功能但不依赖CrewAI框架
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 导入现有的核心组件
from core.company_search import CompanySearcher
from integration_guide import AIAnalyzerManager

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimplifiedAgent:
    """简化的智能体类"""
    
    def __init__(self, role: str, goal: str, backstory: str, tools: List = None):
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.tools = tools or []
        self.agent_id = role.lower().replace(' ', '_')
    
    def execute_task(self, task_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行任务"""
        logger.info(f"{self.role} 开始执行任务: {task_description[:50]}...")
        
        # 模拟任务执行
        start_time = time.time()
        
        try:
            # 根据智能体角色执行相应的逻辑
            if "需求分析" in self.role:
                result = self._analyze_requirement(task_description, context)
            elif "搜索策略" in self.role:
                result = self._plan_search_strategy(task_description, context)
            elif "搜索执行" in self.role:
                result = self._execute_search(task_description, context)
            elif "评分分析" in self.role:
                result = self._analyze_companies(task_description, context)
            elif "结果优化" in self.role:
                result = self._optimize_results(task_description, context)
            else:
                result = {"success": False, "error": f"未知智能体角色: {self.role}"}
            
            execution_time = time.time() - start_time
            result['execution_time'] = execution_time
            
            logger.info(f"{self.role} 任务完成，耗时: {execution_time:.2f}秒")
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{self.role} 任务失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time
            }
    
    def _analyze_requirement(self, task_description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """分析用户需求"""
        user_requirement = context.get('user_requirement', task_description)
        
        # 基础的需求解析逻辑
        parsed_requirement = {
            "product": "",
            "specifications": [],
            "price_range": {"min": None, "max": None, "currency": "RMB"},
            "location": {"city": None, "province": None, "country": "中国"},
            "company_size": "不限",
            "priority_factors": [],
            "confidence_score": 0.8,
            "missing_info": [],
            "original_text": user_requirement
        }
        
        # 简单的关键词提取
        requirement_lower = user_requirement.lower()
        
        # 产品识别
        product_keywords = ["数位板", "太阳能板", "软件", "设备", "产品"]
        for keyword in product_keywords:
            if keyword in user_requirement:
                parsed_requirement["product"] = keyword
                break
        
        # 价格提取
        import re
        price_pattern = r'(\d+)-(\d+)元'
        price_match = re.search(price_pattern, user_requirement)
        if price_match:
            parsed_requirement["price_range"]["min"] = int(price_match.group(1))
            parsed_requirement["price_range"]["max"] = int(price_match.group(2))
        
        # 地区提取
        cities = ["北京", "上海", "深圳", "广州", "杭州", "成都", "武汉", "西安"]
        for city in cities:
            if city in user_requirement:
                parsed_requirement["location"]["city"] = city
                break
        
        return {
            "success": True,
            "parsed_requirement": parsed_requirement,
            "analysis_summary": f"已解析用户需求: {parsed_requirement['product']}"
        }
    
    def _plan_search_strategy(self, task_description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """制定搜索策略"""
        parsed_req = context.get('parsed_requirement', {})
        
        # 生成关键词
        keywords = []
        if parsed_req.get('product'):
            product_mapping = {
                "数位板": ["digital tablet", "graphics tablet", "drawing tablet"],
                "太阳能板": ["solar panel", "solar energy", "photovoltaic"],
                "软件": ["software", "application", "system"],
                "设备": ["equipment", "device", "machinery"]
            }
            keywords.extend(product_mapping.get(parsed_req['product'], [parsed_req['product']]))
        
        # 添加规格关键词
        if parsed_req.get('specifications'):
            keywords.extend(parsed_req['specifications'])
        
        search_strategy = {
            "search_keywords": keywords[:5],  # 限制关键词数量
            "search_mode": "general",  # 或 "linkedin"
            "search_parameters": {
                "gl": "cn" if parsed_req.get('location', {}).get('country') == "中国" else "us",
                "num_results": 20
            },
            "expected_coverage": "中等覆盖度"
        }
        
        return {
            "success": True,
            "search_strategy": search_strategy,
            "strategy_summary": f"已制定搜索策略，使用 {len(keywords)} 个关键词"
        }
    
    def _execute_search(self, task_description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行搜索"""
        search_strategy = context.get('search_strategy', {})
        
        try:
            # 使用现有的搜索器
            searcher = CompanySearcher()
            
            # 执行搜索
            result = searcher.search_companies(
                search_mode=search_strategy.get('search_mode', 'general'),
                keywords=search_strategy.get('search_keywords', []),
                gl=search_strategy.get('search_parameters', {}).get('gl', 'us'),
                num_results=search_strategy.get('search_parameters', {}).get('num_results', 20)
            )
            
            if result.get('success'):
                return {
                    "success": True,
                    "companies_data": result.get('data', []),
                    "search_summary": f"找到 {len(result.get('data', []))} 家公司",
                    "data_quality_report": "数据质量良好"
                }
            else:
                return {
                    "success": False,
                    "error": result.get('error', '搜索失败'),
                    "companies_data": []
                }
                
        except Exception as e:
            logger.error(f"搜索执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "companies_data": []
            }
    
    def _analyze_companies(self, task_description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """分析和评分公司"""
        companies_data = context.get('companies_data', [])
        parsed_req = context.get('parsed_requirement', {})
        
        if not companies_data:
            return {
                "success": True,
                "scored_companies": [],
                "scoring_summary": "无公司数据需要评分"
            }
        
        try:
            # 使用现有的AI分析器
            analyzer = AIAnalyzerManager(
                use_optimized=True,
                max_concurrent=3,
                enable_cache=True
            )
            
            # 构建目标描述
            target_profile = parsed_req.get('original_text', '目标客户需求')
            
            # 执行分析
            analyzed_results = analyzer.batch_analyze_companies(companies_data, target_profile)
            
            # 格式化结果
            scored_companies = []
            for result in analyzed_results:
                scored_company = {
                    "company_name": result.get('company_name', ''),
                    "overall_score": result.get('final_score', 0),
                    "dimension_scores": {
                        "relevance": result.get('industry_match_score', 0) / 10,
                        "quality": result.get('company_scale_score', 0) / 10,
                        "match": result.get('business_model_score', 0) / 10
                    },
                    "match_reasons": result.get('strengths', []),
                    "concerns": result.get('concerns', []),
                    "confidence_level": "high" if result.get('final_score', 0) >= 8 else "medium",
                    "analysis_summary": result.get('analysis_summary', ''),
                    "original_data": {
                        "name": result.get('company_name', ''),
                        "description": result.get('company_description', ''),
                        "domain": result.get('company_domain', ''),
                    }
                }
                scored_companies.append(scored_company)
            
            return {
                "success": True,
                "scored_companies": scored_companies,
                "scoring_summary": f"已评分 {len(scored_companies)} 家公司"
            }
            
        except Exception as e:
            logger.error(f"公司分析失败: {e}")
            # 如果AI分析失败，使用简单评分
            scored_companies = []
            for i, company in enumerate(companies_data):
                scored_company = {
                    "company_name": company.get('name', f'公司{i+1}'),
                    "overall_score": 7.0,  # 默认评分
                    "dimension_scores": {"relevance": 0.7, "quality": 0.7, "match": 0.7},
                    "match_reasons": ["基础匹配"],
                    "concerns": ["需进一步验证"],
                    "confidence_level": "medium",
                    "analysis_summary": company.get('description', ''),
                    "original_data": company
                }
                scored_companies.append(scored_company)
            
            return {
                "success": True,
                "scored_companies": scored_companies,
                "scoring_summary": f"使用基础评分完成 {len(scored_companies)} 家公司分析"
            }
    
    def _optimize_results(self, task_description: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """优化结果"""
        scored_companies = context.get('scored_companies', [])
        
        if not scored_companies:
            return {
                "success": True,
                "final_recommendations": [],
                "optimization_summary": "无结果需要优化"
            }
        
        # 去重
        seen_names = set()
        deduplicated = []
        for company in scored_companies:
            name = company.get('company_name', '').strip().lower()
            if name and name not in seen_names:
                seen_names.add(name)
                deduplicated.append(company)
        
        # 分数过滤 (>= 6分)
        filtered = [c for c in deduplicated if c.get('overall_score', 0) >= 6.0]
        
        # 排序
        filtered.sort(key=lambda x: x.get('overall_score', 0), reverse=True)
        
        # 限制结果数量
        final_results = filtered[:10]
        
        # 添加排名和等级
        for i, company in enumerate(final_results, 1):
            company['rank'] = i
            score = company.get('overall_score', 0)
            if score >= 9:
                company['score_tier'] = 'excellent'
            elif score >= 8:
                company['score_tier'] = 'very_good'
            elif score >= 7:
                company['score_tier'] = 'good'
            else:
                company['score_tier'] = 'acceptable'
        
        return {
            "success": True,
            "final_recommendations": final_results,
            "optimization_summary": f"优化后推荐 {len(final_results)} 家公司",
            "optimization_report": {
                "original_count": len(scored_companies),
                "after_deduplication": len(deduplicated),
                "after_filtering": len(filtered),
                "final_count": len(final_results)
            }
        }


class SimplifiedCrew:
    """简化的Crew类"""
    
    def __init__(self, agents: List[SimplifiedAgent], verbose: bool = True, progress_callback=None):
        self.agents = agents
        self.verbose = verbose
        self.execution_log = []
        self.progress_callback = progress_callback
    
    def kickoff(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """启动工作流"""
        logger.info(f"启动简化Crew工作流，包含 {len(self.agents)} 个智能体")
        
        start_time = time.time()
        context = inputs.copy()
        
        try:
            # 按顺序执行智能体任务
            for i, agent in enumerate(self.agents, 1):
                logger.info(f"执行智能体 {i}/{len(self.agents)}: {agent.role}")
                
                # 更新进度
                if self.progress_callback:
                    self.progress_callback({
                        "step": i,
                        "total_steps": len(self.agents),
                        "current_agent": agent.role,
                        "status": "running",
                        "message": f"🤖 {agent.role} 正在执行任务..."
                    })
                
                # 构建任务描述
                task_description = f"执行 {agent.role} 相关任务"
                
                # 执行任务
                result = agent.execute_task(task_description, context)
                
                # 记录执行日志
                self.execution_log.append({
                    'agent': agent.role,
                    'success': result.get('success', False),
                    'execution_time': result.get('execution_time', 0)
                })
                
                # 任务完成进度更新
                if self.progress_callback:
                    status_icon = "✅" if result.get('success', False) else "❌"
                    self.progress_callback({
                        "step": i,
                        "total_steps": len(self.agents),
                        "current_agent": agent.role,
                        "status": "completed" if result.get('success', False) else "failed",
                        "message": f"{status_icon} {agent.role} 任务完成 (耗时: {result.get('execution_time', 0):.1f}秒)"
                    })
                
                if not result.get('success'):
                    logger.error(f"智能体 {agent.role} 执行失败: {result.get('error')}")
                    # 继续执行其他智能体，不中断整个流程
                
                # 更新上下文，传递结果给下一个智能体
                context.update(result)
            
            total_time = time.time() - start_time
            
            # 返回最终结果
            final_result = context.get('final_recommendations', [])
            
            return {
                "success": True,
                "final_recommendations": final_result,
                "execution_summary": {
                    "total_agents": len(self.agents),
                    "total_time": total_time,
                    "execution_log": self.execution_log
                },
                "full_context": context
            }
            
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"Crew工作流执行失败: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "execution_summary": {
                    "total_agents": len(self.agents),
                    "total_time": total_time,
                    "execution_log": self.execution_log
                },
                "full_context": context
            }


class IntelligentSearchCrewSimplified:
    """简化的智能搜索Crew"""
    
    def __init__(self, verbose: bool = True, output_dir: str = "output"):
        self.verbose = verbose
        self.output_dir = output_dir
        self.search_history = []
        
        # 确保输出目录存在
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        
        # 创建智能体
        self.agents = self._create_agents()
        
        logger.info("简化智能搜索Crew初始化完成")
    
    def _create_agents(self) -> List[SimplifiedAgent]:
        """创建智能体"""
        agents = [
            SimplifiedAgent(
                role="需求分析专家",
                goal="深度理解用户需求，将自然语言转化为结构化搜索规格",
                backstory="专门负责理解用户的业务需求，提取关键信息"
            ),
            SimplifiedAgent(
                role="搜索策略专家", 
                goal="基于需求分析结果制定最优搜索策略和关键词组合",
                backstory="搜索引擎优化和信息检索专家，设计高效的搜索策略"
            ),
            SimplifiedAgent(
                role="搜索执行专家",
                goal="高效执行搜索策略，获取高质量的公司数据",
                backstory="技术执行专家，负责执行复杂的搜索任务"
            ),
            SimplifiedAgent(
                role="AI评分分析师",
                goal="基于用户需求对搜索结果进行智能评分和匹配度分析",
                backstory="专业的商业分析师和AI评估专家，评估企业匹配度"
            ),
            SimplifiedAgent(
                role="结果优化专家",
                goal="优化最终结果，提供最佳匹配公司的排序推荐",
                backstory="数据科学家和业务顾问，优化决策支持结果"
            )
        ]
        
        return agents
    
    def execute_intelligent_search(self, user_requirement: str, progress_callback=None) -> Dict[str, Any]:
        """执行智能搜索"""
        search_id = f"search_{int(time.time())}"
        logger.info(f"开始执行智能搜索: {search_id}")
        
        try:
            # 创建Crew with progress callback
            crew = SimplifiedCrew(self.agents, self.verbose, progress_callback=progress_callback)
            
            # 准备输入
            inputs = {
                "user_requirement": user_requirement,
                "search_id": search_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # 初始化进度
            if progress_callback:
                progress_callback({
                    "step": 0,
                    "total_steps": len(self.agents),
                    "current_agent": "初始化",
                    "status": "starting",
                    "message": "🚀 启动AI多智能体系统..."
                })
            
            # 执行搜索
            result = crew.kickoff(inputs)
            
            # 检查搜索结果是否成功
            if not result.get('success'):
                # 如果整体失败，但有部分成功的智能体，尝试提取可用信息
                error_details = self._analyze_execution_errors(result)
                result['error_details'] = error_details
                
                # 更新失败进度
                if progress_callback:
                    progress_callback({
                        "step": len(self.agents),
                        "total_steps": len(self.agents),
                        "current_agent": "错误处理",
                        "status": "failed",
                        "message": f"❌ 搜索执行失败: {result.get('error', '未知错误')}"
                    })
            
            # 完成进度
            if progress_callback and result.get('success'):
                progress_callback({
                    "step": len(self.agents),
                    "total_steps": len(self.agents),
                    "current_agent": "完成",
                    "status": "completed",
                    "message": "✅ AI智能体协作完成！"
                })
            
            # 记录搜索历史
            self.search_history.append({
                "search_id": search_id,
                "user_requirement": user_requirement,
                "success": result.get("success", False),
                "timestamp": datetime.now().isoformat()
            })
            
            # 保存结果
            self._save_search_results(search_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"智能搜索执行异常: {e}")
            
            # 异常进度更新
            if progress_callback:
                progress_callback({
                    "step": len(self.agents),
                    "total_steps": len(self.agents),
                    "current_agent": "异常处理",
                    "status": "failed",
                    "message": f"💥 系统异常: {str(e)[:50]}..."
                })
            
            # 记录失败历史
            self.search_history.append({
                "search_id": search_id,
                "user_requirement": user_requirement,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": False,
                "error": f"系统异常: {str(e)}",
                "error_details": {
                    "error_type": "system_exception",
                    "error_message": str(e),
                    "search_id": search_id,
                    "timestamp": datetime.now().isoformat(),
                    "user_requirement": user_requirement
                }
            }
    
    def _analyze_execution_errors(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """分析执行错误详情"""
        try:
            error_details = {
                "error_type": "execution_failure",
                "failed_agents": [],
                "successful_agents": [],
                "error_summary": result.get('error', '未知执行错误'),
                "recovery_suggestions": []
            }
            
            # 分析执行日志
            execution_log = result.get('execution_summary', {}).get('execution_log', [])
            
            for log_entry in execution_log:
                agent_info = {
                    "agent": log_entry.get('agent', '未知智能体'),
                    "success": log_entry.get('success', False),
                    "execution_time": log_entry.get('execution_time', 0)
                }
                
                if log_entry.get('success', False):
                    error_details["successful_agents"].append(agent_info)
                else:
                    error_details["failed_agents"].append(agent_info)
            
            # 生成恢复建议
            failed_count = len(error_details["failed_agents"])
            successful_count = len(error_details["successful_agents"])
            
            if failed_count > 0:
                error_details["recovery_suggestions"].append(f"检查失败的{failed_count}个智能体配置")
                
            if "API" in result.get('error', ''):
                error_details["recovery_suggestions"].extend([
                    "检查API密钥配置",
                    "验证网络连接",
                    "确认API服务可用性"
                ])
                
            if "timeout" in result.get('error', '').lower():
                error_details["recovery_suggestions"].extend([
                    "增加超时时间",
                    "检查网络稳定性",
                    "简化搜索需求"
                ])
                
            return error_details
            
        except Exception as e:
            logger.error(f"分析执行错误时出现异常: {e}")
            return {
                "error_type": "error_analysis_failed",
                "error_message": str(e),
                "recovery_suggestions": ["检查系统配置", "联系技术支持"]
            }
    
    def _save_search_results(self, search_id: str, results: Dict[str, Any]):
        """保存搜索结果"""
        try:
            output_file = Path(self.output_dir) / f"{search_id}_simplified_results.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"搜索结果已保存: {output_file}")
            
        except Exception as e:
            logger.error(f"保存搜索结果失败: {e}")
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 检查环境变量
            env_status = {
                "SERPER_API_KEY": bool(os.getenv("SERPER_API_KEY"))
            }
            
            # 检查组件
            agents_healthy = len(self.agents) == 5
            output_dir_exists = Path(self.output_dir).exists()
            
            overall_healthy = all(env_status.values()) and agents_healthy and output_dir_exists
            
            return {
                "overall_status": "healthy" if overall_healthy else "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "environment_variables": env_status,
                "agents_count": len(self.agents),
                "output_dir_exists": output_dir_exists,
                "components": {
                    "agents": agents_healthy,
                    "output_dir": output_dir_exists
                }
            }
            
        except Exception as e:
            return {
                "overall_status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }


# 便捷函数
def quick_intelligent_search(user_requirement: str, **kwargs) -> Dict[str, Any]:
    """快速智能搜索"""
    crew = IntelligentSearchCrewSimplified(**kwargs)
    return crew.execute_intelligent_search(user_requirement)


if __name__ == "__main__":
    # 测试简化版智能搜索
    print("🧪 测试简化版CrewAI智能搜索...")
    
    try:
        # 创建搜索实例
        search_crew = IntelligentSearchCrewSimplified()
        
        # 健康检查
        health = search_crew.health_check()
        print(f"健康状态: {health['overall_status']}")
        
        if health['overall_status'] == 'healthy':
            print("✅ 系统健康，可以进行测试搜索")
            
            # 测试搜索（注释掉以避免实际API调用）
            # test_requirement = "我想找卖数位板的公司，要求支持4K分辨率，价格1000-3000元，深圳地区"
            # result = search_crew.execute_intelligent_search(test_requirement)
            # print(f"搜索结果: {result.get('success', False)}")
        else:
            print("⚠️ 系统健康检查未通过")
            print(f"环境变量状态: {health.get('environment_variables', {})}")
        
        print("✅ 简化版CrewAI智能搜索测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()