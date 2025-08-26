"""
数据模型模块
提供API请求和响应的数据结构定义
"""
from .requests import (
    CompanySearchRequest,
    EmployeeSearchRequest, 
    IntelligentSearchRequest,
    BatchCompanySearchRequest,
    BatchEmployeeSearchRequest,
    SearchConfigRequest
)

from .responses import (
    BaseResponse,
    HealthResponse,
    CompanyInfo,
    CompanySearchResponse,
    EmployeeInfo,
    EmployeeSearchResponse,
    SearchInsight,
    IntelligentSearchResult,
    IntelligentSearchResponse,
    BatchSearchResponse,
    ConfigResponse,
    ExportResponse
)

__all__ = [
    # 请求模型
    "CompanySearchRequest",
    "EmployeeSearchRequest",
    "IntelligentSearchRequest", 
    "BatchCompanySearchRequest",
    "BatchEmployeeSearchRequest",
    "SearchConfigRequest",
    
    # 响应模型
    "BaseResponse",
    "HealthResponse",
    "CompanyInfo",
    "CompanySearchResponse",
    "EmployeeInfo", 
    "EmployeeSearchResponse",
    "SearchInsight",
    "IntelligentSearchResult",
    "IntelligentSearchResponse",
    "BatchSearchResponse",
    "ConfigResponse",
    "ExportResponse"
]