#!/usr/bin/env python3
"""
智能搜索页面 - LangGraph工作流集成
为用户提供自然语言智能搜索体验 - 支持意图识别和复合搜索
"""

import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import os
import sys
from pathlib import Path
import asyncio
import threading
from dotenv import load_dotenv

# 优先加载环境变量 - 在任何其他导入之前
load_dotenv()

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

# 导入组件
from components.common import check_api_keys, display_api_status
from components.language_manager import get_language_manager, t

# 页面配置
st.set_page_config(
    page_title="🔍 LangGraph智能搜索",
    page_icon="🔍",
    layout="wide"
)

# 自定义CSS样式
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}
.section-header {
    font-size: 1.5rem;
    color: #2e86ab;
    margin: 1rem 0;
}
.status-healthy {
    color: #28a745;
}
.intent-badge {
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: bold;
    margin: 0.2rem;
    display: inline-block;
}
.intent-company {
    background-color: #e3f2fd;
    color: #1976d2;
    border: 1px solid #1976d2;
}
.intent-employee {
    background-color: #f3e5f5;
    color: #7b1fa2;
    border: 1px solid #7b1fa2;
}
.intent-composite {
    background-color: #fff3e0;
    color: #f57c00;
    border: 1px solid #f57c00;
}
.workflow-step {
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 1rem;
    margin: 0.5rem 0;
    transition: all 0.3s ease;
}
.step-pending {
    background-color: #f8f9fa;
    color: #6c757d;
}
.step-current {
    background-color: #cce7ff;
    color: #004085;
    border-color: #007bff;
    animation: pulse 2s infinite;
}
.step-completed {
    background-color: #d4edda;
    color: #155724;
    border-color: #28a745;
}
.step-error {
    background-color: #f8d7da;
    color: #721c24;
    border-color: #dc3545;
}
@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.02); }
    100% { transform: scale(1); }
}
.result-card {
    border: 1px solid #dee2e6;
    border-radius: 0.5rem;
    padding: 1rem;
    margin: 0.5rem 0;
    background-color: #ffffff;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.score-excellent {
    color: #28a745;
    font-weight: bold;
}
.score-good {
    color: #17a2b8;
    font-weight: bold;
}
.score-fair {
    color: #ffc107;
    font-weight: bold;
}
.confidence-high {
    color: #28a745;
}
.confidence-medium {
    color: #ffc107;
}
.confidence-low {
    color: #dc3545;
}
.progress-container {
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
    background-color: #f8f9fa;
}
</style>
""", unsafe_allow_html=True)

def initialize_langgraph_search():
    """初始化LangGraph搜索系统"""
    try:
        # 确保环境变量已加载
        if not os.getenv('LLM_PROVIDER'):
            st.warning("检测到环境变量未加载，重新加载...")
            load_dotenv()
            st.info(f"环境变量重新加载完成 - LLM_PROVIDER: {os.getenv('LLM_PROVIDER')}")
        
        from langgraph_search import create_search_graph
        
        # 强制重新创建graph，不使用缓存
        # if 'langgraph_search_graph' not in st.session_state:
        st.session_state.langgraph_search_graph = create_search_graph(
            enable_checkpoints=True
        )
        
        return st.session_state.langgraph_search_graph
    
    except Exception as e:
        st.error(f"❌ LangGraph搜索系统初始化失败: {str(e)}")
        st.error("请确保langgraph_search模块已正确安装和配置")
        import traceback
        st.code(traceback.format_exc())
        return None

def check_system_health():
    """检查LangGraph系统健康状态"""
    try:
        # 检查必要的模块导入
        from langgraph_search import create_search_graph
        from langgraph_search.state import SearchState, create_initial_state
        
        # 尝试创建初始状态
        test_state = create_initial_state("测试查询")
        
        st.success("✅ LangGraph智能搜索系统运行正常")
        return True
        
    except ImportError as e:
        st.error(f"❌ 系统模块缺失: {str(e)}")
        return False
    except Exception as e:
        st.error(f"❌ 系统检查失败: {str(e)}")
        return False

def display_intent_badge(intent: str, confidence: float):
    """显示意图识别徽章"""
    intent_labels = {
        'company': '🏢 公司搜索',
        'employee': '👥 员工搜索', 
        'composite': '🔄 复合搜索',
        'unknown': '❓ 未知意图'
    }
    
    intent_classes = {
        'company': 'intent-company',
        'employee': 'intent-employee',
        'composite': 'intent-composite',
        'unknown': 'intent-unknown'
    }
    
    label = intent_labels.get(intent, f'❓ {intent}')
    css_class = intent_classes.get(intent, 'intent-unknown')
    
    confidence_text = "高" if confidence >= 0.7 else "中" if confidence >= 0.4 else "低"
    confidence_color = "confidence-high" if confidence >= 0.7 else "confidence-medium" if confidence >= 0.4 else "confidence-low"
    
    st.markdown(f"""
    <span class="intent-badge {css_class}">{label}</span>
    <span class="intent-badge {confidence_color}">置信度: {confidence:.2f} ({confidence_text})</span>
    """, unsafe_allow_html=True)

def display_workflow_progress(state: Dict[str, Any]):
    """显示工作流进度"""
    st.markdown("### 🔄 LangGraph工作流进度")
    
    workflow_steps = [
        {
            "name": "意图识别",
            "icon": "🧠",
            "description": "分析用户查询意图",
            "key": "intent_recognition_completed"
        },
        {
            "name": "公司搜索", 
            "icon": "🏢",
            "description": "搜索相关公司信息",
            "key": "company_search_completed"
        },
        {
            "name": "AI评估",
            "icon": "📊", 
            "description": "智能评估和筛选",
            "key": "ai_evaluation_completed"
        },
        {
            "name": "员工搜索",
            "icon": "👥",
            "description": "搜索关键决策人员",
            "key": "employee_search_completed"
        },
        {
            "name": "结果整合",
            "icon": "📋",
            "description": "整合并输出结果",
            "key": "output_integration_completed"
        }
    ]
    
    # 获取当前节点和工作流路径
    current_node = state.get("current_node", "")
    workflow_path = state.get("workflow_path", [])
    errors = state.get("errors", [])
    
    cols = st.columns(len(workflow_steps))
    
    for i, (col, step) in enumerate(zip(cols, workflow_steps)):
        with col:
            # 确定步骤状态
            step_completed = state.get(step["key"], False)
            is_current = step["name"].lower().replace(" ", "_") in current_node.lower()
            has_error = any(error.get("node", "").startswith(step["name"].lower()) for error in errors)
            
            if has_error:
                css_class = "step-error"
                status_icon = "❌"
            elif step_completed:
                css_class = "step-completed" 
                status_icon = "✅"
            elif is_current:
                css_class = "step-current"
                status_icon = "🔄"
            else:
                css_class = "step-pending"
                status_icon = "⏳"
            
            st.markdown(f"""
            <div class="workflow-step {css_class}">
                <div style="text-align: center;">
                    <div style="font-size: 24px;">{step["icon"]}</div>
                    <div style="font-size: 12px; font-weight: bold; margin: 5px 0;">{step["name"]}</div>
                    <div style="font-size: 10px; color: #666; margin-bottom: 5px;">{step["description"]}</div>
                    <div style="font-size: 16px;">{status_icon}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

def display_search_results(result: Dict[str, Any]):
    """显示搜索结果 - 修复代码结构错误版本"""
    try:
        # 第一层验证：结果存在性
        if not result:
            st.error("❌ 搜索结果为空")
            st.info("💡 请返回搜索页面重新执行搜索")
            return
        
        # 第二层验证：成功状态
        if not result.get("success"):
            error_msg = result.get("error", "未知错误")
            st.error(f"❌ 搜索失败: {error_msg}")
            
            # 显示错误处理建议
            with st.expander("🔧 错误解决建议", expanded=True):
                if "output_integration" in error_msg:
                    st.markdown("""
                    **输出集成错误：**
                    - 这是一个内部处理错误
                    - 建议刷新页面重试
                    - 如果问题持续，请联系技术支持
                    """)
                elif "search_criteria" in error_msg:
                    st.markdown("""
                    **参数错误：**
                    - 搜索参数配置有误
                    - 请尝试重新描述搜索需求
                    - 确保搜索条件明确具体
                    """)
                else:
                    st.markdown("""
                    **通用解决方案：**
                    - 检查网络连接
                    - 简化搜索需求
                    - 刷新页面重试
                    """)
            return
        
        # 第三层验证：状态结构
        state = result.get("result", {})
        if not state or not isinstance(state, dict):
            st.error("❌ 搜索结果状态格式错误")
            st.info("💡 内部状态解析失败，请重新搜索")
            return
        
        # 第四层验证：搜索结果结构
        search_results = state.get("search_results", {})
        if not isinstance(search_results, dict):
            st.error("❌ 搜索结果数据格式错误")
            st.info("💡 数据格式不正确，请重新搜索")
            return
        
        # 检查特定错误 - 但不要阻止显示结果
        if 'output_integration_error' in state:
            st.warning(f"⚠️ 输出处理警告: {state['output_integration_error']}")
            with st.expander("🔧 修复建议"):
                st.markdown("""
                **输出集成警告：**
                1. 部分功能可能受影响，但搜索结果仍可显示
                2. 如果导出功能不可用，请手动复制结果
                3. 可以尝试刷新页面以恢复完整功能
                """)
            # 继续显示结果，不要返回

        # 搜索摘要 - 移动到try块内，确保变量作用域正确
        st.markdown("### 📊 搜索摘要")
        
        col1, col2, col3, col4 = st.columns(4)
        
        companies = search_results.get("companies", [])
        qualified_companies = search_results.get("qualified_companies", [])
        employees = search_results.get("employees", [])
        qualified_employees = search_results.get("qualified_employees", [])
        
        with col1:
            st.metric("找到公司", len(companies))
        
        with col2:
            st.metric("合格公司", len(qualified_companies))
        
        with col3:
            st.metric("找到员工", len(employees))
        
        with col4:
            st.metric("合格员工", len(qualified_employees))
        
        # 意图识别结果
        st.markdown("### 🧠 意图识别结果")
        
        intent = state.get("detected_intent", "unknown")
        confidence = state.get("intent_confidence", 0.0)
        reasoning = state.get("intent_reasoning", "")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            display_intent_badge(intent, confidence)
        
        with col2:
            if reasoning:
                with st.expander("📋 识别详情"):
                    st.text(reasoning)
        
        # 公司搜索结果
        if qualified_companies:
            st.markdown("### 🏢 推荐公司")
            
            # 筛选控制
            col1, col2 = st.columns(2)
            
            with col1:
                min_score = st.slider("最低AI评分", 0.0, 10.0, 0.0, 0.5)
            
            with col2:
                show_all = st.checkbox("显示所有公司", value=False)
            
            display_companies = qualified_companies if show_all else [
                c for c in qualified_companies 
                if safe_get_attribute(c, 'ai_score', 0) >= min_score
            ]
            
            for i, company in enumerate(display_companies, 1):
                display_company_result_card(company, i)
        elif companies:  # 如果有公司但没有合格的，显示所有公司
            st.markdown("### 🏢 搜索到的公司")
            st.info("💡 没有公司达到推荐标准（AI评分≥60），显示所有搜索结果")
            
            # 显示所有公司
            for i, company in enumerate(companies, 1):
                display_company_result_card(company, i)
        
        # 员工搜索结果
        if qualified_employees:
            st.markdown("### 👥 推荐员工")
            
            for i, employee in enumerate(qualified_employees, 1):
                display_employee_result_card(employee, i)
        elif employees:  # 如果有员工但没有合格的，显示所有员工
            st.markdown("### 👥 搜索到的员工")
            st.info("💡 没有员工达到推荐标准（AI评分≥70），显示所有搜索结果")
            
            # 显示所有员工
            for i, employee in enumerate(employees, 1):
                display_employee_result_card(employee, i)
        
        # 如果没有任何结果
        if not companies and not employees:
            st.warning("⚠️ 没有找到任何搜索结果")
            st.info("""
            💡 **建议：**
            - 尝试使用更通用的搜索词
            - 检查地区和行业设置是否过于具体
            - 确保搜索查询描述清晰
            """)
        
        # 错误和警告处理
        display_errors_and_warnings(state)
        
        # 澄清建议
        display_clarification_suggestions(state)
        
        # 导出功能
        st.markdown("### 📥 导出结果")
        export_search_results(state)
        
    except Exception as e:
        st.error(f"❌ 搜索结果显示错误: {str(e)}")
        st.info("💡 请尝试刷新页面重新搜索")
        
        # 提供调试信息
        with st.expander("🔍 调试信息", expanded=False):
            st.text(f"错误类型: {type(e).__name__}")
            st.text(f"错误详情: {str(e)}")
            if result:
                st.text(f"结果类型: {type(result)}")
                st.text(f"结果键: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
            else:
                st.text("结果为空")

def display_company_result_card(company, rank: int):
    """显示公司结果卡片 - 增强安全性版本"""
    try:
        with st.container():
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            
            # 标题行
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                company_name = safe_get_attribute(company, 'name', 'Unknown Company')
                st.markdown(f"### {rank}. {company_name}")
            
            with col2:
                ai_score = safe_get_attribute(company, 'ai_score', 0)
                try:
                    ai_score = float(ai_score) if ai_score is not None else 0.0
                except (ValueError, TypeError):
                    ai_score = 0.0
                    
                if ai_score >= 8:
                    st.markdown(f'<span class="score-excellent">⭐ {ai_score:.1f}分</span>', unsafe_allow_html=True)
                elif ai_score >= 6:
                    st.markdown(f'<span class="score-good">🔵 {ai_score:.1f}分</span>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<span class="score-fair">🟡 {ai_score:.1f}分</span>', unsafe_allow_html=True)
            
            with col3:
                is_qualified = safe_get_attribute(company, 'is_qualified', False)
                qualification = "✅ 合格" if is_qualified else "⏳ 待评估"
                st.write(qualification)
            
            # 详细信息
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # 基本信息
                industry = safe_get_attribute(company, 'industry', '')
                location = safe_get_attribute(company, 'location', '')
                description = safe_get_attribute(company, 'description', '')
                
                if industry:
                    st.write(f"**行业**: {industry}")
                if location:
                    st.write(f"**位置**: {location}")
                if description and len(str(description)) > 0:
                    desc_text = str(description)
                    display_desc = desc_text[:200] + "..." if len(desc_text) > 200 else desc_text
                    st.write(f"**描述**: {display_desc}")
                
                # AI评估理由
                ai_reason = safe_get_attribute(company, 'ai_reason', '')
                if ai_reason:
                    st.write(f"**AI评估**: {ai_reason}")
            
            with col2:
                # 链接信息
                website = safe_get_attribute(company, 'website', '') or safe_get_attribute(company, 'website_url', '')
                linkedin_url = safe_get_attribute(company, 'linkedin_url', '')
                
                if website and website.strip():
                    # 确保 URL有协议
                    if not website.startswith(('http://', 'https://')):
                        website = f'https://{website}'
                    st.markdown(f"[🌐 官网]({website})")
                    
                if linkedin_url and linkedin_url.strip():
                    if not linkedin_url.startswith(('http://', 'https://')):
                        linkedin_url = f'https://{linkedin_url}'
                    st.markdown(f"[💼 LinkedIn]({linkedin_url})")
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("---")
            
    except Exception as e:
        st.error(f"❌ 公司信息显示错误: {str(e)}")
        with st.expander("🔍 调试信息"):
            st.write(f"**公司数据类型**: {type(company)}")
            st.write(f"**公司数据**: {str(company)[:200]}...")

def display_employee_result_card(employee, rank: int):
    """显示员工结果卡片 - 增强安全性版本"""
    try:
        with st.container():
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            
            # 标题行
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                name = safe_get_attribute(employee, 'name', 'Unknown Person')
                position = safe_get_attribute(employee, 'position', '')
                company = safe_get_attribute(employee, 'company', '')
                st.markdown(f"### {rank}. {name}")
                if position and company:
                    st.write(f"**{position}** @ {company}")
                elif position:
                    st.write(f"**{position}**")
                elif company:
                    st.write(f"@ {company}")
            
            with col2:
                ai_score = safe_get_attribute(employee, 'ai_score', 0)
                try:
                    ai_score = float(ai_score) if ai_score is not None else 0.0
                except (ValueError, TypeError):
                    ai_score = 0.0
                    
                if ai_score >= 8:
                    st.markdown(f'<span class="score-excellent">⭐ {ai_score:.1f}分</span>', unsafe_allow_html=True)
                elif ai_score >= 6:
                    st.markdown(f'<span class="score-good">🔵 {ai_score:.1f}分</span>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<span class="score-fair">🟡 {ai_score:.1f}分</span>', unsafe_allow_html=True)
            
            with col3:
                is_qualified = safe_get_attribute(employee, 'is_qualified', False)
                qualification = "✅ 合格" if is_qualified else "⏳ 待评估"
                st.write(qualification)
            
            # 详细信息
            col1, col2 = st.columns([2, 1])
            
            with col1:
                location = safe_get_attribute(employee, 'location', '')
                description = safe_get_attribute(employee, 'description', '')
                
                if location:
                    st.write(f"**位置**: {location}")
                if description and len(str(description)) > 0:
                    desc_text = str(description)
                    display_desc = desc_text[:150] + "..." if len(desc_text) > 150 else desc_text
                    st.write(f"**描述**: {display_desc}")
                
                # AI评估理由
                ai_reason = safe_get_attribute(employee, 'ai_reason', '')
                if ai_reason:
                    st.write(f"**AI评估**: {ai_reason}")
            
            with col2:
                linkedin_url = safe_get_attribute(employee, 'linkedin_url', '')
                if linkedin_url and linkedin_url.strip():
                    if not linkedin_url.startswith(('http://', 'https://')):
                        linkedin_url = f'https://{linkedin_url}'
                    st.markdown(f"[💼 LinkedIn Profile]({linkedin_url})")
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("---")
            
    except Exception as e:
        st.error(f"❌ 员工信息显示错误: {str(e)}")
        with st.expander("🔍 调试信息"):
            st.write(f"**员工数据类型**: {type(employee)}")
            st.write(f"**员工数据**: {str(employee)[:200]}...")

def export_search_results(state: Dict[str, Any]):
    """导出搜索结果"""
    col1, col2, col3 = st.columns(3)
    
    search_results = state.get("search_results", {})
    
    with col1:
        if st.button("📄 导出公司结果", use_container_width=True):
            companies = search_results.get("qualified_companies", [])
            if companies:
                export_companies_to_csv(companies)
            else:
                st.warning("无公司结果可导出")
    
    with col2:
        if st.button("👥 导出员工结果", use_container_width=True):
            employees = search_results.get("qualified_employees", [])
            if employees:
                export_employees_to_csv(employees)
            else:
                st.warning("无员工结果可导出")
    
    with col3:
        if st.button("📋 导出完整报告", use_container_width=True):
            export_complete_report(state)

def export_companies_to_csv(companies):
    """导出公司结果为CSV - 增强安全性版本"""
    try:
        export_data = []
        for i, company in enumerate(companies, 1):
            try:
                ai_score = safe_get_attribute(company, 'ai_score', 0)
                ai_score = float(ai_score) if ai_score is not None else 0.0
            except (ValueError, TypeError):
                ai_score = 0.0
                
            export_data.append({
                '排名': i,
                '公司名称': safe_get_attribute(company, 'name', ''),
                '行业': safe_get_attribute(company, 'industry', ''),
                '位置': safe_get_attribute(company, 'location', ''),
                '描述': safe_get_attribute(company, 'description', ''),
                'AI评分': ai_score,
                'AI评估': safe_get_attribute(company, 'ai_reason', ''),
                '是否合格': '是' if safe_get_attribute(company, 'is_qualified', False) else '否',
                '官网': safe_get_attribute(company, 'website', '') or safe_get_attribute(company, 'website_url', ''),
                'LinkedIn': safe_get_attribute(company, 'linkedin_url', '')
            })
        
        df = pd.DataFrame(export_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"companies_search_results_{timestamp}.csv"
        
        csv = df.to_csv(index=False, encoding='utf-8')
        st.download_button(
            label="📥 下载公司结果CSV",
            data=csv,
            file_name=filename,
            mime='text/csv'
        )
        
        st.success(f"✅ 公司结果已准备下载: {len(companies)} 条记录")
        
    except Exception as e:
        st.error(f"导出失败: {str(e)}")

def export_employees_to_csv(employees):
    """导出员工结果为CSV - 增强安全性版本"""
    try:
        export_data = []
        for i, employee in enumerate(employees, 1):
            try:
                ai_score = safe_get_attribute(employee, 'ai_score', 0)
                ai_score = float(ai_score) if ai_score is not None else 0.0
            except (ValueError, TypeError):
                ai_score = 0.0
                
            export_data.append({
                '排名': i,
                '姓名': safe_get_attribute(employee, 'name', ''),
                '职位': safe_get_attribute(employee, 'position', ''),
                '公司': safe_get_attribute(employee, 'company', ''),
                '位置': safe_get_attribute(employee, 'location', ''),
                '描述': safe_get_attribute(employee, 'description', ''),
                'AI评分': ai_score,
                'AI评估': safe_get_attribute(employee, 'ai_reason', ''),
                '是否合格': '是' if safe_get_attribute(employee, 'is_qualified', False) else '否',
                'LinkedIn': safe_get_attribute(employee, 'linkedin_url', '')
            })
        
        df = pd.DataFrame(export_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"employees_search_results_{timestamp}.csv"
        
        csv = df.to_csv(index=False, encoding='utf-8')
        st.download_button(
            label="📥 下载员工结果CSV",
            data=csv,
            file_name=filename,
            mime='text/csv'
        )
        
        st.success(f"✅ 员工结果已准备下载: {len(employees)} 条记录")
        
    except Exception as e:
        st.error(f"导出失败: {str(e)}")

def export_complete_report(state: Dict[str, Any]):
    """导出完整搜索报告"""
    try:
        # 生成报告内容
        report_data = {
            "搜索信息": {
                "查询": state.get("user_query", ""),
                "意图": state.get("detected_intent", ""),
                "置信度": state.get("intent_confidence", 0),
                "会话ID": state.get("session_id", ""),
                "时间戳": state.get("timestamp", "")
            },
            "搜索结果统计": state.get("search_results", {}),
            "工作流路径": state.get("workflow_path", []),
            "错误": state.get("errors", []),
            "警告": state.get("warnings", [])
        }
        
        # 转换为JSON
        report_json = json.dumps(report_data, ensure_ascii=False, indent=2)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"langgraph_search_report_{timestamp}.json"
        
        st.download_button(
            label="📥 下载完整报告JSON",
            data=report_json,
            file_name=filename,
            mime='application/json'
        )
        
        st.success(f"✅ 完整报告已准备下载")
        
    except Exception as e:
        st.error(f"导出失败: {str(e)}")

def main():
    """主界面函数"""
    # 标题
    st.markdown(f'<h1 class="main-header">🔍 LangGraph智能搜索</h1>', unsafe_allow_html=True)
    st.markdown(f'<p style="text-align: center; color: #6c757d;">基于LangGraph的智能搜索工作流 - 支持意图识别和复合搜索</p>', unsafe_allow_html=True)
    
    # 检查API密钥
    api_status = check_api_keys()
    if not api_status["SERPER_API_KEY"]:
        st.error("❌ 缺少必需的API密钥: SERPER_API_KEY")
        st.info("💡 请前往 **系统设置** 页面配置API密钥")
        if st.button("🔗 前往系统设置"):
            st.switch_page("pages/6_⚙️_System_Settings.py")
        st.stop()
    
    # 显示API状态
    display_api_status()
    
    # 系统健康检查
    system_healthy = check_system_health()
    search_graph = None
    if system_healthy:
        search_graph = initialize_langgraph_search()
    
    if system_healthy and search_graph:
        # All checks passed, render the main UI
        # 主界面标签页
        tab1, tab2, tab3, tab4 = st.tabs([
            "🔍 智能搜索", 
            "📊 搜索结果", 
            "📈 搜索历史",
            "⚡ 性能监控"
        ])
        
        with tab1:
            intelligent_search_interface(search_graph)
        
        with tab2:
            search_results_interface()
        
        with tab3:
            search_history_interface()
            
        with tab4:
            performance_monitoring_interface()
    else:
        # Initialization failed, show error guidance
        st.error("❌ 系统初始化失败")
        
        if not system_healthy:
            st.warning("⚠️ 系统健康检查未通过，请检查LangGraph模块配置")
        elif not search_graph:
            st.warning("⚠️ LangGraph搜索系统初始化失败，请检查模块安装")
            
        st.info("""
        💡 **解决方案**:
        1. 确保所有依赖模块已正确安装
        2. 检查 `.env` 文件中的API密钥配置
        3. 重启应用程序
        4. 如果问题持续，请查看终端中的详细错误信息
        """)

def intelligent_search_interface(search_graph):
    """智能搜索界面"""
    st.markdown('<h2 class="section-header">💬 描述您的搜索需求</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # 搜索示例
        st.markdown("### 🎯 搜索示例")
        examples = [
            "找北京的新能源汽车公司",
            "搜索深圳的人工智能初创公司",
            "找华为的销售经理联系方式",
            "找做太阳能发电的科技公司的技术总监",
            "搜索上海金融科技公司及其CEO信息"
        ]
        
        selected_example = st.selectbox(
            "选择示例或自定义搜索",
            [""] + examples
        )
        
        # 需求输入
        # 检查是否有建议的查询
        suggested_query = st.session_state.get("suggested_query", "")
        default_value = suggested_query if suggested_query else (selected_example if selected_example else "")
        
        user_query = st.text_area(
            "🎯 搜索需求",
            value=default_value,
            placeholder="请描述您要搜索的公司或人员信息...\n例如：找北京的新能源汽车公司\n或：搜索华为的销售总监联系方式",
            height=120,
            help="支持中英文搜索，可以搜索公司、员工或两者结合"
        )
        
        # 清除建议查询
        if suggested_query:
            st.session_state.suggested_query = ""
        
        # 智能搜索建议
        if user_query and len(user_query) > 10:
            with st.expander("💡 智能搜索建议", expanded=False):
                display_search_suggestions(user_query)
    
    with col2:
        # 搜索控制面板
        st.markdown("### ⚙️ 搜索设置")
        
        # 初始化搜索状态
        if 'langgraph_search_in_progress' not in st.session_state:
            st.session_state.langgraph_search_in_progress = False
        
        if 'langgraph_search_results' not in st.session_state:
            st.session_state.langgraph_search_results = None
        
        # AI评估设置
        ai_evaluation_enabled = st.checkbox("启用AI评估", value=True, help="使用AI对搜索结果进行智能评分和筛选")
        
        # 高级设置
        with st.expander("🔧 高级设置"):
            max_companies = st.slider("最大公司数", 10, 100, 50)
            max_employees = st.slider("最大员工数", 5, 50, 30)
            min_confidence = st.slider("意图识别最低置信度", 0.0, 1.0, 0.3, 0.1)
        
        # 搜索按钮
        if user_query and not st.session_state.langgraph_search_in_progress:
            if st.button("🚀 开始智能搜索", type="primary", use_container_width=True):
                # 立即设置搜索状态以更新UI
                st.session_state.langgraph_search_in_progress = True
                # 保存搜索参数用于后续执行
                st.session_state.pending_search = {
                    'user_query': user_query,
                    'ai_evaluation_enabled': ai_evaluation_enabled,
                    'max_companies': max_companies,
                    'max_employees': max_employees
                }
                st.rerun()  # 强制页面立即更新按钮状态
        
        elif st.session_state.langgraph_search_in_progress:
            # 显示动态搜索状态
            current_state = st.session_state.get('langgraph_current_state', {})
            current_node = current_state.get('current_node', 'initializing')
            workflow_path = current_state.get('workflow_path', [])
            
            # 状态指示器
            status_text = get_search_status_text(current_node, workflow_path)
            st.warning(f"🔄 {status_text}")
            
            # 显示进度条（如果有工作流路径）
            if workflow_path:
                progress_value = len(workflow_path) / 10  # 假设10步为完成
                st.progress(min(progress_value, 1.0))
                st.caption(f"工作流步骤: {' → '.join(workflow_path[-3:])}")  # 显示最后3步
            
            if st.button("⏹️ 停止搜索", use_container_width=True):
                st.session_state.langgraph_search_in_progress = False
                if 'pending_search' in st.session_state:
                    del st.session_state.pending_search
                st.success("搜索已停止")
                st.rerun()
        
        else:
            st.info("请先输入搜索需求")
    
    # 执行pending search（在UI更新后）
    if st.session_state.get('pending_search') and st.session_state.langgraph_search_in_progress:
        pending_params = st.session_state.pending_search
        # 清除pending状态
        del st.session_state.pending_search
        # 执行搜索
        execute_langgraph_search(
            search_graph,
            pending_params['user_query'],
            ai_evaluation_enabled=pending_params['ai_evaluation_enabled'],
            max_companies=pending_params['max_companies'],
            max_employees=pending_params['max_employees']
        )
    
    # 实时进度显示和自动刷新
    if st.session_state.langgraph_search_in_progress:
        st.markdown("---")
        
        # 添加自动刷新机制
        import time
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = time.time()
        
        # 每2秒自动刷新一次
        current_time = time.time()
        if current_time - st.session_state.last_refresh > 2:
            st.session_state.last_refresh = current_time
            st.rerun()
        
        with st.container():
            st.markdown('<div class="progress-container">', unsafe_allow_html=True)
            
            # 显示当前状态
            current_state = st.session_state.get('langgraph_current_state', {})
            if current_state:
                display_workflow_progress(current_state)
            else:
                st.info("🚀 搜索正在后台运行...")
                st.caption("正在初始化搜索引擎...")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 添加刷新按钮
        if st.button("🔄 刷新状态", key="refresh_status"):
            st.rerun()

def get_search_status_text(current_node: str, workflow_path: list) -> str:
    """获取友好的搜索状态文本"""
    status_map = {
        'initializing': '正在初始化搜索工作流...',
        'intent_recognition': '正在分析搜索意图...',
        'company_search': '正在搜索公司信息...',
        'employee_search': '正在搜索员工信息...',
        'ai_evaluation': '正在进行AI智能评估...',
        'output_integration': '正在整理搜索结果...',
        'clarification': '正在澄清搜索意图...'
    }
    
    # 根据工作流路径判断进度
    if not workflow_path:
        return '正在启动智能搜索...'
    
    latest_step = workflow_path[-1] if workflow_path else ''
    
    # 特殊处理一些状态
    if 'company_search' in latest_step:
        return '正在搜索目标公司...'
    elif 'employee_search' in latest_step:
        return '正在搜索关键员工...'
    elif 'ai_evaluation' in latest_step:
        return 'AI正在评估搜索结果...'
    elif 'output_integration' in latest_step:
        return '正在生成搜索报告...'
    elif 'completed' in latest_step:
        return '搜索即将完成...'
    
    # 使用默认映射
    return status_map.get(current_node, f'正在执行: {current_node}')

def execute_langgraph_search(search_graph, user_query: str, **kwargs):
    """执行LangGraph智能搜索 - 增强错误处理版本"""
    # 注意：搜索状态已在调用前设置
    st.session_state.langgraph_current_state = {}
    
    # 创建进度显示容器
    progress_placeholder = st.empty()
    
    try:
        with progress_placeholder.container():
            st.info("🚀 正在启动LangGraph智能搜索工作流...")
            
            # 执行搜索 - 在这里我们可以考虑添加进度回调
            with st.spinner('正在执行智能搜索...'):
                result = search_graph.execute_search(user_query, **kwargs)
                
                # 尝试获取最终状态用于UI显示
                if result and result.get('success') and 'result' in result:
                    final_state = result['result']
                    st.session_state.langgraph_current_state = final_state
            
            # 保存结果到历史记录
            if 'langgraph_search_history' not in st.session_state:
                st.session_state.langgraph_search_history = []
            
            history_record = {
                'timestamp': datetime.now().isoformat(),
                'query': user_query,
                'result': result,
                'success': False
            }
            
            # 保存结果
            st.session_state.langgraph_search_results = result
            st.session_state.langgraph_search_in_progress = False
            
            if result and result.get('success'):
                state = result.get('result', {})
                
                # 验证状态完整性 - 但不要完全阻止结果保存
                validation_warnings = []
                
                if not state:
                    validation_warnings.append("搜索结果状态为空")
                else:
                    search_results = state.get('search_results', {})
                    if not isinstance(search_results, dict):
                        validation_warnings.append("搜索结果格式不正确")
                    
                    # 检查输出集成错误
                    if 'output_integration_error' in state:
                        validation_warnings.append(f"输出集成错误: {state['output_integration_error']}")
                
                # 如果有验证警告，显示但继续处理
                if validation_warnings:
                    for warning in validation_warnings:
                        progress_placeholder.warning(f"⚠️ {warning}")
                    st.warning("⚠️ 检测到数据问题，但仍会尝试显示结果")
                    
                    # 确保至少保存了基本的搜索结果供调试
                    if not state:
                        # 创建最小状态结构
                        state = {"search_results": {"companies": [], "employees": [], "qualified_companies_count": 0, "qualified_employees_count": 0}}
                        
                # 继续处理，不要返回
                search_results = state.get('search_results', {})
                
                companies_count = len(search_results.get('companies', []))
                employees_count = len(search_results.get('employees', []))
                qualified_companies_count = search_results.get('qualified_companies_count', 0)
                
                # 检查AI评估状态
                ai_evaluation_completed = state.get('ai_evaluation_completed', False)
                ai_evaluation_enabled = state.get('ai_evaluation_enabled', False)
                
                if ai_evaluation_enabled and not ai_evaluation_completed:
                    # AI评估启用但未完成 - 可能遇到了问题
                    progress_placeholder.warning(f"⚠️ 搜索完成！找到 {companies_count} 家公司，{employees_count} 名员工，但AI评估未完成")
                    st.warning("AI智能评估可能遇到问题，显示所有搜索结果供您参考")
                elif ai_evaluation_enabled and ai_evaluation_completed:
                    # AI评估正常完成
                    progress_placeholder.success(f"✅ 搜索完成！找到 {companies_count} 家公司，{employees_count} 名员工，AI筛选出 {qualified_companies_count} 家合格公司")
                    st.balloons()
                else:
                    # AI评估未启用
                    progress_placeholder.success(f"✅ 搜索完成！找到 {companies_count} 家公司，{employees_count} 名员工")
                    st.balloons()
                
                # 检查AI评估是否存在问题
                companies = search_results.get('companies', [])
                if companies and ai_evaluation_enabled:
                    none_scores = sum(1 for c in companies if c.get('ai_score') is None)
                    if none_scores > 0:
                        st.warning(f"⚠️ 发现 {none_scores} 家公司的AI评分为空，可能是AI评估过程中遇到了问题。建议检查API配置或联系技术支持。")
                        
                        # 提供诊断信息
                        with st.expander("🔧 AI评估诊断信息"):
                            st.write(f"- AI评估启用: {ai_evaluation_enabled}")
                            st.write(f"- AI评估完成: {ai_evaluation_completed}")
                            st.write(f"- 总公司数: {companies_count}")
                            st.write(f"- 有AI评分的公司: {companies_count - none_scores}")
                            st.write(f"- AI评分为空的公司: {none_scores}")
                            st.write(f"- 合格公司数: {qualified_companies_count}")
                            
                            # 显示工作流路径用于诊断
                            workflow_path = state.get('workflow_path', [])
                            if workflow_path:
                                st.write(f"- 工作流路径: {' → '.join(workflow_path)}")
                            
                            # 显示错误和警告
                            errors = state.get('errors', [])
                            warnings = state.get('warnings', [])
                            if errors:
                                st.write(f"- 错误: {errors}")
                            if warnings:
                                st.write(f"- 警告: {warnings}")
                
                # 显示最终工作流状态
                st.session_state.langgraph_current_state = state
                
                # 标记为成功
                history_record['success'] = True
                
                # 自动切换到结果标签页提示
                st.info("💡 点击上方 '📊 搜索结果' 标签页查看详细结果")
                
            else:
                # 搜索失败的情况 - 但先检查是否有部分结果
                error_msg = result.get('error', '未知错误') if result else '无响应结果'
                
                # 检查是否有部分搜索结果（可能搜索成功但AI评估失败）
                if result and 'result' in result:
                    partial_state = result.get('result', {})
                    partial_search_results = partial_state.get('search_results', {})
                    partial_companies = partial_search_results.get('companies', [])
                    
                    if partial_companies:
                        # 有搜索结果但标记为失败 - 可能是AI评估问题
                        companies_count = len(partial_companies)
                        progress_placeholder.warning(f"⚠️ 搜索部分成功！找到 {companies_count} 家公司，但处理过程中遇到问题")
                        st.warning(f"搜索找到了结果，但后续处理失败：{error_msg}")
                        
                        # 构造一个可用的结果结构供结果页面显示
                        fixed_result = {
                            'success': True,  # 标记为成功以便结果页面显示
                            'result': partial_state,
                            'error_context': error_msg  # 保存错误信息供调试
                        }
                        st.session_state.langgraph_search_results = fixed_result
                        st.session_state.langgraph_current_state = partial_state
                        history_record['success'] = True  # 标记为成功因为有结果
                        
                        with st.expander("🔧 问题诊断"):
                            st.write(f"错误信息: {error_msg}")
                            st.write(f"找到公司数: {companies_count}")
                            st.write("建议：可以在结果页面查看已找到的公司信息")
                            
                        st.info("💡 点击上方 '📊 搜索结果' 标签页查看已找到的结果")
                    else:
                        # 完全没有结果的失败 - 但仍然保存错误信息供调试
                        error_result = {
                            'success': False,
                            'error': error_msg,
                            'result': {}
                        }
                        st.session_state.langgraph_search_results = error_result
                        progress_placeholder.error(f"❌ 搜索失败: {error_msg}")
                        handle_search_error("search_failed", error_msg, progress_placeholder)
                else:
                    # 完全没有结果的失败 - 保存错误信息
                    error_result = {
                        'success': False,
                        'error': error_msg,
                        'result': {}
                    }
                    st.session_state.langgraph_search_results = error_result
                    progress_placeholder.error(f"❌ 搜索失败: {error_msg}")
                    handle_search_error("search_failed", error_msg, progress_placeholder)
            
            # 添加到历史记录
            st.session_state.langgraph_search_history.append(history_record)
    
    except Exception as e:
        st.session_state.langgraph_search_in_progress = False
        error_str = str(e)
        progress_placeholder.error(f"❌ 搜索异常: {error_str}")
        
        # 保存异常结果供调试
        exception_result = {
            'success': False,
            'error': f"搜索异常: {error_str}",
            'result': {},
            'exception': True
        }
        st.session_state.langgraph_search_results = exception_result
        
        # 添加异常到历史记录
        if 'langgraph_search_history' not in st.session_state:
            st.session_state.langgraph_search_history = []
        
        st.session_state.langgraph_search_history.append({
            'timestamp': datetime.now().isoformat(),
            'query': user_query,
            'result': exception_result,
            'success': False
        })
        
        handle_search_error("exception", error_str, progress_placeholder)

def search_results_interface():
    """搜索结果界面"""
    # 调试信息
    if 'langgraph_search_results' not in st.session_state:
        st.info("❌ 搜索结果状态不存在。请先在'🔍 智能搜索'标签页执行搜索。")
        return
    
    if not st.session_state.langgraph_search_results:
        st.info("❌ 搜索结果为空。请先在'🔍 智能搜索'标签页执行搜索。")
        return
    
    # 显示调试信息（可选，帮助定位问题）
    with st.expander("🔍 调试信息", expanded=False):
        st.write("搜索结果状态存在:", 'langgraph_search_results' in st.session_state)
        st.write("结果数据类型:", type(st.session_state.langgraph_search_results))
        if st.session_state.langgraph_search_results:
            result = st.session_state.langgraph_search_results
            st.write("结果成功标志:", result.get('success'))
            if result.get('success') and 'result' in result:
                state = result['result']
                search_results = state.get('search_results', {})
                st.write("公司数量:", len(search_results.get('companies', [])))
                st.write("员工数量:", len(search_results.get('employees', [])))
                st.write("合格公司数量:", search_results.get('qualified_companies_count', 0))
                st.write("合格员工数量:", search_results.get('qualified_employees_count', 0))
    
    st.markdown('<h2 class="section-header">📊 LangGraph搜索结果</h2>', unsafe_allow_html=True)
    
    display_search_results(st.session_state.langgraph_search_results)

def search_history_interface():
    """搜索历史界面"""
    st.markdown('<h2 class="section-header">📈 搜索历史</h2>', unsafe_allow_html=True)
    
    # 初始化历史记录
    if 'langgraph_search_history' not in st.session_state:
        st.session_state.langgraph_search_history = []
    
    history = st.session_state.langgraph_search_history
    
    if history:
        # 历史统计
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("总搜索次数", len(history))
        
        with col2:
            success_count = sum(1 for h in history if h.get('success'))
            st.metric("成功搜索", success_count)
        
        with col3:
            success_rate = success_count / len(history) if history else 0
            st.metric("成功率", f"{success_rate:.1%}")
        
        # 历史记录表格
        st.markdown("### 📋 搜索记录")
        
        history_data = []
        for i, record in enumerate(reversed(history), 1):  # 最新的在前
            result = record.get('result', {})
            state = result.get('result', {}) if result else {}
            
            history_data.append({
                "序号": i,
                "时间": record.get('timestamp', 'Unknown'),
                "查询": record.get('query', 'N/A')[:50] + "..." if len(record.get('query', '')) > 50 else record.get('query', 'N/A'),
                "意图": state.get('detected_intent', 'unknown'),
                "状态": "✅ 成功" if record.get('success') else "❌ 失败",
                "公司数": len(state.get('search_results', {}).get('companies', [])),
                "员工数": len(state.get('search_results', {}).get('employees', []))
            })
        
        if history_data:
            st.dataframe(history_data, use_container_width=True)
        
        # 清除历史按钮
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ 清除搜索历史"):
                st.session_state.langgraph_search_history = []
                st.success("搜索历史已清除")
                st.rerun()
        
        with col2:
            if st.button("📥 导出历史记录"):
                export_search_history(history)
    
    else:
        st.info("暂无搜索历史记录")

def export_search_history(history):
    """导出搜索历史"""
    try:
        export_data = []
        for record in history:
            result = record.get('result', {})
            state = result.get('result', {}) if result else {}
            
            export_data.append({
                '时间': record.get('timestamp', ''),
                '查询': record.get('query', ''),
                '意图': state.get('detected_intent', ''),
                '置信度': state.get('intent_confidence', 0),
                '状态': '成功' if record.get('success') else '失败',
                '公司数量': len(state.get('search_results', {}).get('companies', [])),
                '员工数量': len(state.get('search_results', {}).get('employees', [])),
                '会话ID': state.get('session_id', '')
            })
        
        df = pd.DataFrame(export_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"langgraph_search_history_{timestamp}.csv"
        
        csv = df.to_csv(index=False, encoding='utf-8')
        st.download_button(
            label="📥 下载历史记录CSV",
            data=csv,
            file_name=filename,
            mime='text/csv'
        )
        
        st.success(f"✅ 搜索历史已准备下载: {len(history)} 条记录")
        
    except Exception as e:
        st.error(f"导出失败: {str(e)}")

def display_errors_and_warnings(state: Dict[str, Any]):
    """显示错误和警告信息的增强版本"""
    errors = state.get("errors", [])
    warnings = state.get("warnings", [])
    error_handling_data = state.get("error_handling_data", {})
    
    # 显示错误信息
    if errors:
        st.markdown("### ❌ 错误信息")
        
        # 错误摘要
        if error_handling_data:
            analysis = error_handling_data.get("analysis", {})
            overall_status = analysis.get("overall_status", "unknown")
            
            status_colors = {
                "critical": "🔴 严重",
                "degraded": "🟠 降级",  
                "warning": "🟡 警告",
                "healthy": "🟢 正常"
            }
            
            st.info(f"系统状态: {status_colors.get(overall_status, overall_status)}")
        
        # 错误详情
        for error in errors:
            error_type = error.get('type', '未知错误')
            error_message = error.get('message', '')
            error_node = error.get('node', '')
            error_time = error.get('timestamp', '')
            
            with st.expander(f"❌ {error_type}", expanded=True):
                st.error(f"**错误消息**: {error_message}")
                if error_node:
                    st.write(f"**发生节点**: {error_node}")
                if error_time:
                    st.write(f"**发生时间**: {error_time}")
    
    # 显示警告信息
    if warnings:
        st.markdown("### ⚠️ 警告信息")
        
        for warning in warnings:
            warning_type = warning.get('type', '一般警告')
            warning_message = warning.get('message', '')
            warning_node = warning.get('node', '')
            
            with st.expander(f"⚠️ {warning_type}"):
                st.warning(f"**警告消息**: {warning_message}")
                if warning_node:
                    st.write(f"**发生节点**: {warning_node}")
    
    # 显示恢复建议
    if error_handling_data:
        recovery_suggestions = error_handling_data.get("recovery_suggestions", [])
        if recovery_suggestions:
            st.markdown("### 🛠️ 恢复建议")
            
            for suggestion in recovery_suggestions:
                priority = suggestion.get("priority", 5)
                severity = suggestion.get("severity", "medium")
                
                priority_color = "🔴" if priority == 1 else "🟠" if priority <= 2 else "🟡"
                
                with st.expander(f"{priority_color} {suggestion.get('error_type', '通用建议')}"):
                    if "recovery_steps" in suggestion:
                        st.write("**推荐步骤:**")
                        for i, step in enumerate(suggestion["recovery_steps"], 1):
                            st.write(f"{i}. {step}")
                    
                    if "actions" in suggestion:
                        st.write("**建议操作:**")
                        for action in suggestion["actions"]:
                            st.write(f"• {action}")
        
        # 自动恢复结果
        auto_recovery = error_handling_data.get("auto_recovery", {})
        if auto_recovery.get("attempted"):
            st.markdown("### 🤖 自动恢复状态")
            
            successful = auto_recovery.get("successful_recoveries", 0)
            failed = auto_recovery.get("failed_recoveries", 0)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("成功恢复", successful)
            with col2:
                st.metric("失败恢复", failed)
            
            if auto_recovery.get("recovery_actions"):
                with st.expander("恢复操作详情"):
                    for action in auto_recovery["recovery_actions"]:
                        status = "✅" if "successful" in action.get("action", "") else "❌"
                        st.write(f"{status} {action.get('error_type', '')}: {action.get('action', '')}")
        
        # 故障排除指南
        troubleshooting_guide = error_handling_data.get("troubleshooting_guide", {})
        if troubleshooting_guide:
            with st.expander("🔍 故障排除指南"):
                
                # 快速修复
                quick_fixes = troubleshooting_guide.get("quick_fixes", [])
                if quick_fixes:
                    st.write("**快速修复:**")
                    for fix in quick_fixes:
                        st.write(f"• **{fix.get('issue', '')}**: {fix.get('solution', '')}")
                
                # 诊断步骤
                diagnostic_steps = troubleshooting_guide.get("diagnostic_steps", [])
                if diagnostic_steps:
                    st.write("**诊断步骤:**")
                    for step in diagnostic_steps:
                        st.write(f"**{step.get('step', '')}. {step.get('title', '')}**")
                        for action in step.get("actions", []):
                            st.write(f"  - {action}")
                
                # 预防建议
                prevention_tips = troubleshooting_guide.get("prevention_tips", [])
                if prevention_tips:
                    st.write("**预防建议:**")
                    for tip in prevention_tips:
                        st.write(f"• {tip}")

def display_clarification_suggestions(state: Dict[str, Any]):
    """显示澄清建议和搜索优化建议"""
    clarification_data = state.get("clarification_data", {})
    
    if not clarification_data:
        return
    
    st.markdown("### 💡 搜索优化建议")
    
    # 澄清需求分析
    needs = clarification_data.get("needs", {})
    if any(needs.values()):
        st.markdown("#### 🎯 需求澄清")
        
        needs_descriptions = {
            "intent_unclear": "🤔 搜索意图不够明确",
            "parameters_missing": "📝 搜索参数缺失", 
            "scope_ambiguous": "🌍 搜索范围模糊",
            "criteria_undefined": "📊 评估标准未定义"
        }
        
        active_needs = [needs_descriptions[key] for key, value in needs.items() if value]
        for need in active_needs:
            st.write(f"• {need}")
    
    # 澄清建议
    suggestions = clarification_data.get("suggestions", [])
    if suggestions:
        st.markdown("#### 💬 澄清建议")
        
        for suggestion in suggestions:
            suggestion_type = suggestion.get("type", "")
            title = suggestion.get("title", "")
            
            with st.expander(f"💡 {title}"):
                questions = suggestion.get("questions", [])
                if questions:
                    st.write("**建议问题:**")
                    for question in questions:
                        st.write(f"• {question}")
                
                # 选项
                options = suggestion.get("options", [])
                if options:
                    st.write("**可选答案:**")
                    for option in options:
                        st.write(f"• {option.get('label', '')}")
                
                # 示例
                examples = suggestion.get("examples", {})
                if examples:
                    st.write("**参考示例:**")
                    for category, example_list in examples.items():
                        st.write(f"**{category}**: {', '.join(example_list)}")
                
                # 标准模板
                criteria_templates = suggestion.get("criteria_templates", {})
                if criteria_templates:
                    st.write("**评估标准模板:**")
                    for category, template_list in criteria_templates.items():
                        st.write(f"**{category}**: {', '.join(template_list)}")
    
    # 搜索优化建议
    optimization_suggestions = clarification_data.get("optimization_suggestions", [])
    if optimization_suggestions:
        st.markdown("#### 🚀 搜索优化")
        
        for opt_suggestion in optimization_suggestions:
            title = opt_suggestion.get("title", "")
            description = opt_suggestion.get("description", "")
            example = opt_suggestion.get("example", "")
            
            with st.expander(f"🔧 {title}"):
                if description:
                    st.write(description)
                if example:
                    st.code(example)
                
                steps = opt_suggestion.get("steps", [])
                if steps:
                    st.write("**操作步骤:**")
                    for step in steps:
                        st.write(f"• {step}")
    
    # 查询重写建议
    query_rewrites = clarification_data.get("query_rewrites", [])
    if query_rewrites:
        st.markdown("#### ✏️ 查询优化建议")
        
        for rewrite in query_rewrites:
            rewrite_type = rewrite.get("type", "")
            query = rewrite.get("query", "")
            description = rewrite.get("description", "")
            
            with st.expander(f"📝 {rewrite_type} - {description}"):
                st.code(query)
                
                # 提供快速应用按钮
                if st.button(f"应用此查询", key=f"apply_{rewrite_type}"):
                    st.session_state.suggested_query = query
                    st.success("查询建议已应用，请返回搜索页面使用！")
    
    # 置信度问题
    confidence_issues = clarification_data.get("confidence_issues", [])
    if confidence_issues:
        st.markdown("#### ⚡ 置信度问题")
        
        for issue in confidence_issues:
            severity = issue.get("severity", "medium")
            severity_icons = {"high": "🔴", "medium": "🟠", "low": "🟡"}
            icon = severity_icons.get(severity, "🟡")
            
            with st.expander(f"{icon} {issue.get('issue', '')}"):
                st.write(issue.get("description", ""))
                
                suggestions = issue.get("suggestions", [])
                if suggestions:
                    st.write("**改进建议:**")
                    for suggestion in suggestions:
                        st.write(f"• {suggestion}")

def performance_monitoring_interface():
    """性能监控界面"""
    st.markdown('<h2 class="section-header">⚡ 系统性能监控</h2>', unsafe_allow_html=True)
    
    try:
        # 导入性能管理器
        from langgraph_search.utils.performance_manager import get_performance_manager
        
        performance_manager = get_performance_manager()
        
        # 获取性能报告
        performance_report = performance_manager.get_performance_report()
        
        # 实时资源监控
        st.markdown("### 📊 实时系统状态")
        
        resource_metrics = performance_manager.resource_monitor.get_current_metrics()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cpu_percent = resource_metrics.get("cpu_percent", 0)
            cpu_color = "🟢" if cpu_percent < 50 else "🟡" if cpu_percent < 80 else "🔴"
            st.metric("CPU使用率", f"{cpu_percent:.1f}%", delta=cpu_color)
        
        with col2:
            memory_percent = resource_metrics.get("memory_percent", 0)
            memory_color = "🟢" if memory_percent < 60 else "🟡" if memory_percent < 85 else "🔴"
            st.metric("内存使用率", f"{memory_percent:.1f}%", delta=memory_color)
        
        with col3:
            disk_percent = resource_metrics.get("disk_percent", 0)
            disk_color = "🟢" if disk_percent < 70 else "🟡" if disk_percent < 90 else "🔴"
            st.metric("磁盘使用率", f"{disk_percent:.1f}%", delta=disk_color)
        
        with col4:
            memory_used = resource_metrics.get("memory_used_mb", 0)
            st.metric("内存用量", f"{memory_used:.0f} MB")
        
        # 缓存性能
        st.markdown("### 💾 缓存性能")
        
        cache_stats = performance_report.get("cache", {})
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            hit_rate = cache_stats.get("hit_rate", 0)
            hit_rate_color = "🟢" if hit_rate > 0.7 else "🟡" if hit_rate > 0.3 else "🔴"
            st.metric("缓存命中率", f"{hit_rate:.1%}", delta=hit_rate_color)
        
        with col2:
            cache_entries = cache_stats.get("entries", 0)
            st.metric("缓存条目", cache_entries)
        
        with col3:
            cache_size = cache_stats.get("total_size_mb", 0)
            max_size = cache_stats.get("max_size_mb", 100)
            st.metric("缓存使用", f"{cache_size:.1f}/{max_size:.0f} MB")
        
        # 缓存详情
        with st.expander("📈 缓存详细统计"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**缓存命中次数**:", cache_stats.get("hits", 0))
                st.write("**缓存未命中次数**:", cache_stats.get("misses", 0))
            
            with col2:
                utilization = (cache_size / max_size * 100) if max_size > 0 else 0
                st.write("**缓存利用率**:", f"{utilization:.1f}%")
                st.write("**最大容量**:", f"{max_size:.0f} MB")
        
        # 执行性能
        st.markdown("### 🚀 执行性能")
        
        execution_stats = performance_report.get("execution", {})
        
        if "total_executions" in execution_stats:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("总执行次数", execution_stats.get("total_executions", 0))
            
            with col2:
                success_rate = execution_stats.get("success_rate", 0)
                success_color = "🟢" if success_rate > 0.9 else "🟡" if success_rate > 0.7 else "🔴"
                st.metric("成功率", f"{success_rate:.1%}", delta=success_color)
            
            with col3:
                avg_time = execution_stats.get("avg_execution_time", 0)
                time_color = "🟢" if avg_time < 10 else "🟡" if avg_time < 30 else "🔴"
                st.metric("平均执行时间", f"{avg_time:.1f}s", delta=time_color)
            
            with col4:
                api_calls = execution_stats.get("total_api_calls", 0)
                st.metric("API调用次数", api_calls)
            
            # 节点性能分析
            nodes_performance = execution_stats.get("nodes_performance", {})
            if nodes_performance:
                st.markdown("#### 🔧 节点性能分析")
                
                node_data = []
                for node_name, stats in nodes_performance.items():
                    node_data.append({
                        "节点名称": node_name,
                        "平均执行时间(s)": f"{stats['avg_time']:.2f}",
                        "执行次数": stats['executions']
                    })
                
                if node_data:
                    st.dataframe(node_data, use_container_width=True)
        
        # 性能历史趋势
        if performance_manager.performance_history:
            st.markdown("### 📈 性能历史趋势")
            
            # 提取最近50次执行的数据
            recent_history = performance_manager.performance_history[-50:]
            
            import pandas as pd
            import plotly.express as px
            import plotly.graph_objects as go
            
            # 创建数据框
            history_data = []
            for metrics in recent_history:
                history_data.append({
                    "时间": metrics.timestamp,
                    "执行时间": metrics.execution_time,
                    "内存使用": metrics.memory_usage,
                    "CPU使用": metrics.cpu_usage,
                    "节点": metrics.node_name,
                    "状态": "成功" if metrics.success else "失败"
                })
            
            if history_data:
                df = pd.DataFrame(history_data)
                
                # 执行时间趋势图
                fig = px.line(df, x='时间', y='执行时间', 
                             title='执行时间趋势', color='节点')
                st.plotly_chart(fig, use_container_width=True)
                
                # 资源使用分布
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.box(df, x='节点', y='执行时间', 
                               title='节点执行时间分布')
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = px.pie(df, names='状态', title='执行状态分布')
                    st.plotly_chart(fig, use_container_width=True)
        
        # 优化建议
        st.markdown("### 💡 性能优化建议")
        
        optimization_suggestions = performance_report.get("optimization_suggestions", [])
        
        if optimization_suggestions:
            for suggestion in optimization_suggestions:
                priority = suggestion.get("priority", "medium")
                priority_colors = {
                    "high": "🔴",
                    "medium": "🟠", 
                    "low": "🟡"
                }
                priority_color = priority_colors.get(priority, "🟡")
                
                with st.expander(f"{priority_color} {suggestion.get('title', '')}", expanded=priority=="high"):
                    st.write(suggestion.get("description", ""))
                    
                    actions = suggestion.get("actions", [])
                    if actions:
                        st.write("**建议操作:**")
                        for action in actions:
                            st.write(f"• {action}")
        else:
            st.success("🎉 系统运行良好，暂无优化建议")
        
        # 性能控制操作
        st.markdown("### 🎛️ 性能控制")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🗑️ 清空缓存"):
                performance_manager.cache.clear()
                st.success("缓存已清空")
                st.rerun()
        
        with col2:
            if st.button("📊 刷新监控"):
                st.rerun()
        
        with col3:
            # 导出性能报告
            report_json = json.dumps(performance_report, ensure_ascii=False, indent=2)
            st.download_button(
                label="📥 导出性能报告",
                data=report_json,
                file_name=f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        # 自动刷新选项
        with st.expander("⚙️ 监控设置"):
            auto_refresh = st.checkbox("启用自动刷新 (30秒)", value=False)
            
            if auto_refresh:
                time.sleep(30)
                st.rerun()
            
            # 性能阈值设置
            st.subheader("性能阈值设置")
            
            new_cpu_threshold = st.slider("CPU使用率警告阈值 (%)", 0, 100, 80)
            new_memory_threshold = st.slider("内存使用率警告阈值 (%)", 0, 100, 85)
            
            if st.button("应用阈值设置"):
                performance_manager.resource_monitor.alert_thresholds.update({
                    "cpu_percent": float(new_cpu_threshold),
                    "memory_percent": float(new_memory_threshold)
                })
                st.success("阈值设置已应用")
        
    except ImportError:
        st.error("❌ 性能管理模块未安装或配置错误")
        st.info("💡 请确保 psutil 包已安装: pip install psutil")
    
    except Exception as e:
        st.error(f"❌ 性能监控初始化失败: {str(e)}")
        st.info("💡 请检查性能管理器配置")

def display_search_suggestions(user_query: str):
    """显示智能搜索建议"""
    
    # 查询分析
    query_analysis = analyze_user_query(user_query)
    
    # 意图预测
    predicted_intent = predict_search_intent(user_query)
    intent_colors = {
        "company": "🏢",
        "employee": "👥", 
        "composite": "🔄",
        "unknown": "❓"
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**预测意图**: {intent_colors.get(predicted_intent, '❓')} {predicted_intent}")
        st.write(f"**关键词**: {', '.join(query_analysis['keywords'])}")
    
    with col2:
        st.write(f"**地区**: {query_analysis['region'] or '未指定'}")
        st.write(f"**行业**: {query_analysis['industry'] or '未指定'}")
    
    # 搜索建议
    suggestions = generate_search_suggestions(user_query, query_analysis)
    
    if suggestions:
        st.write("**优化建议**:")
        for i, suggestion in enumerate(suggestions, 1):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"{i}. {suggestion['description']}")
                
            with col2:
                if st.button(f"应用", key=f"suggestion_{i}"):
                    st.session_state.suggested_query = suggestion['query']
                    st.success("已应用建议!")
                    st.rerun()
    
    # 相关搜索推荐
    related_queries = get_related_queries(user_query)
    if related_queries:
        st.write("**相关搜索**:")
        cols = st.columns(3)
        for i, related in enumerate(related_queries):
            with cols[i % 3]:
                if st.button(f"🔍 {related}", key=f"related_{i}", use_container_width=True):
                    st.session_state.suggested_query = related
                    st.rerun()

def analyze_user_query(query: str) -> Dict[str, Any]:
    """分析用户查询"""
    import re
    
    # 地区关键词
    region_keywords = {
        '北京': '北京', '上海': '上海', '深圳': '深圳', '广州': '广州',
        '杭州': '杭州', '成都': '成都', '西安': '西安', '南京': '南京',
        '中国': 'cn', '美国': 'us', '欧洲': 'eu', '全球': 'global'
    }
    
    # 行业关键词
    industry_keywords = {
        '人工智能': 'AI', '机器学习': 'ML', '科技': 'Technology',
        '新能源': 'New Energy', '汽车': 'Automotive', '金融': 'Finance',
        '医疗': 'Healthcare', '教育': 'Education', '电商': 'E-commerce',
        '制造': 'Manufacturing', '房地产': 'Real Estate'
    }
    
    # 职位关键词
    position_keywords = [
        'CEO', 'CTO', 'CFO', '总经理', '销售经理', '技术总监',
        '市场总监', '产品经理', '研发工程师', '商务经理'
    ]
    
    analysis = {
        'keywords': [],
        'region': None,
        'industry': None,
        'positions': [],
        'entities': []
    }
    
    # 提取关键词
    words = re.findall(r'\w+', query)
    analysis['keywords'] = [word for word in words if len(word) > 1]
    
    # 识别地区
    for region_key, region_value in region_keywords.items():
        if region_key in query:
            analysis['region'] = region_value
            break
    
    # 识别行业
    for industry_key, industry_value in industry_keywords.items():
        if industry_key in query:
            analysis['industry'] = industry_value
            break
    
    # 识别职位
    for position in position_keywords:
        if position in query:
            analysis['positions'].append(position)
    
    return analysis

def predict_search_intent(query: str) -> str:
    """预测搜索意图"""
    query_lower = query.lower()
    
    # 公司相关关键词
    company_keywords = ['公司', '企业', '厂商', '制造商', 'company', 'corporation']
    
    # 员工相关关键词
    employee_keywords = ['CEO', 'CTO', '经理', '总监', '联系方式', '人员', 'contact']
    
    # 复合关键词
    composite_keywords = ['的', '联系方式', 'contact information']
    
    company_score = sum(1 for kw in company_keywords if kw in query_lower)
    employee_score = sum(1 for kw in employee_keywords if kw in query_lower)
    composite_score = sum(1 for kw in composite_keywords if kw in query_lower)
    
    if employee_score > 0 and company_score > 0:
        return "composite"
    elif employee_score > company_score:
        return "employee"
    elif company_score > 0:
        return "company"
    else:
        return "unknown"

def generate_search_suggestions(query: str, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
    """生成搜索建议"""
    suggestions = []
    
    # 基于分析结果生成建议
    if not analysis['region']:
        suggestions.append({
            'description': '添加地区限制以获得更精确的结果',
            'query': f"{query} 北京"
        })
    
    if not analysis['industry']:
        suggestions.append({
            'description': '指定行业类型以缩小搜索范围',
            'query': f"{query} 科技公司"
        })
    
    # 结构化建议
    if '的' not in query and len(analysis['keywords']) > 2:
        suggestions.append({
            'description': '使用结构化描述提高搜索准确度',
            'query': f"找{analysis['region'] or ''}的{analysis['industry'] or ''}公司"
        })
    
    # 具体化建议
    if len(query.split()) < 4:
        suggestions.append({
            'description': '添加更多描述信息以提高匹配度',
            'query': f"{query} 大型企业 联系方式"
        })
    
    return suggestions[:3]  # 限制建议数量

def get_related_queries(query: str) -> List[str]:
    """获取相关查询推荐"""
    
    # 根据查询内容生成相关搜索
    related = []
    
    if '北京' in query:
        related.extend(['上海的同类公司', '深圳的相关企业'])
    elif '上海' in query:
        related.extend(['北京的同类公司', '杭州的相关企业'])
    
    if '人工智能' in query:
        related.extend(['机器学习公司', '大数据企业', '云计算公司'])
    elif '新能源' in query:
        related.extend(['电动汽车公司', '太阳能企业', '风能公司'])
    
    if 'CEO' in query:
        related.extend(['CTO联系方式', '销售总监', '市场总监'])
    elif '销售' in query:
        related.extend(['商务总监', '市场经理', '客户经理'])
    
    # 通用相关搜索
    if not related:
        related = [
            '相关行业领军企业',
            '同地区知名公司',
            '类似规模企业'
        ]
    
    return related[:3]

# 增强搜索历史界面
def enhanced_search_history_interface():
    """增强的搜索历史界面"""
    st.markdown('<h2 class="section-header">📈 智能搜索历史</h2>', unsafe_allow_html=True)
    
    # 初始化历史记录
    if 'langgraph_search_history' not in st.session_state:
        st.session_state.langgraph_search_history = []
    
    history = st.session_state.langgraph_search_history
    
    if history:
        # 历史统计
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("总搜索次数", len(history))
        
        with col2:
            success_count = sum(1 for h in history if h.get('success'))
            st.metric("成功搜索", success_count)
        
        with col3:
            success_rate = success_count / len(history) if history else 0
            st.metric("成功率", f"{success_rate:.1%}")
        
        with col4:
            # 计算平均结果数量
            avg_companies = sum(
                len(h.get('result', {}).get('result', {}).get('search_results', {}).get('companies', [])) 
                for h in history if h.get('success')
            ) / success_count if success_count > 0 else 0
            st.metric("平均公司数", f"{avg_companies:.1f}")
        
        # 快速操作
        st.markdown("### 🚀 快速操作")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 重新执行最近搜索"):
                if history:
                    last_query = history[-1].get('query', '')
                    st.session_state.suggested_query = last_query
                    st.success("已设置最近搜索为当前查询!")
        
        with col2:
            if st.button("⭐ 收藏成功搜索"):
                successful_searches = [h for h in history if h.get('success')]
                if successful_searches:
                    if 'favorite_searches' not in st.session_state:
                        st.session_state.favorite_searches = []
                    
                    # 收藏最近成功的搜索
                    recent_success = successful_searches[-1]
                    if recent_success not in st.session_state.favorite_searches:
                        st.session_state.favorite_searches.append(recent_success)
                        st.success("已收藏最近成功的搜索!")
        
        with col3:
            if st.button("📊 生成搜索报告"):
                generate_search_insights_report(history)
        
        # 搜索过滤和排序
        st.markdown("### 🔍 历史记录筛选")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_type = st.selectbox(
                "筛选类型",
                ["全部", "成功", "失败", "公司搜索", "员工搜索", "复合搜索"]
            )
        
        with col2:
            sort_by = st.selectbox(
                "排序方式", 
                ["时间(最新)", "时间(最旧)", "结果数量(多)", "结果数量(少)"]
            )
        
        with col3:
            time_filter = st.selectbox(
                "时间范围",
                ["全部", "今天", "本周", "本月"]
            )
        
        # 应用筛选
        filtered_history = filter_search_history(history, filter_type, sort_by, time_filter)
        
        if filtered_history:
            # 显示筛选后的历史记录
            for i, record in enumerate(filtered_history[:10], 1):  # 显示前10条
                with st.expander(f"搜索 {i}: {record.get('query', 'N/A')[:50]}...", expanded=False):
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**时间**: {record.get('timestamp', 'Unknown')}")
                        st.write(f"**状态**: {'✅ 成功' if record.get('success') else '❌ 失败'}")
                        
                        result = record.get('result', {})
                        state = result.get('result', {}) if result else {}
                        
                        if state:
                            search_results = state.get('search_results', {})
                            st.write(f"**公司数**: {len(search_results.get('companies', []))}")
                            st.write(f"**员工数**: {len(search_results.get('employees', []))}")
                            st.write(f"**意图**: {state.get('detected_intent', 'unknown')}")
                    
                    with col2:
                        if st.button(f"重新执行", key=f"rerun_{i}"):
                            st.session_state.suggested_query = record.get('query', '')
                            st.success("已应用到搜索框!")
                        
                        if st.button(f"复制查询", key=f"copy_{i}"):
                            st.code(record.get('query', ''), language=None)
        
        # 收藏的搜索
        if 'favorite_searches' in st.session_state and st.session_state.favorite_searches:
            st.markdown("### ⭐ 收藏的搜索")
            
            for i, fav in enumerate(st.session_state.favorite_searches):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"🌟 {fav.get('query', 'N/A')}")
                
                with col2:
                    if st.button("使用", key=f"fav_{i}"):
                        st.session_state.suggested_query = fav.get('query', '')
                        st.success("已应用收藏的搜索!")
    
    else:
        st.info("暂无搜索历史记录")
        st.markdown("### 💡 使用提示")
        st.write("• 执行搜索后，历史记录会自动保存")
        st.write("• 可以重新执行历史搜索")
        st.write("• 支持收藏和管理常用搜索")

def filter_search_history(history, filter_type, sort_by, time_filter):
    """筛选搜索历史"""
    from datetime import datetime, timedelta
    
    # 时间筛选
    if time_filter != "全部":
        now = datetime.now()
        if time_filter == "今天":
            cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_filter == "本周":
            cutoff = now - timedelta(days=7)
        elif time_filter == "本月":
            cutoff = now - timedelta(days=30)
        
        history = [
            h for h in history 
            if datetime.fromisoformat(h.get('timestamp', now.isoformat())) >= cutoff
        ]
    
    # 类型筛选
    if filter_type != "全部":
        if filter_type == "成功":
            history = [h for h in history if h.get('success')]
        elif filter_type == "失败":
            history = [h for h in history if not h.get('success')]
        else:
            intent_map = {
                "公司搜索": "company",
                "员工搜索": "employee", 
                "复合搜索": "composite"
            }
            target_intent = intent_map.get(filter_type)
            if target_intent:
                history = [
                    h for h in history 
                    if h.get('result', {}).get('result', {}).get('detected_intent') == target_intent
                ]
    
    # 排序
    if sort_by == "时间(最新)":
        history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    elif sort_by == "时间(最旧)":
        history.sort(key=lambda x: x.get('timestamp', ''))
    elif sort_by == "结果数量(多)":
        history.sort(
            key=lambda x: len(
                x.get('result', {}).get('result', {}).get('search_results', {}).get('companies', [])
            ),
            reverse=True
        )
    elif sort_by == "结果数量(少)":
        history.sort(
            key=lambda x: len(
                x.get('result', {}).get('result', {}).get('search_results', {}).get('companies', [])
            )
        )
    
    return history

def generate_search_insights_report(history):
    """生成搜索洞察报告"""
    if not history:
        st.warning("暂无历史数据生成报告")
        return
    
    st.markdown("### 📊 搜索洞察报告")
    
    # 成功率分析
    success_count = sum(1 for h in history if h.get('success'))
    success_rate = success_count / len(history)
    
    # 意图分析
    intent_stats = {}
    for h in history:
        if h.get('success'):
            intent = h.get('result', {}).get('result', {}).get('detected_intent', 'unknown')
            intent_stats[intent] = intent_stats.get(intent, 0) + 1
    
    # 结果数量分析
    companies_counts = []
    for h in history:
        if h.get('success'):
            companies_counts.append(
                len(h.get('result', {}).get('result', {}).get('search_results', {}).get('companies', []))
            )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 统计摘要")
        st.write(f"• 总搜索次数: {len(history)}")
        st.write(f"• 成功次数: {success_count}")
        st.write(f"• 成功率: {success_rate:.1%}")
        
        if companies_counts:
            avg_companies = sum(companies_counts) / len(companies_counts)
            st.write(f"• 平均公司数: {avg_companies:.1f}")
            st.write(f"• 最多公司数: {max(companies_counts)}")
    
    with col2:
        st.markdown("#### 🎯 意图分布")
        for intent, count in intent_stats.items():
            percentage = count / success_count * 100 if success_count > 0 else 0
            st.write(f"• {intent}: {count} ({percentage:.1f}%)")
    
    # 生成改进建议
    st.markdown("#### 💡 改进建议")
    
    if success_rate < 0.8:
        st.write("• 建议优化查询描述，提高搜索准确性")
    
    if companies_counts and max(companies_counts) > 50:
        st.write("• 考虑增加筛选条件，避免结果过多")
    
    if len(set(intent_stats.keys())) == 1:
        st.write("• 尝试多样化搜索类型，探索更多可能")

def handle_search_error(error_type: str, error_msg: str, placeholder):
    """统一错误处理函数"""
    
    error_solutions = {
        "empty_state": {
            "title": "空状态错误",
            "description": "搜索工作流返回了空状态",
            "solutions": [
                "检查LangGraph工作流配置",
                "验证搜索参数是否正确", 
                "重新启动搜索服务"
            ]
        },
        "invalid_format": {
            "title": "格式错误",
            "description": "搜索结果格式不符合预期",
            "solutions": [
                "检查数据序列化配置",
                "验证节点输出格式",
                "重新初始化搜索系统"
            ]
        },
        "output_integration": {
            "title": "输出集成错误", 
            "description": "结果整合阶段出现问题",
            "solutions": [
                "这是已知问题，正在修复中",
                "尝试重新执行搜索",
                "如果持续失败，请联系技术支持"
            ]
        },
        "search_failed": {
            "title": "搜索失败",
            "description": "搜索工作流执行失败",
            "solutions": [
                "检查网络连接",
                "验证API密钥配置", 
                "简化搜索条件重试"
            ]
        },
        "exception": {
            "title": "系统异常",
            "description": "搜索过程中发生未预期的错误",
            "solutions": [
                "刷新页面重试",
                "检查系统资源使用",
                "联系技术支持获取帮助"
            ]
        }
    }
    
    error_info = error_solutions.get(error_type, error_solutions["exception"])
    
    with st.expander(f"🔧 {error_info['title']} - 解决方案", expanded=True):
        st.write(f"**问题描述**: {error_info['description']}")
        st.write(f"**具体错误**: {error_msg}")
        st.write("**解决方案**:")
        for i, solution in enumerate(error_info['solutions'], 1):
            st.write(f"{i}. {solution}")
        
        # 提供快速操作
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 重新搜索", key=f"retry_{error_type}"):
                st.session_state.langgraph_search_in_progress = False
                st.session_state.langgraph_search_results = None
                st.success("已重置搜索状态，请重新输入查询")
                st.rerun()
        
        with col2:
            if st.button("📋 复制错误信息", key=f"copy_{error_type}"):
                error_report = f"错误类型: {error_info['title']}\n错误详情: {error_msg}\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                st.code(error_report)
                st.info("错误信息已显示，可手动复制")

def safe_get_attribute(obj, attr_name, default=None):
    """安全获取对象属性"""
    try:
        if hasattr(obj, attr_name):
            return getattr(obj, attr_name)
        elif isinstance(obj, dict):
            return obj.get(attr_name, default)
        else:
            return default
    except Exception:
        return default

def validate_search_state(state: Dict[str, Any]) -> bool:
    """验证搜索状态的完整性"""
    if not isinstance(state, dict):
        return False
    
    required_fields = [
        'user_query', 'detected_intent', 'search_results'
    ]
    
    for field in required_fields:
        if field not in state:
            return False
    
    search_results = state.get('search_results', {})
    if not isinstance(search_results, dict):
        return False
    
    # 检查搜索结果必需字段
    required_result_fields = [
        'companies', 'employees', 'qualified_companies', 'qualified_employees'
    ]
    
    for field in required_result_fields:
        if field not in search_results:
            return False
        if not isinstance(search_results[field], list):
            return False
    
    return True

if __name__ == "__main__":
    main()