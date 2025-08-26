"""
服务层模块
提供业务逻辑处理服务
"""
from .company_service import get_company_service, CompanySearchService
from .employee_service import get_employee_service, EmployeeSearchService
from .intelligent_service import get_intelligent_service, IntelligentSearchService

__all__ = [
    "get_company_service",
    "CompanySearchService",
    "get_employee_service", 
    "EmployeeSearchService",
    "get_intelligent_service",
    "IntelligentSearchService"
]