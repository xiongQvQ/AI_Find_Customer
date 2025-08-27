#!/usr/bin/env python3
"""
测试关键词生成功能
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.llm_keyword_generator import LLMKeywordGenerator

def test_keyword_generation():
    """测试关键词生成功能"""
    
    print("🚀 测试关键词生成功能")
    
    generator = LLMKeywordGenerator()
    
    # 测试用例：新能源汽车 + 加拿大
    test_industry = "新能源汽车"
    test_country = "加拿大"
    test_search_type = "general"
    
    print(f"📋 测试参数:")
    print(f"   行业: {test_industry}")
    print(f"   国家: {test_country}")
    print(f"   搜索类型: {test_search_type}")
    print(f"   LLM Provider: {generator.llm_provider}")
    
    # 执行关键词生成
    try:
        result = generator.generate_search_keywords(
            industry=test_industry,
            target_country=test_country,
            search_type=test_search_type
        )
        
        print(f"\n✅ 关键词生成完成!")
        print(f"🔍 生成方式: {result.get('generated_by')}")
        print(f"🎯 主关键词:")
        for i, keyword in enumerate(result.get('primary_keywords', []), 1):
            print(f"     {i}. {keyword}")
        
        print(f"🔄 备选关键词:")
        for i, keyword in enumerate(result.get('alternative_keywords', []), 1):
            print(f"     {i}. {keyword}")
            
        print(f"📍 国家代码: {result.get('serper_params', {}).get('gl')}")
        print(f"💡 说明: {result.get('explanation')}")
        
        # 重点检查：是否包含"Canada"或"Canadian"
        all_keywords = result.get('primary_keywords', []) + result.get('alternative_keywords', [])
        canada_keywords = [kw for kw in all_keywords if 'canada' in kw.lower() or 'canadian' in kw.lower()]
        
        print(f"\n🇨🇦 包含'Canada/Canadian'的关键词数量: {len(canada_keywords)}")
        if canada_keywords:
            for kw in canada_keywords:
                print(f"     ✓ {kw}")
        
        return True
        
    except Exception as e:
        print(f"❌ 关键词生成失败: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_keyword_generation()
    if success:
        print(f"\n🎉 关键词生成功能工作正常!")
    else:
        print(f"\n💥 关键词生成功能有问题")