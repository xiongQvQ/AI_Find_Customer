"""
员工搜索服务层
专门处理员工搜索相关的业务逻辑
"""
import os
import time
import random
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models.requests import EmployeeSearchRequest
from ..models.responses import EmployeeInfo, EmployeeSearchResponse

logger = logging.getLogger(__name__)


class EmployeeSearchService:
    """员工搜索服务类"""
    
    def __init__(self):
        """初始化员工搜索服务"""
        self.search_engine_available = bool(os.getenv("SERPER_API_KEY"))
        logger.info(f"员工搜索服务初始化: API可用={self.search_engine_available}")
    
    async def search_employees(self, request: EmployeeSearchRequest) -> EmployeeSearchResponse:
        """
        搜索公司员工信息
        
        Args:
            request: 员工搜索请求
            
        Returns:
            EmployeeSearchResponse: 搜索结果
        """
        search_id = f"employee_search_{int(time.time())}"
        start_time = time.time()
        
        try:
            # 验证请求参数
            self._validate_request(request)
            
            logger.info(f"开始员工搜索: {search_id}")
            logger.info(f"目标公司: {request.company_name}, 职位: {request.target_positions}")
            
            # 执行员工搜索
            employees = await self._execute_employee_search(request)
            
            execution_time = time.time() - start_time
            
            # 统计验证联系方式数量
            verified_contacts = sum(
                1 for emp in employees 
                if emp.email_verified == "verified"
            )
            
            return EmployeeSearchResponse(
                success=True,
                message=f"搜索完成，找到 {len(employees)} 名员工",
                search_id=search_id,
                company_name=request.company_name,
                total_found=len(employees),
                verified_contacts=verified_contacts,
                employees=employees,
                execution_time=execution_time,
                search_params={
                    "company_name": request.company_name,
                    "company_domain": request.company_domain,
                    "target_positions": request.target_positions,
                    "country_code": request.country_code,
                    "search_options": request.search_options
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"员工搜索异常: {str(e)}")
            
            return EmployeeSearchResponse(
                success=False,
                message="员工搜索失败",
                search_id=search_id,
                company_name=request.company_name,
                total_found=0,
                verified_contacts=0,
                employees=[],
                execution_time=execution_time,
                error=str(e)
            )
    
    async def _execute_employee_search(self, request: EmployeeSearchRequest) -> List[EmployeeInfo]:
        """执行员工搜索的核心逻辑"""
        
        if not self.search_engine_available:
            # 没有搜索引擎API时使用模拟数据
            return self._generate_mock_employees(request)
        
        # TODO: 实现真实的员工搜索逻辑
        # 这里应该调用实际的搜索引擎API
        # 目前使用模拟数据
        await self._simulate_search_delay()
        return self._generate_mock_employees(request)
    
    async def _simulate_search_delay(self):
        """模拟搜索延迟"""
        import asyncio
        await asyncio.sleep(random.uniform(1.0, 3.0))
    
    def _generate_mock_employees(self, request: EmployeeSearchRequest) -> List[EmployeeInfo]:
        """生成模拟员工数据"""
        employees = []
        
        # 根据不同国家生成不同的姓名
        names_by_country = {
            "us": ["John Smith", "Sarah Johnson", "Michael Brown", "Lisa Davis", "David Wilson"],
            "cn": ["张伟", "李娜", "王强", "刘敏", "陈杰"],
            "uk": ["James Wilson", "Emma Thompson", "Oliver Davies", "Sophie Clarke", "Harry Evans"],
            "de": ["Hans Mueller", "Anna Schmidt", "Klaus Wagner", "Eva Fischer", "Thomas Weber"],
            "jp": ["田中太郎", "佐藤花子", "鈴木一郎", "高橋美里", "渡辺健太"]
        }
        
        names = names_by_country.get(request.country_code, names_by_country["us"])
        
        # 生成员工数据
        num_employees = min(random.randint(2, 8), request.max_results)
        
        for i in range(num_employees):
            name = random.choice(names)
            position = random.choice(request.target_positions)
            
            # 生成邮箱（如果请求包含email选项）
            email = None
            email_verified = "unknown"
            if "email" in request.search_options:
                domain = request.company_domain or f"{request.company_name.lower().replace(' ', '')}.com"
                email = f"{name.lower().replace(' ', '.')}@{domain}"
                email_verified = random.choice(["verified", "unverified", "verified"])
            
            # 生成电话（如果请求包含phone选项）
            phone = None
            if "phone" in request.search_options:
                if request.country_code == "us":
                    phone = f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
                elif request.country_code == "cn":
                    phone = f"+86-138{random.randint(10000000, 99999999)}"
                else:
                    phone = f"+{random.randint(1, 999)}-{random.randint(100000000, 999999999)}"
            
            # 生成LinkedIn（如果请求包含linkedin选项）
            linkedin_url = None
            if "linkedin" in request.search_options:
                linkedin_id = name.lower().replace(' ', '-')
                linkedin_url = f"https://linkedin.com/in/{linkedin_id}-{random.randint(100, 999)}"
            
            employee = EmployeeInfo(
                name=name,
                position=position,
                company=request.company_name,
                linkedin_url=linkedin_url,
                email=email,
                phone=phone,
                location=self._get_location_by_country(request.country_code),
                summary=f"在{request.company_name}担任{position}，有{random.randint(2, 10)}年相关工作经验。",
                experience_years=random.randint(2, 15),
                confidence_score=random.uniform(0.6, 0.95),
                email_verified=email_verified,
                source="linkedin_search"
            )
            
            employees.append(employee)
        
        # 按置信度排序
        employees.sort(key=lambda x: x.confidence_score or 0, reverse=True)
        
        return employees
    
    def _get_location_by_country(self, country_code: str) -> str:
        """根据国家代码返回典型位置"""
        locations = {
            "us": "San Francisco, CA",
            "cn": "北京市",
            "uk": "London, UK",
            "de": "Berlin, Germany", 
            "jp": "Tokyo, Japan",
            "sg": "Singapore",
            "au": "Sydney, Australia",
            "ca": "Toronto, Canada",
            "tw": "台北市"
        }
        return locations.get(country_code, "Unknown Location")
    
    def _validate_request(self, request: EmployeeSearchRequest):
        """验证员工搜索请求参数"""
        if not request.company_name.strip():
            raise ValueError("公司名称不能为空")
        
        if not request.target_positions:
            raise ValueError("必须指定至少一个目标职位")
        
        if request.max_results < 1 or request.max_results > 50:
            raise ValueError("结果数量必须在1-50之间")
        
        valid_options = {"linkedin", "email", "phone"}
        if not all(option in valid_options for option in request.search_options):
            raise ValueError(f"无效的搜索选项，支持的选项: {valid_options}")
    
    async def verify_company_domain(self, company_name: str) -> Optional[str]:
        """验证并获取公司域名"""
        # TODO: 实现公司域名验证逻辑
        # 这里可以集成网站验证器或搜索引擎查询
        
        # 简单的模拟实现
        mock_domains = {
            "tesla": "tesla.com",
            "microsoft": "microsoft.com", 
            "google": "google.com",
            "apple": "apple.com",
            "amazon": "amazon.com"
        }
        
        company_lower = company_name.lower()
        for key, domain in mock_domains.items():
            if key in company_lower:
                return domain
        
        return None
    
    async def get_position_suggestions(self, partial_position: str) -> List[str]:
        """获取职位建议"""
        common_positions = [
            "CEO", "CTO", "COO", "CFO", "VP",
            "销售经理", "市场经理", "产品经理", "技术经理",
            "Sales Manager", "Marketing Manager", "Product Manager",
            "Software Engineer", "Data Scientist", "Business Development"
        ]
        
        if not partial_position:
            return common_positions[:10]
        
        partial_lower = partial_position.lower()
        suggestions = [
            pos for pos in common_positions 
            if partial_lower in pos.lower()
        ]
        
        return suggestions[:10]


# 全局服务实例
_employee_service = None

def get_employee_service() -> EmployeeSearchService:
    """获取员工搜索服务实例"""
    global _employee_service
    if _employee_service is None:
        _employee_service = EmployeeSearchService()
    return _employee_service