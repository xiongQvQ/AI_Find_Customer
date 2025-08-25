#!/usr/bin/env python3
"""
智能搜索页面 - CrewAI多智能体工作流前端集成
为用户提供自然语言智能搜索体验
"""

import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

# 导入组件
from components.common import check_api_keys, display_api_status
from components.language_manager import get_language_manager, t
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 页面配置
st.set_page_config(
    page_title=t('intelligent_search.title'),
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
@keyframes pulse {
    0% { opacity: 0.8; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.02); }
    100% { opacity: 0.8; transform: scale(1); }
}
.agent-step {
    transition: all 0.3s ease;
}
.agent-running {
    animation: pulse 2s infinite;
}
.status-error {
    color: #dc3545;
}
.company-card {
    border: 1px solid #dee2e6;
    border-radius: 0.5rem;
    padding: 1rem;
    margin: 0.5rem 0;
    background-color: #ffffff;
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
.progress-step {
    padding: 0.5rem;
    margin: 0.2rem 0;
    border-radius: 0.25rem;
}
.step-completed {
    background-color: #d4edda;
    color: #155724;
}
.step-current {
    background-color: #cce7ff;
    color: #004085;
}
.step-pending {
    background-color: #f8f9fa;
    color: #6c757d;
}
</style>
""", unsafe_allow_html=True)

def initialize_intelligent_search():
    """初始化智能搜索系统"""
    try:
        from crewai_simplified import IntelligentSearchCrewSimplified
        
        if 'intelligent_search_crew' not in st.session_state:
            st.session_state.intelligent_search_crew = IntelligentSearchCrewSimplified(
                verbose=True,
                output_dir="output"
            )
        
        return st.session_state.intelligent_search_crew
    
    except Exception as e:
        st.error(f"❌ 智能搜索系统初始化失败: {str(e)}")
        return None

def check_system_health(crew):
    """检查系统健康状态"""
    if crew:
        health = crew.health_check()
        
        if health['overall_status'] == 'healthy':
            st.success("✅ 智能搜索系统运行正常")
            return True
        else:
            st.error("❌ 智能搜索系统检查失败")
            st.json(health)
            return False
    return False

def show_search_progress(steps_status):
    """显示搜索进度"""
    st.markdown("### 🔄 智能体协作进度")
    
    steps = [
        ("需求分析智能体", "📋", "解析用户需求，提取关键信息"),
        ("搜索策略智能体", "🎯", "制定最优搜索策略和关键词"),
        ("搜索执行智能体", "🔍", "执行搜索API，获取公司数据"),
        ("AI评分分析师", "📊", "智能评分和匹配度分析"),
        ("结果优化专家", "✨", "优化排序，生成最终推荐")
    ]
    
    for i, (name, icon, desc) in enumerate(steps):
        status = steps_status.get(i, "pending")
        
        if status == "completed":
            css_class = "step-completed"
            status_icon = "✅"
        elif status == "current":
            css_class = "step-current" 
            status_icon = "🔄"
        else:
            css_class = "step-pending"
            status_icon = "⏳"
        
        st.markdown(f"""
        <div class="progress-step {css_class}">
            {status_icon} {icon} <strong>{name}</strong>: {desc}
        </div>
        """, unsafe_allow_html=True)

def display_search_results(result):
    """显示搜索结果"""
    if not result or not result.get('success'):
        st.error(f"搜索失败: {result.get('error', '未知错误') if result else '无结果'}")
        return
    
    # 获取推荐结果
    recommendations = result.get('final_recommendations', [])
    
    if not recommendations:
        st.warning("未找到匹配的公司推荐")
        return
    
    # 搜索摘要
    st.markdown("### 📊 搜索摘要")
    
    col1, col2, col3, col4 = st.columns(4)
    
    execution_summary = result.get('execution_summary', {})
    
    with col1:
        st.metric("找到公司", len(recommendations))
    
    with col2:
        total_time = execution_summary.get('total_time', 0)
        st.metric("执行时间", f"{total_time:.1f}秒")
    
    with col3:
        st.metric("智能体数", execution_summary.get('total_agents', 0))
    
    with col4:
        avg_score = sum(c.get('overall_score', 0) for c in recommendations) / len(recommendations) if recommendations else 0
        st.metric("平均评分", f"{avg_score:.1f}分")
    
    # 筛选控制
    st.markdown("### 🎛️ 结果筛选")
    
    col1, col2 = st.columns(2)
    
    with col1:
        score_threshold = st.slider("最低评分", 0.0, 10.0, 6.0, 0.5, key="score_filter")
    
    with col2:
        tier_options = ["excellent", "very_good", "good", "acceptable"]
        selected_tiers = st.multiselect(
            "质量等级",
            tier_options,
            default=["excellent", "very_good", "good"],
            key="tier_filter"
        )
    
    # 筛选结果
    filtered_companies = [
        company for company in recommendations
        if (company.get('overall_score', 0) >= score_threshold and
            company.get('score_tier', '') in selected_tiers)
    ]
    
    st.markdown(f"### 🏆 推荐结果 ({len(filtered_companies)} 家公司)")
    
    if not filtered_companies:
        st.info("没有符合筛选条件的公司")
        return
    
    # 显示结果
    for i, company in enumerate(filtered_companies, 1):
        display_company_card(company, i)
    
    # 导出功能
    st.markdown("### 📥 导出结果")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 导出为CSV", use_container_width=True):
            export_to_csv(filtered_companies)
    
    with col2:
        if st.button("📋 复制结果摘要", use_container_width=True):
            copy_summary(filtered_companies)

def display_company_card(company, rank):
    """显示公司卡片"""
    with st.container():
        st.markdown('<div class="company-card">', unsafe_allow_html=True)
        
        # 标题行
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            company_name = company.get('company_name', 'Unknown')
            st.markdown(f"### {rank}. {company_name}")
        
        with col2:
            score = company.get('overall_score', 0)
            if score >= 9:
                st.markdown(f'<span class="score-excellent">⭐ {score:.1f}分</span>', unsafe_allow_html=True)
            elif score >= 7:
                st.markdown(f'<span class="score-good">🔵 {score:.1f}分</span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<span class="score-fair">🟡 {score:.1f}分</span>', unsafe_allow_html=True)
        
        with col3:
            tier = company.get('score_tier', '')
            tier_labels = {
                'excellent': '🏆 优秀',
                'very_good': '⭐ 很好',
                'good': '✅ 良好',
                'acceptable': '📝 可接受'
            }
            st.write(tier_labels.get(tier, tier))
        
        # 详细信息
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 分析摘要
            summary = company.get('analysis_summary', '')
            if summary:
                st.write(f"**AI分析摘要:** {summary[:200]}...")
            
            # 匹配优势
            match_reasons = company.get('match_reasons', [])
            if match_reasons:
                st.write(f"**匹配优势:** {', '.join(match_reasons[:3])}")
            
            # 关注点
            concerns = company.get('concerns', [])
            if concerns:
                st.write(f"**注意事项:** {', '.join(concerns[:2])}")
        
        with col2:
            # 维度评分
            dimension_scores = company.get('dimension_scores', {})
            if dimension_scores:
                st.write("**维度评分:**")
                for dimension, score in dimension_scores.items():
                    st.progress(score, text=f"{dimension}: {score:.2f}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("---")

def export_to_csv(companies):
    """导出为CSV"""
    try:
        # 准备导出数据
        export_data = []
        for company in companies:
            export_data.append({
                '排名': company.get('rank', 0),
                '公司名称': company.get('company_name', ''),
                '综合评分': company.get('overall_score', 0),
                '质量等级': company.get('score_tier', ''),
                '匹配优势': ', '.join(company.get('match_reasons', [])),
                '关注事项': ', '.join(company.get('concerns', [])),
                '置信度': company.get('confidence_level', ''),
                'AI分析摘要': company.get('analysis_summary', '')
            })
        
        # 创建DataFrame
        df = pd.DataFrame(export_data)
        
        # 提供下载
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"intelligent_search_results_{timestamp}.csv"
        
        csv = df.to_csv(index=False, encoding='utf-8')
        st.download_button(
            label="📥 下载CSV文件",
            data=csv,
            file_name=filename,
            mime='text/csv'
        )
        
        st.success(f"✅ CSV文件已准备下载: {len(companies)} 条记录")
        
    except Exception as e:
        st.error(f"导出失败: {str(e)}")

def copy_summary(companies):
    """复制结果摘要"""
    try:
        summary_text = "# AI智能搜索结果摘要\n\n"
        summary_text += f"搜索时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        summary_text += f"找到公司: {len(companies)} 家\n\n"
        
        for i, company in enumerate(companies[:5], 1):  # 只显示前5个
            name = company.get('company_name', f'公司{i}')
            score = company.get('overall_score', 0)
            tier = company.get('score_tier', '')
            summary_text += f"{i}. {name} - {score:.1f}分 ({tier})\n"
        
        # 使用st.code显示可复制的文本
        st.code(summary_text, language="markdown")
        st.success("✅ 结果摘要已显示，请手动复制上面的文本")
        
    except Exception as e:
        st.error(f"生成摘要失败: {str(e)}")

def main():
    """主界面函数"""
    # 标题
    st.markdown(f'<h1 class="main-header">🔍 {t("intelligent_search.title")}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p style="text-align: center; color: #6c757d;">{t("intelligent_search.subtitle")}</p>', unsafe_allow_html=True)
    
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
    
    # 初始化智能搜索系统
    crew = initialize_intelligent_search()
    if not crew:
        st.stop()
    
    # 系统健康检查
    if not check_system_health(crew):
        st.stop()
    
    # 主界面标签页
    tab1, tab2, tab3 = st.tabs([
        t('intelligent_search.tabs.search'), 
        t('intelligent_search.tabs.results'), 
        t('intelligent_search.tabs.history')
    ])
    
    with tab1:
        intelligent_search_interface(crew)
    
    with tab2:
        search_results_interface()
    
    with tab3:
        search_history_interface(crew)

def intelligent_search_interface(crew):
    """智能搜索界面"""
    st.markdown('<h2 class="section-header">💬 描述您的需求</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # 初始化示例选择状态
        if 'selected_example_text' not in st.session_state:
            st.session_state.selected_example_text = ""
        
        # 搜索示例
        st.markdown(f"### {t('intelligent_search.examples.title')}")
        examples = t('intelligent_search.examples.list')
        
        selected_example = st.selectbox(
            t('intelligent_search.examples.select'),
            [""] + examples,
            key="example_selector"
        )
        
        if selected_example and st.button(t('intelligent_search.examples.use_button'), key="use_example"):
            st.session_state.selected_example_text = selected_example
            st.rerun()
        
        # 需求输入 - 使用默认值来显示选中的示例
        default_value = st.session_state.selected_example_text if st.session_state.selected_example_text else ""
        user_requirement = st.text_area(
            t('intelligent_search.input.title'),
            value=default_value,
            placeholder=t('intelligent_search.input.placeholder'),
            height=120,
            help=t('intelligent_search.input.help'),
            key="user_requirement_input"
        )
        
        # 清空示例状态，以便用户可以继续编辑
        if st.session_state.selected_example_text and user_requirement != st.session_state.selected_example_text:
            st.session_state.selected_example_text = ""
    
    with col2:
        # 搜索控制面板
        st.markdown(f"### {t('intelligent_search.search_control.title')}")
        
        # 初始化搜索状态
        if 'search_in_progress' not in st.session_state:
            st.session_state.search_in_progress = False
        
        if 'search_results' not in st.session_state:
            st.session_state.search_results = None
        
        # 搜索按钮
        if user_requirement and not st.session_state.search_in_progress:
            if st.button(t('intelligent_search.search_control.start_button'), type="primary", use_container_width=True, key="start_search"):
                execute_intelligent_search(crew, user_requirement)
        
        elif st.session_state.search_in_progress:
            st.warning(t('intelligent_search.search_control.in_progress'))
            if st.button(t('intelligent_search.search_control.stop_button'), use_container_width=True, key="stop_search"):
                st.session_state.search_in_progress = False
                st.success(t('intelligent_search.search_control.stopped'))
                st.rerun()
        
        else:
            st.info("请先输入需求描述")
        
        # 高级设置
        with st.expander("⚙️ 高级设置"):
            max_results = st.slider("最大搜索结果数", 5, 50, 20, key="max_results")
            min_score = st.slider("最低评分阈值", 0.0, 10.0, 6.0, 0.5, key="min_score")
            verbose_mode = st.checkbox("详细输出模式", value=True, key="verbose_mode")
    
    # 实时进度显示
    if st.session_state.search_in_progress and 'search_progress' in st.session_state:
        st.markdown("---")
        show_search_progress(st.session_state.search_progress)

def execute_intelligent_search(crew, user_requirement):
    """执行智能搜索"""
    st.session_state.search_in_progress = True
    st.session_state.search_progress = {}
    
    # 创建进度显示容器
    progress_container = st.container()
    
    with progress_container:
        # 主进度条
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 详细步骤显示
        step_container = st.container()
    
    # 定义智能体信息
    agents_info = [
        {"name": t("intelligent_search.agents.requirement_analyst"), "icon": "📋", "desc": t("intelligent_search.agent_descriptions.requirement_analyst")},
        {"name": t("intelligent_search.agents.search_strategist"), "icon": "🎯", "desc": t("intelligent_search.agent_descriptions.search_strategist")},  
        {"name": t("intelligent_search.agents.search_executor"), "icon": "🔍", "desc": t("intelligent_search.agent_descriptions.search_executor")},
        {"name": t("intelligent_search.agents.ai_scorer"), "icon": "📊", "desc": t("intelligent_search.agent_descriptions.ai_scorer")},
        {"name": t("intelligent_search.agents.result_optimizer"), "icon": "✨", "desc": t("intelligent_search.agent_descriptions.result_optimizer")}
    ]
    
    # 初始化步骤显示
    with step_container:
        step_cols = st.columns(5)
        step_placeholders = []
        for i, (col, agent) in enumerate(zip(step_cols, agents_info)):
            with col:
                step_placeholder = st.empty()
                step_placeholder.markdown(f"""
                <div style="text-align: center; padding: 10px; border: 2px solid #ddd; border-radius: 8px; background-color: #f8f9fa;">
                    <div style="font-size: 24px;">{agent['icon']}</div>
                    <div style="font-size: 12px; margin-top: 5px;">{agent['name']}</div>
                    <div style="font-size: 10px; color: #666;">{agent['desc']}</div>
                    <div style="margin-top: 5px; font-size: 14px;">⏳</div>
                </div>
                """, unsafe_allow_html=True)
                step_placeholders.append(step_placeholder)
    
    def progress_callback(progress_info):
        """进度回调函数"""
        step = progress_info.get('step', 0)
        total_steps = progress_info.get('total_steps', 5)
        current_agent = progress_info.get('current_agent', '')
        status = progress_info.get('status', '')
        message = progress_info.get('message', '')
        
        # 更新主进度条
        progress = min(100, (step / total_steps) * 100)
        progress_bar.progress(int(progress))
        status_text.markdown(f"**{message}**")
        
        # 更新步骤显示
        for i, agent in enumerate(agents_info):
            with step_cols[i]:
                if i < step - 1:
                    # 已完成
                    step_placeholders[i].markdown(f"""
                    <div style="text-align: center; padding: 10px; border: 2px solid #28a745; border-radius: 8px; background-color: #d4edda;">
                        <div style="font-size: 24px;">{agent['icon']}</div>
                        <div style="font-size: 12px; margin-top: 5px;">{agent['name']}</div>
                        <div style="font-size: 10px; color: #666;">{agent['desc']}</div>
                        <div style="margin-top: 5px; font-size: 14px; color: #28a745;">✅</div>
                    </div>
                    """, unsafe_allow_html=True)
                elif i == step - 1 and status == "running":
                    # 正在执行
                    step_placeholders[i].markdown(f"""
                    <div style="text-align: center; padding: 10px; border: 2px solid #007bff; border-radius: 8px; background-color: #cce7ff; animation: pulse 2s infinite;">
                        <div style="font-size: 24px;">{agent['icon']}</div>
                        <div style="font-size: 12px; margin-top: 5px;">{agent['name']}</div>
                        <div style="font-size: 10px; color: #666;">{agent['desc']}</div>
                        <div style="margin-top: 5px; font-size: 14px; color: #007bff;">🔄</div>
                    </div>
                    """, unsafe_allow_html=True)
                elif i == step - 1 and status in ["completed", "failed"]:
                    # 刚完成
                    icon = "✅" if status == "completed" else "❌"
                    color = "#28a745" if status == "completed" else "#dc3545"
                    bg_color = "#d4edda" if status == "completed" else "#f8d7da"
                    
                    step_placeholders[i].markdown(f"""
                    <div style="text-align: center; padding: 10px; border: 2px solid {color}; border-radius: 8px; background-color: {bg_color};">
                        <div style="font-size: 24px;">{agent['icon']}</div>
                        <div style="font-size: 12px; margin-top: 5px;">{agent['name']}</div>
                        <div style="font-size: 10px; color: #666;">{agent['desc']}</div>
                        <div style="margin-top: 5px; font-size: 14px; color: {color};">{icon}</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # 保存进度到session state
        st.session_state.search_progress = progress_info
    
    try:
        # 执行搜索，传入进度回调
        search_result = crew.execute_intelligent_search(user_requirement, progress_callback=progress_callback)
        
        # 保存结果
        st.session_state.search_results = search_result
        st.session_state.search_in_progress = False
        
        if search_result.get('success'):
            recommendations = search_result.get('final_recommendations', [])
            exec_time = search_result.get('execution_summary', {}).get('total_time', 0)
            
            success_msg = t('intelligent_search.progress.success').format(count=len(recommendations), time=exec_time)
            st.success(success_msg)
            st.balloons()
            
            # 自动切换到结果标签页
            time.sleep(1)
            st.rerun()
        else:
            error_msg = search_result.get('error', '未知错误')
            error_details = search_result.get('error_details', {})
            failed_msg = t('intelligent_search.progress.failed').format(error=error_msg)
            
            # 详细错误信息
            st.error(failed_msg)
            
            # 显示错误详情和解决建议
            with st.expander("📋 错误详情和解决建议"):
                if "API调用超时" in error_msg or "timeout" in error_msg.lower():
                    st.markdown("""
                    **常见原因:**
                    - 网络连接不稳定
                    - API服务器响应慢
                    - 请求数据量过大
                    
                    **建议解决方案:**
                    - 检查网络连接
                    - 稍后重试
                    - 简化搜索需求描述
                    - 联系系统管理员检查API配置
                    """)
                elif "API调用失败" in error_msg:
                    st.markdown("""
                    **常见原因:**
                    - API密钥配置错误
                    - API配额已用完
                    - API服务不可用
                    
                    **建议解决方案:**
                    - 检查系统设置中的API配置
                    - 验证API密钥是否有效
                    - 检查API使用配额
                    """)
                else:
                    st.markdown(f"""
                    **错误信息:** {error_msg}
                    
                    **建议解决方案:**
                    - 重新描述您的需求
                    - 检查系统设置和API配置
                    - 如问题持续，请联系技术支持
                    """)
                
                # 显示详细错误信息（供技术人员诊断）
                if error_details:
                    st.json(error_details)
    
    except Exception as e:
        st.session_state.search_in_progress = False
        error_str = str(e)
        error_msg = t('intelligent_search.progress.error').format(error=error_str)
        
        st.error(error_msg)
        
        # 提供详细的错误处理指导
        with st.expander("🔧 技术错误详情"):
            st.code(error_str)
            
            if "timeout" in error_str.lower():
                st.info("💡 **超时错误解决建议:**\n- 重试搜索\n- 简化需求描述\n- 检查网络连接")
            elif "connection" in error_str.lower():
                st.info("💡 **连接错误解决建议:**\n- 检查网络连接\n- 验证API服务状态\n- 稍后重试")
            elif "api" in error_str.lower():
                st.info("💡 **API错误解决建议:**\n- 检查API密钥配置\n- 验证API服务可用性\n- 查看系统设置")
            else:
                st.info("💡 **通用解决建议:**\n- 刷新页面重试\n- 检查系统配置\n- 联系技术支持")

def search_results_interface():
    """搜索结果界面"""
    if 'search_results' not in st.session_state or not st.session_state.search_results:
        st.info("暂无搜索结果。请先在'智能搜索'标签页执行搜索。")
        return
    
    st.markdown('<h2 class="section-header">📊 搜索结果</h2>', unsafe_allow_html=True)
    
    display_search_results(st.session_state.search_results)

def search_history_interface(crew):
    """搜索历史界面"""
    st.markdown('<h2 class="section-header">📈 搜索历史</h2>', unsafe_allow_html=True)
    
    if hasattr(crew, 'search_history') and crew.search_history:
        history = crew.search_history
        
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
        for record in reversed(history):  # 最新的在前
            history_data.append({
                "时间": record.get('timestamp', 'Unknown'),
                "需求描述": record.get('user_requirement', 'N/A')[:50] + "..." if len(record.get('user_requirement', '')) > 50 else record.get('user_requirement', 'N/A'),
                "状态": "✅ 成功" if record.get('success') else "❌ 失败",
                "搜索ID": record.get('search_id', 'N/A')
            })
        
        if history_data:
            st.dataframe(history_data, use_container_width=True)
        
        # 清除历史按钮
        if st.button("🗑️ 清除搜索历史", key="clear_history"):
            crew.search_history = []
            st.success("搜索历史已清除")
            st.rerun()
    
    else:
        st.info("暂无搜索历史记录")

if __name__ == "__main__":
    main()