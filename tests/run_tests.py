"""
测试运行器脚本
提供便捷的测试执行和报告功能
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))


def run_command(cmd, description=""):
    """执行命令并返回结果"""
    print(f"\n{'='*60}")
    print(f"执行: {description or cmd}")
    print(f"{'='*60}")
    
    start_time = time.time()
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    execution_time = time.time() - start_time
    
    print(f"执行时间: {execution_time:.2f}s")
    
    if result.returncode == 0:
        print("✅ 成功")
        if result.stdout:
            print("\n输出:")
            print(result.stdout)
    else:
        print("❌ 失败")
        if result.stderr:
            print("\n错误:")
            print(result.stderr)
        if result.stdout:
            print("\n输出:")
            print(result.stdout)
    
    return result.returncode == 0, result.stdout, result.stderr


def main():
    parser = argparse.ArgumentParser(description="LangGraph智能搜索测试运行器")
    
    # 测试类型选项
    parser.add_argument("--unit", action="store_true", help="运行单元测试")
    parser.add_argument("--integration", action="store_true", help="运行集成测试")
    parser.add_argument("--e2e", action="store_true", help="运行端到端测试")
    parser.add_argument("--performance", action="store_true", help="运行性能测试")
    parser.add_argument("--all", action="store_true", help="运行所有测试")
    
    # 测试框架选项
    parser.add_argument("--framework", choices=["unittest", "pytest"], default="pytest",
                       help="选择测试框架 (默认: pytest)")
    
    # 输出选项
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--coverage", action="store_true", help="生成覆盖率报告")
    parser.add_argument("--html-report", action="store_true", help="生成HTML报告")
    parser.add_argument("--xml-report", action="store_true", help="生成XML报告")
    
    # 其他选项
    parser.add_argument("--parallel", action="store_true", help="并行执行测试")
    parser.add_argument("--fail-fast", action="store_true", help="首次失败时停止")
    parser.add_argument("--pattern", help="测试文件匹配模式")
    
    args = parser.parse_args()
    
    # 检查依赖
    if not check_dependencies():
        return False
    
    # 设置测试目录
    test_dir = Path(__file__).parent
    os.chdir(test_dir)
    
    success = True
    
    print("🚀 LangGraph智能搜索测试执行器")
    print(f"测试目录: {test_dir}")
    print(f"测试框架: {args.framework}")
    
    if args.framework == "pytest":
        success = run_pytest_tests(args)
    else:
        success = run_unittest_tests(args)
    
    # 总结
    print(f"\n{'='*60}")
    if success:
        print("🎉 所有测试执行完成!")
    else:
        print("💥 部分测试失败!")
    print(f"{'='*60}")
    
    return success


def check_dependencies():
    """检查测试依赖"""
    required_packages = [
        "pytest",
        "pytest-cov", 
        "pytest-html",
        "pytest-xdist",
        "psutil"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ 缺少测试依赖包:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n请运行以下命令安装:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True


def run_pytest_tests(args):
    """使用pytest运行测试"""
    cmd_parts = ["python", "-m", "pytest"]
    
    # 选择测试目录
    test_paths = []
    if args.unit:
        test_paths.append("unit/")
    if args.integration:
        test_paths.append("integration/")
    if args.e2e:
        test_paths.append("e2e/")
    if args.performance:
        test_paths.append("performance/")
    if args.all or not test_paths:
        test_paths = ["."]
    
    cmd_parts.extend(test_paths)
    
    # 详细输出
    if args.verbose:
        cmd_parts.append("-v")
    
    # 覆盖率
    if args.coverage:
        cmd_parts.extend([
            "--cov=langgraph_search",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov"
        ])
    
    # HTML报告
    if args.html_report:
        cmd_parts.extend(["--html=reports/report.html", "--self-contained-html"])
    
    # XML报告
    if args.xml_report:
        cmd_parts.append("--junitxml=reports/report.xml")
    
    # 并行执行
    if args.parallel:
        cmd_parts.extend(["-n", "auto"])
    
    # 快速失败
    if args.fail_fast:
        cmd_parts.append("-x")
    
    # 测试模式
    if args.performance:
        cmd_parts.append("--run-performance")
    
    # 文件模式
    if args.pattern:
        cmd_parts.extend(["-k", args.pattern])
    
    # 创建报告目录
    os.makedirs("reports", exist_ok=True)
    
    # 执行测试
    cmd = " ".join(cmd_parts)
    success, stdout, stderr = run_command(cmd, "执行pytest测试")
    
    # 生成测试报告摘要
    if success:
        generate_test_summary(stdout)
    
    return success


def run_unittest_tests(args):
    """使用unittest运行测试"""
    success = True
    
    test_modules = []
    if args.unit:
        test_modules.extend([
            "unit.test_intent_recognition",
            "unit.test_company_search",
            "unit.test_ai_evaluation"
        ])
    if args.integration:
        test_modules.extend([
            "integration.test_workflow_integration",
            # "integration.test_streamlit_integration"  # Removed - no longer using Streamlit
        ])
    if args.e2e:
        test_modules.append("e2e.test_end_to_end_scenarios")
    if args.performance:
        test_modules.append("performance.test_performance_benchmarks")
    
    if args.all or not test_modules:
        test_modules = ["discover"]
    
    for module in test_modules:
        if module == "discover":
            cmd = "python -m unittest discover -s . -p 'test_*.py'"
            description = "发现并运行所有单元测试"
        else:
            cmd = f"python -m unittest tests.{module}"
            description = f"运行 {module} 测试"
        
        if args.verbose:
            cmd += " -v"
        
        module_success, stdout, stderr = run_command(cmd, description)
        success = success and module_success
    
    return success


def generate_test_summary(pytest_output):
    """生成测试摘要"""
    lines = pytest_output.split('\n')
    
    # 提取关键信息
    test_summary = {}
    for line in lines:
        if "passed" in line and "failed" in line:
            # 解析测试结果行
            test_summary["result_line"] = line.strip()
        elif "coverage:" in line:
            test_summary["coverage"] = line.strip()
        elif "seconds" in line:
            test_summary["duration"] = line.strip()
    
    if test_summary:
        print(f"\n📊 测试摘要:")
        for key, value in test_summary.items():
            print(f"  {key}: {value}")


def run_specific_test_category():
    """运行特定类别的测试"""
    print("\n选择要运行的测试类别:")
    print("1. 单元测试 (Unit Tests)")
    print("2. 集成测试 (Integration Tests)")
    print("3. 端到端测试 (E2E Tests)")
    print("4. 性能测试 (Performance Tests)")
    print("5. 所有测试 (All Tests)")
    
    choice = input("\n请输入选择 (1-5): ").strip()
    
    cmd_map = {
        "1": ["--unit"],
        "2": ["--integration"],
        "3": ["--e2e"],
        "4": ["--performance"],
        "5": ["--all"]
    }
    
    if choice in cmd_map:
        # 模拟命令行参数
        sys.argv = ["run_tests.py"] + cmd_map[choice]
        main()
    else:
        print("无效选择!")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # 交互式模式
        run_specific_test_category()
    else:
        # 命令行模式
        success = main()
        sys.exit(0 if success else 1)