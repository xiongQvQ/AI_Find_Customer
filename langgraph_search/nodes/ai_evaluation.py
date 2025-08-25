"""
AI评估节点
集成StreamlitCompatibleAIAnalyzer，对搜索结果进行智能评估和筛选
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from streamlit_compatible_ai_analyzer import StreamlitCompatibleAIAnalyzer
from ..state import SearchState, CompanyInfo, EmployeeInfo, add_error_to_state, add_warning_to_state

@dataclass
class AIEvaluationConfig:
    """AI评估配置"""
    enable_evaluation: bool = True
    company_score_threshold: float = 60.0  # 公司评分阈值
    employee_score_threshold: float = 70.0  # 员工评分阈值
    max_concurrent: int = 4
    timeout: int = 30
    enable_cache: bool = True
    llm_provider: str = "openai"  # openai, anthropic, google, huoshan

class AIEvaluationNode:
    """
    AI评估节点
    
    负责对搜索到的公司和员工进行AI评估：
    - 集成现有AI分析器进行智能评估
    - 支持并行处理提高效率
    - 根据评分阈值筛选优质目标
    - 提供详细的评估结果和建议
    """
    
    def __init__(self, config: Optional[AIEvaluationConfig] = None):
        """初始化AI评估节点"""
        self.config = config or AIEvaluationConfig()
        self.logger = logging.getLogger(__name__)
        
        # 初始化AI分析器
        try:
            self.company_analyzer = StreamlitCompatibleAIAnalyzer(
                provider=self.config.llm_provider,
                max_concurrent=self.config.max_concurrent,
                enable_cache=self.config.enable_cache
            )
            self.employee_analyzer = StreamlitCompatibleAIAnalyzer(
                provider=self.config.llm_provider,
                max_concurrent=self.config.max_concurrent,
                enable_cache=self.config.enable_cache
            )
        except Exception as e:
            self.logger.error(f"AI分析器初始化失败: {e}")
            self.company_analyzer = None
            self.employee_analyzer = None
    
    def execute(self, state: SearchState) -> SearchState:
        """
        执行AI评估节点
        
        Args:
            state: 当前搜索状态
            
        Returns:
            更新后的状态
        """
        try:
            self.logger.info("开始执行AI评估")
            
            # 更新当前节点
            state["current_node"] = "ai_evaluation"
            state["workflow_path"].append("ai_evaluation_started")
            
            # 检查是否启用AI评估
            if not self.config.enable_evaluation or not state.get("ai_evaluation_enabled", True):
                self.logger.info("AI评估已禁用，跳过评估步骤")
                state["ai_evaluation_completed"] = True
                state["workflow_path"].append("ai_evaluation_skipped")
                return state
            
            # 检查AI分析器是否可用
            if not self.company_analyzer and not self.employee_analyzer:
                return add_error_to_state(
                    state,
                    "ai_analyzer_unavailable",
                    "AI分析器不可用",
                    "ai_evaluation"
                )
            
            # 获取评估条件
            evaluation_criteria = self._build_evaluation_criteria(state)
            
            # 评估公司
            if state["search_results"]["companies"]:
                qualified_companies = self._evaluate_companies(
                    state["search_results"]["companies"],
                    evaluation_criteria
                )
                state["search_results"]["qualified_companies"] = qualified_companies
                state["search_results"]["qualified_companies_count"] = len(qualified_companies)
                
                self.logger.info(f"公司评估完成，{len(qualified_companies)}/{len(state['search_results']['companies'])} 家公司符合条件")
            
            # 评估员工 (如果有)
            if state["search_results"]["employees"]:
                qualified_employees = self._evaluate_employees(
                    state["search_results"]["employees"],
                    evaluation_criteria
                )
                state["search_results"]["qualified_employees"] = qualified_employees
                state["search_results"]["qualified_employees_count"] = len(qualified_employees)
                
                self.logger.info(f"员工评估完成，{len(qualified_employees)}/{len(state['search_results']['employees'])} 名员工符合条件")
            
            # 更新状态
            state["ai_evaluation_completed"] = True
            state["workflow_path"].append("ai_evaluation_completed")
            
            # 记录API调用
            state["api_calls_count"] += len(state["search_results"]["companies"]) + len(state["search_results"]["employees"])
            
            # 检查是否有足够的符合条件结果
            total_qualified = (state["search_results"]["qualified_companies_count"] + 
                             state["search_results"]["qualified_employees_count"])
            
            if total_qualified == 0:
                state = add_warning_to_state(
                    state,
                    "no_qualified_results",
                    "AI评估后没有找到符合条件的目标",
                    "ai_evaluation"
                )
            elif total_qualified < 3:
                state = add_warning_to_state(
                    state,
                    "low_qualified_results",
                    f"符合条件的结果较少: {total_qualified}",
                    "ai_evaluation"
                )
            
            return state
            
        except Exception as e:
            self.logger.error(f"AI评估过程中发生错误: {e}")
            return add_error_to_state(
                state,
                "ai_evaluation_exception",
                f"AI评估执行异常: {str(e)}",
                "ai_evaluation"
            )
    
    def _build_evaluation_criteria(self, state: SearchState) -> Dict[str, Any]:
        """构建评估条件"""
        
        # 从用户查询和意图中提取评估条件
        user_query = state["user_query"]
        detected_intent = state["detected_intent"]
        search_params = state["search_params"]
        
        criteria = {
            "user_query": user_query,
            "intent": detected_intent,
            "industry": search_params.industry,
            "region": search_params.region,
            "company_size": search_params.company_size,
            "position": search_params.position,
            "seniority_level": search_params.seniority_level,
            "department": search_params.department
        }
        
        # 构建目标客户画像
        target_profile = self._build_target_profile(criteria)
        criteria["target_profile"] = target_profile
        
        return criteria
    
    def _build_target_profile(self, criteria: Dict[str, Any]) -> str:
        """构建目标客户画像描述"""
        
        profile_parts = []
        
        # 基本信息
        if criteria.get("industry"):
            profile_parts.append(f"所属行业: {criteria['industry']}")
        
        if criteria.get("region"):
            profile_parts.append(f"地理位置: {criteria['region']}")
        
        if criteria.get("company_size"):
            profile_parts.append(f"公司规模: {criteria['company_size']}")
        
        # 职位信息 (针对员工搜索)
        if criteria.get("position"):
            profile_parts.append(f"目标职位: {criteria['position']}")
        
        if criteria.get("seniority_level"):
            profile_parts.append(f"职级要求: {criteria['seniority_level']}")
        
        if criteria.get("department"):
            profile_parts.append(f"所属部门: {criteria['department']}")
        
        # 如果没有明确条件，从用户查询中提取
        if not profile_parts:
            profile_parts.append(f"用户需求: {criteria['user_query']}")
        
        return "; ".join(profile_parts)
    
    def _evaluate_companies(self, companies: List[CompanyInfo], 
                          criteria: Dict[str, Any]) -> List[CompanyInfo]:
        """评估公司列表"""
        
        if not self.company_analyzer or not companies:
            return companies  # 如果分析器不可用，返回原始列表
        
        qualified_companies = []
        target_profile = criteria["target_profile"]
        
        try:
            # 将CompanyInfo转换为AI分析器所需的格式
            companies_data = []
            for company in companies:
                company_dict = {
                    "name": company.name,
                    "domain": company.domain,
                    "industry": company.industry, 
                    "size": company.size,
                    "location": company.location,
                    "description": company.description,
                    "linkedin_url": company.linkedin_url,
                    "website_url": company.website_url
                }
                companies_data.append(company_dict)
            
            # 批量分析
            analysis_results = self.company_analyzer.batch_analyze_companies(
                companies_data, 
                target_profile
            )
            
            # 处理分析结果
            for i, result in enumerate(analysis_results):
                if i < len(companies):
                    company = companies[i]
                    
                    # 提取评分和评估结果
                    final_score = result.get("final_score", 0)
                    analysis_summary = result.get("analysis_summary", "")
                    
                    # 更新CompanyInfo
                    company.ai_score = final_score
                    company.ai_reason = analysis_summary
                    company.is_qualified = final_score >= self.config.company_score_threshold
                    
                    # 如果符合条件，添加到结果列表
                    if company.is_qualified:
                        qualified_companies.append(company)
            
            # 按评分排序
            qualified_companies.sort(key=lambda x: x.ai_score or 0, reverse=True)
            
        except Exception as e:
            self.logger.error(f"公司评估失败: {e}")
            # 如果评估失败，返回原始列表但标记为未评估
            for company in companies:
                company.ai_score = None
                company.ai_reason = "评估失败"
                company.is_qualified = None
            return companies
        
        return qualified_companies
    
    def _evaluate_employees(self, employees: List[EmployeeInfo], 
                          criteria: Dict[str, Any]) -> List[EmployeeInfo]:
        """评估员工列表"""
        
        if not self.employee_analyzer or not employees:
            return employees  # 如果分析器不可用，返回原始列表
        
        qualified_employees = []
        business_context = f"业务背景: {criteria['target_profile']}"
        
        try:
            # 逐个分析员工 (员工数据通常较少，可以逐个处理)
            for employee in employees:
                employee_dict = {
                    "name": employee.name,
                    "position": employee.position,
                    "company": employee.company,
                    "linkedin_url": employee.linkedin_url,
                    "location": employee.location,
                    "description": employee.description
                }
                
                # 分析单个员工
                result = self.employee_analyzer.analyze_employee_sync(
                    employee_dict,
                    business_context
                )
                
                # 提取评分和评估结果
                final_score = result.get("final_score", 0)
                analysis_summary = result.get("analysis_summary", "")
                
                # 更新EmployeeInfo
                employee.ai_score = final_score
                employee.ai_reason = analysis_summary
                employee.is_qualified = final_score >= self.config.employee_score_threshold
                
                # 如果符合条件，添加到结果列表
                if employee.is_qualified:
                    qualified_employees.append(employee)
            
            # 按评分排序
            qualified_employees.sort(key=lambda x: x.ai_score or 0, reverse=True)
            
        except Exception as e:
            self.logger.error(f"员工评估失败: {e}")
            # 如果评估失败，返回原始列表但标记为未评估
            for employee in employees:
                employee.ai_score = None
                employee.ai_reason = "评估失败"
                employee.is_qualified = None
            return employees
        
        return qualified_employees
    
    def get_evaluation_summary(self, state: SearchState) -> Dict[str, Any]:
        """获取评估摘要"""
        
        companies = state["search_results"]["companies"]
        employees = state["search_results"]["employees"] 
        qualified_companies = state["search_results"]["qualified_companies"]
        qualified_employees = state["search_results"]["qualified_employees"]
        
        # 统计信息
        summary = {
            "total_companies": len(companies),
            "qualified_companies": len(qualified_companies),
            "company_qualification_rate": len(qualified_companies) / len(companies) * 100 if companies else 0,
            
            "total_employees": len(employees),
            "qualified_employees": len(qualified_employees), 
            "employee_qualification_rate": len(qualified_employees) / len(employees) * 100 if employees else 0,
            
            "evaluation_completed": state.get("ai_evaluation_completed", False),
            "config": {
                "company_threshold": self.config.company_score_threshold,
                "employee_threshold": self.config.employee_score_threshold,
                "llm_provider": self.config.llm_provider
            }
        }
        
        # 评分分布统计
        if qualified_companies:
            company_scores = [c.ai_score for c in qualified_companies if c.ai_score]
            summary["company_score_stats"] = {
                "avg": sum(company_scores) / len(company_scores) if company_scores else 0,
                "max": max(company_scores) if company_scores else 0,
                "min": min(company_scores) if company_scores else 0
            }
        
        if qualified_employees:
            employee_scores = [e.ai_score for e in qualified_employees if e.ai_score]
            summary["employee_score_stats"] = {
                "avg": sum(employee_scores) / len(employee_scores) if employee_scores else 0,
                "max": max(employee_scores) if employee_scores else 0,
                "min": min(employee_scores) if employee_scores else 0
            }
        
        return summary
    
    def adjust_thresholds_based_on_results(self, state: SearchState) -> Tuple[float, float]:
        """
        根据结果质量动态调整评分阈值
        
        Returns:
            (建议的公司阈值, 建议的员工阈值)
        """
        
        companies = state["search_results"]["companies"]
        employees = state["search_results"]["employees"]
        
        # 获取所有评分
        company_scores = [c.ai_score for c in companies if c.ai_score is not None]
        employee_scores = [e.ai_score for e in employees if e.ai_score is not None]
        
        # 基于评分分布调整阈值
        suggested_company_threshold = self.config.company_score_threshold
        suggested_employee_threshold = self.config.employee_score_threshold
        
        if company_scores:
            avg_score = sum(company_scores) / len(company_scores)
            # 如果平均分过低，降低阈值
            if avg_score < 50:
                suggested_company_threshold = max(30, avg_score - 10)
            # 如果平均分很高，提高阈值
            elif avg_score > 80:
                suggested_company_threshold = min(80, avg_score - 5)
        
        if employee_scores:
            avg_score = sum(employee_scores) / len(employee_scores)
            if avg_score < 60:
                suggested_employee_threshold = max(40, avg_score - 10)
            elif avg_score > 85:
                suggested_employee_threshold = min(85, avg_score - 5)
        
        return suggested_company_threshold, suggested_employee_threshold

# 创建节点实例
ai_evaluation_node = AIEvaluationNode()