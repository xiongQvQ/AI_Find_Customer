"""
API响应数据模型
定义各个模块的响应数据结构
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ============ 基础响应模型 ============

class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = Field(..., description="请求是否成功")
    message: str = Field(..., description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")
    execution_time: Optional[float] = Field(None, description="执行时间（秒）")
    error: Optional[str] = Field(None, description="错误信息")


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    timestamp: datetime = Field(..., description="检查时间")
    environment: Dict[str, Any] = Field(..., description="环境变量状态")
    modules: Dict[str, str] = Field(..., description="模块状态")


# ============ 公司数据模型 ============

class CompanyInfo(BaseModel):
    """公司信息模型"""
    name: str = Field(..., description="公司名称")
    domain: Optional[str] = Field(None, description="公司域名")
    website_url: Optional[str] = Field(None, description="官方网站")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn公司页面")
    industry: Optional[str] = Field(None, description="所属行业")
    location: Optional[str] = Field(None, description="地理位置")
    description: Optional[str] = Field(None, description="公司描述")
    employee_count: Optional[str] = Field(None, description="员工规模")
    founded_year: Optional[str] = Field(None, description="成立年份")
    confidence_score: Optional[float] = Field(None, description="匹配置信度", ge=0, le=1)
    source: str = Field(..., description="数据来源")
    search_query: Optional[str] = Field(None, description="使用的搜索查询")
    
    # AI分析字段
    is_company: Optional[bool] = Field(None, description="是否为真实公司")
    ai_score: Optional[float] = Field(None, description="AI综合评分", ge=0, le=1)
    ai_reason: Optional[str] = Field(None, description="AI分析理由")
    relevance_score: Optional[float] = Field(None, description="与搜索条件的相关性", ge=0, le=1)
    analysis_confidence: Optional[float] = Field(None, description="分析置信度", ge=0, le=1)


class CompanySearchResponse(BaseResponse):
    """公司搜索响应模型"""
    search_id: str = Field(..., description="搜索ID")
    total_found: int = Field(..., description="找到的公司总数")
    companies: List[CompanyInfo] = Field(default=[], description="公司信息列表")
    search_params: Dict[str, Any] = Field(default={}, description="搜索参数")
    optimization_info: Optional[Dict[str, Any]] = Field(None, description="LLM优化信息")


# ============ 员工数据模型 ============

class EmployeeInfo(BaseModel):
    """员工信息模型"""
    name: str = Field(..., description="员工姓名")
    position: str = Field(..., description="职位")
    company: str = Field(..., description="所在公司")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn个人资料")
    email: Optional[str] = Field(None, description="电子邮箱")
    phone: Optional[str] = Field(None, description="电话号码")
    location: Optional[str] = Field(None, description="地理位置")
    summary: Optional[str] = Field(None, description="个人简介")
    experience_years: Optional[int] = Field(None, description="工作经验年数")
    confidence_score: Optional[float] = Field(None, description="匹配置信度", ge=0, le=1)
    email_verified: Optional[str] = Field(None, description="邮箱验证状态: verified | unverified | unknown")
    source: str = Field(..., description="数据来源")


class EmployeeSearchResponse(BaseResponse):
    """员工搜索响应模型"""
    search_id: str = Field(..., description="搜索ID")
    company_name: str = Field(..., description="目标公司名称")
    total_found: int = Field(..., description="找到的员工总数")
    verified_contacts: int = Field(0, description="已验证联系方式数量")
    employees: List[EmployeeInfo] = Field(default=[], description="员工信息列表")
    search_params: Dict[str, Any] = Field(default={}, description="搜索参数")


# ============ 智能搜索数据模型 ============

class SearchInsight(BaseModel):
    """搜索洞察模型"""
    query_analysis: str = Field(..., description="查询分析结果")
    search_strategy: str = Field(..., description="使用的搜索策略")
    optimization_applied: List[str] = Field(default=[], description="应用的优化措施")
    confidence_level: str = Field(..., description="结果置信度级别: low | medium | high")
    suggestions: List[str] = Field(default=[], description="改进建议")


class IntelligentSearchResult(BaseModel):
    """智能搜索结果模型"""
    companies: List[CompanyInfo] = Field(default=[], description="找到的公司")
    employees: List[EmployeeInfo] = Field(default=[], description="找到的员工")
    total_companies: int = Field(0, description="公司总数")
    total_employees: int = Field(0, description="员工总数")
    search_insights: SearchInsight = Field(..., description="搜索洞察")


class IntelligentSearchResponse(BaseResponse):
    """智能搜索响应模型"""
    search_id: str = Field(..., description="搜索ID")
    original_query: str = Field(..., description="原始查询")
    processed_query: str = Field(..., description="处理后的查询")
    results: IntelligentSearchResult = Field(..., description="搜索结果")
    performance_metrics: Dict[str, Any] = Field(default={}, description="性能指标")


# ============ 批量处理响应模型 ============

class BatchSearchResponse(BaseResponse):
    """批量搜索响应模型"""
    batch_id: str = Field(..., description="批量处理ID")
    total_queries: int = Field(..., description="总查询数量")
    completed_queries: int = Field(..., description="完成查询数量")
    failed_queries: int = Field(..., description="失败查询数量")
    results: List[Dict[str, Any]] = Field(default=[], description="批量结果列表")
    summary: Dict[str, Any] = Field(default={}, description="批量处理摘要")


# ============ 配置响应模型 ============

class ConfigResponse(BaseResponse):
    """配置响应模型"""
    current_config: Dict[str, Any] = Field(..., description="当前配置")
    available_options: Dict[str, List[str]] = Field(..., description="可用选项")


# ============ 文件导出响应模型 ============

class ExportResponse(BaseResponse):
    """文件导出响应模型"""
    file_path: str = Field(..., description="导出文件路径")
    file_format: str = Field(..., description="文件格式: csv | json | xlsx")
    file_size: int = Field(..., description="文件大小（字节）")
    download_url: Optional[str] = Field(None, description="下载链接")
    expires_at: Optional[datetime] = Field(None, description="链接过期时间")