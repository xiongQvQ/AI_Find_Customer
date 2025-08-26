"""
公司搜索路由
提供公司搜索相关的API端点
"""
import logging
from typing import List
from fastapi import APIRouter, HTTPException, Query, Depends

from ..models.requests import CompanySearchRequest, BatchCompanySearchRequest
from ..models.responses import CompanySearchResponse, BatchSearchResponse
from ..services.company_service import get_company_service, CompanySearchService

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()


@router.post("/search", response_model=CompanySearchResponse)
async def search_companies(
    request: CompanySearchRequest,
    service: CompanySearchService = Depends(get_company_service)
):
    """
    搜索公司信息
    
    ## 功能描述
    - 支持按行业、地区关键词搜索
    - 支持自定义搜索查询
    - 支持LinkedIn专业搜索和通用搜索
    - 集成LLM关键词优化
    
    ## 搜索类型
    - **linkedin**: LinkedIn专业搜索（推荐）- 数据质量更高
    - **general**: 通用搜索 - 覆盖范围更广
    
    ## 参数说明
    - **industry**: 行业关键词，如"新能源汽车"、"人工智能"
    - **region**: 地区关键词，如"加利福尼亚"、"北京"
    - **custom_query**: 自定义查询，会覆盖行业和地区参数
    - **country_code**: 国家代码，影响搜索结果的地理偏向
    - **use_llm_optimization**: 是否使用LLM优化搜索关键词
    
    ## 示例请求
    ```json
    {
        "industry": "人工智能",
        "region": "硅谷", 
        "search_type": "linkedin",
        "country_code": "us",
        "max_results": 30,
        "use_llm_optimization": true
    }
    ```
    """
    try:
        logger.info(f"收到公司搜索请求: 行业={request.industry}, 地区={request.region}")
        result = await service.search_companies(request)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"公司搜索API异常: {e}")
        raise HTTPException(status_code=500, detail="公司搜索服务异常")


@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., description="部分查询字符串"),
    service: CompanySearchService = Depends(get_company_service)
):
    """
    获取搜索建议
    
    根据用户输入的部分查询返回相关的搜索建议
    """
    try:
        suggestions = await service.get_search_suggestions(q)
        return {
            "success": True,
            "suggestions": suggestions,
            "query": q
        }
    except Exception as e:
        logger.error(f"获取搜索建议失败: {e}")
        raise HTTPException(status_code=500, detail="获取建议失败")


@router.get("/history")
async def get_search_history(
    limit: int = Query(10, description="返回记录数量", ge=1, le=50),
    service: CompanySearchService = Depends(get_company_service)
):
    """
    获取搜索历史
    
    返回最近的搜索历史记录
    """
    try:
        history = await service.get_search_history(limit)
        return {
            "success": True,
            "history": history,
            "total": len(history)
        }
    except Exception as e:
        logger.error(f"获取搜索历史失败: {e}")
        raise HTTPException(status_code=500, detail="获取历史记录失败")


@router.post("/batch-search", response_model=BatchSearchResponse)
async def batch_search_companies(
    request: BatchCompanySearchRequest,
    service: CompanySearchService = Depends(get_company_service)
):
    """
    批量公司搜索
    
    ## 功能描述
    - 支持批量提交多个搜索查询
    - 可选择并行或串行处理
    - 支持结果合并和去重
    
    ## 适用场景
    - 大量公司信息收集
    - 多行业横向对比
    - 不同地区的同行业搜索
    
    ## 注意事项
    - 批量搜索会消耗更多API配额
    - 建议合理控制查询数量
    - 大批量请求可能需要更长处理时间
    """
    try:
        import time
        # TODO: 实现批量搜索逻辑
        # 这里先返回一个占位响应
        return BatchSearchResponse(
            success=True,
            message="批量搜索功能开发中",
            batch_id=f"batch_{int(time.time())}",
            total_queries=len(request.search_queries),
            completed_queries=0,
            failed_queries=0,
            results=[],
            error="功能开发中，敬请期待"
        )
        
    except Exception as e:
        logger.error(f"批量搜索异常: {e}")
        raise HTTPException(status_code=500, detail="批量搜索服务异常")


@router.get("/supported-countries")
async def get_supported_countries():
    """
    获取支持的国家列表
    
    返回系统支持的国家代码和相关信息
    """
    countries = {
        "us": {"name": "美国", "language": "英语", "search_quality": "高"},
        "cn": {"name": "中国", "language": "中文", "search_quality": "高"},
        "uk": {"name": "英国", "language": "英语", "search_quality": "高"},
        "de": {"name": "德国", "language": "德语/英语", "search_quality": "中"},
        "jp": {"name": "日本", "language": "日语/英语", "search_quality": "中"},
        "sg": {"name": "新加坡", "language": "英语", "search_quality": "中"},
        "au": {"name": "澳大利亚", "language": "英语", "search_quality": "中"},
        "ca": {"name": "加拿大", "language": "英语/法语", "search_quality": "中"},
        "tw": {"name": "台湾", "language": "繁体中文", "search_quality": "中"}
    }
    
    return {
        "success": True,
        "countries": countries,
        "total": len(countries),
        "recommended": ["us", "cn", "uk"]  # 推荐的高质量搜索国家
    }