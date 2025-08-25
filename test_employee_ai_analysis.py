#!/usr/bin/env python3
"""
测试员工AI分析功能
验证员工AI分析器的完整功能包括个人分析和团队分析
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from employee_ai_analyzer import EmployeeAIAnalyzer

def test_employee_ai_analysis():
    """测试员工AI分析功能"""
    
    print("🧪 测试员工AI分析功能...")
    
    # 检查API配置
    from dotenv import load_dotenv
    load_dotenv()
    
    api_keys = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
        'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY'),
        'ARK_API_KEY': os.getenv('ARK_API_KEY')
    }
    
    available_providers = [k.split('_')[0].lower() for k, v in api_keys.items() if v]
    if 'ark' in available_providers:
        available_providers = [p if p != 'ark' else 'huoshan' for p in available_providers]
    
    if not available_providers:
        print("❌ 未找到可用的LLM API配置，请在.env文件中配置至少一个API密钥")
        return False
    
    provider = available_providers[0]
    print(f"✅ 使用 {provider} 作为LLM提供商")
    
    # 创建测试数据
    test_employees = [
        {
            'name': 'John Smith',
            'title': 'Chief Technology Officer',
            'company': 'Tesla Energy',
            'linkedin_url': 'https://linkedin.com/in/johnsmith',
            'description': 'CTO at Tesla Energy with 15+ years experience in renewable energy technology. Leads technical strategy and innovation for solar and battery storage solutions.',
            'email': 'john.smith@tesla.com'
        },
        {
            'name': 'Sarah Johnson',
            'title': 'VP of Procurement',
            'company': 'Tesla Energy',
            'linkedin_url': 'https://linkedin.com/in/sarahjohnson',
            'description': 'VP of Procurement responsible for supply chain strategy and vendor relationships. Expert in renewable energy component sourcing.',
            'email': 'sarah.johnson@tesla.com'
        },
        {
            'name': 'Michael Chen',
            'title': 'Project Manager',
            'company': 'Tesla Energy',
            'linkedin_url': 'https://linkedin.com/in/michaelchen',
            'description': 'Senior Project Manager overseeing large-scale solar installation projects across California.',
            'email': 'michael.chen@tesla.com'
        }
    ]
    
    business_context = """
    我们是一家可再生能源解决方案提供商，主要业务包括：
    - 太阳能发电系统设计与安装
    - 储能系统集成服务
    - 清洁能源项目开发
    - 能源管理软件开发
    
    我们希望找到能够影响采购决策的关键人员。
    """
    
    try:
        # 初始化分析器
        print(f"\n🤖 初始化员工AI分析器 (使用 {provider})...")
        analyzer = EmployeeAIAnalyzer(provider=provider)
        
        # 测试个人分析
        print("\n📊 测试个人分析功能...")
        
        def progress_callback(current, total, name):
            print(f"   分析进度: {current}/{total} - {name}")
        
        individual_results = analyzer.batch_analyze_employees(
            test_employees, 
            business_context, 
            callback=progress_callback
        )
        
        print(f"\n✅ 个人分析完成，分析了 {len(individual_results)} 位员工")
        
        # 显示个人分析结果
        print("\n📋 个人分析结果:")
        for result in individual_results:
            print(f"   👤 {result['employee_name']}")
            print(f"      职位: {result['title']}")
            print(f"      综合得分: {result['final_score']:.1f}")
            print(f"      优先级: {result['priority_level']}")
            print(f"      分析摘要: {result['analysis_summary'][:100]}...")
            print(f"      智能标签: {result['tags']}")
            print()
        
        # 测试团队分析
        print("👥 测试团队分析功能...")
        team_results = analyzer.analyze_team_structure(test_employees, business_context)
        
        print("✅ 团队分析完成")
        
        # 显示团队分析结果
        print("\n📋 团队分析结果:")
        team_insights = team_results.get('team_insights', {})
        
        if team_insights.get('key_decision_makers'):
            print("   🎯 关键决策者:")
            for decision_maker in team_insights['key_decision_makers']:
                print(f"      • {decision_maker}")
        
        if team_insights.get('collaboration_opportunities'):
            print("   🔗 协作关系:")
            for collaboration in team_insights['collaboration_opportunities']:
                print(f"      • {collaboration}")
        
        if team_insights.get('team_approach_strategy'):
            print(f"   📋 团队接触策略:")
            print(f"      {team_insights['team_approach_strategy'][:200]}...")
        
        print(f"\n🎉 员工AI分析测试成功完成！")
        print(f"✅ 个人分析: {len(individual_results)} 位员工")
        print(f"✅ 团队分析: 完整团队结构分析")
        print(f"✅ AI模型: {provider}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 员工AI分析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_employee_ai_analysis()
    
    if success:
        print("\n🎉 所有测试通过！员工AI分析功能已经准备就绪。")
        print("💡 现在可以通过Streamlit Web界面使用员工AI分析功能了：")
        print("   1. 运行: streamlit run streamlit_app.py")
        print("   2. 访问: http://localhost:8501")
        print("   3. 点击: '👥 员工AI分析'")
    else:
        print("\n❌ 测试失败，请检查配置和代码。")
        sys.exit(1)