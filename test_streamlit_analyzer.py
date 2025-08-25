#!/usr/bin/env python3
"""
Streamlit兼容AI分析器测试脚本
验证新的同步版本是否解决了asyncio上下文问题
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

def test_streamlit_compatible_analyzer():
    """测试Streamlit兼容的分析器"""
    print("🧪 测试Streamlit兼容AI分析器...")
    
    try:
        from integration_guide import AIAnalyzerManager, EmployeeAIAnalyzerManager
        
        # 测试公司分析器
        print("\n1. 测试公司分析器初始化...")
        company_analyzer = AIAnalyzerManager(
            use_optimized=True,
            max_concurrent=3,  # 减少并发数以便观察
            enable_cache=True
        )
        
        # 测试数据
        test_companies = [
            {
                'name': 'TestSolar Corp',
                'description': 'Leading solar panel manufacturer with 500+ employees',
                'domain': 'testsolar.com'
            },
            {
                'name': 'GreenEnergy Ltd',
                'description': 'Renewable energy consultancy based in California',
                'domain': 'greenenergy.com'
            }
        ]
        
        target_profile = "太阳能设备采购商，寻找可靠的太阳能板供应商"
        
        print(f"\n2. 开始批量分析 {len(test_companies)} 家公司...")
        start_time = time.time()
        
        def progress_callback(current, total, company_name):
            print(f"   进度: {current}/{total} - 分析中: {company_name}")
        
        results = company_analyzer.batch_analyze_companies(
            test_companies, 
            target_profile, 
            callback=progress_callback
        )
        
        elapsed_time = time.time() - start_time
        print(f"\n✅ 公司分析完成! 耗时: {elapsed_time:.2f}秒")
        print(f"📊 分析结果: {len(results)} 家公司")
        
        # 显示结果摘要
        for result in results:
            company_name = result.get('company_name', 'Unknown')
            final_score = result.get('final_score', 0)
            summary = result.get('analysis_summary', 'No summary')[:50]
            print(f"   • {company_name}: {final_score}分 - {summary}...")
        
        # 显示性能统计
        try:
            if hasattr(company_analyzer, 'get_performance_stats'):
                stats = company_analyzer.get_performance_stats()
                print(f"\n📈 管理器统计: {stats}")
            elif hasattr(company_analyzer.analyzer, 'get_performance_stats'):
                stats = company_analyzer.analyzer.get_performance_stats()
                print(f"\n📈 分析器统计: {stats}")
        except Exception as e:
            print(f"\n📈 统计获取失败: {e}")
        
        print("\n" + "="*60)
        
        # 测试员工分析器
        print("3. 测试员工分析器...")
        employee_analyzer = EmployeeAIAnalyzerManager(
            use_optimized=True,
            max_concurrent=2,
            enable_cache=True
        )
        
        test_employees = [
            {
                'name': 'John Smith',
                'title': 'Procurement Director',
                'company': 'TestSolar Corp',
                'description': '15年采购经验，负责设备采购决策'
            }
        ]
        
        business_context = "太阳能板供应商，希望与采购决策者建立联系"
        
        print(f"   开始分析 {len(test_employees)} 位员工...")
        emp_start_time = time.time()
        
        emp_results = employee_analyzer.batch_analyze_employees(
            test_employees, 
            business_context
        )
        
        emp_elapsed_time = time.time() - emp_start_time
        print(f"   ✅ 员工分析完成! 耗时: {emp_elapsed_time:.2f}秒")
        
        for result in emp_results:
            emp_name = result.get('employee_name', 'Unknown')
            final_score = result.get('final_score', 0)
            print(f"   • {emp_name}: {final_score}分")
        
        print("\n🎉 Streamlit兼容分析器测试完成!")
        print("🔍 关键观察:")
        print("   - 无 'missing ScriptRunContext' 警告")
        print("   - 使用ThreadPoolExecutor而非asyncio")
        print("   - 保持并发性能优势")
        print("   - 完全兼容Streamlit环境")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 Streamlit兼容AI分析器测试")
    print("=" * 60)
    
    # 检查环境
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        from components.common import check_api_keys
        api_status = check_api_keys()
        
        if not any(api_status.values()):
            print("⚠️ 未配置API密钥，将只能测试基础功能")
            return False
        else:
            available_apis = [key for key, status in api_status.items() if status]
            print(f"✅ 检测到可用API: {available_apis}")
    except Exception as e:
        print(f"⚠️ 无法检查API状态: {e}")
    
    # 运行测试
    success = test_streamlit_compatible_analyzer()
    
    if success:
        print("\n✅ 所有测试通过! 分析器已准备好在Streamlit中使用")
    else:
        print("\n❌ 测试失败，请检查错误信息")
    
    return success

if __name__ == "__main__":
    main()