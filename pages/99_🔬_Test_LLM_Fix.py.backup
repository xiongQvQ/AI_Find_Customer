#!/usr/bin/env python3
"""Test page for LLM fix verification"""

import streamlit as st
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import json
import time

# 加载环境变量 - 在最开始
load_dotenv()

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

# 页面配置
st.set_page_config(page_title="🔬 Test LLM Fix", page_icon="🔬", layout="wide")

st.title("🔬 LLM Fix Test Page")

# 显示环境变量状态
st.header("1️⃣ Environment Variables")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("LLM_PROVIDER", os.getenv('LLM_PROVIDER', 'NOT SET'))
with col2:
    st.metric("ARK_API_KEY", "SET" if os.getenv('ARK_API_KEY') else "NOT SET")
with col3:
    st.metric("ARK_BASE_URL", "SET" if os.getenv('ARK_BASE_URL') else "NOT SET")
with col4:
    st.metric("ARK_MODEL", "SET" if os.getenv('ARK_MODEL') else "NOT SET")

# LLM客户端测试
st.header("2️⃣ Test LLM Client")
if st.button("Test LLM Client Creation"):
    try:
        from langgraph_search.utils.robust_llm_client import get_robust_llm_client
        client = get_robust_llm_client()
        st.success(f"✅ LLM client created successfully: {client}")
        
        # 测试简单调用
        messages = [{"role": "user", "content": "Say 'LLM is working' in Chinese"}]
        response = client.call_llm_with_retry(messages)
        st.info(f"LLM Response: {response}")
    except Exception as e:
        st.error(f"❌ Error: {e}")
        import traceback
        st.code(traceback.format_exc())

# AI评估节点测试
st.header("3️⃣ Test AI Evaluation Node")
if st.button("Test AI Evaluation Node"):
    try:
        from langgraph_search.nodes.robust_ai_evaluation import get_robust_ai_evaluation_node
        
        node = get_robust_ai_evaluation_node()
        st.success(f"✅ Node created: {node}")
        st.info(f"Node has LLM client: {node.llm_client is not None}")
        
        # 测试评估
        test_company = {
            "name": "深圳AI科技有限公司",
            "industry": "人工智能",
            "description": "专注于深度学习和计算机视觉技术"
        }
        
        criteria = {
            "user_intent": "找深圳的AI公司",
            "target_industry": "人工智能"
        }
        
        result = node._evaluate_single_company_robust(test_company, criteria)
        if result:
            st.success("✅ Evaluation successful!")
            st.json({
                "ai_score": result.get('ai_score'),
                "ai_reason": result.get('ai_reason'),
                "is_qualified": result.get('is_qualified')
            })
        else:
            st.error("❌ Evaluation returned None")
            
    except Exception as e:
        st.error(f"❌ Error: {e}")
        import traceback
        st.code(traceback.format_exc())

# 完整工作流测试
st.header("4️⃣ Test Complete Workflow")
query = st.text_input("Search Query", value="Find AI companies in Shenzhen")

if st.button("Run Search Test"):
    with st.spinner("Running search..."):
        try:
            from langgraph_search import create_search_graph
            
            # 创建新的graph实例
            graph = create_search_graph(enable_checkpoints=True)
            
            # 执行搜索
            result = graph.execute_search(query, ai_evaluation_enabled=True)
            
            if result.get('success'):
                state = result.get('result', {})
                companies = state.get('search_results', {}).get('companies', [])
                
                st.success(f"✅ Search completed! Found {len(companies)} companies")
                
                # 显示前3个公司的评估结果
                if companies:
                    st.subheader("Sample Results:")
                    for i, company in enumerate(companies[:3]):
                        with st.expander(f"Company {i+1}: {company.get('name', 'Unknown')}"):
                            col1, col2 = st.columns([1, 2])
                            with col1:
                                st.metric("AI Score", company.get('ai_score', 'N/A'))
                            with col2:
                                st.info(f"**AI Reason:** {company.get('ai_reason', 'N/A')}")
                            
                            # 检查是否还在使用基础评估
                            if company.get('ai_reason') == '基础评估（无LLM可用）':
                                st.error("❌ Still using basic evaluation!")
                            else:
                                st.success("✅ Using proper AI evaluation!")
                                
                # 保存完整结果
                timestamp = int(time.time())
                filename = f"test_workflow_result_{timestamp}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(state.get('search_results', {}), f, ensure_ascii=False, indent=2)
                st.info(f"Full results saved to: {filename}")
                
            else:
                st.error(f"Search failed: {result.get('error')}")
                
        except Exception as e:
            st.error(f"❌ Error: {e}")
            import traceback
            st.code(traceback.format_exc())

# 清理缓存
st.header("5️⃣ Cache Management")
col1, col2 = st.columns(2)
with col1:
    if st.button("Clear Streamlit Cache"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("✅ Cache cleared!")
        
with col2:
    if st.button("Clear Session State"):
        for key in list(st.session_state.keys()):
            if 'langgraph' in key.lower():
                del st.session_state[key]
        st.success("✅ Session state cleared!")