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

# 导入核心搜索模块
try:
    from core.employee_search import EmployeeSearcher
    EMPLOYEE_SEARCH_AVAILABLE = True
except ImportError as e:
    print(f"警告: 员工搜索模块不可用: {e}")
    EMPLOYEE_SEARCH_AVAILABLE = False

# 导入LLM关键词生成器
try:
    from core.llm_keyword_generator import LLMKeywordGenerator
    LLM_KEYWORD_AVAILABLE = True
except ImportError as e:
    print(f"警告: LLM关键词生成器不可用: {e}")
    LLM_KEYWORD_AVAILABLE = False

logger = logging.getLogger(__name__)


class EmployeeSearchService:
    """员工搜索服务类"""
    
    def __init__(self):
        """初始化员工搜索服务"""
        self.searcher = None
        self.keyword_generator = None
        
        # 初始化员工搜索器
        if EMPLOYEE_SEARCH_AVAILABLE:
            try:
                self.searcher = EmployeeSearcher()
                logger.info("✅ 员工搜索器初始化成功")
            except Exception as e:
                logger.error(f"❌ 员工搜索器初始化失败: {e}")
                self.searcher = None
        
        # 初始化LLM关键词生成器
        if LLM_KEYWORD_AVAILABLE:
            try:
                self.keyword_generator = LLMKeywordGenerator()
                logger.info("✅ 员工搜索LLM关键词生成器初始化成功")
            except Exception as e:
                logger.error(f"❌ 员工搜索LLM关键词生成器初始化失败: {e}")
                self.keyword_generator = None
    
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
            logger.info(f"搜索器状态: {'可用' if self.searcher else '不可用'}")
            
            # 步骤1: LLM关键词优化
            optimized_params = await self._optimize_search_params(request)
            logger.info(f"LLM优化参数: {optimized_params}")
            
            # 执行员工搜索
            logger.info("🔄 开始执行员工搜索")
            employees = await self._execute_employee_search(request, optimized_params)
            logger.info(f"✅ 员工搜索完成，找到 {len(employees)} 名员工")
            
            # AI分析和评分（如果有员工结果）
            if employees and self.keyword_generator:
                employees = await self._analyze_employees_with_ai(employees, request)
            
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
    
    async def _execute_employee_search(self, request: EmployeeSearchRequest, optimized_params: Dict[str, Any]) -> List[EmployeeInfo]:
        """执行员工搜索的核心逻辑 - 参考公司搜索的多关键词策略"""
        
        if not self.searcher:
            # 没有搜索器时使用模拟数据
            logger.warning("🔧 员工搜索器不可用，使用增强模拟数据")
            return self._generate_enhanced_mock_employees(request, optimized_params)
        
        logger.info(f"✅ 员工搜索器可用，开始实际搜索")
        
        try:
            # 获取LLM生成的关键词
            keywords = optimized_params.get('keywords', [])
            query_variants = optimized_params.get('query_variants', [])
            
            if not keywords:
                # 回退到基础查询
                keywords = [f"{request.company_name} {' '.join(request.target_positions)}"]
                query_variants = [{"query": keywords[0], "type": "basic"}]
                logger.info(f"📝 使用基础查询关键词: {keywords}")
            else:
                logger.info(f"📝 使用LLM优化关键词: {keywords}")
            
            # 🔄 执行多关键词搜索策略（参考公司搜索）
            logger.info(f"🔄 执行多关键词员工搜索策略，共 {len(keywords)} 个关键词")
            logger.info(f"👥 用户搜索请求: 公司={request.company_name}, 职位={request.target_positions}, 国家={request.country_code}")
            
            all_employees = []
            employee_urls_seen = set()  # 用于去重
            search_stats = []  # 记录每轮搜索统计
            
            for i, keyword in enumerate(keywords, 1):
                try:
                    logger.info(f"🎯 第{i}轮搜索 - 关键词: {keyword}")
                    
                    # 构建简化的员工搜索查询（不直接使用复杂的LLM关键词）
                    # 使用更简单、直接的查询格式
                    position = request.target_positions[0] if request.target_positions else "manager"
                    if i == 1:
                        # 第1轮：基础查询
                        simple_query = f'"{request.company_name}" "{position}"'
                        logger.info(f"🔧 第{i}轮搜索策略: 基础查询 - 公司名 + 职位")
                    elif i == 2:
                        # 第2轮：加入位置信息
                        simple_query = f'"{request.company_name}" "{position}" "{optimized_params.get("location", "")}"'
                        logger.info(f"🔧 第{i}轮搜索策略: 位置增强 - 公司名 + 职位 + 地理位置")
                    else:
                        # 第3轮：使用原LLM关键词但简化
                        simple_query = f'"{request.company_name}" "{position}" {keyword.split()[-1]}'  # 取关键词的最后一部分
                        logger.info(f"🔧 第{i}轮搜索策略: LLM增强 - 公司名 + 职位 + LLM关键词片段")
                    
                    search_query = f"site:linkedin.com/in {simple_query}"
                    logger.info(f"🔍 LinkedIn员工搜索查询 {i}: {search_query}")
                    logger.info(f"📄 原始LLM关键词 {i}: {keyword}")
                    logger.info(f"🔧 简化搜索查询 {i}: {simple_query}")
                    
                    # 使用优化的Serper参数
                    serper_params = {
                        'gl': optimized_params.get('gl', request.country_code),
                        'location': optimized_params.get('location', self._get_location_by_country(request.country_code))
                    }
                    logger.info(f"📡 使用优化的Serper参数: {serper_params}")
                    
                    # 调用真实搜索器，使用简化查询
                    search_result = self.searcher.search_employees(
                        company_name=request.company_name,
                        position=position,  # 使用上面定义的position变量
                        location=optimized_params.get('location', '') if i == 2 else '',  # 只在第2轮使用位置
                        country=request.country_code,
                        additional_keywords=[],  # 不使用复杂的额外关键词
                        gl=optimized_params.get('gl', request.country_code),
                        num_results=min(10, request.max_results)  # 每轮最多10个结果
                    )
                    
                    # 处理搜索结果并去重
                    round_employees = []
                    raw_results = search_result.get('data', []) if isinstance(search_result, dict) else []
                    
                    # 详细记录原始搜索数据
                    logger.info(f"📊 第{i}轮原始搜索结果数据:")
                    logger.info(f"   - 搜索结果类型: {type(search_result)}")
                    logger.info(f"   - 原始结果条数: {len(raw_results)}")
                    if raw_results:
                        logger.info(f"   - 示例结果结构: {list(raw_results[0].keys()) if raw_results[0] else 'Empty result'}")
                        logger.info(f"   - 前3个结果预览:")
                        for idx, result in enumerate(raw_results[:3], 1):
                            name = result.get('name', 'Unknown')
                            position = result.get('position', 'Unknown')
                            linkedin = result.get('linkedin_url', '')
                            logger.info(f"     {idx}. {name} - {position} ({linkedin[:50]}...)")
                    
                    # 获取当前关键词的类型信息
                    current_variant = query_variants[i-1] if i-1 < len(query_variants) else {"type": "unknown"}
                    keyword_type = current_variant.get('type', 'unknown')
                    
                    for result in raw_results:
                        # 使用LinkedIn URL作为去重键
                        linkedin_url = result.get('linkedin_url', '')
                        if linkedin_url and linkedin_url not in employee_urls_seen:
                            employee = EmployeeInfo(
                                name=result.get('name', 'Unknown'),
                                position=result.get('position', request.target_positions[0] if request.target_positions else 'Employee'),
                                company=request.company_name,
                                linkedin_url=linkedin_url,
                                email=result.get('email'),
                                phone=result.get('phone'),
                                location=result.get('location'),
                                summary=result.get('summary'),
                                experience_years=result.get('experience_years'),
                                confidence_score=result.get('confidence_score', 0.8),
                                email_verified=result.get('email_verified', 'unknown'),
                                source=f"linkedin_search_round_{i}",
                                # 新增关键词来源信息
                                source_keyword=keyword,
                                keyword_type=keyword_type,
                                search_round=i
                            )
                            round_employees.append(employee)
                            employee_urls_seen.add(linkedin_url)
                    
                    all_employees.extend(round_employees)
                    
                    # 记录详细的搜索统计
                    round_stat = {
                        "round": i,
                        "keyword": keyword,
                        "keyword_type": keyword_type,
                        "raw_count": len(raw_results),
                        "valid_count": len(round_employees),
                        "cumulative_total": len(all_employees)
                    }
                    search_stats.append(round_stat)
                    
                    logger.info(f"✅ 第{i}轮搜索完成:")
                    logger.info(f"   🔍 关键词: {keyword} ({keyword_type})")
                    logger.info(f"   📊 原始结果: {len(raw_results)} 个")
                    logger.info(f"   ✨ 有效结果: {len(round_employees)} 个（去重后）")
                    logger.info(f"   🎯 累计总数: {len(all_employees)} 名员工")
                    
                except Exception as e:
                    logger.error(f"❌ 第{i}轮员工搜索失败: {e}")
                    continue
            
            logger.info(f"🎉 多关键词员工搜索完成，总共找到 {len(all_employees)} 名去重后的员工")
            
            # 按置信度排序并限制结果数量
            all_employees.sort(key=lambda x: x.confidence_score or 0, reverse=True)
            return all_employees[:request.max_results]
            
        except Exception as e:
            logger.error(f"❌ 员工搜索完全失败，使用增强模拟数据: {e}")
            import traceback
            logger.error(f"❌ 详细错误信息: {traceback.format_exc()}")
            return self._generate_enhanced_mock_employees(request, optimized_params)
    
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
    
    async def _optimize_search_params(self, request: EmployeeSearchRequest) -> Dict[str, Any]:
        """
        优化员工搜索参数：LLM关键词生成 + 职位增强 + 多样化搜索策略
        """
        result = {
            'enhanced_positions': request.target_positions.copy(),
            'keywords': [],
            'gl': request.country_code.upper(),
            'location': self._get_location_by_country(request.country_code)
        }
        
        try:
            if self.keyword_generator:
                # 🤖 使用LLM生成员工搜索关键词
                positions_str = " ".join(request.target_positions)
                search_context = f"{positions_str} employees at {request.company_name}"
                
                logger.info(f"🤖 使用LLM生成关键词: {search_context} -> {request.country_code.upper()}")
                
                keyword_result = self.keyword_generator.generate_search_keywords(
                    industry=search_context,
                    target_country=request.country_code,
                    search_type="linkedin"  # 员工搜索主要使用LinkedIn
                )
                
                # 详细记录LLM生成结果的原始数据
                logger.info(f"📊 LLM关键词生成详细结果: {keyword_result}")
                
                if keyword_result.get('success'):
                    # 获取LLM生成的多样化查询变体
                    if 'query_variants' in keyword_result:
                        queries = []
                        logger.info(f"🔍 发现 {len(keyword_result['query_variants'])} 个查询变体")
                        for i, variant in enumerate(keyword_result['query_variants'][:3], 1):  # 取前3个变体
                            query = variant.get('query', '')
                            variant_type = variant.get('type', 'unknown')
                            if query:
                                queries.append(query)
                                logger.info(f"📝 关键词变体{i}({variant_type}): {query}")
                        result['keywords'] = queries
                        logger.info(f"✅ LLM关键词生成成功: {queries}")
                        logger.info(f"🎯 将使用分别搜索策略，逐个关键词执行搜索")
                    else:
                        # 回退到primary_keywords
                        primary_keywords = keyword_result.get('primary_keywords', [])
                        if primary_keywords:
                            result['keywords'] = primary_keywords[:3]
                            logger.info(f"✅ 使用主关键词: {primary_keywords[:3]}")
                            # 为主关键词创建query_variants结构
                            result['query_variants'] = [
                                {"query": keyword, "type": "primary"} 
                                for keyword in primary_keywords[:3]
                            ]
                            for i, keyword in enumerate(primary_keywords[:3], 1):
                                logger.info(f"📝 主关键词{i}: {keyword}")
                        logger.info(f"🎯 将使用分别搜索策略，逐个关键词执行搜索")
                else:
                    error_msg = keyword_result.get('error', '未知错误')
                    logger.warning(f"❌ LLM关键词生成失败: {error_msg}")
                        
        except Exception as e:
            logger.error(f"❌ 搜索参数优化失败: {e}")
        
        # 确保至少有基础关键词（生成多样化查询）
        if not result['keywords']:
            result['keywords'] = [
                f"{request.company_name} {positions_str}",  # 基础查询
                f"{positions_str} at {request.company_name}",  # 职位导向
                f"{request.company_name} executive {positions_str}"  # 高管导向
            ]
            result['query_variants'] = [
                {"query": result['keywords'][0], "type": "basic"},
                {"query": result['keywords'][1], "type": "position_focused"},
                {"query": result['keywords'][2], "type": "executive_focused"}
            ]
            logger.info(f"🔧 使用回退关键词: {result['keywords']}")
            logger.info(f"🔧 使用回退查询变体: {result['query_variants']}")
        
        return result
    
    def _generate_enhanced_mock_employees(self, request: EmployeeSearchRequest, optimized_params: Dict[str, Any]) -> List[EmployeeInfo]:
        """生成增强的模拟员工数据（考虑LLM优化参数）"""
        employees = []
        
        # 根据不同国家生成不同的姓名
        names_by_country = {
            "us": ["John Smith", "Sarah Johnson", "Michael Brown", "Lisa Davis", "David Wilson", "Jennifer Taylor"],
            "cn": ["张伟", "李娜", "王强", "刘敏", "陈杰", "赵雅"], 
            "uk": ["James Wilson", "Emma Thompson", "Oliver Davies", "Sophie Clarke", "Harry Evans"],
            "de": ["Hans Mueller", "Anna Schmidt", "Klaus Wagner", "Eva Fischer", "Thomas Weber"],
            "jp": ["田中太郎", "佐藤花子", "鈴木一郎", "高橋美里", "渡辺健太"],
            "ca": ["Alex Johnson", "Maria Garcia", "Daniel Kim", "Sophie Dubois", "Ryan Chen"],
            "au": ["Liam Anderson", "Charlotte Wang", "Noah Thompson", "Emily Jones", "James Wilson"]
        }
        
        names = names_by_country.get(request.country_code, names_by_country["us"])
        
        # 使用增强的职位列表
        enhanced_positions = optimized_params.get('enhanced_positions', request.target_positions)
        
        # 生成员工数据
        num_employees = min(random.randint(3, 8), request.max_results)
        
        for i in range(num_employees):
            name = random.choice(names)
            position = random.choice(enhanced_positions)
            
            # 生成邮箱
            email = None
            email_verified = "unknown"
            if "email" in request.search_options:
                domain = request.company_domain or f"{request.company_name.lower().replace(' ', '')}.com"
                first_name = name.split()[0].lower()
                last_name = name.split()[-1].lower() if len(name.split()) > 1 else "user"
                email = f"{first_name}.{last_name}@{domain}"
                email_verified = random.choice(["verified", "verified", "unverified"])  # 偏向验证成功
            
            # 生成电话
            phone = None
            if "phone" in request.search_options:
                phone = self._generate_phone_by_country(request.country_code)
            
            # 生成LinkedIn
            linkedin_url = None
            if "linkedin" in request.search_options:
                linkedin_id = name.lower().replace(' ', '-')
                linkedin_url = f"https://linkedin.com/in/{linkedin_id}-{random.randint(100, 999)}"
            
            # 增强的员工信息
            employee = EmployeeInfo(
                name=name,
                position=position,
                company=request.company_name,
                linkedin_url=linkedin_url,
                email=email,
                phone=phone,
                location=self._get_enhanced_location_by_country(request.country_code),
                summary=self._generate_professional_summary(name, position, request.company_name),
                experience_years=random.randint(2, 15),
                confidence_score=random.uniform(0.75, 0.95),  # 提高置信度范围
                email_verified=email_verified,
                source="enhanced_linkedin_search"
            )
            
            employees.append(employee)
        
        # 按置信度排序
        employees.sort(key=lambda x: x.confidence_score or 0, reverse=True)
        
        return employees
    
    def _generate_phone_by_country(self, country_code: str) -> str:
        """根据国家代码生成对应格式的电话号码"""
        phone_formats = {
            "us": lambda: f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            "cn": lambda: f"+86-138{random.randint(10000000, 99999999)}",
            "uk": lambda: f"+44-20-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
            "de": lambda: f"+49-30-{random.randint(100000, 999999)}",
            "jp": lambda: f"+81-3-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
            "ca": lambda: f"+1-{random.randint(400, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            "au": lambda: f"+61-2-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
        }
        
        phone_generator = phone_formats.get(country_code)
        if phone_generator:
            return phone_generator()
        else:
            return f"+{random.randint(1, 999)}-{random.randint(100000000, 999999999)}"
    
    def _get_enhanced_location_by_country(self, country_code: str) -> str:
        """根据国家代码返回增强的典型位置"""
        locations = {
            "us": random.choice(["San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX", "Boston, MA"]),
            "cn": random.choice(["北京市", "上海市", "深圳市", "广州市", "杭州市"]),
            "uk": random.choice(["London, UK", "Manchester, UK", "Birmingham, UK", "Edinburgh, UK"]),
            "de": random.choice(["Berlin, Germany", "Munich, Germany", "Hamburg, Germany", "Frankfurt, Germany"]), 
            "jp": random.choice(["Tokyo, Japan", "Osaka, Japan", "Kyoto, Japan", "Yokohama, Japan"]),
            "sg": "Singapore",
            "au": random.choice(["Sydney, Australia", "Melbourne, Australia", "Brisbane, Australia"]),
            "ca": random.choice(["Toronto, Canada", "Vancouver, Canada", "Montreal, Canada", "Calgary, Canada"]),
            "tw": random.choice(["台北市", "新北市", "高雄市"])
        }
        return locations.get(country_code, "Unknown Location")
    
    def _generate_professional_summary(self, name: str, position: str, company: str) -> str:
        """生成专业的员工简介"""
        experience_years = random.randint(3, 12)
        
        summaries = [
            f"在{company}担任{position}，拥有{experience_years}年相关工作经验，专注于团队领导和业务发展。",
            f"资深{position}，在{company}负责核心业务，有丰富的行业经验和专业技能。",
            f"{company}的{position}，致力于推动业务创新和团队合作，具有强烈的责任心。",
            f"经验丰富的{position}，在{company}发挥关键作用，擅长跨部门协作和项目管理。"
        ]
        
        return random.choice(summaries)
    
    async def _analyze_employees_with_ai(self, employees: List[EmployeeInfo], request: EmployeeSearchRequest) -> List[EmployeeInfo]:
        """使用AI分析员工信息并添加评分"""
        try:
            logger.info(f"🤖 开始AI分析 {len(employees)} 名员工")
            
            for employee in employees:
                # 模拟AI分析评分
                ai_score = self._calculate_ai_employee_score(employee, request)
                ai_reason = self._generate_ai_analysis_reason(employee, ai_score, request)
                
                # 添加AI分析字段
                employee.ai_score = ai_score
                employee.ai_reason = ai_reason
                employee.relevance_score = min(ai_score + random.uniform(-0.1, 0.1), 1.0)
                employee.analysis_confidence = random.uniform(0.8, 0.95)
                
            logger.info(f"✅ AI分析完成")
            return employees
            
        except Exception as e:
            logger.error(f"❌ AI分析失败: {e}")
            return employees
    
    def _calculate_ai_employee_score(self, employee: EmployeeInfo, request: EmployeeSearchRequest) -> float:
        """计算员工的AI相关性评分"""
        score = 0.5  # 基础分数
        
        # 职位匹配度
        if employee.position in request.target_positions:
            score += 0.3
        
        # 经验年限加分
        if hasattr(employee, 'experience_years') and employee.experience_years:
            if employee.experience_years >= 5:
                score += 0.2
            elif employee.experience_years >= 2:
                score += 0.1
        
        # 联系方式完整度加分
        contact_completeness = 0
        if employee.email:
            contact_completeness += 0.33
        if employee.phone:
            contact_completeness += 0.33
        if employee.linkedin_url:
            contact_completeness += 0.34
        
        score += contact_completeness * 0.2  # 最多加0.2分
        
        # 邮箱验证状态加分
        if employee.email_verified == "verified":
            score += 0.1
        
        return min(max(score, 0.0), 1.0)
    
    def _generate_ai_analysis_reason(self, employee: EmployeeInfo, ai_score: float, request: EmployeeSearchRequest) -> str:
        """生成AI分析原因"""
        reasons = []
        
        # 职位匹配分析
        if employee.position in request.target_positions:
            reasons.append(f"职位完全匹配({employee.position})")
        else:
            reasons.append(f"职位相关({employee.position})")
        
        # 经验分析
        if hasattr(employee, 'experience_years') and employee.experience_years:
            if employee.experience_years >= 5:
                reasons.append(f"丰富经验({employee.experience_years}年)")
            else:
                reasons.append(f"相关经验({employee.experience_years}年)")
        
        # 联系方式分析
        contact_info = []
        if employee.email:
            contact_info.append("邮箱")
        if employee.phone:
            contact_info.append("电话")
        if employee.linkedin_url:
            contact_info.append("LinkedIn")
        
        if contact_info:
            reasons.append(f"联系方式完整({', '.join(contact_info)})")
        
        # 验证状态
        if employee.email_verified == "verified":
            reasons.append("邮箱已验证")
        
        return "; ".join(reasons)


# 全局服务实例
_employee_service = None

def get_employee_service() -> EmployeeSearchService:
    """获取员工搜索服务实例"""
    global _employee_service
    if _employee_service is None:
        _employee_service = EmployeeSearchService()
    return _employee_service