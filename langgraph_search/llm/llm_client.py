"""
LLM客户端接口
支持多种LLM提供商（OpenAI、Anthropic、Google、火山引擎）
"""

import os
import json
from typing import List, Dict, Any, Optional
import logging
from dotenv import load_dotenv

# 确保加载环境变量
load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)

# 尝试导入各种LLM库
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

# 火山引擎SDK
try:
    from volcengine.maas import MaasService
    VOLCANO_AVAILABLE = True
except ImportError:
    VOLCANO_AVAILABLE = False


class LLMClient:
    """统一的LLM客户端接口"""
    
    def __init__(self):
        """初始化LLM客户端"""
        self.provider = os.getenv("LLM_PROVIDER", "none").lower()
        self.client = None
        
        # 初始化对应的客户端
        if self.provider == "openai" and OPENAI_AVAILABLE:
            self._init_openai()
        elif self.provider == "anthropic" and ANTHROPIC_AVAILABLE:
            self._init_anthropic()
        elif self.provider == "google" and GOOGLE_AVAILABLE:
            self._init_google()
        elif self.provider == "huoshan" and VOLCANO_AVAILABLE:
            self._init_volcano()
        else:
            logger.warning(f"LLM provider '{self.provider}' not available or set to 'none'")
    
    def _init_openai(self):
        """初始化OpenAI客户端"""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            openai.api_key = api_key
            self.client = openai
            logger.info("OpenAI client initialized")
        else:
            logger.warning("OPENAI_API_KEY not found")
    
    def _init_anthropic(self):
        """初始化Anthropic客户端"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            self.client = anthropic.Anthropic(api_key=api_key)
            logger.info("Anthropic client initialized")
        else:
            logger.warning("ANTHROPIC_API_KEY not found")
    
    def _init_google(self):
        """初始化Google客户端"""
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.client = genai
            logger.info("Google Generative AI client initialized")
        else:
            logger.warning("GOOGLE_API_KEY not found")
    
    def _init_volcano(self):
        """初始化火山引擎客户端"""
        api_key = os.getenv("ARK_API_KEY")
        base_url = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
        model = os.getenv("ARK_MODEL", "doubao-seed-1-6-250615")
        
        if api_key:
            # 使用requests库进行HTTP调用（火山引擎SDK可能不可用）
            self.client = "huoshan"  # 标记为火山引擎
            self.ark_api_key = api_key
            self.ark_base_url = base_url
            self.volcano_model = model
            logger.info("Volcano Engine client initialized (using HTTP)")
        else:
            logger.warning("ARK_API_KEY not found")
    
    def call_llm(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        调用LLM生成响应
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            **kwargs: 其他参数（如temperature、max_tokens等）
            
        Returns:
            生成的响应文本
        """
        if not self.client:
            # 如果没有可用的LLM，返回默认响应
            return self._get_default_response(messages)
        
        try:
            if self.provider == "openai":
                return self._call_openai(messages, **kwargs)
            elif self.provider == "anthropic":
                return self._call_anthropic(messages, **kwargs)
            elif self.provider == "google":
                return self._call_google(messages, **kwargs)
            elif self.provider == "huoshan":
                return self._call_volcano(messages, **kwargs)
            else:
                return self._get_default_response(messages)
                
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
    
    def _call_openai(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """调用OpenAI API"""
        response = openai.ChatCompletion.create(
            model=kwargs.get("model", "gpt-3.5-turbo"),
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 1000)
        )
        return response.choices[0].message.content
    
    def _call_anthropic(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """调用Anthropic API"""
        # 转换消息格式
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        
        response = self.client.completions.create(
            model=kwargs.get("model", "claude-2"),
            prompt=f"\n\nHuman: {prompt}\n\nAssistant:",
            max_tokens_to_sample=kwargs.get("max_tokens", 1000),
            temperature=kwargs.get("temperature", 0.7)
        )
        return response.completion
    
    def _call_google(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """调用Google Generative AI"""
        model = self.client.GenerativeModel(kwargs.get("model", "gemini-pro"))
        
        # 转换消息格式
        prompt = "\n".join([f"{msg['content']}" for msg in messages])
        
        response = model.generate_content(prompt)
        return response.text
    
    def _call_volcano(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """调用火山引擎API (使用OpenAI兼容接口)"""
        try:
            # 使用OpenAI客户端调用火山引擎
            import openai
            import importlib.metadata
            
            try:
                openai_version = importlib.metadata.version("openai")
                is_old_version = int(openai_version.split('.')[0]) < 1
            except:
                is_old_version = True
            
            if is_old_version:
                # 旧版本OpenAI库调用方式
                openai.api_base = self.ark_base_url
                openai.api_key = self.ark_api_key
                
                response = openai.ChatCompletion.create(
                    model=self.volcano_model,
                    messages=messages,
                    temperature=kwargs.get("temperature", 0.7),
                    max_tokens=kwargs.get("max_tokens", 1000)
                )
                
                return response.choices[0].message.content.strip()
            else:
                # 新版本OpenAI库调用方式
                client = openai.OpenAI(
                    base_url=self.ark_base_url,
                    api_key=self.ark_api_key
                )
                
                completion = client.chat.completions.create(
                    model=self.volcano_model,
                    messages=messages,
                    temperature=kwargs.get("temperature", 0.7),
                    max_tokens=kwargs.get("max_tokens", 1000)
                )
                
                return completion.choices[0].message.content.strip()
                
        except Exception as e:
            logger.error(f"Volcano API call failed: {e}")
            return self._get_default_response(messages)
    
    def _get_default_response(self, messages: List[Dict[str, str]]) -> str:
        """获取默认响应（无LLM时使用）"""
        user_content = messages[0]["content"] if messages else ""
        
        # 基于简单规则的响应
        if "评估" in user_content or "evaluate" in user_content.lower():
            return json.dumps({
                "ai_score": 75.0,
                "ai_reason": "基础评估（无LLM可用）"
            }, ensure_ascii=False)
        
        return "由于LLM服务不可用，使用基础评估模式。"
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """
        生成响应（兼容旧接口）
        
        Args:
            prompt: 提示文本
            **kwargs: 其他参数
            
        Returns:
            生成的响应
        """
        messages = [{"role": "user", "content": prompt}]
        return self.call_llm(messages, **kwargs)
    
    def is_available(self) -> bool:
        """检查LLM客户端是否可用"""
        return self.client is not None


# 全局实例
_global_llm_client: Optional[LLMClient] = None

def get_llm_client() -> LLMClient:
    """获取全局LLM客户端实例"""
    global _global_llm_client
    if _global_llm_client is None:
        _global_llm_client = LLMClient()
    return _global_llm_client