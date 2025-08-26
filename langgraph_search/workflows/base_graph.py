"""
基础工作流图构建
创建LangGraph状态图，定义节点和边的连接关系
"""

from typing import Dict, Any
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
from ..utils.smart_router import smart_router

class SearchWorkflowGraph:
    """
    搜索工作流图管理器
    
    负责构建和管理LangGraph状态图，包括：
    1. 节点定义和注册
    2. 边的连接逻辑
    3. 条件路由规则
    4. 检查点管理
    """
    
    def __init__(self, enable_checkpoints: bool = True):
        """
        初始化工作流图
        
        Args:
            enable_checkpoints: 是否启用检查点功能
        """
        self.enable_checkpoints = enable_checkpoints
        self.graph = None
        self.compiled_graph = None
        self.checkpointer = MemorySaver() if enable_checkpoints else None
        
        # 创建状态图
        self.build_graph()
    
    def build_graph(self):
        """构建LangGraph状态图"""
        # 创建状态图
        self.graph = StateGraph(SearchState)
        
        # 添加节点
        self.add_nodes()
        
        # 添加边连接
        self.add_edges()
        
        # 设置入口节点
        self.graph.set_entry_point("intent_recognition")
        
        # 编译图
        self.compile_graph()
    
    def add_nodes(self):
        """添加所有节点到图中"""
        
        # 1. 意图识别节点
        self.graph.add_node("intent_recognition", self._intent_recognition_wrapper)
        
        # 2. 公司搜索节点 (已实现)
        self.graph.add_node("company_search", self._company_search_wrapper)
        
        # 3. AI评估节点 (已实现)
        self.graph.add_node("ai_evaluation", self._ai_evaluation_wrapper)
        
        # 4. 员工搜索节点 (已实现)
        self.graph.add_node("employee_search", self._employee_search_wrapper)
        
        # 5. 输出集成节点 (已实现)
        self.graph.add_node("output", self._output_integration_wrapper)
        
        # 6. 澄清节点
        self.graph.add_node("clarification", self._clarification_wrapper)
        
        # 7. 错误处理节点
        self.graph.add_node("error_handler", self._error_handler_wrapper)
    
    def add_edges(self):
        """添加节点间的边连接"""
        
        # 从意图识别到路由决策
        self.graph.add_conditional_edges(
            "intent_recognition",
            self._route_after_intent_recognition,
            {
                "company_search": "company_search",
                "clarification": "clarification",
                "error_handler": "error_handler"
            }
        )
        
        # 从公司搜索到下一步 (基于意图和结果)
        self.graph.add_conditional_edges(
            "company_search",
            self._route_after_company_search,
            {
                "ai_evaluation": "ai_evaluation",
                "output": "output",
                "error_handler": "error_handler"
            }
        )
        
        # 从AI评估到下一步
        self.graph.add_conditional_edges(
            "ai_evaluation", 
            self._route_after_ai_evaluation,
            {
                "employee_search": "employee_search",
                "output": "output",
                "error_handler": "error_handler"
            }
        )
        
        # 从员工搜索到结束
        self.graph.add_conditional_edges(
            "employee_search",
            self._route_after_employee_search,
            {
                "output": "output",
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
                debug=True  # 启用调试模式
            )
        except Exception as e:
            print(f"图编译失败: {e}")
            raise
    
    # ============ 节点包装函数 ============
    
    def _intent_recognition_wrapper(self, state: SearchState) -> SearchState:
        """增强版意图识别节点包装器"""
        try:
            result_state = enhanced_intent_recognition_node.execute(state)
            result_state["current_node"] = "intent_recognition"
            return result_state
        except Exception as e:
            from ..state import add_error_to_state
            return add_error_to_state(
                state,
                "intent_recognition_error", 
                str(e),
                "intent_recognition"
            )
    
    def _company_search_wrapper(self, state: SearchState) -> SearchState:
        """公司搜索节点包装器"""
        try:
            result_state = company_search_node.execute(state)
            return result_state
        except Exception as e:
            from ..state import add_error_to_state
            return add_error_to_state(
                state,
                "company_search_error",
                str(e),
                "company_search"
            )
    
    def _ai_evaluation_wrapper(self, state: SearchState) -> SearchState:
        """AI评估节点包装器"""
        try:
            result_state = robust_ai_evaluation_node.execute(state)
            return result_state
        except Exception as e:
            from ..state import add_error_to_state
            return add_error_to_state(
                state,
                "ai_evaluation_error",
                str(e),
                "ai_evaluation"
            )
    
    def _employee_search_wrapper(self, state: SearchState) -> SearchState:
        """员工搜索节点包装器"""
        try:
            result_state = employee_search_node.execute(state)
            return result_state
        except Exception as e:
            from ..state import add_error_to_state
            return add_error_to_state(
                state,
                "employee_search_error",
                str(e),
                "employee_search"
            )
    
    def _output_integration_wrapper(self, state: SearchState) -> SearchState:
        """输出集成节点包装器"""
        try:
            result_state = output_integration_node.execute(state)
            return result_state
        except Exception as e:
            from ..state import add_error_to_state
            return add_error_to_state(
                state,
                "output_integration_error",
                str(e),
                "output_integration"
            )
    
    def _clarification_wrapper(self, state: SearchState) -> SearchState:
        """澄清节点包装器"""
        try:
            result_state = clarification_node.execute(state)
            return result_state
        except Exception as e:
            from ..state import add_error_to_state
            return add_error_to_state(
                state,
                "clarification_error",
                str(e),
                "clarification"
            )
    
    def _error_handler_wrapper(self, state: SearchState) -> SearchState:
        """错误处理节点包装器"""
        try:
            result_state = error_handler_node.execute(state)
            return result_state
        except Exception as e:
            from ..state import add_error_to_state
            # 错误处理节点本身出错时的最后处理
            state["current_node"] = "error_handler"
            state["workflow_path"].append("error_handler_failed")
            return add_error_to_state(
                state,
                "error_handler_exception",
                f"错误处理节点异常: {str(e)}",
                "error_handler"
            )
    
    # ============ 路由决策函数 ============
    
    def _route_after_intent_recognition(self, state: SearchState) -> str:
        """意图识别后的路由决策"""
        try:
            intent = state["detected_intent"]
            confidence = state.get("intent_confidence", 0)
            errors = state.get("errors", [])
            
            # 如果有错误，转到错误处理
            if errors:
                return "error_handler"
            
            # 根据意图和置信度决定路由
            if intent == "unknown" or confidence < 0.3:
                return "clarification"
            else:
                return "company_search"
                
        except Exception as e:
            return "error_handler"
    
    def _route_after_company_search(self, state: SearchState) -> str:
        """公司搜索后的路由决策"""
        try:
            intent = state["detected_intent"]
            errors = state.get("errors", [])
            company_count = state["search_results"]["total_companies_found"]
            ai_evaluation_enabled = state.get("ai_evaluation_enabled", True)
            
            # 如果有错误，转到错误处理
            if errors:
                return "error_handler"
            
            # 如果没有找到公司，直接输出
            if company_count == 0:
                return "output"
            
            # 路由决策逻辑
            if intent == "company":
                # 纯公司搜索：如果启用AI评估则评估，否则直接输出
                if ai_evaluation_enabled:
                    return "ai_evaluation"
                else:
                    return "output"
            elif intent == "employee":
                # 员工搜索：需要AI评估来筛选合格公司
                return "ai_evaluation"
            elif intent == "composite":
                # 复合搜索：必须进行AI评估
                return "ai_evaluation"
            else:
                # 未知意图：直接输出
                return "output"
                
        except Exception as e:
            return "error_handler"
    
    def _route_after_ai_evaluation(self, state: SearchState) -> str:
        """AI评估后的路由决策"""
        try:
            intent = state["detected_intent"]
            errors = state.get("errors", [])
            qualified_count = state["search_results"]["qualified_companies_count"]
            
            # 如果有错误，转到错误处理
            if errors:
                return "error_handler"
            
            # 路由决策逻辑
            if intent == "company":
                # 纯公司搜索：AI评估完成后直接输出
                return "output"
            elif intent == "employee":
                # 员工搜索：如果有合格公司则搜索员工，否则直接输出
                if qualified_count > 0:
                    return "employee_search"
                else:
                    return "output"
            elif intent == "composite":
                # 复合搜索：如果有合格公司则搜索员工，否则输出公司结果
                if qualified_count > 0:
                    return "employee_search"
                else:
                    return "output"
            else:
                # 未知意图：直接输出
                return "output"
                
        except Exception as e:
            return "error_handler"
    
    def _route_after_employee_search(self, state: SearchState) -> str:
        """员工搜索后的路由决策"""
        try:
            errors = state.get("errors", [])
            
            # 如果有错误，转到错误处理
            if errors:
                return "error_handler"
            
            # 员工搜索完成，输出结果
            return "output"
            
        except Exception as e:
            return "error_handler"
    
    # ============ 执行接口 ============
    
    def execute_search(self, user_query: str, **kwargs) -> Dict[str, Any]:
        """
        执行搜索工作流
        
        Args:
            user_query: 用户查询
            **kwargs: 额外参数
            
        Returns:
            执行结果
        """
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
    
    def get_graph_visualization(self) -> str:
        """
        获取图的可视化表示
        
        Returns:
            图的Mermaid语法表示
        """
        mermaid_graph = """
        graph TD
            A[Start] --> B[Intent Recognition]
            B --> C{Intent & Confidence}
            C -->|Company/Employee/Composite & High Confidence| D[Company Search]
            C -->|Unknown/Low Confidence| E[Clarification]
            D --> F{Companies Found}
            F -->|No Companies| I[Output Integration]
            F -->|Has Companies| G{Intent Type}
            G -->|Company + AI Enabled| H[AI Evaluation]
            G -->|Company + AI Disabled| I
            G -->|Employee/Composite| H
            H --> J{Evaluation Results}
            J -->|Company Intent| I
            J -->|Employee/Composite + Qualified Companies| K[Employee Search]
            J -->|Employee/Composite + No Qualified Companies| I
            K --> I[Output Integration]
            I --> L[End]
            E --> L
            
            style A fill:#90EE90
            style L fill:#FFB6C1
            style B fill:#87CEEB
            style D fill:#87CEEB
            style H fill:#87CEEB
            style K fill:#87CEEB
            style I fill:#DDA0DD
            style E fill:#F0E68C
            style F fill:#FFFFE0
            style G fill:#FFFFE0
            style J fill:#FFFFE0
        """
        return mermaid_graph

def create_search_graph(enable_checkpoints: bool = True) -> SearchWorkflowGraph:
    """
    创建搜索工作流图实例
    
    Args:
        enable_checkpoints: 是否启用检查点功能
        
    Returns:
        配置好的SearchWorkflowGraph实例
    """
    return SearchWorkflowGraph(enable_checkpoints=enable_checkpoints)