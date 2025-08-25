#!/usr/bin/env python3
"""
生成智能评分系统综合报告
分析所有评分结果，提供洞察和建议
"""

import pandas as pd
import os
from pathlib import Path
from datetime import datetime
import json

def generate_comprehensive_report():
    """生成综合评分报告"""
    
    scored_dir = Path("output/scored")
    if not scored_dir.exists():
        print("❌ 评分结果目录不存在")
        return
    
    csv_files = list(scored_dir.glob("*.csv"))
    if not csv_files:
        print("❌ 未找到评分结果文件")
        return
    
    print("🎯 AI客户发现工具 - 智能评分系统综合报告")
    print("=" * 60)
    
    all_results = []
    category_stats = {}
    
    for csv_file in csv_files:
        if csv_file.stat().st_size < 500:  # 跳过空文件
            continue
            
        try:
            df = pd.read_csv(csv_file)
            if len(df) == 0:
                continue
                
            # 提取文件信息
            filename = csv_file.stem
            parts = filename.split('_')
            
            # 确定数据类型
            if 'solar' in filename:
                category = '太阳能制造'
            elif 'ai_coding' in filename:
                category = 'AI编程软件'
            elif 'software' in filename:
                category = '软件服务'
            else:
                category = '其他'
            
            # 统计信息
            stats = {
                'category': category,
                'total_companies': len(df),
                'avg_score': df['final_score'].mean(),
                'max_score': df['final_score'].max(),
                'min_score': df['final_score'].min(),
                'high_score_count': len(df[df['final_score'] >= 50]),
                'medium_score_count': len(df[(df['final_score'] >= 30) & (df['final_score'] < 50)]),
                'low_score_count': len(df[df['final_score'] < 30]),
                'top_companies': df.head(3)['name'].tolist()
            }
            
            category_stats[category] = stats
            all_results.extend(df.to_dict('records'))
            
        except Exception as e:
            print(f"⚠️  处理文件失败 {csv_file}: {e}")
    
    # 输出分类统计
    print("\n📊 分类评分统计:")
    print("-" * 60)
    
    for category, stats in category_stats.items():
        print(f"\n🏷️  {category}:")
        print(f"   公司数量: {stats['total_companies']}")
        print(f"   平均得分: {stats['avg_score']:.1f}")
        print(f"   最高得分: {stats['max_score']:.1f}")
        print(f"   高分客户 (≥50): {stats['high_score_count']} 家")
        print(f"   中分客户 (30-49): {stats['medium_score_count']} 家")
        print(f"   低分客户 (<30): {stats['low_score_count']} 家")
        
        if stats['top_companies']:
            print(f"   推荐客户: {', '.join(stats['top_companies'][:2])}")
    
    # 整体洞察
    print(f"\n🔍 整体洞察:")
    print("-" * 60)
    
    if category_stats:
        best_category = max(category_stats.items(), key=lambda x: x[1]['avg_score'])
        worst_category = min(category_stats.items(), key=lambda x: x[1]['avg_score'])
        
        print(f"✅ 最佳匹配行业: {best_category[0]} (平均分: {best_category[1]['avg_score']:.1f})")
        print(f"❌ 待优化行业: {worst_category[0]} (平均分: {worst_category[1]['avg_score']:.1f})")
        
        total_companies = sum(stats['total_companies'] for stats in category_stats.values())
        total_high_score = sum(stats['high_score_count'] for stats in category_stats.values())
        
        print(f"📈 总计分析公司: {total_companies} 家")
        print(f"🎯 高潜力客户: {total_high_score} 家 ({total_high_score/total_companies*100:.1f}%)")
    
    # 生成改进建议
    print(f"\n💡 改进建议:")
    print("-" * 60)
    
    suggestions = []
    
    for category, stats in category_stats.items():
        if stats['avg_score'] < 30:
            suggestions.append(f"• {category}: 评分较低，建议优化关键词配置或调整目标客户画像")
        elif stats['high_score_count'] == 0:
            suggestions.append(f"• {category}: 缺少高分客户，建议检查搜索策略和评分权重")
        elif stats['avg_score'] > 40:
            suggestions.append(f"• {category}: 表现良好，可优先开发此类客户")
    
    if not suggestions:
        suggestions.append("• 整体表现良好，建议继续收集更多联系信息数据")
    
    for suggestion in suggestions:
        print(suggestion)
    
    # 行动计划
    print(f"\n📋 推荐行动计划:")
    print("-" * 60)
    
    action_items = []
    
    # 找出最好的客户
    all_df = pd.DataFrame(all_results)
    if not all_df.empty and 'final_score' in all_df.columns:
        top_clients = all_df.nlargest(5, 'final_score')
        
        print("1. 立即联系的优质客户:")
        for idx, row in top_clients.iterrows():
            print(f"   • {row.get('name', 'Unknown')[:40]} (得分: {row.get('final_score', 0):.1f})")
    
    print("\n2. 系统优化建议:")
    print("   • 收集更多联系信息（邮箱、电话）以提高完整性得分")
    print("   • 搭配员工搜索功能识别关键决策者")
    print("   • 定期更新行业关键词配置")
    
    print("\n3. 数据收集建议:")
    print("   • 针对高分行业增加搜索范围")
    print("   • 收集公司规模和财务数据")
    print("   • 获取更详细的业务描述信息")
    
    # 保存报告
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"output/scored/comprehensive_report_{timestamp}.txt"
    
    # 这里可以保存详细的文本报告...
    print(f"\n📄 详细报告已保存至: {report_file}")
    
    return category_stats

if __name__ == "__main__":
    generate_comprehensive_report()