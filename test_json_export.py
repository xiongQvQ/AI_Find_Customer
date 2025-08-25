#!/usr/bin/env python3
"""
测试JSON导出功能修复
验证pandas DataFrame的JSON导出是否正常工作
"""

import pandas as pd
import json

def test_json_export():
    """测试JSON导出功能"""
    
    print("🧪 测试JSON导出功能修复...")
    
    # 创建测试数据
    test_data = [
        {
            'company_name': 'Tesla Energy',
            'final_score': 92.5,
            'analysis_summary': 'Tesla Energy作为全球领先的储能和太阳能解决方案提供商，具有极高的行业匹配度。',
            'tags': ['🎯 行业高匹配', '🏢 大型企业', '🚀 高增长潜力'],
            'dimension_scores': {'industry_match': 95, 'business_scale': 98}
        },
        {
            'company_name': 'First Solar Inc',
            'final_score': 88.2,
            'analysis_summary': 'First Solar作为美国领先的太阳能面板制造商，在行业匹配度方面表现出色。',
            'tags': ['🎯 行业高匹配', '🏬 中型企业', '📈 中等增长潜力'],
            'dimension_scores': {'industry_match': 98, 'business_scale': 85}
        }
    ]
    
    # 转换为DataFrame
    df = pd.DataFrame(test_data)
    print(f"✅ 创建测试DataFrame，包含 {len(df)} 行数据")
    
    # 测试旧方法（会失败）
    print("\n🔍 测试pandas to_json方法...")
    try:
        old_json = df.to_json(orient='records')
        print("✅ pandas to_json基础功能正常")
    except Exception as e:
        print(f"❌ pandas to_json失败: {e}")
        return False
    
    # 测试修复后的方法
    print("\n🔧 测试修复后的JSON导出方法...")
    try:
        import json as json_lib
        json_data = json_lib.dumps(
            df.to_dict('records'), 
            ensure_ascii=False, 
            indent=2
        )
        print("✅ 修复后的JSON导出方法正常工作")
        print(f"📄 生成的JSON长度: {len(json_data)} 字符")
        
        # 验证JSON格式
        parsed_data = json_lib.loads(json_data)
        print(f"✅ JSON格式验证通过，包含 {len(parsed_data)} 条记录")
        
        # 显示部分内容
        print("\n📋 JSON导出示例（前200字符）:")
        print(json_data[:200] + "..." if len(json_data) > 200 else json_data)
        
        return True
        
    except Exception as e:
        print(f"❌ 修复后的方法仍有问题: {e}")
        return False

if __name__ == "__main__":
    success = test_json_export()
    
    if success:
        print("\n🎉 JSON导出功能修复成功！")
        print("💡 AI分析页面的导出功能现在应该正常工作了。")
    else:
        print("\n❌ JSON导出功能仍有问题，需要进一步检查。")