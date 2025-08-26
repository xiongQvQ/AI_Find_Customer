"""
智能搜索路由
基于自然语言的智能搜索API端点
"""
import logging
from typing import List
from fastapi import APIRouter, HTTPException, Query, Depends

from ..models.requests import IntelligentSearchRequest
from ..models.responses import IntelligentSearchResponse
from ..services.intelligent_service import get_intelligent_service, IntelligentSearchService

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()


@router.post("/search", response_model=IntelligentSearchResponse)
async def intelligent_search(
    request: IntelligentSearchRequest,
    service: IntelligentSearchService = Depends(get_intelligent_service)
):
    """
    智能搜索 - 自然语言驱动的综合搜索
    
    ## 功能描述
    - 🧠 **自然语言理解**: 智能解析用户意图，无需复杂参数设置
    - 🔍 **综合搜索**: 同时搜索公司信息和员工信息
    - 🎯 **智能匹配**: AI评估和过滤，提供高质量结果
    - 📊 **搜索洞察**: 提供搜索策略分析和优化建议
    
    ## 支持的查询类型
    
    ### 📈 行业+地区查询
    ```
    "硅谷的人工智能公司"
    "中国的新能源汽车企业"  
    "伦敦的金融科技startup"
    ```
    
    ### 🏢 具体公司查询
    ```
    "Tesla的高管团队"
    "Google的工程师"
    "阿里巴巴的销售经理"
    ```
    
    ### 🌐 综合商业查询
    ```
    "欧洲的生物技术公司及其CEO"
    "美国电动车行业的关键决策者"
    "亚洲fintech领域的投资机构"
    ```
    
    ## 搜索范围选项
    - **comprehensive** (推荐): 公司+员工综合搜索
    - **company_only**: 仅搜索公司信息
    - **employee_only**: 仅搜索员工信息
    
    ## 智能优化特性
    - **关键词扩展**: 自动识别和扩展相关关键词
    - **地理定位**: 智能识别地理位置和市场范围
    - **行业分类**: 自动归类和细分行业领域
    - **职位匹配**: 智能匹配目标职位和层级
    
    ## 示例请求
    ```json
    {
        "query": "硅谷的人工智能startup及其创始人",
        "search_scope": "comprehensive",
        "ai_evaluation": true,
        "max_companies": 20,
        "max_employees_per_company": 5,
        "enable_optimization": true
    }
    ```
    
    ## 返回信息
    - 📋 **搜索结果**: 公司和员工的详细信息
    - 🔍 **搜索洞察**: 查询分析和搜索策略说明
    - ⚡ **性能指标**: 搜索执行时间和优化效果
    - 💡 **优化建议**: 改进搜索的具体建议
    """
    try:
        logger.info(f"收到智能搜索请求: {request.query}")
        result = await service.intelligent_search(request)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"智能搜索API异常: {e}")
        raise HTTPException(status_code=500, detail="智能搜索服务异常")


@router.get("/analyze-query")
async def analyze_query(
    query: str = Query(..., description="待分析的查询", min_length=3),
    service: IntelligentSearchService = Depends(get_intelligent_service)
):
    """
    查询意图分析
    
    ## 功能描述
    分析用户的自然语言查询，识别搜索意图和关键信息
    
    ## 分析内容
    - 🏭 **行业识别**: 识别目标行业和细分领域
    - 🌍 **地理定位**: 识别地理位置和市场范围
    - 👥 **搜索重点**: 判断是公司导向还是人员导向
    - 💼 **职位分析**: 识别目标职位和层级
    - 🎯 **搜索策略**: 推荐最适合的搜索策略
    
    ## 应用场景
    - 搜索前的预分析
    - 查询优化建议
    - 搜索策略制定
    - 参数自动填充
    
    ## 示例查询
    ```
    "北京的AI独角兽公司"
    "Tesla的销售团队联系方式"
    "欧洲可再生能源领域的投资人"
    ```
    """
    try:
        # 调用内部查询分析方法
        analysis = await service._analyze_query(query)
        
        return {
            "success": True,
            "original_query": query,
            "analysis": {
                "detected_industry": analysis.get("detected_industry"),
                "detected_location": analysis.get("detected_location"), 
                "search_focus": analysis.get("search_focus"),
                "detected_positions": analysis.get("detected_positions"),
                "confidence": analysis.get("confidence", 0),
                "strategy": analysis.get("strategy", "rule_based")
            },
            "recommendations": {
                "suggested_scope": _suggest_search_scope(analysis),
                "suggested_params": _suggest_search_params(analysis),
                "optimization_tips": _get_optimization_tips(analysis)
            }
        }
        
    except Exception as e:
        logger.error(f"查询分析失败: {e}")
        raise HTTPException(status_code=500, detail="查询分析服务异常")


@router.get("/search-examples")
async def get_search_examples():
    """
    获取搜索示例
    
    提供各种类型的搜索示例，帮助用户了解系统能力
    """
    examples = {
        "行业+地区搜索": [
            {
                "query": "硅谷的人工智能公司",
                "description": "搜索特定地区的行业公司",
                "expected_results": "AI公司列表及基本信息"
            },
            {
                "query": "中国的新能源汽车制造商",
                "description": "国内特定行业搜索",
                "expected_results": "新能源车企及其详细信息"
            },
            {
                "query": "伦敦的金融科技startup",
                "description": "海外细分领域搜索",
                "expected_results": "英国fintech创业公司"
            }
        ],
        "公司+人员搜索": [
            {
                "query": "Tesla的高管团队联系方式",
                "description": "特定公司的管理层搜索",
                "expected_results": "Tesla高管信息和联系方式"
            },
            {
                "query": "微软的AI研发负责人",
                "description": "公司特定部门负责人",
                "expected_results": "微软AI部门关键人员"
            },
            {
                "query": "字节跳动的销售团队",
                "description": "公司特定职能团队",
                "expected_results": "字节跳动销售人员信息"
            }
        ],
        "综合商业查询": [
            {
                "query": "欧洲生物技术公司及其CEO",
                "description": "地区行业+高管综合搜索",
                "expected_results": "欧洲biotech公司及CEO信息"
            },
            {
                "query": "美国电动车产业链关键企业",
                "description": "产业链上下游企业搜索",
                "expected_results": "电动车相关企业完整图谱"
            },
            {
                "query": "亚太区块链投资机构及合伙人",
                "description": "投资机构+决策者搜索",
                "expected_results": "区块链投资机构和合伙人"
            }
        ],
        "高级搜索技巧": [
            {
                "query": "成立5年内的AI芯片公司创始人",
                "description": "时间+行业+职位组合搜索",
                "expected_results": "新兴AI芯片公司创始人"
            },
            {
                "query": "B轮融资的教育科技公司商务总监",
                "description": "融资阶段+行业+职位搜索", 
                "expected_results": "特定阶段edtech公司BD"
            },
            {
                "query": "跨境电商独角兽的海外市场负责人",
                "description": "公司类型+职能+地区搜索",
                "expected_results": "跨境电商海外业务负责人"
            }
        ]
    }
    
    return {
        "success": True,
        "examples": examples,
        "tips": [
            "💡 使用具体的行业术语可以获得更精准的结果",
            "🌍 明确地理范围有助于定位目标市场",
            "👔 指定职位层级可以快速找到决策者",
            "🔍 组合多个关键词可以实现精细化搜索",
            "⚡ 系统会自动优化查询，无需担心语法"
        ]
    }


@router.get("/supported-languages")
async def get_supported_languages():
    """
    获取支持的语言和地区
    
    返回系统支持的查询语言和搜索地区信息
    """
    languages = {
        "query_languages": {
            "zh-CN": {
                "name": "简体中文",
                "support_level": "完全支持",
                "examples": ["北京的AI公司", "阿里巴巴的技术团队"]
            },
            "en-US": {
                "name": "英语",
                "support_level": "完全支持", 
                "examples": ["AI companies in Silicon Valley", "Tesla executives"]
            },
            "zh-TW": {
                "name": "繁体中文",
                "support_level": "基础支持",
                "examples": ["台北的科技公司", "鴻海的管理層"]
            }
        },
        "search_regions": {
            "北美": ["美国", "加拿大"],
            "欧洲": ["英国", "德国", "法国", "荷兰"],
            "亚太": ["中国", "日本", "新加坡", "澳大利亚", "台湾"],
            "其他": ["印度", "以色列", "巴西"]
        },
        "industry_coverage": {
            "科技": ["人工智能", "软件", "硬件", "互联网", "区块链"],
            "金融": ["银行", "保险", "投资", "支付", "金融科技"],
            "能源": ["新能源", "清洁能源", "石油", "电力", "核能"],
            "医疗": ["生物技术", "制药", "医疗设备", "数字健康"],
            "汽车": ["传统汽车", "新能源汽车", "自动驾驶", "汽车零部件"],
            "其他": ["教育", "零售", "物流", "房地产", "制造业"]
        }
    }
    
    return {
        "success": True,
        "supported_languages": languages
    }


def _suggest_search_scope(analysis: dict) -> str:
    """根据分析结果建议搜索范围"""
    search_focus = analysis.get("search_focus", "comprehensive")
    
    if search_focus == "employee_focused":
        return "employee_only"
    elif search_focus == "company_focused":
        return "company_only"
    else:
        return "comprehensive"


def _suggest_search_params(analysis: dict) -> dict:
    """建议搜索参数"""
    return {
        "max_companies": 30 if analysis.get("search_focus") != "employee_focused" else 10,
        "max_employees_per_company": 5 if analysis.get("detected_positions") else 3,
        "ai_evaluation": True,
        "enable_optimization": True
    }


def _get_optimization_tips(analysis: dict) -> List[str]:
    """获取优化建议"""
    tips = []
    
    if not analysis.get("detected_industry"):
        tips.append("添加具体的行业关键词可以提高搜索精度")
    
    if not analysis.get("detected_location"):
        tips.append("指定地理位置可以获得更相关的结果")
        
    if not analysis.get("detected_positions"):
        tips.append("明确目标职位有助于快速定位关键人员")
        
    if analysis.get("confidence", 0) < 0.7:
        tips.append("尝试使用更具体或更常见的关键词")
    
    return tips