"""
LangGraph系统状态报告生成器
整合所有监控数据，生成全面的系统健康报告
"""

import json
import platform
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import psutil

# 导入监控组件
try:
    from config.logging_config import (
        performance_monitor,
        error_tracker,
        get_logger,
        app_logger
    )
    LOGGING_CONFIG_AVAILABLE = True
    logger = get_logger("langgraph.reporter")
except ImportError:
    LOGGING_CONFIG_AVAILABLE = False
    import logging
    logger = logging.getLogger(__name__)

try:
    from .performance_manager import get_performance_manager, get_performance_status
    from .monitoring_integration import get_langgraph_monitor, get_monitoring_summary
    from .error_diagnostics import get_error_diagnostics, get_diagnostic_summary
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False
    logger.warning("监控工具模块不可用，将使用基础报告功能")

class SystemReporter:
    """系统状态报告生成器"""
    
    def __init__(self):
        self.report_history: List[Dict[str, Any]] = []
        
        # 检查组件可用性
        self.components_status = {
            "logging_config": LOGGING_CONFIG_AVAILABLE,
            "performance_manager": UTILS_AVAILABLE,
            "monitoring_integration": UTILS_AVAILABLE,
            "error_diagnostics": UTILS_AVAILABLE
        }
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统基本信息"""
        try:
            # 系统信息
            system_info = {
                "platform": platform.platform(),
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "hostname": platform.node(),
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
            }
            
            # CPU信息
            cpu_info = {
                "physical_cores": psutil.cpu_count(logical=False),
                "logical_cores": psutil.cpu_count(logical=True),
                "current_frequency": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
                "usage_percent": psutil.cpu_percent(interval=1)
            }
            
            # 内存信息
            memory = psutil.virtual_memory()
            memory_info = {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "percentage": memory.percent
            }
            
            # 磁盘信息
            disk = psutil.disk_usage('/')
            disk_info = {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percentage": round((disk.used / disk.total) * 100, 2)
            }
            
            # 网络信息
            network = psutil.net_io_counters()
            network_info = {
                "bytes_sent": network.bytes_sent,
                "bytes_received": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_received": network.packets_recv
            }
            
            return {
                "system": system_info,
                "cpu": cpu_info,
                "memory": memory_info,
                "disk": disk_info,
                "network": network_info,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取系统信息失败: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_application_status(self) -> Dict[str, Any]:
        """获取应用程序状态"""
        status = {
            "application_name": "LangGraph智能搜索系统",
            "version": "1.0.0",
            "environment": "production",  # 可以从环境变量获取
            "uptime": self._calculate_uptime(),
            "components": self.components_status.copy(),
            "dependencies": self._check_dependencies(),
            "timestamp": datetime.now().isoformat()
        }
        
        return status
    
    def _calculate_uptime(self) -> str:
        """计算应用程序运行时间"""
        # 这里简化处理，实际可以记录应用启动时间
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        uptime_days = uptime_seconds // 86400
        uptime_hours = (uptime_seconds % 86400) // 3600
        uptime_minutes = (uptime_seconds % 3600) // 60
        
        return f"{int(uptime_days)}天 {int(uptime_hours)}小时 {int(uptime_minutes)}分钟"
    
    def _check_dependencies(self) -> Dict[str, Any]:
        """检查依赖项状态"""
        dependencies = {}
        
        # 检查环境变量
        import os
        env_vars = {
            "SERPER_API_KEY": bool(os.getenv("SERPER_API_KEY")),
            "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
            "ANTHROPIC_API_KEY": bool(os.getenv("ANTHROPIC_API_KEY")),
            "GOOGLE_API_KEY": bool(os.getenv("GOOGLE_API_KEY"))
        }
        dependencies["environment_variables"] = env_vars
        
        # 检查关键文件
        project_root = Path(__file__).parent.parent.parent
        critical_files = [
            project_root / "langgraph_search" / "workflows" / "base_graph.py",
            project_root / "langgraph_search" / "state.py",
            project_root / "config" / "logging_config.py",
            project_root / "pages" / "7_🔍_Intelligent_Search_LangGraph.py"
        ]
        
        file_status = {}
        for file_path in critical_files:
            file_status[str(file_path)] = file_path.exists()
        dependencies["critical_files"] = file_status
        
        # 检查日志目录
        log_dir = project_root / "logs"
        dependencies["log_directory"] = {
            "exists": log_dir.exists(),
            "writable": log_dir.is_dir() and os.access(log_dir, os.W_OK) if log_dir.exists() else False
        }
        
        return dependencies
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        if not UTILS_AVAILABLE:
            return {"error": "性能监控模块不可用"}
        
        try:
            # 获取性能管理器状态
            performance_status = get_performance_status()
            
            # 添加系统资源使用趋势
            performance_status["resource_trends"] = self._get_resource_trends()
            
            return performance_status
            
        except Exception as e:
            logger.error(f"获取性能报告失败: {e}")
            return {"error": str(e)}
    
    def get_monitoring_report(self) -> Dict[str, Any]:
        """获取监控报告"""
        if not UTILS_AVAILABLE:
            return {"error": "监控集成模块不可用"}
        
        try:
            # 获取LangGraph监控摘要
            monitoring_summary = get_monitoring_summary()
            
            # 添加会话统计信息
            langgraph_monitor = get_langgraph_monitor()
            monitoring_summary["session_details"] = {
                "active_sessions": len(langgraph_monitor.active_sessions),
                "completed_sessions": len(langgraph_monitor.session_metrics),
                "recent_sessions": list(langgraph_monitor.session_metrics.keys())[-10:]  # 最近10个会话
            }
            
            return monitoring_summary
            
        except Exception as e:
            logger.error(f"获取监控报告失败: {e}")
            return {"error": str(e)}
    
    def get_error_report(self) -> Dict[str, Any]:
        """获取错误报告"""
        if not UTILS_AVAILABLE:
            return {"error": "错误诊断模块不可用"}
        
        try:
            # 获取诊断摘要
            diagnostic_summary = get_diagnostic_summary(24)  # 24小时内的错误
            
            # 获取错误诊断器
            error_diagnostics = get_error_diagnostics()
            
            # 添加最近的严重错误
            recent_critical_errors = []
            for report in reversed(error_diagnostics.error_history[-20:]):  # 最近20个错误
                if report.severity in ["critical", "high"]:
                    recent_critical_errors.append({
                        "error_hash": report.error_signature.error_hash,
                        "error_type": report.error_signature.error_type,
                        "severity": report.severity,
                        "node_name": report.error_context.node_name,
                        "timestamp": report.error_context.timestamp,
                        "root_cause": report.root_cause_analysis
                    })
                    if len(recent_critical_errors) >= 5:
                        break
            
            diagnostic_summary["recent_critical_errors"] = recent_critical_errors
            
            return diagnostic_summary
            
        except Exception as e:
            logger.error(f"获取错误报告失败: {e}")
            return {"error": str(e)}
    
    def get_logging_status(self) -> Dict[str, Any]:
        """获取日志系统状态"""
        if not LOGGING_CONFIG_AVAILABLE:
            return {"error": "日志配置模块不可用"}
        
        try:
            # 检查日志文件
            project_root = Path(__file__).parent.parent.parent
            log_dir = project_root / "logs"
            
            log_files_status = {}
            if log_dir.exists():
                for log_file in log_dir.glob("*.log"):
                    stat = log_file.stat()
                    log_files_status[log_file.name] = {
                        "size_mb": round(stat.st_size / (1024**2), 2),
                        "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "exists": True
                    }
            
            # 获取性能监控状态
            perf_summary = {}
            if performance_monitor:
                perf_summary = performance_monitor.get_performance_summary()
            
            # 获取错误跟踪状态
            error_summary = {}
            if error_tracker:
                error_summary = error_tracker.get_error_summary()
            
            return {
                "logging_enabled": True,
                "log_directory": str(log_dir),
                "log_files": log_files_status,
                "performance_monitoring": perf_summary,
                "error_tracking": error_summary,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取日志状态失败: {e}")
            return {"error": str(e)}
    
    def _get_resource_trends(self) -> Dict[str, Any]:
        """获取资源使用趋势"""
        try:
            # 这里简化处理，实际可以从历史数据计算趋势
            current_memory = psutil.virtual_memory().percent
            current_cpu = psutil.cpu_percent()
            current_disk = psutil.disk_usage('/').percent
            
            return {
                "memory_trend": "stable",  # 可以基于历史数据计算：increasing/decreasing/stable
                "cpu_trend": "stable",
                "disk_trend": "stable",
                "current_memory_usage": current_memory,
                "current_cpu_usage": current_cpu,
                "current_disk_usage": current_disk,
                "alert_level": self._calculate_alert_level(current_memory, current_cpu, current_disk)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _calculate_alert_level(self, memory_usage: float, cpu_usage: float, disk_usage: float) -> str:
        """计算告警级别"""
        max_usage = max(memory_usage, cpu_usage, disk_usage)
        
        if max_usage >= 90:
            return "critical"
        elif max_usage >= 80:
            return "high"
        elif max_usage >= 70:
            return "medium"
        else:
            return "normal"
    
    def generate_comprehensive_report(self, include_history: bool = False) -> Dict[str, Any]:
        """生成综合系统报告"""
        report_timestamp = datetime.now()
        
        report = {
            "report_metadata": {
                "timestamp": report_timestamp.isoformat(),
                "report_type": "comprehensive_system_status",
                "generated_by": "LangGraph系统监控",
                "report_version": "1.0"
            },
            
            "system_information": self.get_system_info(),
            "application_status": self.get_application_status(),
            "performance_metrics": self.get_performance_report(),
            "monitoring_status": self.get_monitoring_report(),
            "error_analysis": self.get_error_report(),
            "logging_system": self.get_logging_status(),
            
            "health_assessment": self._assess_system_health(report_timestamp),
            "recommendations": self._generate_recommendations(),
            
            "component_availability": self.components_status
        }
        
        # 添加到历史记录
        self.report_history.append({
            "timestamp": report_timestamp.isoformat(),
            "summary": report["health_assessment"]
        })
        
        # 保持历史记录在合理范围内
        if len(self.report_history) > 100:
            self.report_history = self.report_history[-50:]
        
        # 包含历史记录
        if include_history:
            report["report_history"] = self.report_history.copy()
        
        # 记录报告生成
        logger.info("系统状态报告已生成", extra={
            "report_timestamp": report_timestamp.isoformat(),
            "health_status": report["health_assessment"]["overall_status"],
            "components_available": sum(self.components_status.values()),
            "total_components": len(self.components_status)
        })
        
        return report
    
    def _assess_system_health(self, report_time: datetime) -> Dict[str, Any]:
        """评估系统整体健康状况"""
        health_scores = []
        issues = []
        
        # 系统资源健康评估
        try:
            memory_usage = psutil.virtual_memory().percent
            cpu_usage = psutil.cpu_percent()
            disk_usage = psutil.disk_usage('/').percent
            
            resource_score = 100 - max(memory_usage, cpu_usage, disk_usage)
            health_scores.append(resource_score)
            
            if memory_usage > 85:
                issues.append(f"内存使用率过高: {memory_usage:.1f}%")
            if cpu_usage > 85:
                issues.append(f"CPU使用率过高: {cpu_usage:.1f}%")
            if disk_usage > 90:
                issues.append(f"磁盘使用率过高: {disk_usage:.1f}%")
                
        except Exception as e:
            issues.append(f"系统资源评估失败: {e}")
        
        # 组件可用性评估
        available_components = sum(self.components_status.values())
        total_components = len(self.components_status)
        component_score = (available_components / total_components) * 100 if total_components > 0 else 0
        health_scores.append(component_score)
        
        if available_components < total_components:
            missing = total_components - available_components
            issues.append(f"{missing}个监控组件不可用")
        
        # 错误率评估
        if UTILS_AVAILABLE:
            try:
                error_stats = get_diagnostic_summary(1)  # 1小时内错误
                if isinstance(error_stats, dict) and "error_rate" in error_stats:
                    error_rate = error_stats["error_rate"]
                    error_score = max(0, 100 - (error_rate * 10))  # 每小时10个错误扣100分
                    health_scores.append(error_score)
                    
                    if error_rate > 5:
                        issues.append(f"错误率过高: {error_rate:.1f}/小时")
            except Exception as e:
                issues.append(f"错误率评估失败: {e}")
        
        # 计算整体健康分数
        overall_score = sum(health_scores) / len(health_scores) if health_scores else 50
        
        # 确定健康状态
        if overall_score >= 90:
            status = "excellent"
            status_zh = "优秀"
        elif overall_score >= 80:
            status = "good"
            status_zh = "良好"
        elif overall_score >= 70:
            status = "fair"
            status_zh = "一般"
        elif overall_score >= 60:
            status = "poor"
            status_zh = "较差"
        else:
            status = "critical"
            status_zh = "严重"
        
        return {
            "overall_status": status,
            "overall_status_zh": status_zh,
            "health_score": round(overall_score, 1),
            "assessment_time": report_time.isoformat(),
            "issues_found": issues,
            "components_status": self.components_status,
            "detailed_scores": {
                "system_resources": health_scores[0] if len(health_scores) > 0 else 0,
                "component_availability": component_score,
                "error_rate": health_scores[2] if len(health_scores) > 2 else 50
            }
        }
    
    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """生成改进建议"""
        recommendations = []
        
        # 基于系统资源的建议
        try:
            memory_usage = psutil.virtual_memory().percent
            cpu_usage = psutil.cpu_percent()
            disk_usage = psutil.disk_usage('/').percent
            
            if memory_usage > 80:
                recommendations.append({
                    "category": "resource_optimization",
                    "priority": "high",
                    "title": "内存使用优化",
                    "description": f"当前内存使用率 {memory_usage:.1f}%，建议优化内存使用",
                    "actions": [
                        "检查是否有内存泄漏",
                        "优化数据结构和算法",
                        "实施内存缓存清理策略"
                    ]
                })
            
            if cpu_usage > 80:
                recommendations.append({
                    "category": "performance_optimization",
                    "priority": "high",
                    "title": "CPU使用优化",
                    "description": f"当前CPU使用率 {cpu_usage:.1f}%，建议优化处理逻辑",
                    "actions": [
                        "识别CPU密集型操作",
                        "实施异步处理",
                        "考虑分布式处理"
                    ]
                })
            
            if disk_usage > 85:
                recommendations.append({
                    "category": "storage_management",
                    "priority": "medium",
                    "title": "磁盘空间管理",
                    "description": f"当前磁盘使用率 {disk_usage:.1f}%，建议清理空间",
                    "actions": [
                        "清理旧日志文件",
                        "压缩历史数据",
                        "实施日志轮换策略"
                    ]
                })
        except Exception:
            pass
        
        # 基于组件可用性的建议
        if not all(self.components_status.values()):
            recommendations.append({
                "category": "system_integrity",
                "priority": "medium",
                "title": "组件完整性检查",
                "description": "部分监控组件不可用，影响监控功能",
                "actions": [
                    "检查依赖项安装",
                    "验证配置文件",
                    "重新启动相关服务"
                ]
            })
        
        # 通用建议
        recommendations.append({
            "category": "monitoring_enhancement",
            "priority": "low",
            "title": "监控系统增强",
            "description": "建议定期检查系统状态和性能指标",
            "actions": [
                "设置定期健康检查",
                "配置告警阈值",
                "建立监控仪表板"
            ]
        })
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any], file_path: Optional[str] = None) -> str:
        """保存报告到文件"""
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"system_report_{timestamp}.json"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"系统报告已保存: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"保存报告失败: {e}")
            raise

# 全局报告器实例
_global_reporter: Optional[SystemReporter] = None

def get_system_reporter() -> SystemReporter:
    """获取全局系统报告器"""
    global _global_reporter
    
    if _global_reporter is None:
        _global_reporter = SystemReporter()
    
    return _global_reporter

def generate_system_report(include_history: bool = False) -> Dict[str, Any]:
    """生成系统状态报告"""
    reporter = get_system_reporter()
    return reporter.generate_comprehensive_report(include_history)

def save_system_report(file_path: Optional[str] = None, include_history: bool = False) -> str:
    """生成并保存系统状态报告"""
    reporter = get_system_reporter()
    report = reporter.generate_comprehensive_report(include_history)
    return reporter.save_report(report, file_path)

def get_system_health() -> Dict[str, Any]:
    """快速获取系统健康状态"""
    reporter = get_system_reporter()
    return reporter._assess_system_health(datetime.now())

# 初始化日志
logger.info("LangGraph系统状态报告器初始化完成", extra={
    "component": "system_reporter",
    "logging_integration": LOGGING_CONFIG_AVAILABLE,
    "monitoring_integration": UTILS_AVAILABLE,
    "features": ["comprehensive_reporting", "health_assessment", "recommendations", "trend_analysis"]
})