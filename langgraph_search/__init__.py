"""
LangGraph智能搜索系统
支持意图识别和复合搜索工作流
"""

__version__ = "1.0.0"
__author__ = "AI开发团队"

from .state import SearchState, create_initial_state, SearchIntent
from .workflows.base_graph import SearchWorkflowGraph, create_search_graph
from .nodes.enhanced_intent_recognition import EnhancedIntentRecognitionNode
from .utils.smart_router import SmartRouter

__all__ = [
    "SearchState", 
    "create_initial_state",
    "SearchIntent",
    "SearchWorkflowGraph",
    "create_search_graph",
    "EnhancedIntentRecognitionNode", 
    "SmartRouter"
]