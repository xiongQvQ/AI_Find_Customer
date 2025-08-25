"""
LangGraph搜索系统核心状态定义
支持意图识别、公司搜索、AI评估和员工搜索的完整工作流
"""

from typing import Dict, List, Any, Optional, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from datetime import datetime

# 搜索意图枚举
SearchIntent = Literal["company", "employee", "composite", "unknown"]

# 搜索参数
class SearchParams(BaseModel):
    """搜索参数配置"""
    # 通用参数
    query: str = Field(description="搜索查询")
    region: str = Field(default="", description="地区限制")
    gl: str = Field(default="us", description="Google搜索地理位置")
    
    # 公司搜索参数
    industry: str = Field(default="", description="行业关键词")
    company_size: Optional[str] = Field(default=None, description="公司规模")
    
    # 员工搜索参数  
    position: str = Field(default="", description="职位关键词")
    seniority_level: Optional[str] = Field(default=None, description="职级")
    department: Optional[str] = Field(default=None, description="部门")
    
    # 搜索配置
    max_results: int = Field(default=50, description="最大结果数")
    search_type: Literal["general", "linkedin"] = Field(default="general", description="搜索类型")
    use_custom_query: bool = Field(default=False, description="是否使用自定义查询")

class CompanyInfo(BaseModel):
    """公司信息结构"""
    name: str = Field(description="公司名称")
    domain: Optional[str] = Field(default=None, description="公司域名")
    industry: Optional[str] = Field(default=None, description="所属行业")
    size: Optional[str] = Field(default=None, description="公司规模")
    location: Optional[str] = Field(default=None, description="公司地址")
    description: Optional[str] = Field(default=None, description="公司描述")
    linkedin_url: Optional[str] = Field(default=None, description="LinkedIn链接")
    website_url: Optional[str] = Field(default=None, description="官网链接")
    
    # AI评估结果
    ai_score: Optional[float] = Field(default=None, description="AI评分(0-100)")
    ai_reason: Optional[str] = Field(default=None, description="评分原因")
    is_qualified: Optional[bool] = Field(default=None, description="是否符合条件")

class EmployeeInfo(BaseModel):
    """员工信息结构"""
    name: str = Field(description="员工姓名")
    position: Optional[str] = Field(default=None, description="职位")
    company: str = Field(description="所属公司")
    linkedin_url: Optional[str] = Field(default=None, description="LinkedIn链接")
    location: Optional[str] = Field(default=None, description="工作地点")
    description: Optional[str] = Field(default=None, description="个人描述")
    
    # AI评估结果
    ai_score: Optional[float] = Field(default=None, description="AI评分(0-100)")
    ai_reason: Optional[str] = Field(default=None, description="评分原因")
    is_qualified: Optional[bool] = Field(default=None, description="是否符合条件")

class SearchResult(TypedDict):
    """搜索结果汇总"""
    companies: List[Dict[str, Any]]  # 改为字典类型以兼容LangGraph序列化
    employees: List[Dict[str, Any]]  # 改为字典类型以兼容LangGraph序列化
    qualified_companies: List[Dict[str, Any]]  # 改为字典类型以兼容LangGraph序列化
    qualified_employees: List[Dict[str, Any]]  # 改为字典类型以兼容LangGraph序列化
    
    # 统计信息
    total_companies_found: int
    total_employees_found: int
    qualified_companies_count: int
    qualified_employees_count: int

class SearchState(TypedDict):
    """
    LangGraph工作流的核心状态
    包含意图识别、搜索执行、AI评估的完整流程状态
    """
    # === 基础信息 ===
    session_id: str  # 会话ID
    timestamp: str   # 创建时间戳
    
    # === 用户输入 ===
    user_query: str              # 用户原始查询
    search_params: SearchParams  # 解析后的搜索参数
    
    # === 意图识别 ===
    detected_intent: SearchIntent  # 识别的搜索意图
    intent_confidence: float       # 意图识别置信度(0-1)
    intent_reasoning: str          # 意图识别推理过程
    
    # === 路由决策 ===
    workflow_path: List[str]       # 工作流路径记录
    current_node: str              # 当前执行节点
    next_nodes: List[str]          # 下一步节点列表
    
    # === 搜索执行状态 ===
    company_search_completed: bool   # 公司搜索完成标志
    employee_search_completed: bool  # 员工搜索完成标志
    ai_evaluation_completed: bool    # AI评估完成标志
    
    # === 搜索结果 ===
    search_results: SearchResult     # 所有搜索结果
    
    # === AI评估配置 ===
    ai_evaluation_enabled: bool      # 是否启用AI评估
    evaluation_criteria: Dict[str, Any]  # 评估标准
    
    # === 错误处理 ===
    errors: List[Dict[str, Any]]     # 错误记录
    warnings: List[Dict[str, Any]]   # 警告记录
    
    # === 执行元数据 ===
    execution_time: float            # 执行耗时(秒)
    api_calls_count: int            # API调用次数
    tokens_used: int                # 使用的token数
    
    # === 输出配置 ===
    output_format: Literal["csv", "json", "both"]  # 输出格式
    output_files: List[str]         # 生成的输出文件路径

def create_initial_state(
    user_query: str,
    search_params: Optional[SearchParams] = None,
    session_id: Optional[str] = None
) -> SearchState:
    """
    创建初始搜索状态
    
    Args:
        user_query: 用户查询
        search_params: 搜索参数配置
        session_id: 会话ID
        
    Returns:
        初始化的SearchState
    """
    if session_id is None:
        session_id = f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if search_params is None:
        search_params = SearchParams(query=user_query)
    
    return SearchState(
        # 基础信息
        session_id=session_id,
        timestamp=datetime.now().isoformat(),
        
        # 用户输入
        user_query=user_query,
        search_params=search_params,
        
        # 意图识别 - 初始化为unknown
        detected_intent="unknown",
        intent_confidence=0.0,
        intent_reasoning="",
        
        # 路由决策
        workflow_path=["start"],
        current_node="intent_recognition",
        next_nodes=["intent_recognition"],
        
        # 搜索执行状态
        company_search_completed=False,
        employee_search_completed=False,
        ai_evaluation_completed=False,
        
        # 搜索结果
        search_results=SearchResult(
            companies=[],
            employees=[],
            qualified_companies=[],
            qualified_employees=[],
            total_companies_found=0,
            total_employees_found=0,
            qualified_companies_count=0,
            qualified_employees_count=0
        ),
        
        # AI评估配置
        ai_evaluation_enabled=True,
        evaluation_criteria={},
        
        # 错误处理
        errors=[],
        warnings=[],
        
        # 执行元数据
        execution_time=0.0,
        api_calls_count=0,
        tokens_used=0,
        
        # 输出配置
        output_format="csv",
        output_files=[]
    )

def update_state_with_intent(
    state: SearchState,
    intent: SearchIntent,
    confidence: float,
    reasoning: str
) -> SearchState:
    """
    更新状态的意图识别结果
    
    Args:
        state: 当前状态
        intent: 识别的意图
        confidence: 置信度
        reasoning: 推理过程
        
    Returns:
        更新后的状态
    """
    state["detected_intent"] = intent
    state["intent_confidence"] = confidence
    state["intent_reasoning"] = reasoning
    state["workflow_path"].append("intent_recognition")
    
    # 根据意图决定下一步节点
    if intent == "company":
        state["next_nodes"] = ["company_search"]
    elif intent == "employee":
        state["next_nodes"] = ["company_search"]  # 员工搜索也需要先搜索公司
    elif intent == "composite":
        state["next_nodes"] = ["company_search"]
    else:
        state["next_nodes"] = ["clarification"]  # 需要澄清意图
        
    return state

def add_error_to_state(
    state: SearchState,
    error_type: str,
    error_message: str,
    node_name: str
) -> SearchState:
    """
    向状态添加错误记录
    
    Args:
        state: 当前状态
        error_type: 错误类型
        error_message: 错误消息
        node_name: 发生错误的节点名称
        
    Returns:
        更新后的状态
    """
    error_record = {
        "type": error_type,
        "message": error_message,
        "node": node_name,
        "timestamp": datetime.now().isoformat()
    }
    state["errors"].append(error_record)
    return state

def add_warning_to_state(
    state: SearchState,
    warning_type: str,
    warning_message: str,
    node_name: str
) -> SearchState:
    """
    向状态添加警告记录
    
    Args:
        state: 当前状态
        warning_type: 警告类型
        warning_message: 警告消息
        node_name: 发生警告的节点名称
        
    Returns:
        更新后的状态
    """
    warning_record = {
        "type": warning_type,
        "message": warning_message,
        "node": node_name,
        "timestamp": datetime.now().isoformat()
    }
    state["warnings"].append(warning_record)
    return state