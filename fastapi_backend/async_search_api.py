"""
异步搜索API模块
支持实时进度更新和Server-Sent Events (SSE)
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from enum import Enum

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel


class SearchStatus(str, Enum):
    """搜索状态枚举"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    SEARCHING = "searching"
    EVALUATING = "evaluating"
    FILTERING = "filtering"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SearchProgress:
    """搜索进度数据"""
    search_id: str
    status: SearchStatus
    progress: float  # 0-100
    current_step: str
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self):
        return {
            "search_id": self.search_id,
            "status": self.status.value,
            "progress": self.progress,
            "current_step": self.current_step,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }


class AsyncSearchRequest(BaseModel):
    """异步搜索请求"""
    query: str
    ai_evaluation_enabled: bool = True
    employee_search_enabled: bool = False
    output_format: str = "csv"
    enable_realtime: bool = True


class AsyncSearchManager:
    """异步搜索管理器"""
    
    def __init__(self):
        self.active_searches: Dict[str, SearchProgress] = {}
        self.search_results: Dict[str, Dict[str, Any]] = {}
        self._stop_events: Dict[str, asyncio.Event] = {}
    
    async def start_search(self, request: AsyncSearchRequest) -> str:
        """启动异步搜索"""
        search_id = str(uuid.uuid4())
        
        # 初始化搜索状态
        progress = SearchProgress(
            search_id=search_id,
            status=SearchStatus.PENDING,
            progress=0,
            current_step="initializing",
            message="正在初始化搜索..."
        )
        
        self.active_searches[search_id] = progress
        self._stop_events[search_id] = asyncio.Event()
        
        # 在后台启动搜索任务
        asyncio.create_task(self._execute_search(search_id, request))
        
        return search_id
    
    async def _execute_search(self, search_id: str, request: AsyncSearchRequest):
        """执行搜索的后台任务"""
        try:
            # 导入LangGraph搜索模块
            from langgraph_search import create_search_graph
            
            # 步骤1: 意图分析 (10%)
            await self._update_progress(
                search_id, SearchStatus.ANALYZING, 10,
                "intent_recognition", f"正在分析查询: {request.query}"
            )
            await asyncio.sleep(0.5)  # 模拟处理时间
            
            # 创建搜索图实例
            search_graph = create_search_graph(enable_checkpoints=True)
            
            # 步骤2: 公司搜索 (30%)
            await self._update_progress(
                search_id, SearchStatus.SEARCHING, 30,
                "company_search", "正在搜索相关公司..."
            )
            
            # 执行搜索 - 在独立线程中运行避免阻塞
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                search_graph.execute_search,
                request.query,
                request.ai_evaluation_enabled,
                request.employee_search_enabled,
                request.output_format
            )
            
            if not result.get('success'):
                raise Exception(result.get('error', 'Search execution failed'))
            
            search_results = result.get('result', {}).get('search_results', {})
            companies = search_results.get('companies', [])
            
            # 步骤3: AI评估 (60%)
            if request.ai_evaluation_enabled and companies:
                await self._update_progress(
                    search_id, SearchStatus.EVALUATING, 60,
                    "ai_evaluation", f"正在AI评估 {len(companies)} 家公司..."
                )
                await asyncio.sleep(1.0)  # AI评估需要更多时间
            
            # 步骤4: 官网过滤 (80%)
            await self._update_progress(
                search_id, SearchStatus.FILTERING, 80,
                "website_filtering", "正在过滤和验证官网..."
            )
            
            # 应用官网过滤
            filtered_companies = await self._apply_website_filtering(companies)
            search_results['companies'] = filtered_companies
            search_results['total_companies_found'] = len(filtered_companies)
            search_results['filtered_by_website'] = True
            
            # 步骤5: 员工搜索 (如果启用) (90%)
            if request.employee_search_enabled and filtered_companies:
                await self._update_progress(
                    search_id, SearchStatus.SEARCHING, 90,
                    "employee_search", "正在搜索员工信息..."
                )
                await asyncio.sleep(1.5)
            
            # 步骤6: 完成 (100%)
            await self._update_progress(
                search_id, SearchStatus.COMPLETED, 100,
                "completed", f"搜索完成! 找到 {len(filtered_companies)} 家符合条件的公司",
                data={
                    "search_results": search_results,
                    "total_companies": len(filtered_companies),
                    "ai_evaluation_enabled": request.ai_evaluation_enabled,
                    "employee_search_enabled": request.employee_search_enabled
                }
            )
            
            # 存储最终结果
            self.search_results[search_id] = search_results
            
        except Exception as e:
            await self._update_progress(
                search_id, SearchStatus.FAILED, 100,
                "error", f"搜索失败: {str(e)}",
                data={"error": str(e)}
            )
    
    async def _apply_website_filtering(self, companies: list) -> list:
        """应用官网过滤（异步版本）"""
        from enhanced_website_utils import enhanced_website_validator
        
        filtered_companies = []
        
        for company in companies:
            company_name = company.get('name', '')
            if company_name:
                # 异步获取官网信息（使用增强版搜索引擎验证）
                website_info = await asyncio.get_event_loop().run_in_executor(
                    None,
                    enhanced_website_validator.get_official_website,
                    company_name
                )
                
                if website_info['website']:
                    company['official_website'] = website_info['website']
                    company['website_confidence'] = website_info['confidence']
                    company['website_method'] = website_info['method']
                    company['search_results'] = website_info.get('search_results', [])
                
                # 验证现有网站URL（使用增强版深度分析）
                if company.get('website_url'):
                    verification = await asyncio.get_event_loop().run_in_executor(
                        None,
                        enhanced_website_validator.is_official_website,
                        company['website_url'],
                        company_name
                    )
                    
                    company['is_official_website'] = verification['is_official']
                    company['verification_confidence'] = verification['confidence']
                    company['verification_reasons'] = verification['reasons']
                    company['detailed_analysis'] = verification.get('analysis', {})
                    
                    # 使用更智能的过滤策略 - 只保留高置信度的官网
                    if verification['is_official'] or verification['confidence'] > 0.6:
                        filtered_companies.append(company)
                else:
                    # 如果没有现有URL但找到了官网，直接添加
                    if company.get('official_website'):
                        filtered_companies.append(company)
        
        return filtered_companies
    
    async def _update_progress(self, search_id: str, status: SearchStatus, 
                             progress: float, current_step: str, message: str,
                             data: Optional[Dict[str, Any]] = None):
        """更新搜索进度"""
        if search_id in self.active_searches:
            self.active_searches[search_id] = SearchProgress(
                search_id=search_id,
                status=status,
                progress=progress,
                current_step=current_step,
                message=message,
                data=data
            )
    
    def get_search_status(self, search_id: str) -> Optional[SearchProgress]:
        """获取搜索状态"""
        return self.active_searches.get(search_id)
    
    def get_search_results(self, search_id: str) -> Optional[Dict[str, Any]]:
        """获取搜索结果"""
        return self.search_results.get(search_id)
    
    async def cancel_search(self, search_id: str) -> bool:
        """取消搜索"""
        if search_id in self._stop_events:
            self._stop_events[search_id].set()
            
            if search_id in self.active_searches:
                await self._update_progress(
                    search_id, SearchStatus.FAILED, 100,
                    "cancelled", "搜索已被用户取消"
                )
            
            return True
        return False
    
    async def stream_progress(self, search_id: str) -> AsyncGenerator[str, None]:
        """生成SSE进度流"""
        if search_id not in self.active_searches:
            yield f"data: {json.dumps({'error': 'Search not found'})}\n\n"
            return
        
        last_progress = -1
        
        while True:
            progress = self.active_searches.get(search_id)
            if not progress:
                break
            
            # 只在进度变化时发送更新
            if progress.progress != last_progress:
                yield f"data: {json.dumps(progress.to_dict())}\n\n"
                last_progress = progress.progress
            
            # 如果搜索完成或失败，结束流
            if progress.status in [SearchStatus.COMPLETED, SearchStatus.FAILED]:
                break
            
            await asyncio.sleep(0.5)  # 每500ms检查一次
        
        # 发送结束信号
        yield f"data: {json.dumps({'type': 'close'})}\n\n"
    
    def cleanup_old_searches(self, max_age_minutes: int = 60):
        """清理旧的搜索记录"""
        cutoff_time = datetime.now().timestamp() - (max_age_minutes * 60)
        
        to_remove = []
        for search_id, progress in self.active_searches.items():
            if progress.timestamp.timestamp() < cutoff_time:
                to_remove.append(search_id)
        
        for search_id in to_remove:
            self.active_searches.pop(search_id, None)
            self.search_results.pop(search_id, None)
            self._stop_events.pop(search_id, None)


# 全局搜索管理器实例
search_manager = AsyncSearchManager()


async def create_streaming_response(search_id: str) -> StreamingResponse:
    """创建SSE流响应"""
    return StreamingResponse(
        search_manager.stream_progress(search_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )


# 定期清理任务
async def periodic_cleanup():
    """定期清理旧的搜索记录"""
    while True:
        await asyncio.sleep(300)  # 每5分钟清理一次
        search_manager.cleanup_old_searches()


# 清理任务将在 FastAPI 启动时启动
# asyncio.create_task(periodic_cleanup())  # 这会在 FastAPI app 的启动事件中调用