"""
AI客户发现工具 - 员工AI智能分析页面
基于大语言模型进行深度员工价值评估和团队分析
"""

import streamlit as st
import pandas as pd
import json
import os
import sys
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from employee_ai_analyzer import EmployeeAIAnalyzer
from components.common import check_api_keys, display_api_status

# 页面配置
st.set_page_config(
    page_title="员工AI分析 - AI Customer Finder",
    page_icon="👥",
    layout="wide"
)

st.title("👥 员工AI智能分析")
st.markdown("""
基于大语言模型的深度员工价值评估系统，提供：
- **决策权力分析** - AI评估员工的决策影响力和权威性
- **可接触性评估** - 智能分析联系难易度和接触成功率
- **岗位关联度** - 评估员工岗位与业务需求的匹配程度
- **网络影响力** - 分析员工在组织和行业中的影响力
""")

# 检查API配置状态
api_status = check_api_keys()
display_api_status()

# 如果没有配置LLM API，显示警告
llm_available = any([
    api_status.get('OPENAI_API_KEY', False),
    api_status.get('ANTHROPIC_API_KEY', False), 
    api_status.get('GOOGLE_API_KEY', False),
    api_status.get('ARK_API_KEY', False)
])

if not llm_available:
    st.error("""
    ⚠️ **需要配置LLM API才能使用AI分析功能**
    
    请在 `.env` 文件中配置以下任一API：
    - OpenAI API Key
    - Anthropic API Key  
    - Google API Key
    - Huoshan/Volcano API Key
    """)
    st.stop()

# 主功能区域
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📁 数据源选择")
    
    # 选择数据文件
    employee_dir = Path("output/employee")
    
    if not employee_dir.exists() or not list(employee_dir.glob("*.csv")):
        st.warning("📂 未找到员工数据文件，请先运行员工搜索功能")
        st.stop()
    
    # 获取可用的数据文件
    csv_files = list(employee_dir.glob("*.csv"))
    file_options = {f.stem: str(f) for f in csv_files}
    
    selected_file = st.selectbox(
        "选择要分析的员工数据文件",
        options=list(file_options.keys()),
        help="选择之前搜索生成的员工数据文件"
    )
    
    # 业务背景输入
    st.subheader("🎯 业务背景描述")
    business_context = st.text_area(
        "描述您的业务背景和目标",
        value="""我们是一家可再生能源解决方案提供商，主要业务包括：
- 太阳能发电系统设计与安装
- 储能系统集成服务
- 清洁能源项目开发
- 能源管理软件开发

我们希望找到能够影响采购决策的关键人员，特别是：
- 技术决策者和工程负责人
- 采购经理和供应链负责人
- 项目经理和业务发展负责人""",
        height=150,
        help="请详细描述您的业务背景，AI将基于此评估员工价值"
    )
    
    # 分析类型选择
    st.subheader("🔍 分析类型")
    analysis_type = st.radio(
        "选择分析类型",
        ["个人分析", "团队分析"],
        help="个人分析：单独评估每个员工；团队分析：分析团队结构和协作关系"
    )
    
    # LLM提供商选择
    st.subheader("🧠 AI模型选择")
    available_providers = []
    if api_status.get('OPENAI_API_KEY'): available_providers.append('openai')
    if api_status.get('ANTHROPIC_API_KEY'): available_providers.append('anthropic')
    if api_status.get('GOOGLE_API_KEY'): available_providers.append('google')
    if api_status.get('ARK_API_KEY'): available_providers.append('huoshan')
    
    provider_names = {
        'openai': 'OpenAI GPT-4',
        'anthropic': 'Anthropic Claude',
        'google': 'Google Gemini',
        'huoshan': 'Huoshan Volcano'
    }
    
    selected_provider = st.selectbox(
        "选择AI模型",
        options=available_providers,
        format_func=lambda x: provider_names.get(x, x),
        help="选择用于分析的大语言模型"
    )
    
    # 分析按钮
    analyze_button = st.button(
        "🚀 开始员工AI分析",
        type="primary",
        use_container_width=True
    )

with col2:
    st.subheader("📊 员工AI分析结果")
    
    # 结果显示区域
    results_container = st.container()
    
    if analyze_button:
        if not business_context.strip():
            st.error("请输入业务背景描述")
            st.stop()
        
        # 加载数据
        file_path = file_options[selected_file]
        try:
            df = pd.read_csv(file_path)
            st.success(f"✅ 已加载 {len(df)} 位员工数据")
        except Exception as e:
            st.error(f"读取数据文件失败: {e}")
            st.stop()
        
        # 初始化AI分析器
        with st.spinner("🤖 正在初始化员工AI分析器..."):
            analyzer = EmployeeAIAnalyzer(provider=selected_provider)
        
        # 创建进度条
        progress_bar = st.progress(0)
        status_text = st.empty()
        results_data = []
        
        # 批量分析
        def update_progress(current, total, employee_name):
            progress = current / total
            progress_bar.progress(progress)
            status_text.text(f"正在分析: {employee_name} ({current}/{total})")
        
        with st.spinner("🔍 正在进行员工AI分析..."):
            try:
                # 转换数据格式
                employees_data = df.to_dict('records')
                
                if analysis_type == "个人分析":
                    # 个人分析
                    results = analyzer.batch_analyze_employees(
                        employees_data, 
                        business_context, 
                        callback=update_progress
                    )
                else:
                    # 团队分析
                    results = analyzer.analyze_team_structure(
                        employees_data, 
                        business_context
                    )
                    # 为团队分析创建进度更新
                    for i in range(len(employees_data)):
                        update_progress(i+1, len(employees_data), f"团队分析第{i+1}阶段")
                
                # 清空进度显示
                progress_bar.empty()
                status_text.empty()
                
                # 显示结果
                st.success("🎉 员工AI分析完成！")
                
                # 转换结果为DataFrame
                if analysis_type == "个人分析":
                    results_df = pd.DataFrame(results)
                else:
                    # 团队分析结果处理
                    individual_results = results.get('individual_analysis', [])
                    results_df = pd.DataFrame(individual_results)
                    
                    # 显示团队洞察
                    team_insights = results.get('team_insights', {})
                    if team_insights:
                        st.subheader("👥 团队结构洞察")
                        
                        col_team1, col_team2 = st.columns(2)
                        with col_team1:
                            st.markdown("**🎯 关键决策者**")
                            for decision_maker in team_insights.get('key_decision_makers', []):
                                st.write(f"• {decision_maker}")
                        
                        with col_team2:
                            st.markdown("**🔗 协作关系**")
                            for collaboration in team_insights.get('collaboration_opportunities', []):
                                st.write(f"• {collaboration}")
                        
                        if team_insights.get('team_approach_strategy'):
                            st.markdown("**📋 团队接触策略**")
                            st.write(team_insights['team_approach_strategy'])
                
                # 保存结果
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                analysis_suffix = "individual" if analysis_type == "个人分析" else "team"
                output_file = f"output/employee/employee_ai_analysis_{selected_file}_{analysis_suffix}_{timestamp}.csv"
                os.makedirs("output/employee", exist_ok=True)
                results_df.to_csv(output_file, index=False, encoding='utf-8-sig')
                
                st.info(f"📄 分析结果已保存至: {output_file}")
                
                # 显示统计概览
                st.subheader("📈 分析概览")
                
                col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
                
                with col_stats1:
                    avg_score = results_df['final_score'].mean()
                    st.metric("平均得分", f"{avg_score:.1f}", help="所有员工的平均AI评分")
                
                with col_stats2:
                    high_score_count = len(results_df[results_df['final_score'] >= 70])
                    st.metric("高价值员工", f"{high_score_count} 位", help="得分≥70的高价值员工数量")
                
                with col_stats3:
                    max_score = results_df['final_score'].max()
                    top_employee = results_df.loc[results_df['final_score'].idxmax(), 'employee_name']
                    st.metric("最高得分", f"{max_score:.1f}", help=f"最高分员工: {top_employee}")
                
                with col_stats4:
                    p0_count = len(results_df[results_df.get('priority_level', 'P4') == 'P0'])
                    st.metric("P0优先级", f"{p0_count} 位", help="最高优先级员工数量")
                
                # 得分分布图
                st.subheader("📊 得分分布分析")
                
                fig_dist = px.histogram(
                    results_df,
                    x='final_score',
                    nbins=20,
                    title="员工价值得分分布",
                    labels={'final_score': '综合得分', 'count': '员工数量'}
                )
                fig_dist.update_layout(showlegend=False)
                st.plotly_chart(fig_dist, use_container_width=True)
                
                # 维度雷达图（选择前5名员工）
                if 'dimension_scores' in results_df.columns:
                    st.subheader("🎯 TOP5员工维度分析")
                    
                    top5 = results_df.nlargest(5, 'final_score')
                    
                    # 解析维度得分
                    radar_data = []
                    dimensions = ['决策权力', '可接触性', '岗位关联度', '网络影响力']
                    
                    for _, row in top5.iterrows():
                        try:
                            if isinstance(row['dimension_scores'], str):
                                scores = json.loads(row['dimension_scores'])
                            else:
                                scores = row['dimension_scores']
                            
                            radar_data.append({
                                'employee': row['employee_name'][:15] + "..." if len(row['employee_name']) > 15 else row['employee_name'],
                                'decision_power': scores.get('decision_power', 0),
                                'accessibility': scores.get('accessibility', 0),
                                'role_relevance': scores.get('role_relevance', 0),
                                'network_influence': scores.get('network_influence', 0)
                            })
                        except:
                            continue
                    
                    if radar_data:
                        # 创建雷达图
                        fig_radar = go.Figure()
                        
                        for data in radar_data:
                            fig_radar.add_trace(go.Scatterpolar(
                                r=[data['decision_power'], data['accessibility'], 
                                   data['role_relevance'], data['network_influence']],
                                theta=['决策权力', '可接触性', '岗位关联度', '网络影响力'],
                                fill='toself',
                                name=data['employee']
                            ))
                        
                        fig_radar.update_layout(
                            polar=dict(
                                radialaxis=dict(
                                    visible=True,
                                    range=[0, 100]
                                )),
                            showlegend=True,
                            title="TOP5员工四维分析对比"
                        )
                        
                        st.plotly_chart(fig_radar, use_container_width=True)
                
                # 优先级分布饼图
                if 'priority_level' in results_df.columns:
                    st.subheader("📋 优先级分布")
                    
                    priority_counts = results_df['priority_level'].value_counts()
                    
                    fig_pie = px.pie(
                        values=priority_counts.values,
                        names=priority_counts.index,
                        title="员工优先级分布",
                        color_discrete_map={
                            'P0': '#ff4444',  # 红色
                            'P1': '#ff8800',  # 橙色
                            'P2': '#ffdd00',  # 黄色
                            'P3': '#88dd00',  # 黄绿色
                            'P4': '#44dd44'   # 绿色
                        }
                    )
                    
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                # 详细结果表格
                st.subheader("📋 详细分析结果")
                
                # 创建显示用的DataFrame
                display_columns = ['employee_name', 'title', 'final_score', 'priority_level', 'analysis_summary', 'tags']
                available_columns = [col for col in display_columns if col in results_df.columns]
                display_df = results_df[available_columns].copy()
                
                if 'final_score' in display_df.columns:
                    display_df['final_score'] = display_df['final_score'].round(1)
                
                # 重命名列
                column_mapping = {
                    'employee_name': '姓名',
                    'title': '职位',
                    'final_score': '综合得分',
                    'priority_level': '优先级',
                    'analysis_summary': '分析摘要',
                    'tags': '智能标签'
                }
                
                display_df = display_df.rename(columns=column_mapping)
                
                # 按得分排序
                if '综合得分' in display_df.columns:
                    display_df = display_df.sort_values('综合得分', ascending=False)
                
                # 添加得分颜色标识
                def score_color(score):
                    if score >= 80:
                        return "🟢"
                    elif score >= 60:
                        return "🟡"
                    elif score >= 40:
                        return "🟠"
                    else:
                        return "🔴"
                
                if '综合得分' in display_df.columns:
                    display_df['状态'] = display_df['综合得分'].apply(score_color)
                    # 重新排列列顺序
                    cols = ['状态'] + [col for col in display_df.columns if col != '状态']
                    display_df = display_df[cols]
                
                # 配置列显示
                column_config = {}
                if '综合得分' in display_df.columns:
                    column_config["综合得分"] = st.column_config.ProgressColumn(
                        "综合得分",
                        help="AI评估的综合得分",
                        min_value=0,
                        max_value=100,
                        format="%.1f"
                    )
                if '分析摘要' in display_df.columns:
                    column_config["分析摘要"] = st.column_config.TextColumn(
                        "分析摘要",
                        width="large"
                    )
                if '智能标签' in display_df.columns:
                    column_config["智能标签"] = st.column_config.TextColumn(
                        "智能标签", 
                        width="medium"
                    )
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config=column_config
                )
                
                # 导出选项
                st.subheader("💾 导出分析结果")
                
                col_export1, col_export2 = st.columns(2)
                
                with col_export1:
                    # CSV导出
                    csv = results_df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📄 下载CSV文件",
                        data=csv,
                        file_name=f"employee_ai_analysis_results_{timestamp}.csv",
                        mime="text/csv"
                    )
                
                with col_export2:
                    # JSON导出
                    import json as json_lib
                    json_data = json_lib.dumps(
                        results_df.to_dict('records'), 
                        ensure_ascii=False, 
                        indent=2
                    )
                    st.download_button(
                        label="📋 下载JSON文件", 
                        data=json_data,
                        file_name=f"employee_ai_analysis_results_{timestamp}.json",
                        mime="application/json"
                    )
                
            except Exception as e:
                st.error(f"员工AI分析过程中出错: {e}")
                st.exception(e)
        
    else:
        with results_container:
            st.info("👈 请在左侧配置分析参数，然后点击开始员工AI分析按钮")
            
            # 显示功能介绍
            st.markdown("""
            ### 🚀 员工AI分析功能亮点
            
            **🎯 四维智能评分体系：**
            - **决策权力** (35% 权重) - AI评估决策影响力和权威性
            - **可接触性** (25% 权重) - 智能分析联系难易度和成功率  
            - **岗位关联度** (25% 权重) - 评估岗位与业务需求匹配程度
            - **网络影响力** (15% 权重) - 分析组织和行业影响力
            
            **🧠 深度AI洞察：**
            - 个性化员工价值分析
            - 优先级自动分级 (P0-P4)
            - 接触策略个性化建议  
            - 团队结构协作分析
            - 决策链路智能识别
            
            **📊 可视化分析报告：**
            - 价值分布统计图表
            - 四维能力雷达图
            - 优先级分布饼图
            - 智能标签分类展示
            """)

# 侧边栏附加信息
st.sidebar.markdown("---")
st.sidebar.subheader("💡 使用提示")
st.sidebar.markdown("""
**最佳实践：**
1. 详细描述业务背景和目标
2. 选择合适的AI模型和分析类型
3. 重点关注P0-P1优先级员工
4. 结合团队分析制定接触策略

**评分说明：**
- 🟢 80+ 分：核心关键人员
- 🟡 60-79 分：重要联系人  
- 🟠 40-59 分：潜在影响者
- 🔴 <40 分：一般员工

**优先级说明：**
- P0：立即接触，核心决策者
- P1：高优先级，重要影响者
- P2：中优先级，协助决策者
- P3：低优先级，信息提供者
- P4：参考级别，一般员工
""")

st.sidebar.markdown("---")
st.sidebar.info("💰 **提示**: AI分析会消耗LLM API调用额度，建议合理使用。")