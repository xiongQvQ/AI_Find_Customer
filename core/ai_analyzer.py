"""
AI分析器核心模块
替代StreamlitCompatibleAIAnalyzer，提供公司和员工评估功能
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv

# 确保加载环境变量
load_dotenv()

# 延迟导入LLM客户端以避免循环导入

logger = logging.getLogger(__name__)

class AIAnalyzer:
    """AI分析器，用于评估公司和员工"""
    
    def __init__(self, provider: str = None, **kwargs):
        """初始化AI分析器"""
        # 兼容旧的参数格式，但实际使用环境变量中的配置
        self.llm_client = self._get_llm_client()
    
    def _get_llm_client(self):
        """延迟导入LLM客户端"""
        try:
            from langgraph_search.llm.llm_client import get_llm_client
            return get_llm_client()
        except ImportError:
            logger.warning("LangGraph LLM客户端不可用，使用基础实现")
            return None
        
    def evaluate_company(self, company_data: Dict[str, Any], criteria: str = "") -> Tuple[float, str]:
        """
        评估公司
        
        Args:
            company_data: 公司数据
            criteria: 评估标准
            
        Returns:
            (评分(0-100), 评分原因)
        """
        try:
            # 构建评估提示
            company_info = f"""
公司名称: {company_data.get('name', 'N/A')}
行业: {company_data.get('industry', 'N/A')}
描述: {company_data.get('description', 'N/A')}
网站: {company_data.get('website_url', 'N/A')}
LinkedIn: {company_data.get('linkedin_url', 'N/A')}
位置: {company_data.get('location', 'N/A')}
"""
            
            prompt = f"""
请对以下公司进行评估，给出0-100的评分和详细原因。

{company_info}

评估标准: {criteria if criteria else "综合评估公司的业务潜力、规模和可信度"}

请以JSON格式返回结果:
{{
    "ai_score": 评分(0-100的数值),
    "ai_reason": "详细的评估原因"
}}
"""
            
            response = self.llm_client.generate_response(prompt)
            
            # 尝试解析JSON响应
            try:
                result = json.loads(response)
                score = float(result.get("ai_score", 50.0))
                reason = result.get("ai_reason", "基础评估")
            except (json.JSONDecodeError, ValueError):
                # 如果解析失败，使用默认值
                score = 60.0
                reason = f"LLM评估: {response[:200]}..."
            
            # 确保评分在有效范围内
            score = max(0.0, min(100.0, score))
            
            return score, reason
            
        except Exception as e:
            logger.error(f"公司评估失败: {e}")
            return 50.0, f"评估出现错误: {str(e)}"
    
    def evaluate_employee(self, employee_data: Dict[str, Any], criteria: str = "") -> Tuple[float, str]:
        """
        评估员工
        
        Args:
            employee_data: 员工数据
            criteria: 评估标准
            
        Returns:
            (评分(0-100), 评分原因)
        """
        try:
            # 构建评估提示
            employee_info = f"""
员工姓名: {employee_data.get('name', 'N/A')}
职位: {employee_data.get('position', 'N/A')}
公司: {employee_data.get('company', 'N/A')}
LinkedIn: {employee_data.get('linkedin_url', 'N/A')}
位置: {employee_data.get('location', 'N/A')}
描述: {employee_data.get('description', 'N/A')}
"""
            
            prompt = f"""
请对以下员工进行评估，给出0-100的评分和详细原因。

{employee_info}

评估标准: {criteria if criteria else "综合评估员工的职位匹配度、影响力和联系价值"}

请以JSON格式返回结果:
{{
    "ai_score": 评分(0-100的数值),
    "ai_reason": "详细的评估原因"
}}
"""
            
            response = self.llm_client.generate_response(prompt)
            
            # 尝试解析JSON响应
            try:
                result = json.loads(response)
                score = float(result.get("ai_score", 50.0))
                reason = result.get("ai_reason", "基础评估")
            except (json.JSONDecodeError, ValueError):
                # 如果解析失败，使用默认值
                score = 60.0
                reason = f"LLM评估: {response[:200]}..."
            
            # 确保评分在有效范围内
            score = max(0.0, min(100.0, score))
            
            return score, reason
            
        except Exception as e:
            logger.error(f"员工评估失败: {e}")
            return 50.0, f"评估出现错误: {str(e)}"
    
    def batch_evaluate_companies(self, companies: List[Dict[str, Any]], 
                                criteria: str = "") -> List[Dict[str, Any]]:
        """
        批量评估公司
        
        Args:
            companies: 公司列表
            criteria: 评估标准
            
        Returns:
            添加了AI评估结果的公司列表
        """
        evaluated_companies = []
        
        for company in companies:
            try:
                score, reason = self.evaluate_company(company, criteria)
                
                # 添加AI评估结果
                company_with_ai = company.copy()
                company_with_ai['ai_score'] = score
                company_with_ai['ai_reason'] = reason
                company_with_ai['is_qualified'] = score >= 60.0  # 默认阈值
                
                evaluated_companies.append(company_with_ai)
                
            except Exception as e:
                logger.error(f"评估公司失败 {company.get('name', 'Unknown')}: {e}")
                # 添加默认评估
                company_with_ai = company.copy()
                company_with_ai['ai_score'] = 50.0
                company_with_ai['ai_reason'] = f"评估失败: {str(e)}"
                company_with_ai['is_qualified'] = False
                
                evaluated_companies.append(company_with_ai)
        
        return evaluated_companies
    
    def batch_evaluate_employees(self, employees: List[Dict[str, Any]], 
                               criteria: str = "") -> List[Dict[str, Any]]:
        """
        批量评估员工
        
        Args:
            employees: 员工列表
            criteria: 评估标准
            
        Returns:
            添加了AI评估结果的员工列表
        """
        evaluated_employees = []
        
        for employee in employees:
            try:
                score, reason = self.evaluate_employee(employee, criteria)
                
                # 添加AI评估结果
                employee_with_ai = employee.copy()
                employee_with_ai['ai_score'] = score
                employee_with_ai['ai_reason'] = reason
                employee_with_ai['is_qualified'] = score >= 70.0  # 员工阈值更高
                
                evaluated_employees.append(employee_with_ai)
                
            except Exception as e:
                logger.error(f"评估员工失败 {employee.get('name', 'Unknown')}: {e}")
                # 添加默认评估
                employee_with_ai = employee.copy()
                employee_with_ai['ai_score'] = 50.0
                employee_with_ai['ai_reason'] = f"评估失败: {str(e)}"
                employee_with_ai['is_qualified'] = False
                
                evaluated_employees.append(employee_with_ai)
        
        return evaluated_employees
    
    def is_available(self) -> bool:
        """检查AI分析器是否可用"""
        return self.llm_client is not None and self.llm_client.is_available()


# 兼容性别名，替代StreamlitCompatibleAIAnalyzer
StreamlitCompatibleAIAnalyzer = AIAnalyzer

# 全局实例
_global_ai_analyzer: Optional[AIAnalyzer] = None

def get_ai_analyzer() -> AIAnalyzer:
    """获取全局AI分析器实例"""
    global _global_ai_analyzer
    if _global_ai_analyzer is None:
        _global_ai_analyzer = AIAnalyzer()
    return _global_ai_analyzer