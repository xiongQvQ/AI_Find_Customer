#!/usr/bin/env python3
"""
AI客户发现工具 - 智能AI分析系统
使用大语言模型进行深度客户分析、评分和标签化

核心功能：
1. LLM驱动的行业匹配度分析
2. 智能客户价值评估
3. 决策者重要性分析
4. 自动标签生成
5. 个性化分析报告
"""

import os
import json
import openai
import requests
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, List, Tuple, Any, Optional
import time

load_dotenv()

class AIAnalyzer:
    """基于LLM的智能客户分析器"""
    
    def __init__(self, provider: str = None):
        """
        初始化AI分析器
        
        Args:
            provider: LLM提供商 (openai, anthropic, google, huoshan)
        """
        self.provider = provider or os.getenv('LLM_PROVIDER', 'openai')
        self.setup_llm_client()
        
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
    
    def setup_llm_client(self):
        """设置LLM客户端"""
        if self.provider == 'openai':
            openai.api_key = os.getenv('OPENAI_API_KEY')
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
    
    def call_llm(self, prompt: str, system_prompt: str = None) -> str:
        """
        调用LLM API
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            
        Returns:
            str: LLM响应结果
        """
        if not self.provider:
            return "无法调用LLM - 未配置API密钥"
        
        try:
            if self.provider == 'openai':
                client = openai.OpenAI(api_key=openai.api_key)
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt or "你是一个专业的B2B客户分析专家。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1500
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
                    'max_tokens': 1500,
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
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result['content'][0]['text'].strip()
                else:
                    return f"API调用失败: {response.status_code}"
                    
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
                    'max_tokens': 1500
                }
                
                response = requests.post(
                    f'{self.ark_base_url}/chat/completions',
                    headers=headers,
                    json=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result['choices'][0]['message']['content'].strip()
                else:
                    return f"API调用失败: {response.status_code}"
                    
        except Exception as e:
            print(f"LLM调用错误: {e}")
            return f"分析失败: {str(e)}"
        
        return "不支持的LLM提供商"
    
    def analyze_company(self, company_data: Dict[str, Any], target_profile: str) -> Dict[str, Any]:
        """
        对单个公司进行AI分析
        
        Args:
            company_data: 公司数据字典
            target_profile: 目标客户画像描述
            
        Returns:
            Dict: 分析结果
        """
        # 构建公司描述
        company_description = self._build_company_description(company_data)
        
        # 构建分析提示词
        analysis_prompt = self._build_analysis_prompt(company_description, target_profile)
        
        # 系统提示词
        system_prompt = """你是一个资深的B2B销售分析专家，专门分析潜在客户的商业价值。
        
请根据提供的公司信息和目标客户画像，进行深度分析并返回JSON格式的结果。

分析维度：
1. 行业匹配度 (0-100) - 公司业务与目标市场的契合程度
2. 商业规模 (0-100) - 公司规模和购买力评估  
3. 决策者可达性 (0-100) - 关键决策者的识别和接触难易度
4. 增长潜力 (0-100) - 未来业务增长和合作机会

请确保返回标准的JSON格式。"""
        
        # 调用LLM进行分析
        llm_response = self.call_llm(analysis_prompt, system_prompt)
        
        # 解析LLM响应
        analysis_result = self._parse_llm_response(llm_response)
        
        # 计算最终得分
        final_score = self._calculate_final_score(analysis_result)
        
        # 生成标签
        tags = self._generate_ai_tags(analysis_result, company_description)
        
        return {
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
            'raw_llm_response': llm_response  # 用于调试
        }
    
    def _build_company_description(self, company_data: Dict[str, Any]) -> str:
        """构建公司描述文本"""
        description_parts = []
        
        # 基础信息
        if company_data.get('name'):
            description_parts.append(f"公司名称: {company_data['name']}")
        
        if company_data.get('title'):
            description_parts.append(f"公司标题: {company_data['title']}")
        
        if company_data.get('description'):
            description_parts.append(f"业务描述: {company_data['description']}")
        
        if company_data.get('domain'):
            description_parts.append(f"网站域名: {company_data['domain']}")
        
        # 联系信息
        contact_info = []
        if company_data.get('emails'):
            contact_info.append(f"邮箱: {company_data['emails']}")
        if company_data.get('phones'):
            contact_info.append(f"电话: {company_data['phones']}")
        if company_data.get('linkedin'):
            contact_info.append(f"LinkedIn: {company_data['linkedin']}")
        
        if contact_info:
            description_parts.append(f"联系信息: {', '.join(contact_info)}")
        
        # 员工信息
        if company_data.get('employee_titles'):
            description_parts.append(f"关键职位: {company_data['employee_titles']}")
        
        return '\n'.join(description_parts)
    
    def _build_analysis_prompt(self, company_description: str, target_profile: str) -> str:
        """构建分析提示词"""
        return f"""请分析以下公司作为潜在B2B客户的价值：

目标客户画像：
{target_profile}

公司信息：
{company_description}

请从以下四个维度进行评分 (0-100分)：
1. 行业匹配度 - 公司业务与我们目标市场的匹配程度
2. 商业规模 - 公司规模和购买力评估
3. 决策者可达性 - 关键决策者的识别和接触难易度  
4. 增长潜力 - 未来业务增长和合作机会

请返回JSON格式结果，包含：
{{
  "scores": {{
    "industry_match": 85,
    "business_scale": 75,
    "decision_accessibility": 60,
    "growth_potential": 80
  }},
  "summary": "一句话总结这家公司的商业价值",
  "insights": ["关键洞察1", "关键洞察2", "关键洞察3"],
  "risks": ["潜在风险1", "潜在风险2"],
  "opportunities": ["合作机会1", "合作机会2"],
  "actions": ["建议行动1", "建议行动2"],
  "confidence": "high|medium|low"
}}"""
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应为结构化数据"""
        try:
            # 尝试提取JSON内容
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                # 如果没有找到JSON，返回默认结构
                return {
                    'scores': {
                        'industry_match': 50,
                        'business_scale': 50,
                        'decision_accessibility': 50,
                        'growth_potential': 50
                    },
                    'summary': response[:200] + "..." if len(response) > 200 else response,
                    'insights': ["分析内容格式化失败"],
                    'risks': [],
                    'opportunities': [],
                    'actions': [],
                    'confidence': 'low'
                }
        except Exception as e:
            print(f"解析LLM响应失败: {e}")
            return {
                'scores': {'industry_match': 0, 'business_scale': 0, 'decision_accessibility': 0, 'growth_potential': 0},
                'summary': "分析失败",
                'insights': [f"解析错误: {str(e)}"],
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
        
        # 基于各维度得分生成标签
        if scores.get('industry_match', 0) >= 80:
            tags.append('🎯 行业高匹配')
        elif scores.get('industry_match', 0) >= 60:
            tags.append('📊 行业中匹配')
        else:
            tags.append('❓ 行业待确认')
        
        if scores.get('business_scale', 0) >= 80:
            tags.append('🏢 大型企业')
        elif scores.get('business_scale', 0) >= 60:
            tags.append('🏬 中型企业')
        else:
            tags.append('🏪 小型企业')
        
        if scores.get('decision_accessibility', 0) >= 80:
            tags.append('👥 决策者易接触')
        elif scores.get('decision_accessibility', 0) >= 60:
            tags.append('👤 决策者可接触')
        else:
            tags.append('🔒 决策者难接触')
        
        if scores.get('growth_potential', 0) >= 80:
            tags.append('🚀 高增长潜力')
        elif scores.get('growth_potential', 0) >= 60:
            tags.append('📈 中等增长潜力')
        else:
            tags.append('📉 增长潜力有限')
        
        # 基于置信度添加标签
        confidence = analysis_result.get('confidence', 'medium')
        if confidence == 'high':
            tags.append('✅ 分析可信度高')
        elif confidence == 'low':
            tags.append('⚠️ 分析可信度低')
        
        return tags
    
    def batch_analyze_companies(self, companies_data: List[Dict[str, Any]], 
                               target_profile: str, 
                               callback=None) -> List[Dict[str, Any]]:
        """
        批量分析公司列表
        
        Args:
            companies_data: 公司数据列表
            target_profile: 目标客户画像
            callback: 进度回调函数
            
        Returns:
            List: 分析结果列表
        """
        results = []
        total = len(companies_data)
        
        for i, company_data in enumerate(companies_data):
            if callback:
                callback(i + 1, total, company_data.get('name', 'Unknown'))
            
            try:
                analysis_result = self.analyze_company(company_data, target_profile)
                results.append(analysis_result)
                
                # 添加延迟避免API限流
                time.sleep(0.5)
                
            except Exception as e:
                print(f"分析公司 {company_data.get('name')} 时出错: {e}")
                # 添加错误结果
                results.append({
                    'company_name': company_data.get('name', 'Unknown'),
                    'final_score': 0,
                    'error': str(e),
                    'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        
        return results

def main():
    """测试AI分析器"""
    # 示例公司数据
    test_company = {
        'name': 'Tesla Energy',
        'title': 'Clean Energy and Electric Vehicle Company',
        'description': 'Tesla designs and manufactures electric vehicles, energy storage systems, and solar panels.',
        'domain': 'tesla.com',
        'emails': 'info@tesla.com',
        'phones': '+1-510-249-3400',
        'linkedin': 'https://linkedin.com/company/tesla-motors',
        'employee_titles': 'CEO | CTO | VP of Energy | Sales Director'
    }
    
    # 目标客户画像
    target_profile = """
    我们的目标客户是从事可再生能源业务的大中型企业，特别是：
    - 太阳能设备制造商和分销商
    - 清洁能源项目开发商
    - 电池储能系统供应商
    - 具有国际业务的企业
    - 年营收1000万美元以上的公司
    """
    
    # 初始化AI分析器
    analyzer = AIAnalyzer()
    
    # 分析公司
    print("🤖 开始AI分析...")
    result = analyzer.analyze_company(test_company, target_profile)
    
    print("\n📊 分析结果:")
    print(f"公司名称: {result['company_name']}")
    print(f"综合得分: {result['final_score']}/100")
    print(f"分析摘要: {result['analysis_summary']}")
    print(f"标签: {', '.join(result['tags'])}")
    print(f"LLM提供商: {result['llm_provider']}")

if __name__ == "__main__":
    main()