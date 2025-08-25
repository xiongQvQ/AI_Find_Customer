"""
意图澄清节点
当意图识别置信度低或用户查询模糊时，提供澄清建议和搜索优化建议
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..state import SearchState, add_warning_to_state, SearchParams

class ClarificationNode:
    """
    意图澄清节点
    
    负责处理模糊查询和低置信度意图识别：
    - 分析用户查询的模糊点
    - 生成澄清问题和建议
    - 提供搜索优化建议
    - 支持查询重新构建
    """
    
    def __init__(self):
        """初始化澄清节点"""
        self.logger = logging.getLogger(__name__)
        
    def execute(self, state: SearchState) -> SearchState:
        """
        执行意图澄清
        
        Args:
            state: 当前搜索状态
            
        Returns:
            更新后的状态
        """
        try:
            self.logger.info("开始执行意图澄清")
            
            # 更新当前节点
            state["current_node"] = "clarification"
            state["workflow_path"].append("clarification_started")
            
            # 分析澄清需求
            clarification_needs = self._analyze_clarification_needs(state)
            
            # 生成澄清建议
            suggestions = self._generate_clarification_suggestions(state, clarification_needs)
            
            # 生成搜索优化建议
            optimization_suggestions = self._generate_search_optimization_suggestions(state)
            
            # 生成查询重写建议
            query_rewrites = self._generate_query_rewrites(state)
            
            # 将建议添加到状态中
            state["clarification_data"] = {
                "needs": clarification_needs,
                "suggestions": suggestions,
                "optimization_suggestions": optimization_suggestions,
                "query_rewrites": query_rewrites,
                "confidence_issues": self._identify_confidence_issues(state),
                "timestamp": datetime.now().isoformat()
            }
            
            state["workflow_path"].append("clarification_completed")
            
            self.logger.info("意图澄清完成")
            return state
            
        except Exception as e:
            self.logger.error(f"意图澄清过程中发生错误: {e}")
            state = add_warning_to_state(
                state,
                "clarification_error",
                f"澄清过程异常: {str(e)}",
                "clarification"
            )
            return state
    
    def _analyze_clarification_needs(self, state: SearchState) -> Dict[str, Any]:
        """分析澄清需求"""
        needs = {
            "intent_unclear": False,
            "parameters_missing": False,
            "scope_ambiguous": False,
            "criteria_undefined": False
        }
        
        # 检查意图清晰度
        if state["intent_confidence"] < 0.5:
            needs["intent_unclear"] = True
        
        # 检查参数完整性
        search_params = state["search_params"]
        if not search_params.industry and not search_params.position:
            needs["parameters_missing"] = True
        
        # 检查范围明确性
        if not search_params.region and not search_params.gl:
            needs["scope_ambiguous"] = True
        
        # 检查评估标准
        if not state["evaluation_criteria"]:
            needs["criteria_undefined"] = True
            
        return needs
    
    def _generate_clarification_suggestions(self, state: SearchState, needs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成澄清建议"""
        suggestions = []
        user_query = state["user_query"]
        
        if needs["intent_unclear"]:
            suggestions.append({
                "type": "intent_clarification",
                "title": "明确搜索目标",
                "questions": [
                    "您是想要寻找目标公司还是寻找特定职位的员工？",
                    "您的搜索主要目的是什么？(找客户、找供应商、找合作伙伴、招聘等)"
                ],
                "options": [
                    {"label": "寻找目标公司", "value": "company"},
                    {"label": "寻找员工/联系人", "value": "employee"},
                    {"label": "两者都需要", "value": "composite"}
                ]
            })
        
        if needs["parameters_missing"]:
            suggestions.append({
                "type": "parameter_enhancement",
                "title": "完善搜索条件",
                "questions": [
                    "请提供更具体的行业关键词",
                    "是否有特定的职位或角色要求？"
                ],
                "examples": {
                    "industry": ["科技公司", "制造业", "金融服务", "电商平台"],
                    "position": ["销售经理", "采购总监", "技术负责人", "市场专员"]
                }
            })
        
        if needs["scope_ambiguous"]:
            suggestions.append({
                "type": "scope_clarification", 
                "title": "明确搜索范围",
                "questions": [
                    "您希望搜索哪个地区的公司？",
                    "有特定的国家或城市要求吗？"
                ],
                "options": [
                    {"label": "中国大陆", "value": "cn"},
                    {"label": "美国", "value": "us"},
                    {"label": "欧洲", "value": "eu"},
                    {"label": "全球", "value": "global"}
                ]
            })
        
        if needs["criteria_undefined"]:
            suggestions.append({
                "type": "criteria_definition",
                "title": "定义评估标准",
                "questions": [
                    "什么样的公司是您的理想目标？",
                    "评估员工时您最看重什么？"
                ],
                "criteria_templates": {
                    "company": ["公司规模", "年营收", "行业地位", "创新能力"],
                    "employee": ["工作经验", "技能匹配", "职位级别", "所在公司"]
                }
            })
            
        return suggestions
    
    def _generate_search_optimization_suggestions(self, state: SearchState) -> List[Dict[str, str]]:
        """生成搜索优化建议"""
        suggestions = []
        user_query = state["user_query"]
        
        # 关键词优化建议
        if len(user_query.split()) < 3:
            suggestions.append({
                "type": "keyword_enhancement",
                "title": "增加关键词",
                "description": "建议添加更多描述性关键词来提高搜索精确度",
                "example": f"将 '{user_query}' 扩展为 '{user_query} [地区] [规模] [具体行业]'"
            })
        
        # 语言建议
        if any(char > '\u4e00' and char < '\u9fff' for char in user_query):
            suggestions.append({
                "type": "language_optimization",
                "title": "尝试英文关键词",
                "description": "使用英文关键词可能会获得更多国际化搜索结果",
                "example": "例如：'科技公司' → 'technology company'"
            })
        
        # 搜索策略建议
        suggestions.append({
            "type": "strategy_suggestion",
            "title": "搜索策略建议",
            "description": "建议分步骤搜索：先搜索目标公司，再搜索关键联系人",
            "steps": ["1. 确定目标行业和地区", "2. 搜索相关公司", "3. 评估公司匹配度", "4. 搜索关键决策者"]
        })
        
        return suggestions
    
    def _generate_query_rewrites(self, state: SearchState) -> List[Dict[str, str]]:
        """生成查询重写建议"""
        user_query = state["user_query"]
        rewrites = []
        
        # 基于意图的重写
        intent = state["detected_intent"]
        if intent == "unknown":
            rewrites.extend([
                {
                    "type": "company_focused",
                    "query": f"寻找 {user_query} 相关的公司",
                    "description": "专注于公司搜索"
                },
                {
                    "type": "employee_focused", 
                    "query": f"寻找 {user_query} 领域的专业人员",
                    "description": "专注于人员搜索"
                }
            ])
        
        # 结构化查询建议
        rewrites.append({
            "type": "structured",
            "query": self._create_structured_query(user_query),
            "description": "结构化查询，包含行业、地区、职位信息"
        })
        
        # 具体化查询建议
        rewrites.append({
            "type": "specific",
            "query": self._create_specific_query(user_query),
            "description": "更具体的查询，减少歧义"
        })
        
        return rewrites
    
    def _create_structured_query(self, original_query: str) -> str:
        """创建结构化查询"""
        # 这里可以使用NLP技术来提取关键信息并重组
        # 暂时使用简单的模板
        return f"行业:[请填写] 地区:[请填写] 职位:[请填写] - 基于 '{original_query}'"
    
    def _create_specific_query(self, original_query: str) -> str:
        """创建具体化查询"""
        # 添加常见的限定词
        if "公司" not in original_query and "企业" not in original_query:
            return f"{original_query} 公司"
        return f"{original_query} 详细信息"
    
    def _identify_confidence_issues(self, state: SearchState) -> List[Dict[str, Any]]:
        """识别置信度问题"""
        issues = []
        
        confidence = state["intent_confidence"]
        if confidence < 0.3:
            issues.append({
                "severity": "high",
                "issue": "意图识别置信度过低",
                "description": f"当前置信度: {confidence:.2f}，建议重新描述查询需求",
                "suggestions": [
                    "使用更清晰的描述",
                    "添加具体的行业或职位关键词",
                    "明确说明搜索目的"
                ]
            })
        elif confidence < 0.7:
            issues.append({
                "severity": "medium", 
                "issue": "意图识别不够确定",
                "description": f"当前置信度: {confidence:.2f}，可能需要进一步明确",
                "suggestions": [
                    "确认搜索目标是否正确",
                    "考虑添加更多上下文信息"
                ]
            })
        
        return issues

# 创建节点实例
clarification_node = ClarificationNode()