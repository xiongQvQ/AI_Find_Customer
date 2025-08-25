#!/usr/bin/env python3
"""
AI分析功能演示
展示AI分析的完整流程和结果格式
"""

import json
from datetime import datetime

def demo_ai_analysis():
    """演示AI分析功能"""
    
    print("🤖 AI智能分析功能演示")
    print("=" * 60)
    
    # 模拟公司数据
    demo_companies = [
        {
            'name': 'Tesla Energy',
            'title': 'Clean Energy and Electric Vehicle Company',
            'description': 'Tesla designs and manufactures electric vehicles, energy storage systems, and solar panels for residential and commercial use.',
            'domain': 'tesla.com',
            'emails': 'info@tesla.com',
            'phones': '+1-510-249-3400',
            'linkedin': 'https://linkedin.com/company/tesla-motors',
            'employee_titles': 'CEO | CTO | VP of Energy | Sales Director'
        },
        {
            'name': 'First Solar Inc',
            'title': 'Leading American Solar Panel Manufacturer',
            'description': 'First Solar is a leading global provider of comprehensive photovoltaic solar solutions.',
            'domain': 'firstsolar.com',
            'emails': 'info@firstsolar.com',
            'phones': '+1-602-414-9300',
            'linkedin': 'https://linkedin.com/company/first-solar',
            'employee_titles': 'CEO | VP Manufacturing | Director of Sales'
        },
        {
            'name': 'Local Coffee Shop',
            'title': 'Small Local Coffee Business',
            'description': 'A small local coffee shop serving the community with fresh roasted coffee.',
            'domain': 'localcoffee.com',
            'emails': '',
            'phones': '',
            'linkedin': '',
            'employee_titles': ''
        }
    ]
    
    # 目标客户画像
    target_profile = """
    我们的目标客户是从事可再生能源业务的大中型企业，特别是：
    - 太阳能设备制造商和分销商
    - 清洁能源项目开发商
    - 电池储能系统供应商
    - 具有国际业务的企业
    - 年营收1000万美元以上的公司
    """
    
    print("🎯 目标客户画像:")
    print(target_profile.strip())
    print("\n" + "="*60)
    
    # 模拟AI分析结果
    demo_results = [
        {
            'company_name': 'Tesla Energy',
            'final_score': 92.5,
            'dimension_scores': {
                'industry_match': 95,
                'business_scale': 98,
                'decision_accessibility': 85,
                'growth_potential': 90
            },
            'analysis_summary': 'Tesla Energy作为全球领先的储能和太阳能解决方案提供商，具有极高的行业匹配度、庞大的商业规模和强劲的增长潜力，是理想的B2B合作伙伴。',
            'key_insights': [
                '在清洁能源领域具有技术领导地位',
                '拥有完整的产业链和全球业务网络',
                '高管团队在行业内具有强大影响力',
                '持续的研发投入和技术创新能力'
            ],
            'risk_factors': [
                'CEO个人影响力较大，存在关键人风险',
                '股价波动可能影响投资决策'
            ],
            'opportunities': [
                '大规模储能项目合作机会',
                '全球市场扩张的供应链合作',
                '技术创新领域的深度合作'
            ],
            'recommended_actions': [
                '立即联系其供应链负责人',
                '准备大客户专属解决方案',
                '重点突出国际化服务能力',
                '展示在储能领域的技术优势'
            ],
            'confidence_level': 'high',
            'tags': ['🎯 行业高匹配', '🏢 大型企业', '👥 决策者易接触', '🚀 高增长潜力', '✅ 分析可信度高'],
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'llm_provider': 'demo_ai'
        },
        {
            'company_name': 'First Solar Inc',
            'final_score': 88.2,
            'dimension_scores': {
                'industry_match': 98,
                'business_scale': 85,
                'decision_accessibility': 80,
                'growth_potential': 85
            },
            'analysis_summary': 'First Solar作为美国领先的太阳能面板制造商，在行业匹配度方面表现出色，具有稳定的商业规模和良好的增长前景。',
            'key_insights': [
                '专注于薄膜太阳能技术，具有技术差异化',
                '在美国本土制造，符合政策导向',
                '拥有完整的制造和销售网络',
                '财务状况稳健，现金流良好'
            ],
            'risk_factors': [
                '技术路线相对单一，存在技术风险',
                '面临来自中国制造商的价格竞争'
            ],
            'opportunities': [
                '美国本土制造优势明显',
                '政府政策支持力度大',
                '大型地面电站项目合作机会'
            ],
            'recommended_actions': [
                '联系其商务拓展部门',
                '准备本土化服务方案',
                '重点展示成本优势',
                '提供定制化解决方案'
            ],
            'confidence_level': 'high',
            'tags': ['🎯 行业高匹配', '🏬 中型企业', '👤 决策者可接触', '📈 中等增长潜力', '✅ 分析可信度高'],
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'llm_provider': 'demo_ai'
        },
        {
            'company_name': 'Local Coffee Shop',
            'final_score': 15.8,
            'dimension_scores': {
                'industry_match': 5,
                'business_scale': 20,
                'decision_accessibility': 30,
                'growth_potential': 15
            },
            'analysis_summary': '当地咖啡店与可再生能源业务不匹配，规模较小，不符合目标客户画像要求。',
            'key_insights': [
                '属于传统服务业，与目标行业无关',
                '规模较小，购买力有限',
                '本地化经营，国际业务机会较少'
            ],
            'risk_factors': [
                '行业完全不匹配',
                '没有相关业务需求',
                '预算和采购能力有限'
            ],
            'opportunities': [
                '可能有小规模节能设备需求',
                '作为展示案例的潜在价值'
            ],
            'recommended_actions': [
                '不建议作为重点客户',
                '可考虑作为本地案例展示',
                '关注其他相关行业客户'
            ],
            'confidence_level': 'high',
            'tags': ['❓ 行业待确认', '🏪 小型企业', '👤 决策者可接触', '📉 增长潜力有限', '✅ 分析可信度高'],
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'llm_provider': 'demo_ai'
        }
    ]
    
    # 显示分析结果
    print("📊 AI分析结果:")
    print("\n" + "="*60)
    
    for i, result in enumerate(demo_results, 1):
        print(f"\n{i}. 【{result['company_name']}】")
        print(f"   🎯 综合得分: {result['final_score']}/100")
        print(f"   📝 分析摘要: {result['analysis_summary']}")
        print(f"   🏷️  智能标签: {' | '.join(result['tags'])}")
        
        print(f"   📊 维度得分:")
        for dim, score in result['dimension_scores'].items():
            dim_names = {
                'industry_match': '行业匹配度',
                'business_scale': '商业规模', 
                'decision_accessibility': '决策者可达性',
                'growth_potential': '增长潜力'
            }
            print(f"      • {dim_names[dim]}: {score}/100")
        
        print(f"   💡 关键洞察:")
        for insight in result['key_insights']:
            print(f"      • {insight}")
        
        print(f"   🚨 风险因素:")
        for risk in result['risk_factors']:
            print(f"      • {risk}")
        
        print(f"   🚀 合作机会:")
        for opportunity in result['opportunities']:
            print(f"      • {opportunity}")
        
        print(f"   📋 建议行动:")
        for action in result['recommended_actions']:
            print(f"      • {action}")
        
        print(f"   ⏱️  分析时间: {result['analysis_time']}")
        print(f"   🧠 AI置信度: {result['confidence_level']}")
    
    # 生成统计报告
    print(f"\n" + "="*60)
    print("📈 分析统计报告:")
    
    avg_score = sum(r['final_score'] for r in demo_results) / len(demo_results)
    max_score = max(r['final_score'] for r in demo_results)
    high_score_count = len([r for r in demo_results if r['final_score'] >= 70])
    
    print(f"   📊 分析公司总数: {len(demo_results)} 家")
    print(f"   📊 平均得分: {avg_score:.1f}/100")
    print(f"   🏆 最高得分: {max_score:.1f}/100")
    print(f"   ⭐ 优质客户数: {high_score_count} 家 (得分≥70)")
    
    # 推荐行动计划
    print(f"\n🎯 推荐行动计划:")
    
    # 按得分排序
    sorted_results = sorted(demo_results, key=lambda x: x['final_score'], reverse=True)
    
    print("   💎 立即重点跟进:")
    for result in sorted_results:
        if result['final_score'] >= 80:
            print(f"      • {result['company_name']} (得分: {result['final_score']:.1f})")
    
    print("   📞 可适度接触:")
    for result in sorted_results:
        if 60 <= result['final_score'] < 80:
            print(f"      • {result['company_name']} (得分: {result['final_score']:.1f})")
    
    print("   ⏳ 低优先级:")
    for result in sorted_results:
        if result['final_score'] < 60:
            print(f"      • {result['company_name']} (得分: {result['final_score']:.1f})")
    
    print(f"\n🎉 AI智能分析演示完成！")
    print("🌐 访问 http://localhost:8501 体验完整的Web界面")
    
    return demo_results

if __name__ == "__main__":
    demo_ai_analysis()