"""
LLM连接诊断和恢复助手
专门处理LLM API连接问题的诊断和自动恢复
"""

import os
import time
import requests
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from enum import Enum

# 导入错误诊断系统
try:
    from .error_diagnostics import get_error_diagnostics, diagnose_exception, ErrorContext
    from config.logging_config import get_logger
    DIAGNOSTICS_AVAILABLE = True
    logger = get_logger("langgraph.llm_helper")
except ImportError:
    DIAGNOSTICS_AVAILABLE = False
    logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    """LLM提供商枚举"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    HUOSHAN = "huoshan"

class ConnectionStatus(Enum):
    """连接状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"

class LLMConnectionDiagnostics:
    """LLM连接诊断器"""
    
    def __init__(self):
        self.connection_history = []
        self.provider_status = {}
        self.retry_configs = {
            LLMProvider.OPENAI: {
                "base_url": "https://api.openai.com/v1/models",
                "timeout": 10,
                "retry_delays": [1, 2, 4, 8, 16]  # 指数退避
            },
            LLMProvider.ANTHROPIC: {
                "base_url": "https://api.anthropic.com/v1/messages",
                "timeout": 10,
                "retry_delays": [1, 2, 4, 8, 16]
            },
            LLMProvider.GOOGLE: {
                "base_url": "https://generativelanguage.googleapis.com/v1/models",
                "timeout": 10,
                "retry_delays": [1, 2, 4, 8, 16]
            },
            LLMProvider.HUOSHAN: {
                "base_url": "https://ark.cn-beijing.volces.com/api/v3/models",
                "timeout": 10,
                "retry_delays": [1, 2, 4, 8, 16]
            }
        }
    
    def check_api_key_availability(self) -> Dict[LLMProvider, bool]:
        """检查API密钥可用性"""
        api_keys = {
            LLMProvider.OPENAI: os.getenv("OPENAI_API_KEY"),
            LLMProvider.ANTHROPIC: os.getenv("ANTHROPIC_API_KEY"),
            LLMProvider.GOOGLE: os.getenv("GOOGLE_API_KEY"),
            LLMProvider.HUOSHAN: os.getenv("ARK_API_KEY")
        }
        
        availability = {}
        for provider, key in api_keys.items():
            availability[provider] = bool(key and len(key.strip()) > 0)
            
        return availability
    
    def test_connection(self, provider: LLMProvider, timeout: int = 10) -> Tuple[ConnectionStatus, Dict[str, Any]]:
        """测试特定提供商的连接"""
        if provider not in self.retry_configs:
            return ConnectionStatus.UNKNOWN, {"error": "不支持的提供商"}
        
        config = self.retry_configs[provider]
        api_keys = self.check_api_key_availability()
        
        # 检查API密钥
        if not api_keys.get(provider, False):
            return ConnectionStatus.UNAVAILABLE, {
                "error": "API密钥未设置或为空",
                "suggestion": f"请设置{provider.value.upper()}_API_KEY环境变量"
            }
        
        # 构建请求头
        headers = self._build_headers(provider)
        if not headers:
            return ConnectionStatus.UNAVAILABLE, {"error": "无法构建请求头"}
        
        start_time = time.time()
        try:
            # 发送测试请求
            response = requests.get(
                config["base_url"],
                headers=headers,
                timeout=timeout
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                status = ConnectionStatus.HEALTHY
                details = {
                    "status_code": response.status_code,
                    "response_time": round(response_time, 3),
                    "message": "连接正常"
                }
            elif response.status_code == 429:
                status = ConnectionStatus.DEGRADED
                details = {
                    "status_code": response.status_code,
                    "response_time": round(response_time, 3),
                    "message": "API限流，建议稍后重试",
                    "suggestion": "实施指数退避策略或减少请求频率"
                }
            elif response.status_code in [401, 403]:
                status = ConnectionStatus.UNAVAILABLE
                details = {
                    "status_code": response.status_code,
                    "response_time": round(response_time, 3),
                    "message": "API密钥验证失败",
                    "suggestion": "检查API密钥是否正确且未过期"
                }
            else:
                status = ConnectionStatus.DEGRADED
                details = {
                    "status_code": response.status_code,
                    "response_time": round(response_time, 3),
                    "message": f"服务响应异常: {response.status_code}"
                }
                
        except requests.exceptions.Timeout:
            status = ConnectionStatus.DEGRADED
            details = {
                "error": "请求超时",
                "timeout": timeout,
                "suggestion": "检查网络连接或增加超时时间"
            }
            
        except requests.exceptions.ConnectionError as e:
            status = ConnectionStatus.UNAVAILABLE
            details = {
                "error": "连接失败",
                "message": str(e),
                "suggestion": "检查网络连接、防火墙设置或代理配置"
            }
            
        except Exception as e:
            status = ConnectionStatus.UNKNOWN
            details = {
                "error": "未知错误",
                "message": str(e)
            }
            
            # 如果有错误诊断系统，记录这个错误
            if DIAGNOSTICS_AVAILABLE:
                try:
                    context = ErrorContext(
                        node_name="llm_connection_test",
                        operation_type="connection_check",
                        session_id="diagnostic"
                    )
                    diagnose_exception(e, "llm_connection_test", "connection_check", "diagnostic")
                except Exception:
                    pass  # 静默处理诊断失败
        
        # 记录连接测试结果
        self.connection_history.append({
            "provider": provider.value,
            "status": status.value,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
        self.provider_status[provider] = status
        
        return status, details
    
    def _build_headers(self, provider: LLMProvider) -> Optional[Dict[str, str]]:
        """构建API请求头"""
        if provider == LLMProvider.OPENAI:
            api_key = os.getenv("OPENAI_API_KEY")
            return {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            } if api_key else None
            
        elif provider == LLMProvider.ANTHROPIC:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            return {
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            } if api_key else None
            
        elif provider == LLMProvider.GOOGLE:
            api_key = os.getenv("GOOGLE_API_KEY")
            return {
                "Content-Type": "application/json"
            } if api_key else None  # Google API uses key in URL
            
        elif provider == LLMProvider.HUOSHAN:
            api_key = os.getenv("ARK_API_KEY")
            return {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            } if api_key else None
            
        return None
    
    def diagnose_all_providers(self) -> Dict[str, Any]:
        """诊断所有可用的LLM提供商"""
        results = {}
        available_count = 0
        healthy_count = 0
        
        logger.info("开始LLM连接诊断...")
        
        for provider in LLMProvider:
            logger.info(f"测试{provider.value}连接...")
            status, details = self.test_connection(provider)
            
            results[provider.value] = {
                "status": status.value,
                "details": details
            }
            
            if status != ConnectionStatus.UNAVAILABLE:
                available_count += 1
                if status == ConnectionStatus.HEALTHY:
                    healthy_count += 1
        
        # 生成诊断摘要
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_providers": len(LLMProvider),
            "available_providers": available_count,
            "healthy_providers": healthy_count,
            "results": results,
            "recommendations": self._generate_recommendations(results)
        }
        
        logger.info(f"LLM连接诊断完成: {healthy_count}/{len(LLMProvider)} 健康, {available_count}/{len(LLMProvider)} 可用")
        
        return summary
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[Dict[str, str]]:
        """生成恢复建议"""
        recommendations = []
        
        healthy_providers = []
        degraded_providers = []
        unavailable_providers = []
        
        for provider, result in results.items():
            status = result["status"]
            if status == "healthy":
                healthy_providers.append(provider)
            elif status == "degraded":
                degraded_providers.append(provider)
            elif status == "unavailable":
                unavailable_providers.append(provider)
        
        # 基于健康状况生成建议
        if len(healthy_providers) == 0:
            recommendations.append({
                "priority": "critical",
                "title": "所有LLM提供商不可用",
                "description": "系统无法正常工作，需要立即修复",
                "actions": "1. 检查网络连接\n2. 验证所有API密钥\n3. 检查防火墙和代理设置\n4. 联系网络管理员"
            })
        elif len(healthy_providers) < 2:
            recommendations.append({
                "priority": "high",
                "title": "LLM提供商冗余不足",
                "description": f"仅有{len(healthy_providers)}个健康提供商，建议增加备用选项",
                "actions": "1. 设置更多API密钥\n2. 配置故障转移逻辑\n3. 监控可用性"
            })
        
        if degraded_providers:
            recommendations.append({
                "priority": "medium",
                "title": "部分提供商性能降级",
                "description": f"以下提供商存在问题: {', '.join(degraded_providers)}",
                "actions": "1. 检查API配额和限制\n2. 优化请求频率\n3. 实施重试策略"
            })
        
        if unavailable_providers:
            recommendations.append({
                "priority": "low",
                "title": "配置更多LLM提供商",
                "description": f"以下提供商未配置: {', '.join(unavailable_providers)}",
                "actions": "1. 申请API密钥\n2. 设置环境变量\n3. 测试连接"
            })
        
        return recommendations
    
    def get_best_provider(self) -> Optional[LLMProvider]:
        """获取当前最佳的LLM提供商"""
        if not self.provider_status:
            # 如果没有状态信息，进行快速诊断
            self.diagnose_all_providers()
        
        # 优先选择健康的提供商
        healthy_providers = [
            provider for provider, status in self.provider_status.items()
            if status == ConnectionStatus.HEALTHY
        ]
        
        if healthy_providers:
            return healthy_providers[0]  # 返回第一个健康的提供商
        
        # 如果没有健康的，选择降级但可用的
        degraded_providers = [
            provider for provider, status in self.provider_status.items()
            if status == ConnectionStatus.DEGRADED
        ]
        
        if degraded_providers:
            return degraded_providers[0]
        
        return None
    
    def suggest_recovery_actions(self) -> List[str]:
        """建议恢复操作"""
        actions = [
            "🔍 **即时检查**:",
            "1. 检查网络连接是否正常",
            "2. 验证API密钥是否设置正确",
            "3. 确认API服务是否可访问",
            "",
            "⚙️ **配置优化**:",
            "4. 增加请求超时时间",
            "5. 实施指数退避重试策略", 
            "6. 配置多个LLM提供商作为备用",
            "",
            "🛠️ **长期解决方案**:",
            "7. 设置连接状态监控",
            "8. 配置自动故障转移",
            "9. 建立API使用量监控和告警"
        ]
        return actions

# 全局诊断器实例
_llm_diagnostics: Optional[LLMConnectionDiagnostics] = None

def get_llm_diagnostics() -> LLMConnectionDiagnostics:
    """获取LLM连接诊断器"""
    global _llm_diagnostics
    if _llm_diagnostics is None:
        _llm_diagnostics = LLMConnectionDiagnostics()
    return _llm_diagnostics

def diagnose_llm_connections() -> Dict[str, Any]:
    """诊断所有LLM连接"""
    diagnostics = get_llm_diagnostics()
    return diagnostics.diagnose_all_providers()

def get_recovery_suggestions() -> List[str]:
    """获取LLM连接恢复建议"""
    diagnostics = get_llm_diagnostics()
    return diagnostics.suggest_recovery_actions()

def find_working_llm_provider() -> Optional[str]:
    """寻找可工作的LLM提供商"""
    diagnostics = get_llm_diagnostics()
    provider = diagnostics.get_best_provider()
    return provider.value if provider else None

if __name__ == "__main__":
    # 命令行诊断模式
    print("🔍 LLM连接诊断工具")
    print("=" * 50)
    
    result = diagnose_llm_connections()
    
    print(f"\n📊 诊断结果 ({result['timestamp']})")
    print(f"总提供商: {result['total_providers']}")
    print(f"可用提供商: {result['available_providers']}")
    print(f"健康提供商: {result['healthy_providers']}")
    
    print("\n📋 详细结果:")
    for provider, details in result['results'].items():
        status_icon = {
            "healthy": "✅",
            "degraded": "⚠️", 
            "unavailable": "❌",
            "unknown": "❓"
        }.get(details["status"], "❓")
        
        print(f"{status_icon} {provider.upper()}: {details['status']}")
        if "message" in details["details"]:
            print(f"   {details['details']['message']}")
    
    print(f"\n💡 恢复建议:")
    suggestions = get_recovery_suggestions()
    for suggestion in suggestions:
        print(suggestion)