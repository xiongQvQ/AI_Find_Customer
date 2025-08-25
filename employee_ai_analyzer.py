#!/usr/bin/env python3
"""
AI客户发现工具 - 员工智能AI分析系统
使用大语言模型深度分析员工价值、影响力和联系优先级

核心功能：
1. LLM驱动的员工价值分析
2. 决策影响力评估
3. 联系优先级智能排序
4. 组织架构洞察
5. 个性化联系策略建议
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

class EmployeeAIAnalyzer:
    """基于LLM的智能员工分析器"""
    
    def __init__(self, provider: str = None):
        """
        初始化员工AI分析器
        
        Args:
            provider: LLM提供商 (openai, anthropic, google, huoshan)
        """
        self.provider = provider or os.getenv('LLM_PROVIDER', 'openai')
        self.setup_llm_client()
        
        # 员工评分维度配置
        self.scoring_dimensions = {
            'decision_power': {
                'weight': 0.35,
                'description': '决策权力 - 在采购和商业决策中的影响力'
            },
            'accessibility': {
                'weight': 0.25, 
                'description': '可接触性 - 联系和建立关系的难易程度'
            },
            'role_relevance': {
                'weight': 0.25,
                'description': '角色相关性 - 职位与业务需求的匹配度'
            },
            'network_influence': {
                'weight': 0.15,
                'description': '网络影响力 - 在组织内外的人脉和影响力'
            }
        }
        
        # 职位权重映射
        self.position_weights = {
            # C级高管
            'CEO': 100, 'Chief Executive Officer': 100, 'President': 95,
            'CTO': 95, 'Chief Technology Officer': 95, 'CIO': 95,
            'CFO': 90, 'Chief Financial Officer': 90, 'COO': 90,
            
            # VP级别
            'VP': 85, 'Vice President': 85, 'SVP': 88, 'EVP': 90,
            
            # 总监级别
            'Director': 75, 'Managing Director': 80, 'Executive Director': 78,
            
            # 部门负责人
            'Head of': 70, 'Department Head': 70,
            
            # 采购相关
            'Procurement': 85, 'Purchasing': 85, 'Supply Chain': 80, 'Sourcing': 75,
            
            # 技术相关
            'IT Manager': 65, 'IT Director': 75, 'CTO': 95, 'Tech Lead': 60,
            
            # 销售商务
            'Sales Director': 80, 'Business Development': 75, 'Sales Manager': 65,
            
            # 运营相关
            'Operations': 70, 'Plant Manager': 75, 'General Manager': 80,
            
            # 经理级别
            'Manager': 55, 'Senior Manager': 65, 'Project Manager': 55,
            
            # 专员/专家
            'Specialist': 40, 'Analyst': 35, 'Coordinator': 35, 'Assistant': 25
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
        """调用LLM API"""
        if not self.provider:
            return "无法调用LLM - 未配置API密钥"
        
        try:
            if self.provider == 'openai':
                client = openai.OpenAI(api_key=openai.api_key)
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt or "你是一个专业的B2B销售和人力资源分析专家。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1200
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
                    'system': system_prompt or "你是一个专业的B2B销售和人力资源分析专家。",
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
                        {"role": "system", "content": system_prompt or "你是一个专业的B2B销售和人力资源分析专家。"},
                        {"role": "user", "content": prompt}
                    ],
                    'temperature': 0.3,
                    'max_tokens': 1200
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
    
    def analyze_employee(self, employee_data: Dict[str, Any], business_context: str) -> Dict[str, Any]:
        """
        对单个员工进行AI分析
        
        Args:
            employee_data: 员工数据字典
            business_context: 业务背景和需求描述
            
        Returns:
            Dict: 分析结果
        """
        # 构建员工描述
        employee_description = self._build_employee_description(employee_data)
        
        # 构建分析提示词
        analysis_prompt = self._build_employee_analysis_prompt(employee_description, business_context)
        
        # 系统提示词
        system_prompt = """你是一个资深的B2B销售和组织行为分析专家，专门分析企业员工的商业价值和联系策略。

请根据提供的员工信息和业务背景，进行深度分析并返回JSON格式的结果。

分析维度：
1. 决策权力 (0-100) - 在采购和商业决策中的影响力
2. 可接触性 (0-100) - 联系和建立关系的难易程度
3. 角色相关性 (0-100) - 职位与业务需求的匹配度  
4. 网络影响力 (0-100) - 在组织内外的人脉和影响力

请确保返回标准的JSON格式。"""
        
        # 调用LLM进行分析
        llm_response = self.call_llm(analysis_prompt, system_prompt)
        
        # 解析LLM响应
        analysis_result = self._parse_llm_response(llm_response)
        
        # 计算最终得分
        final_score = self._calculate_employee_final_score(analysis_result)
        
        # 生成标签
        tags = self._generate_employee_tags(analysis_result, employee_data)
        
        # 确定联系优先级
        priority_level = self._determine_priority_level(final_score, analysis_result)
        
        return {
            'employee_name': employee_data.get('name', 'Unknown'),
            'title': employee_data.get('title', 'Unknown'),
            'company': employee_data.get('company', 'Unknown'),
            'final_score': final_score,
            'priority_level': priority_level,
            'dimension_scores': analysis_result.get('scores', {}),
            'analysis_summary': analysis_result.get('summary', ''),
            'key_insights': analysis_result.get('insights', []),
            'contact_strategy': analysis_result.get('strategy', []),
            'potential_value': analysis_result.get('value', ''),
            'recommended_approach': analysis_result.get('approach', []),
            'contact_timing': analysis_result.get('timing', 'immediate'),
            'confidence_level': analysis_result.get('confidence', 'medium'),
            'tags': tags,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'llm_provider': self.provider,
            'raw_llm_response': llm_response  # 用于调试
        }
    
    def _build_employee_description(self, employee_data: Dict[str, Any]) -> str:
        """构建员工描述文本"""
        description_parts = []
        
        # 基础信息
        if employee_data.get('name'):
            description_parts.append(f"姓名: {employee_data['name']}")
        
        if employee_data.get('title'):
            description_parts.append(f"职位: {employee_data['title']}")
        
        if employee_data.get('company'):
            description_parts.append(f"公司: {employee_data['company']}")
        
        if employee_data.get('description'):
            description_parts.append(f"简介: {employee_data['description']}")
        
        # 联系信息
        contact_info = []
        if employee_data.get('email'):
            contact_info.append(f"邮箱: {employee_data['email']}")
        if employee_data.get('phone'):
            contact_info.append(f"电话: {employee_data['phone']}")
        if employee_data.get('linkedin_url'):
            contact_info.append(f"LinkedIn: {employee_data['linkedin_url']}")
        
        if contact_info:
            description_parts.append(f"联系方式: {', '.join(contact_info)}")
        
        # 社交媒体
        if employee_data.get('twitter'):
            description_parts.append(f"Twitter: {employee_data['twitter']}")
        if employee_data.get('github'):
            description_parts.append(f"GitHub: {employee_data['github']}")
        
        return '\n'.join(description_parts)
    
    def _build_employee_analysis_prompt(self, employee_description: str, business_context: str) -> str:
        """构建员工分析提示词"""
        return f"""请分析以下员工作为B2B销售目标联系人的价值：

业务背景：
{business_context}

员工信息：
{employee_description}

请从以下四个维度进行评分 (0-100分)：
1. 决策权力 - 在采购和商业决策中的影响力
2. 可接触性 - 联系和建立关系的难易程度
3. 角色相关性 - 职位与我们业务需求的匹配度
4. 网络影响力 - 在组织内外的人脉和影响力

请返回JSON格式结果，包含：
{{
  "scores": {{
    "decision_power": 75,
    "accessibility": 60,
    "role_relevance": 85,
    "network_influence": 70
  }},
  "summary": "一句话总结这位员工的联系价值",
  "insights": ["关键洞察1", "关键洞察2", "关键洞察3"],
  "strategy": ["联系策略1", "联系策略2"],
  "value": "此人对我们业务的潜在价值",
  "approach": ["建议接触方式1", "建议接触方式2"],
  "timing": "immediate|soon|later",
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
                        'decision_power': 50,
                        'accessibility': 50,
                        'role_relevance': 50,
                        'network_influence': 50
                    },
                    'summary': response[:150] + "..." if len(response) > 150 else response,
                    'insights': ["分析内容格式化失败"],
                    'strategy': ["需要进一步分析"],
                    'value': "待评估",
                    'approach': ["标准商务联系"],
                    'timing': 'later',
                    'confidence': 'low'
                }
        except Exception as e:
            print(f"解析LLM响应失败: {e}")
            return {
                'scores': {'decision_power': 0, 'accessibility': 0, 'role_relevance': 0, 'network_influence': 0},
                'summary': "分析失败",
                'insights': [f"解析错误: {str(e)}"],
                'strategy': [],
                'value': "未知",
                'approach': [],
                'timing': 'later',
                'confidence': 'low'
            }
    
    def _calculate_employee_final_score(self, analysis_result: Dict[str, Any]) -> float:
        """计算员工最终综合得分"""
        scores = analysis_result.get('scores', {})
        
        final_score = 0
        for dimension, config in self.scoring_dimensions.items():
            score = scores.get(dimension, 0)
            final_score += score * config['weight']
        
        return round(final_score, 2)
    
    def _generate_employee_tags(self, analysis_result: Dict[str, Any], employee_data: Dict[str, Any]) -> List[str]:
        """基于AI分析结果生成员工智能标签"""
        tags = []
        scores = analysis_result.get('scores', {})
        
        # 基于决策权力的标签
        if scores.get('decision_power', 0) >= 80:
            tags.append('👑 决策层核心')
        elif scores.get('decision_power', 0) >= 60:
            tags.append('📊 中层管理')
        else:
            tags.append('👤 执行层员工')
        
        # 基于可接触性的标签
        if scores.get('accessibility', 0) >= 80:
            tags.append('🤝 易于接触')
        elif scores.get('accessibility', 0) >= 60:
            tags.append('📞 中等难度')
        else:
            tags.append('🔒 接触困难')
        
        # 基于角色相关性的标签
        if scores.get('role_relevance', 0) >= 80:
            tags.append('🎯 高度相关')
        elif scores.get('role_relevance', 0) >= 60:
            tags.append('📋 中等相关')
        else:
            tags.append('❓ 相关性低')
        
        # 基于网络影响力的标签
        if scores.get('network_influence', 0) >= 80:
            tags.append('🌟 影响力人物')
        elif scores.get('network_influence', 0) >= 60:
            tags.append('🔗 有一定影响力')
        else:
            tags.append('📱 影响力有限')
        
        # 基于职位的标签
        title = employee_data.get('title', '').lower()
        if any(keyword in title for keyword in ['ceo', 'president', 'chief']):
            tags.append('🏆 C级高管')
        elif any(keyword in title for keyword in ['vp', 'vice president', 'director']):
            tags.append('🎖️ 高级管理')
        elif any(keyword in title for keyword in ['manager', 'head of']):
            tags.append('📈 中层管理')
        elif any(keyword in title for keyword in ['procurement', 'purchasing', 'supply']):
            tags.append('💼 采购相关')
        
        # 基于联系方式的标签
        if employee_data.get('email'):
            tags.append('📧 有邮箱')
        if employee_data.get('linkedin_url'):
            tags.append('💼 有LinkedIn')
        
        # 基于置信度添加标签
        confidence = analysis_result.get('confidence', 'medium')
        if confidence == 'high':
            tags.append('✅ 高置信度')
        elif confidence == 'low':
            tags.append('⚠️ 低置信度')
        
        return tags
    
    def _determine_priority_level(self, final_score: float, analysis_result: Dict[str, Any]) -> str:
        """确定联系优先级级别"""
        timing = analysis_result.get('timing', 'later')
        
        if final_score >= 80:
            return 'P0 - 立即联系'
        elif final_score >= 70:
            return 'P1 - 优先联系'
        elif final_score >= 60:
            return 'P2 - 适时联系'
        elif final_score >= 50:
            return 'P3 - 备选联系'
        else:
            return 'P4 - 低优先级'
    
    def batch_analyze_employees(self, employees_data: List[Dict[str, Any]], 
                               business_context: str, 
                               callback=None) -> List[Dict[str, Any]]:
        """
        批量分析员工列表
        
        Args:
            employees_data: 员工数据列表
            business_context: 业务背景描述
            callback: 进度回调函数
            
        Returns:
            List: 分析结果列表
        """
        results = []
        total = len(employees_data)
        
        for i, employee_data in enumerate(employees_data):
            if callback:
                callback(i + 1, total, employee_data.get('name', 'Unknown'))
            
            try:
                analysis_result = self.analyze_employee(employee_data, business_context)
                results.append(analysis_result)
                
                # 添加延迟避免API限流
                time.sleep(0.3)
                
            except Exception as e:
                print(f"分析员工 {employee_data.get('name')} 时出错: {e}")
                # 添加错误结果
                results.append({
                    'employee_name': employee_data.get('name', 'Unknown'),
                    'title': employee_data.get('title', 'Unknown'),
                    'company': employee_data.get('company', 'Unknown'),
                    'final_score': 0,
                    'priority_level': 'P4 - 低优先级',
                    'error': str(e),
                    'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        
        return results
    
    def analyze_team_structure(self, employees_data: List[Dict[str, Any]], 
                              business_context: str) -> Dict[str, Any]:
        """
        分析团队结构和关键联系人
        
        Args:
            employees_data: 员工数据列表
            business_context: 业务背景
            
        Returns:
            Dict: 团队分析结果
        """
        if not employees_data:
            return {}
        
        # 构建团队概览
        team_overview = f"团队规模: {len(employees_data)}人\n"
        team_overview += "职位分布:\n"
        
        # 统计职位分布
        title_counts = {}
        for emp in employees_data:
            title = emp.get('title', 'Unknown')
            title_counts[title] = title_counts.get(title, 0) + 1
        
        for title, count in sorted(title_counts.items(), key=lambda x: x[1], reverse=True):
            team_overview += f"- {title}: {count}人\n"
        
        # LLM分析团队结构
        team_prompt = f"""请分析以下团队结构，并为B2B销售提供建议：

业务背景：
{business_context}

{team_overview}

请分析：
1. 团队的决策层次结构
2. 关键决策者识别
3. 最佳接触路径
4. 团队影响力分析

返回JSON格式结果包含：
- structure_analysis: 结构分析
- key_decision_makers: 关键决策者列表
- contact_strategy: 联系策略
- influence_map: 影响力地图
"""
        
        system_prompt = "你是一个专业的组织结构和销售策略分析专家。"
        
        llm_response = self.call_llm(team_prompt, system_prompt)
        
        try:
            # 解析团队分析结果
            import re
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                team_analysis = json.loads(json_match.group())
            else:
                team_analysis = {
                    'structure_analysis': llm_response[:500],
                    'key_decision_makers': [],
                    'contact_strategy': [],
                    'influence_map': {}
                }
        except Exception as e:
            team_analysis = {
                'structure_analysis': f"分析失败: {str(e)}",
                'key_decision_makers': [],
                'contact_strategy': [],
                'influence_map': {}
            }
        
        return {
            'team_size': len(employees_data),
            'title_distribution': title_counts,
            'analysis_result': team_analysis,
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'llm_provider': self.provider
        }

def main():
    """测试员工AI分析器"""
    # 示例员工数据
    test_employees = [
        {
            'name': 'Elon Musk',
            'title': 'CEO',
            'company': 'Tesla',
            'description': 'CEO and Product Architect of Tesla, leading the company\'s vision for sustainable energy.',
            'linkedin_url': 'https://linkedin.com/in/elonmusk',
            'email': '',
            'phone': ''
        },
        {
            'name': 'John Doe',
            'title': 'VP of Procurement',
            'company': 'Tesla',
            'description': 'VP of Global Procurement responsible for supply chain and vendor relationships.',
            'linkedin_url': 'https://linkedin.com/in/johndoe',
            'email': 'john.doe@tesla.com',
            'phone': ''
        },
        {
            'name': 'Jane Smith',
            'title': 'IT Specialist',
            'company': 'Tesla',
            'description': 'IT Specialist focusing on infrastructure and technical support.',
            'linkedin_url': 'https://linkedin.com/in/janesmith',
            'email': '',
            'phone': ''
        }
    ]
    
    # 业务背景
    business_context = """
    我们是一家提供企业级云服务和IT解决方案的公司，主要服务对象是：
    - 大型制造企业的IT部门
    - 需要数字化转型的传统企业
    - 寻求云迁移和基础设施升级的公司
    - 重点关注成本优化和技术创新的采购决策者
    """
    
    # 初始化员工AI分析器
    analyzer = EmployeeAIAnalyzer()
    
    # 分析单个员工
    print("🤖 开始员工AI分析...")
    print("=" * 60)
    
    for i, employee in enumerate(test_employees, 1):
        print(f"\n{i}. 分析员工: {employee['name']} - {employee['title']}")
        result = analyzer.analyze_employee(employee, business_context)
        
        print(f"   🎯 综合得分: {result['final_score']:.1f}/100")
        print(f"   📊 优先级: {result['priority_level']}")
        print(f"   📝 分析摘要: {result['analysis_summary']}")
        print(f"   🏷️  标签: {', '.join(result['tags'][:4])}")
        print(f"   💡 关键洞察: {', '.join(result['key_insights'][:2])}")
        print(f"   🧠 AI模型: {result['llm_provider']}")
    
    # 分析团队结构
    print(f"\n" + "="*60)
    print("🏢 团队结构分析:")
    team_analysis = analyzer.analyze_team_structure(test_employees, business_context)
    print(f"   团队规模: {team_analysis.get('team_size', 0)} 人")
    print(f"   结构分析: {team_analysis.get('analysis_result', {}).get('structure_analysis', '')[:100]}...")

if __name__ == "__main__":
    main()