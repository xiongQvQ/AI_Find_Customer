#!/usr/bin/env python3
"""
CrewAI智能体定义 - 5个专业化智能体角色
实现智能搜索多智能体工作流
"""

from crewai import Agent
from crewai_tools import get_search_tools, get_analysis_tools

class IntelligentSearchAgents:
    """智能搜索智能体集合"""
    
    @staticmethod
    def requirement_analyzer():
        """需求分析智能体"""
        return Agent(
            role='需求分析专家',
            goal='深度理解用户需求，将自然语言转化为结构化搜索规格',
            backstory="""
            你是一位经验丰富的需求分析专家，专门负责理解用户的业务需求。
            你具备以下核心能力：
            - 从模糊的自然语言描述中提取关键信息
            - 识别产品规格、价格范围、地理位置等结构化数据
            - 判断需求的完整性和可执行性
            - 生成后续搜索和分析所需的标准化需求文档
            
            你的工作方式：
            1. 仔细分析用户的原始需求描述
            2. 识别产品类型、技术规格、预算范围、地理限制等关键要素
            3. 标记缺失或不明确的信息
            4. 输出结构化的需求规格，为后续搜索提供清晰指导
            """,
            tools=[
                tool for tool in get_analysis_tools() 
                if tool.name in ['requirement_parser']
            ],
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
    
    @staticmethod 
    def search_strategist():
        """搜索策略智能体"""
        return Agent(
            role='搜索策略专家',
            goal='基于需求分析结果制定最优搜索策略和关键词组合',
            backstory="""
            你是一位搜索引擎优化和信息检索专家，专门设计高效的搜索策略。
            你具备以下核心能力：
            - 深度理解搜索引擎算法和排名机制
            - 精准的关键词选择和组合策略
            - 多渠道搜索规划（Google通用搜索 vs LinkedIn专业搜索）
            - 搜索参数优化（地理位置、结果数量、语言设置）
            
            你的工作方式：
            1. 分析结构化需求，识别核心搜索意图
            2. 生成多层级关键词（主要关键词、补充关键词、排除关键词）
            3. 选择最适合的搜索模式（general vs linkedin）
            4. 制定搜索参数配置策略
            5. 预测搜索效果并规划多轮搜索方案
            """,
            tools=[
                tool for tool in get_search_tools() 
                if tool.name in ['keyword_generator']
            ],
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
    
    @staticmethod
    def search_executor():
        """搜索执行智能体"""
        return Agent(
            role='搜索执行专家', 
            goal='高效执行搜索策略，获取高质量的公司数据',
            backstory="""
            你是一位技术执行专家，专门负责执行复杂的搜索任务。
            你具备以下核心能力：
            - 熟练操作各种搜索API和工具
            - 处理搜索结果异常和API限制
            - 优化搜索性能和成功率
            - 数据清洗和标准化处理
            
            你的工作方式：
            1. 根据搜索策略执行精确的API调用
            2. 处理搜索过程中的技术问题和限制
            3. 确保搜索结果的完整性和准确性
            4. 对原始搜索数据进行初步清洗和验证
            5. 为下一步分析准备标准化的公司数据
            """,
            tools=[
                tool for tool in get_search_tools()
                if tool.name in ['company_search']
            ],
            verbose=True,
            allow_delegation=False,
            max_iter=5
        )
    
    @staticmethod
    def scoring_analyst():
        """评分分析智能体"""
        return Agent(
            role='AI评分分析师',
            goal='基于用户需求对搜索结果进行智能评分和匹配度分析',
            backstory="""
            你是一位专业的商业分析师和AI评估专家，专门评估企业匹配度。
            你具备以下核心能力：
            - 多维度企业评估（业务匹配、规模实力、地理适配、价格合理性）
            - 智能风险识别和关注点分析
            - 基于AI的深度内容理解和语义分析
            - 量化评分和置信度评估
            
            你的工作方式：
            1. 将每家公司与用户需求进行多维度对比分析
            2. 评估业务匹配度、技术能力、市场地位等关键指标
            3. 识别潜在风险和关注点
            4. 生成量化评分（0-10分）和详细分析报告
            5. 提供匹配理由和改进建议
            """,
            tools=[
                tool for tool in get_analysis_tools()
                if tool.name in ['company_scorer']
            ],
            verbose=True,
            allow_delegation=False,
            max_iter=4
        )
    
    @staticmethod
    def result_optimizer():
        """结果优化智能体"""
        return Agent(
            role='结果优化专家',
            goal='优化最终结果，提供最佳匹配公司的排序推荐',
            backstory="""
            你是一位数据科学家和业务顾问，专门优化决策支持结果。
            你具备以下核心能力：
            - 高级数据分析和排序算法设计
            - 去重和数据质量控制
            - 多目标优化和平衡决策
            - 用户体验设计和结果呈现优化
            
            你的工作方式：
            1. 对评分结果进行质量检查和去重处理
            2. 应用智能排序算法，平衡多个评估维度
            3. 过滤低质量结果，保留最有价值的推荐
            4. 生成分层推荐（优秀、良好、可考虑）
            5. 提供决策支持摘要和行动建议
            """,
            tools=[
                tool for tool in get_analysis_tools()
                if tool.name in ['result_optimizer']
            ],
            verbose=True, 
            allow_delegation=False,
            max_iter=3
        )


class AgentOrchestrator:
    """智能体编排器"""
    
    def __init__(self):
        self.agents = {
            'requirement_analyzer': IntelligentSearchAgents.requirement_analyzer(),
            'search_strategist': IntelligentSearchAgents.search_strategist(),
            'search_executor': IntelligentSearchAgents.search_executor(), 
            'scoring_analyst': IntelligentSearchAgents.scoring_analyst(),
            'result_optimizer': IntelligentSearchAgents.result_optimizer()
        }
    
    def get_agent(self, agent_name: str) -> Agent:
        """根据名称获取智能体"""
        return self.agents.get(agent_name)
    
    def get_all_agents(self) -> list:
        """获取所有智能体列表"""
        return [
            self.agents['requirement_analyzer'],
            self.agents['search_strategist'], 
            self.agents['search_executor'],
            self.agents['scoring_analyst'],
            self.agents['result_optimizer']
        ]
    
    def get_agent_names(self) -> list:
        """获取智能体名称列表"""
        return list(self.agents.keys())
    
    def validate_agents(self) -> dict:
        """验证所有智能体配置"""
        validation_result = {
            'valid_agents': [],
            'invalid_agents': [],
            'total_agents': len(self.agents),
            'validation_passed': True
        }
        
        for name, agent in self.agents.items():
            try:
                # 基本验证：检查必要属性
                if hasattr(agent, 'role') and hasattr(agent, 'goal') and hasattr(agent, 'backstory'):
                    validation_result['valid_agents'].append(name)
                else:
                    validation_result['invalid_agents'].append(name)
                    validation_result['validation_passed'] = False
            except Exception as e:
                validation_result['invalid_agents'].append(f"{name}: {str(e)}")
                validation_result['validation_passed'] = False
        
        return validation_result


# 便捷函数
def create_intelligent_search_crew():
    """创建智能搜索crew的所有智能体"""
    orchestrator = AgentOrchestrator()
    return orchestrator.get_all_agents()

def get_agent_by_role(role_name: str):
    """根据角色名称获取智能体"""
    orchestrator = AgentOrchestrator()
    return orchestrator.get_agent(role_name)


if __name__ == "__main__":
    # 测试智能体创建和验证
    print("🤖 测试CrewAI智能体创建...")
    
    try:
        # 创建智能体编排器
        orchestrator = AgentOrchestrator()
        
        # 验证智能体配置
        validation = orchestrator.validate_agents()
        print(f"智能体验证结果: {validation}")
        
        # 测试获取单个智能体
        requirement_agent = orchestrator.get_agent('requirement_analyzer')
        print(f"需求分析智能体: {requirement_agent.role}")
        
        # 获取所有智能体
        all_agents = orchestrator.get_all_agents()
        print(f"创建了 {len(all_agents)} 个智能体")
        
        # 显示智能体角色
        for i, agent in enumerate(all_agents, 1):
            print(f"{i}. {agent.role} - 目标: {agent.goal[:50]}...")
        
        print("✅ CrewAI智能体创建和验证成功！")
        
    except Exception as e:
        print(f"❌ 智能体创建失败: {e}")
        import traceback
        traceback.print_exc()