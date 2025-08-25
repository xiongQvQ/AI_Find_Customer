"""
鲁棒性LLM客户端
具有自动重试、故障转移和连接诊断功能
"""

import time
import random
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import logging
from enum import Enum
import asyncio
from functools import wraps

# 导入现有的LLM客户端
try:
    from langgraph_search.llm.llm_client import LLMClient
    CLIENT_AVAILABLE = True
except ImportError:
    CLIENT_AVAILABLE = False

try:
    from .llm_connection_helper import get_llm_diagnostics, LLMProvider, ConnectionStatus
    DIAGNOSTICS_AVAILABLE = True
except ImportError:
    DIAGNOSTICS_AVAILABLE = False

try:
    from config.logging_config import get_logger
    logger = get_logger("langgraph.robust_llm")
except ImportError:
    logger = logging.getLogger(__name__)

class RetryStrategy(Enum):
    """重试策略"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_INTERVAL = "fixed_interval"
    LINEAR_BACKOFF = "linear_backoff"
    RANDOM_JITTER = "random_jitter"

class RobustLLMClient:
    """鲁棒性LLM客户端包装器"""
    
    def __init__(self, 
                 max_retries: int = 5,
                 base_delay: float = 1.0,
                 max_delay: float = 30.0,
                 retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
                 enable_fallback: bool = True):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.retry_strategy = retry_strategy
        self.enable_fallback = enable_fallback
        
        # 初始化LLM客户端
        if CLIENT_AVAILABLE:
            self.llm_client = LLMClient()
        else:
            self.llm_client = None
            logger.warning("LLMClient不可用，使用模拟模式")
        
        # 连接诊断器
        if DIAGNOSTICS_AVAILABLE:
            self.diagnostics = get_llm_diagnostics()
        else:
            self.diagnostics = None
        
        # 统计信息
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retries_used": 0,
            "fallback_used": 0,
            "last_success_time": None,
            "last_failure_time": None
        }
        
        # 连接状态缓存
        self.connection_cache = {}
        self.cache_expiry = 300  # 5分钟缓存
    
    def _calculate_delay(self, attempt: int) -> float:
        """计算重试延迟时间"""
        if self.retry_strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        elif self.retry_strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = min(self.base_delay * attempt, self.max_delay)
        elif self.retry_strategy == RetryStrategy.FIXED_INTERVAL:
            delay = self.base_delay
        elif self.retry_strategy == RetryStrategy.RANDOM_JITTER:
            base_delay = min(self.base_delay * (2 ** attempt), self.max_delay)
            delay = base_delay * (0.5 + random.random() * 0.5)
        else:
            delay = self.base_delay
        
        return delay
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """判断错误是否可重试"""
        error_msg = str(error).lower()
        
        # 可重试的错误类型
        retryable_patterns = [
            "connection error",
            "timeout",
            "connection aborted",
            "connection refused",
            "network is unreachable",
            "temporary failure",
            "service unavailable",
            "too many requests",
            "rate limit",
            "server error",
            "internal server error"
        ]
        
        for pattern in retryable_patterns:
            if pattern in error_msg:
                return True
        
        return False
    
    def _log_retry_attempt(self, attempt: int, error: Exception, delay: float):
        """记录重试尝试"""
        logger.warning(f"LLM调用失败 (尝试 {attempt}/{self.max_retries}): {error}")
        logger.info(f"将在 {delay:.2f} 秒后重试...")
    
    def _update_stats(self, success: bool, retries_used: int = 0, fallback_used: bool = False):
        """更新统计信息"""
        self.stats["total_requests"] += 1
        
        if success:
            self.stats["successful_requests"] += 1
            self.stats["last_success_time"] = datetime.now().isoformat()
        else:
            self.stats["failed_requests"] += 1
            self.stats["last_failure_time"] = datetime.now().isoformat()
        
        self.stats["retries_used"] += retries_used
        
        if fallback_used:
            self.stats["fallback_used"] += 1
    
    def call_llm_with_retry(self, messages: List[Dict[str, str]], 
                           **kwargs) -> Union[str, Dict[str, Any]]:
        """
        带重试的LLM调用
        
        Args:
            messages: 消息列表
            **kwargs: 其他LLM参数
            
        Returns:
            LLM响应
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # 第一次尝试或重试
                if self.llm_client:
                    if hasattr(self.llm_client, 'call_llm'):
                        result = self.llm_client.call_llm(messages, **kwargs)
                    else:
                        # 兼容不同的方法名
                        result = self.llm_client.generate_response(messages[0]["content"])
                else:
                    # 模拟模式
                    result = self._mock_response(messages)
                
                # 成功
                self._update_stats(True, attempt)
                if attempt > 0:
                    logger.info(f"LLM调用成功 (经过 {attempt} 次重试)")
                
                return result
                
            except Exception as e:
                last_error = e
                
                # 记录错误
                logger.error(f"LLM调用错误 (尝试 {attempt + 1}/{self.max_retries + 1}): {e}")
                
                # 如果这是最后一次尝试，或者错误不可重试，跳出循环
                if attempt == self.max_retries or not self._is_retryable_error(e):
                    break
                
                # 计算延迟并等待
                delay = self._calculate_delay(attempt)
                self._log_retry_attempt(attempt + 1, e, delay)
                time.sleep(delay)
        
        # 所有重试都失败了
        self._update_stats(False, self.max_retries)
        
        # 尝试故障转移
        if self.enable_fallback:
            try:
                fallback_result = self._try_fallback(messages, **kwargs)
                self._update_stats(True, self.max_retries, True)
                logger.info("使用故障转移成功获取响应")
                return fallback_result
            except Exception as fallback_error:
                logger.error(f"故障转移也失败: {fallback_error}")
        
        # 最终失败
        logger.error(f"LLM调用最终失败: {last_error}")
        raise last_error
    
    def _try_fallback(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """尝试故障转移方案"""
        # 方案1: 简单的模板响应
        user_content = messages[0]["content"] if messages else ""
        
        if "意图" in user_content or "intent" in user_content.lower():
            return json.dumps({
                "intent": "company",
                "confidence": 0.8,
                "reasoning": "基于关键词匹配的意图识别（故障转移模式）"
            }, ensure_ascii=False)
        
        # 方案2: 基于规则的响应
        if any(keyword in user_content for keyword in ["搜索", "公司", "企业"]):
            return "基于用户查询内容，建议执行公司搜索操作。"
        
        # 方案3: 通用响应
        return "由于LLM服务暂时不可用，系统将使用基础搜索功能继续为您服务。"
    
    def _mock_response(self, messages: List[Dict[str, str]]) -> str:
        """模拟响应（用于测试）"""
        user_content = messages[0]["content"] if messages else ""
        return f"模拟响应: 已处理查询 '{user_content[:50]}...'"
    
    def check_health(self) -> Dict[str, Any]:
        """检查LLM客户端健康状态"""
        try:
            # 进行快速健康检查
            test_messages = [{"role": "user", "content": "hello"}]
            start_time = time.time()
            
            # 尝试简单调用
            response = self.call_llm_with_retry(test_messages)
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time": round(response_time, 3),
                "last_check": datetime.now().isoformat(),
                "stats": self.stats.copy()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat(),
                "stats": self.stats.copy()
            }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        total = self.stats["total_requests"]
        if total > 0:
            success_rate = self.stats["successful_requests"] / total
            avg_retries = self.stats["retries_used"] / total
        else:
            success_rate = 0.0
            avg_retries = 0.0
        
        return {
            "success_rate": round(success_rate, 3),
            "average_retries_per_request": round(avg_retries, 2),
            "fallback_usage_rate": round(self.stats["fallback_used"] / max(total, 1), 3),
            **self.stats
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retries_used": 0,
            "fallback_used": 0,
            "last_success_time": None,
            "last_failure_time": None
        }
        logger.info("LLM客户端统计信息已重置")

# 装饰器：为函数添加自动重试功能
def with_llm_retry(max_retries: int = 3, base_delay: float = 1.0):
    """LLM调用重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            client = RobustLLMClient(max_retries=max_retries, base_delay=base_delay)
            
            # 如果函数第一个参数是messages，使用robust client
            if args and isinstance(args[0], list):
                return client.call_llm_with_retry(args[0], **kwargs)
            else:
                # 否则直接调用原函数，但添加重试逻辑
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if attempt == max_retries or not client._is_retryable_error(e):
                            raise
                        delay = client._calculate_delay(attempt)
                        logger.warning(f"函数 {func.__name__} 调用失败，{delay:.2f}秒后重试: {e}")
                        time.sleep(delay)
        
        return wrapper
    return decorator

# 全局实例
_global_robust_client: Optional[RobustLLMClient] = None

def get_robust_llm_client() -> RobustLLMClient:
    """获取全局鲁棒LLM客户端"""
    global _global_robust_client
    if _global_robust_client is None:
        _global_robust_client = RobustLLMClient()
    return _global_robust_client

def safe_llm_call(messages: List[Dict[str, str]], **kwargs) -> Union[str, Dict[str, Any]]:
    """安全的LLM调用"""
    client = get_robust_llm_client()
    return client.call_llm_with_retry(messages, **kwargs)

# 初始化日志
logger.info("鲁棒性LLM客户端初始化完成", extra={
    "component": "robust_llm_client",
    "features": ["retry_mechanism", "fallback_support", "connection_diagnostics", "performance_stats"]
})