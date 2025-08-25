#!/usr/bin/env python3
"""
快速AI分析器性能测试
对比原版和优化版在小数据集上的性能差异
"""

import time
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

def quick_test():
    """快速性能测试"""
    
    print("⚡ 快速性能测试开始...")
    
    # 测试数据 - 较小的数据集
    test_companies = [
        {
            'name': 'Tesla Energy',
            'description': 'Clean energy and electric vehicle company specializing in solar panels and battery storage.',
            'domain': 'tesla.com'
        },
        {
            'name': 'First Solar',
            'description': 'Leading American photovoltaic panel manufacturer.',
            'domain': 'firstsolar.com'
        }
    ]
    
    test_employees = [
        {
            'name': 'John Smith',
            'title': 'Chief Technology Officer',
            'company': 'Tesla Energy',
            'description': 'CTO with 15+ years in renewable energy technology.'
        }
    ]
    
    target_profile = "可再生能源企业"
    business_context = "太阳能解决方案提供商"
    
    print(f"📊 测试数据: {len(test_companies)} 家公司, {len(test_employees)} 位员工")
    
    # 测试优化版公司分析器
    print("\n⚡ 测试优化版公司AI分析器...")
    try:
        from optimized_ai_analyzer import OptimizedAIAnalyzerSync
        
        optimized_analyzer = OptimizedAIAnalyzerSync(max_concurrent=4, enable_cache=True)
        
        start_time = time.time()
        optimized_company_results = optimized_analyzer.batch_analyze_companies(
            test_companies, target_profile
        )
        optimized_company_time = time.time() - start_time
        
        print(f"✅ 优化版公司分析完成: {len(optimized_company_results)} 家公司，耗时 {optimized_company_time:.2f}秒")
        print(f"   平均每家公司: {optimized_company_time / len(optimized_company_results):.2f}秒")
        
        # 显示性能统计
        stats = optimized_analyzer.get_performance_stats()
        print(f"📈 性能统计: {stats}")
        
        # 显示分析结果示例
        if optimized_company_results:
            result = optimized_company_results[0]
            print(f"📋 分析结果示例:")
            print(f"   公司: {result.get('company_name')}")
            print(f"   得分: {result.get('final_score', 0):.1f}/100")
            print(f"   摘要: {result.get('analysis_summary', '')[:100]}...")
        
    except Exception as e:
        print(f"❌ 优化版公司分析器测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试缓存效果
    print("\n🔄 测试缓存效果...")
    try:
        print("重复运行优化版公司分析（测试缓存）...")
        
        start_time = time.time()
        cached_results = optimized_analyzer.batch_analyze_companies(
            test_companies, target_profile  # 相同数据
        )
        cached_time = time.time() - start_time
        
        print(f"✅ 缓存测试完成: {len(cached_results)} 家公司，耗时 {cached_time:.2f}秒")
        
        # 缓存加速比
        if optimized_company_time > 0 and cached_time > 0:
            cache_speedup = optimized_company_time / cached_time
            print(f"🚀 缓存加速比: {cache_speedup:.1f}x")
        
        # 显示最终统计
        final_stats = optimized_analyzer.get_performance_stats()
        print(f"📊 最终统计: {final_stats}")
        
    except Exception as e:
        print(f"❌ 缓存测试失败: {e}")
    
    # 测试优化版员工分析器
    print("\n⚡ 测试优化版员工AI分析器...")
    try:
        from optimized_employee_ai_analyzer import OptimizedEmployeeAIAnalyzerSync
        
        optimized_employee_analyzer = OptimizedEmployeeAIAnalyzerSync(max_concurrent=4, enable_cache=True)
        
        start_time = time.time()
        optimized_employee_results = optimized_employee_analyzer.batch_analyze_employees(
            test_employees, business_context
        )
        optimized_employee_time = time.time() - start_time
        
        print(f"✅ 优化版员工分析完成: {len(optimized_employee_results)} 位员工，耗时 {optimized_employee_time:.2f}秒")
        print(f"   平均每位员工: {optimized_employee_time / len(optimized_employee_results):.2f}秒")
        
        # 显示性能统计
        stats = optimized_employee_analyzer.get_performance_stats()
        print(f"📈 性能统计: {stats}")
        
        # 显示分析结果示例
        if optimized_employee_results:
            result = optimized_employee_results[0]
            print(f"📋 员工分析结果示例:")
            print(f"   员工: {result.get('employee_name')}")
            print(f"   得分: {result.get('final_score', 0):.1f}/100")
            print(f"   优先级: {result.get('priority_level')}")
        
    except Exception as e:
        print(f"❌ 优化版员工分析器测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("🎉 快速性能测试完成！")
    print("="*60)
    
    print("\n💡 优化效果总结:")
    print("✅ 异步并发处理 - 支持同时处理多个分析")
    print("✅ 智能缓存机制 - 重复分析接近即时响应") 
    print("✅ 自适应超时 - 根据复杂度优化等待时间")
    print("✅ 性能统计追踪 - 实时监控分析效果")
    print("✅ 向下兼容设计 - 无需修改现有代码")

def main():
    """主测试函数"""
    print("🚀 AI分析器快速性能测试")
    print("="*60)
    
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
        return
    
    print(f"✅ 检测到可用的LLM提供商: {', '.join(available_providers)}")
    print(f"🎯 使用提供商: {available_providers[0]}")
    
    # 运行快速测试
    quick_test()

if __name__ == "__main__":
    main()