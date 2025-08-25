"""
系统监控和日志配置
为LangGraph智能搜索系统提供完整的日志记录和监控功能
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import json

# 创建日志目录
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

class StructuredFormatter(logging.Formatter):
    """结构化日志格式器，支持JSON输出"""
    
    def __init__(self, include_json: bool = True):
        super().__init__()
        self.include_json = include_json
    
    def format(self, record):
        # 基础信息
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加异常信息
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # 添加自定义字段
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 
                          'pathname', 'filename', 'module', 'lineno', 'funcName',
                          'created', 'msecs', 'relativeCreated', 'thread',
                          'threadName', 'processName', 'process', 'exc_info',
                          'exc_text', 'stack_info', 'getMessage']:
                log_entry[key] = value
        
        if self.include_json:
            return json.dumps(log_entry, ensure_ascii=False, default=str)
        else:
            return f"[{log_entry['timestamp']}] {log_entry['level']} - {log_entry['logger']} - {log_entry['message']}"

class LangGraphLogger:
    """LangGraph专用日志管理器"""
    
    def __init__(self):
        self.loggers: Dict[str, logging.Logger] = {}
        self._setup_loggers()
    
    def _setup_loggers(self):
        """设置各种日志记录器"""
        
        # 主应用日志
        self.setup_logger(
            name="langgraph.app",
            filename="app.log",
            level=logging.INFO,
            max_bytes=10*1024*1024,  # 10MB
            backup_count=5
        )
        
        # 工作流执行日志
        self.setup_logger(
            name="langgraph.workflow",
            filename="workflow.log", 
            level=logging.DEBUG,
            max_bytes=20*1024*1024,  # 20MB
            backup_count=10
        )
        
        # API调用日志
        self.setup_logger(
            name="langgraph.api",
            filename="api.log",
            level=logging.INFO,
            max_bytes=15*1024*1024,  # 15MB
            backup_count=7
        )
        
        # 错误和异常日志
        self.setup_logger(
            name="langgraph.error",
            filename="error.log",
            level=logging.ERROR,
            max_bytes=50*1024*1024,  # 50MB
            backup_count=10
        )
        
        # 性能监控日志
        self.setup_logger(
            name="langgraph.performance",
            filename="performance.log",
            level=logging.INFO,
            max_bytes=30*1024*1024,  # 30MB
            backup_count=5
        )
        
        # 用户活动日志
        self.setup_logger(
            name="langgraph.user",
            filename="user_activity.log",
            level=logging.INFO,
            max_bytes=25*1024*1024,  # 25MB
            backup_count=15
        )
    
    def setup_logger(self, name: str, filename: str, level: int = logging.INFO,
                    max_bytes: int = 10*1024*1024, backup_count: int = 5) -> logging.Logger:
        """设置单个日志记录器"""
        
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
        
        # 文件处理器 - 结构化JSON格式
        file_handler = logging.handlers.RotatingFileHandler(
            filename=LOG_DIR / filename,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(StructuredFormatter(include_json=True))
        
        # 控制台处理器 - 人类可读格式
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(StructuredFormatter(include_json=False))
        console_handler.setLevel(logging.WARNING)  # 控制台只显示警告及以上
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        self.loggers[name] = logger
        return logger
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志记录器"""
        if name not in self.loggers:
            # 如果是已知的日志类型，返回对应的记录器
            if name.startswith("langgraph."):
                base_name = name.split(".")[1] if len(name.split(".")) > 1 else "app"
                logger_mapping = {
                    "app": "langgraph.app",
                    "workflow": "langgraph.workflow", 
                    "api": "langgraph.api",
                    "error": "langgraph.error",
                    "performance": "langgraph.performance",
                    "user": "langgraph.user"
                }
                return self.loggers.get(logger_mapping.get(base_name, "langgraph.app"))
        
        return self.loggers.get(name, self.loggers["langgraph.app"])

# 全局日志管理器实例
_logger_manager = LangGraphLogger()

def get_logger(name: str) -> logging.Logger:
    """获取日志记录器的便捷函数"""
    return _logger_manager.get_logger(name)

# 预定义的日志记录器
app_logger = get_logger("langgraph.app")
workflow_logger = get_logger("langgraph.workflow")
api_logger = get_logger("langgraph.api")
error_logger = get_logger("langgraph.error")
performance_logger = get_logger("langgraph.performance")
user_logger = get_logger("langgraph.user")

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.logger = performance_logger
        self.metrics_history = []
        self.alert_thresholds = {
            "response_time": 30.0,    # 30秒
            "memory_usage": 1000.0,   # 1GB
            "cpu_usage": 80.0,        # 80%
            "error_rate": 0.05        # 5%
        }
    
    def log_performance(self, metrics: Dict):
        """记录性能指标"""
        self.logger.info("Performance metrics", extra=metrics)
        self.metrics_history.append({
            **metrics,
            "timestamp": datetime.now().isoformat()
        })
        
        # 保持历史记录在合理范围内
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-500:]
        
        # 检查性能阈值
        self._check_performance_alerts(metrics)
    
    def _check_performance_alerts(self, metrics: Dict):
        """检查性能告警阈值"""
        for key, threshold in self.alert_thresholds.items():
            if key in metrics and metrics[key] > threshold:
                self.logger.warning(
                    f"Performance alert: {key} exceeded threshold",
                    extra={
                        "alert_type": "performance_threshold",
                        "metric": key,
                        "value": metrics[key],
                        "threshold": threshold
                    }
                )
    
    def get_performance_summary(self) -> Dict:
        """获取性能摘要"""
        if not self.metrics_history:
            return {}
        
        recent_metrics = self.metrics_history[-100:]  # 最近100条记录
        
        response_times = [m.get("response_time", 0) for m in recent_metrics if "response_time" in m]
        memory_usage = [m.get("memory_usage", 0) for m in recent_metrics if "memory_usage" in m]
        
        return {
            "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "avg_memory_usage": sum(memory_usage) / len(memory_usage) if memory_usage else 0,
            "max_memory_usage": max(memory_usage) if memory_usage else 0,
            "total_requests": len(recent_metrics),
            "time_window": "last_100_requests"
        }

class ErrorTracker:
    """错误跟踪器"""
    
    def __init__(self):
        self.logger = error_logger
        self.error_counts = {}
        self.recent_errors = []
    
    def log_error(self, error: Exception, context: Dict = None):
        """记录错误"""
        error_type = type(error).__name__
        error_msg = str(error)
        
        # 更新错误计数
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1
        
        # 记录到日志
        self.logger.error(
            f"{error_type}: {error_msg}",
            extra={
                "error_type": error_type,
                "error_message": error_msg,
                "context": context or {},
                "error_count": self.error_counts[error_type]
            },
            exc_info=True
        )
        
        # 保存到最近错误列表
        self.recent_errors.append({
            "timestamp": datetime.now().isoformat(),
            "type": error_type,
            "message": error_msg,
            "context": context or {}
        })
        
        # 保持最近错误列表在合理范围内
        if len(self.recent_errors) > 100:
            self.recent_errors = self.recent_errors[-50:]
    
    def get_error_summary(self) -> Dict:
        """获取错误摘要"""
        return {
            "error_counts": self.error_counts.copy(),
            "recent_errors_count": len(self.recent_errors),
            "most_common_error": max(self.error_counts.items(), key=lambda x: x[1]) if self.error_counts else None
        }

# 全局监控实例
performance_monitor = PerformanceMonitor()
error_tracker = ErrorTracker()

def log_user_action(user_id: str, action: str, details: Dict = None):
    """记录用户操作"""
    user_logger.info(
        f"User action: {action}",
        extra={
            "user_id": user_id,
            "action": action,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
    )

def log_workflow_step(step_name: str, status: str, duration: float = None, details: Dict = None):
    """记录工作流步骤"""
    workflow_logger.info(
        f"Workflow step: {step_name} - {status}",
        extra={
            "step_name": step_name,
            "status": status,
            "duration": duration,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
    )

def log_api_call(endpoint: str, method: str, status_code: int, response_time: float, details: Dict = None):
    """记录API调用"""
    api_logger.info(
        f"{method} {endpoint} - {status_code}",
        extra={
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "response_time": response_time,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
    )

# 系统启动日志
app_logger.info("LangGraph智能搜索系统日志系统初始化完成", extra={
    "component": "logging_system",
    "log_directory": str(LOG_DIR),
    "loggers_configured": list(_logger_manager.loggers.keys())
})