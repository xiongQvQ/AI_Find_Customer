#!/usr/bin/env python3
"""
多智能体工作流框架 - 基础架构
实现BaseAgent、MessageBus、WorkflowState等核心组件
"""

import asyncio
import json
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Set
import threading
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================== 数据结构定义 ========================

class WorkflowPhase(Enum):
    """工作流阶段枚举"""
    INIT = "init"
    REQUIREMENT_ANALYSIS = "requirement_analysis"
    STRATEGY_PLANNING = "strategy_planning"
    SEARCH_EXECUTION = "search_execution"
    RESULT_SCORING = "result_scoring"
    RESULT_OPTIMIZATION = "result_optimization"
    COMPLETED = "completed"
    ERROR = "error"

class AgentState(Enum):
    """Agent状态枚举"""
    IDLE = "idle"
    PROCESSING = "processing" 
    WAITING = "waiting"
    ERROR = "error"
    COMPLETED = "completed"

@dataclass
class PriceRange:
    """价格区间"""
    min: Optional[float] = None
    max: Optional[float] = None
    currency: str = "RMB"

@dataclass 
class LocationSpec:
    """地理位置规格"""
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None

@dataclass
class RequirementSpec:
    """标准化需求规格"""
    product: str
    specifications: List[str] = field(default_factory=list)
    price_range: Optional[PriceRange] = None
    location: Optional[LocationSpec] = None
    company_size: str = "不限"  # 大型|中型|小型|不限
    priority_factors: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    missing_info: List[str] = field(default_factory=list)
    original_text: str = ""
    
    def to_dict(self):
        return asdict(self)

@dataclass
class SearchTask:
    """搜索任务"""
    task_id: str
    query_type: str  # general, linkedin, semantic
    keywords: str
    search_params: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class CompanyResult:
    """公司搜索结果"""
    name: str
    description: str = ""
    domain: str = ""
    linkedin_url: str = ""
    location: str = ""
    industry: str = ""
    source: str = ""  # 数据来源

@dataclass
class ScoredCompany:
    """评分后的公司结果"""
    company: CompanyResult
    overall_score: float
    dimension_scores: Dict[str, float]
    match_reasons: List[str]
    concerns: List[str]
    confidence_level: str = "medium"

@dataclass
class AgentEvent:
    """Agent事件"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    data: Any = None
    source_agent: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: str = ""  # 用于追踪工作流

@dataclass
class WorkflowResult:
    """工作流最终结果"""
    success: bool
    results: List[ScoredCompany] = field(default_factory=list)
    error_message: str = ""
    execution_time: float = 0.0
    workflow_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

# ======================== 消息总线 ========================

class MessageBus:
    """Agent间通信的消息总线"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.message_history: List[AgentEvent] = []
        self._lock = threading.Lock()
        
    def subscribe(self, event_type: str, callback: Callable[[AgentEvent], None]):
        """订阅特定类型的事件"""
        with self._lock:
            self.subscribers[event_type].append(callback)
            logger.info(f"Subscribed to event type: {event_type}")
    
    def unsubscribe(self, event_type: str, callback: Callable):
        """取消订阅"""
        with self._lock:
            if callback in self.subscribers[event_type]:
                self.subscribers[event_type].remove(callback)
    
    async def publish(self, event: AgentEvent):
        """发布事件到所有订阅者"""
        with self._lock:
            self.message_history.append(event)
            subscribers = self.subscribers.get(event.event_type, []).copy()
        
        logger.info(f"Publishing event: {event.event_type} from {event.source_agent}")
        
        # 异步通知所有订阅者
        for callback in subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")
    
    def get_history(self, event_type: Optional[str] = None) -> List[AgentEvent]:
        """获取事件历史"""
        if event_type:
            return [event for event in self.message_history if event.event_type == event_type]
        return self.message_history.copy()

# ======================== 工作流状态管理 ========================

class WorkflowState:
    """工作流状态管理器"""
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.current_phase = WorkflowPhase.INIT
        self.agent_states: Dict[str, AgentState] = {}
        self.intermediate_results: Dict[str, Any] = {}
        self.error_history: List[str] = []
        self.started_at = datetime.now()
        self.phase_history: List[tuple] = [(self.current_phase, self.started_at)]
        self._lock = threading.Lock()
    
    def transition_to(self, new_phase: WorkflowPhase):
        """切换到新的工作流阶段"""
        with self._lock:
            old_phase = self.current_phase
            self.current_phase = new_phase
            self.phase_history.append((new_phase, datetime.now()))
            logger.info(f"Workflow {self.workflow_id} transitioned from {old_phase} to {new_phase}")
    
    def update_agent_state(self, agent_id: str, state: AgentState):
        """更新Agent状态"""
        with self._lock:
            old_state = self.agent_states.get(agent_id, AgentState.IDLE)
            self.agent_states[agent_id] = state
            logger.info(f"Agent {agent_id} state: {old_state} -> {state}")
    
    def store_result(self, key: str, result: Any):
        """存储中间结果"""
        with self._lock:
            self.intermediate_results[key] = result
            logger.info(f"Stored intermediate result: {key}")
    
    def get_result(self, key: str) -> Any:
        """获取中间结果"""
        return self.intermediate_results.get(key)
    
    def add_error(self, error: str):
        """添加错误记录"""
        with self._lock:
            self.error_history.append(f"[{datetime.now()}] {error}")
            logger.error(f"Workflow error: {error}")
    
    def get_execution_time(self) -> float:
        """获取执行时间（秒）"""
        return (datetime.now() - self.started_at).total_seconds()
    
    def is_complete(self) -> bool:
        """检查工作流是否完成"""
        return self.current_phase in [WorkflowPhase.COMPLETED, WorkflowPhase.ERROR]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'workflow_id': self.workflow_id,
            'current_phase': self.current_phase.value,
            'agent_states': {k: v.value for k, v in self.agent_states.items()},
            'execution_time': self.get_execution_time(),
            'error_count': len(self.error_history),
            'is_complete': self.is_complete()
        }

# ======================== Agent基础类 ========================

class BaseAgent(ABC):
    """Agent基础抽象类"""
    
    def __init__(self, agent_id: str, message_bus: MessageBus):
        self.agent_id = agent_id
        self.message_bus = message_bus
        self.state = AgentState.IDLE
        self.capabilities: Set[str] = set()
        self.processing_stats = {
            'total_processed': 0,
            'success_count': 0,
            'error_count': 0,
            'avg_processing_time': 0.0
        }
        
        # 注册事件处理器
        self._register_event_handlers()
        
        logger.info(f"Agent {self.agent_id} initialized")
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        self.message_bus.subscribe(f"{self.agent_id}_task", self._handle_task_event)
        self.message_bus.subscribe("workflow_phase_change", self._handle_phase_change)
    
    async def _handle_task_event(self, event: AgentEvent):
        """处理任务事件"""
        try:
            self.state = AgentState.PROCESSING
            result = await self.process(event.data)
            
            # 发送完成事件
            completion_event = AgentEvent(
                event_type=f"{self.agent_id}_completed",
                data=result,
                source_agent=self.agent_id,
                correlation_id=event.correlation_id
            )
            await self.message_bus.publish(completion_event)
            
            self.state = AgentState.COMPLETED
            self.processing_stats['success_count'] += 1
            
        except Exception as e:
            self.state = AgentState.ERROR
            self.processing_stats['error_count'] += 1
            
            error_event = AgentEvent(
                event_type=f"{self.agent_id}_error",
                data=str(e),
                source_agent=self.agent_id,
                correlation_id=event.correlation_id
            )
            await self.message_bus.publish(error_event)
            
            logger.error(f"Agent {self.agent_id} error: {e}")
        finally:
            self.processing_stats['total_processed'] += 1
    
    async def _handle_phase_change(self, event: AgentEvent):
        """处理工作流阶段变更事件"""
        phase = event.data
        logger.info(f"Agent {self.agent_id} received phase change: {phase}")
    
    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """处理核心逻辑，子类必须实现"""
        pass
    
    async def emit_event(self, event_type: str, data: Any, correlation_id: str = ""):
        """发送事件"""
        event = AgentEvent(
            event_type=event_type,
            data=data,
            source_agent=self.agent_id,
            correlation_id=correlation_id
        )
        await self.message_bus.publish(event)
    
    def add_capability(self, capability: str):
        """添加能力标签"""
        self.capabilities.add(capability)
    
    def has_capability(self, capability: str) -> bool:
        """检查是否具备某种能力"""
        return capability in self.capabilities
    
    def get_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        return {
            'agent_id': self.agent_id,
            'state': self.state.value,
            'capabilities': list(self.capabilities),
            **self.processing_stats
        }

# ======================== Agent注册中心 ========================

class AgentRegistry:
    """Agent注册中心"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self._lock = threading.Lock()
    
    def register(self, agent: BaseAgent):
        """注册Agent"""
        with self._lock:
            self.agents[agent.agent_id] = agent
            logger.info(f"Registered agent: {agent.agent_id}")
    
    def unregister(self, agent_id: str):
        """注销Agent"""
        with self._lock:
            if agent_id in self.agents:
                del self.agents[agent_id]
                logger.info(f"Unregistered agent: {agent_id}")
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """获取Agent实例"""
        return self.agents.get(agent_id)
    
    def find_agents_by_capability(self, capability: str) -> List[BaseAgent]:
        """根据能力查找Agent"""
        return [agent for agent in self.agents.values() 
                if agent.has_capability(capability)]
    
    def get_all_agents(self) -> List[BaseAgent]:
        """获取所有Agent"""
        return list(self.agents.values())
    
    def get_agent_stats(self) -> List[Dict[str, Any]]:
        """获取所有Agent的统计信息"""
        return [agent.get_stats() for agent in self.agents.values()]

# ======================== 工具函数 ========================

def create_correlation_id() -> str:
    """创建关联ID用于追踪工作流"""
    return str(uuid.uuid4())

def validate_requirement_spec(spec: RequirementSpec) -> List[str]:
    """验证需求规格，返回验证错误列表"""
    errors = []
    
    if not spec.product or spec.product.strip() == "":
        errors.append("产品名称不能为空")
    
    if spec.price_range:
        if spec.price_range.min is not None and spec.price_range.max is not None:
            if spec.price_range.min > spec.price_range.max:
                errors.append("价格区间最小值不能大于最大值")
    
    if spec.confidence_score < 0 or spec.confidence_score > 1:
        errors.append("置信度得分必须在0-1之间")
    
    return errors

def format_company_results(companies: List[ScoredCompany]) -> Dict[str, Any]:
    """格式化公司结果为前端友好格式"""
    return {
        'total_count': len(companies),
        'companies': [
            {
                'name': company.company.name,
                'description': company.company.description,
                'score': company.overall_score,
                'match_reasons': company.match_reasons,
                'concerns': company.concerns,
                'domain': company.company.domain,
                'location': company.company.location
            }
            for company in companies
        ],
        'generated_at': datetime.now().isoformat()
    }

# ======================== 导出接口 ========================

__all__ = [
    # 枚举
    'WorkflowPhase', 'AgentState',
    # 数据结构
    'RequirementSpec', 'SearchTask', 'CompanyResult', 'ScoredCompany',
    'AgentEvent', 'WorkflowResult', 'PriceRange', 'LocationSpec',
    # 核心组件
    'MessageBus', 'WorkflowState', 'BaseAgent', 'AgentRegistry',
    # 工具函数
    'create_correlation_id', 'validate_requirement_spec', 'format_company_results'
]

if __name__ == "__main__":
    # 基础框架测试
    async def test_framework():
        print("🧪 测试多智能体基础框架...")
        
        # 创建消息总线
        message_bus = MessageBus()
        
        # 创建工作流状态
        workflow_state = WorkflowState("test_workflow")
        
        # 创建Agent注册中心
        registry = AgentRegistry()
        
        print("✅ 基础组件初始化成功")
        print(f"📊 工作流状态: {workflow_state.to_dict()}")
        
        # 测试事件发布
        test_event = AgentEvent(
            event_type="test_event",
            data="Hello Multi-Agent World!",
            source_agent="test_agent"
        )
        
        event_received = False
        
        def test_callback(event: AgentEvent):
            nonlocal event_received
            event_received = True
            print(f"📨 收到事件: {event.event_type} - {event.data}")
        
        message_bus.subscribe("test_event", test_callback)
        await message_bus.publish(test_event)
        
        # 验证事件传递
        await asyncio.sleep(0.1)  # 等待异步处理
        assert event_received, "事件传递失败"
        
        print("✅ 事件系统测试通过")
        print("🎉 多智能体基础框架测试完成！")
    
    asyncio.run(test_framework())