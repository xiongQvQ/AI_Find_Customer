#!/usr/bin/env python3
"""
Streamlit智能搜索界面 - CrewAI多智能体工作流前端
为用户提供直观的智能搜索体验
"""

import streamlit as st
import json
import time
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

# 导入CrewAI主程序
from crewai_main import IntelligentSearchCrew, SearchCrewManager

# 页面配置
st.set_page_config(
    page_title="AI智能客户搜索系统",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
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
.metric-container {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}
.status-healthy {
    color: #28a745;
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
</style>
""", unsafe_allow_html=True)

# 初始化会话状态
if 'search_crew_manager' not in st.session_state:
    st.session_state.search_crew_manager = SearchCrewManager()
    
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
    
if 'search_in_progress' not in st.session_state:
    st.session_state.search_in_progress = False

if 'crew_health' not in st.session_state:
    st.session_state.crew_health = None

def main():
    """主界面函数"""
    
    # 主标题
    st.markdown('<h1 class="main-header">🔍 AI智能客户搜索系统</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #6c757d;">基于CrewAI多智能体技术，智能理解需求，精准匹配客户</p>', unsafe_allow_html=True)
    
    # 侧边栏配置
    setup_sidebar()
    
    # 主界面标签页
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 智能搜索", "📊 搜索结果", "⚙️ 系统状态", "📈 搜索历史"])
    
    with tab1:
        intelligent_search_interface()
    
    with tab2:
        search_results_interface()
    
    with tab3:
        system_status_interface()
    
    with tab4:
        search_history_interface()

def setup_sidebar():
    """设置侧边栏"""
    with st.sidebar:
        st.markdown("## ⚙️ 系统配置")
        
        # LLM模型选择
        llm_model = st.selectbox(
            "选择LLM模型",
            ["gpt-4", "gpt-3.5-turbo", "claude-3"],
            index=0,
            help="选择用于智能分析的语言模型"
        )
        
        # 搜索配置
        st.markdown("### 搜索参数")
        max_results = st.slider("最大搜索结果数", 5, 50, 20)
        min_score = st.slider("最低评分阈值", 0.0, 10.0, 6.0, 0.5)
        
        # 高级配置
        with st.expander("高级配置"):
            verbose_mode = st.checkbox("详细输出模式", value=True)
            save_results = st.checkbox("保存搜索结果", value=True)
            enable_memory = st.checkbox("启用智能体记忆", value=True)
        
        # 保存配置到会话状态
        st.session_state.search_config = {
            'llm_model': llm_model,
            'max_results': max_results,
            'min_score': min_score,
            'verbose': verbose_mode,
            'save_results': save_results,
            'memory': enable_memory
        }
        
        st.markdown("---")
        
        # 系统信息
        if st.button("检查系统健康状态"):
            check_system_health()

def intelligent_search_interface():
    """智能搜索界面"""
    st.markdown('<h2 class="section-header">💬 描述您的需求</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # 需求输入
        user_requirement = st.text_area(
            "请用自然语言描述您的采购需求：",
            placeholder="例如：我想找卖数位板的公司，要求支持4K分辨率，价格1000-3000元，深圳地区",
            height=100,
            help="系统会智能理解您的需求，自动生成搜索策略"
        )
        
        # 搜索示例
        st.markdown("### 💡 搜索示例")
        examples = [
            "我需要太阳能板供应商，功率300W以上，价格合理，华东地区",
            "寻找LED显示屏制造商，户外P10规格，深圳或广州厂家",
            "需要工业机器人供应商，6轴关节机器人，负载20kg，江浙沪地区"
        ]
        
        selected_example = st.selectbox("选择示例需求", [""] + examples)
        if selected_example and st.button("使用此示例"):
            user_requirement = selected_example
            st.rerun()
    
    with col2:
        # 搜索按钮和状态
        st.markdown("### 🚀 开始搜索")
        
        if user_requirement and not st.session_state.search_in_progress:
            if st.button("🔍 启动智能搜索", type="primary", use_container_width=True):
                execute_intelligent_search(user_requirement)
        
        elif st.session_state.search_in_progress:
            st.warning("🔄 搜索正在进行中...")
            if st.button("⏹️ 停止搜索", use_container_width=True):
                st.session_state.search_in_progress = False
                st.success("搜索已停止")
        
        else:
            st.info("请先输入需求描述")
    
    # 实时进度显示
    if st.session_state.search_in_progress:
        show_search_progress()

def execute_intelligent_search(user_requirement: str):
    """执行智能搜索"""
    st.session_state.search_in_progress = True
    
    # 创建进度条和状态显示
    progress_container = st.container()
    status_container = st.container()
    
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    try:
        with status_container:
            st.info("🚀 正在初始化智能搜索Crew...")
        
        # 获取配置
        config = st.session_state.search_config
        
        # 创建或获取Crew
        crew_id = "main_search_crew"
        if crew_id not in st.session_state.search_crew_manager.crews:
            crew = st.session_state.search_crew_manager.create_crew(
                crew_id=crew_id,
                llm_model=config['llm_model'],
                verbose=config['verbose']
            )
        
        # 更新进度
        progress_bar.progress(20)
        status_text.text("🔄 启动多智能体协作...")
        time.sleep(1)  # 模拟处理时间
        
        # 执行搜索
        with st.spinner("AI智能体正在协作分析您的需求..."):
            search_result = st.session_state.search_crew_manager.execute_search(
                crew_id=crew_id,
                user_requirement=user_requirement,
                save_intermediate_results=config['save_results']
            )
        
        progress_bar.progress(100)
        status_text.text("✅ 搜索完成！")
        
        # 保存结果
        st.session_state.search_results = search_result
        st.session_state.search_in_progress = False
        
        if search_result.get('success'):
            st.success(f"🎉 智能搜索完成！用时: {search_result.get('execution_time', 0):.1f}秒")
            st.balloons()
        else:
            st.error(f"❌ 搜索失败: {search_result.get('error', '未知错误')}")
    
    except Exception as e:
        st.session_state.search_in_progress = False
        st.error(f"❌ 搜索执行失败: {str(e)}")

def show_search_progress():
    """显示搜索进度"""
    progress_container = st.container()
    
    with progress_container:
        st.markdown("### 🔄 搜索进度")
        
        # 模拟进度步骤
        steps = [
            "📋 需求分析智能体: 解析用户需求",
            "🎯 搜索策略智能体: 制定搜索计划",
            "🔍 搜索执行智能体: 执行搜索任务",
            "📊 评分分析智能体: AI智能评分",
            "✨ 结果优化智能体: 优化排序结果"
        ]
        
        for i, step in enumerate(steps):
            if i < 3:  # 模拟前3个步骤已完成
                st.success(f"✅ {step}")
            elif i == 3:  # 当前正在执行的步骤
                st.info(f"🔄 {step}")
            else:  # 未来的步骤
                st.write(f"⏳ {step}")

def search_results_interface():
    """搜索结果界面"""
    if not st.session_state.search_results:
        st.info("暂无搜索结果。请先在'智能搜索'标签页执行搜索。")
        return
    
    result = st.session_state.search_results
    
    if not result.get('success'):
        st.error(f"搜索失败: {result.get('error', '未知错误')}")
        return
    
    st.markdown('<h2 class="section-header">📊 搜索结果</h2>', unsafe_allow_html=True)
    
    # 搜索摘要
    show_search_summary(result)
    
    # 结果展示
    crew_result = result.get('crew_result', {})
    if isinstance(crew_result, dict) and 'optimized_results' in crew_result:
        show_detailed_results(crew_result['optimized_results'])
    else:
        st.info("搜索结果处理中，请稍后查看详细结果。")

def show_search_summary(result: Dict[str, Any]):
    """显示搜索摘要"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "执行时间",
            f"{result.get('execution_time', 0):.1f}秒",
            help="总搜索时间"
        )
    
    with col2:
        workflow_summary = result.get('workflow_summary', {})
        st.metric(
            "智能体数量",
            workflow_summary.get('total_agents', 0),
            help="参与的智能体数量"
        )
    
    with col3:
        st.metric(
            "任务步骤",
            workflow_summary.get('total_tasks', 0),
            help="执行的任务步骤数"
        )
    
    with col4:
        perf_metrics = workflow_summary.get('performance_metrics', {})
        st.metric(
            "效率评分",
            f"{perf_metrics.get('efficiency_score', 0):.2f}",
            help="搜索效率评分"
        )

def show_detailed_results(companies: List[Dict[str, Any]]):
    """显示详细搜索结果"""
    if not companies:
        st.warning("未找到匹配的公司结果")
        return
    
    st.markdown(f"### 📋 找到 {len(companies)} 家匹配公司")
    
    # 结果筛选
    col1, col2 = st.columns([1, 1])
    with col1:
        score_filter = st.slider("评分筛选", 0.0, 10.0, (6.0, 10.0))
    with col2:
        tier_filter = st.multiselect(
            "质量等级",
            ["excellent", "very_good", "good", "acceptable"],
            default=["excellent", "very_good", "good"]
        )
    
    # 筛选结果
    filtered_companies = [
        company for company in companies
        if (score_filter[0] <= company.get('overall_score', 0) <= score_filter[1] and
            company.get('score_tier', '') in tier_filter)
    ]
    
    if not filtered_companies:
        st.warning("没有符合筛选条件的公司")
        return
    
    # 结果排序
    sort_by = st.selectbox("排序方式", ["评分", "公司名称", "匹配度"], index=0)
    if sort_by == "评分":
        filtered_companies.sort(key=lambda x: x.get('overall_score', 0), reverse=True)
    elif sort_by == "公司名称":
        filtered_companies.sort(key=lambda x: x.get('company_name', ''))
    
    # 显示结果
    for i, company in enumerate(filtered_companies, 1):
        show_company_card(company, i)
    
    # 导出选项
    if st.button("📄 导出搜索结果"):
        export_results(filtered_companies)

def show_company_card(company: Dict[str, Any], rank: int):
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
            # 公司描述
            description = company.get('analysis_summary', '') or company.get('original_data', {}).get('description', '')
            if description:
                st.write(f"**公司描述:** {description[:200]}...")
            
            # 匹配原因
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
                st.write("**细分评分:**")
                for dimension, score in dimension_scores.items():
                    st.progress(score, text=f"{dimension}: {score:.1f}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("---")

def export_results(companies: List[Dict[str, Any]]):
    """导出搜索结果"""
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
                '公司描述': company.get('analysis_summary', '')
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
        
        st.success(f"搜索结果已准备下载: {len(companies)} 条记录")
        
    except Exception as e:
        st.error(f"导出失败: {str(e)}")

def system_status_interface():
    """系统状态界面"""
    st.markdown('<h2 class="section-header">⚙️ 系统状态</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🔄 刷新系统状态", use_container_width=True):
            check_system_health()
        
        # 显示健康状态
        if st.session_state.crew_health:
            health = st.session_state.crew_health
            
            if health['overall_status'] == 'healthy':
                st.success("✅ 系统运行正常")
            else:
                st.error("❌ 系统存在问题")
            
            # 详细状态
            st.markdown("### 组件状态")
            
            env_vars = health.get('environment_variables', {})
            for var, status in env_vars.items():
                if status:
                    st.success(f"✅ {var}: 已配置")
                else:
                    st.error(f"❌ {var}: 未配置")
            
            # 智能体状态
            if health.get('agents_status'):
                st.success("✅ 智能体: 正常")
            else:
                st.error("❌ 智能体: 异常")
            
            # 工具状态
            if health.get('tools_status'):
                st.success("✅ 工具: 可用")
            else:
                st.error("❌ 工具: 不可用")
    
    with col2:
        # 系统信息
        st.markdown("### 📊 系统信息")
        
        if 'main_search_crew' in st.session_state.search_crew_manager.crews:
            crew = st.session_state.search_crew_manager.crews['main_search_crew']
            info = crew.get_crew_info()
            
            st.info(f"**Crew版本:** {info.get('crew_version', 'N/A')}")
            st.info(f"**LLM模型:** {info.get('llm_model', 'N/A')}")
            st.info(f"**智能体数量:** {info.get('agents_info', {}).get('total_agents', 0)}")
            st.info(f"**可用工具:** {info.get('available_tools', 0)}")
            
            # 任务序列
            with st.expander("查看任务序列"):
                task_sequence = info.get('task_sequence', [])
                for i, task in enumerate(task_sequence, 1):
                    st.write(f"{i}. {task}")

def check_system_health():
    """检查系统健康状态"""
    try:
        # 创建临时Crew进行健康检查
        crew = IntelligentSearchCrew()
        health = crew.health_check()
        st.session_state.crew_health = health
        
        if health['overall_status'] == 'healthy':
            st.success("系统健康检查通过")
        else:
            st.warning("系统健康检查发现问题")
            
    except Exception as e:
        st.session_state.crew_health = {
            'overall_status': 'error',
            'error': str(e)
        }
        st.error(f"健康检查失败: {str(e)}")

def search_history_interface():
    """搜索历史界面"""
    st.markdown('<h2 class="section-header">📈 搜索历史</h2>', unsafe_allow_html=True)
    
    history = st.session_state.search_crew_manager.get_search_history()
    
    if not history:
        st.info("暂无搜索历史")
        return
    
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
    
    # 历史列表
    st.markdown("### 搜索记录")
    
    for i, record in enumerate(reversed(history), 1):
        with st.expander(f"搜索 {i} - {record.get('timestamp', 'Unknown')}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**需求:** {record.get('requirement', 'N/A')}")
                st.write(f"**Crew ID:** {record.get('crew_id', 'N/A')}")
            
            with col2:
                if record.get('success'):
                    st.success("✅ 成功")
                else:
                    st.error("❌ 失败")

if __name__ == "__main__":
    main()