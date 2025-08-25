#!/usr/bin/env python3
"""
测试AI分析功能
快速验证AI分析器是否正常工作
"""

import pandas as pd
from ai_analyzer import AIAnalyzer
import os
from pathlib import Path

def test_ai_analysis():
    """测试AI分析功能"""
    
    print("🤖 测试AI分析功能...")
    print("=" * 50)
    
    # 检查数据文件
    company_dir = Path("output/company")
    if not company_dir.exists() or not list(company_dir.glob("*.csv")):
        print("❌ 未找到公司数据文件")
        print("请先运行搜索功能生成数据")
        return
    
    # 获取最新数据文件
    csv_files = list(company_dir.glob("*.csv"))
    latest_file = max(csv_files, key=os.path.getctime)
    
    print(f"📁 使用数据文件: {latest_file}")
    
    # 加载数据
    try:
        df = pd.read_csv(latest_file)
        print(f"📈 加载了 {len(df)} 家公司数据")
    except Exception as e:
        print(f"❌ 读取数据失败: {e}")
        return
    
    # 测试前3家公司
    test_companies = df.head(3).to_dict('records')
    
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
    try:
        analyzer = AIAnalyzer()
        print(f"✅ AI分析器初始化成功 (使用: {analyzer.provider})")
    except Exception as e:
        print(f"❌ AI分析器初始化失败: {e}")
        return
    
    # 逐个分析测试
    print(f"\n🔍 开始分析前3家公司...")
    print("-" * 50)
    
    results = []
    for i, company in enumerate(test_companies, 1):
        print(f"\n{i}. 分析: {company.get('name', 'Unknown')[:40]}")
        
        try:
            result = analyzer.analyze_company(company, target_profile)
            results.append(result)
            
            print(f"   ✅ 综合得分: {result['final_score']:.1f}/100")
            print(f"   📝 摘要: {result['analysis_summary'][:80]}...")
            print(f"   🏷️  标签: {', '.join(result['tags'][:3])}")
            print(f"   🧠 AI模型: {result['llm_provider']}")
            print(f"   ⏱️  分析时间: {result['analysis_time']}")
            
        except Exception as e:
            print(f"   ❌ 分析失败: {e}")
            continue
    
    # 统计结果
    if results:
        avg_score = sum(r['final_score'] for r in results) / len(results)
        max_score = max(r['final_score'] for r in results)
        
        print(f"\n📊 测试结果统计:")
        print(f"   分析成功: {len(results)}/{len(test_companies)} 家公司")
        print(f"   平均得分: {avg_score:.1f}")
        print(f"   最高得分: {max_score:.1f}")
        
        # 找到最佳客户
        best_client = max(results, key=lambda x: x['final_score'])
        print(f"\n🏆 最佳客户:")
        print(f"   公司: {best_client['company_name']}")
        print(f"   得分: {best_client['final_score']:.1f}/100")
        print(f"   理由: {best_client['analysis_summary']}")
        
        print(f"\n🎉 AI分析功能测试完成！")
    else:
        print(f"\n❌ 所有分析都失败了，请检查API配置")

if __name__ == "__main__":
    test_ai_analysis()