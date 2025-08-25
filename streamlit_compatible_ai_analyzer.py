#!/usr/bin/env python3
"""
Streamlit兼容的AI分析器 - 解决asyncio ScriptRunContext错误
使用ThreadPoolExecutor实现并发处理，完全兼容Streamlit环境
"""

import os
import json
import hashlib
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import openai
import requests
import pickle
import threading

load_dotenv()

class StreamlitCompatibleAIAnalyzer:
    """Streamlit兼容的高性能AI客户分析器"""
    
    def __init__(self, provider: str = None, max_concurrent: int = 6, enable_cache: bool = True):
        """
        初始化Streamlit兼容的AI分析器
        
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
        self.cache_lock = threading.Lock()
        if self.enable_cache:
            self._load_cache()
        
        # 评分维度配置
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
        self.stats_lock = threading.Lock()
    
    def setup_llm_client(self):
        """设置LLM客户端"""
        if self.provider == 'openai':
            self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        elif self.provider == 'anthropic':
            self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
            self.model = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
        elif self.provider == 'google':
            self.google_key = os.getenv('GOOGLE_API_KEY') 
            self.model = os.getenv('GOOGLE_MODEL', 'gemini-1.5-flash')
        elif self.provider == 'huoshan':
            self.ark_api_key = os.getenv('ARK_API_KEY')
            self.ark_base_url = os.getenv('ARK_BASE_URL')
            self.model = os.getenv('ARK_MODEL', 'ep-20241022140031-89nkp')
        else:
            print(f"⚠️ 不支持的LLM提供商: {self.provider}")
            self.provider = None
    
    def _generate_cache_key(self, company_data: Dict[str, Any], target_profile: str) -> str:
        """生成缓存键"""
        key_string = f"{company_data.get('name', '')}{company_data.get('description', '')}{target_profile}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _load_cache(self):
        """加载缓存"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
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
            with self.cache_lock:
                with open(self.cache_file, 'wb') as f:
                    pickle.dump(self.cache, f)
        except Exception as e:
            print(f"缓存保存失败: {e}")
    
    def call_llm_sync(self, prompt: str, system_prompt: str = None, timeout: int = 30, max_retries: int = 3) -> str:
        """
        同步调用LLM API - Streamlit兼容版本，带重试机制
        """
        if not self.provider:
            return "无法调用LLM - 未配置API密钥"
        
        with self.stats_lock:
            self.stats['api_calls'] += 1
        
        # 重试机制
        for attempt in range(max_retries):
            try:
                if self.provider == 'openai':
                    response = self.openai_client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt or "你是一个专业的B2B客户分析专家。"},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                        max_tokens=1200,
                        timeout=timeout
                    )
                    return response.choices[0].message.content.strip()
                    
                elif self.provider == 'anthropic':
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
                    
                    response = requests.post(
                        'https://api.anthropic.com/v1/messages',
                        headers=headers,
                        json=data,
                        timeout=timeout
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        return result['content'][0]['text'].strip()
                    else:
                        return f"API调用失败: {response.status_code}"
                
                elif self.provider == 'google':
                    import google.generativeai as genai
                    genai.configure(api_key=self.google_key)
                    
                    model = genai.GenerativeModel(self.model)
                    full_prompt = f"{system_prompt or '你是一个专业的B2B客户分析专家。'}\n\n{prompt}"
                    
                    response = model.generate_content(
                        full_prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.3,
                            max_output_tokens=1200,
                        )
                    )
                    return response.text.strip()
                
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
                    
                    response = requests.post(
                        f'{self.ark_base_url}/chat/completions',
                        headers=headers,
                        json=data,
                        timeout=timeout
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        return result['choices'][0]['message']['content'].strip()
                    else:
                        return f"API调用失败: {response.status_code}"
                
                else:
                    return "不支持的LLM提供商"
                            
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避
                    print(f"API调用超时，{wait_time}秒后重试 (尝试 {attempt + 1}/{max_retries}): {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    with self.stats_lock:
                        self.stats['errors'] += 1
                    print(f"LLM调用最终失败: {e}")
                    return f"分析失败: API调用超时 - {str(e)}"
            except Exception as e:
                with self.stats_lock:
                    self.stats['errors'] += 1
                print(f"LLM调用错误: {e}")
                return f"分析失败: {str(e)}"
        
        return "不支持的LLM提供商"
    
    def analyze_company_sync(self, company_data: Dict[str, Any], target_profile: str) -> Dict[str, Any]:
        """
        同步分析单个公司 - Streamlit兼容版本
        """
        # 检查缓存
        cache_key = self._generate_cache_key(company_data, target_profile)
        if self.enable_cache and cache_key in self.cache:
            with self.stats_lock:
                self.stats['cache_hits'] += 1
            return self.cache[cache_key]['result']
        
        with self.stats_lock:
            self.stats['total_analyzed'] += 1
        
        # 构建公司描述
        company_description = self._build_company_description(company_data)
        
        # 构建分析提示词
        analysis_prompt = self._build_optimized_analysis_prompt(company_description, target_profile)
        
        # 系统提示词
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
        
        # 调用LLM
        llm_response = self.call_llm_sync(analysis_prompt, system_prompt, timeout)
        
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
            with self.cache_lock:
                self.cache[cache_key] = {
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                }
        
        return result
    
    def batch_analyze_companies(self, companies_data: List[Dict[str, Any]], 
                              target_profile: str, 
                              callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """
        高性能批量分析公司 - Streamlit兼容版本
        使用ThreadPoolExecutor实现并发处理
        """
        total = len(companies_data)
        results = [None] * total
        
        def analyze_single_company(index_and_data):
            index, company_data = index_and_data
            try:
                result = self.analyze_company_sync(company_data, target_profile)
                if callback:
                    callback(index + 1, total, company_data.get('name', 'Unknown'))
                return index, result
            except Exception as e:
                print(f"分析公司 {company_data.get('name')} 时出错: {e}")
                error_result = {
                    'company_name': company_data.get('name', 'Unknown'),
                    'final_score': 0,
                    'error': str(e),
                    'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                return index, error_result
        
        # 使用ThreadPoolExecutor进行并发处理
        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            # 提交所有任务
            future_to_index = {
                executor.submit(analyze_single_company, (i, company_data)): i 
                for i, company_data in enumerate(companies_data)
            }
            
            # 收集结果
            for future in as_completed(future_to_index):
                try:
                    index, result = future.result()
                    results[index] = result
                except Exception as e:
                    index = future_to_index[future]
                    company_name = companies_data[index].get('name', 'Unknown')
                    print(f"分析公司 {company_name} 时发生异常: {e}")
                    results[index] = {
                        'company_name': company_name,
                        'final_score': 0,
                        'error': str(e),
                        'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
        
        # 保存缓存
        if self.enable_cache:
            self._save_cache()
        
        return [r for r in results if r is not None]
    
    def _build_optimized_analysis_prompt(self, company_description: str, target_profile: str) -> str:
        """构建优化的分析提示词"""
        return f"""分析以下公司作为B2B客户的价值：

目标客户：{target_profile[:300]}...

公司信息：{company_description[:500]}...

四维评分(0-100)：行业匹配度、商业规模、决策者可达性、增长潜力
返回JSON格式结果。"""
    
    def _build_company_description(self, company_data: Dict[str, Any]) -> str:
        """构建公司描述文本"""
        description_parts = []
        
        if company_data.get('name'):
            description_parts.append(f"公司: {company_data['name']}")
        if company_data.get('description'):
            description_parts.append(f"业务: {company_data['description'][:200]}")
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
        with self.stats_lock:
            return {
                '总分析数量': self.stats['total_analyzed'],
                '缓存命中数': self.stats['cache_hits'],
                'API调用数': self.stats['api_calls'],
                '错误数': self.stats['errors'],
                '运行时间': f"{elapsed_time:.2f}秒",
                '平均每个分析': f"{elapsed_time / max(1, self.stats['total_analyzed']):.2f}秒",
                '缓存命中率': f"{self.stats['cache_hits'] / max(1, self.stats['total_analyzed']) * 100:.1f}%"
            }


# 员工分析器 - Streamlit兼容版本
class StreamlitCompatibleEmployeeAIAnalyzer:
    """Streamlit兼容的员工AI分析器"""
    
    def __init__(self, provider: str = None, max_concurrent: int = 6, enable_cache: bool = True):
        self.provider = provider or os.getenv('LLM_PROVIDER', 'openai')
        self.max_concurrent = max_concurrent
        self.enable_cache = enable_cache
        self.setup_llm_client()
        
        # 缓存配置
        self.cache = {}
        self.cache_file = ".employee_analysis_cache.pkl"
        self.cache_lock = threading.Lock()
        if self.enable_cache:
            self._load_cache()
        
        # 员工评分维度
        self.scoring_dimensions = {
            'role_relevance': {
                'weight': 0.35,
                'description': '角色相关性 - 职位与业务需求的匹配度'
            },
            'decision_power': {
                'weight': 0.3,
                'description': '决策权力 - 在采购决策中的影响力'
            },
            'contact_probability': {
                'weight': 0.25,
                'description': '联系可能性 - 成功接触的可能性'
            },
            'influence_scope': {
                'weight': 0.1,
                'description': '影响范围 - 在组织中的影响范围'
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
        self.stats_lock = threading.Lock()
    
    def setup_llm_client(self):
        """设置LLM客户端"""
        if self.provider == 'openai':
            self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        elif self.provider == 'anthropic':
            self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
            self.model = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
        elif self.provider == 'google':
            self.google_key = os.getenv('GOOGLE_API_KEY')
            self.model = os.getenv('GOOGLE_MODEL', 'gemini-1.5-flash')
        elif self.provider == 'huoshan':
            self.ark_api_key = os.getenv('ARK_API_KEY')
            self.ark_base_url = os.getenv('ARK_BASE_URL')
            self.model = os.getenv('ARK_MODEL', 'ep-20241022140031-89nkp')
        else:
            print(f"⚠️ 不支持的LLM提供商: {self.provider}")
            self.provider = None
    
    def _generate_cache_key(self, employee_data: Dict[str, Any], business_context: str) -> str:
        """生成缓存键"""
        key_string = f"{employee_data.get('name', '')}{employee_data.get('title', '')}{employee_data.get('company', '')}{business_context}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _load_cache(self):
        """加载缓存"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                    cutoff_time = datetime.now() - timedelta(hours=24)
                    self.cache = {k: v for k, v in cache_data.items() 
                                if v.get('timestamp') and 
                                datetime.fromisoformat(v['timestamp']) > cutoff_time}
        except Exception as e:
            print(f"员工缓存加载失败: {e}")
            self.cache = {}
    
    def _save_cache(self):
        """保存缓存"""
        if not self.enable_cache:
            return
        try:
            with self.cache_lock:
                with open(self.cache_file, 'wb') as f:
                    pickle.dump(self.cache, f)
        except Exception as e:
            print(f"员工缓存保存失败: {e}")
    
    def call_llm_sync(self, prompt: str, system_prompt: str = None, timeout: int = 30, max_retries: int = 3) -> str:
        """同步调用LLM API - 带重试机制"""
        if not self.provider:
            return "无法调用LLM - 未配置API密钥"
        
        with self.stats_lock:
            self.stats['api_calls'] += 1
        
        # 重试机制
        for attempt in range(max_retries):
            try:
                if self.provider == 'openai':
                    response = self.openai_client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt or "你是一个专业的B2B销售和人事分析专家。"},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                        max_tokens=1200,
                        timeout=timeout
                    )
                    return response.choices[0].message.content.strip()
                    
                elif self.provider == 'anthropic':
                    headers = {
                        'x-api-key': self.anthropic_key,
                        'content-type': 'application/json',
                        'anthropic-version': '2023-06-01'
                    }
                    
                    data = {
                        'model': self.model,
                        'max_tokens': 1200,
                        'temperature': 0.3,
                        'system': system_prompt or "你是一个专业的B2B销售和人事分析专家。",
                        'messages': [
                            {'role': 'user', 'content': prompt}
                        ]
                    }
                    
                    response = requests.post(
                        'https://api.anthropic.com/v1/messages',
                        headers=headers,
                        json=data,
                        timeout=timeout
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        return result['content'][0]['text'].strip()
                    else:
                        return f"API调用失败: {response.status_code}"
                
                elif self.provider == 'google':
                    import google.generativeai as genai
                    genai.configure(api_key=self.google_key)
                    
                    model = genai.GenerativeModel(self.model)
                    full_prompt = f"{system_prompt or '你是一个专业的B2B销售和人事分析专家。'}\n\n{prompt}"
                    
                    response = model.generate_content(
                        full_prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.3,
                            max_output_tokens=1200,
                        )
                    )
                    return response.text.strip()
                
                elif self.provider == 'huoshan':
                    headers = {
                        'Authorization': f'Bearer {self.ark_api_key}',
                        'Content-Type': 'application/json'
                    }
                    
                    data = {
                        'model': self.model,
                        'messages': [
                            {"role": "system", "content": system_prompt or "你是一个专业的B2B销售和人事分析专家。"},
                            {"role": "user", "content": prompt}
                        ],
                        'temperature': 0.3,
                        'max_tokens': 1200
                    }
                    
                    response = requests.post(
                        f'{self.ark_base_url}/chat/completions',
                        headers=headers,
                        json=data,
                        timeout=timeout
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        return result['choices'][0]['message']['content'].strip()
                    else:
                        return f"API调用失败: {response.status_code}"
                
                else:
                    return "不支持的LLM提供商"
                            
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避
                    print(f"员工分析API调用超时，{wait_time}秒后重试 (尝试 {attempt + 1}/{max_retries}): {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    with self.stats_lock:
                        self.stats['errors'] += 1
                    print(f"员工分析LLM调用最终失败: {e}")
                    return f"分析失败: API调用超时 - {str(e)}"
            except Exception as e:
                with self.stats_lock:
                    self.stats['errors'] += 1
                print(f"员工LLM调用错误: {e}")
                return f"分析失败: {str(e)}"
        
        return "不支持的LLM提供商"
    
    def analyze_employee_sync(self, employee_data: Dict[str, Any], business_context: str) -> Dict[str, Any]:
        """同步分析单个员工"""
        # 检查缓存
        cache_key = self._generate_cache_key(employee_data, business_context)
        if self.enable_cache and cache_key in self.cache:
            with self.stats_lock:
                self.stats['cache_hits'] += 1
            return self.cache[cache_key]['result']
        
        with self.stats_lock:
            self.stats['total_analyzed'] += 1
        
        # 构建员工描述
        employee_description = self._build_employee_description(employee_data)
        
        # 构建分析提示词
        analysis_prompt = f"""分析以下员工作为B2B业务联系人的价值：

业务背景：{business_context[:300]}...

员工信息：{employee_description[:400]}...

四维评分(0-100)：角色相关性、决策权力、联系可能性、影响范围
返回JSON格式结果。"""
        
        # 系统提示词
        system_prompt = """你是B2B销售分析专家。分析员工并返回JSON格式：
{
  "scores": {"role_relevance": 85, "decision_power": 75, "contact_probability": 80, "influence_scope": 70},
  "summary": "一句话总结",
  "insights": ["洞察1", "洞察2"],
  "contact_strategy": ["策略1"],
  "decision_influence": "high",
  "recommended_approach": "direct_contact"
}"""
        
        # 调用LLM
        llm_response = self.call_llm_sync(analysis_prompt, system_prompt, 15)
        
        # 解析LLM响应
        analysis_result = self._parse_llm_response(llm_response)
        
        # 计算最终得分
        final_score = self._calculate_final_score(analysis_result)
        
        # 生成标签
        tags = self._generate_employee_tags(analysis_result, employee_description)
        
        result = {
            'employee_name': employee_data.get('name', 'Unknown'),
            'company': employee_data.get('company', 'Unknown'),
            'title': employee_data.get('title', 'Unknown'),
            'final_score': final_score,
            'dimension_scores': analysis_result.get('scores', {}),
            'analysis_summary': analysis_result.get('summary', ''),
            'key_insights': analysis_result.get('insights', []),
            'contact_strategy': analysis_result.get('contact_strategy', []),
            'decision_influence': analysis_result.get('decision_influence', 'medium'),
            'recommended_approach': analysis_result.get('recommended_approach', 'research_first'),
            'tags': tags,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'llm_provider': self.provider,
            'cached': False
        }
        
        # 保存到缓存
        if self.enable_cache:
            with self.cache_lock:
                self.cache[cache_key] = {
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                }
        
        return result
    
    def batch_analyze_employees(self, employees_data: List[Dict[str, Any]], 
                              business_context: str, 
                              callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """批量分析员工 - Streamlit兼容版本"""
        total = len(employees_data)
        results = [None] * total
        
        def analyze_single_employee(index_and_data):
            index, employee_data = index_and_data
            try:
                result = self.analyze_employee_sync(employee_data, business_context)
                if callback:
                    callback(index + 1, total, employee_data.get('name', 'Unknown'))
                return index, result
            except Exception as e:
                print(f"分析员工 {employee_data.get('name')} 时出错: {e}")
                error_result = {
                    'employee_name': employee_data.get('name', 'Unknown'),
                    'final_score': 0,
                    'error': str(e),
                    'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                return index, error_result
        
        # 使用ThreadPoolExecutor进行并发处理
        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            # 提交所有任务
            future_to_index = {
                executor.submit(analyze_single_employee, (i, employee_data)): i 
                for i, employee_data in enumerate(employees_data)
            }
            
            # 收集结果
            for future in as_completed(future_to_index):
                try:
                    index, result = future.result()
                    results[index] = result
                except Exception as e:
                    index = future_to_index[future]
                    employee_name = employees_data[index].get('name', 'Unknown')
                    print(f"分析员工 {employee_name} 时发生异常: {e}")
                    results[index] = {
                        'employee_name': employee_name,
                        'final_score': 0,
                        'error': str(e),
                        'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
        
        # 保存缓存
        if self.enable_cache:
            self._save_cache()
        
        return [r for r in results if r is not None]
    
    def _build_employee_description(self, employee_data: Dict[str, Any]) -> str:
        """构建员工描述文本"""
        parts = []
        
        if employee_data.get('name'):
            parts.append(f"姓名: {employee_data['name']}")
        if employee_data.get('title'):
            parts.append(f"职位: {employee_data['title']}")
        if employee_data.get('company'):
            parts.append(f"公司: {employee_data['company']}")
        if employee_data.get('description'):
            parts.append(f"描述: {employee_data['description'][:150]}")
        
        return ' | '.join(parts)
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
        except:
            pass
        
        return {
            'scores': {'role_relevance': 50, 'decision_power': 50, 'contact_probability': 50, 'influence_scope': 50},
            'summary': response[:100] + "..." if len(response) > 100 else response,
            'insights': ["分析格式化失败"],
            'contact_strategy': [],
            'decision_influence': 'medium',
            'recommended_approach': 'research_first'
        }
    
    def _calculate_final_score(self, analysis_result: Dict[str, Any]) -> float:
        """计算最终得分"""
        scores = analysis_result.get('scores', {})
        final_score = 0
        for dimension, config in self.scoring_dimensions.items():
            score = scores.get(dimension, 0)
            final_score += score * config['weight']
        return round(final_score, 2)
    
    def _generate_employee_tags(self, analysis_result: Dict[str, Any], employee_description: str) -> List[str]:
        """生成员工标签"""
        tags = []
        scores = analysis_result.get('scores', {})
        
        if scores.get('role_relevance', 0) >= 80:
            tags.append('🎯 高相关性')
        if scores.get('decision_power', 0) >= 80:
            tags.append('👑 决策者')
        if scores.get('contact_probability', 0) >= 80:
            tags.append('📞 易联系')
        if scores.get('influence_scope', 0) >= 80:
            tags.append('🌟 高影响力')
        
        decision_influence = analysis_result.get('decision_influence', 'medium')
        if decision_influence == 'high':
            tags.append('⚡ 强决策影响力')
        
        return tags
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        elapsed_time = time.time() - self.stats['start_time']
        with self.stats_lock:
            return {
                '总分析数量': self.stats['total_analyzed'],
                '缓存命中数': self.stats['cache_hits'],
                'API调用数': self.stats['api_calls'],
                '错误数': self.stats['errors'],
                '运行时间': f"{elapsed_time:.2f}秒",
                '平均每个分析': f"{elapsed_time / max(1, self.stats['total_analyzed']):.2f}秒",
                '缓存命中率': f"{self.stats['cache_hits'] / max(1, self.stats['total_analyzed']) * 100:.1f}%"
            }