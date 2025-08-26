"""
API请求数据模型
定义各个模块的请求参数结构
"""
from typing import List, Optional
from pydantic import BaseModel, Field


# ============ 公司搜索模块 ============

class CompanySearchRequest(BaseModel):
    """公司搜索请求模型"""
    industry: Optional[str] = Field(None, description="行业关键词")
    region: Optional[str] = Field(None, description="地区关键词") 
    search_type: str = Field("linkedin", description="搜索类型: general | linkedin")
    country_code: str = Field("us", description="国家代码: us | cn | uk | de | jp等")
    max_results: int = Field(30, description="最大结果数量", ge=1, le=100)
    custom_query: Optional[str] = Field(None, description="自定义搜索查询")
    keywords: Optional[List[str]] = Field(None, description="额外关键词列表")
    use_llm_optimization: bool = Field(True, description="是否使用LLM优化关键词")


# ============ 员工搜索模块 ============

class EmployeeSearchRequest(BaseModel):
    """员工搜索请求模型"""
    company_name: str = Field(..., description="目标公司名称")
    company_domain: Optional[str] = Field(None, description="公司域名（可选）")
    target_positions: List[str] = Field(..., description="目标职位列表", min_items=1)
    country_code: str = Field("us", description="国家代码")
    max_results: int = Field(20, description="最大结果数量", ge=1, le=50)
    search_options: List[str] = Field(
        ["linkedin", "email"], 
        description="搜索选项: linkedin | email | phone"
    )
    verify_emails: bool = Field(False, description="是否验证邮箱")


# ============ 智能搜索模块 ============

class IntelligentSearchRequest(BaseModel):
    """智能搜索请求模型"""
    query: str = Field(..., description="自然语言搜索查询", min_length=5)
    search_scope: str = Field("comprehensive", description="搜索范围: company_only | employee_only | comprehensive")
    ai_evaluation: bool = Field(True, description="是否启用AI评估和过滤")
    max_companies: int = Field(30, description="最大公司数量", ge=1, le=100)
    max_employees_per_company: int = Field(5, description="每个公司最大员工数量", ge=1, le=20)
    preferred_strategy: Optional[str] = Field(None, description="首选策略: company_first | employee_first | balanced | adaptive")
    enable_optimization: bool = Field(True, description="启用搜索优化")


# ============ 批量处理模块 ============

class BatchCompanySearchRequest(BaseModel):
    """批量公司搜索请求模型"""
    search_queries: List[CompanySearchRequest] = Field(..., description="批量搜索查询列表", min_items=1)
    parallel_processing: bool = Field(True, description="是否并行处理")
    merge_results: bool = Field(True, description="是否合并结果")


class BatchEmployeeSearchRequest(BaseModel):
    """批量员工搜索请求模型"""
    companies: List[str] = Field(..., description="公司名称列表", min_items=1)
    target_positions: List[str] = Field(..., description="目标职位列表", min_items=1)
    country_code: str = Field("us", description="国家代码")
    search_options: List[str] = Field(["linkedin", "email"], description="搜索选项")


# ============ 配置和设置 ============

class SearchConfigRequest(BaseModel):
    """搜索配置请求模型"""
    llm_provider: str = Field("none", description="LLM提供商: none | openai | anthropic | google | huoshan")
    timeout_seconds: int = Field(30, description="搜索超时时间（秒）", ge=5, le=300)
    rate_limit: int = Field(10, description="API限流（请求/分钟）", ge=1, le=100)
    enable_caching: bool = Field(True, description="启用结果缓存")
    cache_ttl_minutes: int = Field(60, description="缓存有效时间（分钟）", ge=5, le=1440)