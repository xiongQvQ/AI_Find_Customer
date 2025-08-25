"""
LangGraph监控集成工具
将性能监控和日志记录集成到LangGraph工作流中
"""

import time
import functools
from typing import Dict, Any, Callable, Optional
from datetime import datetime

from .performance_manager import (
    monitor_node_execution,
    get_performance_status,
    log_workflow_performance,
    log_api_performance,
    get_performance_manager,
    LOGGING_CONFIG_AVAILABLE
)

# 导入日志配置
if LOGGING_CONFIG_AVAILABLE:
    from config.logging_config import (
        get_logger,
        log_user_action,
        log_workflow_step,
        log_api_call,
        workflow_logger,
        api_logger,
        user_logger
    )
    logger = get_logger("langgraph.monitoring")
else:
    import logging
    logger = logging.getLogger(__name__)

class LangGraphMonitor:
    """LangGraph工作流监控器"""
    
    def __init__(self):
        self.session_metrics = {}
        self.active_sessions = {}
        self.performance_manager = get_performance_manager()
        
    def start_session(self, session_id: str, user_query: str) -> Dict[str, Any]:
        """开始监控会话"""
        session_data = {
            "session_id": session_id,
            "user_query": user_query,
            "start_time": datetime.now().isoformat(),
            "nodes_executed": [],
            "total_execution_time": 0.0,
            "total_api_calls": 0,
            "total_tokens": 0,
            "errors": [],
            "status": "running"
        }
        
        self.active_sessions[session_id] = session_data
        
        # 记录用户操作
        if LOGGING_CONFIG_AVAILABLE:
            log_user_action(session_id, "search_started", {
                "query": user_query,
                "timestamp": session_data["start_time"]
            })
        
        logger.info(f"监控会话开始: {session_id}", extra={
            "session_id": session_id,
            "user_query": user_query,
            "action": "session_start"
        })
        
        return session_data
    
    def monitor_node(self, session_id: str, node_name: str, operation_type: str = "execution"):
        """监控节点执行"""
        return monitor_node_execution(f"{session_id}_{node_name}", operation_type)
    
    def record_node_execution(self, session_id: str, node_name: str, 
                            execution_time: float, success: bool = True, 
                            error_message: str = "", details: Dict = None):
        """记录节点执行结果"""
        if session_id not in self.active_sessions:
            logger.warning(f"未找到活跃会话: {session_id}")
            return
        
        session = self.active_sessions[session_id]
        
        node_data = {
            "node_name": node_name,
            "execution_time": execution_time,
            "success": success,
            "error_message": error_message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        
        session["nodes_executed"].append(node_data)
        session["total_execution_time"] += execution_time
        
        if not success:
            session["errors"].append({
                "node_name": node_name,
                "error_message": error_message,
                "timestamp": node_data["timestamp"]
            })
        
        # 记录工作流步骤
        status = "completed" if success else "failed"
        if LOGGING_CONFIG_AVAILABLE:
            log_workflow_step(f"{session_id}_{node_name}", status, execution_time, details)
        
        logger.info(f"节点执行完成: {node_name}", extra={
            "session_id": session_id,
            "node_name": node_name,
            "execution_time": execution_time,
            "success": success,
            "error_message": error_message
        })
    
    def record_api_call(self, session_id: str, api_name: str, 
                       response_time: float, status_code: int = 200,
                       tokens_used: int = 0, details: Dict = None):
        """记录API调用"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["total_api_calls"] += 1
            self.active_sessions[session_id]["total_tokens"] += tokens_used
        
        # 记录API调用
        if LOGGING_CONFIG_AVAILABLE:
            log_api_call(api_name, "POST", status_code, response_time, details)
        
        logger.info(f"API调用完成: {api_name}", extra={
            "session_id": session_id,
            "api_name": api_name,
            "response_time": response_time,
            "status_code": status_code,
            "tokens_used": tokens_used
        })
    
    def end_session(self, session_id: str, final_status: str = "completed") -> Dict[str, Any]:
        """结束监控会话"""
        if session_id not in self.active_sessions:
            logger.warning(f"未找到活跃会话: {session_id}")
            return {}
        
        session = self.active_sessions[session_id]
        session["status"] = final_status
        session["end_time"] = datetime.now().isoformat()
        
        # 计算总体统计
        session["total_nodes"] = len(session["nodes_executed"])
        session["success_rate"] = (
            sum(1 for node in session["nodes_executed"] if node["success"]) /
            len(session["nodes_executed"]) if session["nodes_executed"] else 0
        )
        
        # 移动到历史记录
        self.session_metrics[session_id] = session.copy()
        del self.active_sessions[session_id]
        
        # 记录用户操作
        if LOGGING_CONFIG_AVAILABLE:
            log_user_action(session_id, "search_completed", {
                "final_status": final_status,
                "total_execution_time": session["total_execution_time"],
                "total_nodes": session["total_nodes"],
                "success_rate": session["success_rate"]
            })
        
        logger.info(f"监控会话结束: {session_id}", extra={
            "session_id": session_id,
            "final_status": final_status,
            "total_execution_time": session["total_execution_time"],
            "total_nodes": session["total_nodes"],
            "success_rate": session["success_rate"]
        })
        
        return session
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话状态"""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id].copy()
        elif session_id in self.session_metrics:
            return self.session_metrics[session_id].copy()
        else:
            return None
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """获取监控摘要"""
        active_count = len(self.active_sessions)
        completed_count = len(self.session_metrics)
        
        # 计算平均指标
        if completed_count > 0:
            avg_execution_time = sum(
                session["total_execution_time"] 
                for session in self.session_metrics.values()
            ) / completed_count
            
            avg_success_rate = sum(
                session["success_rate"] 
                for session in self.session_metrics.values()
            ) / completed_count
        else:
            avg_execution_time = 0
            avg_success_rate = 0
        
        # 获取系统性能状态
        performance_status = get_performance_status()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "active_sessions": active_count,
            "completed_sessions": completed_count,
            "average_execution_time": avg_execution_time,
            "average_success_rate": avg_success_rate,
            "system_performance": performance_status,
            "monitoring_enabled": True,
            "logging_integration": LOGGING_CONFIG_AVAILABLE
        }

# 全局监控器实例
_global_monitor: Optional[LangGraphMonitor] = None

def get_langgraph_monitor() -> LangGraphMonitor:
    """获取全局LangGraph监控器"""
    global _global_monitor
    
    if _global_monitor is None:
        _global_monitor = LangGraphMonitor()
    
    return _global_monitor

def monitor_langgraph_node(session_id: str, node_name: str, operation_type: str = "execution"):
    """LangGraph节点监控装饰器"""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            monitor = get_langgraph_monitor()
            
            start_time = time.time()
            try:
                with monitor.monitor_node(session_id, node_name, operation_type) as metrics:
                    result = func(*args, **kwargs)
                    
                    # 更新metrics中的详细信息
                    if hasattr(result, 'get') and 'api_calls_count' in result:
                        metrics.api_calls = result.get('api_calls_count', 0)
                    if hasattr(result, 'get') and 'tokens_used' in result:
                        metrics.tokens_used = result.get('tokens_used', 0)
                
                execution_time = time.time() - start_time
                monitor.record_node_execution(
                    session_id, node_name, execution_time, 
                    success=True, details={"result_type": type(result).__name__}
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                monitor.record_node_execution(
                    session_id, node_name, execution_time,
                    success=False, error_message=str(e)
                )
                raise
        
        return wrapper
    return decorator

def create_monitored_node(node_func: Callable, node_name: str) -> Callable:
    """创建带监控的节点函数"""
    @functools.wraps(node_func)
    def monitored_node(state, config=None):
        # 从状态中获取session_id
        session_id = state.get("session_id", "unknown")
        
        monitor = get_langgraph_monitor()
        start_time = time.time()
        
        try:
            with monitor.monitor_node(session_id, node_name) as metrics:
                result = node_func(state, config)
                
                # 更新性能指标
                if isinstance(result, dict):
                    if 'api_calls_count' in result:
                        metrics.api_calls = result.get('api_calls_count', 0)
                    if 'tokens_used' in result:
                        metrics.tokens_used = result.get('tokens_used', 0)
            
            execution_time = time.time() - start_time
            monitor.record_node_execution(
                session_id, node_name, execution_time,
                success=True, details={"state_keys": list(result.keys()) if isinstance(result, dict) else []}
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            monitor.record_node_execution(
                session_id, node_name, execution_time,
                success=False, error_message=str(e)
            )
            raise
    
    return monitored_node

# 便捷函数
def start_monitoring_session(session_id: str, user_query: str) -> Dict[str, Any]:
    """开始监控会话"""
    monitor = get_langgraph_monitor()
    return monitor.start_session(session_id, user_query)

def end_monitoring_session(session_id: str, final_status: str = "completed") -> Dict[str, Any]:
    """结束监控会话"""
    monitor = get_langgraph_monitor()
    return monitor.end_session(session_id, final_status)

def get_monitoring_summary() -> Dict[str, Any]:
    """获取监控摘要"""
    monitor = get_langgraph_monitor()
    return monitor.get_monitoring_summary()

def record_api_call(session_id: str, api_name: str, response_time: float, 
                   status_code: int = 200, tokens_used: int = 0, details: Dict = None):
    """记录API调用"""
    monitor = get_langgraph_monitor()
    monitor.record_api_call(session_id, api_name, response_time, status_code, tokens_used, details)

# 初始化日志
logger.info("LangGraph监控集成初始化完成", extra={
    "component": "monitoring_integration",
    "logging_integration": LOGGING_CONFIG_AVAILABLE,
    "features": ["session_monitoring", "node_monitoring", "api_tracking", "performance_integration"]
})