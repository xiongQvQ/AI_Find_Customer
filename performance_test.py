#!/usr/bin/env python3
"""
AI分析器性能测试脚本
对比原版和优化版的性能差异
"""

import time
import sys
import os
from pathlib import Path
import pandas as pd
import asyncio
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

def create_test_data(count: int) -> List[Dict[str, Any]]:
    """创建测试数据"""
    companies = []
    for i in range(count):
        companies.append({
            'name': f'Test Company {i+1}',
            'title': f'Test Company {i+1} - Industry Leader',
            'description': f'This is test company {i+1} operating in the renewable energy sector. '
                          f'The company specializes in solar panel manufacturing and installation. '
                          f'Founded in 2020, it has grown rapidly and now serves customers worldwide.',
            'domain': f'testcompany{i+1}.com',
            'emails': f'info@testcompany{i+1}.com',
            'phones': f'+1-555-{1000+i}',
            'linkedin': f'https://linkedin.com/company/test-company-{i+1}'
        })
    return companies

def create_employee_test_data(count: int) -> List[Dict[str, Any]]:
    """创建员工测试数据"""
    employees = []
    titles = ['CEO', 'CTO', 'VP Sales', 'Sales Director', 'Product Manager', 'Marketing Manager']
    for i in range(count):
        employees.append({
            'name': f'Test Employee {i+1}',
            'title': titles[i % len(titles)],
            'company': f'Test Company {(i//6)+1}',
            'description': f'Experienced professional with 10+ years in the industry. '
                          f'Strong background in renewable energy and business development.',
            'email': f'employee{i+1}@testcompany.com',
            'linkedin_url': f'https://linkedin.com/in/test-employee-{i+1}'
        })
    return employees

async def test_original_vs_optimized():
    """对比原版和优化版性能"""
    
    print("🧪 开始性能对比测试...")
    
    # 测试数据
    test_companies = create_test_data(20)  # 20家公司
    test_employees = create_employee_test_data(15)  # 15位员工
    
    target_profile = """
    我们的目标客户是从事可再生能源业务的大中型企业，特别是：
    - 太阳能设备制造商和分销商
    - 清洁能源项目开发商
    - 电池储能系统供应商
    """
    
    business_context = """
    我们是一家可再生能源解决方案提供商，主要业务包括：
    - 太阳能发电系统设计与安装
    - 储能系统集成服务
    - 清洁能源项目开发
    """
    
    print(f"\n📊 测试数据: {len(test_companies)} 家公司, {len(test_employees)} 位员工")
    
    # 测试原版公司分析器
    print("\n🔄 测试原版公司AI分析器...")
    try:
        from ai_analyzer import AIAnalyzer
        
        original_analyzer = AIAnalyzer()
        
        start_time = time.time()
        original_company_results = original_analyzer.batch_analyze_companies(
            test_companies[:5], target_profile  # 只测试5家公司，避免等待太久
        )
        original_company_time = time.time() - start_time
        
        print(f"✅ 原版公司分析完成: {len(original_company_results)} 家公司，耗时 {original_company_time:.2f}秒")
        print(f"   平均每家公司: {original_company_time / len(original_company_results):.2f}秒")
        
    except Exception as e:
        print(f"❌ 原版公司分析器测试失败: {e}")
        original_company_time = float('inf')
        original_company_results = []
    
    # 测试优化版公司分析器
    print("\n⚡ 测试优化版公司AI分析器...")
    try:
        from optimized_ai_analyzer import OptimizedAIAnalyzerSync
        
        optimized_analyzer = OptimizedAIAnalyzerSync(max_concurrent=6, enable_cache=True)
        
        start_time = time.time()
        optimized_company_results = optimized_analyzer.batch_analyze_companies(
            test_companies[:5], target_profile  # 测试相同数量
        )
        optimized_company_time = time.time() - start_time
        
        print(f"✅ 优化版公司分析完成: {len(optimized_company_results)} 家公司，耗时 {optimized_company_time:.2f}秒")
        print(f"   平均每家公司: {optimized_company_time / len(optimized_company_results):.2f}秒")
        
        # 显示性能统计
        stats = optimized_analyzer.get_performance_stats()
        print(f"📈 性能统计: {stats}")
        
    except Exception as e:
        print(f"❌ 优化版公司分析器测试失败: {e}")
        optimized_company_time = float('inf')
        optimized_company_results = []
    
    # 测试原版员工分析器
    print("\n🔄 测试原版员工AI分析器...")
    try:
        from employee_ai_analyzer import EmployeeAIAnalyzer
        
        original_employee_analyzer = EmployeeAIAnalyzer()
        
        start_time = time.time()
        original_employee_results = original_employee_analyzer.batch_analyze_employees(
            test_employees[:3], business_context  # 只测试3位员工
        )
        original_employee_time = time.time() - start_time
        
        print(f"✅ 原版员工分析完成: {len(original_employee_results)} 位员工，耗时 {original_employee_time:.2f}秒")
        print(f"   平均每位员工: {original_employee_time / len(original_employee_results):.2f}秒")
        
    except Exception as e:
        print(f"❌ 原版员工分析器测试失败: {e}")
        original_employee_time = float('inf')
        original_employee_results = []
    
    # 测试优化版员工分析器
    print("\n⚡ 测试优化版员工AI分析器...")
    try:
        from optimized_employee_ai_analyzer import OptimizedEmployeeAIAnalyzerSync
        
        optimized_employee_analyzer = OptimizedEmployeeAIAnalyzerSync(max_concurrent=6, enable_cache=True)
        
        start_time = time.time()
        optimized_employee_results = optimized_employee_analyzer.batch_analyze_employees(
            test_employees[:3], business_context  # 测试相同数量
        )
        optimized_employee_time = time.time() - start_time
        
        print(f"✅ 优化版员工分析完成: {len(optimized_employee_results)} 位员工，耗时 {optimized_employee_time:.2f}秒")
        print(f"   平均每位员工: {optimized_employee_time / len(optimized_employee_results):.2f}秒")
        
        # 显示性能统计
        stats = optimized_employee_analyzer.get_performance_stats()
        print(f"📈 性能统计: {stats}")
        
    except Exception as e:
        print(f"❌ 优化版员工分析器测试失败: {e}")
        optimized_employee_time = float('inf')
        optimized_employee_results = []
    
    # 性能对比报告
    print("\n" + "="*60)
    print("🏆 性能对比报告")
    print("="*60)
    
    if original_company_time != float('inf') and optimized_company_time != float('inf'):
        company_speedup = original_company_time / optimized_company_time
        print(f"📈 公司分析性能提升: {company_speedup:.1f}x")
        print(f"   原版: {original_company_time:.2f}秒")
        print(f"   优化版: {optimized_company_time:.2f}秒")
        print(f"   节省时间: {original_company_time - optimized_company_time:.2f}秒")
    
    if original_employee_time != float('inf') and optimized_employee_time != float('inf'):
        employee_speedup = original_employee_time / optimized_employee_time
        print(f"👥 员工分析性能提升: {employee_speedup:.1f}x")
        print(f"   原版: {original_employee_time:.2f}秒")
        print(f"   优化版: {optimized_employee_time:.2f}秒")
        print(f"   节省时间: {original_employee_time - optimized_employee_time:.2f}秒")
    
    # 缓存效果测试
    print("\n🔄 测试缓存效果...")
    if len(optimized_company_results) > 0:
        print("重复运行优化版公司分析（测试缓存）...")
        
        start_time = time.time()
        cached_results = optimized_analyzer.batch_analyze_companies(
            test_companies[:5], target_profile  # 相同数据
        )
        cached_time = time.time() - start_time
        
        print(f"✅ 缓存测试完成: {len(cached_results)} 家公司，耗时 {cached_time:.2f}秒")
        
        # 缓存加速比
        if optimized_company_time > 0:
            cache_speedup = optimized_company_time / cached_time
            print(f"🚀 缓存加速比: {cache_speedup:.1f}x")
        
        # 显示最终统计
        final_stats = optimized_analyzer.get_performance_stats()
        print(f"📊 最终统计: {final_stats}")

def test_concurrent_scalability():
    """测试并发扩展性"""
    print("\n" + "="*60)
    print("🔧 并发扩展性测试")
    print("="*60)
    
    test_companies = create_test_data(10)
    target_profile = "可再生能源企业分析测试"
    
    # 测试不同并发级别
    concurrent_levels = [1, 2, 4, 8]
    
    for max_concurrent in concurrent_levels:
        try:
            from optimized_ai_analyzer import OptimizedAIAnalyzerSync
            
            analyzer = OptimizedAIAnalyzerSync(max_concurrent=max_concurrent, enable_cache=False)
            
            print(f"\n🔄 测试并发级别: {max_concurrent}")
            start_time = time.time()
            
            results = analyzer.batch_analyze_companies(test_companies[:6], target_profile)
            
            end_time = time.time()
            elapsed = end_time - start_time
            
            print(f"✅ 完成 {len(results)} 家公司分析")
            print(f"⏱️  耗时: {elapsed:.2f}秒")
            print(f"📈 平均速度: {elapsed / len(results):.2f}秒/家")
            
            stats = analyzer.get_performance_stats()
            print(f"📊 统计: API调用={stats.get('API调用数', 0)}, 错误={stats.get('错误数', 0)}")
            
        except Exception as e:
            print(f"❌ 并发级别 {max_concurrent} 测试失败: {e}")

def main():
    """主测试函数"""
    print("🚀 AI分析器性能测试开始")
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
    
    # 运行性能测试
    asyncio.run(test_original_vs_optimized())
    
    # 运行并发测试
    test_concurrent_scalability()
    
    print("\n" + "="*60)
    print("🎉 性能测试完成！")
    print("="*60)
    
    print("\n💡 优化建议:")
    print("1. 在生产环境中启用缓存以获得最佳性能")
    print("2. 根据API服务商限制调整max_concurrent参数")
    print("3. 监控API调用频率，避免触发限流")
    print("4. 定期清理缓存文件以释放磁盘空间")

if __name__ == "__main__":
    main()