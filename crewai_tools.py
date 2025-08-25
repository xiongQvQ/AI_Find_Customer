#!/usr/bin/env python3
"""
CrewAI工具封装 - Serper API和LLM分析系统
为CrewAI智能体提供搜索和分析能力
"""

import os
import json
import time
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# 导入现有的核心组件
from core.company_search import CompanySearcher
from integration_guide import AIAnalyzerManager

# 加载环境变量
load_dotenv()

# 为了兼容性，创建一个简单的BaseTool基类
class BaseTool:
    """简单的工具基类，兼容CrewAI接口"""
    name: str = ""
    description: str = ""
    
    def _run(self, *args, **kwargs):
        """工具执行方法，子类需要重写"""
        raise NotImplementedError("Subclasses must implement _run method")

class SearchTools:
    """搜索工具集合"""
    
    @staticmethod
    def company_search_tool():
        """公司搜索工具"""
        
        class CompanySearchTool(BaseTool):
            name: str = "company_search"
            description: str = """
            搜索目标公司的工具。支持两种搜索模式：
            1. general: 通用Google搜索
            2. linkedin: LinkedIn公司专页搜索
            
            输入参数：
            - search_mode: 搜索模式 ('general' 或 'linkedin')
            - industry: 行业关键词 (可选)
            - region: 地区 (可选) 
            - keywords: 额外关键词列表 (可选)
            - custom_query: 自定义搜索查询 (可选，仅general模式)
            - gl: 地理位置代码 (默认 'us')
            - num_results: 结果数量 (默认 20)
            
            返回：包含搜索结果的字典，包含success、data、error字段
            """
            
            def _run(self, **kwargs) -> Dict[str, Any]:
                try:
                    searcher = CompanySearcher()
                    
                    # 提取参数，设置默认值
                    search_mode = kwargs.get('search_mode', 'general')
                    industry = kwargs.get('industry')
                    region = kwargs.get('region')
                    keywords = kwargs.get('keywords', [])
                    custom_query = kwargs.get('custom_query')
                    gl = kwargs.get('gl', 'us')
                    num_results = kwargs.get('num_results', 20)
                    
                    # 确保keywords是列表
                    if isinstance(keywords, str):
                        keywords = [keywords]
                    elif keywords is None:
                        keywords = []
                    
                    # 执行搜索
                    result = searcher.search_companies(
                        search_mode=search_mode,
                        industry=industry,
                        region=region,
                        custom_query=custom_query,
                        keywords=keywords,
                        gl=gl,
                        num_results=num_results
                    )
                    
                    return result
                    
                except Exception as e:
                    return {
                        "success": False,
                        "data": [],
                        "error": f"搜索失败: {str(e)}",
                        "output_file": None
                    }
        
        return CompanySearchTool()
    
    @staticmethod
    def keyword_generator_tool():
        """关键词生成工具"""
        
        class KeywordGeneratorTool(BaseTool):
            name: str = "keyword_generator"
            description: str = """
            根据用户需求生成搜索关键词的工具。
            
            输入参数：
            - user_requirement: 用户的原始需求描述
            - max_keywords: 最大关键词数量 (默认 5)
            
            返回：生成的关键词列表和搜索策略
            """
            
            def _run(self, user_requirement: str, max_keywords: int = 5) -> Dict[str, Any]:
                try:
                    # 这里使用简单的关键词提取逻辑
                    # 在实际应用中，可以集成更复杂的NLP处理
                    
                    # 基础关键词映射
                    keyword_mapping = {
                        "数位板": ["digital tablet", "graphics tablet", "drawing tablet"],
                        "太阳能": ["solar panel", "solar energy", "photovoltaic"],
                        "软件开发": ["software development", "programming", "coding"],
                        "制造": ["manufacturing", "production", "factory"],
                        "贸易": ["trading", "import export", "commerce"],
                        "电子": ["electronics", "electronic components", "semiconductor"],
                        "机械": ["machinery", "mechanical", "equipment"],
                        "化工": ["chemical", "chemicals", "chemical industry"]
                    }
                    
                    # 提取关键词
                    extracted_keywords = []
                    requirement_lower = user_requirement.lower()
                    
                    for chinese_term, english_keywords in keyword_mapping.items():
                        if chinese_term in requirement_lower:
                            extracted_keywords.extend(english_keywords[:2])  # 限制每个概念最多2个关键词
                    
                    # 如果没有匹配到预定义关键词，使用原始需求的关键部分
                    if not extracted_keywords:
                        # 简单的中文分词逻辑
                        words = user_requirement.replace('，', ' ').replace('。', ' ').split()
                        extracted_keywords = [word for word in words if len(word) > 1][:max_keywords]
                    
                    # 限制关键词数量
                    final_keywords = extracted_keywords[:max_keywords]
                    
                    return {
                        "success": True,
                        "keywords": final_keywords,
                        "original_requirement": user_requirement,
                        "extraction_method": "keyword_mapping" if extracted_keywords else "simple_split"
                    }
                    
                except Exception as e:
                    return {
                        "success": False,
                        "keywords": [],
                        "error": f"关键词生成失败: {str(e)}"
                    }
        
        return KeywordGeneratorTool()


class AnalysisTools:
    """分析工具集合"""
    
    @staticmethod 
    def requirement_parser_tool():
        """需求解析工具"""
        
        class RequirementParserTool(BaseTool):
            name: str = "requirement_parser" 
            description: str = """
            解析用户需求，提取产品、规格、价格、地区等结构化信息。
            
            输入参数：
            - user_requirement: 用户的原始需求描述
            
            返回：结构化的需求信息
            """
            
            def _run(self, user_requirement: str) -> Dict[str, Any]:
                try:
                    # 基础的需求解析逻辑
                    parsed_requirement = {
                        "product": "",
                        "specifications": [],
                        "price_range": {
                            "min": None,
                            "max": None,
                            "currency": "RMB"
                        },
                        "location": {
                            "city": None,
                            "province": None,
                            "country": "中国"
                        },
                        "company_size": "不限",
                        "priority_factors": [],
                        "confidence_score": 0.8,
                        "missing_info": [],
                        "original_text": user_requirement
                    }
                    
                    requirement_lower = user_requirement.lower()
                    
                    # 提取产品信息
                    product_keywords = ["数位板", "太阳能板", "软件", "设备", "产品", "服务"]
                    for keyword in product_keywords:
                        if keyword in user_requirement:
                            parsed_requirement["product"] = keyword
                            break
                    
                    # 提取价格信息
                    import re
                    price_pattern = r'(\d+)-(\d+)元'
                    price_match = re.search(price_pattern, user_requirement)
                    if price_match:
                        parsed_requirement["price_range"]["min"] = int(price_match.group(1))
                        parsed_requirement["price_range"]["max"] = int(price_match.group(2))
                    
                    # 提取地区信息
                    cities = ["北京", "上海", "深圳", "广州", "杭州", "成都", "武汉", "西安"]
                    for city in cities:
                        if city in user_requirement:
                            parsed_requirement["location"]["city"] = city
                            break
                    
                    # 提取规格要求
                    spec_keywords = ["4K", "高清", "分辨率", "尺寸", "功率", "效率"]
                    for keyword in spec_keywords:
                        if keyword in user_requirement:
                            parsed_requirement["specifications"].append(keyword)
                    
                    # 检查缺失信息
                    if not parsed_requirement["product"]:
                        parsed_requirement["missing_info"].append("产品类型")
                    if not parsed_requirement["location"]["city"]:
                        parsed_requirement["missing_info"].append("地理位置")
                    
                    return {
                        "success": True,
                        "parsed_requirement": parsed_requirement
                    }
                    
                except Exception as e:
                    return {
                        "success": False,
                        "parsed_requirement": {},
                        "error": f"需求解析失败: {str(e)}"
                    }
        
        return RequirementParserTool()
    
    @staticmethod
    def company_scorer_tool():
        """公司评分工具"""
        
        class CompanyScorerTool(BaseTool):
            name: str = "company_scorer"
            description: str = """
            根据用户需求对搜索到的公司进行智能评分。
            
            输入参数：
            - companies: 公司列表
            - target_profile: 目标需求描述
            - batch_size: 批处理大小 (默认 5)
            
            返回：评分后的公司列表
            """
            
            def _run(self, companies: List[Dict], target_profile: str, batch_size: int = 5) -> Dict[str, Any]:
                try:
                    if not companies:
                        return {
                            "success": True,
                            "scored_companies": [],
                            "total_processed": 0
                        }
                    
                    # 初始化AI分析器
                    analyzer = AIAnalyzerManager(
                        use_optimized=True,
                        max_concurrent=3,
                        enable_cache=True
                    )
                    
                    # 准备公司数据用于分析
                    companies_for_analysis = []
                    for company in companies:
                        company_data = {
                            'name': company.get('name', ''),
                            'description': company.get('description', ''),
                            'domain': company.get('domain', ''),
                            'linkedin': company.get('linkedin', ''),
                            'location': company.get('location', ''),
                            'industry': company.get('industry', '')
                        }
                        companies_for_analysis.append(company_data)
                    
                    # 执行批量分析
                    analyzed_results = analyzer.batch_analyze_companies(
                        companies_for_analysis, 
                        target_profile
                    )
                    
                    # 格式化结果
                    scored_companies = []
                    for result in analyzed_results:
                        scored_company = {
                            "company_name": result.get('company_name', ''),
                            "overall_score": result.get('final_score', 0),
                            "dimension_scores": {
                                "relevance": result.get('industry_match_score', 0) / 10,
                                "quality": result.get('company_scale_score', 0) / 10,
                                "match": result.get('business_model_score', 0) / 10
                            },
                            "match_reasons": result.get('strengths', []),
                            "concerns": result.get('concerns', []),
                            "confidence_level": "high" if result.get('final_score', 0) >= 8 else "medium" if result.get('final_score', 0) >= 6 else "low",
                            "analysis_summary": result.get('analysis_summary', ''),
                            "original_data": {
                                "name": result.get('company_name', ''),
                                "description": result.get('company_description', ''),
                                "domain": result.get('company_domain', ''),
                            }
                        }
                        scored_companies.append(scored_company)
                    
                    # 按分数排序
                    scored_companies.sort(key=lambda x: x['overall_score'], reverse=True)
                    
                    return {
                        "success": True,
                        "scored_companies": scored_companies,
                        "total_processed": len(scored_companies),
                        "avg_score": sum(c['overall_score'] for c in scored_companies) / len(scored_companies) if scored_companies else 0
                    }
                    
                except Exception as e:
                    return {
                        "success": False,
                        "scored_companies": [],
                        "total_processed": 0,
                        "error": f"公司评分失败: {str(e)}"
                    }
        
        return CompanyScorerTool()
    
    @staticmethod
    def result_optimizer_tool():
        """结果优化工具"""
        
        class ResultOptimizerTool(BaseTool):
            name: str = "result_optimizer"
            description: str = """
            优化搜索结果，去重、排序、筛选最佳匹配。
            
            输入参数：
            - scored_companies: 已评分的公司列表
            - min_score: 最低分数阈值 (默认 6.0)
            - max_results: 最大结果数量 (默认 10)
            
            返回：优化后的公司列表
            """
            
            def _run(self, scored_companies: List[Dict], min_score: float = 6.0, max_results: int = 10) -> Dict[str, Any]:
                try:
                    if not scored_companies:
                        return {
                            "success": True,
                            "optimized_results": [],
                            "optimization_summary": {
                                "original_count": 0,
                                "after_deduplication": 0,
                                "after_filtering": 0,
                                "final_count": 0
                            }
                        }
                    
                    original_count = len(scored_companies)
                    
                    # 1. 去重 (基于公司名称)
                    seen_names = set()
                    deduplicated = []
                    for company in scored_companies:
                        name = company.get('company_name', '').strip().lower()
                        if name and name not in seen_names:
                            seen_names.add(name)
                            deduplicated.append(company)
                    
                    after_deduplication = len(deduplicated)
                    
                    # 2. 分数过滤
                    filtered = [
                        company for company in deduplicated 
                        if company.get('overall_score', 0) >= min_score
                    ]
                    
                    after_filtering = len(filtered)
                    
                    # 3. 按分数排序
                    filtered.sort(key=lambda x: x.get('overall_score', 0), reverse=True)
                    
                    # 4. 限制结果数量
                    final_results = filtered[:max_results]
                    
                    # 5. 添加排名信息
                    for i, company in enumerate(final_results, 1):
                        company['rank'] = i
                        company['score_tier'] = (
                            'excellent' if company.get('overall_score', 0) >= 9 
                            else 'very_good' if company.get('overall_score', 0) >= 8
                            else 'good' if company.get('overall_score', 0) >= 7
                            else 'acceptable'
                        )
                    
                    optimization_summary = {
                        "original_count": original_count,
                        "after_deduplication": after_deduplication, 
                        "after_filtering": after_filtering,
                        "final_count": len(final_results),
                        "avg_score": sum(c.get('overall_score', 0) for c in final_results) / len(final_results) if final_results else 0,
                        "score_distribution": {
                            'excellent': len([c for c in final_results if c.get('overall_score', 0) >= 9]),
                            'very_good': len([c for c in final_results if 8 <= c.get('overall_score', 0) < 9]),
                            'good': len([c for c in final_results if 7 <= c.get('overall_score', 0) < 8]),
                            'acceptable': len([c for c in final_results if 6 <= c.get('overall_score', 0) < 7])
                        }
                    }
                    
                    return {
                        "success": True,
                        "optimized_results": final_results,
                        "optimization_summary": optimization_summary
                    }
                    
                except Exception as e:
                    return {
                        "success": False,
                        "optimized_results": [],
                        "optimization_summary": {},
                        "error": f"结果优化失败: {str(e)}"
                    }
        
        return ResultOptimizerTool()


# 工具实例化函数
def get_search_tools():
    """获取搜索工具集合"""
    return [
        SearchTools.company_search_tool(),
        SearchTools.keyword_generator_tool()
    ]

def get_analysis_tools():
    """获取分析工具集合"""
    return [
        AnalysisTools.requirement_parser_tool(),
        AnalysisTools.company_scorer_tool(),
        AnalysisTools.result_optimizer_tool()
    ]

def get_all_tools():
    """获取所有工具"""
    return get_search_tools() + get_analysis_tools()


if __name__ == "__main__":
    # 测试工具功能
    print("🧪 测试CrewAI工具...")
    
    # 测试关键词生成工具
    keyword_tool = SearchTools.keyword_generator_tool()
    test_requirement = "我想找卖数位板的公司，要求支持4K分辨率，价格1000-3000元，深圳地区"
    keywords_result = keyword_tool._run(user_requirement=test_requirement)
    print(f"关键词生成结果: {keywords_result}")
    
    # 测试需求解析工具
    parser_tool = AnalysisTools.requirement_parser_tool()
    parsing_result = parser_tool._run(user_requirement=test_requirement)
    print(f"需求解析结果: {parsing_result}")
    
    print("✅ CrewAI工具测试完成!")