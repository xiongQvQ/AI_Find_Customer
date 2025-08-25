"""
LangGraph性能管理器
集成缓存、并发控制、资源监控和智能告警的综合性能管理系统
与logging_config.py配合提供完整的监控和告警解决方案
"""

import time
import hashlib
import json
import asyncio
import threading
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, Future
from contextlib import contextmanager
import psutil
import logging
from pathlib import Path

# 导入日志配置模块
try:
    from config.logging_config import (
        performance_monitor as perf_monitor,
        error_tracker,
        get_logger,
        PerformanceMonitor,
        ErrorTracker
    )
    LOGGING_CONFIG_AVAILABLE = True
except ImportError:
    LOGGING_CONFIG_AVAILABLE = False
    perf_monitor = None
    error_tracker = None

# 获取日志记录器
logger = get_logger("langgraph.performance") if LOGGING_CONFIG_AVAILABLE else logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """性能指标数据结构"""
    execution_time: float
    memory_usage: float  # MB
    cpu_usage: float     # %
    api_calls: int
    cache_hits: int
    cache_misses: int
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    node_name: str = ""
    success: bool = True
    tokens_used: int = 0
    operation_type: str = "execution"
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，兼容logging_config"""
        return {
            "timestamp": self.timestamp,
            "node_name": self.node_name,
            "operation_type": self.operation_type,
            "execution_time": self.execution_time,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "api_calls": self.api_calls,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "tokens_used": self.tokens_used,
            "success": self.success,
            "error_message": self.error_message
        }

@dataclass
class CacheEntry:
    """缓存条目数据结构"""
    data: Any
    timestamp: float
    ttl: int  # 秒
    access_count: int
    key: str
    size_bytes: int

class PerformanceCache:
    """高性能缓存系统"""
    
    def __init__(self, max_size_mb: int = 100, default_ttl: int = 3600):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.access_stats = {"hits": 0, "misses": 0}
        self.lock = threading.RLock()
        
    def _calculate_size(self, data: Any) -> int:
        """计算数据大小(字节)"""
        try:
            return len(json.dumps(data, default=str).encode('utf-8'))
        except:
            return 1024  # 默认1KB
    
    def _generate_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        with self.lock:
            entry = self.cache.get(key)
            
            if entry is None:
                self.access_stats["misses"] += 1
                return None
            
            # 检查TTL
            if time.time() - entry.timestamp > entry.ttl:
                del self.cache[key]
                self.access_stats["misses"] += 1
                return None
            
            # 更新访问统计
            entry.access_count += 1
            self.access_stats["hits"] += 1
            return entry.data
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存数据"""
        ttl = ttl or self.default_ttl
        size_bytes = self._calculate_size(data)
        
        with self.lock:
            # 检查大小限制
            if size_bytes > self.max_size_bytes / 4:  # 单个条目不超过最大缓存的1/4
                return False
            
            # 确保有足够空间
            self._ensure_space(size_bytes)
            
            # 创建缓存条目
            entry = CacheEntry(
                data=data,
                timestamp=time.time(),
                ttl=ttl,
                access_count=1,
                key=key,
                size_bytes=size_bytes
            )
            
            self.cache[key] = entry
            return True
    
    def _ensure_space(self, needed_bytes: int):
        """确保有足够的缓存空间"""
        current_size = sum(entry.size_bytes for entry in self.cache.values())
        
        if current_size + needed_bytes > self.max_size_bytes:
            # 按访问次数和时间排序，删除最少使用的条目
            entries_by_priority = sorted(
                self.cache.items(),
                key=lambda x: (x[1].access_count, x[1].timestamp)
            )
            
            for key, entry in entries_by_priority:
                del self.cache[key]
                current_size -= entry.size_bytes
                
                if current_size + needed_bytes <= self.max_size_bytes:
                    break
    
    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.access_stats = {"hits": 0, "misses": 0}
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self.lock:
            total_size = sum(entry.size_bytes for entry in self.cache.values())
            hit_rate = (
                self.access_stats["hits"] / 
                (self.access_stats["hits"] + self.access_stats["misses"])
                if (self.access_stats["hits"] + self.access_stats["misses"]) > 0
                else 0
            )
            
            return {
                "entries": len(self.cache),
                "total_size_mb": total_size / (1024 * 1024),
                "max_size_mb": self.max_size_bytes / (1024 * 1024),
                "hit_rate": hit_rate,
                "hits": self.access_stats["hits"],
                "misses": self.access_stats["misses"]
            }

class ResourceMonitor:
    """资源监控器"""
    
    def __init__(self):
        self.metrics_history: List[Dict[str, Any]] = []
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0
        }
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前系统资源指标"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_mb": memory.used / (1024 * 1024),
                "memory_available_mb": memory.available / (1024 * 1024),
                "disk_percent": disk.percent,
                "disk_used_gb": disk.used / (1024 * 1024 * 1024),
                "disk_free_gb": disk.free / (1024 * 1024 * 1024)
            }
            
            # 记录历史
            self.metrics_history.append(metrics)
            
            # 保持历史记录在合理范围内
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-500:]
            
            return metrics
            
        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_percent": 0
            }
    
    def check_resource_alerts(self) -> List[Dict[str, Any]]:
        """检查资源警报"""
        alerts = []
        metrics = self.get_current_metrics()
        
        for metric_name, threshold in self.alert_thresholds.items():
            value = metrics.get(metric_name, 0)
            if value > threshold:
                alerts.append({
                    "type": "resource_warning",
                    "metric": metric_name,
                    "value": value,
                    "threshold": threshold,
                    "message": f"{metric_name} 使用率 {value:.1f}% 超过阈值 {threshold}%",
                    "timestamp": metrics["timestamp"]
                })
        
        return alerts
    
    def get_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """获取性能摘要"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_metrics = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m["timestamp"]) >= cutoff_time
        ]
        
        if not recent_metrics:
            return {"message": "无足够数据"}
        
        cpu_values = [m["cpu_percent"] for m in recent_metrics if "cpu_percent" in m]
        memory_values = [m["memory_percent"] for m in recent_metrics if "memory_percent" in m]
        
        return {
            "period_hours": hours,
            "sample_count": len(recent_metrics),
            "cpu": {
                "avg": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                "max": max(cpu_values) if cpu_values else 0,
                "min": min(cpu_values) if cpu_values else 0
            },
            "memory": {
                "avg": sum(memory_values) / len(memory_values) if memory_values else 0,
                "max": max(memory_values) if memory_values else 0,
                "min": min(memory_values) if memory_values else 0
            }
        }

class PerformanceManager:
    """
    性能管理器主类
    
    负责整体性能优化：
    - 缓存管理
    - 资源监控
    - 并发控制  
    - 性能度量
    - 优化建议
    """
    
    def __init__(self, 
                 cache_size_mb: int = 100,
                 max_concurrent_tasks: int = 5,
                 enable_monitoring: bool = True):
        self.cache = PerformanceCache(cache_size_mb)
        self.resource_monitor = ResourceMonitor()
        self.max_concurrent_tasks = max_concurrent_tasks
        self.enable_monitoring = enable_monitoring
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_tasks)
        self.performance_history: List[PerformanceMetrics] = []
        
        # 集成logging_config监控器
        if LOGGING_CONFIG_AVAILABLE:
            self.perf_monitor = perf_monitor
            self.error_tracker = error_tracker
            self.logger = logger
        else:
            self.perf_monitor = None
            self.error_tracker = None
            self.logger = logging.getLogger(__name__)
        
        # 增强告警配置
        self.alert_thresholds = {
            "execution_time": {"warning": 10.0, "critical": 30.0},
            "memory_usage": {"warning": 200.0, "critical": 500.0},
            "cpu_usage": {"warning": 70.0, "critical": 90.0},
            "error_rate": {"warning": 0.05, "critical": 0.15},
            "cache_hit_rate": {"warning": 0.3, "critical": 0.1}
        }
        
    def cached_execution(self, 
                        func: Callable,
                        cache_key: str,
                        ttl: Optional[int] = None,
                        *args, **kwargs) -> Tuple[Any, bool]:
        """
        带缓存的函数执行
        
        Returns:
            (result, cache_hit): 结果和是否命中缓存
        """
        # 尝试从缓存获取
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            self.logger.debug(f"缓存命中: {cache_key}")
            return cached_result, True
        
        # 执行函数并缓存结果
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # 存入缓存
            self.cache.set(cache_key, result, ttl)
            self.logger.debug(f"执行完成并缓存: {cache_key}, 耗时: {execution_time:.2f}s")
            
            return result, False
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"执行失败: {cache_key}, 耗时: {execution_time:.2f}s, 错误: {e}")
            raise
    
    def async_execution(self, func: Callable, *args, **kwargs) -> Future:
        """异步执行函数"""
        return self.executor.submit(func, *args, **kwargs)
    
    def batch_execution(self, 
                       tasks: List[Tuple[Callable, tuple, dict]],
                       timeout: Optional[float] = None) -> List[Any]:
        """
        批量执行任务
        
        Args:
            tasks: [(func, args, kwargs), ...] 任务列表
            timeout: 超时时间(秒)
            
        Returns:
            结果列表
        """
        futures = []
        for func, args, kwargs in tasks:
            future = self.executor.submit(func, *args, **kwargs)
            futures.append(future)
        
        results = []
        for i, future in enumerate(futures):
            try:
                result = future.result(timeout=timeout)
                results.append(result)
            except Exception as e:
                self.logger.error(f"批量任务 {i} 执行失败: {e}")
                results.append(None)
        
        return results
    
    def monitor_execution(self, 
                         func: Callable,
                         node_name: str,
                         operation_type: str = "execution",
                         *args, **kwargs) -> Tuple[Any, PerformanceMetrics]:
        """
        监控函数执行性能
        
        Args:
            func: 要执行的函数
            node_name: 节点名称
            operation_type: 操作类型
            
        Returns:
            (result, metrics): 执行结果和性能指标
        """
        start_time = time.time()
        start_metrics = self.resource_monitor.get_current_metrics() if self.enable_monitoring else {}
        
        # 获取缓存统计起始值
        cache_stats_start = self.cache.get_stats()
        
        try:
            result = func(*args, **kwargs)
            success = True
            error_message = ""
        except Exception as e:
            self.logger.error(f"执行失败 {node_name}: {e}")
            # 记录错误到error_tracker
            if self.error_tracker:
                self.error_tracker.log_error(e, {
                    "node_name": node_name,
                    "operation_type": operation_type
                })
            result = e
            success = False
            error_message = str(e)
        
        end_time = time.time()
        end_metrics = self.resource_monitor.get_current_metrics() if self.enable_monitoring else {}
        cache_stats_end = self.cache.get_stats()
        
        # 计算性能指标
        execution_time = end_time - start_time
        memory_usage = end_metrics.get("memory_used_mb", 0) - start_metrics.get("memory_used_mb", 0)
        cpu_usage = end_metrics.get("cpu_percent", 0)
        cache_hits = cache_stats_end["hits"] - cache_stats_start["hits"]
        cache_misses = cache_stats_end["misses"] - cache_stats_start["misses"]
        
        metrics = PerformanceMetrics(
            execution_time=execution_time,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            api_calls=1,  # 这个需要根据实际情况计算
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            timestamp=datetime.now().isoformat(),
            node_name=node_name,
            operation_type=operation_type,
            success=success,
            error_message=error_message,
            tokens_used=0  # 这个需要从LLM调用中获取
        )
        
        # 记录到performance_monitor
        if self.perf_monitor:
            self.perf_monitor.log_performance(metrics.to_dict())
        
        # 记录性能历史
        self.performance_history.append(metrics)
        
        # 检查性能告警
        self._check_performance_alerts(metrics)
        
        # 保持历史记录在合理范围内
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-500:]
        
        return result, metrics
    
    def _check_performance_alerts(self, metrics: PerformanceMetrics):
        """检查性能告警"""
        alerts = []
        
        # 执行时间告警
        if metrics.execution_time > self.alert_thresholds["execution_time"]["critical"]:
            alerts.append({
                "severity": "critical",
                "type": "execution_time",
                "message": f"节点 {metrics.node_name} 执行时间严重超时: {metrics.execution_time:.2f}s",
                "metrics": {"execution_time": metrics.execution_time},
                "node_name": metrics.node_name
            })
        elif metrics.execution_time > self.alert_thresholds["execution_time"]["warning"]:
            alerts.append({
                "severity": "warning",
                "type": "execution_time", 
                "message": f"节点 {metrics.node_name} 执行时间较长: {metrics.execution_time:.2f}s",
                "metrics": {"execution_time": metrics.execution_time},
                "node_name": metrics.node_name
            })
        
        # 内存使用告警
        if metrics.memory_usage > self.alert_thresholds["memory_usage"]["critical"]:
            alerts.append({
                "severity": "critical",
                "type": "memory_usage",
                "message": f"节点 {metrics.node_name} 内存使用过高: {metrics.memory_usage:.1f}MB",
                "metrics": {"memory_usage": metrics.memory_usage},
                "node_name": metrics.node_name
            })
        elif metrics.memory_usage > self.alert_thresholds["memory_usage"]["warning"]:
            alerts.append({
                "severity": "warning",
                "type": "memory_usage",
                "message": f"节点 {metrics.node_name} 内存使用较高: {metrics.memory_usage:.1f}MB", 
                "metrics": {"memory_usage": metrics.memory_usage},
                "node_name": metrics.node_name
            })
        
        # 错误告警
        if not metrics.success:
            alerts.append({
                "severity": "high",
                "type": "execution_error",
                "message": f"节点 {metrics.node_name} 执行失败: {metrics.error_message}",
                "metrics": {"error": metrics.error_message},
                "node_name": metrics.node_name
            })
        
        # 记录告警
        for alert in alerts:
            self.logger.warning(f"性能告警: {alert['message']}", extra={
                "alert_type": alert["type"],
                "severity": alert["severity"],
                "node_name": alert["node_name"],
                "metrics": alert["metrics"]
            })
    
    @contextmanager
    def monitor_node(self, node_name: str, operation_type: str = "execution"):
        """节点监控上下文管理器"""
        start_time = time.time()
        start_metrics = self.resource_monitor.get_current_metrics() if self.enable_monitoring else {}
        cache_stats_start = self.cache.get_stats()
        
        metrics = PerformanceMetrics(
            execution_time=0.0,
            memory_usage=0.0,
            cpu_usage=0.0,
            api_calls=0,
            cache_hits=0,
            cache_misses=0,
            node_name=node_name,
            operation_type=operation_type,
            success=True
        )
        
        try:
            yield metrics
            
        except Exception as e:
            metrics.success = False
            metrics.error_message = str(e)
            
            # 记录错误
            if self.error_tracker:
                self.error_tracker.log_error(e, {
                    "node_name": node_name,
                    "operation_type": operation_type
                })
            raise
            
        finally:
            end_time = time.time()
            end_metrics = self.resource_monitor.get_current_metrics() if self.enable_monitoring else {}
            cache_stats_end = self.cache.get_stats()
            
            # 更新指标
            metrics.execution_time = end_time - start_time
            metrics.memory_usage = end_metrics.get("memory_used_mb", 0) - start_metrics.get("memory_used_mb", 0)
            metrics.cpu_usage = end_metrics.get("cpu_percent", 0)
            metrics.cache_hits = cache_stats_end["hits"] - cache_stats_start["hits"]
            metrics.cache_misses = cache_stats_end["misses"] - cache_stats_start["misses"]
            metrics.timestamp = datetime.now().isoformat()
            
            # 记录到performance_monitor
            if self.perf_monitor:
                self.perf_monitor.log_performance(metrics.to_dict())
            
            # 记录性能历史
            self.performance_history.append(metrics)
            
            # 检查性能告警
            self._check_performance_alerts(metrics)
            
            # 保持历史记录在合理范围内
            if len(self.performance_history) > 1000:
                self.performance_history = self.performance_history[-500:]
    
    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """获取性能优化建议"""
        suggestions = []
        
        # 分析缓存效率
        cache_stats = self.cache.get_stats()
        if cache_stats["hit_rate"] < 0.3 and cache_stats["hits"] + cache_stats["misses"] > 10:
            suggestions.append({
                "type": "cache_optimization",
                "priority": "high",
                "title": "缓存命中率偏低",
                "description": f"当前缓存命中率 {cache_stats['hit_rate']:.1%}，建议优化缓存策略",
                "actions": [
                    "检查缓存键生成逻辑",
                    "增加缓存TTL时间",
                    "扩大缓存容量"
                ]
            })
        
        # 分析资源使用
        resource_alerts = self.resource_monitor.check_resource_alerts()
        if resource_alerts:
            suggestions.append({
                "type": "resource_optimization",
                "priority": "medium",
                "title": "系统资源使用率过高",
                "description": "检测到系统资源使用率超出正常范围",
                "actions": [
                    "减少并发任务数量",
                    "优化内存使用",
                    "检查是否有资源泄漏"
                ]
            })
        
        # 分析执行性能
        if self.performance_history:
            recent_executions = self.performance_history[-50:]  # 最近50次执行
            avg_execution_time = sum(m.execution_time for m in recent_executions) / len(recent_executions)
            
            if avg_execution_time > 30:  # 平均执行时间超过30秒
                suggestions.append({
                    "type": "execution_optimization", 
                    "priority": "medium",
                    "title": "执行时间过长",
                    "description": f"平均执行时间 {avg_execution_time:.1f}秒，建议优化",
                    "actions": [
                        "启用并发执行",
                        "优化搜索参数",
                        "增加缓存使用"
                    ]
                })
        
        # 分析并发使用
        if self.executor._threads and len(self.executor._threads) == self.max_concurrent_tasks:
            suggestions.append({
                "type": "concurrency_optimization",
                "priority": "low", 
                "title": "并发资源已满",
                "description": "当前并发任务已达上限，可能影响响应速度",
                "actions": [
                    "增加最大并发数",
                    "优化任务调度",
                    "使用任务队列"
                ]
            })
        
        return suggestions
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        cache_stats = self.cache.get_stats()
        resource_summary = self.resource_monitor.get_performance_summary()
        optimization_suggestions = self.get_optimization_suggestions()
        
        # 执行统计
        if self.performance_history:
            recent_executions = self.performance_history[-100:]
            execution_stats = {
                "total_executions": len(recent_executions),
                "success_rate": sum(1 for m in recent_executions if m.success) / len(recent_executions),
                "avg_execution_time": sum(m.execution_time for m in recent_executions) / len(recent_executions),
                "total_api_calls": sum(m.api_calls for m in recent_executions),
                "nodes_performance": {}
            }
            
            # 按节点统计性能
            node_stats = {}
            for metrics in recent_executions:
                node = metrics.node_name
                if node not in node_stats:
                    node_stats[node] = []
                node_stats[node].append(metrics.execution_time)
            
            for node, times in node_stats.items():
                execution_stats["nodes_performance"][node] = {
                    "avg_time": sum(times) / len(times),
                    "executions": len(times)
                }
        else:
            execution_stats = {"message": "暂无执行历史"}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cache": cache_stats,
            "resources": resource_summary,
            "execution": execution_stats,
            "optimization_suggestions": optimization_suggestions
        }
    
    def cleanup(self):
        """清理资源"""
        self.executor.shutdown(wait=True)
        self.cache.clear()

# 全局性能管理器实例
_global_performance_manager: Optional[PerformanceManager] = None

def get_performance_manager() -> PerformanceManager:
    """获取全局性能管理器实例"""
    global _global_performance_manager
    
    if _global_performance_manager is None:
        _global_performance_manager = PerformanceManager()
    
    return _global_performance_manager

def performance_cache(ttl: int = 3600):
    """性能缓存装饰器"""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            manager = get_performance_manager()
            
            # 生成缓存键
            cache_key = manager.cache._generate_key(func.__name__, *args, **kwargs)
            
            # 执行带缓存的函数
            result, cache_hit = manager.cached_execution(func, cache_key, ttl, *args, **kwargs)
            
            return result
        return wrapper
    return decorator

def performance_monitor(node_name: str, operation_type: str = "execution"):
    """性能监控装饰器"""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            manager = get_performance_manager()
            result, metrics = manager.monitor_execution(func, node_name, operation_type, *args, **kwargs)
            
            # 如果结果是异常，重新抛出
            if isinstance(result, Exception):
                raise result
            
            return result
        return wrapper
    return decorator

# 便捷函数
def monitor_node_execution(node_name: str, operation_type: str = "execution"):
    """节点执行监控上下文管理器"""
    manager = get_performance_manager()
    return manager.monitor_node(node_name, operation_type)

def get_performance_status() -> Dict[str, Any]:
    """获取性能状态摘要"""
    manager = get_performance_manager()
    
    # 获取基本性能报告
    report = manager.get_performance_report()
    
    # 添加告警信息
    resource_alerts = manager.resource_monitor.check_resource_alerts()
    
    # 集成logging_config的状态
    if LOGGING_CONFIG_AVAILABLE and manager.perf_monitor:
        system_status = manager.perf_monitor.get_performance_summary()
        report["integrated_monitoring"] = system_status
    
    report["resource_alerts"] = resource_alerts
    report["alert_count"] = len(resource_alerts)
    
    return report

def log_workflow_performance(step_name: str, status: str, duration: float = None, details: Dict = None):
    """记录工作流性能信息"""
    if LOGGING_CONFIG_AVAILABLE:
        from config.logging_config import log_workflow_step
        log_workflow_step(step_name, status, duration, details)

def log_api_performance(endpoint: str, method: str, status_code: int, response_time: float, details: Dict = None):
    """记录API调用性能"""
    if LOGGING_CONFIG_AVAILABLE:
        from config.logging_config import log_api_call
        log_api_call(endpoint, method, status_code, response_time, details)

# 启动日志
if LOGGING_CONFIG_AVAILABLE:
    logger.info("增强版LangGraph性能管理器初始化完成", extra={
        "component": "performance_manager_enhanced",
        "logging_integration": True,
        "monitoring_enabled": True
    })
else:
    logger.info("LangGraph性能管理器初始化完成（基础版）", extra={
        "component": "performance_manager_basic",
        "logging_integration": False,
        "monitoring_enabled": True
    })