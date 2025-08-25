#!/usr/bin/env python3
"""
测试评分系统的示例脚本
演示如何使用不同的profile对现有数据进行评分
"""

import subprocess
import os
from pathlib import Path

def run_scoring_test():
    """运行评分测试"""
    
    # 检查是否有数据文件
    company_dir = Path("output/company")
    if not company_dir.exists() or not list(company_dir.glob("*.csv")):
        print("❌ 未找到公司数据文件，请先运行搜索脚本生成数据")
        print("   示例: python serper_company_search.py --general-search --industry 'solar energy' --region 'California' --gl 'us'")
        return
    
    # 获取最新的公司数据文件
    csv_files = list(company_dir.glob("*.csv"))
    latest_file = max(csv_files, key=os.path.getctime)
    
    print(f"🔍 使用数据文件: {latest_file}")
    
    # 测试不同的profile
    profiles = [
        "profiles/solar_profile.yaml",
        "profiles/software_saas_profile.yaml", 
        "profiles/logistics_profile.yaml"
    ]
    
    for profile in profiles:
        if not os.path.exists(profile):
            print(f"⚠️  配置文件不存在: {profile}")
            continue
            
        print(f"\n🎯 测试配置: {profile}")
        
        # 运行评分命令
        cmd = [
            "python", "score_leads.py",
            "--company-csv", str(latest_file),
            "--profile", profile,
            "--min-score", "20"  # 只显示得分20以上的结果
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("✅ 评分完成")
                # 输出最后几行结果（统计信息）
                lines = result.stdout.strip().split('\n')
                for line in lines[-10:]:  # 显示最后10行
                    if line.strip():
                        print(f"   {line}")
            else:
                print("❌ 评分失败")
                print(f"   错误: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("⏰ 评分超时")
        except Exception as e:
            print(f"❌ 运行错误: {e}")

def show_usage_examples():
    """显示使用示例"""
    print("📖 使用示例:")
    print()
    print("1. 基础评分:")
    print("   python score_leads.py --company-csv output/company/your_file.csv --profile profiles/solar_profile.yaml")
    print()
    print("2. 带联系信息的评分:")
    print("   python score_leads.py --company-csv output/company/your_file.csv --contact-csv output/contact/contact_file.csv --profile profiles/solar_profile.yaml")
    print()
    print("3. 完整评分（包含员工信息）:")
    print("   python score_leads.py --company-csv output/company/your_file.csv --contact-csv output/contact/contact_file.csv --employee-csv output/employee/employee_file.csv --profile profiles/solar_profile.yaml")
    print()
    print("4. 设置最低分数阈值:")
    print("   python score_leads.py --company-csv output/company/your_file.csv --profile profiles/solar_profile.yaml --min-score 60")
    print()
    print("📁 支持的配置文件:")
    profiles_dir = Path("profiles")
    if profiles_dir.exists():
        for profile_file in profiles_dir.glob("*.yaml"):
            print(f"   - {profile_file}")

if __name__ == "__main__":
    import sys
    
    print("🧪 AI客户发现工具 - 评分系统测试")
    print("="*50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        run_scoring_test()
    else:
        show_usage_examples()
        print("\n运行 'python test_scoring.py test' 来自动测试现有数据")