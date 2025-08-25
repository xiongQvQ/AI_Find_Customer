"""
意图识别节点
分析用户查询，识别搜索意图（公司搜索、员工搜索、复合搜索）
"""

import re
from typing import Dict, List, Tuple
from ..state import SearchState, SearchIntent, update_state_with_intent, add_warning_to_state

class IntentRecognitionNode:
    """
    意图识别节点
    
    负责分析用户查询，识别用户的搜索意图：
    - company: 纯公司搜索
    - employee: 纯员工搜索  
    - composite: 复合搜索（先找公司再找员工）
    - unknown: 意图不明确，需要澄清
    """
    
    def __init__(self):
        """初始化意图识别器，设置关键词和规则"""
        self.setup_keywords()
        self.setup_patterns()
    
    def setup_keywords(self):
        """设置意图识别关键词库"""
        # 公司相关关键词
        self.company_keywords = {
            # 中文关键词
            "中文": [
                "公司", "企业", "厂商", "供应商", "制造商", "服务商",
                "集团", "机构", "组织", "品牌", "商家", "厂家",
                "公司名单", "企业目录", "厂商信息"
            ],
            # 英文关键词  
            "英文": [
                "company", "companies", "business", "businesses",
                "corporation", "enterprise", "firm", "organization",
                "manufacturer", "supplier", "vendor", "provider",
                "startup", "company list", "business directory"
            ]
        }
        
        # 员工相关关键词
        self.employee_keywords = {
            # 中文关键词
            "中文": [
                "员工", "职员", "雇员", "人员", "人才", "专家",
                "经理", "总监", "CEO", "CTO", "销售", "市场",
                "联系人", "负责人", "决策者", "关键人物",
                "销售经理", "市场总监", "技术总监", "业务经理"
            ],
            # 英文关键词
            "英文": [
                "employee", "employees", "staff", "personnel", "people",
                "manager", "director", "executive", "officer", 
                "sales", "marketing", "technical", "business",
                "contact", "decision maker", "key person",
                "sales manager", "marketing director", "ceo", "cto"
            ]
        }
        
        # 职位层级关键词
        self.position_keywords = {
            # 高级管理层
            "high_level": [
                "CEO", "CTO", "CFO", "COO", "总裁", "董事", "总经理",
                "VP", "vice president", "副总裁", "总监", "director"
            ],
            # 中层管理
            "mid_level": [
                "manager", "经理", "主管", "supervisor", "team lead",
                "部门经理", "项目经理", "产品经理"
            ],
            # 特定部门
            "departments": [
                "sales", "销售", "marketing", "市场", "technical", "技术",
                "business", "商务", "procurement", "采购", "hr", "人事"
            ]
        }
        
        # 搜索动作词
        self.action_keywords = {
            "search": ["搜索", "查找", "寻找", "获取", "收集", "search", "find", "get", "collect"],
            "analyze": ["分析", "评估", "筛选", "analyze", "evaluate", "filter"],
            "contact": ["联系", "接触", "合作", "contact", "reach", "collaborate"]
        }
    
    def setup_patterns(self):
        """设置正则表达式模式"""
        # 复合搜索模式 - 同时包含公司和员工元素
        self.composite_patterns = [
            r"(\w+公司|企业).*(员工|经理|总监|联系人)",
            r"(员工|经理|总监|联系人).*(\w+公司|企业)",
            r"(\w+\s+companies?).*(employee|manager|director|contact)",
            r"(employee|manager|director|contact).*(\w+\s+companies?)",
            r"在.*公司.*工作.*的.*人",
            r"find.*people.*at.*companies?",
        ]
        
        # 明确的员工搜索模式
        self.employee_patterns = [
            r"找.*员工|搜索.*员工",
            r"find.*employee|search.*employee",
            r"联系人.*信息",
            r"contact.*information",
            r"销售.*经理|市场.*总监",
            r"sales.*manager|marketing.*director"
        ]
        
        # 明确的公司搜索模式  
        self.company_patterns = [
            r"找.*公司|搜索.*公司",
            r"find.*compan|search.*compan",
            r"公司.*名单|企业.*目录",
            r"company.*list|business.*directory",
            r"制造商|供应商|服务商",
            r"manufacturer|supplier|provider"
        ]
    
    def analyze_query(self, query: str) -> Tuple[SearchIntent, float, str]:
        """
        分析用户查询，返回意图识别结果
        
        Args:
            query: 用户查询字符串
            
        Returns:
            Tuple[意图, 置信度, 推理过程]
        """
        query_lower = query.lower()
        reasoning_steps = []
        scores = {
            "company": 0.0,
            "employee": 0.0,
            "composite": 0.0
        }
        
        # 1. 检查复合搜索模式
        composite_score, composite_reasoning = self._check_composite_patterns(query_lower)
        scores["composite"] = composite_score
        reasoning_steps.extend(composite_reasoning)
        
        # 2. 检查公司关键词
        company_score, company_reasoning = self._check_company_keywords(query_lower)
        scores["company"] = company_score
        reasoning_steps.extend(company_reasoning)
        
        # 3. 检查员工关键词
        employee_score, employee_reasoning = self._check_employee_keywords(query_lower)
        scores["employee"] = employee_score
        reasoning_steps.extend(employee_reasoning)
        
        # 4. 综合分析并决定意图
        intent, confidence, final_reasoning = self._determine_final_intent(scores, reasoning_steps)
        
        return intent, confidence, final_reasoning
    
    def _check_composite_patterns(self, query: str) -> Tuple[float, List[str]]:
        """检查复合搜索模式"""
        reasoning = []
        score = 0.0
        
        for pattern in self.composite_patterns:
            if re.search(pattern, query):
                score += 0.3
                reasoning.append(f"检测到复合搜索模式: {pattern}")
        
        # 检查是否同时包含公司和员工关键词
        has_company = any(kw in query for lang_kws in self.company_keywords.values() for kw in lang_kws)
        has_employee = any(kw in query for lang_kws in self.employee_keywords.values() for kw in lang_kws)
        
        if has_company and has_employee:
            score += 0.4
            reasoning.append("同时检测到公司和员工相关关键词")
        
        return min(score, 1.0), reasoning
    
    def _check_company_keywords(self, query: str) -> Tuple[float, List[str]]:
        """检查公司相关关键词"""
        reasoning = []
        score = 0.0
        
        # 检查关键词匹配
        for lang, keywords in self.company_keywords.items():
            matches = [kw for kw in keywords if kw in query]
            if matches:
                score += len(matches) * 0.1
                reasoning.append(f"检测到{lang}公司关键词: {matches}")
        
        # 检查明确的公司搜索模式
        for pattern in self.company_patterns:
            if re.search(pattern, query):
                score += 0.2
                reasoning.append(f"匹配公司搜索模式: {pattern}")
        
        return min(score, 1.0), reasoning
    
    def _check_employee_keywords(self, query: str) -> Tuple[float, List[str]]:
        """检查员工相关关键词"""
        reasoning = []
        score = 0.0
        
        # 检查员工关键词匹配
        for lang, keywords in self.employee_keywords.items():
            matches = [kw for kw in keywords if kw in query]
            if matches:
                score += len(matches) * 0.1
                reasoning.append(f"检测到{lang}员工关键词: {matches}")
        
        # 检查职位层级关键词
        for level, keywords in self.position_keywords.items():
            matches = [kw for kw in keywords if kw in query]
            if matches:
                score += len(matches) * 0.15
                reasoning.append(f"检测到{level}职位关键词: {matches}")
        
        # 检查明确的员工搜索模式
        for pattern in self.employee_patterns:
            if re.search(pattern, query):
                score += 0.2
                reasoning.append(f"匹配员工搜索模式: {pattern}")
        
        return min(score, 1.0), reasoning
    
    def _determine_final_intent(self, scores: Dict[str, float], reasoning_steps: List[str]) -> Tuple[SearchIntent, float, str]:
        """根据分数确定最终意图"""
        
        # 获取最高分意图
        max_score = max(scores.values())
        best_intents = [intent for intent, score in scores.items() if score == max_score]
        
        # 构建推理过程
        reasoning = "\n".join(reasoning_steps)
        reasoning += f"\n\n评分结果: {scores}"
        
        # 意图决策逻辑
        if max_score < 0.3:
            # 分数太低，意图不明确
            return "unknown", max_score, reasoning + f"\n\n决策: 所有意图分数过低({max_score:.2f}), 需要澄清用户意图"
        
        elif scores["composite"] >= 0.5:
            # 复合搜索分数较高
            return "composite", scores["composite"], reasoning + f"\n\n决策: 复合搜索意图明确(分数: {scores['composite']:.2f})"
        
        elif len(best_intents) > 1:
            # 多个意图分数相同，优先级处理
            if "composite" in best_intents:
                return "composite", max_score, reasoning + f"\n\n决策: 多个意图分数相同，选择复合搜索(分数: {max_score:.2f})"
            elif "employee" in best_intents:
                return "employee", max_score, reasoning + f"\n\n决策: 多个意图分数相同，选择员工搜索(分数: {max_score:.2f})"
            else:
                return "company", max_score, reasoning + f"\n\n决策: 多个意图分数相同，选择公司搜索(分数: {max_score:.2f})"
        
        else:
            # 单一最高分意图
            best_intent = best_intents[0]
            return best_intent, max_score, reasoning + f"\n\n决策: {best_intent}搜索意图明确(分数: {max_score:.2f})"
    
    def execute(self, state: SearchState) -> SearchState:
        """
        执行意图识别节点
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            # 从状态获取用户查询
            user_query = state["user_query"]
            
            # 执行意图分析
            intent, confidence, reasoning = self.analyze_query(user_query)
            
            # 更新状态
            state = update_state_with_intent(state, intent, confidence, reasoning)
            state["current_node"] = "intent_recognition"
            
            # 添加执行记录
            state["workflow_path"].append("intent_recognition_completed")
            
            # 如果置信度较低，添加警告
            if confidence < 0.5:
                state = add_warning_to_state(
                    state,
                    "low_confidence",
                    f"意图识别置信度较低: {confidence:.2f}",
                    "intent_recognition"
                )
            
            return state
            
        except Exception as e:
            # 添加错误记录
            from ..state import add_error_to_state
            state = add_error_to_state(
                state,
                "intent_recognition_error",
                f"意图识别过程中出现错误: {str(e)}",
                "intent_recognition"
            )
            # 默认设置为unknown意图
            state["detected_intent"] = "unknown"
            state["intent_confidence"] = 0.0
            state["intent_reasoning"] = f"错误: {str(e)}"
            
            return state

# 创建节点实例
intent_recognition_node = IntentRecognitionNode()