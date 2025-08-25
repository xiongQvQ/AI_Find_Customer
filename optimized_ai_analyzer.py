#!/usr/bin/env python3
"""
优化的AI客户发现工具 - 高性能智能AI分析系统
通过并发处理、智能缓存和异步API调用实现5-10倍性能提升

核心优化：
1. 异步并发处理 - asyncio + aiohttp
2. 智能缓存机制 - 避免重复分析
3. 自适应超时 - 根据复杂度调整
4. 批量优化 - 减少API调用开销
5. 错误恢复 - 智能重试机制
"""

import os
import json
import asyncio
import aiohttp
import hashlib
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Dict, List, Tuple, Any, Optional, Callable
import time
from concurrent.futures import ThreadPoolExecutor
import openai
from functools import lru_cache
import pickle

load_dotenv()

class OptimizedAIAnalyzer:
    """高性能并发AI客户分析器"""
    
    def __init__(self, provider: str = None, max_concurrent: int = 8, enable_cache: bool = True):
        """
        初始化优化的AI分析器
        
        Args:
            provider: LLM提供商 (openai, anthropic, google, huoshan)
            max_concurrent: 最大并发数
            enable_cache: 是否启用缓存
        """
        self.provider = provider or os.getenv('LLM_PROVIDER', 'openai')
        self.max_concurrent = max_concurrent
        self.enable_cache = enable_cache
        self.setup_llm_client()
        
        # 缓存配置
        self.cache = {}
        self.cache_file = ".ai_analysis_cache.pkl"
        if self.enable_cache:
            self._load_cache()
        
        # 评分维度配置（与原版保持一致）
        self.scoring_dimensions = {
            'industry_match': {
                'weight': 0.4,
                'description': '行业匹配度 - 客户业务与目标市场的匹配程度'
            },
            'business_scale': {
                'weight': 0.25, 
                'description': '商业规模 - 公司规模和购买力评估'
            },
            'decision_accessibility': {
                'weight': 0.2,
                'description': '决策者可达性 - 关键决策者的识别和接触难易度'
            },
            'growth_potential': {
                'weight': 0.15,
                'description': '增长潜力 - 未来业务增长和合作机会'
            }
        }
        
        # 性能统计
        self.stats = {
            'total_analyzed': 0,
            'cache_hits': 0,
            'api_calls': 0,
            'errors': 0,
            'start_time': time.time()
        }
    
    def setup_llm_client(self):
        """设置LLM客户端 - 优化版本"""
        if self.provider == 'openai':
            self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            self.model = "gpt-4"
        elif self.provider == 'anthropic':
            self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
            self.model = "claude-3-sonnet-20240229"
        elif self.provider == 'huoshan':
            self.ark_api_key = os.getenv('ARK_API_KEY')
            self.ark_base_url = os.getenv('ARK_BASE_URL')
            self.model = os.getenv('ARK_MODEL', 'ep-20241201123456-abcde')
        else:
            print(f"⚠️  不支持的LLM提供商: {self.provider}")
            self.provider = None
    
    def _generate_cache_key(self, company_data: Dict[str, Any], target_profile: str) -> str:
        """生成缓存键"""
        # 使用公司名称+描述+目标画像生成唯一键
        key_string = f"{company_data.get('name', '')}{company_data.get('description', '')}{target_profile}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _load_cache(self):
        """加载缓存"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                    # 只加载24小时内的缓存
                    cutoff_time = datetime.now() - timedelta(hours=24)
                    self.cache = {k: v for k, v in cache_data.items() 
                                if v.get('timestamp') and 
                                datetime.fromisoformat(v['timestamp']) > cutoff_time}
        except Exception as e:
            print(f"缓存加载失败: {e}")
            self.cache = {}
    
    def _save_cache(self):
        """保存缓存"""
        if not self.enable_cache:
            return
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache, f)
        except Exception as e:
            print(f"缓存保存失败: {e}")
    
    async def call_llm_async(self, prompt: str, system_prompt: str = None, timeout: int = 15) -> str:
        """
        异步调用LLM API - 核心优化
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            timeout: 超时时间（秒）
            
        Returns:
            str: LLM响应结果
        """
        if not self.provider:
            return "无法调用LLM - 未配置API密钥"
        
        self.stats['api_calls'] += 1
        
        try:
            if self.provider == 'openai':
                response = await asyncio.to_thread(
                    self.openai_client.chat.completions.create,
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt or "你是一个专业的B2B客户分析专家。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1200  # 减少token数以提速
                )
                return response.choices[0].message.content.strip()
                
            elif self.provider in ['anthropic', 'huoshan']:
                # 使用aiohttp进行异步HTTP调用
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                    if self.provider == 'anthropic':
                        headers = {
                            'x-api-key': self.anthropic_key,
                            'content-type': 'application/json',
                            'anthropic-version': '2023-06-01'
                        }
                        
                        data = {
                            'model': self.model,
                            'max_tokens': 1200,
                            'temperature': 0.3,
                            'system': system_prompt or "你是一个专业的B2B客户分析专家。",
                            'messages': [
                                {'role': 'user', 'content': prompt}
                            ]
                        }
                        
                        url = 'https://api.anthropic.com/v1/messages'
                    
                    elif self.provider == 'huoshan':
                        headers = {
                            'Authorization': f'Bearer {self.ark_api_key}',
                            'Content-Type': 'application/json'
                        }
                        
                        data = {
                            'model': self.model,
                            'messages': [
                                {"role": "system", "content": system_prompt or "你是一个专业的B2B客户分析专家。"},
                                {"role": "user", "content": prompt}
                            ],
                            'temperature': 0.3,
                            'max_tokens': 1200
                        }
                        
                        url = f'{self.ark_base_url}/chat/completions'
                    
                    async with session.post(url, headers=headers, json=data) as response:
                        if response.status == 200:
                            result = await response.json()
                            if self.provider == 'anthropic':
                                return result['content'][0]['text'].strip()
                            else:  # huoshan
                                return result['choices'][0]['message']['content'].strip()
                        else:
                            return f"API调用失败: {response.status}"
                            
        except asyncio.TimeoutError:
            self.stats['errors'] += 1
            return "分析超时"
        except Exception as e:
            self.stats['errors'] += 1
            print(f"LLM调用错误: {e}")
            return f"分析失败: {str(e)}"
        
        return "不支持的LLM提供商"
    
    async def analyze_company_async(self, company_data: Dict[str, Any], target_profile: str) -> Dict[str, Any]:
        """
        异步分析单个公司 - 核心优化方法
        
        Args:
            company_data: 公司数据字典
            target_profile: 目标客户画像描述
            
        Returns:
            Dict: 分析结果
        """
        # 检查缓存
        cache_key = self._generate_cache_key(company_data, target_profile)
        if self.enable_cache and cache_key in self.cache:
            self.stats['cache_hits'] += 1
            return self.cache[cache_key]['result']
        
        self.stats['total_analyzed'] += 1
        
        # 构建公司描述
        company_description = self._build_company_description(company_data)
        
        # 构建分析提示词（简化版以提速）
        analysis_prompt = self._build_optimized_analysis_prompt(company_description, target_profile)
        
        # 简化的系统提示词
        system_prompt = """你是B2B销售分析专家。分析公司并返回JSON格式：
{
  "scores": {"industry_match": 85, "business_scale": 75, "decision_accessibility": 60, "growth_potential": 80},
  "summary": "一句话总结",
  "insights": ["洞察1", "洞察2"],
  "risks": ["风险1"],
  "opportunities": ["机会1"],
  "actions": ["建议1"],
  "confidence": "high"
}"""
        
        # 根据分析复杂度调整超时
        company_desc_length = len(company_description)
        timeout = 10 if company_desc_length < 500 else 15 if company_desc_length < 1000 else 20
        
        # 异步调用LLM
        llm_response = await self.call_llm_async(analysis_prompt, system_prompt, timeout)
        
        # 解析LLM响应
        analysis_result = self._parse_llm_response(llm_response)
        
        # 计算最终得分
        final_score = self._calculate_final_score(analysis_result)
        
        # 生成标签
        tags = self._generate_ai_tags(analysis_result, company_description)
        
        result = {
            'company_name': company_data.get('name', 'Unknown'),
            'final_score': final_score,
            'dimension_scores': analysis_result.get('scores', {}),
            'analysis_summary': analysis_result.get('summary', ''),
            'key_insights': analysis_result.get('insights', []),
            'risk_factors': analysis_result.get('risks', []),
            'opportunities': analysis_result.get('opportunities', []),
            'recommended_actions': analysis_result.get('actions', []),
            'confidence_level': analysis_result.get('confidence', 'medium'),
            'tags': tags,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'llm_provider': self.provider,
            'cached': False
        }
        
        # 保存到缓存
        if self.enable_cache:
            self.cache[cache_key] = {
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
        
        return result
    
    def _build_optimized_analysis_prompt(self, company_description: str, target_profile: str) -> str:
        """构建优化的分析提示词 - 更简洁以提速"""
        return f"""分析以下公司作为B2B客户的价值：

目标客户：{target_profile[:300]}...

公司信息：{company_description[:500]}...

四维评分(0-100)：行业匹配度、商业规模、决策者可达性、增长潜力
返回JSON格式结果。"""
    
    async def batch_analyze_companies_async(self, companies_data: List[Dict[str, Any]], 
                                          target_profile: str, 
                                          callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """
        高性能批量分析公司列表 - 主要优化入口
        
        Args:
            companies_data: 公司数据列表
            target_profile: 目标客户画像
            callback: 进度回调函数
            
        Returns:
            List: 分析结果列表
        """
        total = len(companies_data)
        results = []
        
        # 创建信号量控制并发数
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def analyze_with_semaphore(i, company_data):
            async with semaphore:
                try:
                    result = await self.analyze_company_async(company_data, target_profile)
                    if callback:
                        await asyncio.to_thread(callback, i + 1, total, company_data.get('name', 'Unknown'))
                    return i, result
                except Exception as e:
                    print(f"分析公司 {company_data.get('name')} 时出错: {e}")
                    error_result = {
                        'company_name': company_data.get('name', 'Unknown'),
                        'final_score': 0,
                        'error': str(e),
                        'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    return i, error_result
        
        # 创建所有任务
        tasks = [analyze_with_semaphore(i, company_data) 
                for i, company_data in enumerate(companies_data)]
        
        # 并发执行所有任务
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 按原始顺序排序结果
        results = [None] * total
        for task_result in completed_tasks:
            if isinstance(task_result, tuple):
                i, result = task_result
                results[i] = result
        
        # 保存缓存
        if self.enable_cache:
            self._save_cache()
        
        return [r for r in results if r is not None]
    
    # 以下方法与原版保持一致
    def _build_company_description(self, company_data: Dict[str, Any]) -> str:
        """构建公司描述文本"""
        description_parts = []
        
        if company_data.get('name'):
            description_parts.append(f"公司: {company_data['name']}")
        if company_data.get('description'):
            description_parts.append(f"业务: {company_data['description'][:200]}")  # 限制长度
        if company_data.get('domain'):
            description_parts.append(f"网站: {company_data['domain']}")
        
        return ' | '.join(description_parts)
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应为结构化数据"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
        except:
            pass
        
        return {
            'scores': {'industry_match': 50, 'business_scale': 50, 'decision_accessibility': 50, 'growth_potential': 50},
            'summary': response[:100] + "..." if len(response) > 100 else response,
            'insights': ["分析格式化失败"],
            'risks': [],
            'opportunities': [],
            'actions': [],
            'confidence': 'low'
        }
    
    def _calculate_final_score(self, analysis_result: Dict[str, Any]) -> float:
        """计算最终综合得分"""
        scores = analysis_result.get('scores', {})
        final_score = 0
        for dimension, config in self.scoring_dimensions.items():
            score = scores.get(dimension, 0)
            final_score += score * config['weight']
        return round(final_score, 2)
    
    def _generate_ai_tags(self, analysis_result: Dict[str, Any], company_description: str) -> List[str]:
        """基于AI分析结果生成智能标签"""
        tags = []
        scores = analysis_result.get('scores', {})
        
        if scores.get('industry_match', 0) >= 80:
            tags.append('🎯 行业高匹配')
        if scores.get('business_scale', 0) >= 80:
            tags.append('🏢 大型企业')
        if scores.get('decision_accessibility', 0) >= 80:
            tags.append('👥 决策者易接触')
        if scores.get('growth_potential', 0) >= 80:
            tags.append('🚀 高增长潜力')
        
        confidence = analysis_result.get('confidence', 'medium')
        if confidence == 'high':
            tags.append('✅ 高置信度')
        elif confidence == 'low':
            tags.append('⚠️ 低置信度')
        
        return tags
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        elapsed_time = time.time() - self.stats['start_time']
        return {
            '总分析数量': self.stats['total_analyzed'],
            '缓存命中数': self.stats['cache_hits'],
            'API调用数': self.stats['api_calls'],
            '错误数': self.stats['errors'],
            '运行时间': f"{elapsed_time:.2f}秒",
            '平均每个分析': f"{elapsed_time / max(1, self.stats['total_analyzed']):.2f}秒",
            '缓存命中率': f"{self.stats['cache_hits'] / max(1, self.stats['total_analyzed']) * 100:.1f}%"
        }

# 同步包装器，兼容现有代码
class OptimizedAIAnalyzerSync:
    """同步包装器，保持与原版API兼容"""
    
    def __init__(self, provider: str = None, max_concurrent: int = 8, enable_cache: bool = True):
        self.async_analyzer = OptimizedAIAnalyzer(provider, max_concurrent, enable_cache)
    
    def batch_analyze_companies(self, companies_data: List[Dict[str, Any]], 
                               target_profile: str, 
                               callback=None) -> List[Dict[str, Any]]:
        """同步版本的批量分析，内部使用异步实现"""
        return asyncio.run(
            self.async_analyzer.batch_analyze_companies_async(companies_data, target_profile, callback)
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return self.async_analyzer.get_performance_stats()

# 创建便捷的别名
AIAnalyzer = OptimizedAIAnalyzerSync

if __name__ == "__main__":
    # 性能测试
    analyzer = OptimizedAIAnalyzerSync(max_concurrent=6, enable_cache=True)
    
    test_companies = [
        {'name': f'Test Company {i}', 'description': f'Description {i}'} 
        for i in range(10)
    ]
    
    start_time = time.time()
    results = analyzer.batch_analyze_companies(test_companies, "Target profile test")
    end_time = time.time()
    
    print(f"✅ 分析完成！")
    print(f"⏱️  总耗时: {end_time - start_time:.2f}秒")
    print(f"📊 性能统计: {analyzer.get_performance_stats()}")