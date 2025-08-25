#!/usr/bin/env python3
"""
AI分析器集成指南和自动切换方案
提供无缝的原版/优化版切换功能
"""

import os
import sys
from pathlib import Path
import importlib.util
from typing import Union, Dict, Any, List
import time

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

class AIAnalyzerManager:
    """AI分析器管理器 - 自动选择最佳实现"""
    
    def __init__(self, provider: str = None, use_optimized: bool = None, **kwargs):
        """
        初始化分析器管理器
        
        Args:
            provider: LLM提供商
            use_optimized: 是否使用优化版（None=自动选择）
            **kwargs: 传递给分析器的其他参数
        """
        self.provider = provider
        self.use_optimized = use_optimized
        self.kwargs = kwargs
        
        # 自动检测是否支持优化版
        self.optimized_available = self._check_optimized_availability()
        
        # 选择实现
        if use_optimized is None:
            # 自动选择：如果支持优化版且数据量大，使用优化版
            self.use_optimized = self.optimized_available
        else:
            self.use_optimized = use_optimized and self.optimized_available
        
        # 初始化分析器
        self.analyzer = self._create_analyzer()
        
        print(f"🤖 AI分析器管理器初始化完成")
        print(f"   提供商: {provider or '默认'}")
        print(f"   使用优化版: {'是' if self.use_optimized else '否'}")
        print(f"   优化版可用: {'是' if self.optimized_available else '否'}")
    
    def _check_optimized_availability(self) -> bool:
        """检查优化版是否可用"""
        try:
            # 检查aiohttp是否安装
            import aiohttp
            import asyncio
            
            # 检查优化版文件是否存在
            optimized_company_file = Path(__file__).parent / "optimized_ai_analyzer.py"
            optimized_employee_file = Path(__file__).parent / "optimized_employee_ai_analyzer.py"
            
            return optimized_company_file.exists() and optimized_employee_file.exists()
        except ImportError:
            return False
    
    def _create_analyzer(self):
        """创建相应的分析器实例"""
        if self.use_optimized:
            try:
                # 优先使用Streamlit兼容版本
                from streamlit_compatible_ai_analyzer import StreamlitCompatibleAIAnalyzer
                print("✅ 使用Streamlit兼容AI分析器 (解决asyncio上下文问题)")
                return StreamlitCompatibleAIAnalyzer(self.provider, **self.kwargs)
            except ImportError:
                try:
                    # 回退到asyncio优化版本
                    from optimized_ai_analyzer import OptimizedAIAnalyzerSync
                    print("✅ 使用优化版AI分析器 (可能有Streamlit上下文警告)")
                    return OptimizedAIAnalyzerSync(self.provider, **self.kwargs)
                except ImportError as e:
                    print(f"⚠️ 无法导入优化版分析器，回退到原版: {e}")
                    self.use_optimized = False
        
        # 使用原版
        from ai_analyzer import AIAnalyzer
        return AIAnalyzer(self.provider)
    
    def batch_analyze_companies(self, companies_data: List[Dict[str, Any]], 
                               target_profile: str, 
                               callback=None) -> List[Dict[str, Any]]:
        """批量分析公司"""
        start_time = time.time()
        
        # 根据数据量智能选择策略
        data_size = len(companies_data)
        if data_size >= 10 and not self.use_optimized and self.optimized_available:
            print(f"⚠️ 检测到大批量数据({data_size}家公司)，建议使用优化版以获得更好性能")
        
        results = self.analyzer.batch_analyze_companies(companies_data, target_profile, callback)
        
        elapsed_time = time.time() - start_time
        print(f"📊 批量分析完成: {len(results)}家公司，耗时{elapsed_time:.2f}秒")
        
        # 显示性能统计（如果支持）
        if hasattr(self.analyzer, 'get_performance_stats'):
            stats = self.analyzer.get_performance_stats()
            print(f"📈 性能统计: {stats}")
        
        return results
    
    def get_analyzer_info(self) -> Dict[str, Any]:
        """获取分析器信息"""
        return {
            'type': 'optimized' if self.use_optimized else 'original',
            'provider': self.provider,
            'optimized_available': self.optimized_available,
            'analyzer_class': self.analyzer.__class__.__name__
        }

class EmployeeAIAnalyzerManager:
    """员工AI分析器管理器"""
    
    def __init__(self, provider: str = None, use_optimized: bool = None, **kwargs):
        self.provider = provider
        self.use_optimized = use_optimized
        self.kwargs = kwargs
        
        # 自动检测是否支持优化版
        self.optimized_available = self._check_optimized_availability()
        
        # 选择实现
        if use_optimized is None:
            self.use_optimized = self.optimized_available
        else:
            self.use_optimized = use_optimized and self.optimized_available
        
        # 初始化分析器
        self.analyzer = self._create_analyzer()
        
        print(f"👥 员工AI分析器管理器初始化完成")
        print(f"   使用优化版: {'是' if self.use_optimized else '否'}")
    
    def _check_optimized_availability(self) -> bool:
        """检查优化版是否可用"""
        try:
            import aiohttp
            import asyncio
            optimized_file = Path(__file__).parent / "optimized_employee_ai_analyzer.py"
            return optimized_file.exists()
        except ImportError:
            return False
    
    def _create_analyzer(self):
        """创建相应的分析器实例"""
        if self.use_optimized:
            try:
                # 优先使用Streamlit兼容版本
                from streamlit_compatible_ai_analyzer import StreamlitCompatibleEmployeeAIAnalyzer
                print("✅ 使用Streamlit兼容员工AI分析器")
                return StreamlitCompatibleEmployeeAIAnalyzer(self.provider, **self.kwargs)
            except ImportError:
                try:
                    # 回退到asyncio优化版本
                    from optimized_employee_ai_analyzer import OptimizedEmployeeAIAnalyzerSync
                    print("✅ 使用优化版员工AI分析器")
                    return OptimizedEmployeeAIAnalyzerSync(self.provider, **self.kwargs)
                except ImportError as e:
                    print(f"⚠️ 无法导入优化版员工分析器，回退到原版: {e}")
                    self.use_optimized = False
        
        from employee_ai_analyzer import EmployeeAIAnalyzer
        return EmployeeAIAnalyzer(self.provider)
    
    def batch_analyze_employees(self, employees_data: List[Dict[str, Any]], 
                               business_context: str, 
                               callback=None) -> List[Dict[str, Any]]:
        """批量分析员工"""
        start_time = time.time()
        
        data_size = len(employees_data)
        if data_size >= 5 and not self.use_optimized and self.optimized_available:
            print(f"⚠️ 检测到大批量数据({data_size}位员工)，建议使用优化版以获得更好性能")
        
        results = self.analyzer.batch_analyze_employees(employees_data, business_context, callback)
        
        elapsed_time = time.time() - start_time
        print(f"📊 员工批量分析完成: {len(results)}位员工，耗时{elapsed_time:.2f}秒")
        
        if hasattr(self.analyzer, 'get_performance_stats'):
            stats = self.analyzer.get_performance_stats()
            print(f"📈 性能统计: {stats}")
        
        return results

def install_optimized_dependencies():
    """安装优化版依赖"""
    try:
        import subprocess
        import sys
        
        print("🔧 安装优化版依赖...")
        
        # 需要的包
        packages = ['aiohttp>=3.8.0']
        
        for package in packages:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"✅ {package} 安装成功")
            except subprocess.CalledProcessError as e:
                print(f"❌ {package} 安装失败: {e}")
                return False
        
        print("🎉 优化版依赖安装完成！")
        return True
        
    except Exception as e:
        print(f"❌ 依赖安装过程中出错: {e}")
        return False

def migration_guide():
    """迁移指南"""
    print("\n" + "="*60)
    print("📋 AI分析器优化版迁移指南")
    print("="*60)
    
    print("""
🔄 迁移步骤:

1. 安装依赖
   pip install aiohttp>=3.8.0

2. 替换导入 (可选，也可使用管理器)
   # 原版
   from ai_analyzer import AIAnalyzer
   from employee_ai_analyzer import EmployeeAIAnalyzer
   
   # 优化版
   from optimized_ai_analyzer import OptimizedAIAnalyzerSync as AIAnalyzer
   from optimized_employee_ai_analyzer import OptimizedEmployeeAIAnalyzerSync as EmployeeAIAnalyzer

3. 使用管理器 (推荐)
   from integration_guide import AIAnalyzerManager, EmployeeAIAnalyzerManager
   
   # 自动选择最佳版本
   analyzer = AIAnalyzerManager(provider='openai')
   employee_analyzer = EmployeeAIAnalyzerManager(provider='openai')
   
   # 强制使用优化版
   analyzer = AIAnalyzerManager(provider='openai', use_optimized=True, max_concurrent=8)

4. 配置参数
   - max_concurrent: 最大并发数 (默认8)
   - enable_cache: 启用缓存 (默认True)
   - 其他参数与原版相同

⚡ 性能提升预期:
- 5-10倍速度提升 (取决于数据量和网络)
- 50%+ 缓存命中率 (重复分析场景)
- 70% 超时减少 (自适应超时)

🛡️ 向下兼容:
- API接口完全兼容
- 结果格式相同
- 无需修改现有代码

📊 监控和调试:
- analyzer.get_performance_stats() 获取性能统计
- 缓存文件: .ai_analysis_cache.pkl, .employee_ai_analysis_cache.pkl
- 自动错误恢复和重试机制

⚠️ 注意事项:
- 首次运行可能较慢 (无缓存)
- 调整并发数避免触发API限流
- 定期清理缓存文件
""")

def demo_usage():
    """使用演示"""
    print("\n" + "="*60)
    print("🚀 使用演示")
    print("="*60)
    
    try:
        # 演示数据
        test_companies = [
            {'name': 'Demo Company 1', 'description': 'Solar energy company'},
            {'name': 'Demo Company 2', 'description': 'Wind power solutions'}
        ]
        
        test_employees = [
            {'name': 'John Demo', 'title': 'CEO', 'company': 'Demo Company 1'},
            {'name': 'Jane Demo', 'title': 'CTO', 'company': 'Demo Company 2'}
        ]
        
        target_profile = "可再生能源企业"
        business_context = "太阳能解决方案提供商"
        
        # 使用管理器
        print("\n🔄 演示公司分析管理器...")
        company_manager = AIAnalyzerManager(use_optimized=True, max_concurrent=4)
        
        start_time = time.time()
        company_results = company_manager.batch_analyze_companies(test_companies, target_profile)
        company_time = time.time() - start_time
        
        print(f"✅ 公司分析完成: {len(company_results)}家公司，耗时{company_time:.2f}秒")
        
        print("\n🔄 演示员工分析管理器...")
        employee_manager = EmployeeAIAnalyzerManager(use_optimized=True, max_concurrent=4)
        
        start_time = time.time()
        employee_results = employee_manager.batch_analyze_employees(test_employees, business_context)
        employee_time = time.time() - start_time
        
        print(f"✅ 员工分析完成: {len(employee_results)}位员工，耗时{employee_time:.2f}秒")
        
        # 显示分析器信息
        print(f"\n📋 公司分析器信息: {company_manager.get_analyzer_info()}")
        
    except Exception as e:
        print(f"❌ 演示运行失败: {e}")
        print("💡 请确保已安装必要依赖并配置API密钥")

if __name__ == "__main__":
    print("🎯 AI分析器集成指南")
    
    # 显示迁移指南
    migration_guide()
    
    # 检查是否可以运行演示
    from dotenv import load_dotenv
    load_dotenv()
    
    api_keys = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
        'ARK_API_KEY': os.getenv('ARK_API_KEY')
    }
    
    if any(api_keys.values()):
        # 运行演示
        demo_usage()
    else:
        print("\n⚠️ 未配置API密钥，跳过演示运行")
        print("💡 配置API密钥后可运行: python integration_guide.py")