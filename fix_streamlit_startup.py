#!/usr/bin/env python3
"""
修复Streamlit应用启动问题
主要解决文件名包含emoji字符导致的导入问题
"""

import os
import sys
import shutil
from pathlib import Path

def fix_streamlit_pages():
    """修复Streamlit页面文件名问题"""
    
    pages_dir = Path("pages")
    if not pages_dir.exists():
        print("❌ pages目录不存在")
        return False
    
    # 问题文件映射：emoji文件名 -> 安全文件名
    problematic_files = {
        "7_🔍_Intelligent_Search_LangGraph.py": "7_Intelligent_Search_LangGraph.py",
        "7_🔍_Intelligent_Search.py": "7_Intelligent_Search.py", 
        "1_🔍_Company_Search.py": "1_Company_Search.py",
        "2_📧_Contact_Extraction.py": "2_Contact_Extraction.py",
        "3_👥_Employee_Search.py": "3_Employee_Search.py",
        "4_🤖_AI_Analysis.py": "4_AI_Analysis.py",
        "5_👥_Employee_AI_Analysis.py": "5_Employee_AI_Analysis.py",
        "6_⚙️_System_Settings.py": "6_System_Settings.py",
        "8_📊_AI_Analytics_Dashboard.py": "8_AI_Analytics_Dashboard.py",
        "99_🔬_Test_LLM_Fix.py": "99_Test_LLM_Fix.py"
    }
    
    print("🔧 开始修复Streamlit页面文件名...")
    
    for old_name, new_name in problematic_files.items():
        old_path = pages_dir / old_name
        new_path = pages_dir / new_name
        
        if old_path.exists():
            try:
                # 备份原文件
                backup_path = pages_dir / f"{old_name}.backup"
                if not backup_path.exists():
                    shutil.copy2(old_path, backup_path)
                    print(f"📋 备份: {old_name} -> {backup_path.name}")
                
                # 创建新文件（修复文件名问题）
                print(f"🔄 修复: {old_name} -> {new_name}")
                
                # 读取原文件内容
                with open(old_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 写入新文件
                with open(new_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ 成功创建: {new_name}")
                
            except Exception as e:
                print(f"❌ 修复失败 {old_name}: {e}")
                return False
        else:
            print(f"⚠️ 文件不存在: {old_name}")
    
    print("🎉 Streamlit页面文件名修复完成")
    return True

def fix_import_references():
    """修复导入引用中的emoji文件名"""
    
    files_to_check = [
        "streamlit_app.py",
        "pages/7_Intelligent_Search_LangGraph.py"
    ]
    
    print("🔧 检查并修复导入引用...")
    
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 替换emoji文件名引用
            replacements = {
                "7_🔍_Intelligent_Search_LangGraph.py": "7_Intelligent_Search_LangGraph.py",
                "pages/7_🔍_Intelligent_Search_LangGraph.py": "pages/7_Intelligent_Search_LangGraph.py",
                '"7_🔍_Intelligent_Search_LangGraph"': '"7_Intelligent_Search_LangGraph"',
                "'7_🔍_Intelligent_Search_LangGraph'": "'7_Intelligent_Search_LangGraph'"
            }
            
            for old_ref, new_ref in replacements.items():
                if old_ref in content:
                    content = content.replace(old_ref, new_ref)
                    print(f"🔄 修复引用: {file_path} 中的 {old_ref}")
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ 更新文件: {file_path}")
            
        except Exception as e:
            print(f"❌ 修复文件失败 {file_path}: {e}")
            return False
    
    print("🎉 导入引用修复完成")
    return True

def create_startup_test():
    """创建启动测试脚本"""
    
    test_script = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
Streamlit应用启动测试
\"\"\"

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

def test_imports():
    \"\"\"测试关键模块导入\"\"\"
    print("🧪 测试模块导入...")
    
    try:
        import streamlit as st
        print(f"✅ Streamlit {st.__version__}")
    except Exception as e:
        print(f"❌ Streamlit导入失败: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ 环境变量加载")
    except Exception as e:
        print(f"❌ 环境变量加载失败: {e}")
        return False
    
    try:
        from components.common import check_api_keys
        api_status = check_api_keys()
        print("✅ 组件导入")
    except Exception as e:
        print(f"❌ 组件导入失败: {e}")
        return False
    
    try:
        from langgraph_search import create_search_graph
        print("✅ LangGraph模块")
    except Exception as e:
        print(f"❌ LangGraph模块失败: {e}")
        return False
    
    return True

def test_llm_connection():
    \"\"\"测试LLM连接\"\"\"
    print("🧪 测试LLM连接...")
    
    try:
        from langgraph_search.llm.llm_client import LLMClient
        client = LLMClient()
        if client.is_available():
            print(f"✅ LLM客户端可用 ({client.provider})")
            
            # 测试调用
            test_messages = [{"role": "user", "content": "测试"}]
            response = client.call_llm(test_messages)
            print("✅ LLM调用测试通过")
            return True
        else:
            print("❌ LLM客户端不可用")
            return False
    except Exception as e:
        print(f"❌ LLM连接测试失败: {e}")
        return False

def main():
    print("🚀 开始Streamlit应用启动测试...")
    print("=" * 50)
    
    # 测试导入
    imports_ok = test_imports()
    
    # 测试LLM
    llm_ok = test_llm_connection()
    
    print("=" * 50)
    if imports_ok and llm_ok:
        print("🎉 所有测试通过！Streamlit应用应该可以正常启动。")
        print()
        print("📋 启动命令:")
        print("streamlit run streamlit_app.py")
        print()
        print("🌐 访问地址:")
        print("http://localhost:8501")
        return True
    else:
        print("❌ 部分测试失败，请检查错误信息。")
        return False

if __name__ == "__main__":
    main()
"""
    
    try:
        with open("test_startup.py", 'w', encoding='utf-8') as f:
            f.write(test_script)
        
        os.chmod("test_startup.py", 0o755)
        print("✅ 创建启动测试脚本: test_startup.py")
        return True
    except Exception as e:
        print(f"❌ 创建测试脚本失败: {e}")
        return False

def main():
    """主修复流程"""
    print("🔧 Streamlit应用修复工具")
    print("=" * 50)
    
    # 1. 修复页面文件名
    if not fix_streamlit_pages():
        print("❌ 页面文件名修复失败")
        return False
    
    # 2. 修复导入引用
    if not fix_import_references():
        print("❌ 导入引用修复失败")
        return False
    
    # 3. 创建测试脚本
    if not create_startup_test():
        print("❌ 测试脚本创建失败")
        return False
    
    print("=" * 50)
    print("🎉 修复完成！")
    print()
    print("📋 后续步骤:")
    print("1. 运行测试: python test_startup.py")
    print("2. 启动应用: streamlit run streamlit_app.py")
    print("3. 访问页面: http://localhost:8501")
    print()
    print("🔧 如果仍有问题，请检查:")
    print("- 确保在正确的conda环境中: conda activate aifinder_env")
    print("- 检查端口8501是否被占用")
    print("- 查看启动时的错误日志")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)