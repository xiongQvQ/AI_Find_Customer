#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit应用启动测试
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

def test_imports():
    """测试关键模块导入"""
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
    """测试LLM连接"""
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
