"""
员工搜索节点
集成现有serper_employee_search功能，基于符合条件的公司搜索员工
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import time

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from serper_employee_search import SerperEmployeeSearch
from ..state import SearchState, CompanyInfo, EmployeeInfo, add_error_to_state, add_warning_to_state

@dataclass
class EmployeeSearchConfig:
    """员工搜索配置"""
    max_results_per_company: int = 20
    max_companies_to_search: int = 10
    gl: str = "us"
    timeout_per_company: int = 30
    max_retries: int = 3
    enable_cache: bool = True
    max_concurrent_searches: int = 3  # 并发搜索公司数量
    enable_deduplication: bool = True  # 启用去重
    min_qualified_companies: int = 1  # 最少需要的合格公司数量

class EmployeeSearchNode:
    """
    员工搜索节点
    
    负责基于符合条件的公司搜索员工：
    - 使用AI评估后的合格公司列表
    - 并行搜索多家公司的员工
    - 支持职位匹配和过滤
    - 实现员工信息去重
    - 提供搜索结果排序和优化
    """
    
    def __init__(self, config: Optional[EmployeeSearchConfig] = None):
        """初始化员工搜索节点"""
        self.config = config or EmployeeSearchConfig()
        self.logger = logging.getLogger(__name__)
        self.search_cache = {}  # 简单内存缓存
        
        # 验证API密钥
        self.api_key = os.getenv("SERPER_API_KEY")
        if not self.api_key:
            self.logger.error("SERPER_API_KEY not found in environment variables")
    
    def execute(self, state: SearchState) -> SearchState:
        """
        执行员工搜索节点
        
        Args:
            state: 当前搜索状态
            
        Returns:
            更新后的状态
        """
        try:
            self.logger.info("开始执行员工搜索")
            
            # 更新当前节点
            state["current_node"] = "employee_search"
            state["workflow_path"].append("employee_search_started")
            
            # 检查API密钥
            if not self.api_key:
                return add_error_to_state(
                    state,
                    "missing_api_key",
                    "SERPER_API_KEY not configured",
                    "employee_search"
                )
            
            # 检查是否需要员工搜索
            intent = state["detected_intent"]
            if intent not in ["employee", "composite"]:
                self.logger.info("当前意图不需要员工搜索，跳过")
                state["employee_search_completed"] = True
                state["workflow_path"].append("employee_search_skipped")
                return state
            
            # 获取符合条件的公司列表
            qualified_companies = state["search_results"]["qualified_companies"]
            if not qualified_companies:
                return add_error_to_state(
                    state,
                    "no_qualified_companies",
                    "没有符合条件的公司进行员工搜索",
                    "employee_search"
                )
            
            if len(qualified_companies) < self.config.min_qualified_companies:
                return add_warning_to_state(
                    state,
                    "insufficient_companies",
                    f"符合条件的公司数量较少: {len(qualified_companies)}",
                    "employee_search"
                )
            
            # 准备搜索参数
            search_criteria = self._prepare_employee_search_criteria(state)
            
            # 执行并行员工搜索
            all_employees = self._perform_parallel_employee_search(
                qualified_companies,
                search_criteria
            )
            
            if not all_employees:
                return add_warning_to_state(
                    state,
                    "no_employees_found",
                    "未找到任何员工信息",
                    "employee_search"
                )
            
            # 去重和过滤
            if self.config.enable_deduplication:
                all_employees = self._deduplicate_employees(all_employees)
            
            filtered_employees = self._filter_and_rank_employees(all_employees, search_criteria)
            
            # 更新状态
            state["search_results"]["employees"] = filtered_employees
            state["search_results"]["total_employees_found"] = len(filtered_employees)
            state["employee_search_completed"] = True
            state["workflow_path"].append("employee_search_completed")
            
            # 记录API调用次数
            companies_searched = min(len(qualified_companies), self.config.max_companies_to_search)
            state["api_calls_count"] += companies_searched
            
            self.logger.info(f"员工搜索完成，找到 {len(filtered_employees)} 名员工")
            
            # 如果结果数量较少，添加警告
            if len(filtered_employees) < 5:
                state = add_warning_to_state(
                    state,
                    "low_employee_results",
                    f"员工搜索结果数量较少: {len(filtered_employees)}",
                    "employee_search"
                )
            
            return state
            
        except Exception as e:
            self.logger.error(f"员工搜索过程中发生错误: {e}")
            return add_error_to_state(
                state,
                "employee_search_exception",
                f"员工搜索执行异常: {str(e)}",
                "employee_search"
            )
    
    def _prepare_employee_search_criteria(self, state: SearchState) -> Dict[str, Any]:
        """准备员工搜索条件"""
        
        search_params = state["search_params"]
        
        criteria = {
            "position": search_params.position or self._extract_position_from_query(state["user_query"]),
            "location": search_params.region or "",
            "seniority_level": search_params.seniority_level or "",
            "department": search_params.department or "",
            "additional_keywords": self._extract_employee_keywords(state["user_query"])
        }
        
        # 如果没有明确的职位信息，从意图和查询中推断
        if not criteria["position"]:
            criteria["position"] = self._infer_target_position(state)
        
        return criteria
    
    def _extract_position_from_query(self, query: str) -> str:
        """从用户查询中提取职位信息"""
        
        # 常见职位关键词映射
        position_keywords = {
            "销售": ["销售经理", "销售总监", "销售代表"],
            "市场": ["市场经理", "市场总监", "市场专员"], 
            "技术": ["技术经理", "技术总监", "CTO"],
            "采购": ["采购经理", "采购总监", "采购专员"],
            "CEO": ["CEO", "总裁", "首席执行官"],
            "CTO": ["CTO", "技术总监", "首席技术官"],
            "CFO": ["CFO", "财务总监", "首席财务官"],
            "经理": ["经理"],
            "总监": ["总监"],
            "专员": ["专员"],
            "主管": ["主管"]
        }
        
        query_lower = query.lower()
        
        for keyword, positions in position_keywords.items():
            if keyword.lower() in query_lower:
                return positions[0]  # 返回最常见的职位
        
        return ""
    
    def _extract_employee_keywords(self, query: str) -> List[str]:
        """从查询中提取员工搜索关键词"""
        keywords = []
        
        # 移除常见停用词
        stop_words = {"找", "搜索", "查找", "的", "联系方式", "信息", "员工", "人员"}
        
        words = query.replace("，", " ").replace(",", " ").split()
        for word in words:
            word = word.strip()
            if len(word) > 1 and word not in stop_words:
                keywords.append(word)
        
        return keywords[:3]  # 限制关键词数量
    
    def _infer_target_position(self, state: SearchState) -> str:
        """推断目标职位"""
        
        # 基于搜索意图推断默认职位
        intent = state["detected_intent"]
        
        default_positions = {
            "employee": "经理",  # 员工搜索默认找经理
            "composite": "销售经理"  # 复合搜索默认找销售
        }
        
        return default_positions.get(intent, "经理")
    
    def _perform_parallel_employee_search(self, qualified_companies: List[CompanyInfo], 
                                        search_criteria: Dict[str, Any]) -> List[EmployeeInfo]:
        """并行搜索多家公司的员工"""
        
        all_employees = []
        companies_to_search = qualified_companies[:self.config.max_companies_to_search]
        
        self.logger.info(f"开始并行搜索 {len(companies_to_search)} 家公司的员工")
        
        with ThreadPoolExecutor(max_workers=self.config.max_concurrent_searches) as executor:
            # 提交搜索任务
            future_to_company = {
                executor.submit(
                    self._search_company_employees, 
                    company, 
                    search_criteria
                ): company for company in companies_to_search
            }
            
            # 收集结果
            for future in as_completed(future_to_company, timeout=self.config.timeout_per_company * len(companies_to_search)):
                company = future_to_company[future]
                try:
                    employees = future.result(timeout=self.config.timeout_per_company)
                    if employees:
                        all_employees.extend(employees)
                        self.logger.info(f"在 {company.name} 找到 {len(employees)} 名员工")
                    else:
                        self.logger.warning(f"在 {company.name} 未找到员工")
                        
                except Exception as e:
                    self.logger.error(f"搜索 {company.name} 员工失败: {e}")
                    continue
        
        self.logger.info(f"并行搜索完成，总计找到 {len(all_employees)} 名员工")
        return all_employees
    
    def _search_company_employees(self, company: CompanyInfo, 
                                search_criteria: Dict[str, Any]) -> List[EmployeeInfo]:
        """搜索单个公司的员工"""
        
        try:
            # 生成缓存键
            cache_key = f"{company.name}_{search_criteria['position']}_{search_criteria['location']}"
            
            # 检查缓存
            if self.config.enable_cache and cache_key in self.search_cache:
                cache_entry = self.search_cache[cache_key]
                if time.time() - cache_entry["timestamp"] < 3600:  # 1小时缓存
                    return cache_entry["results"]
            
            # 创建搜索器
            searcher = SerperEmployeeSearch(
                output_file=None,  # 不保存文件，只返回结果
                gl=self.config.gl,
                num_results=self.config.max_results_per_company
            )
            
            # 执行搜索
            raw_employees = searcher.search_employees(
                company_name=company.name,
                position=search_criteria["position"],
                location=search_criteria["location"],
                additional_keywords=search_criteria.get("additional_keywords")
            )
            
            if not raw_employees:
                return []
            
            # 转换为标准格式
            standardized_employees = self._standardize_employee_results(raw_employees, company)
            
            # 缓存结果
            if self.config.enable_cache:
                self.search_cache[cache_key] = {
                    "results": standardized_employees,
                    "timestamp": time.time()
                }
                
                # 限制缓存大小
                if len(self.search_cache) > 50:
                    oldest_key = min(self.search_cache.keys(), 
                                   key=lambda k: self.search_cache[k]["timestamp"])
                    del self.search_cache[oldest_key]
            
            return standardized_employees
            
        except Exception as e:
            self.logger.error(f"搜索 {company.name} 员工时发生错误: {e}")
            return []
    
    def _standardize_employee_results(self, raw_employees: List[Dict[str, Any]], 
                                    company: CompanyInfo) -> List[EmployeeInfo]:
        """将员工搜索结果标准化为EmployeeInfo对象"""
        
        standardized_employees = []
        
        for raw_employee in raw_employees:
            try:
                # 创建标准化的员工信息
                employee = EmployeeInfo(
                    name=raw_employee.get("name", "").strip(),
                    position=raw_employee.get("position", ""),
                    company=company.name,
                    linkedin_url=raw_employee.get("linkedin_url", raw_employee.get("url", "")),
                    location=raw_employee.get("location", company.location or ""),
                    description=raw_employee.get("description", raw_employee.get("snippet", ""))
                )
                
                # 只添加有效的员工信息
                if employee.name and employee.linkedin_url:
                    standardized_employees.append(employee)
                
            except Exception as e:
                self.logger.warning(f"标准化员工信息失败: {e}")
                continue
        
        return standardized_employees
    
    def _deduplicate_employees(self, employees: List[EmployeeInfo]) -> List[EmployeeInfo]:
        """员工信息去重"""
        
        unique_employees = []
        seen_profiles = set()
        seen_names_companies = set()
        
        for employee in employees:
            # 基于LinkedIn URL去重 (最准确)
            if employee.linkedin_url:
                linkedin_key = employee.linkedin_url.lower().strip().rstrip('/')
                if linkedin_key in seen_profiles:
                    continue
                seen_profiles.add(linkedin_key)
            
            # 基于姓名+公司去重 (次选方案)
            name_company_key = f"{employee.name.lower()}_{employee.company.lower()}"
            if name_company_key in seen_names_companies:
                continue
            seen_names_companies.add(name_company_key)
            
            unique_employees.append(employee)
        
        removed_count = len(employees) - len(unique_employees)
        if removed_count > 0:
            self.logger.info(f"去重完成，移除了 {removed_count} 个重复员工")
        
        return unique_employees
    
    def _filter_and_rank_employees(self, employees: List[EmployeeInfo], 
                                 search_criteria: Dict[str, Any]) -> List[EmployeeInfo]:
        """过滤和排序员工"""
        
        filtered_employees = []
        target_position = search_criteria.get("position", "").lower()
        target_keywords = [kw.lower() for kw in search_criteria.get("additional_keywords", [])]
        
        for employee in employees:
            # 基本过滤条件
            if not employee.name or not employee.linkedin_url:
                continue
            
            # 职位匹配评分
            position_score = self._calculate_position_match_score(employee.position, target_position)
            
            # 关键词匹配评分
            keyword_score = self._calculate_keyword_match_score(employee, target_keywords)
            
            # 综合评分
            total_score = position_score * 0.7 + keyword_score * 0.3
            
            # 设置一个基本的过滤阈值
            if total_score >= 0.3:  # 30%的匹配度
                # 将评分信息存储到员工对象中 (用于后续AI评估)
                employee.ai_score = total_score * 100  # 转换为0-100分
                filtered_employees.append(employee)
        
        # 按评分排序
        filtered_employees.sort(key=lambda x: x.ai_score or 0, reverse=True)
        
        return filtered_employees
    
    def _calculate_position_match_score(self, employee_position: str, target_position: str) -> float:
        """计算职位匹配评分"""
        
        if not employee_position or not target_position:
            return 0.5  # 中等评分
        
        employee_pos_lower = employee_position.lower()
        target_pos_lower = target_position.lower()
        
        # 完全匹配
        if target_pos_lower in employee_pos_lower:
            return 1.0
        
        # 关键词匹配
        target_keywords = ["经理", "总监", "专员", "主管", "CEO", "CTO", "CFO", "销售", "市场", "技术", "采购"]
        
        matches = 0
        total_keywords = 0
        
        for keyword in target_keywords:
            if keyword in target_pos_lower:
                total_keywords += 1
                if keyword in employee_pos_lower:
                    matches += 1
        
        if total_keywords > 0:
            return matches / total_keywords
        
        return 0.3  # 默认评分
    
    def _calculate_keyword_match_score(self, employee: EmployeeInfo, target_keywords: List[str]) -> float:
        """计算关键词匹配评分"""
        
        if not target_keywords:
            return 1.0  # 没有关键词要求，满分
        
        # 检查的文本内容
        check_text = f"{employee.position} {employee.description}".lower()
        
        matches = 0
        for keyword in target_keywords:
            if keyword in check_text:
                matches += 1
        
        return matches / len(target_keywords) if target_keywords else 0
    
    def get_search_statistics(self, state: SearchState) -> Dict[str, Any]:
        """获取员工搜索统计信息"""
        
        qualified_companies = state["search_results"]["qualified_companies"]
        employees = state["search_results"]["employees"]
        
        stats = {
            "companies_searched": min(len(qualified_companies), self.config.max_companies_to_search),
            "total_companies_available": len(qualified_companies),
            "total_employees_found": len(employees),
            "average_employees_per_company": len(employees) / len(qualified_companies) if qualified_companies else 0,
            "search_completed": state.get("employee_search_completed", False),
            "config": {
                "max_results_per_company": self.config.max_results_per_company,
                "max_companies_to_search": self.config.max_companies_to_search,
                "concurrent_searches": self.config.max_concurrent_searches
            }
        }
        
        # 公司分布统计
        if employees:
            company_distribution = {}
            for employee in employees:
                company = employee.company
                company_distribution[company] = company_distribution.get(company, 0) + 1
            
            stats["company_distribution"] = company_distribution
            stats["companies_with_results"] = len(company_distribution)
        
        return stats

# 创建节点实例
employee_search_node = EmployeeSearchNode()