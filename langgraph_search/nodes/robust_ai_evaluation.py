"""
鲁棒性AI评估节点
集成连接重试和故障转移机制的AI评估系统
"""

import os
import sys
import time
import logging
import json
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from ..utils.robust_llm_client import get_robust_llm_client, RobustLLMClient
    ROBUST_CLIENT_AVAILABLE = True
except ImportError:
    ROBUST_CLIENT_AVAILABLE = False

# Simple error diagnosis decorator
def with_error_diagnosis(node_name: str, operation_type: str):
    """简化版错误诊断装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 简单日志记录
                logger = logging.getLogger(__name__)
                logger.error(f"Error in {node_name}.{operation_type}: {e}")
                raise
        return wrapper
    return decorator

from ..state import SearchState, CompanyInfo, EmployeeInfo, add_error_to_state, add_warning_to_state

@dataclass
class RobustAIEvaluationConfig:
    """鲁棒性AI评估配置"""
    enable_evaluation: bool = True
    company_score_threshold: float = 60.0
    employee_score_threshold: float = 70.0
    max_concurrent: int = 2  # 降低并发数减少连接压力
    timeout: int = 60  # 增加超时时间
    max_retries: int = 5  # 最大重试次数
    retry_delay: float = 2.0  # 重试延迟
    enable_fallback: bool = True  # 启用故障转移
    llm_provider: str = "huoshan"  # 默认使用火山引擎

class RobustAIEvaluationNode:
    """
    鲁棒性AI评估节点
    
    具有以下增强功能：
    - 自动重试机制
    - 连接故障诊断  
    - 故障转移支持
    - 性能监控集成
    - 详细错误日志
    """
    
    def __init__(self, config: Optional[RobustAIEvaluationConfig] = None):
        """初始化鲁棒性AI评估节点"""
        self.config = config or RobustAIEvaluationConfig()
        self.logger = logging.getLogger(__name__)
        
        # 初始化鲁棒性LLM客户端
        if ROBUST_CLIENT_AVAILABLE:
            self.llm_client = get_robust_llm_client()
        else:
            self.llm_client = None
            self.logger.warning("鲁棒性LLM客户端不可用，使用降级模式")
        
        # 初始化计数器
        self.evaluation_stats = {
            "companies_evaluated": 0,
            "employees_evaluated": 0,
            "failed_evaluations": 0,
            "retry_count": 0,
            "fallback_count": 0
        }
    
    @with_error_diagnosis("ai_evaluation", "evaluation")
    def execute(self, state: SearchState) -> SearchState:
        """
        执行鲁棒性AI评估
        
        Args:
            state: 当前搜索状态
            
        Returns:
            更新后的状态
        """
        try:
            self.logger.info("开始执行鲁棒性AI评估")
            
            # 更新状态
            state["current_node"] = "ai_evaluation"
            state["workflow_path"].append("robust_ai_evaluation_started")
            
            # 检查是否启用评估
            if not self.config.enable_evaluation or not state.get("ai_evaluation_enabled", True):
                self.logger.info("AI评估已禁用，跳过评估步骤")
                state["ai_evaluation_completed"] = True
                state["workflow_path"].append("ai_evaluation_skipped")
                return state
            
            # 检查LLM客户端可用性
            if not self.llm_client:
                self.logger.warning("LLM客户端不可用，使用基础评估模式")
                return self._basic_evaluation_fallback(state)
            
            # 获取评估数据
            companies = state["search_results"].get("companies", [])
            employees = state["search_results"].get("employees", [])
            
            if not companies and not employees:
                self.logger.info("没有数据需要评估")
                state["ai_evaluation_completed"] = True
                state["workflow_path"].append("no_data_to_evaluate")
                return state
            
            # 构建评估标准
            evaluation_criteria = self._build_evaluation_criteria(state)
            
            # 并行评估
            qualified_companies = []
            qualified_employees = []
            
            if companies:
                self.logger.info(f"开始评估 {len(companies)} 个公司")
                qualified_companies = self._evaluate_companies_robust(companies, evaluation_criteria)
                
            if employees:
                self.logger.info(f"开始评估 {len(employees)} 个员工")
                qualified_employees = self._evaluate_employees_robust(employees, evaluation_criteria)
            
            # 更新搜索结果
            state["search_results"]["qualified_companies"] = qualified_companies
            state["search_results"]["qualified_employees"] = qualified_employees
            state["search_results"]["qualified_companies_count"] = len(qualified_companies)
            state["search_results"]["qualified_employees_count"] = len(qualified_employees)
            
            # 完成状态更新
            state["ai_evaluation_completed"] = True
            state["workflow_path"].append("robust_ai_evaluation_completed")
            
            # 记录统计信息
            self.logger.info(f"AI评估完成 - 公司: {len(qualified_companies)}/{len(companies)}, "
                           f"员工: {len(qualified_employees)}/{len(employees)}")
            
            # 添加性能统计
            state["evaluation_stats"] = self.evaluation_stats.copy()
            
            return state
            
        except Exception as e:
            self.logger.error(f"鲁棒性AI评估失败: {e}")
            return add_error_to_state(state, "robust_ai_evaluation_error", str(e), "ai_evaluation")
    
    def _basic_evaluation_fallback(self, state: SearchState) -> SearchState:
        """基础评估后备方案"""
        self.logger.info("使用基础评估后备方案")
        
        companies = state["search_results"].get("companies", [])
        employees = state["search_results"].get("employees", [])
        
        # 简单的基于关键词的评估
        qualified_companies = []
        for company in companies:
            # 基础评分逻辑
            score = self._calculate_basic_company_score(company)
            if score >= self.config.company_score_threshold:
                company_dict = company.dict() if hasattr(company, 'dict') else company
                company_dict.update({
                    "ai_score": score,
                    "ai_reason": "基础评估（LLM不可用）",
                    "is_qualified": True
                })
                qualified_companies.append(CompanyInfo(**company_dict))
        
        qualified_employees = []
        for employee in employees:
            score = self._calculate_basic_employee_score(employee)
            if score >= self.config.employee_score_threshold:
                employee_dict = employee.dict() if hasattr(employee, 'dict') else employee
                employee_dict.update({
                    "ai_score": score,
                    "ai_reason": "基础评估（LLM不可用）",
                    "is_qualified": True
                })
                qualified_employees.append(EmployeeInfo(**employee_dict))
        
        # 更新状态
        state["search_results"]["qualified_companies"] = qualified_companies
        state["search_results"]["qualified_employees"] = qualified_employees
        state["search_results"]["qualified_companies_count"] = len(qualified_companies)
        state["search_results"]["qualified_employees_count"] = len(qualified_employees)
        state["ai_evaluation_completed"] = True
        state["workflow_path"].append("basic_evaluation_fallback_completed")
        
        return state
    
    def _calculate_basic_company_score(self, company) -> float:
        """计算基础公司评分"""
        score = 50.0  # 基础分
        
        # 检查公司信息完整性
        company_dict = company.dict() if hasattr(company, 'dict') else company
        
        if company_dict.get("industry"):
            score += 10
        if company_dict.get("size"):
            score += 10
        if company_dict.get("location"):
            score += 5
        if company_dict.get("description"):
            score += 15
        if company_dict.get("website_url"):
            score += 10
        
        return min(score, 100.0)
    
    def _calculate_basic_employee_score(self, employee) -> float:
        """计算基础员工评分"""
        score = 60.0  # 基础分
        
        employee_dict = employee.dict() if hasattr(employee, 'dict') else employee
        
        if employee_dict.get("position"):
            score += 15
        if employee_dict.get("company"):
            score += 10
        if employee_dict.get("location"):
            score += 5
        if employee_dict.get("description"):
            score += 10
        
        return min(score, 100.0)
    
    def _evaluate_companies_robust(self, companies: List, evaluation_criteria: Dict) -> List[CompanyInfo]:
        """鲁棒性公司评估"""
        qualified_companies = []
        
        # 使用ThreadPoolExecutor进行并发评估
        with ThreadPoolExecutor(max_workers=self.config.max_concurrent) as executor:
            # 提交评估任务
            future_to_company = {
                executor.submit(self._evaluate_single_company_robust, company, evaluation_criteria): company
                for company in companies[:20]  # 限制数量防止过载
            }
            
            # 收集结果
            for future in as_completed(future_to_company, timeout=self.config.timeout * 2):
                company = future_to_company[future]
                try:
                    result = future.result(timeout=30)
                    if result and result.get("is_qualified", False):
                        qualified_companies.append(CompanyInfo(**result))
                    self.evaluation_stats["companies_evaluated"] += 1
                except Exception as e:
                    company_name = getattr(company, 'name', 'Unknown')
                    self.logger.warning(f"公司评估失败: {company_name}: {e}")
                    self.evaluation_stats["failed_evaluations"] += 1
        
        return qualified_companies
    
    def _evaluate_employees_robust(self, employees: List, evaluation_criteria: Dict) -> List[EmployeeInfo]:
        """鲁棒性员工评估"""
        qualified_employees = []
        
        with ThreadPoolExecutor(max_workers=self.config.max_concurrent) as executor:
            future_to_employee = {
                executor.submit(self._evaluate_single_employee_robust, employee, evaluation_criteria): employee
                for employee in employees[:20]  # 限制数量
            }
            
            for future in as_completed(future_to_employee, timeout=self.config.timeout * 2):
                employee = future_to_employee[future]
                try:
                    result = future.result(timeout=30)
                    if result and result.get("is_qualified", False):
                        qualified_employees.append(EmployeeInfo(**result))
                    self.evaluation_stats["employees_evaluated"] += 1
                except Exception as e:
                    employee_name = getattr(employee, 'name', 'Unknown')
                    self.logger.warning(f"员工评估失败: {employee_name}: {e}")
                    self.evaluation_stats["failed_evaluations"] += 1
        
        return qualified_employees
    
    def _evaluate_single_company_robust(self, company, evaluation_criteria: Dict) -> Optional[Dict]:
        """单个公司的鲁棒性评估"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # 构建评估提示
                company_dict = company.dict() if hasattr(company, 'dict') else company
                
                prompt = self._build_company_evaluation_prompt(company_dict, evaluation_criteria)
                messages = [{"role": "user", "content": prompt}]
                
                # 使用鲁棒性客户端调用LLM
                response = self.llm_client.call_llm_with_retry(messages)
                
                # 解析响应
                evaluation_result = self._parse_evaluation_response(response)
                
                if evaluation_result:
                    # 更新公司信息
                    company_dict.update(evaluation_result)
                    company_dict["is_qualified"] = evaluation_result.get("ai_score", 0) >= self.config.company_score_threshold
                    return company_dict
                
            except Exception as e:
                self.logger.warning(f"公司评估尝试 {attempt + 1} 失败: {e}")
                self.evaluation_stats["retry_count"] += 1
                
                if attempt < max_attempts - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
        
        # 如果所有尝试都失败，使用基础评估
        self.evaluation_stats["fallback_count"] += 1
        score = self._calculate_basic_company_score(company)
        company_dict = company.to_dict() if hasattr(company, 'to_dict') else company
        company_dict.update({
            "ai_score": score,
            "ai_reason": "基础评估（LLM调用失败）",
            "is_qualified": score >= self.config.company_score_threshold
        })
        return company_dict
    
    def _evaluate_single_employee_robust(self, employee, evaluation_criteria: Dict) -> Optional[Dict]:
        """单个员工的鲁棒性评估"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                employee_dict = employee.dict() if hasattr(employee, 'dict') else employee
                
                prompt = self._build_employee_evaluation_prompt(employee_dict, evaluation_criteria)
                messages = [{"role": "user", "content": prompt}]
                
                response = self.llm_client.call_llm_with_retry(messages)
                evaluation_result = self._parse_evaluation_response(response)
                
                if evaluation_result:
                    employee_dict.update(evaluation_result)
                    employee_dict["is_qualified"] = evaluation_result.get("ai_score", 0) >= self.config.employee_score_threshold
                    return employee_dict
                
            except Exception as e:
                self.logger.warning(f"员工评估尝试 {attempt + 1} 失败: {e}")
                self.evaluation_stats["retry_count"] += 1
                
                if attempt < max_attempts - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
        
        # 基础评估后备
        self.evaluation_stats["fallback_count"] += 1
        score = self._calculate_basic_employee_score(employee)
        employee_dict = employee.dict() if hasattr(employee, 'dict') else employee
        employee_dict.update({
            "ai_score": score,
            "ai_reason": "基础评估（LLM调用失败）",
            "is_qualified": score >= self.config.employee_score_threshold
        })
        return employee_dict
    
    def _build_evaluation_criteria(self, state: SearchState) -> Dict[str, Any]:
        """构建评估标准"""
        user_query = state.get("user_query", "")
        search_params = state.get("search_params", {})
        
        criteria = {
            "user_intent": user_query,
            "target_industry": getattr(search_params, "industry", "") if hasattr(search_params, "industry") else "",
            "target_region": getattr(search_params, "region", "") if hasattr(search_params, "region") else "",
            "target_position": getattr(search_params, "position", "") if hasattr(search_params, "position") else "",
            "evaluation_focus": ["relevance", "quality", "completeness"]
        }
        
        return criteria
    
    def _build_company_evaluation_prompt(self, company: Dict, criteria: Dict) -> str:
        """构建公司评估提示"""
        return f"""请评估以下公司是否符合用户需求：

用户查询：{criteria.get('user_intent', '')}
目标行业：{criteria.get('target_industry', '任何')}
目标地区：{criteria.get('target_region', '任何')}

公司信息：
- 公司名称：{getattr(company, 'name', '未知')}
- 行业：{getattr(company, 'industry', '未知')}
- 规模：{getattr(company, 'size', '未知')}
- 地址：{getattr(company, 'location', '未知')}
- 描述：{str(getattr(company, 'description', '无'))[:200]}

请给出0-100分的评分和简短理由，格式为JSON：
{{
    "ai_score": 分数,
    "ai_reason": "评分理由"
}}"""
    
    def _build_employee_evaluation_prompt(self, employee: Dict, criteria: Dict) -> str:
        """构建员工评估提示"""
        return f"""请评估以下员工是否符合用户需求：

用户查询：{criteria.get('user_intent', '')}
目标职位：{criteria.get('target_position', '任何')}
目标地区：{criteria.get('target_region', '任何')}

员工信息：
- 姓名：{getattr(employee, 'name', '未知')}
- 职位：{getattr(employee, 'position', '未知')}
- 公司：{getattr(employee, 'company', '未知')}
- 地址：{getattr(employee, 'location', '未知')}
- 描述：{str(getattr(employee, 'description', '无'))[:200]}

请给出0-100分的评分和简短理由，格式为JSON：
{{
    "ai_score": 分数,
    "ai_reason": "评分理由"
}}"""
    
    def _parse_evaluation_response(self, response: str) -> Optional[Dict]:
        """解析评估响应"""
        try:
            # 尝试直接解析JSON
            return json.loads(response)
        except:
            # 尝试从响应中提取JSON
            import re
            json_pattern = r'\{[^}]*"ai_score"[^}]*\}'
            match = re.search(json_pattern, response)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
            
            # 如果都失败了，返回None
            return None

# 创建节点实例
robust_ai_evaluation_node = RobustAIEvaluationNode()
ai_evaluation_node = robust_ai_evaluation_node  # 向后兼容

def create_robust_ai_evaluation_node(config: Optional[RobustAIEvaluationConfig] = None):
    """创建鲁棒性AI评估节点"""
    return RobustAIEvaluationNode(config)