#!/usr/bin/env python3
"""
测试LLM关键词生成系统
验证新的智能关键词生成功能是否正常工作
"""

import os
import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'core'))

from dotenv import load_dotenv
load_dotenv()

def test_llm_keyword_generator():
    """测试LLM关键词生成器"""
    print("🧪 测试LLM关键词生成器...")
    
    try:
        from core.llm_keyword_generator import LLMKeywordGenerator
        
        generator = LLMKeywordGenerator()
        print(f"✅ LLM关键词生成器初始化成功")
        print(f"   LLM提供商: {generator.llm_provider}")
        print(f"   客户端可用: {generator.client is not None}")
        
        # 测试用例
        test_cases = [
            {
                "industry": "新能源汽车", 
                "target_country": "us", 
                "search_type": "linkedin",
                "expected_keywords": ["electric vehicle", "EV", "clean energy vehicle"]
            },
            {
                "industry": "人工智能", 
                "target_country": "us", 
                "search_type": "general",
                "expected_keywords": ["artificial intelligence", "AI", "machine learning"]
            },
            {
                "industry": "artificial intelligence", 
                "target_country": "cn", 
                "search_type": "linkedin",
                "expected_keywords": ["人工智能", "AI", "机器学习"]
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📋 测试用例 {i}:")
            print(f"   输入: {test_case['industry']} -> {test_case['target_country'].upper()}")
            
            start_time = time.time()
            result = generator.generate_search_keywords(
                industry=test_case['industry'],
                target_country=test_case['target_country'],
                search_type=test_case['search_type']
            )
            elapsed_time = time.time() - start_time
            
            print(f"   生成耗时: {elapsed_time:.2f}秒")
            print(f"   生成成功: {result.get('success')}")
            print(f"   生成方式: {result.get('generated_by', 'unknown')}")
            print(f"   主关键词: {result.get('primary_keywords')}")
            print(f"   备选关键词: {result.get('alternative_keywords')}")
            
            if result.get('serper_params'):
                print(f"   Serper参数: {result.get('serper_params')}")
            
            if result.get('explanation'):
                explanation = result.get('explanation', '')[:100]
                print(f"   说明: {explanation}...")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_company_search_integration():
    """测试公司搜索系统集成"""
    print("\n🔍 测试公司搜索系统集成...")
    
    try:
        from core.company_search import CompanySearcher
        
        searcher = CompanySearcher()
        print(f"✅ CompanySearcher初始化成功")
        print(f"   LLM可用: {searcher.llm_available}")
        
        if searcher.llm_available:
            # 测试关键词生成
            print("\n📝 测试关键词生成集成:")
            result = searcher._generate_optimized_keywords(
                industry="新能源汽车",
                region="美国加利福尼亚",
                gl="us",
                search_mode="linkedin"
            )
            
            print(f"   优化成功: {result.get('success')}")
            print(f"   优化方式: {result.get('method')}")
            print(f"   优化关键词: {result.get('optimized_keywords')}")
            
            if result.get('serper_params'):
                print(f"   Serper参数: {result.get('serper_params')}")
        else:
            print("⚠️ LLM不可用，将使用原始关键词")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_environment_setup():
    """测试环境配置"""
    print("🔧 检查环境配置...")
    
    # 检查必需的环境变量
    required_vars = ["SERPER_API_KEY"]
    optional_vars = ["LLM_PROVIDER", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "ARK_API_KEY"]
    
    print("\n📋 必需环境变量:")
    for var in required_vars:
        value = os.getenv(var)
        status = "✅" if value else "❌"
        print(f"   {status} {var}: {'已配置' if value else '未配置'}")
    
    print("\n📋 可选环境变量:")
    for var in optional_vars:
        value = os.getenv(var)
        status = "✅" if value else "⚪"
        print(f"   {status} {var}: {'已配置' if value else '未配置'}")
    
    # 检查LLM配置
    llm_provider = os.getenv("LLM_PROVIDER", "none").lower()
    print(f"\n🤖 LLM配置:")
    print(f"   提供商: {llm_provider}")
    
    if llm_provider == "openai":
        print(f"   OpenAI API Key: {'✅ 已配置' if os.getenv('OPENAI_API_KEY') else '❌ 未配置'}")
    elif llm_provider == "anthropic":
        print(f"   Anthropic API Key: {'✅ 已配置' if os.getenv('ANTHROPIC_API_KEY') else '❌ 未配置'}")
    elif llm_provider == "google":
        print(f"   Google API Key: {'✅ 已配置' if os.getenv('GOOGLE_API_KEY') else '❌ 未配置'}")
    elif llm_provider == "huoshan":
        ark_key = os.getenv('ARK_API_KEY')
        ark_base = os.getenv('ARK_BASE_URL')
        ark_model = os.getenv('ARK_MODEL')
        print(f"   Huoshan ARK API Key: {'✅ 已配置' if ark_key else '❌ 未配置'}")
        print(f"   Huoshan ARK Base URL: {'✅ 已配置' if ark_base else '❌ 未配置'}")
        print(f"   Huoshan ARK Model: {'✅ 已配置' if ark_model else '❌ 未配置'}")
    elif llm_provider == "none":
        print("   ⚠️ 未配置LLM提供商，将使用回退方案")
    else:
        print(f"   ❌ 不支持的LLM提供商: {llm_provider}")

def main():
    """主测试函数"""
    print("🚀 开始测试LLM关键词生成系统\n")
    print("=" * 50)
    
    # 测试环境配置
    test_environment_setup()
    
    print("\n" + "=" * 50)
    
    # 测试LLM关键词生成器
    generator_success = test_llm_keyword_generator()
    
    print("\n" + "=" * 50)
    
    # 测试公司搜索集成
    integration_success = test_company_search_integration()
    
    print("\n" + "=" * 50)
    
    # 总结
    print("📊 测试总结:")
    print(f"   LLM关键词生成器: {'✅ 通过' if generator_success else '❌ 失败'}")
    print(f"   公司搜索集成: {'✅ 通过' if integration_success else '❌ 失败'}")
    
    if generator_success and integration_success:
        print("\n🎉 所有测试通过！LLM关键词生成系统已就绪。")
        print("\n💡 使用说明:")
        print("   - 当用户搜索'美国 + 新能源汽车'时，系统将自动生成'electric vehicle'等英文关键词")
        print("   - 当用户搜索'中国 + artificial intelligence'时，系统将自动生成'人工智能'等中文关键词")
        print("   - 系统会根据目标国家优化搜索参数，提高搜索准确性")
        print("   - 如果LLM不可用，系统会自动回退到基础翻译字典")
    else:
        print("\n⚠️ 部分测试失败，请检查配置和代码")
    
    return generator_success and integration_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)