"""
LLM-based Intelligent Keyword Generator
基于LLM的智能关键词生成器 - 替代硬编码翻译字典
"""
import os
import json
import time
import csv
import requests
from typing import List, Dict, Optional, Any
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class LLMKeywordGenerator:
    """
    基于LLM的智能关键词生成器
    
    功能：
    1. 根据行业术语和目标国家生成优化的搜索关键词
    2. 理解上下文和地域特色，生成本地化关键词
    3. 支持多种LLM提供商（OpenAI, Anthropic, Google, Huoshan）
    4. 智能缓存机制，避免重复调用
    5. 生成Google搜索优化的关键词组合
    """
    
    def __init__(self):
        """初始化LLM关键词生成器"""
        self.llm_provider = os.getenv("LLM_PROVIDER", "none").lower()
        self.cache = {}  # 内存缓存
        self.cache_ttl = 3600  # 缓存1小时
        
        # 加载国家代码映射表
        self._load_country_codes()
        
        # 初始化LLM客户端
        self._init_llm_client()
    
    def _load_country_codes(self):
        """从CSV文件加载国家代码映射"""
        self.country_codes = {}
        self.country_name_mapping = {}  # 中文名 -> 英文名映射
        
        csv_path = Path(__file__).parent.parent / "config" / "serper_countries.csv"
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    country_name = row['name'].strip()
                    country_code = row['countryCode'].strip()
                    
                    # 建立英文名 -> 代码映射
                    self.country_codes[country_name.lower()] = country_code
                    
                    # 建立常见中文名映射
                    if country_name == "United States":
                        self.country_name_mapping.update({
                            "美国": "United States",
                            "美利坚合众国": "United States"
                        })
                    elif country_name == "China":
                        self.country_name_mapping.update({
                            "中国": "China",
                            "中华人民共和国": "China"
                        })
                    elif country_name == "United Kingdom":
                        self.country_name_mapping.update({
                            "英国": "United Kingdom",
                            "英": "United Kingdom",
                            "大不列颠": "United Kingdom"
                        })
                    elif country_name == "Germany":
                        self.country_name_mapping.update({
                            "德国": "Germany",
                            "德意志": "Germany"
                        })
                    elif country_name == "Japan":
                        self.country_name_mapping.update({
                            "日本": "Japan"
                        })
                    elif country_name == "Singapore":
                        self.country_name_mapping.update({
                            "新加坡": "Singapore"
                        })
                    elif country_name == "Australia":
                        self.country_name_mapping.update({
                            "澳大利亚": "Australia",
                            "澳洲": "Australia"
                        })
                    elif country_name == "Canada":
                        self.country_name_mapping.update({
                            "加拿大": "Canada"
                        })
            
            print(f"✅ 加载了{len(self.country_codes)}个国家代码映射")
            
        except FileNotFoundError:
            print("⚠️ 找不到serper_countries.csv，使用默认映射")
            self._load_default_country_codes()
        except Exception as e:
            print(f"⚠️ 加载国家代码时出错: {e}，使用默认映射")
            self._load_default_country_codes()
    
    def _load_default_country_codes(self):
        """加载默认的国家代码映射（备用方案）"""
        self.country_codes = {
            "united states": "US",
            "china": "CN",
            "united kingdom": "GB",
            "germany": "DE",
            "japan": "JP",
            "singapore": "SG",
            "australia": "AU",
            "canada": "CA"
        }
        
        self.country_name_mapping = {
            "美国": "United States",
            "中国": "China",
            "英国": "United Kingdom",
            "德国": "Germany",
            "日本": "Japan",
            "新加坡": "Singapore",
            "澳大利亚": "Australia",
            "加拿大": "Canada"
        }
    
    def _resolve_country_code(self, country_input: str) -> str:
        """解析国家代码"""
        if not country_input:
            return "US"  # 默认美国
        
        # 直接是代码格式（如US, CN等）
        if len(country_input) == 2 and country_input.isupper():
            return country_input
        
        # 小写代码转大写
        if len(country_input) == 2 and country_input.lower() in ['us', 'cn', 'gb', 'de', 'jp', 'sg', 'au', 'ca']:
            mapping = {
                'us': 'US', 'cn': 'CN', 'gb': 'GB', 'uk': 'GB', 
                'de': 'DE', 'jp': 'JP', 'sg': 'SG', 'au': 'AU', 'ca': 'CA'
            }
            return mapping.get(country_input.lower(), "US")
        
        # 中文名转英文名再转代码
        if country_input in self.country_name_mapping:
            english_name = self.country_name_mapping[country_input]
            return self.country_codes.get(english_name.lower(), "US")
        
        # 直接查找英文名
        return self.country_codes.get(country_input.lower(), "US")
    
    def _init_llm_client(self):
        """初始化LLM客户端"""
        if self.llm_provider == "openai":
            try:
                import openai
                self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                self.model_name = "gpt-4o-mini"  # 使用较新且便宜的模型
            except ImportError:
                print("OpenAI library not installed")
                self.client = None
                
        elif self.llm_provider == "anthropic":
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
                self.model_name = "claude-3-haiku-20240307"  # 使用快速模型
            except ImportError:
                print("Anthropic library not installed")
                self.client = None
                
        elif self.llm_provider == "google":
            try:
                import google.generativeai as genai
                genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
                self.client = genai.GenerativeModel("gemini-1.5-flash")  # 使用快速模型
                self.model_name = "gemini-1.5-flash"
            except ImportError:
                print("Google AI library not installed")
                self.client = None
                
        elif self.llm_provider == "huoshan":
            # 使用requests直接调用火山引擎API，不依赖SDK
            self.api_key = os.getenv("ARK_API_KEY")
            self.base_url = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
            self.model_name = os.getenv("ARK_MODEL", "doubao-seed-1-6-250615")
            self.client = "huoshan_http"  # 标记为HTTP调用
            print(f"✅ 火山引擎配置成功: {self.model_name}")
        else:
            print(f"Unsupported LLM provider: {self.llm_provider}")
            self.client = None
    
    def _get_cache_key(self, industry: str, target_country: str, search_type: str) -> str:
        """生成缓存键"""
        return f"{industry}|{target_country}|{search_type}".lower()
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """检查缓存是否有效"""
        return time.time() - cache_entry["timestamp"] < self.cache_ttl
    
    def _call_llm(self, prompt: str) -> Optional[str]:
        """调用LLM生成内容"""
        if not self.client:
            return None
        
        try:
            if self.llm_provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=500
                )
                return response.choices[0].message.content
                
            elif self.llm_provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=500
                )
                return response.content[0].text
                
            elif self.llm_provider == "google":
                response = self.client.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.3,
                        "max_output_tokens": 500,
                    }
                )
                return response.text
                
            elif self.llm_provider == "huoshan":
                # 使用HTTP请求调用火山引擎API
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                payload = {
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 500
                }
                
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    print(f"火山引擎API调用失败: {response.status_code} - {response.text}")
                    return None
                
        except Exception as e:
            print(f"LLM调用失败: {str(e)}")
            return None
    
    def generate_search_keywords(
        self,
        industry: str,
        target_country: str,
        search_type: str = "linkedin"
    ) -> Dict[str, Any]:
        """
        生成智能搜索关键词
        
        Args:
            industry: 行业关键词（可以是中文或英文）
            target_country: 目标国家代码 (us, cn, uk, de, jp等)
            search_type: 搜索类型 ("linkedin" 或 "general")
        
        Returns:
            Dict包含:
            - primary_keywords: 主要关键词列表
            - alternative_keywords: 备选关键词列表  
            - search_strategy: 搜索策略建议
            - serper_params: Serper API参数建议
            - success: 是否成功生成
        """
        # 检查缓存
        cache_key = self._get_cache_key(industry, target_country, search_type)
        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            print(f"✅ 使用缓存的关键词生成结果")
            return self.cache[cache_key]["data"]
        
        # 构造提示词
        prompt = self._build_keyword_prompt(industry, target_country, search_type)
        
        # 调用LLM生成关键词
        llm_response = self._call_llm(prompt)
        
        if not llm_response:
            # LLM调用失败，使用智能回退方案
            print(f"⚠️ LLM调用失败，使用智能回退方案")
            result = self._smart_simulation(industry, target_country, search_type)
            
            # 缓存回退结果
            self.cache[cache_key] = {
                "timestamp": time.time(),
                "data": result
            }
            
            print(f"✅ 回退方案生成关键词成功: {len(result.get('primary_keywords', []))} 个主关键词")
            return result
        
        # 解析LLM响应
        result = self._parse_llm_response(llm_response, industry, target_country, search_type)
        
        # 缓存结果
        self.cache[cache_key] = {
            "timestamp": time.time(),
            "data": result
        }
        
        print(f"✅ LLM生成关键词成功: {len(result.get('primary_keywords', []))} 个主关键词")
        return result
    
    def _build_keyword_prompt(self, industry: str, target_country: str, search_type: str) -> str:
        """构造LLM提示词"""
        
        # 国家信息映射
        country_info = {
            "us": {"name": "美国", "language": "英语", "business_context": "美国商业环境"},
            "cn": {"name": "中国", "language": "中文", "business_context": "中国商业环境"},
            "uk": {"name": "英国", "language": "英语", "business_context": "英国商业环境"},
            "de": {"name": "德国", "language": "德语/英语", "business_context": "德国商业环境"},
            "jp": {"name": "日本", "language": "日语/英语", "business_context": "日本商业环境"}
        }
        
        country_detail = country_info.get(target_country, {
            "name": target_country.upper(), 
            "language": "英语", 
            "business_context": f"{target_country.upper()}商业环境"
        })
        
        # 搜索类型说明
        search_context = ""
        if search_type == "linkedin":
            search_context = "这些关键词将用于LinkedIn公司搜索，需要适合LinkedIn平台的商业和职业语境。"
        else:
            search_context = "这些关键词将用于Google通用搜索，需要适合搜索引擎优化。"
        
        # 解析正确的国家代码
        resolved_country_code = self._resolve_country_code(target_country)
        
        prompt = f"""你是一个专业的国际市场研究专家和Serper.dev搜索优化专家。

任务：为以下搜索需求生成3种不同的优化查询字符串

**搜索需求：**
- 行业领域：{industry}
- 目标国家：{country_detail['name']} ({resolved_country_code})
- 主要语言：{country_detail['language']}
- 商业环境：{country_detail['business_context']}
- 搜索平台：{search_type}

**背景说明：**
{search_context}

**重要要求：**
1. 生成3种不同的完整查询字符串（不是关键词列表）
2. 每种查询针对不同搜索策略：
   - 精确匹配查询：使用引号包围的精确术语
   - 广泛匹配查询：相关术语的自然组合
   - 上下文查询：包含地域和行业上下文的描述性查询

3. 查询字符串要求：
   - 使用目标国家的本地化商业术语
   - 适合Serper.dev API的查询格式
   - 避免直译，使用地道的表达
   - 每个查询长度控制在50字符以内

4. 国家代码必须使用：{resolved_country_code}

**输出格式（必须是有效的JSON）：**
```json
{{
    "query_variants": [
        {{
            "type": "exact",
            "query": "\"具体术语\" companies",
            "description": "精确匹配策略说明"
        }},
        {{
            "type": "broad",
            "query": "相关术语 industry business",
            "description": "广泛匹配策略说明"
        }},
        {{
            "type": "contextual",
            "query": "地域化描述性查询",
            "description": "上下文策略说明"
        }}
    ],
    "country_code": "{resolved_country_code}",
    "location": "{country_detail['name']}",
    "search_strategy": "整体搜索策略描述",
    "explanation": "查询选择的理由和本地化考虑"
}}
```

**例子参考：**
美国搜索"新能源汽车":
- 精确: "electric vehicle" companies
- 广泛: EV automotive industry
- 上下文: clean energy transportation solutions

中国搜索"artificial intelligence":
- 精确: "人工智能" 公司
- 广泛: AI 科技 企业
- 上下文: 智能技术 解决方案

请现在生成针对上述需求的3种查询变体："""
        
        return prompt
    
    def _parse_llm_response(self, response: str, industry: str, target_country: str, search_type: str) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            # 尝试提取JSON内容
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_content = response[json_start:json_end]
                result = json.loads(json_content)
                
                # 验证必需的字段（新格式）
                if "query_variants" in result and len(result["query_variants"]) >= 3:
                    # 转换为兼容格式
                    converted_result = self._convert_query_variants_to_legacy(result, industry, target_country, search_type)
                    converted_result["success"] = True
                    converted_result["generated_by"] = "llm"
                    converted_result["llm_provider"] = self.llm_provider
                    return converted_result
            
            # JSON解析失败，尝试文本解析
            return self._parse_text_response(response, industry, target_country, search_type)
            
        except Exception as e:
            error_msg = f"⚠️ LLM响应解析失败: {str(e)}，使用回退方案"
            print(error_msg)
            # 使用智能模拟作为回退
            return self._smart_simulation(industry, target_country, search_type)
    
    def _convert_query_variants_to_legacy(self, llm_result: Dict, industry: str, target_country: str, search_type: str) -> Dict[str, Any]:
        """转换新的查询变体格式为兼容的旧格式"""
        query_variants = llm_result.get("query_variants", [])
        
        # 提取查询字符串作为关键词
        primary_keywords = []
        alternative_keywords = []
        
        for variant in query_variants[:3]:  # 取前3个变体
            query = variant.get("query", "")
            if query:
                primary_keywords.append(query)
        
        # 如果查询变体不足，生成备选
        if len(primary_keywords) < 3:
            primary_keywords.extend([industry, f"{industry} companies", f"{industry} business"])
        
        alternative_keywords = primary_keywords[1:4]  # 备选关键词
        
        resolved_country_code = self._resolve_country_code(target_country)
        
        return {
            "primary_keywords": primary_keywords[:5],
            "alternative_keywords": alternative_keywords[:5],
            "query_variants": query_variants,  # 保留新格式
            "search_strategy": llm_result.get("search_strategy", f"使用多变体查询策略在{resolved_country_code}搜索"),
            "serper_params": {
                "gl": resolved_country_code,
                "location": llm_result.get("location", target_country)
            },
            "explanation": llm_result.get("explanation", "LLM生成的多变体查询策略")
        }
    
    def _parse_text_response(self, response: str, industry: str, target_country: str, search_type: str) -> Dict[str, Any]:
        """解析文本格式的响应"""
        try:
            lines = response.split('\n')
            primary_keywords = []
            alternative_keywords = []
            
            # 简单的文本解析逻辑
            for line in lines:
                line = line.strip()
                if any(keyword in line.lower() for keyword in ['primary', 'main', '主要', '核心']):
                    # 提取关键词
                    keywords = [kw.strip().strip('"').strip("'") for kw in line.split(':')[-1].split(',') if kw.strip()]
                    primary_keywords.extend(keywords[:3])
                elif any(keyword in line.lower() for keyword in ['alternative', 'backup', '备选', '替代']):
                    keywords = [kw.strip().strip('"').strip("'") for kw in line.split(':')[-1].split(',') if kw.strip()]
                    alternative_keywords.extend(keywords[:3])
            
            if primary_keywords:
                return {
                    "primary_keywords": primary_keywords[:5],
                    "alternative_keywords": alternative_keywords[:5] if alternative_keywords else primary_keywords[:3],
                    "search_strategy": f"使用{target_country.upper()}本地化关键词进行搜索",
                    "serper_params": self._get_default_serper_params(target_country),
                    "success": True,
                    "generated_by": "llm_text_parse",
                    "explanation": "从LLM文本响应中解析得到的关键词"
                }
            
        except Exception as e:
            print(f"文本响应解析失败: {str(e)}")
        
        # 解析失败，使用智能回退方案
        error_msg = f"⚠️ LLM文本响应解析失败，使用回退方案"
        print(error_msg)
        return self._smart_simulation(industry, target_country, search_type)
    
    def _smart_simulation(self, industry: str, target_country: str, search_type: str) -> Dict[str, Any]:
        """智能模拟LLM关键词生成（当LLM不可用时的高级回退方案）"""
        
        resolved_country_code = self._resolve_country_code(target_country)
        
        # 智能关键词映射表 - 模拟LLM的智能分析
        smart_mappings = {
            'CA': {  # 加拿大特别优化
                '新能源汽车': [
                    'electric vehicle companies Canada', 
                    'Canadian EV manufacturers Ontario Quebec',
                    'clean transportation technology Toronto Vancouver',
                    'battery electric vehicle industry Canada',
                    'sustainable mobility solutions Canadian'
                ],
                '人工智能': [
                    'artificial intelligence companies Canada',
                    'Canadian AI startups Toronto Montreal', 
                    'machine learning technology firms Canada',
                    'AI research companies Vancouver Calgary',
                    'intelligent systems development Canadian'
                ],
                '生物技术': [
                    'biotechnology companies Canada',
                    'Canadian biotech pharmaceutical',
                    'life sciences research Canada',
                    'biomedical innovation Toronto Montreal',
                    'healthcare technology Canadian firms'
                ]
            },
            'US': {
                '新能源汽车': [
                    'electric vehicle companies United States',
                    'American EV manufacturers California Michigan',
                    'clean energy automotive Tesla competitors',
                    'electric car industry Silicon Valley Detroit',
                    'sustainable transportation technology USA'
                ],
                '人工智能': [
                    'artificial intelligence companies America',
                    'US AI technology firms Silicon Valley',
                    'machine learning startups California New York',
                    'AI research companies Boston Seattle',
                    'intelligent automation solutions USA'
                ]
            },
            'CN': {
                '新能源汽车': [
                    '新能源汽车公司 中国',
                    '电动汽车制造商 比亚迪 理想',
                    '清洁能源交通技术 深圳 上海',
                    '电池电动车行业 中国制造',
                    '可持续出行解决方案 中国企业'
                ],
                '人工智能': [
                    '人工智能公司 中国',
                    '中国AI科技企业 北京 深圳',
                    '机器学习技术公司 中国',
                    'AI研究企业 杭州 上海',
                    '智能系统开发 中国科技'
                ]
            }
        }
        
        # 获取智能关键词
        country_mappings = smart_mappings.get(resolved_country_code, smart_mappings.get('US', {}))
        industry_keywords = country_mappings.get(industry, [])
        
        # 如果没有精确匹配，使用模糊匹配
        if not industry_keywords:
            # 检查是否是英文行业名称
            english_mappings = {
                'artificial intelligence': '人工智能',
                'electric vehicle': '新能源汽车', 
                'biotechnology': '生物技术',
                'fintech': '金融科技'
            }
            
            for english, chinese in english_mappings.items():
                if english.lower() in industry.lower():
                    industry_keywords = country_mappings.get(chinese, [])
                    break
        
        # 仍然没有匹配，生成通用关键词
        if not industry_keywords:
            country_suffix = {
                'CA': 'Canada Canadian',
                'US': 'United States American USA',
                'CN': '中国 中国企业',
                'UK': 'United Kingdom British UK',
                'DE': 'Germany German Deutschland'
            }.get(resolved_country_code, f'{resolved_country_code} companies')
            
            industry_keywords = [
                f'{industry} companies {country_suffix}',
                f'{industry} industry {resolved_country_code}',
                f'{industry} business {country_suffix}'
            ]
        
        # 确保至少有5个关键词
        while len(industry_keywords) < 5:
            industry_keywords.append(f'{industry} {resolved_country_code}')
        
        return {
            "primary_keywords": industry_keywords[:5],
            "alternative_keywords": industry_keywords[1:6] if len(industry_keywords) > 5 else industry_keywords,
            "search_strategy": f"使用智能模拟关键词在{resolved_country_code}搜索{industry}",
            "serper_params": {
                "gl": resolved_country_code,
                "location": target_country
            },
            "success": True,
            "generated_by": "smart_simulation",
            "llm_provider": "simulation",
            "explanation": f"智能模拟生成了{len(industry_keywords)}个针对{resolved_country_code}的{industry}行业关键词"
        }
    
    def _fallback_translation(self, industry: str, target_country: str, search_type: str) -> Dict[str, Any]:
        """LLM调用失败时的回退翻译方案"""
        
        # 基础翻译字典（作为回退）
        resolved_country_code = self._resolve_country_code(target_country)
        
        basic_translations = {
            'US': {
                '新能源汽车': ['"electric vehicle" companies', 'EV automotive industry', 'clean energy transportation'],
                '人工智能': ['"artificial intelligence" companies', 'AI technology firms', 'machine learning solutions'],
                '生物技术': ['"biotechnology" companies', 'biotech industry', 'life sciences firms'],
                '金融科技': ['"fintech" companies', 'financial technology', 'digital banking solutions'],
                '半导体': ['"semiconductor" companies', 'chip manufacturing', 'integrated circuits industry'],
                '软件开发': ['"software development" companies', 'tech companies', 'software solutions'],
                '云计算': ['"cloud computing" companies', 'cloud services', 'SaaS providers'],
                '网络安全': ['"cybersecurity" companies', 'information security', 'network security firms']
            },
            'CN': {
                'electric vehicle': ['"新能源汽车" 公司', '电动汽车 企业', '清洁能源 交通'],
                'artificial intelligence': ['"人工智能" 公司', 'AI 科技 企业', '机器学习 解决方案'],
                'biotechnology': ['"生物技术" 公司', '生物科技 企业', '生命科学 公司'],
                'fintech': ['"金融科技" 公司', '金融技术 企业', '数字银行 解决方案'],
                'semiconductor': ['"半导体" 公司', '芯片 制造', '集成电路 产业'],
                'software': ['"软件" 公司', '软件开发 企业', '科技 公司'],
                'cloud computing': ['"云计算" 公司', '云服务 提供商', '云平台 企业'],
                'cybersecurity': ['"网络安全" 公司', '信息安全 企业', '数据安全 解决方案']
            }
        }
        
        # 查找翻译
        country_dict = basic_translations.get(resolved_country_code, {})
        queries = country_dict.get(industry.lower(), [f'"{industry}" companies', f'{industry} industry', f'{industry} business'])
        
        if not queries or queries == [f'"{industry}" companies']:
            # 没有找到翻译，生成默认查询
            queries = [f'"{industry}" companies', f'{industry} industry', f'{industry} business']
        
        print(f"⚠️ LLM不可用，使用基础翻译字典: {queries}")
        
        return {
            "primary_keywords": queries[:3],
            "alternative_keywords": queries[1:4] if len(queries) > 1 else queries,
            "query_variants": [
                {"type": "exact", "query": queries[0], "description": "精确匹配查询"},
                {"type": "broad", "query": queries[1] if len(queries) > 1 else queries[0], "description": "广泛匹配查询"},
                {"type": "contextual", "query": queries[2] if len(queries) > 2 else queries[0], "description": "上下文查询"}
            ],
            "search_strategy": f"使用基础翻译字典进行{resolved_country_code}搜索",
            "serper_params": self._get_default_serper_params(target_country),
            "success": True,
            "generated_by": "fallback_dictionary",
            "explanation": f"LLM不可用时的回退方案，使用基础翻译字典生成查询变体"
        }
    
    def _get_default_serper_params(self, target_country: str) -> Dict[str, str]:
        """获取默认的Serper API参数（简化版，按官方文档）"""
        resolved_country_code = self._resolve_country_code(target_country)
        
        # 按照官方文档，主要使用gl参数
        return {
            "gl": resolved_country_code
        }
    
    def batch_generate_keywords(self, requests: List[Dict]) -> List[Dict[str, Any]]:
        """批量生成关键词"""
        results = []
        for req in requests:
            result = self.generate_search_keywords(
                industry=req.get("industry"),
                target_country=req.get("target_country"),
                search_type=req.get("search_type", "linkedin")
            )
            result["request"] = req
            results.append(result)
        
        return results

# 全局实例
_keyword_generator = None

def get_keyword_generator() -> LLMKeywordGenerator:
    """获取全局关键词生成器实例"""
    global _keyword_generator
    if _keyword_generator is None:
        _keyword_generator = LLMKeywordGenerator()
    return _keyword_generator

# 便捷函数
def generate_keywords(industry: str, target_country: str, search_type: str = "linkedin") -> Dict[str, Any]:
    """
    便捷函数：生成搜索关键词
    
    Args:
        industry: 行业关键词
        target_country: 目标国家代码
        search_type: 搜索类型
    
    Returns:
        关键词生成结果
    """
    generator = get_keyword_generator()
    return generator.generate_search_keywords(industry, target_country, search_type)

if __name__ == "__main__":
    # 测试代码
    print("🧪 测试LLM关键词生成器...")
    
    # 测试用例
    test_cases = [
        {"industry": "新能源汽车", "target_country": "us", "search_type": "linkedin"},
        {"industry": "人工智能", "target_country": "us", "search_type": "general"},
        {"industry": "artificial intelligence", "target_country": "cn", "search_type": "linkedin"},
        {"industry": "fintech", "target_country": "uk", "search_type": "general"}
    ]
    
    generator = LLMKeywordGenerator()
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📋 测试用例 {i}: {test['industry']} in {test['target_country'].upper()}")
        result = generator.generate_search_keywords(**test)
        
        print(f"  ✅ 生成成功: {result.get('success')}")
        print(f"  🎯 主关键词: {result.get('primary_keywords')}")
        print(f"  🔄 备选关键词: {result.get('alternative_keywords')}")
        print(f"  📡 生成方式: {result.get('generated_by')}")
        if result.get('explanation'):
            print(f"  💡 说明: {result.get('explanation')[:80]}...")