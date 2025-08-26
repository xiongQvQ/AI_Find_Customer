"""
公司分析服务
使用LLM分析搜索结果中的公司信息
"""
import logging
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# 导入LLM关键词生成器
try:
    from core.llm_keyword_generator import get_keyword_generator
    LLM_AVAILABLE = True
except ImportError as e:
    print(f"警告: LLM模块不可用: {e}")
    LLM_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class CompanyAnalysis:
    """公司分析结果"""
    is_company: bool
    ai_score: float  # 0.0 - 1.0
    ai_reason: str
    relevance_score: float  # 0.0 - 1.0 与搜索关键词的相关性
    confidence: float  # 0.0 - 1.0 分析的置信度


class CompanyAnalyzer:
    """公司分析器类"""
    
    def __init__(self):
        """初始化公司分析器"""
        self.llm_generator = None
        self.llm_available = False
        
        if LLM_AVAILABLE:
            try:
                self.llm_generator = get_keyword_generator()
                self.llm_available = True
                logger.info("✅ 公司分析器初始化成功，LLM可用")
            except Exception as e:
                logger.error(f"❌ 公司分析器初始化失败: {e}")
                self.llm_available = False
        else:
            logger.warning("⚠️ LLM不可用，将使用基础分析逻辑")
    
    async def analyze_companies(
        self, 
        companies: List[Dict[str, Any]], 
        search_industry: str = None,
        search_region: str = None
    ) -> List[Dict[str, Any]]:
        """
        批量分析公司信息
        
        Args:
            companies: 公司信息列表
            search_industry: 搜索的行业关键词
            search_region: 搜索的地区关键词
            
        Returns:
            增强后的公司信息列表，包含分析结果
        """
        enhanced_companies = []
        
        logger.info(f"开始分析 {len(companies)} 家公司")
        
        for i, company in enumerate(companies):
            try:
                # 分析单个公司
                analysis = await self._analyze_single_company(
                    company, search_industry, search_region
                )
                
                # 增强公司信息
                enhanced_company = {
                    **company,
                    'is_company': analysis.is_company,
                    'ai_score': analysis.ai_score,
                    'ai_reason': analysis.ai_reason,
                    'relevance_score': analysis.relevance_score,
                    'analysis_confidence': analysis.confidence
                }
                
                enhanced_companies.append(enhanced_company)
                
                logger.info(f"分析进度: {i+1}/{len(companies)} - {company.get('name', '未知')} - 分数: {analysis.ai_score:.2f}")
                
            except Exception as e:
                logger.error(f"分析公司失败 {company.get('name', '未知')}: {e}")
                # 使用基础分析作为回退
                fallback_analysis = self._basic_company_analysis(company, search_industry)
                enhanced_company = {
                    **company,
                    'is_company': fallback_analysis.is_company,
                    'ai_score': fallback_analysis.ai_score,
                    'ai_reason': fallback_analysis.ai_reason,
                    'relevance_score': fallback_analysis.relevance_score,
                    'analysis_confidence': 0.3  # 基础分析置信度较低
                }
                enhanced_companies.append(enhanced_company)
        
        logger.info(f"公司分析完成，共分析 {len(enhanced_companies)} 家公司")
        return enhanced_companies
    
    async def _analyze_single_company(
        self, 
        company: Dict[str, Any], 
        search_industry: str = None,
        search_region: str = None
    ) -> CompanyAnalysis:
        """分析单个公司"""
        
        if self.llm_available and self.llm_generator:
            return await self._llm_analyze_company(company, search_industry, search_region)
        else:
            return self._basic_company_analysis(company, search_industry)
    
    async def _llm_analyze_company(
        self, 
        company: Dict[str, Any], 
        search_industry: str = None,
        search_region: str = None
    ) -> CompanyAnalysis:
        """使用LLM分析公司"""
        
        # 构建分析prompt
        prompt = self._build_analysis_prompt(company, search_industry, search_region)
        
        try:
            # 调用LLM分析
            if hasattr(self.llm_generator, 'analyze_company'):
                response = await self.llm_generator.analyze_company(prompt)
            else:
                # 使用通用生成方法
                response = await self.llm_generator.generate_keywords(
                    industry="公司分析",
                    region="",
                    gl="",
                    custom_prompt=prompt
                )
            
            # 解析LLM响应
            return self._parse_llm_response(response, company)
            
        except Exception as e:
            logger.error(f"LLM分析失败: {e}")
            # 回退到基础分析
            return self._basic_company_analysis(company, search_industry)
    
    def _build_analysis_prompt(
        self, 
        company: Dict[str, Any], 
        search_industry: str = None,
        search_region: str = None
    ) -> str:
        """构建分析prompt"""
        
        company_name = company.get('name', '未知公司')
        company_desc = company.get('description', '无描述')
        company_website = company.get('website_url', '')
        company_location = company.get('location', '')
        
        prompt = f"""
请分析以下公司信息，判断这是否是一个真实的公司，以及它与搜索条件的相关性。

公司信息：
- 公司名称: {company_name}
- 描述: {company_desc}
- 网站: {company_website}
- 位置: {company_location}

搜索条件：
- 目标行业: {search_industry or '未指定'}
- 目标地区: {search_region or '未指定'}

请从以下几个维度进行分析并返回JSON格式结果：

1. is_company: 这是否是一个真实的公司/企业 (true/false)
2. ai_score: 综合评分 (0.0-1.0, 1.0表示最符合搜索条件)
3. relevance_score: 与搜索行业的相关性 (0.0-1.0)
4. confidence: 分析置信度 (0.0-1.0)
5. reason: 分析理由 (简要说明判断依据)

返回格式：
{{
    "is_company": true/false,
    "ai_score": 0.85,
    "relevance_score": 0.90,
    "confidence": 0.95,
    "reason": "这是一家专业的新能源汽车公司，与搜索的行业高度相关，有明确的业务描述和官方网站"
}}
"""
        return prompt
    
    def _parse_llm_response(self, response: Any, company: Dict[str, Any]) -> CompanyAnalysis:
        """解析LLM响应"""
        try:
            # 尝试解析JSON响应
            if isinstance(response, dict):
                result = response
            elif isinstance(response, str):
                # 尝试从字符串中提取JSON
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    raise ValueError("无法找到JSON格式的响应")
            else:
                raise ValueError(f"未知的响应格式: {type(response)}")
            
            return CompanyAnalysis(
                is_company=result.get('is_company', True),
                ai_score=max(0.0, min(1.0, result.get('ai_score', 0.5))),
                ai_reason=result.get('reason', '基于LLM分析'),
                relevance_score=max(0.0, min(1.0, result.get('relevance_score', 0.5))),
                confidence=max(0.0, min(1.0, result.get('confidence', 0.7)))
            )
            
        except Exception as e:
            logger.error(f"解析LLM响应失败: {e}, 响应: {response}")
            # 回退到基础分析
            return self._basic_company_analysis(company, None)
    
    def _basic_company_analysis(self, company: Dict[str, Any], search_industry: str = None) -> CompanyAnalysis:
        """基础分析逻辑"""
        
        company_name = company.get('name', '').lower()
        company_desc = company.get('description', '').lower()
        company_website = company.get('website_url', '')
        
        # 基础公司判断
        is_company = True
        
        # 排除明显不是公司的结果
        exclude_patterns = [
            'individual', 'personal', 'freelancer', 'consultant',
            '个人', '个体', '自由职业', '顾问'
        ]
        
        if any(pattern in company_name or pattern in company_desc for pattern in exclude_patterns):
            is_company = False
        
        # 基础评分逻辑
        score = 0.5  # 基础分数
        
        # 有网站加分
        if company_website:
            score += 0.2
        
        # 有详细描述加分
        if len(company_desc) > 50:
            score += 0.1
            
        # 行业相关性
        relevance_score = 0.5
        if search_industry:
            industry_lower = search_industry.lower()
            if industry_lower in company_name or industry_lower in company_desc:
                relevance_score = 0.8
                score += 0.2
        
        # 确保分数在合理范围内
        score = max(0.0, min(1.0, score))
        
        reason = f"基础分析: {'是' if is_company else '不是'}公司"
        if company_website:
            reason += ", 有官方网站"
        if search_industry and relevance_score > 0.6:
            reason += f", 与'{search_industry}'相关"
        
        return CompanyAnalysis(
            is_company=is_company,
            ai_score=score,
            ai_reason=reason,
            relevance_score=relevance_score,
            confidence=0.6  # 基础分析的置信度
        )


# 全局分析器实例
_company_analyzer = None

def get_company_analyzer() -> CompanyAnalyzer:
    """获取公司分析器实例"""
    global _company_analyzer
    if _company_analyzer is None:
        _company_analyzer = CompanyAnalyzer()
    return _company_analyzer