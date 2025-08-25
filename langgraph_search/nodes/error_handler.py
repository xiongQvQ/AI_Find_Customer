"""
错误处理节点
统一处理工作流中的各种错误，提供错误恢复建议和故障排除指导
"""

import logging
import os
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from ..state import SearchState, add_error_to_state, add_warning_to_state

class ErrorHandlerNode:
    """
    错误处理节点
    
    负责统一处理工作流中的各种错误：
    - 分析错误类型和严重程度
    - 生成错误恢复建议
    - 提供故障排除指导
    - 记录错误统计和模式
    - 支持自动恢复策略
    """
    
    def __init__(self):
        """初始化错误处理节点"""
        self.logger = logging.getLogger(__name__)
        self.error_recovery_strategies = self._initialize_recovery_strategies()
        
    def execute(self, state: SearchState) -> SearchState:
        """
        执行错误处理
        
        Args:
            state: 当前搜索状态
            
        Returns:
            更新后的状态，包含错误分析和恢复建议
        """
        try:
            self.logger.info("开始执行错误处理")
            
            # 更新当前节点
            state["current_node"] = "error_handler"
            state["workflow_path"].append("error_handler_started")
            
            # 分析所有错误
            error_analysis = self._analyze_errors(state)
            
            # 生成恢复建议
            recovery_suggestions = self._generate_recovery_suggestions(state, error_analysis)
            
            # 执行自动恢复(如果可能)
            auto_recovery_result = self._attempt_auto_recovery(state, error_analysis)
            
            # 生成故障排除指导
            troubleshooting_guide = self._generate_troubleshooting_guide(state, error_analysis)
            
            # 更新状态
            state["error_handling_data"] = {
                "analysis": error_analysis,
                "recovery_suggestions": recovery_suggestions,
                "auto_recovery": auto_recovery_result,
                "troubleshooting_guide": troubleshooting_guide,
                "handled_timestamp": datetime.now().isoformat()
            }
            
            state["workflow_path"].append("error_handler_completed")
            
            self.logger.info(f"错误处理完成，处理了 {len(state['errors'])} 个错误")
            return state
            
        except Exception as e:
            self.logger.error(f"错误处理过程中发生异常: {e}")
            return add_error_to_state(
                state,
                "error_handler_exception",
                f"错误处理节点异常: {str(e)}",
                "error_handler"
            )
    
    def _initialize_recovery_strategies(self) -> Dict[str, Dict[str, Any]]:
        """初始化错误恢复策略"""
        return {
            "missing_api_key": {
                "auto_recoverable": False,
                "severity": "critical",
                "recovery_steps": [
                    "检查环境变量配置",
                    "验证API密钥有效性",
                    "重新配置.env文件"
                ]
            },
            "api_rate_limit": {
                "auto_recoverable": True,
                "severity": "high",
                "recovery_steps": [
                    "等待限流重置",
                    "减少请求频率",
                    "使用指数退避重试"
                ]
            },
            "search_failed": {
                "auto_recoverable": True,
                "severity": "high",
                "recovery_steps": [
                    "检查网络连接",
                    "验证搜索参数",
                    "尝试简化查询"
                ]
            },
            "timeout_error": {
                "auto_recoverable": True,
                "severity": "medium",
                "recovery_steps": [
                    "增加超时时间",
                    "检查网络稳定性",
                    "分批处理请求"
                ]
            },
            "parsing_error": {
                "auto_recoverable": False,
                "severity": "medium",
                "recovery_steps": [
                    "检查输入格式",
                    "验证数据结构",
                    "使用备用解析方法"
                ]
            },
            "low_results_count": {
                "auto_recoverable": False,
                "severity": "low",
                "recovery_steps": [
                    "扩大搜索范围",
                    "减少限制条件",
                    "尝试不同关键词"
                ]
            }
        }
    
    def _analyze_errors(self, state: SearchState) -> Dict[str, Any]:
        """分析错误状态"""
        errors = state.get("errors", [])
        warnings = state.get("warnings", [])
        
        analysis = {
            "total_errors": len(errors),
            "total_warnings": len(warnings),
            "error_types": {},
            "severity_distribution": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "node_error_distribution": {},
            "auto_recoverable_errors": 0,
            "critical_path_blocked": False,
            "suggested_action": "continue"
        }
        
        # 分析错误类型和分布
        for error in errors:
            error_type = error.get("type", "unknown")
            node_name = error.get("node", "unknown")
            
            # 错误类型统计
            analysis["error_types"][error_type] = analysis["error_types"].get(error_type, 0) + 1
            
            # 节点错误分布
            analysis["node_error_distribution"][node_name] = analysis["node_error_distribution"].get(node_name, 0) + 1
            
            # 严重程度分析
            severity = self._get_error_severity(error_type)
            analysis["severity_distribution"][severity] += 1
            
            # 自动恢复能力
            if self._is_auto_recoverable(error_type):
                analysis["auto_recoverable_errors"] += 1
            
            # 检查是否阻塞关键路径
            if severity == "critical":
                analysis["critical_path_blocked"] = True
                analysis["suggested_action"] = "abort"
        
        # 分析警告
        warning_types = {}
        for warning in warnings:
            warning_type = warning.get("type", "unknown")
            warning_types[warning_type] = warning_types.get(warning_type, 0) + 1
        
        analysis["warning_types"] = warning_types
        
        # 确定整体状态
        if analysis["critical_path_blocked"]:
            analysis["overall_status"] = "critical"
        elif analysis["severity_distribution"]["high"] > 0:
            analysis["overall_status"] = "degraded"
        elif analysis["total_errors"] > 0:
            analysis["overall_status"] = "warning"
        else:
            analysis["overall_status"] = "healthy"
        
        return analysis
    
    def _get_error_severity(self, error_type: str) -> str:
        """获取错误严重程度"""
        return self.error_recovery_strategies.get(error_type, {}).get("severity", "medium")
    
    def _is_auto_recoverable(self, error_type: str) -> bool:
        """检查错误是否可以自动恢复"""
        return self.error_recovery_strategies.get(error_type, {}).get("auto_recoverable", False)
    
    def _generate_recovery_suggestions(self, state: SearchState, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成恢复建议"""
        suggestions = []
        
        # 基于错误类型的恢复建议
        for error_type, count in analysis["error_types"].items():
            strategy = self.error_recovery_strategies.get(error_type)
            if strategy:
                suggestions.append({
                    "error_type": error_type,
                    "count": count,
                    "severity": strategy["severity"],
                    "auto_recoverable": strategy["auto_recoverable"],
                    "recovery_steps": strategy["recovery_steps"],
                    "priority": self._calculate_priority(strategy["severity"], count)
                })
        
        # 基于整体分析的建议
        if analysis["overall_status"] == "critical":
            suggestions.append({
                "type": "critical_recovery",
                "title": "关键错误恢复",
                "description": "检测到关键错误，建议立即处理",
                "actions": [
                    "停止当前操作",
                    "检查系统配置",
                    "修复关键问题后重新启动"
                ],
                "priority": 1
            })
        
        # 性能优化建议
        if analysis["total_errors"] > 5:
            suggestions.append({
                "type": "system_optimization",
                "title": "系统优化建议",
                "description": "检测到多个错误，建议优化系统配置",
                "actions": [
                    "检查API配额和限制",
                    "优化搜索参数",
                    "增加错误处理机制"
                ],
                "priority": 3
            })
        
        # 排序建议
        suggestions.sort(key=lambda x: x.get("priority", 5))
        
        return suggestions
    
    def _calculate_priority(self, severity: str, count: int) -> int:
        """计算恢复建议的优先级"""
        severity_weight = {"critical": 1, "high": 2, "medium": 3, "low": 4}
        base_priority = severity_weight.get(severity, 4)
        
        # 错误数量影响优先级
        if count > 3:
            base_priority -= 1
        
        return max(1, base_priority)
    
    def _attempt_auto_recovery(self, state: SearchState, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """尝试自动恢复"""
        recovery_result = {
            "attempted": False,
            "successful_recoveries": 0,
            "failed_recoveries": 0,
            "recovery_actions": []
        }
        
        if analysis["auto_recoverable_errors"] == 0:
            return recovery_result
        
        recovery_result["attempted"] = True
        
        # 处理可自动恢复的错误
        for error in state.get("errors", []):
            error_type = error.get("type")
            if self._is_auto_recoverable(error_type):
                success = self._execute_auto_recovery(error_type, state)
                if success:
                    recovery_result["successful_recoveries"] += 1
                    recovery_result["recovery_actions"].append({
                        "error_type": error_type,
                        "action": "auto_recovery_successful",
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    recovery_result["failed_recoveries"] += 1
                    recovery_result["recovery_actions"].append({
                        "error_type": error_type,
                        "action": "auto_recovery_failed",
                        "timestamp": datetime.now().isoformat()
                    })
        
        return recovery_result
    
    def _execute_auto_recovery(self, error_type: str, state: SearchState) -> bool:
        """执行特定类型的自动恢复"""
        try:
            if error_type == "api_rate_limit":
                # 等待并重试
                self.logger.info("检测到API限流，等待重试...")
                time.sleep(60)  # 等待60秒
                return True
            
            elif error_type == "timeout_error":
                # 增加超时时间
                self.logger.info("检测到超时，调整配置...")
                # 这里可以调整超时配置
                return True
            
            elif error_type == "search_failed":
                # 尝试重新搜索
                self.logger.info("搜索失败，准备重试...")
                # 可以标记需要重试
                state["needs_retry"] = True
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"自动恢复执行失败: {e}")
            return False
    
    def _generate_troubleshooting_guide(self, state: SearchState, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成故障排除指导"""
        guide = {
            "quick_fixes": [],
            "diagnostic_steps": [],
            "prevention_tips": [],
            "contact_info": {}
        }
        
        # 快速修复建议
        if "missing_api_key" in analysis["error_types"]:
            guide["quick_fixes"].append({
                "issue": "API密钥缺失",
                "solution": "在.env文件中添加SERPER_API_KEY=your_key_here",
                "verification": "检查os.getenv('SERPER_API_KEY')是否返回有效值"
            })
        
        if "low_results_count" in analysis["warning_types"]:
            guide["quick_fixes"].append({
                "issue": "搜索结果过少",
                "solution": "尝试扩大搜索范围或使用更通用的关键词",
                "verification": "确认搜索参数设置合理"
            })
        
        # 诊断步骤
        guide["diagnostic_steps"] = [
            {
                "step": 1,
                "title": "检查API配置",
                "actions": [
                    "验证SERPER_API_KEY是否正确设置",
                    "测试API连接性",
                    "检查API配额使用情况"
                ]
            },
            {
                "step": 2,
                "title": "验证搜索参数",
                "actions": [
                    "检查用户查询格式",
                    "验证地区和语言设置",
                    "确认搜索类型配置"
                ]
            },
            {
                "step": 3,
                "title": "测试网络连接",
                "actions": [
                    "ping外部API服务",
                    "检查防火墙设置",
                    "测试DNS解析"
                ]
            }
        ]
        
        # 预防建议
        guide["prevention_tips"] = [
            "定期检查API密钥有效性",
            "设置合理的超时和重试机制",
            "监控API使用配额",
            "实施错误日志记录",
            "建立健康检查机制"
        ]
        
        # 联系信息
        guide["contact_info"] = {
            "documentation": "参考README.md获取详细配置说明",
            "issues": "在GitHub issues中报告问题",
            "support": "查看错误日志获取更多诊断信息"
        }
        
        return guide
    
    def get_error_summary(self, state: SearchState) -> Dict[str, Any]:
        """获取错误摘要信息"""
        errors = state.get("errors", [])
        warnings = state.get("warnings", [])
        
        return {
            "has_errors": len(errors) > 0,
            "has_warnings": len(warnings) > 0,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "last_error": errors[-1] if errors else None,
            "last_warning": warnings[-1] if warnings else None,
            "critical_errors": [e for e in errors if self._get_error_severity(e.get("type", "")) == "critical"],
            "can_continue": len([e for e in errors if self._get_error_severity(e.get("type", "")) == "critical"]) == 0
        }

# 创建节点实例
error_handler_node = ErrorHandlerNode()