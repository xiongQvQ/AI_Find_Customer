"""
增强版意图识别节点
使用LLM进行智能语义解析，支持复杂查询理解
"""

import json
import logging
import re
from typing import List, Optional
from pydantic import BaseModel, Field

from ..state import SearchState, update_state_with_intent, add_warning_to_state
from ..llm.llm_client import get_llm_client


class SearchQuery(BaseModel):
    """结构化搜索查询"""
    intent: str = Field(..., description="搜索意图: company, employee, composite")
    location: Optional[str] = Field(None, description="地理位置: 深圳, 北京, California等")
    industry: Optional[str] = Field(None, description="行业领域: 智能机器人, 新能源汽车等")
    company_type: Optional[str] = Field(None, description="公司类型: 创业公司, 上市公司, 制造商等")
    company_size: Optional[str] = Field(None, description="公司规模: 初创, 中型, 大型等")
    target_position: Optional[str] = Field(None, description="目标职位: CTO, 销售总监, 技术经理等")
    department: Optional[str] = Field(None, description="部门: 技术部, 销售部, 市场部等")
    specific_company: Optional[str] = Field(None, description="特定公司名称")
    keywords: List[str] = Field(default=[], description="其他关键词")
    confidence: float = Field(default=0.0, description="解析置信度 0-1")


class EnhancedIntentRecognitionNode:
    """
    增强版意图识别节点
    
    使用LLM进行智能语义解析，能够：
    1. 从自然语言中提取结构化信息
    2. 识别复杂搜索意图和策略
    3. 支持多种搜索模式的组合
    4. 提供高置信度的解析结果
    """
    
    def __init__(self):
        """初始化增强版意图识别器"""
        self.logger = logging.getLogger(__name__)
        self.llm_client = get_llm_client()
        
        # 搜索意图分类提示词
        self.intent_prompt = """
你是一个专业的搜索意图分析师。请分析用户的查询并提取结构化信息。

搜索意图类型：
- company: 纯公司搜索（找公司信息、公司列表等）
- employee: 纯员工搜索（找特定公司的员工）
- composite: 复合搜索（找某类公司的某些员工）

用户查询: "{query}"

请提取以下信息并以JSON格式返回：
{{
    "intent": "company|employee|composite",
    "location": "地理位置（如：深圳、北京、California）",
    "industry": "行业领域（如：智能机器人、新能源汽车）",
    "company_type": "公司类型（如：创业公司、上市公司、制造商）",
    "company_size": "公司规模（如：初创、中型、大型）",
    "target_position": "目标职位（如：CTO、销售总监）",
    "department": "部门（如：技术部、销售部）",
    "specific_company": "特定公司名称",
    "keywords": ["其他相关关键词"],
    "confidence": 0.95
}}

分析要求：
1. 准确识别搜索意图类型
2. 尽可能提取所有有用信息
3. 对于模糊或不确定的信息，设置为null
4. 设置合理的置信度分数
5. 只返回JSON，不要其他解释

示例：
查询："深圳的智能机器人创业公司"
{{
    "intent": "company",
    "location": "深圳",
    "industry": "智能机器人",
    "company_type": "创业公司",
    "company_size": "初创",
    "target_position": null,
    "department": null,
    "specific_company": null,
    "keywords": ["机器人", "AI", "人工智能"],
    "confidence": 0.92
}}

查询："腾讯的技术总监联系方式"
{{
    "intent": "employee",
    "location": null,
    "industry": "互联网",
    "company_type": "大型科技公司",
    "company_size": "大型",
    "target_position": "技术总监",
    "department": "技术部",
    "specific_company": "腾讯",
    "keywords": ["联系方式", "CTO"],
    "confidence": 0.95
}}

查询："北京新能源汽车公司的销售经理"
{{
    "intent": "composite",
    "location": "北京",
    "industry": "新能源汽车",
    "company_type": null,
    "company_size": null,
    "target_position": "销售经理",
    "department": "销售部",
    "specific_company": null,
    "keywords": ["电动汽车", "汽车制造"],
    "confidence": 0.88
}}
"""
    
    def analyze_query_with_llm(self, query: str) -> SearchQuery:
        """
        使用LLM分析用户查询
        
        Args:
            query: 用户查询字符串
            
        Returns:
            结构化的搜索查询对象
        """
        try:
            # 构建提示词
            prompt = self.intent_prompt.format(query=query)
            
            # 调用LLM
            response = self.llm_client.generate_response(
                prompt=prompt,
                temperature=0.1,  # 低温度确保稳定输出
                max_tokens=500
            )
            
            # 解析JSON响应
            response_text = response.strip()
            
            # 提取JSON部分（处理可能的前后文本）
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
            else:
                json_str = response_text
            
            # 解析为结构化对象
            parsed_data = json.loads(json_str)
            search_query = SearchQuery(**parsed_data)
            
            self.logger.info(f"LLM解析成功，置信度: {search_query.confidence}")
            return search_query
            
        except json.JSONDecodeError as e:
            self.logger.error(f"LLM响应JSON解析失败: {e}, 响应内容: {response_text}")
            return self._fallback_analysis(query)
        except Exception as e:
            self.logger.error(f"LLM调用失败: {e}")
            return self._fallback_analysis(query)
    
    def _fallback_analysis(self, query: str) -> SearchQuery:
        """
        当LLM失败时的备用解析方法
        """
        self.logger.warning("使用备用解析方法")
        
        # 简单意图判断
        if any(kw in query for kw in ["员工", "经理", "总监", "联系人", "employee", "manager"]):
            if any(kw in query for kw in ["公司", "企业", "company"]):
                intent = "composite"
            else:
                intent = "employee"
        else:
            intent = "company"
        
        # 提取基本信息
        location = self._extract_location(query)
        industry = self._extract_industry(query)
        
        return SearchQuery(
            intent=intent,
            location=location,
            industry=industry,
            confidence=0.5  # 低置信度表示备用方法
        )
    
    def _extract_location(self, query: str) -> Optional[str]:
        """提取地理位置信息"""
        locations = ["北京", "上海", "深圳", "广州", "杭州", "成都", "南京", "武汉", "西安", "天津"]
        for loc in locations:
            if loc in query:
                return loc
        return None
    
    def _extract_industry(self, query: str) -> Optional[str]:
        """提取行业信息"""
        industries = {
            "智能机器人": ["机器人", "智能", "AI", "人工智能"],
            "新能源汽车": ["新能源", "电动汽车", "汽车"],
            "生物医药": ["生物", "医药", "制药"],
            "互联网": ["互联网", "软件", "IT", "科技"]
        }
        
        for industry, keywords in industries.items():
            if any(kw in query for kw in keywords):
                return industry
        return None
    
    def execute(self, state: SearchState) -> SearchState:
        """
        执行增强版意图识别节点
        
        Args:
            state: 当前状态
            
        Returns:
            更新后的状态
        """
        try:
            self.logger.info("开始执行增强版意图识别")
            
            # 从状态获取用户查询
            user_query = state["user_query"]
            
            # 使用LLM进行智能解析
            search_query = self.analyze_query_with_llm(user_query)
            
            # 更新搜索参数
            search_params = state["search_params"]
            if search_query.location:
                search_params.region = search_query.location
            if search_query.industry:
                search_params.industry = search_query.industry
            if search_query.target_position:
                search_params.position = search_query.target_position
            if search_query.company_size:
                search_params.company_size = search_query.company_size
            
            # 构建推理过程
            reasoning = f"""
智能意图分析结果:
- 搜索意图: {search_query.intent}
- 地理位置: {search_query.location or '未指定'}
- 行业领域: {search_query.industry or '未指定'}
- 公司类型: {search_query.company_type or '未指定'}
- 目标职位: {search_query.target_position or '未指定'}
- 特定公司: {search_query.specific_company or '未指定'}
- 关键词: {', '.join(search_query.keywords) if search_query.keywords else '无'}
- 解析置信度: {search_query.confidence:.2f}

搜索策略建议:
"""
            if search_query.intent == "company":
                reasoning += "- 执行公司搜索，重点关注行业和地理位置筛选"
            elif search_query.intent == "employee":
                reasoning += "- 执行员工搜索，需要先确定目标公司"
            elif search_query.intent == "composite":
                reasoning += "- 执行复合搜索：先搜索匹配的公司，然后搜索这些公司的目标员工"
            
            # 更新状态
            state = update_state_with_intent(state, search_query.intent, search_query.confidence, reasoning)
            state["current_node"] = "enhanced_intent_recognition"
            state["workflow_path"].append("enhanced_intent_recognition_completed")
            
            # 存储解析的结构化信息
            state["parsed_query"] = search_query.model_dump()
            
            # 添加警告（如果置信度较低）
            if search_query.confidence < 0.7:
                state = add_warning_to_state(
                    state,
                    "low_parsing_confidence",
                    f"意图解析置信度较低: {search_query.confidence:.2f}，建议用户提供更明确的查询",
                    "enhanced_intent_recognition"
                )
            
            self.logger.info(f"增强版意图识别完成，意图: {search_query.intent}, 置信度: {search_query.confidence:.2f}")
            return state
            
        except Exception as e:
            # 添加错误记录
            from ..state import add_error_to_state
            state = add_error_to_state(
                state,
                "enhanced_intent_recognition_error",
                f"增强版意图识别过程中出现错误: {str(e)}",
                "enhanced_intent_recognition"
            )
            
            # 默认设置
            state["detected_intent"] = "unknown"
            state["intent_confidence"] = 0.0
            state["intent_reasoning"] = f"错误: {str(e)}"
            
            return state


# 创建节点实例
enhanced_intent_recognition_node = EnhancedIntentRecognitionNode()