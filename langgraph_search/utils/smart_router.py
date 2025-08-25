"""
智能路由器
根据意图识别结果和当前状态，智能决定下一步执行路径
"""

from typing import List, Dict, Any, Optional
from ..state import SearchState, SearchIntent

class SmartRouter:
    """
    智能路由器
    
    根据以下因素决定工作流路径：
    1. 用户意图 (company/employee/composite/unknown)
    2. 当前执行状态 (哪些步骤已完成)
    3. 搜索结果质量 (是否需要重试或调整)
    4. 错误处理 (遇到错误时的路由策略)
    """
    
    def __init__(self):
        """初始化路由器，设置路由规则"""
        self.setup_routing_rules()
    
    def setup_routing_rules(self):
        """设置路由决策规则"""
        
        # 基于意图的基础路由表
        self.intent_routes = {
            "company": {
                "primary_path": ["company_search", "ai_evaluation", "output"],
                "description": "纯公司搜索流程"
            },
            "employee": {
                "primary_path": ["company_search", "ai_evaluation", "employee_search", "output"],
                "description": "员工搜索流程(需要先找到相关公司)"
            },
            "composite": {
                "primary_path": ["company_search", "ai_evaluation", "employee_search", "output"],
                "description": "复合搜索流程(公司+员工)"
            },
            "unknown": {
                "primary_path": ["clarification"],
                "description": "意图不明确，需要用户澄清"
            }
        }
        
        # 节点执行条件检查
        self.node_conditions = {
            "company_search": {
                "required": [],
                "blocked_by": ["company_search_completed"],
                "triggers": ["company", "employee", "composite"]
            },
            "ai_evaluation": {
                "required": ["company_search_completed"],
                "blocked_by": ["ai_evaluation_completed"],
                "triggers": ["company", "employee", "composite"]
            },
            "employee_search": {
                "required": ["ai_evaluation_completed"],
                "blocked_by": ["employee_search_completed"],
                "triggers": ["employee", "composite"],
                "conditions": ["has_qualified_companies"]
            },
            "output": {
                "required": [],
                "blocked_by": [],
                "triggers": ["company", "employee", "composite"]
            },
            "clarification": {
                "required": [],
                "blocked_by": [],
                "triggers": ["unknown"]
            }
        }
        
        # 错误恢复路由
        self.error_recovery_routes = {
            "company_search_failed": {
                "retry_conditions": ["retry_count < 3"],
                "alternative_routes": ["manual_input", "clarification"],
                "escalation": "human_intervention"
            },
            "ai_evaluation_failed": {
                "retry_conditions": ["retry_count < 2"],
                "alternative_routes": ["simple_filtering", "all_companies"],
                "escalation": "skip_evaluation"
            },
            "employee_search_failed": {
                "retry_conditions": ["retry_count < 3"],
                "alternative_routes": ["manual_employee_input"],
                "escalation": "company_only_output"
            }
        }
        
        # 结果质量评估阈值
        self.quality_thresholds = {
            "min_company_results": 5,      # 最少公司结果数
            "min_qualified_companies": 2,  # 最少符合条件的公司数
            "min_employee_results": 10,    # 最少员工结果数
            "min_confidence_score": 0.3,   # 最低置信度阈值
            "max_error_rate": 0.2          # 最大错误率
        }
    
    def route_next_nodes(self, state: SearchState) -> List[str]:
        """
        确定下一步应该执行的节点
        
        Args:
            state: 当前搜索状态
            
        Returns:
            下一步节点列表 (按优先级排序)
        """
        try:
            # 1. 获取当前状态信息
            current_intent = state["detected_intent"]
            current_node = state.get("current_node", "")
            workflow_path = state.get("workflow_path", [])
            
            # 2. 检查是否有严重错误需要处理
            if self._has_critical_errors(state):
                return self._handle_critical_errors(state)
            
            # 3. 基于意图获取基础路径
            if current_intent not in self.intent_routes:
                return ["clarification"]
            
            base_path = self.intent_routes[current_intent]["primary_path"]
            
            # 4. 过滤可执行的节点
            executable_nodes = []
            for node in base_path:
                if self._can_execute_node(node, state):
                    executable_nodes.append(node)
            
            # 5. 如果没有可执行节点，检查是否需要特殊处理
            if not executable_nodes:
                executable_nodes = self._handle_no_executable_nodes(state)
            
            # 6. 应用优先级排序
            executable_nodes = self._prioritize_nodes(executable_nodes, state)
            
            return executable_nodes[:3]  # 返回最多3个优先节点
            
        except Exception as e:
            # 路由器出错，返回安全的默认路径
            return self._get_safe_default_route(state)
    
    def _has_critical_errors(self, state: SearchState) -> bool:
        """检查是否存在需要立即处理的严重错误"""
        errors = state.get("errors", [])
        
        # 检查严重错误类型
        critical_error_types = [
            "api_key_invalid",
            "quota_exceeded", 
            "network_failure",
            "authentication_failed"
        ]
        
        for error in errors:
            if error.get("type") in critical_error_types:
                return True
        
        # 检查错误率
        total_errors = len(errors)
        total_operations = len(state.get("workflow_path", []))
        if total_operations > 0 and total_errors / total_operations > self.quality_thresholds["max_error_rate"]:
            return True
        
        return False
    
    def _handle_critical_errors(self, state: SearchState) -> List[str]:
        """处理严重错误的路由策略"""
        errors = state.get("errors", [])
        latest_error = errors[-1] if errors else {}
        error_type = latest_error.get("type", "unknown")
        
        if error_type in self.error_recovery_routes:
            recovery_route = self.error_recovery_routes[error_type]
            return recovery_route.get("alternative_routes", ["error_handler"])
        
        return ["error_handler"]
    
    def _can_execute_node(self, node_name: str, state: SearchState) -> bool:
        """
        检查节点是否可以执行
        
        Args:
            node_name: 节点名称
            state: 当前状态
            
        Returns:
            是否可以执行
        """
        if node_name not in self.node_conditions:
            return True  # 未定义条件的节点默认可执行
        
        conditions = self.node_conditions[node_name]
        
        # 1. 检查必需条件
        for required in conditions.get("required", []):
            if not state.get(required, False):
                return False
        
        # 2. 检查阻塞条件
        for blocked in conditions.get("blocked_by", []):
            if state.get(blocked, False):
                return False
        
        # 3. 检查意图触发条件
        triggers = conditions.get("triggers", [])
        if triggers and state["detected_intent"] not in triggers:
            return False
        
        # 4. 检查特殊条件
        special_conditions = conditions.get("conditions", [])
        for condition in special_conditions:
            if not self._check_special_condition(condition, state):
                return False
        
        return True
    
    def _check_special_condition(self, condition: str, state: SearchState) -> bool:
        """检查特殊执行条件"""
        if condition == "has_qualified_companies":
            qualified_count = state["search_results"]["qualified_companies_count"]
            return qualified_count >= self.quality_thresholds["min_qualified_companies"]
        
        # 可以添加更多特殊条件
        return True
    
    def _handle_no_executable_nodes(self, state: SearchState) -> List[str]:
        """处理没有可执行节点的情况"""
        current_intent = state["detected_intent"]
        
        # 检查是否所有步骤都已完成
        if self._is_workflow_complete(state):
            return ["output"]
        
        # 检查是否需要重试失败的步骤
        retry_nodes = self._get_retry_candidates(state)
        if retry_nodes:
            return retry_nodes
        
        # 根据意图提供备选方案
        if current_intent == "unknown":
            return ["clarification"]
        elif current_intent in ["employee", "composite"]:
            # 如果没有合格的公司，尝试调整搜索策略
            return ["adjust_search_strategy", "manual_input"]
        else:
            return ["output"]  # 默认输出当前结果
    
    def _is_workflow_complete(self, state: SearchState) -> bool:
        """检查工作流是否完成"""
        intent = state["detected_intent"]
        
        if intent == "company":
            return state.get("company_search_completed", False)
        elif intent in ["employee", "composite"]:
            return (state.get("company_search_completed", False) and 
                   state.get("employee_search_completed", False))
        else:
            return False
    
    def _get_retry_candidates(self, state: SearchState) -> List[str]:
        """获取可重试的节点"""
        retry_candidates = []
        errors = state.get("errors", [])
        
        for error in errors:
            error_type = error.get("type", "")
            if error_type in self.error_recovery_routes:
                recovery_info = self.error_recovery_routes[error_type]
                retry_conditions = recovery_info.get("retry_conditions", [])
                
                # 简单的重试次数检查 (这里需要更完善的实现)
                current_retries = len([e for e in errors if e.get("type") == error_type])
                if current_retries < 3:  # 最多重试3次
                    # 从错误类型推断需要重试的节点
                    if "company_search" in error_type:
                        retry_candidates.append("company_search")
                    elif "employee_search" in error_type:
                        retry_candidates.append("employee_search")
                    elif "ai_evaluation" in error_type:
                        retry_candidates.append("ai_evaluation")
        
        return retry_candidates
    
    def _prioritize_nodes(self, nodes: List[str], state: SearchState) -> List[str]:
        """对可执行节点进行优先级排序"""
        # 定义节点优先级 (数字越小优先级越高)
        priority_map = {
            "company_search": 1,
            "ai_evaluation": 2,
            "employee_search": 3,
            "output": 4,
            "clarification": 5,
            "error_handler": 6
        }
        
        # 根据优先级排序
        sorted_nodes = sorted(nodes, key=lambda x: priority_map.get(x, 999))
        
        return sorted_nodes
    
    def _get_safe_default_route(self, state: SearchState) -> List[str]:
        """获取安全的默认路由 (路由器出错时使用)"""
        intent = state.get("detected_intent", "unknown")
        
        if intent == "unknown":
            return ["clarification"]
        elif not state.get("company_search_completed", False):
            return ["company_search"]
        elif intent in ["employee", "composite"] and not state.get("employee_search_completed", False):
            return ["employee_search"]
        else:
            return ["output"]
    
    def get_routing_explanation(self, state: SearchState, next_nodes: List[str]) -> str:
        """
        生成路由决策的解释说明
        
        Args:
            state: 当前状态
            next_nodes: 下一步节点
            
        Returns:
            路由决策解释
        """
        intent = state["detected_intent"]
        confidence = state.get("intent_confidence", 0)
        
        explanation = f"路由决策基于以下因素:\n"
        explanation += f"- 检测意图: {intent} (置信度: {confidence:.2f})\n"
        explanation += f"- 当前节点: {state.get('current_node', 'unknown')}\n"
        explanation += f"- 已完成步骤: {', '.join(state.get('workflow_path', []))}\n"
        
        if next_nodes:
            explanation += f"- 下一步节点: {', '.join(next_nodes)}\n"
            explanation += f"- 选择原因: 根据{intent}意图的标准流程路径"
        else:
            explanation += f"- 无可执行节点，可能需要用户干预"
        
        return explanation
    
    def should_continue_workflow(self, state: SearchState) -> bool:
        """
        判断工作流是否应该继续执行
        
        Args:
            state: 当前状态
            
        Returns:
            是否继续执行
        """
        # 检查是否有严重错误阻止继续执行
        if self._has_critical_errors(state):
            return False
        
        # 检查是否达到预设的终止条件
        intent = state["detected_intent"]
        
        if intent == "company" and state.get("company_search_completed", False):
            return False
        elif intent in ["employee", "composite"]:
            if (state.get("company_search_completed", False) and 
                state.get("employee_search_completed", False)):
                return False
        
        # 检查是否超过最大步骤数 (防止无限循环)
        max_steps = 20
        current_steps = len(state.get("workflow_path", []))
        if current_steps > max_steps:
            return False
        
        return True

# 创建路由器实例
smart_router = SmartRouter()