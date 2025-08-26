"""
复合搜索策略系统
支持灵活的复合搜索策略，能够根据用户意图和搜索结果动态调整搜索策略
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import logging


class SearchMode(Enum):
    """搜索模式"""
    COMPANY_FOCUSED = "company_focused"  # 以公司为主
    EMPLOYEE_FOCUSED = "employee_focused"  # 以员工为主
    BALANCED = "balanced"  # 平衡模式
    ADAPTIVE = "adaptive"  # 自适应模式


class FilterStrategy(Enum):
    """过滤策略"""
    STRICT = "strict"  # 严格过滤
    MODERATE = "moderate"  # 适中过滤
    LENIENT = "lenient"  # 宽松过滤


@dataclass
class SearchCriteria:
    """搜索条件"""
    user_query: str
    detected_intent: str
    target_position: Optional[str] = None
    department: Optional[str] = None
    seniority_level: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    specific_company: Optional[str] = None
    keywords: List[str] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []


@dataclass
class SearchResult:
    """搜索结果"""
    companies: List[Dict[str, Any]]
    employees: List[Dict[str, Any]]
    qualified_companies: List[Dict[str, Any]]
    qualified_employees: List[Dict[str, Any]]
    total_companies_found: int = 0
    total_employees_found: int = 0
    qualified_companies_count: int = 0
    qualified_employees_count: int = 0


class CompositeSearchStrategy(ABC):
    """复合搜索策略抽象基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(__name__)
    
    @abstractmethod
    def should_apply(self, criteria: SearchCriteria, current_results: SearchResult) -> bool:
        """判断是否应该应用此策略"""
        pass
    
    @abstractmethod
    def get_search_parameters(self, criteria: SearchCriteria) -> Dict[str, Any]:
        """获取搜索参数"""
        pass
    
    @abstractmethod
    def evaluate_results(self, results: SearchResult, criteria: SearchCriteria) -> Dict[str, Any]:
        """评估搜索结果"""
        pass
    
    @abstractmethod
    def decide_next_action(self, results: SearchResult, criteria: SearchCriteria) -> str:
        """决定下一步操作"""
        pass


class CompanyFirstStrategy(CompositeSearchStrategy):
    """公司优先策略 - 先找到优质公司，再搜索员工"""
    
    def __init__(self):
        super().__init__(
            "company_first",
            "优先寻找符合条件的公司，然后在这些公司中搜索目标员工"
        )
    
    def should_apply(self, criteria: SearchCriteria, current_results: SearchResult) -> bool:
        """适用于行业+职位的复合搜索"""
        return (
            criteria.detected_intent == "composite" and
            criteria.industry and
            criteria.target_position and
            not criteria.specific_company
        )
    
    def get_search_parameters(self, criteria: SearchCriteria) -> Dict[str, Any]:
        """获取公司优先的搜索参数"""
        return {
            "company_search": {
                "industry": criteria.industry,
                "location": criteria.location,
                "company_size": criteria.company_size,
                "max_results": 30,  # 增加公司搜索结果
                "quality_threshold": 60  # 公司质量阈值
            },
            "employee_search": {
                "target_position": criteria.target_position,
                "department": criteria.department,
                "seniority_level": criteria.seniority_level,
                "max_results_per_company": 15,  # 每家公司最多搜索员工数
                "max_companies_to_search": 10,  # 最多搜索公司数
                "quality_threshold": 70  # 员工质量阈值
            }
        }
    
    def evaluate_results(self, results: SearchResult, criteria: SearchCriteria) -> Dict[str, Any]:
        """评估公司优先策略的结果"""
        evaluation = {
            "strategy": self.name,
            "company_coverage": len(results.qualified_companies),
            "employee_coverage": len(results.qualified_employees),
            "success_rate": 0.0,
            "recommendations": []
        }
        
        # 计算成功率
        if results.qualified_companies_count > 0:
            evaluation["success_rate"] = (
                results.qualified_employees_count / 
                (results.qualified_companies_count * 5)  # 假设每家公司期望找到5个员工
            ) * 100
        
        # 生成建议
        if results.qualified_companies_count < 3:
            evaluation["recommendations"].append("建议放宽公司筛选条件")
        if results.qualified_employees_count < 5:
            evaluation["recommendations"].append("建议放宽员工筛选条件或扩大搜索范围")
        
        return evaluation
    
    def decide_next_action(self, results: SearchResult, criteria: SearchCriteria) -> str:
        """决定下一步操作"""
        if results.qualified_companies_count == 0:
            return "expand_company_search"  # 扩大公司搜索
        elif results.qualified_companies_count > 0 and results.qualified_employees_count == 0:
            return "expand_employee_search"  # 扩大员工搜索
        else:
            return "complete"  # 搜索完成


class EmployeeFirstStrategy(CompositeSearchStrategy):
    """员工优先策略 - 先搜索目标职位的员工，再筛选合适的公司"""
    
    def __init__(self):
        super().__init__(
            "employee_first",
            "优先搜索目标职位的员工，然后筛选出符合条件的公司"
        )
    
    def should_apply(self, criteria: SearchCriteria, current_results: SearchResult) -> bool:
        """适用于特定职位的广泛搜索"""
        return (
            criteria.detected_intent == "composite" and
            criteria.target_position and
            not criteria.industry and
            not criteria.specific_company
        )
    
    def get_search_parameters(self, criteria: SearchCriteria) -> Dict[str, Any]:
        return {
            "employee_search": {
                "target_position": criteria.target_position,
                "location": criteria.location,
                "department": criteria.department,
                "seniority_level": criteria.seniority_level,
                "max_results": 50,  # 增加员工搜索结果
                "quality_threshold": 60
            },
            "company_filter": {
                "min_employee_count": 2,  # 最少员工数的公司才保留
                "quality_threshold": 50
            }
        }
    
    def evaluate_results(self, results: SearchResult, criteria: SearchCriteria) -> Dict[str, Any]:
        return {
            "strategy": self.name,
            "unique_companies": len(set(emp.get('company', '') for emp in results.qualified_employees)),
            "total_employees": len(results.qualified_employees),
            "success_rate": (len(results.qualified_employees) / 50) * 100 if results.qualified_employees else 0
        }
    
    def decide_next_action(self, results: SearchResult, criteria: SearchCriteria) -> str:
        if results.qualified_employees_count == 0:
            return "expand_employee_search"
        else:
            return "complete"


class BalancedStrategy(CompositeSearchStrategy):
    """平衡策略 - 公司和员工搜索并重"""
    
    def __init__(self):
        super().__init__(
            "balanced",
            "平衡的公司和员工搜索，适用于大多数复合搜索场景"
        )
    
    def should_apply(self, criteria: SearchCriteria, current_results: SearchResult) -> bool:
        """适用于大多数复合搜索场景"""
        return criteria.detected_intent == "composite"
    
    def get_search_parameters(self, criteria: SearchCriteria) -> Dict[str, Any]:
        return {
            "company_search": {
                "industry": criteria.industry,
                "location": criteria.location,
                "company_size": criteria.company_size,
                "max_results": 20,
                "quality_threshold": 55
            },
            "employee_search": {
                "target_position": criteria.target_position,
                "department": criteria.department,
                "max_results_per_company": 10,
                "max_companies_to_search": 8,
                "quality_threshold": 65
            }
        }
    
    def evaluate_results(self, results: SearchResult, criteria: SearchCriteria) -> Dict[str, Any]:
        return {
            "strategy": self.name,
            "balance_score": (
                (results.qualified_companies_count * 2) + 
                results.qualified_employees_count
            ) / 3,
            "coverage": {
                "companies": results.qualified_companies_count,
                "employees": results.qualified_employees_count
            }
        }
    
    def decide_next_action(self, results: SearchResult, criteria: SearchCriteria) -> str:
        total_qualified = results.qualified_companies_count + results.qualified_employees_count
        if total_qualified < 5:
            return "expand_search"
        else:
            return "complete"


class AdaptiveStrategy(CompositeSearchStrategy):
    """自适应策略 - 根据中间结果动态调整搜索策略"""
    
    def __init__(self):
        super().__init__(
            "adaptive",
            "根据搜索过程中的结果动态调整策略，优化搜索效果"
        )
        self.sub_strategies = [
            CompanyFirstStrategy(),
            EmployeeFirstStrategy(),
            BalancedStrategy()
        ]
    
    def should_apply(self, criteria: SearchCriteria, current_results: SearchResult) -> bool:
        """总是可以应用自适应策略"""
        return True
    
    def get_search_parameters(self, criteria: SearchCriteria) -> Dict[str, Any]:
        """根据条件选择最适合的子策略"""
        best_strategy = self._select_best_strategy(criteria)
        return best_strategy.get_search_parameters(criteria)
    
    def evaluate_results(self, results: SearchResult, criteria: SearchCriteria) -> Dict[str, Any]:
        """综合评估结果"""
        return {
            "strategy": self.name,
            "adaptive_score": self._calculate_adaptive_score(results, criteria),
            "selected_substrategy": self._select_best_strategy(criteria).name,
            "recommendations": self._generate_recommendations(results, criteria)
        }
    
    def decide_next_action(self, results: SearchResult, criteria: SearchCriteria) -> str:
        """自适应决策"""
        # 如果结果太少，尝试其他策略
        if results.qualified_companies_count == 0 and results.qualified_employees_count == 0:
            return "try_alternative_strategy"
        elif results.qualified_companies_count + results.qualified_employees_count < 3:
            return "expand_with_alternative"
        else:
            return "complete"
    
    def _select_best_strategy(self, criteria: SearchCriteria) -> CompositeSearchStrategy:
        """选择最佳子策略"""
        for strategy in self.sub_strategies:
            if strategy.should_apply(criteria, SearchResult([], [], [], [])):
                return strategy
        return BalancedStrategy()  # 默认策略
    
    def _calculate_adaptive_score(self, results: SearchResult, criteria: SearchCriteria) -> float:
        """计算自适应评分"""
        # 基础分数
        base_score = min(results.qualified_companies_count + results.qualified_employees_count, 10) * 10
        
        # 多样性奖励
        if results.qualified_companies_count > 0 and results.qualified_employees_count > 0:
            base_score += 20
        
        # 目标匹配奖励
        if criteria.target_position:
            matching_employees = sum(1 for emp in results.qualified_employees 
                                   if criteria.target_position.lower() in emp.get('position', '').lower())
            base_score += (matching_employees / max(len(results.qualified_employees), 1)) * 30
        
        return min(base_score, 100.0)
    
    def _generate_recommendations(self, results: SearchResult, criteria: SearchCriteria) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        if results.qualified_companies_count == 0:
            recommendations.append("尝试扩大行业搜索范围")
            recommendations.append("降低公司质量筛选标准")
        
        if results.qualified_employees_count == 0:
            recommendations.append("尝试相近职位搜索")
            recommendations.append("扩大地理位置搜索范围")
        
        if len(recommendations) == 0:
            recommendations.append("当前搜索策略效果良好")
        
        return recommendations


class CompositeSearchStrategyManager:
    """复合搜索策略管理器"""
    
    def __init__(self):
        self.strategies = {
            "company_first": CompanyFirstStrategy(),
            "employee_first": EmployeeFirstStrategy(),
            "balanced": BalancedStrategy(),
            "adaptive": AdaptiveStrategy()
        }
        self.logger = logging.getLogger(__name__)
    
    def select_strategy(self, criteria: SearchCriteria, current_results: Optional[SearchResult] = None) -> CompositeSearchStrategy:
        """选择最适合的搜索策略"""
        if current_results is None:
            current_results = SearchResult([], [], [], [])
        
        # 按优先级检查策略
        strategy_priority = ["company_first", "employee_first", "balanced", "adaptive"]
        
        for strategy_name in strategy_priority:
            strategy = self.strategies[strategy_name]
            if strategy.should_apply(criteria, current_results):
                self.logger.info(f"选择搜索策略: {strategy.name}")
                return strategy
        
        # 默认使用自适应策略
        return self.strategies["adaptive"]
    
    def get_strategy_by_name(self, name: str) -> Optional[CompositeSearchStrategy]:
        """根据名称获取策略"""
        return self.strategies.get(name)
    
    def evaluate_all_strategies(self, criteria: SearchCriteria, results: SearchResult) -> Dict[str, Any]:
        """评估所有策略的效果"""
        evaluations = {}
        for name, strategy in self.strategies.items():
            try:
                evaluations[name] = strategy.evaluate_results(results, criteria)
            except Exception as e:
                evaluations[name] = {"error": str(e)}
        
        return evaluations
    
    def get_strategy_recommendations(self, criteria: SearchCriteria, results: SearchResult) -> Dict[str, Any]:
        """获取策略建议"""
        selected_strategy = self.select_strategy(criteria, results)
        next_action = selected_strategy.decide_next_action(results, criteria)
        evaluation = selected_strategy.evaluate_results(results, criteria)
        
        return {
            "selected_strategy": selected_strategy.name,
            "next_action": next_action,
            "evaluation": evaluation,
            "search_parameters": selected_strategy.get_search_parameters(criteria)
        }


# 全局策略管理器实例
strategy_manager = CompositeSearchStrategyManager()