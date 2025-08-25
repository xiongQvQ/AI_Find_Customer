#!/usr/bin/env python3
"""
部署脚本
自动化部署AI客户发现系统到生产环境
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from config.logging_config import LangGraphLogger
from langgraph_search.utils.system_reporter import SystemReporter
from langgraph_search.utils.llm_connection_helper import LLMConnectionDiagnostics

class DeploymentManager:
    """部署管理器"""
    
    def __init__(self, environment: str = "production"):
        """
        初始化部署管理器
        
        Args:
            environment: 部署环境 (development, staging, production)
        """
        self.environment = environment
        self.project_root = Path(__file__).parent.parent
        self.deployment_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 初始化日志
        self.logger = LangGraphLogger()
        self.log = self.logger.setup_logger(
            "deployment", 
            f"deployment_{self.deployment_timestamp}.log"
        )
        
        # 系统报告器
        self.reporter = SystemReporter()
        
    def run_deployment(self) -> Dict[str, Any]:
        """运行完整部署流程"""
        try:
            self.log.info(f"开始部署到 {self.environment} 环境")
            
            deployment_result = {
                "environment": self.environment,
                "timestamp": self.deployment_timestamp,
                "steps": [],
                "success": False,
                "errors": []
            }
            
            # Step 1: 部署前检查
            self.log.info("Step 1: 执行部署前检查")
            pre_check_result = self._pre_deployment_checks()
            deployment_result["steps"].append({
                "name": "pre_deployment_checks",
                "success": pre_check_result["success"],
                "details": pre_check_result
            })
            
            if not pre_check_result["success"]:
                self.log.error("部署前检查失败，停止部署")
                deployment_result["errors"].extend(pre_check_result.get("errors", []))
                return deployment_result
            
            # Step 2: 环境准备
            self.log.info("Step 2: 准备部署环境")
            env_result = self._prepare_environment()
            deployment_result["steps"].append({
                "name": "prepare_environment", 
                "success": env_result["success"],
                "details": env_result
            })
            
            if not env_result["success"]:
                self.log.error("环境准备失败")
                deployment_result["errors"].extend(env_result.get("errors", []))
                return deployment_result
            
            # Step 3: 依赖安装
            self.log.info("Step 3: 安装依赖包")
            deps_result = self._install_dependencies()
            deployment_result["steps"].append({
                "name": "install_dependencies",
                "success": deps_result["success"], 
                "details": deps_result
            })
            
            if not deps_result["success"]:
                self.log.error("依赖安装失败")
                deployment_result["errors"].extend(deps_result.get("errors", []))
                return deployment_result
            
            # Step 4: 配置文件设置
            self.log.info("Step 4: 设置配置文件")
            config_result = self._setup_configuration()
            deployment_result["steps"].append({
                "name": "setup_configuration",
                "success": config_result["success"],
                "details": config_result
            })
            
            if not config_result["success"]:
                self.log.error("配置设置失败")
                deployment_result["errors"].extend(config_result.get("errors", []))
                return deployment_result
            
            # Step 5: 系统集成测试
            self.log.info("Step 5: 执行系统集成测试")
            test_result = self._run_integration_tests()
            deployment_result["steps"].append({
                "name": "integration_tests",
                "success": test_result["success"],
                "details": test_result
            })
            
            if not test_result["success"]:
                self.log.error("集成测试失败")
                deployment_result["errors"].extend(test_result.get("errors", []))
                return deployment_result
            
            # Step 6: 服务启动
            self.log.info("Step 6: 启动系统服务")
            service_result = self._start_services()
            deployment_result["steps"].append({
                "name": "start_services",
                "success": service_result["success"],
                "details": service_result
            })
            
            if not service_result["success"]:
                self.log.error("服务启动失败")
                deployment_result["errors"].extend(service_result.get("errors", []))
                return deployment_result
            
            # Step 7: 部署后验证
            self.log.info("Step 7: 部署后验证")
            post_check_result = self._post_deployment_verification()
            deployment_result["steps"].append({
                "name": "post_deployment_verification",
                "success": post_check_result["success"],
                "details": post_check_result
            })
            
            deployment_result["success"] = post_check_result["success"]
            
            if deployment_result["success"]:
                self.log.info("✅ 部署成功完成")
            else:
                self.log.error("❌ 部署验证失败")
                deployment_result["errors"].extend(post_check_result.get("errors", []))
            
            return deployment_result
            
        except Exception as e:
            self.log.error(f"部署过程中发生异常: {e}")
            return {
                "environment": self.environment,
                "timestamp": self.deployment_timestamp,
                "success": False,
                "error": str(e),
                "steps": deployment_result.get("steps", [])
            }
    
    def _pre_deployment_checks(self) -> Dict[str, Any]:
        """部署前检查"""
        try:
            result = {
                "success": True,
                "errors": [],
                "checks": {}
            }
            
            # 检查Python版本
            python_version = sys.version_info
            if python_version.major != 3 or python_version.minor < 8:
                result["errors"].append("需要Python 3.8或更高版本")
                result["success"] = False
            result["checks"]["python_version"] = f"{python_version.major}.{python_version.minor}"
            
            # 检查必要文件
            required_files = [
                "requirements.txt",
                ".env.example", 
                "langgraph_search/workflows/base_graph.py",
                "config/logging_config.py"
            ]
            
            missing_files = []
            for file in required_files:
                if not (self.project_root / file).exists():
                    missing_files.append(file)
            
            if missing_files:
                result["errors"].append(f"缺少必要文件: {missing_files}")
                result["success"] = False
            result["checks"]["required_files"] = "✅" if not missing_files else f"❌ 缺少: {missing_files}"
            
            # 检查环境变量
            env_file = self.project_root / ".env"
            if not env_file.exists():
                result["errors"].append(".env文件不存在")
                result["success"] = False
            else:
                result["checks"]["env_file"] = "✅"
            
            # 检查LLM连接
            self.log.info("检查LLM连接状态")
            llm_diagnostics = LLMConnectionDiagnostics()
            llm_status = llm_diagnostics.diagnose_all_providers()
            
            # LLM不可用时只给警告，不阻止部署（系统有fallback模式）
            available_providers = []
            for provider_name, provider_data in llm_status["results"].items():
                if provider_data["status"] == "healthy":
                    available_providers.append(provider_name)
            
            if not available_providers:
                self.log.warning("⚠️ 没有可用的LLM提供商，系统将使用fallback模式")
                result["checks"]["llm_connectivity_status"] = "⚠️ 无可用提供商，fallback模式"
            else:
                result["checks"]["llm_connectivity_status"] = f"✅ 可用提供商: {available_providers}"
            
            result["checks"]["llm_connectivity_details"] = llm_status
            
            # 生成系统报告
            system_report = self.reporter.generate_comprehensive_report()
            result["checks"]["system_status"] = system_report
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "checks": {}
            }
    
    def _prepare_environment(self) -> Dict[str, Any]:
        """准备部署环境"""
        try:
            result = {
                "success": True,
                "actions": [],
                "errors": []
            }
            
            # 创建必要目录
            directories = [
                "output/company",
                "output/contact", 
                "output/employee",
                "logs",
                "backups",
                f"deployments/{self.deployment_timestamp}"
            ]
            
            for directory in directories:
                dir_path = self.project_root / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                result["actions"].append(f"创建目录: {directory}")
            
            # 设置权限
            if os.name != 'nt':  # 非Windows系统
                os.chmod(self.project_root / "logs", 0o755)
                os.chmod(self.project_root / "output", 0o755)
                result["actions"].append("设置目录权限")
            
            # 创建配置备份
            if (self.project_root / ".env").exists():
                backup_path = self.project_root / f"backups/env_backup_{self.deployment_timestamp}"
                shutil.copy2(self.project_root / ".env", backup_path)
                result["actions"].append(f"备份配置文件到: {backup_path}")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "actions": []
            }
    
    def _install_dependencies(self) -> Dict[str, Any]:
        """安装依赖包"""
        try:
            result = {
                "success": True,
                "packages": [],
                "errors": []
            }
            
            # 升级pip
            self.log.info("升级pip")
            pip_result = subprocess.run([
                sys.executable, "-m", "pip", "install", "--upgrade", "pip"
            ], capture_output=True, text=True)
            
            if pip_result.returncode != 0:
                result["errors"].append(f"pip升级失败: {pip_result.stderr}")
                result["success"] = False
                return result
            
            # 安装requirements.txt
            requirements_file = self.project_root / "requirements.txt"
            if requirements_file.exists():
                self.log.info("安装Python依赖")
                install_result = subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
                ], capture_output=True, text=True)
                
                if install_result.returncode != 0:
                    result["errors"].append(f"依赖安装失败: {install_result.stderr}")
                    result["success"] = False
                    return result
                
                result["packages"].append("requirements.txt")
            
            # 安装Playwright浏览器
            self.log.info("安装Playwright浏览器")
            playwright_result = subprocess.run([
                sys.executable, "-m", "playwright", "install", "chromium"
            ], capture_output=True, text=True)
            
            if playwright_result.returncode != 0:
                result["errors"].append(f"Playwright安装失败: {playwright_result.stderr}")
                result["success"] = False
                return result
            
            result["packages"].append("playwright-chromium")
            
            # 验证关键包
            key_packages = {
                "langgraph": "langgraph",
                "playwright": "playwright", 
                "streamlit": "streamlit",
                "python-dotenv": "dotenv"
            }
            for package_name, import_name in key_packages.items():
                try:
                    __import__(import_name)
                    result["packages"].append(f"{package_name} ✅")
                except ImportError:
                    result["errors"].append(f"关键包 {package_name} 未正确安装")
                    result["success"] = False
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "packages": []
            }
    
    def _setup_configuration(self) -> Dict[str, Any]:
        """设置配置文件"""
        try:
            result = {
                "success": True,
                "configs": [],
                "errors": []
            }
            
            # 检查.env文件
            env_file = self.project_root / ".env"
            if not env_file.exists():
                # 复制示例文件
                example_file = self.project_root / ".env.example"
                if example_file.exists():
                    shutil.copy2(example_file, env_file)
                    result["configs"].append("从.env.example创建.env文件")
                    self.log.warning("⚠️ 请手动配置.env文件中的API密钥")
                else:
                    result["errors"].append(".env.example文件不存在")
                    result["success"] = False
                    return result
            
            # 验证环境配置
            from dotenv import load_dotenv
            load_dotenv(env_file)
            
            required_vars = ["SERPER_API_KEY"]
            missing_vars = []
            
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                self.log.warning(f"⚠️ 缺少环境变量: {missing_vars}")
                result["configs"].append(f"警告: 缺少环境变量 {missing_vars}")
            
            # 创建生产环境专用配置
            if self.environment == "production":
                prod_config = {
                    "environment": "production",
                    "debug": False,
                    "log_level": "INFO",
                    "max_concurrent": 2,  # 生产环境降低并发
                    "timeout": 60,
                    "enable_cache": True,
                    "performance_monitoring": True
                }
                
                config_file = self.project_root / "config" / "production.json"
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(prod_config, f, indent=2, ensure_ascii=False)
                
                result["configs"].append("创建生产环境配置")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "configs": []
            }
    
    def _run_integration_tests(self) -> Dict[str, Any]:
        """运行集成测试"""
        try:
            result = {
                "success": True,
                "tests": [],
                "errors": []
            }
            
            # 测试1: 基础模块导入
            self.log.info("测试基础模块导入")
            try:
                from langgraph_search.workflows.base_graph import create_search_graph
                from langgraph_search.nodes.robust_ai_evaluation import robust_ai_evaluation_node
                from config.logging_config import LangGraphLogger
                result["tests"].append("基础模块导入 ✅")
            except Exception as e:
                result["errors"].append(f"基础模块导入失败: {e}")
                result["success"] = False
            
            # 测试2: LangGraph工作流创建
            self.log.info("测试LangGraph工作流创建")
            try:
                graph = create_search_graph(enable_checkpoints=False)
                if graph.compiled_graph:
                    result["tests"].append("LangGraph工作流创建 ✅")
                else:
                    result["errors"].append("LangGraph编译失败")
                    result["success"] = False
            except Exception as e:
                result["errors"].append(f"LangGraph工作流创建失败: {e}")
                result["success"] = False
            
            # 测试3: LLM连接测试
            self.log.info("测试LLM连接")
            diagnostics = LLMConnectionDiagnostics()
            llm_result = diagnostics.diagnose_all_providers()
            
            working_providers = [name for name, data in llm_result["results"].items() if data["status"] == "healthy"]
            if working_providers:
                result["tests"].append(f"LLM连接测试 ✅ (可用: {working_providers})")
            else:
                self.log.warning("⚠️ 没有可用的LLM提供商，但不阻止部署")
                result["tests"].append("LLM连接测试 ⚠️ (无可用提供商)")
            
            # 测试4: 文件系统权限
            self.log.info("测试文件系统权限")
            test_file = self.project_root / "logs" / "test_write.tmp"
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                result["tests"].append("文件系统权限 ✅")
            except Exception as e:
                result["errors"].append(f"文件系统权限测试失败: {e}")
                result["success"] = False
            
            # 测试5: 监控系统
            self.log.info("测试监控系统")
            try:
                system_report = self.reporter.generate_comprehensive_report()
                if system_report.get("status") == "healthy":
                    result["tests"].append("监控系统 ✅")
                else:
                    result["tests"].append("监控系统 ⚠️ (系统状态异常)")
            except Exception as e:
                result["errors"].append(f"监控系统测试失败: {e}")
                result["success"] = False
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tests": []
            }
    
    def _start_services(self) -> Dict[str, Any]:
        """启动系统服务"""
        try:
            result = {
                "success": True,
                "services": [],
                "errors": []
            }
            
            # 对于这个项目，主要是确保Streamlit应用可以启动
            # 这里我们只做启动准备，不实际启动（避免阻塞）
            
            # 检查Streamlit配置
            streamlit_config = self.project_root / ".streamlit" / "config.toml"
            if not streamlit_config.exists():
                # 创建Streamlit配置目录和文件
                streamlit_config.parent.mkdir(exist_ok=True)
                with open(streamlit_config, 'w') as f:
                    f.write("""[server]
headless = true
port = 8501
address = "0.0.0.0"

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
""")
                result["services"].append("创建Streamlit配置")
            
            # 验证Streamlit应用文件存在
            app_files = [
                "streamlit_app.py",
                "pages/1_Company_Search.py", 
                "pages/2_Contact_Extraction.py",
                "pages/3_Employee_Search.py"
            ]
            
            missing_files = []
            for file in app_files:
                if not (self.project_root / file).exists():
                    missing_files.append(file)
            
            if missing_files:
                self.log.warning(f"⚠️ 缺少Streamlit应用文件: {missing_files}")
                result["services"].append(f"警告: 缺少应用文件 {missing_files}")
            else:
                result["services"].append("Streamlit应用文件检查 ✅")
            
            # 创建服务启动脚本
            start_script = self.project_root / "scripts" / "start_production.sh"
            with open(start_script, 'w') as f:
                f.write(f"""#!/bin/bash
# 生产环境启动脚本
# 生成时间: {self.deployment_timestamp}

cd "{self.project_root}"

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 设置环境变量
export PYTHONPATH="${{PYTHONPATH}}:{self.project_root}"
export ENVIRONMENT=production

# 启动Streamlit应用
echo "启动AI客户发现系统..."
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true

echo "系统已启动，访问 http://localhost:8501"
""")
            
            # 设置执行权限
            if os.name != 'nt':
                os.chmod(start_script, 0o755)
            
            result["services"].append(f"创建启动脚本: {start_script}")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "services": []
            }
    
    def _post_deployment_verification(self) -> Dict[str, Any]:
        """部署后验证"""
        try:
            result = {
                "success": True,
                "verifications": [],
                "errors": []
            }
            
            # 验证1: 系统健康检查
            self.log.info("系统健康检查")
            try:
                system_report = self.reporter.generate_comprehensive_report()
                health_score = system_report.get("health_score", 0)
                
                if health_score >= 70:
                    result["verifications"].append(f"系统健康检查 ✅ (得分: {health_score})")
                else:
                    result["verifications"].append(f"系统健康检查 ⚠️ (得分: {health_score})")
                    
            except Exception as e:
                result["errors"].append(f"健康检查失败: {e}")
                result["success"] = False
            
            # 验证2: 关键文件存在
            critical_files = [
                "langgraph_search/workflows/base_graph.py",
                "langgraph_search/nodes/robust_ai_evaluation.py",
                "config/logging_config.py",
                "scripts/start_production.sh"
            ]
            
            missing_critical = []
            for file in critical_files:
                if not (self.project_root / file).exists():
                    missing_critical.append(file)
            
            if missing_critical:
                result["errors"].append(f"缺少关键文件: {missing_critical}")
                result["success"] = False
            else:
                result["verifications"].append("关键文件检查 ✅")
            
            # 验证3: 鲁棒性AI评估节点
            self.log.info("验证鲁棒性AI评估节点")
            try:
                from langgraph_search.nodes.robust_ai_evaluation import robust_ai_evaluation_node
                if hasattr(robust_ai_evaluation_node, 'execute'):
                    result["verifications"].append("鲁棒性AI评估节点 ✅")
                else:
                    result["errors"].append("鲁棒性AI评估节点缺少execute方法")
                    result["success"] = False
            except Exception as e:
                result["errors"].append(f"鲁棒性AI评估节点验证失败: {e}")
                result["success"] = False
            
            # 验证4: 日志系统
            try:
                test_logger = LangGraphLogger()
                test_log = test_logger.setup_logger("deployment_test", "test_deployment.log")
                test_log.info("部署验证测试日志")
                result["verifications"].append("日志系统 ✅")
            except Exception as e:
                result["errors"].append(f"日志系统验证失败: {e}")
                result["success"] = False
            
            # 生成部署报告
            deployment_report = {
                "deployment_id": self.deployment_timestamp,
                "environment": self.environment,
                "completed_at": datetime.now().isoformat(),
                "system_health": system_report if 'system_report' in locals() else None,
                "verification_results": result
            }
            
            # 保存部署报告
            report_file = self.project_root / f"deployments/{self.deployment_timestamp}/deployment_report.json"
            report_file.parent.mkdir(parents=True, exist_ok=True)
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(deployment_report, f, indent=2, ensure_ascii=False, default=str)
            
            result["verifications"].append(f"部署报告已保存: {report_file}")
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "verifications": []
            }


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI客户发现系统部署脚本")
    parser.add_argument(
        "--environment", "-e", 
        choices=["development", "staging", "production"],
        default="production",
        help="部署环境"
    )
    parser.add_argument(
        "--skip-tests", 
        action="store_true",
        help="跳过集成测试"
    )
    
    args = parser.parse_args()
    
    # 创建部署管理器
    deployment_manager = DeploymentManager(environment=args.environment)
    
    print(f"""
🚀 AI客户发现系统部署
==========================================
环境: {args.environment}
时间: {deployment_manager.deployment_timestamp}
==========================================
""")
    
    # 运行部署
    result = deployment_manager.run_deployment()
    
    # 输出结果
    print("\n📊 部署结果:")
    print("=" * 40)
    
    for step in result.get("steps", []):
        status = "✅" if step["success"] else "❌"
        print(f"{status} {step['name']}")
        
        if not step["success"] and "errors" in step["details"]:
            for error in step["details"]["errors"]:
                print(f"   🔸 {error}")
    
    if result["success"]:
        print(f"\n🎉 部署成功完成!")
        print(f"📁 部署ID: {deployment_manager.deployment_timestamp}")
        print(f"🌐 启动命令: ./scripts/start_production.sh")
        print(f"📊 访问地址: http://localhost:8501")
        
        # 显示启动建议
        print(f"\n💡 启动建议:")
        print(f"1. 检查并配置 .env 文件中的API密钥")
        print(f"2. 运行 ./scripts/start_production.sh 启动系统")
        print(f"3. 访问 http://localhost:8501 使用系统")
        print(f"4. 查看日志: logs/ 目录")
        
    else:
        print(f"\n❌ 部署失败!")
        if result.get("errors"):
            print("错误详情:")
            for error in result["errors"]:
                print(f"   🔸 {error}")
    
    return 0 if result["success"] else 1


if __name__ == "__main__":
    exit(main())