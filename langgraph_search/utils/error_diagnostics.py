"""
LangGraph错误跟踪和诊断工具
提供详细的错误分析、根因诊断和恢复建议
"""

import traceback
import sys
import re
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json
import hashlib

# 导入日志配置
try:
    from config.logging_config import (
        error_tracker,
        get_logger,
        ErrorTracker
    )
    LOGGING_CONFIG_AVAILABLE = True
    logger = get_logger("langgraph.diagnostics")
except ImportError:
    LOGGING_CONFIG_AVAILABLE = False
    error_tracker = None
    import logging
    logger = logging.getLogger(__name__)

@dataclass
class ErrorSignature:
    """错误签名"""
    error_type: str
    error_message: str
    error_hash: str
    file_path: str = ""
    line_number: int = 0
    function_name: str = ""
    
    @classmethod
    def from_exception(cls, exc: Exception, tb: Optional[object] = None) -> 'ErrorSignature':
        """从异常对象创建错误签名"""
        error_type = type(exc).__name__
        error_message = str(exc)
        
        # 生成错误哈希
        hash_input = f"{error_type}:{error_message}"
        error_hash = hashlib.md5(hash_input.encode()).hexdigest()[:12]
        
        # 提取堆栈信息
        file_path = ""
        line_number = 0
        function_name = ""
        
        if tb:
            frame_summary = traceback.extract_tb(tb)[-1]  # 最后一帧
            file_path = frame_summary.filename
            line_number = frame_summary.lineno
            function_name = frame_summary.name
        
        return cls(
            error_type=error_type,
            error_message=error_message,
            error_hash=error_hash,
            file_path=file_path,
            line_number=line_number,
            function_name=function_name
        )

@dataclass
class ErrorContext:
    """错误上下文信息"""
    node_name: str = ""
    operation_type: str = ""
    session_id: str = ""
    user_query: str = ""
    state_data: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class DiagnosticReport:
    """诊断报告"""
    error_signature: ErrorSignature
    error_context: ErrorContext
    root_cause_analysis: str = ""
    recovery_suggestions: List[str] = field(default_factory=list)
    similar_errors: List[str] = field(default_factory=list)
    severity: str = "medium"  # low, medium, high, critical
    impact_assessment: str = ""
    prevention_tips: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "error_signature": {
                "error_type": self.error_signature.error_type,
                "error_message": self.error_signature.error_message,
                "error_hash": self.error_signature.error_hash,
                "file_path": self.error_signature.file_path,
                "line_number": self.error_signature.line_number,
                "function_name": self.error_signature.function_name
            },
            "error_context": {
                "node_name": self.error_context.node_name,
                "operation_type": self.error_context.operation_type,
                "session_id": self.error_context.session_id,
                "user_query": self.error_context.user_query,
                "timestamp": self.error_context.timestamp
            },
            "analysis": {
                "root_cause_analysis": self.root_cause_analysis,
                "recovery_suggestions": self.recovery_suggestions,
                "similar_errors": self.similar_errors,
                "severity": self.severity,
                "impact_assessment": self.impact_assessment,
                "prevention_tips": self.prevention_tips
            }
        }

class ErrorPatternMatcher:
    """错误模式匹配器"""
    
    def __init__(self):
        # 常见错误模式和对应的诊断信息
        self.patterns = {
            # API相关错误
            r"serper.*api.*key": {
                "root_cause": "Serper API密钥缺失或无效",
                "recovery": [
                    "检查环境变量SERPER_API_KEY是否设置",
                    "验证API密钥是否有效且未过期",
                    "确认API配额是否充足"
                ],
                "severity": "high",
                "prevention": ["定期检查API配额", "设置API密钥监控", "准备备用API密钥"]
            },
            r"openai.*api.*key": {
                "root_cause": "OpenAI API密钥缺失或无效",
                "recovery": [
                    "检查环境变量OPENAI_API_KEY是否设置",
                    "验证API密钥格式是否正确",
                    "确认账户余额是否充足"
                ],
                "severity": "high",
                "prevention": ["监控API使用量", "设置余额告警", "配置备用LLM提供商"]
            },
            r"timeout|timed out": {
                "root_cause": "请求超时，可能是网络问题或服务响应慢",
                "recovery": [
                    "增加超时时间配置",
                    "检查网络连接状态",
                    "重试请求或使用缓存结果"
                ],
                "severity": "medium",
                "prevention": ["优化网络配置", "实施重试机制", "使用负载均衡"]
            },
            r"rate.*limit": {
                "root_cause": "API调用频率超出限制",
                "recovery": [
                    "等待重置周期后重试",
                    "实施指数退避策略",
                    "优化API调用频率"
                ],
                "severity": "medium",
                "prevention": ["实施速率限制", "使用请求队列", "缓存API响应"]
            },
            r"connection.*refused|connection.*failed": {
                "root_cause": "网络连接失败或服务不可用",
                "recovery": [
                    "检查网络连接",
                    "验证目标服务状态",
                    "尝试使用备用服务端点"
                ],
                "severity": "high",
                "prevention": ["配置健康检查", "准备备用服务", "监控网络状态"]
            },
            r"json.*decode": {
                "root_cause": "JSON解析失败，响应格式不正确",
                "recovery": [
                    "检查API响应格式",
                    "验证响应内容编码",
                    "实施响应格式验证"
                ],
                "severity": "medium",
                "prevention": ["添加响应验证", "处理格式异常", "记录异常响应"]
            },
            r"keyerror.*|missing.*key": {
                "root_cause": "数据结构中缺少必需的字段",
                "recovery": [
                    "检查数据结构完整性",
                    "添加字段存在性验证",
                    "使用默认值处理缺失字段"
                ],
                "severity": "medium",
                "prevention": ["数据验证", "使用类型检查", "添加防御性编程"]
            },
            r"memory|out of memory": {
                "root_cause": "内存不足或内存泄漏",
                "recovery": [
                    "释放不必要的内存占用",
                    "优化数据结构",
                    "增加系统内存"
                ],
                "severity": "critical",
                "prevention": ["内存监控", "数据分批处理", "实施内存限制"]
            },
            r"permission.*denied|access.*denied": {
                "root_cause": "权限不足或文件访问被拒绝",
                "recovery": [
                    "检查文件或目录权限",
                    "确认运行用户权限",
                    "修复权限配置"
                ],
                "severity": "high",
                "prevention": ["权限审计", "最小权限原则", "权限监控"]
            }
        }
    
    def match_pattern(self, error_message: str, error_type: str) -> Optional[Dict[str, Any]]:
        """匹配错误模式"""
        combined_text = f"{error_type} {error_message}".lower()
        
        for pattern, info in self.patterns.items():
            if re.search(pattern, combined_text, re.IGNORECASE):
                return info
        
        return None

class ErrorDiagnostics:
    """错误诊断系统"""
    
    def __init__(self):
        self.pattern_matcher = ErrorPatternMatcher()
        self.error_history: List[DiagnosticReport] = []
        self.error_stats = defaultdict(int)
        self.recovery_success_rate = defaultdict(list)
        
        if LOGGING_CONFIG_AVAILABLE:
            self.error_tracker = error_tracker
        else:
            self.error_tracker = None
    
    def diagnose_error(self, exc: Exception, context: ErrorContext, 
                      tb: Optional[object] = None) -> DiagnosticReport:
        """诊断错误并生成报告"""
        
        # 创建错误签名
        error_signature = ErrorSignature.from_exception(exc, tb)
        
        # 模式匹配
        pattern_info = self.pattern_matcher.match_pattern(
            error_signature.error_message, 
            error_signature.error_type
        )
        
        # 查找相似错误
        similar_errors = self._find_similar_errors(error_signature)
        
        # 生成诊断报告
        report = DiagnosticReport(
            error_signature=error_signature,
            error_context=context
        )
        
        if pattern_info:
            report.root_cause_analysis = pattern_info.get("root_cause", "")
            report.recovery_suggestions = pattern_info.get("recovery", [])
            report.severity = pattern_info.get("severity", "medium")
            report.prevention_tips = pattern_info.get("prevention", [])
        else:
            # 通用诊断
            report = self._generic_diagnosis(report)
        
        # 影响评估
        report.impact_assessment = self._assess_impact(report)
        report.similar_errors = similar_errors
        
        # 记录到历史
        self.error_history.append(report)
        self.error_stats[error_signature.error_hash] += 1
        
        # 记录到error_tracker
        if self.error_tracker:
            self.error_tracker.log_error(exc, {
                "node_name": context.node_name,
                "operation_type": context.operation_type,
                "session_id": context.session_id,
                "error_hash": error_signature.error_hash,
                "severity": report.severity
            })
        
        # 保持历史记录在合理范围内
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-500:]
        
        logger.error(f"错误诊断完成: {error_signature.error_hash}", extra={
            "error_hash": error_signature.error_hash,
            "error_type": error_signature.error_type,
            "severity": report.severity,
            "node_name": context.node_name,
            "session_id": context.session_id
        })
        
        return report
    
    def _generic_diagnosis(self, report: DiagnosticReport) -> DiagnosticReport:
        """通用错误诊断"""
        error_type = report.error_signature.error_type
        error_message = report.error_signature.error_message
        
        # 根据错误类型提供通用建议
        if error_type == "KeyError":
            report.root_cause_analysis = "字典或对象中缺少预期的键"
            report.recovery_suggestions = [
                "检查数据结构是否完整",
                "添加键存在性验证",
                "使用get()方法提供默认值"
            ]
            report.severity = "medium"
        
        elif error_type == "TypeError":
            report.root_cause_analysis = "数据类型不匹配或操作不支持"
            report.recovery_suggestions = [
                "检查变量类型",
                "添加类型验证",
                "确认操作方法正确"
            ]
            report.severity = "medium"
        
        elif error_type == "ValueError":
            report.root_cause_analysis = "值错误或格式不正确"
            report.recovery_suggestions = [
                "验证输入值格式",
                "添加值范围检查",
                "提供输入验证"
            ]
            report.severity = "medium"
        
        elif error_type == "ConnectionError":
            report.root_cause_analysis = "网络连接失败"
            report.recovery_suggestions = [
                "检查网络连接",
                "验证服务可用性",
                "实施重试机制"
            ]
            report.severity = "high"
        
        elif error_type == "TimeoutError":
            report.root_cause_analysis = "操作超时"
            report.recovery_suggestions = [
                "增加超时时间",
                "优化操作性能",
                "分批处理数据"
            ]
            report.severity = "medium"
        
        else:
            report.root_cause_analysis = f"遇到未知的{error_type}错误"
            report.recovery_suggestions = [
                "检查错误消息中的具体信息",
                "查看相关日志",
                "联系技术支持"
            ]
            report.severity = "medium"
        
        # 通用预防建议
        report.prevention_tips = [
            "添加异常处理",
            "实施输入验证",
            "增加错误日志",
            "设置监控告警"
        ]
        
        return report
    
    def _assess_impact(self, report: DiagnosticReport) -> str:
        """评估错误影响"""
        severity = report.severity
        node_name = report.error_context.node_name
        
        impact_map = {
            "critical": f"严重影响：{node_name}节点完全失效，可能导致整个工作流中断",
            "high": f"高影响：{node_name}节点失效，影响主要功能，需要立即处理",
            "medium": f"中等影响：{node_name}节点部分功能受限，可能影响用户体验",
            "low": f"低影响：{node_name}节点轻微问题，不影响核心功能"
        }
        
        return impact_map.get(severity, "影响程度未知")
    
    def _find_similar_errors(self, error_signature: ErrorSignature, limit: int = 5) -> List[str]:
        """查找相似错误"""
        similar = []
        
        for report in reversed(self.error_history[-100:]):  # 最近100个错误
            if report.error_signature.error_hash == error_signature.error_hash:
                continue
                
            # 检查相似性
            if (report.error_signature.error_type == error_signature.error_type or
                report.error_signature.function_name == error_signature.function_name):
                similar.append(report.error_signature.error_hash)
                
                if len(similar) >= limit:
                    break
        
        return similar
    
    def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """获取错误统计"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_errors = [
            report for report in self.error_history
            if datetime.fromisoformat(report.error_context.timestamp) > cutoff_time
        ]
        
        if not recent_errors:
            return {"message": f"过去{hours}小时内无错误记录"}
        
        # 按错误类型统计
        error_types = Counter(report.error_signature.error_type for report in recent_errors)
        
        # 按节点统计
        error_nodes = Counter(report.error_context.node_name for report in recent_errors)
        
        # 按严重性统计
        severity_stats = Counter(report.severity for report in recent_errors)
        
        # 最频繁的错误
        most_common_hash = Counter(
            report.error_signature.error_hash for report in recent_errors
        ).most_common(1)
        
        return {
            "time_period": f"过去{hours}小时",
            "total_errors": len(recent_errors),
            "unique_errors": len(set(report.error_signature.error_hash for report in recent_errors)),
            "error_types": dict(error_types),
            "error_nodes": dict(error_nodes),
            "severity_distribution": dict(severity_stats),
            "most_common_error": most_common_hash[0] if most_common_hash else None,
            "error_rate": len(recent_errors) / hours  # 每小时错误数
        }
    
    def get_recovery_recommendations(self, error_hash: str) -> Optional[Dict[str, Any]]:
        """获取恢复建议"""
        # 查找匹配的错误
        matching_reports = [
            report for report in self.error_history
            if report.error_signature.error_hash == error_hash
        ]
        
        if not matching_reports:
            return None
        
        latest_report = matching_reports[-1]
        
        return {
            "error_hash": error_hash,
            "occurrence_count": len(matching_reports),
            "latest_occurrence": latest_report.error_context.timestamp,
            "root_cause": latest_report.root_cause_analysis,
            "recovery_suggestions": latest_report.recovery_suggestions,
            "prevention_tips": latest_report.prevention_tips,
            "severity": latest_report.severity,
            "impact": latest_report.impact_assessment
        }
    
    def export_diagnostic_report(self, session_id: Optional[str] = None, 
                               hours: int = 24) -> str:
        """导出诊断报告"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # 过滤报告
        reports = [
            report for report in self.error_history
            if datetime.fromisoformat(report.error_context.timestamp) > cutoff_time
        ]
        
        if session_id:
            reports = [
                report for report in reports
                if report.error_context.session_id == session_id
            ]
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "time_period": f"过去{hours}小时",
            "session_filter": session_id,
            "total_reports": len(reports),
            "reports": [report.to_dict() for report in reports],
            "statistics": self.get_error_statistics(hours)
        }
        
        return json.dumps(export_data, ensure_ascii=False, indent=2)

# 全局诊断器实例
_global_diagnostics: Optional[ErrorDiagnostics] = None

def get_error_diagnostics() -> ErrorDiagnostics:
    """获取全局错误诊断器"""
    global _global_diagnostics
    
    if _global_diagnostics is None:
        _global_diagnostics = ErrorDiagnostics()
    
    return _global_diagnostics

def diagnose_exception(exc: Exception, node_name: str = "", operation_type: str = "",
                      session_id: str = "", user_query: str = "",
                      state_data: Optional[Dict] = None) -> DiagnosticReport:
    """诊断异常的便捷函数"""
    diagnostics = get_error_diagnostics()
    
    context = ErrorContext(
        node_name=node_name,
        operation_type=operation_type,
        session_id=session_id,
        user_query=user_query,
        state_data=state_data or {}
    )
    
    return diagnostics.diagnose_error(exc, context, sys.exc_info()[2])

def get_error_recovery_guide(error_hash: str) -> Optional[Dict[str, Any]]:
    """获取错误恢复指南"""
    diagnostics = get_error_diagnostics()
    return diagnostics.get_recovery_recommendations(error_hash)

def get_diagnostic_summary(hours: int = 24) -> Dict[str, Any]:
    """获取诊断摘要"""
    diagnostics = get_error_diagnostics()
    return diagnostics.get_error_statistics(hours)

# 错误处理装饰器
def with_error_diagnosis(node_name: str, operation_type: str = "execution"):
    """错误诊断装饰器"""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                # 尝试从参数中获取会话信息
                session_id = ""
                user_query = ""
                state_data = {}
                
                if args and isinstance(args[0], dict):
                    state = args[0]
                    session_id = state.get("session_id", "")
                    user_query = state.get("user_query", "")
                    state_data = state
                
                # 进行错误诊断
                report = diagnose_exception(
                    exc, node_name, operation_type, 
                    session_id, user_query, state_data
                )
                
                # 记录诊断结果
                logger.error(f"节点错误已诊断: {node_name}", extra={
                    "error_hash": report.error_signature.error_hash,
                    "severity": report.severity,
                    "recovery_suggestions": len(report.recovery_suggestions)
                })
                
                # 重新抛出异常
                raise
        
        return wrapper
    return decorator

# 初始化日志
logger.info("LangGraph错误诊断系统初始化完成", extra={
    "component": "error_diagnostics",
    "logging_integration": LOGGING_CONFIG_AVAILABLE,
    "features": ["pattern_matching", "root_cause_analysis", "recovery_suggestions", "impact_assessment"]
})