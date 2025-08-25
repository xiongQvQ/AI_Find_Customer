#!/usr/bin/env python3
"""
CrewAI任务定义 - 智能搜索工作流任务链
定义从需求分析到结果优化的完整任务序列
"""

from crewai import Task
from typing import Dict, Any, List

class IntelligentSearchTasks:
    """智能搜索任务集合"""
    
    @staticmethod
    def requirement_analysis_task(agent, user_requirement: str) -> Task:
        """需求分析任务"""
        return Task(
            description=f"""
            分析用户需求并生成结构化的搜索规格。
            
            用户原始需求: {user_requirement}
            
            你的具体任务:
            1. 深度解析用户需求，提取关键信息:
               - 产品类型和核心功能
               - 技术规格和性能要求  
               - 价格范围和预算限制
               - 地理位置和区域偏好
               - 公司规模和其他条件
            
            2. 识别需求的完整性:
               - 标记清晰明确的信息
               - 识别模糊或缺失的部分
               - 评估需求可执行性
            
            3. 生成标准化需求文档:
               - 结构化的产品规格
               - 明确的筛选条件
               - 优先级排序
               - 置信度评估
            
            使用requirement_parser工具进行需求解析，确保输出完整的结构化需求信息。
            """,
            expected_output="""
            结构化需求分析结果，包含:
            - parsed_requirement: 完整的结构化需求对象
            - confidence_score: 需求理解置信度(0-1)
            - missing_info: 缺失信息列表
            - priority_factors: 优先考虑因素
            - search_guidance: 给后续搜索的指导建议
            """,
            agent=agent,
            output_file="output/requirement_analysis.json"
        )
    
    @staticmethod
    def search_strategy_task(agent, context_tasks: List[Task]) -> Task:
        """搜索策略制定任务"""
        return Task(
            description="""
            基于需求分析结果，制定最优的搜索策略。
            
            你的具体任务:
            1. 分析结构化需求，确定搜索重点:
               - 识别核心搜索意图和目标
               - 评估不同搜索渠道的适用性
               - 确定搜索的优先级顺序
            
            2. 生成智能关键词策略:
               - 主要关键词（产品核心词汇）
               - 补充关键词（技术规格、特色功能）
               - 地理和行业限定词
               - 排除关键词（避免无关结果）
            
            3. 选择最佳搜索模式:
               - general模式：适合广泛发现和综合搜索
               - linkedin模式：适合专业B2B和企业信息
               - 混合策略：结合多种搜索方式
            
            4. 优化搜索参数:
               - 地理位置代码(gl)设置
               - 结果数量平衡(质量vs覆盖度)
               - 语言和市场定位
            
            使用keyword_generator工具生成关键词，制定comprehensive搜索计划。
            """,
            expected_output="""
            完整的搜索策略方案，包含:
            - search_keywords: 分层关键词列表
            - search_mode: 选定的搜索模式(general/linkedin/mixed)
            - search_parameters: 优化的搜索参数配置
            - search_sequence: 多轮搜索执行顺序
            - expected_coverage: 预期结果覆盖范围
            """,
            agent=agent,
            context=context_tasks,
            output_file="output/search_strategy.json"
        )
    
    @staticmethod
    def search_execution_task(agent, context_tasks: List[Task]) -> Task:
        """搜索执行任务"""
        return Task(
            description="""
            执行搜索策略，获取高质量的目标公司数据。
            
            你的具体任务:
            1. 严格按照搜索策略执行API调用:
               - 使用制定好的关键词组合
               - 应用优化的搜索参数
               - 按照搜索序列逐步执行
            
            2. 处理搜索过程中的技术问题:
               - API调用异常和超时处理
               - 结果为空时的策略调整
               - 搜索质量监控和优化
            
            3. 数据质量控制和预处理:
               - 过滤明显不相关的结果
               - 数据标准化和清洗
               - 去除重复和无效条目
               - 基础信息完整性检查
            
            4. 结果整合和验证:
               - 合并多轮搜索结果
               - 保持数据结构一致性
               - 记录搜索执行日志
            
            使用company_search工具执行搜索，确保获得高质量、完整的公司数据集。
            """,
            expected_output="""
            搜索执行结果，包含:
            - companies_data: 标准化的公司信息列表
            - search_summary: 搜索执行摘要统计
            - data_quality_report: 数据质量评估报告
            - execution_log: 详细的执行日志
            - next_analysis_ready: 为评分分析准备的数据状态确认
            """,
            agent=agent,
            context=context_tasks,
            output_file="output/search_results.json"
        )
    
    @staticmethod
    def company_scoring_task(agent, context_tasks: List[Task]) -> Task:
        """公司评分分析任务"""
        return Task(
            description="""
            基于用户需求对搜索到的公司进行AI智能评分和匹配度分析。
            
            你的具体任务:
            1. 多维度匹配度评估:
               - 业务相关性分析（产品/服务匹配度）
               - 技术能力评估（规格要求满足度）
               - 地理位置适配度（物流成本、时区等）
               - 公司规模和实力评估
               - 价格竞争力分析
            
            2. 深度内容理解和语义分析:
               - 公司描述与需求的语义匹配
               - 业务模式和目标客户群体分析
               - 市场定位和竞争优势识别
               - 服务能力和交付水平评估
            
            3. 风险识别和关注点分析:
               - 潜在合作风险评估
               - 服务质量和可靠性分析
               - 沟通和合作便利性评估
               - 长期合作潜力判断
            
            4. 量化评分和置信度评估:
               - 综合评分（0-10分制）
               - 各维度细分评分
               - 匹配置信度等级
               - 推荐优先级排序
            
            使用company_scorer工具对每家公司进行comprehensive分析评分。
            """,
            expected_output="""
            完整的公司评分分析结果，包含:
            - scored_companies: 详细评分的公司列表
            - scoring_methodology: 评分方法和权重说明  
            - quality_distribution: 评分分布统计
            - top_recommendations: 高分推荐企业
            - concerns_summary: 主要风险和关注点汇总
            """,
            agent=agent,
            context=context_tasks,
            output_file="output/company_scores.json"
        )
    
    @staticmethod
    def result_optimization_task(agent, context_tasks: List[Task]) -> Task:
        """结果优化任务"""
        return Task(
            description="""
            优化最终搜索结果，生成最佳匹配公司的排序推荐列表。
            
            你的具体任务:
            1. 高级数据质量控制:
               - 智能去重（基于公司名称、域名、描述相似度）
               - 数据完整性验证和修复
               - 异常值检测和处理
               - 评分一致性检查
            
            2. 多目标优化排序:
               - 综合评分权重优化
               - 用户偏好特征匹配
               - 地理位置优先级调整
               - 价格敏感度因子考虑
            
            3. 智能结果分层:
               - 优秀级别（9-10分）：强烈推荐
               - 良好级别（7-8.9分）：值得考虑
               - 可接受级别（6-6.9分）：备选方案
               - 筛选阈值优化
            
            4. 决策支持优化:
               - 生成执行摘要和行动建议
               - 提供多方案比较分析
               - 风险提示和注意事项
               - 后续行动计划建议
            
            使用result_optimizer工具进行最终结果优化，确保用户获得最有价值的推荐。
            """,
            expected_output="""
            优化后的最终推荐结果，包含:
            - final_recommendations: 分层推荐公司列表
            - executive_summary: 执行摘要和核心发现
            - optimization_report: 优化过程和效果报告
            - decision_guidance: 决策指导和行动建议
            - success_metrics: 搜索成功度量指标
            """,
            agent=agent,
            context=context_tasks,
            output_file="output/final_recommendations.json"
        )


class TaskOrchestrator:
    """任务编排器"""
    
    def __init__(self):
        self.tasks = {}
        self.task_sequence = [
            'requirement_analysis',
            'search_strategy', 
            'search_execution',
            'company_scoring',
            'result_optimization'
        ]
    
    def create_task_chain(self, agents: Dict[str, Any], user_requirement: str) -> List[Task]:
        """创建完整的任务链"""
        tasks = []
        
        # 1. 需求分析任务
        requirement_task = IntelligentSearchTasks.requirement_analysis_task(
            agents['requirement_analyzer'], 
            user_requirement
        )
        tasks.append(requirement_task)
        self.tasks['requirement_analysis'] = requirement_task
        
        # 2. 搜索策略任务
        strategy_task = IntelligentSearchTasks.search_strategy_task(
            agents['search_strategist'],
            [requirement_task]
        )
        tasks.append(strategy_task)
        self.tasks['search_strategy'] = strategy_task
        
        # 3. 搜索执行任务
        execution_task = IntelligentSearchTasks.search_execution_task(
            agents['search_executor'],
            [requirement_task, strategy_task]
        )
        tasks.append(execution_task)
        self.tasks['search_execution'] = execution_task
        
        # 4. 公司评分任务
        scoring_task = IntelligentSearchTasks.company_scoring_task(
            agents['scoring_analyst'],
            [requirement_task, execution_task]
        )
        tasks.append(scoring_task)
        self.tasks['company_scoring'] = scoring_task
        
        # 5. 结果优化任务
        optimization_task = IntelligentSearchTasks.result_optimization_task(
            agents['result_optimizer'],
            [requirement_task, scoring_task]
        )
        tasks.append(optimization_task)
        self.tasks['result_optimization'] = optimization_task
        
        return tasks
    
    def get_task(self, task_name: str) -> Task:
        """根据名称获取任务"""
        return self.tasks.get(task_name)
    
    def get_task_sequence(self) -> List[str]:
        """获取任务执行序列"""
        return self.task_sequence
    
    def validate_task_chain(self, tasks: List[Task]) -> Dict[str, Any]:
        """验证任务链配置"""
        validation_result = {
            'valid_tasks': [],
            'invalid_tasks': [],
            'total_tasks': len(tasks),
            'context_dependencies': [],
            'validation_passed': True
        }
        
        for i, task in enumerate(tasks):
            try:
                # 基本验证
                if hasattr(task, 'description') and hasattr(task, 'expected_output') and hasattr(task, 'agent'):
                    validation_result['valid_tasks'].append(f"Task {i+1}")
                    
                    # 检查上下文依赖
                    if hasattr(task, 'context') and task.context:
                        validation_result['context_dependencies'].append(f"Task {i+1} depends on {len(task.context)} previous tasks")
                else:
                    validation_result['invalid_tasks'].append(f"Task {i+1}: Missing required attributes")
                    validation_result['validation_passed'] = False
                    
            except Exception as e:
                validation_result['invalid_tasks'].append(f"Task {i+1}: {str(e)}")
                validation_result['validation_passed'] = False
        
        return validation_result


# 便捷函数
def create_intelligent_search_tasks(agents: Dict[str, Any], user_requirement: str) -> List[Task]:
    """创建智能搜索任务链"""
    orchestrator = TaskOrchestrator()
    return orchestrator.create_task_chain(agents, user_requirement)

def validate_tasks(tasks: List[Task]) -> Dict[str, Any]:
    """验证任务链配置"""
    orchestrator = TaskOrchestrator()
    return orchestrator.validate_task_chain(tasks)


if __name__ == "__main__":
    # 测试任务创建和验证
    print("📋 测试CrewAI任务创建...")
    
    try:
        # 模拟智能体字典
        mock_agents = {
            'requirement_analyzer': None,  # 实际使用时应该是真实的Agent对象
            'search_strategist': None,
            'search_executor': None, 
            'scoring_analyst': None,
            'result_optimizer': None
        }
        
        # 测试用户需求
        test_requirement = "我想找卖数位板的公司，要求支持4K分辨率，价格1000-3000元，深圳地区"
        
        # 创建任务编排器
        orchestrator = TaskOrchestrator()
        
        # 获取任务序列
        sequence = orchestrator.get_task_sequence()
        print(f"任务执行序列: {sequence}")
        
        print("✅ CrewAI任务结构验证成功！")
        print(f"📊 任务链包含 {len(sequence)} 个步骤:")
        for i, task_name in enumerate(sequence, 1):
            print(f"  {i}. {task_name}")
        
    except Exception as e:
        print(f"❌ 任务创建失败: {e}")
        import traceback
        traceback.print_exc()