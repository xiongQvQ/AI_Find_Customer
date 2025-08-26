"""
增强版工作流管理器
集成灵活的复合搜索策略，支持动态策略调整和优化
"""

from typing import Dict, Any, Optional
import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ..state import SearchState, create_initial_state
from ..nodes.enhanced_intent_recognition import enhanced_intent_recognition_node
from ..nodes.company_search import company_search_node
from ..nodes.robust_ai_evaluation import robust_ai_evaluation_node
from ..nodes.employee_search import employee_search_node
from ..nodes.output_integration import output_integration_node
from ..nodes.clarification import clarification_node
from ..nodes.error_handler import error_handler_node
from ..strategies import strategy_manager, SearchCriteria, SearchResult


class EnhancedSearchWorkflowGraph:
    """
    增强版搜索工作流图
    
    支持功能：
    - 智能策略选择和动态调整
    - 多轮搜索优化
    - 实时策略评估和建议
    - 灵活的复合搜索模式
    """
    
    def __init__(self, enable_checkpoints: bool = True):
        """初始化增强版工作流图"""
        self.enable_checkpoints = enable_checkpoints
        self.graph = None
        self.compiled_graph = None
        self.checkpointer = MemorySaver() if enable_checkpoints else None
        self.logger = logging.getLogger(__name__)
        
        # 创建状态图
        self.build_graph()
    
    def build_graph(self):
        """构建增强版LangGraph状态图"""
        self.graph = StateGraph(SearchState)
        
        # 添加节点
        self.add_nodes()
        
        # 添加边连接
        self.add_edges()
        
        # 设置入口节点
        self.graph.set_entry_point("enhanced_intent_recognition")
        
        # 编译图
        self.compile_graph()
    
    def add_nodes(self):
        """添加所有节点到图中"""
        
        # 1. 增强版意图识别节点
        self.graph.add_node("enhanced_intent_recognition", self._enhanced_intent_recognition_wrapper)
        
        # 2. 策略选择节点
        self.graph.add_node("strategy_selection", self._strategy_selection_wrapper)
        
        # 3. 公司搜索节点
        self.graph.add_node("company_search", self._company_search_wrapper)
        
        # 4. AI评估节点
        self.graph.add_node("ai_evaluation", self._ai_evaluation_wrapper)
        
        # 5. 策略评估和调整节点
        self.graph.add_node("strategy_evaluation", self._strategy_evaluation_wrapper)
        
        # 6. 员工搜索节点
        self.graph.add_node("employee_search", self._employee_search_wrapper)
        
        # 7. 搜索优化节点（可选的第二轮搜索）
        self.graph.add_node("search_optimization", self._search_optimization_wrapper)
        
        # 8. 输出集成节点
        self.graph.add_node("output", self._output_integration_wrapper)
        
        # 9. 澄清节点
        self.graph.add_node("clarification", self._clarification_wrapper)
        
        # 10. 错误处理节点
        self.graph.add_node("error_handler", self._error_handler_wrapper)
    
    def add_edges(self):
        """添加节点间的边连接"""
        
        # 从增强意图识别到策略选择
        self.graph.add_conditional_edges(
            "enhanced_intent_recognition",
            self._route_after_intent_recognition,
            {
                "strategy_selection": "strategy_selection",
                "clarification": "clarification",
                "error_handler": "error_handler"
            }
        )
        
        # 从策略选择到公司搜索
        self.graph.add_conditional_edges(
            "strategy_selection", 
            self._route_after_strategy_selection,
            {
                "company_search": "company_search",
                "employee_search": "employee_search",  # 员工优先策略
                "error_handler": "error_handler"
            }
        )
        
        # 从公司搜索到AI评估
        self.graph.add_conditional_edges(
            "company_search",
            self._route_after_company_search,
            {
                "ai_evaluation": "ai_evaluation",
                "output": "output",
                "error_handler": "error_handler"
            }
        )
        
        # 从AI评估到策略评估
        self.graph.add_conditional_edges(
            "ai_evaluation",
            self._route_after_ai_evaluation,
            {
                "strategy_evaluation": "strategy_evaluation",
                "output": "output",
                "error_handler": "error_handler"
            }
        )
        
        # 从策略评估到下一步
        self.graph.add_conditional_edges(
            "strategy_evaluation",
            self._route_after_strategy_evaluation,
            {
                "employee_search": "employee_search",
                "search_optimization": "search_optimization",
                "output": "output",
                "error_handler": "error_handler"
            }
        )
        
        # 从员工搜索到搜索优化或输出
        self.graph.add_conditional_edges(
            "employee_search",
            self._route_after_employee_search,
            {
                "search_optimization": "search_optimization",
                "output": "output",
                "error_handler": "error_handler"
            }
        )
        
        # 从搜索优化到输出
        self.graph.add_conditional_edges(
            "search_optimization",
            self._route_after_optimization,
            {
                "output": "output",
                "company_search": "company_search",  # 可能需要重新搜索
                "employee_search": "employee_search",
                "error_handler": "error_handler"
            }
        )
        
        # 终端节点到END
        self.graph.add_edge("output", END)
        self.graph.add_edge("clarification", END)
        self.graph.add_edge("error_handler", END)
    
    def compile_graph(self):
        """编译图以供执行"""
        try:
            self.compiled_graph = self.graph.compile(
                checkpointer=self.checkpointer,
                debug=True
            )
        except Exception as e:
            self.logger.error(f"图编译失败: {e}")
            raise
    
    # ============ 节点包装函数 ============
    
    def _enhanced_intent_recognition_wrapper(self, state: SearchState) -> SearchState:
        """增强版意图识别节点包装器"""
        try:
            result_state = enhanced_intent_recognition_node.execute(state)
            result_state["current_node"] = "enhanced_intent_recognition"
            return result_state
        except Exception as e:
            from ..state import add_error_to_state
            return add_error_to_state(
                state, "intent_recognition_error", str(e), "enhanced_intent_recognition"
            )
    
    def _strategy_selection_wrapper(self, state: SearchState) -> SearchState:
        """策略选择包装器"""
        try:
            # 构建搜索条件
            parsed_query = state.get("parsed_query", {})
            criteria = SearchCriteria(
                user_query=state["user_query"],
                detected_intent=state["detected_intent"],
                target_position=parsed_query.get("target_position"),
                department=parsed_query.get("department"),
                location=parsed_query.get("location"),
                industry=parsed_query.get("industry"),
                company_size=parsed_query.get("company_size"),
                specific_company=parsed_query.get("specific_company"),
                keywords=parsed_query.get("keywords", [])
            )
            
            # 选择最佳策略
            selected_strategy = strategy_manager.select_strategy(criteria)
            strategy_params = selected_strategy.get_search_parameters(criteria)
            
            # 更新状态
            state["selected_strategy"] = selected_strategy.name
            state["strategy_params"] = strategy_params
            state["search_criteria"] = criteria.__dict__
            state["current_node"] = "strategy_selection"
            state["workflow_path"].append("strategy_selected")
            
            self.logger.info(f"选择搜索策略: {selected_strategy.name}")
            return state
            
        except Exception as e:
            from ..state import add_error_to_state
            return add_error_to_state(
                state, "strategy_selection_error", str(e), "strategy_selection"
            )
    
    def _company_search_wrapper(self, state: SearchState) -> SearchState:
        """公司搜索节点包装器"""
        try:
            # 应用策略参数
            strategy_params = state.get("strategy_params", {})
            company_params = strategy_params.get("company_search", {})
            
            # 更新搜索参数
            if company_params:
                search_params = state["search_params"]
                search_params.max_results = company_params.get("max_results", 20)
                # 可以添加更多策略参数的应用
            
            result_state = company_search_node.execute(state)
            return result_state
        except Exception as e:
            from ..state import add_error_to_state
            return add_error_to_state(
                state, "company_search_error", str(e), "company_search"
            )
    
    def _ai_evaluation_wrapper(self, state: SearchState) -> SearchState:
        """AI评估节点包装器"""
        try:
            result_state = robust_ai_evaluation_node.execute(state)
            return result_state
        except Exception as e:
            from ..state import add_error_to_state
            return add_error_to_state(
                state, "ai_evaluation_error", str(e), "ai_evaluation"
            )
    
    def _strategy_evaluation_wrapper(self, state: SearchState) -> SearchState:
        """策略评估包装器"""
        try:
            # 构建当前结果
            search_results = state["search_results"]
            current_results = SearchResult(
                companies=search_results.get("companies", []),
                employees=search_results.get("employees", []),
                qualified_companies=search_results.get("qualified_companies", []),
                qualified_employees=search_results.get("qualified_employees", []),
                total_companies_found=search_results.get("total_companies_found", 0),
                qualified_companies_count=search_results.get("qualified_companies_count", 0)
            )
            
            # 获取搜索条件
            criteria_dict = state.get("search_criteria", {})
            criteria = SearchCriteria(**criteria_dict)
            
            # 获取策略建议
            recommendations = strategy_manager.get_strategy_recommendations(criteria, current_results)
            
            # 更新状态
            state["strategy_evaluation"] = recommendations
            state["next_action"] = recommendations["next_action"]
            state["current_node"] = "strategy_evaluation"
            state["workflow_path"].append("strategy_evaluated")
            
            self.logger.info(f"策略评估完成，下一步: {recommendations['next_action']}")
            return state
            
        except Exception as e:
            from ..state import add_error_to_state
            return add_error_to_state(
                state, "strategy_evaluation_error", str(e), "strategy_evaluation"
            )
    
    def _employee_search_wrapper(self, state: SearchState) -> SearchState:
        """员工搜索节点包装器"""
        try:
            # 应用策略参数
            strategy_params = state.get("strategy_params", {})
            employee_params = strategy_params.get("employee_search", {})
            
            # 可以根据策略参数调整员工搜索配置
            result_state = employee_search_node.execute(state)
            return result_state
        except Exception as e:
            from ..state import add_error_to_state
            return add_error_to_state(
                state, "employee_search_error", str(e), "employee_search"
            )
    
    def _search_optimization_wrapper(self, state: SearchState) -> SearchState:
        """搜索优化包装器"""
        try:
            next_action = state.get("next_action", "complete")
            
            # 根据建议的下一步操作进行优化
            if next_action == "expand_company_search":
                # 扩大公司搜索范围
                state["optimization_action"] = "expand_company_search"
                state["search_params"].max_results = min(state["search_params"].max_results * 1.5, 50)
                
            elif next_action == "expand_employee_search":
                # 扩大员工搜索范围
                state["optimization_action"] = "expand_employee_search"
                # 可以调整员工搜索参数
                
            elif next_action == "try_alternative_strategy":
                # 尝试替代策略
                state["optimization_action"] = "try_alternative_strategy"
                # 选择其他策略并更新参数
                
            state["current_node"] = "search_optimization"
            state["workflow_path"].append("search_optimized")
            
            return state
            
        except Exception as e:
            from ..state import add_error_to_state
            return add_error_to_state(
                state, "search_optimization_error", str(e), "search_optimization"
            )
    
    def _output_integration_wrapper(self, state: SearchState) -> SearchState:
        """输出集成节点包装器"""
        try:
            result_state = output_integration_node.execute(state)
            return result_state
        except Exception as e:
            from ..state import add_error_to_state
            return add_error_to_state(
                state, "output_integration_error", str(e), "output_integration"
            )
    
    def _clarification_wrapper(self, state: SearchState) -> SearchState:
        """澄清节点包装器"""
        try:
            result_state = clarification_node.execute(state)
            return result_state
        except Exception as e:
            from ..state import add_error_to_state
            return add_error_to_state(
                state, "clarification_error", str(e), "clarification"
            )
    
    def _error_handler_wrapper(self, state: SearchState) -> SearchState:
        """错误处理节点包装器"""
        try:
            result_state = error_handler_node.execute(state)
            return result_state
        except Exception as e:
            from ..state import add_error_to_state
            return add_error_to_state(
                state, "error_handler_exception", f"错误处理节点异常: {str(e)}", "error_handler"
            )
    
    # ============ 路由决策函数 ============
    
    def _route_after_intent_recognition(self, state: SearchState) -> str:
        """意图识别后的路由决策"""
        try:
            intent = state["detected_intent"]
            confidence = state.get("intent_confidence", 0)
            errors = state.get("errors", [])
            
            if errors:
                return "error_handler"
            
            if intent == "unknown" or confidence < 0.3:
                return "clarification"
            else:
                return "strategy_selection"
                
        except Exception:
            return "error_handler"
    
    def _route_after_strategy_selection(self, state: SearchState) -> str:
        """策略选择后的路由决策"""
        try:
            selected_strategy = state.get("selected_strategy", "balanced")
            errors = state.get("errors", [])
            
            if errors:
                return "error_handler"
            
            # 员工优先策略直接搜索员工
            if selected_strategy == "employee_first":
                return "employee_search"
            else:
                # 其他策略从公司搜索开始
                return "company_search"
                
        except Exception:
            return "error_handler"
    
    def _route_after_company_search(self, state: SearchState) -> str:
        """公司搜索后的路由决策"""
        try:
            errors = state.get("errors", [])
            company_count = state["search_results"]["total_companies_found"]
            
            if errors:
                return "error_handler"
            
            if company_count == 0:
                return "output"
            else:
                return "ai_evaluation"
                
        except Exception:
            return "error_handler"
    
    def _route_after_ai_evaluation(self, state: SearchState) -> str:
        """AI评估后的路由决策"""
        try:
            errors = state.get("errors", [])
            qualified_count = state["search_results"]["qualified_companies_count"]
            intent = state["detected_intent"]
            
            if errors:
                return "error_handler"
            
            # 复合搜索需要策略评估
            if intent in ["composite", "employee"]:
                return "strategy_evaluation"
            else:
                return "output"
                
        except Exception:
            return "error_handler"
    
    def _route_after_strategy_evaluation(self, state: SearchState) -> str:
        """策略评估后的路由决策"""
        try:
            errors = state.get("errors", [])
            next_action = state.get("next_action", "complete")
            qualified_count = state["search_results"]["qualified_companies_count"]
            
            if errors:
                return "error_handler"
            
            if next_action == "complete":
                return "output"
            elif next_action == "expand_company_search":
                return "search_optimization"
            elif qualified_count > 0:
                return "employee_search"
            else:
                return "output"
                
        except Exception:
            return "error_handler"
    
    def _route_after_employee_search(self, state: SearchState) -> str:
        """员工搜索后的路由决策"""
        try:
            errors = state.get("errors", [])
            next_action = state.get("next_action", "complete")
            
            if errors:
                return "error_handler"
            
            # 根据策略评估的建议决定是否需要优化
            if next_action in ["expand_employee_search", "try_alternative_strategy"]:
                return "search_optimization"
            else:
                return "output"
                
        except Exception:
            return "error_handler"
    
    def _route_after_optimization(self, state: SearchState) -> str:
        """搜索优化后的路由决策"""
        try:
            errors = state.get("errors", [])
            optimization_action = state.get("optimization_action", "complete")
            
            if errors:
                return "error_handler"
            
            if optimization_action == "expand_company_search":
                return "company_search"
            elif optimization_action == "expand_employee_search":
                return "employee_search"
            else:
                return "output"
                
        except Exception:
            return "error_handler"
    
    # ============ 执行接口 ============
    
    def execute_search(self, user_query: str, **kwargs) -> Dict[str, Any]:
        """执行增强版搜索工作流"""
        try:
            # 创建初始状态
            initial_state = create_initial_state(user_query)
            
            # 应用额外参数
            for key, value in kwargs.items():
                if key in initial_state:
                    initial_state[key] = value
            
            # 执行图
            config = {"configurable": {"thread_id": initial_state["session_id"]}}
            result = self.compiled_graph.invoke(initial_state, config=config)
            
            return {
                "success": True,
                "result": result,
                "session_id": initial_state["session_id"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "session_id": None
            }


def create_enhanced_search_graph(enable_checkpoints: bool = True) -> EnhancedSearchWorkflowGraph:
    """创建增强版搜索工作流图实例"""
    return EnhancedSearchWorkflowGraph(enable_checkpoints=enable_checkpoints)