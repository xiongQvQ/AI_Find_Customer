"""
输出集成节点
整合搜索结果并生成输出文件
"""

import os
import json
import csv
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

from ..state import SearchState, CompanyInfo, EmployeeInfo

logger = logging.getLogger(__name__)

class OutputIntegrationNode:
    """
    输出集成节点
    
    负责：
    1. 整合公司和员工搜索结果
    2. 生成结构化输出文件 (CSV/JSON)
    3. 创建搜索报告和统计信息
    4. 设置输出路径和文件命名
    """
    
    def __init__(self):
        self.output_base_dir = "output/langgraph"
        # 确保输出目录存在
        os.makedirs(self.output_base_dir, exist_ok=True)
        
    def execute(self, state: SearchState) -> SearchState:
        """
        执行输出集成
        
        Args:
            state: 当前搜索状态
            
        Returns:
            更新后的搜索状态，包含输出文件路径和统计信息
        """
        try:
            logger.info("开始执行输出集成节点")
            
            # 更新当前节点状态
            state["current_node"] = "output_integration"
            state["workflow_path"].append("output_integration")
            
            # 获取搜索结果
            companies = state["search_results"]["companies"]
            qualified_companies = state["search_results"]["qualified_companies"]
            employees = state["search_results"]["employees"]
            qualified_employees = state["search_results"]["qualified_employees"]
            
            # 生成输出文件
            output_files = self._generate_output_files(
                state=state,
                companies=companies,
                qualified_companies=qualified_companies,
                employees=employees,
                qualified_employees=qualified_employees
            )
            
            # 生成搜索报告
            search_report = self._generate_search_report(
                state=state,
                companies=companies,
                qualified_companies=qualified_companies,
                employees=employees,
                qualified_employees=qualified_employees
            )
            
            # 更新状态
            state["output_files"] = output_files
            state["search_report"] = search_report
            state["output_integration_completed"] = True
            
            logger.info(f"输出集成完成，生成了 {len(output_files)} 个文件")
            
            return state
            
        except Exception as e:
            logger.error(f"输出集成节点执行失败: {e}")
            # 添加错误到状态
            from ..state import add_error_to_state
            return add_error_to_state(
                state,
                "output_integration_error",
                f"输出集成失败: {str(e)}",
                "output_integration"
            )
    
    def _generate_output_files(
        self,
        state: SearchState,
        companies: List[CompanyInfo],
        qualified_companies: List[CompanyInfo],
        employees: List[EmployeeInfo],
        qualified_employees: List[EmployeeInfo]
    ) -> List[str]:
        """生成输出文件"""
        output_files = []
        
        # 生成时间戳和基础文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = state["session_id"]
        intent = state["detected_intent"]
        
        # 构建文件前缀
        file_prefix = f"{intent}_search_{session_id}_{timestamp}"
        
        try:
            # 1. 公司结果文件
            if companies:
                company_files = self._save_company_results(
                    companies, qualified_companies, file_prefix
                )
                output_files.extend(company_files)
            
            # 2. 员工结果文件
            if employees:
                employee_files = self._save_employee_results(
                    employees, qualified_employees, file_prefix
                )
                output_files.extend(employee_files)
            
            # 3. 综合报告文件
            if intent == "composite" or (companies and employees):
                composite_files = self._save_composite_results(
                    companies, qualified_companies, 
                    employees, qualified_employees,
                    file_prefix
                )
                output_files.extend(composite_files)
            
            # 4. 搜索配置和元数据
            metadata_file = self._save_search_metadata(state, file_prefix)
            if metadata_file:
                output_files.append(metadata_file)
                
        except Exception as e:
            logger.error(f"生成输出文件失败: {e}")
            raise
        
        return output_files
    
    def _save_company_results(
        self, 
        companies: List[CompanyInfo], 
        qualified_companies: List[CompanyInfo],
        file_prefix: str
    ) -> List[str]:
        """保存公司搜索结果"""
        files = []
        
        try:
            # 保存所有公司结果
            all_companies_csv = os.path.join(self.output_base_dir, f"{file_prefix}_companies_all.csv")
            all_companies_json = os.path.join(self.output_base_dir, f"{file_prefix}_companies_all.json")
            
            self._write_companies_csv(companies, all_companies_csv)
            self._write_companies_json(companies, all_companies_json)
            
            files.extend([all_companies_csv, all_companies_json])
            
            # 保存符合条件的公司结果
            if qualified_companies:
                qualified_companies_csv = os.path.join(self.output_base_dir, f"{file_prefix}_companies_qualified.csv")
                qualified_companies_json = os.path.join(self.output_base_dir, f"{file_prefix}_companies_qualified.json")
                
                self._write_companies_csv(qualified_companies, qualified_companies_csv)
                self._write_companies_json(qualified_companies, qualified_companies_json)
                
                files.extend([qualified_companies_csv, qualified_companies_json])
                
        except Exception as e:
            logger.error(f"保存公司结果失败: {e}")
            raise
            
        return files
    
    def _save_employee_results(
        self,
        employees: List[EmployeeInfo],
        qualified_employees: List[EmployeeInfo],
        file_prefix: str
    ) -> List[str]:
        """保存员工搜索结果"""
        files = []
        
        try:
            # 保存所有员工结果
            all_employees_csv = os.path.join(self.output_base_dir, f"{file_prefix}_employees_all.csv")
            all_employees_json = os.path.join(self.output_base_dir, f"{file_prefix}_employees_all.json")
            
            self._write_employees_csv(employees, all_employees_csv)
            self._write_employees_json(employees, all_employees_json)
            
            files.extend([all_employees_csv, all_employees_json])
            
            # 保存符合条件的员工结果
            if qualified_employees:
                qualified_employees_csv = os.path.join(self.output_base_dir, f"{file_prefix}_employees_qualified.csv")
                qualified_employees_json = os.path.join(self.output_base_dir, f"{file_prefix}_employees_qualified.json")
                
                self._write_employees_csv(qualified_employees, qualified_employees_csv)
                self._write_employees_json(qualified_employees, qualified_employees_json)
                
                files.extend([qualified_employees_csv, qualified_employees_json])
                
        except Exception as e:
            logger.error(f"保存员工结果失败: {e}")
            raise
            
        return files
    
    def _save_composite_results(
        self,
        companies: List[CompanyInfo],
        qualified_companies: List[CompanyInfo],
        employees: List[EmployeeInfo],
        qualified_employees: List[EmployeeInfo],
        file_prefix: str
    ) -> List[str]:
        """保存综合搜索结果"""
        files = []
        
        try:
            composite_csv = os.path.join(self.output_base_dir, f"{file_prefix}_composite.csv")
            composite_json = os.path.join(self.output_base_dir, f"{file_prefix}_composite.json")
            
            # 创建综合数据结构
            composite_data = {
                "companies": {
                    "all": [self._company_to_dict(c) for c in companies],
                    "qualified": [self._company_to_dict(c) for c in qualified_companies]
                },
                "employees": {
                    "all": [self._employee_to_dict(e) for e in employees],
                    "qualified": [self._employee_to_dict(e) for e in qualified_employees]
                },
                "summary": {
                    "total_companies": len(companies),
                    "qualified_companies": len(qualified_companies),
                    "total_employees": len(employees),
                    "qualified_employees": len(qualified_employees)
                }
            }
            
            # 保存JSON格式
            with open(composite_json, 'w', encoding='utf-8') as f:
                json.dump(composite_data, f, indent=2, ensure_ascii=False)
            
            # 保存CSV格式 (扁平化结构)
            self._write_composite_csv(composite_data, composite_csv)
            
            files.extend([composite_csv, composite_json])
            
        except Exception as e:
            logger.error(f"保存综合结果失败: {e}")
            raise
            
        return files
    
    def _save_search_metadata(self, state: SearchState, file_prefix: str) -> Optional[str]:
        """保存搜索元数据"""
        try:
            metadata_file = os.path.join(self.output_base_dir, f"{file_prefix}_metadata.json")
            
            metadata = {
                "session_id": state["session_id"],
                "user_query": state["user_query"],
                "detected_intent": state["detected_intent"],
                "intent_confidence": state["intent_confidence"],
                "workflow_path": state["workflow_path"],
                "search_params": state["search_params"],
                "ai_evaluation_enabled": state.get("ai_evaluation_enabled", False),
                "errors": state.get("errors", []),
                "warnings": state.get("warnings", []),
                "execution_time": datetime.now().isoformat(),
                "counts": {
                    "total_companies": state["search_results"]["total_companies_found"],
                    "qualified_companies": state["search_results"]["qualified_companies_count"],
                    "total_employees": state["search_results"]["total_employees_found"],
                    "qualified_employees": state["search_results"]["qualified_employees_count"]
                }
            }
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            return metadata_file
            
        except Exception as e:
            logger.error(f"保存搜索元数据失败: {e}")
            return None
    
    def _write_companies_csv(self, companies: List[CompanyInfo], file_path: str):
        """将公司数据写入CSV文件"""
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            if companies:
                fieldnames = [
                    'name', 'industry', 'location', 'description', 'website',
                    'employee_count', 'founded_year', 'linkedin_url', 'ai_score',
                    'ai_reason', 'is_qualified'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for company in companies:
                    writer.writerow(self._company_to_dict(company))
    
    def _write_companies_json(self, companies: List[CompanyInfo], file_path: str):
        """将公司数据写入JSON文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            data = [self._company_to_dict(c) for c in companies]
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _write_employees_csv(self, employees: List[EmployeeInfo], file_path: str):
        """将员工数据写入CSV文件"""
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            if employees:
                fieldnames = [
                    'name', 'position', 'company', 'linkedin_url', 'location',
                    'description', 'ai_score', 'ai_reason', 'is_qualified'
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for employee in employees:
                    writer.writerow(self._employee_to_dict(employee))
    
    def _write_employees_json(self, employees: List[EmployeeInfo], file_path: str):
        """将员工数据写入JSON文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            data = [self._employee_to_dict(e) for e in employees]
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _write_composite_csv(self, composite_data: Dict[str, Any], file_path: str):
        """将综合数据写入CSV文件"""
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'type', 'name', 'company', 'position', 'industry', 'location',
                'website', 'linkedin_url', 'description', 'ai_score', 
                'ai_reason', 'is_qualified'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            # 写入公司数据
            for company in composite_data['companies']['qualified']:
                row = {
                    'type': 'company',
                    'name': company.get('name', ''),
                    'company': company.get('name', ''),
                    'position': '',
                    'industry': company.get('industry', ''),
                    'location': company.get('location', ''),
                    'website': company.get('website', ''),
                    'linkedin_url': company.get('linkedin_url', ''),
                    'description': company.get('description', ''),
                    'ai_score': company.get('ai_score', ''),
                    'ai_reason': company.get('ai_reason', ''),
                    'is_qualified': company.get('is_qualified', False)
                }
                writer.writerow(row)
            
            # 写入员工数据
            for employee in composite_data['employees']['qualified']:
                row = {
                    'type': 'employee',
                    'name': employee.get('name', ''),
                    'company': employee.get('company', ''),
                    'position': employee.get('position', ''),
                    'industry': '',
                    'location': employee.get('location', ''),
                    'website': '',
                    'linkedin_url': employee.get('linkedin_url', ''),
                    'description': employee.get('description', ''),
                    'ai_score': employee.get('ai_score', ''),
                    'ai_reason': employee.get('ai_reason', ''),
                    'is_qualified': employee.get('is_qualified', False)
                }
                writer.writerow(row)
    
    def _company_to_dict(self, company: CompanyInfo) -> Dict[str, Any]:
        """将CompanyInfo转换为字典"""
        return {
            'name': company.name,
            'industry': company.industry,
            'location': company.location,
            'description': company.description,
            'website': company.website_url,
            'employee_count': getattr(company, 'employee_count', ''),
            'founded_year': getattr(company, 'founded_year', ''),
            'linkedin_url': getattr(company, 'linkedin_url', ''),
            'ai_score': getattr(company, 'ai_score', ''),
            'ai_reason': getattr(company, 'ai_reason', ''),
            'is_qualified': getattr(company, 'is_qualified', False)
        }
    
    def _employee_to_dict(self, employee: EmployeeInfo) -> Dict[str, Any]:
        """将EmployeeInfo转换为字典"""
        return {
            'name': employee.name,
            'position': employee.position,
            'company': employee.company,
            'linkedin_url': employee.linkedin_url,
            'location': employee.location,
            'description': employee.description,
            'ai_score': getattr(employee, 'ai_score', ''),
            'ai_reason': getattr(employee, 'ai_reason', ''),
            'is_qualified': getattr(employee, 'is_qualified', False)
        }
    
    def _generate_search_report(
        self,
        state: SearchState,
        companies: List[CompanyInfo],
        qualified_companies: List[CompanyInfo],
        employees: List[EmployeeInfo],
        qualified_employees: List[EmployeeInfo]
    ) -> Dict[str, Any]:
        """生成搜索报告"""
        
        report = {
            "session_info": {
                "session_id": state["session_id"],
                "user_query": state["user_query"],
                "detected_intent": state["detected_intent"],
                "intent_confidence": state["intent_confidence"],
                "workflow_path": state["workflow_path"]
            },
            "search_params": state["search_params"],
            "results_summary": {
                "companies": {
                    "total_found": len(companies),
                    "qualified": len(qualified_companies),
                    "qualification_rate": len(qualified_companies) / len(companies) * 100 if companies else 0
                },
                "employees": {
                    "total_found": len(employees),
                    "qualified": len(qualified_employees),
                    "qualification_rate": len(qualified_employees) / len(employees) * 100 if employees else 0
                }
            },
            "quality_metrics": {
                "errors": len(state.get("errors", [])),
                "warnings": len(state.get("warnings", [])),
                "success_rate": self._calculate_success_rate(state)
            },
            "ai_evaluation": {
                "enabled": state.get("ai_evaluation_enabled", False),
                "completed": state.get("ai_evaluation_completed", False)
            }
        }
        
        # 添加顶级结果统计
        if qualified_companies:
            report["top_companies"] = [
                {
                    "name": c.name,
                    "industry": c.industry,
                    "ai_score": getattr(c, 'ai_score', 0)
                }
                for c in sorted(qualified_companies, key=lambda x: getattr(x, 'ai_score', 0), reverse=True)[:5]
            ]
        
        if qualified_employees:
            report["top_employees"] = [
                {
                    "name": e.name,
                    "position": e.position,
                    "company": e.company,
                    "ai_score": getattr(e, 'ai_score', 0)
                }
                for e in sorted(qualified_employees, key=lambda x: getattr(x, 'ai_score', 0), reverse=True)[:10]
            ]
        
        return report
    
    def _calculate_success_rate(self, state: SearchState) -> float:
        """计算成功率"""
        try:
            total_operations = len(state["workflow_path"])
            error_count = len(state.get("errors", []))
            
            if total_operations == 0:
                return 0.0
            
            success_rate = (total_operations - error_count) / total_operations * 100
            return round(success_rate, 2)
            
        except Exception:
            return 0.0


# 创建全局实例
output_integration_node = OutputIntegrationNode()