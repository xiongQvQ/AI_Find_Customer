"""
AI客户发现工具 - AI智能分析页面
基于大语言模型进行深度客户分析和评分
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

from ai_analyzer import AIAnalyzer
from components.common import check_api_keys, display_api_status

# 页面配置
st.set_page_config(
    page_title="AI智能分析 - AI Customer Finder",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI智能客户分析")
st.markdown("""
基于大语言模型的深度客户分析系统，提供：
- **行业匹配度分析** - AI评估客户与目标市场的匹配程度
- **商业价值评估** - 智能分析客户规模和购买力
- **决策者分析** - 识别和评估关键决策者可达性
- **增长潜力预测** - 预测未来合作机会和业务增长
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
    company_dir = Path("output/company")
    contact_dir = Path("output/contact")
    
    if not company_dir.exists() or not list(company_dir.glob("*.csv")):
        st.warning("📂 未找到公司数据文件，请先运行搜索功能")
        st.stop()
    
    # 获取可用的数据文件
    csv_files = list(company_dir.glob("*.csv"))
    file_options = {f.stem: str(f) for f in csv_files}
    
    selected_file = st.selectbox(
        "选择要分析的公司数据文件",
        options=list(file_options.keys()),
        help="选择之前搜索生成的公司数据文件"
    )
    
    # 目标客户画像输入
    st.subheader("🎯 目标客户画像")
    target_profile = st.text_area(
        "描述您的理想客户",
        value="""我们的目标客户是从事可再生能源业务的大中型企业，特别是：
- 太阳能设备制造商和分销商
- 清洁能源项目开发商
- 电池储能系统供应商
- 具有国际业务的企业
- 年营收1000万美元以上的公司""",
        height=150,
        help="请详细描述您的理想客户特征，AI将基于此进行匹配分析"
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
        "🚀 开始AI分析",
        type="primary",
        use_container_width=True
    )

with col2:
    st.subheader("📊 AI分析结果")
    
    # 结果显示区域
    results_container = st.container()
    
    if analyze_button:
        if not target_profile.strip():
            st.error("请输入目标客户画像描述")
            st.stop()
        
        # 加载数据
        file_path = file_options[selected_file]
        try:
            df = pd.read_csv(file_path)
            st.success(f"✅ 已加载 {len(df)} 家公司数据")
        except Exception as e:
            st.error(f"读取数据文件失败: {e}")
            st.stop()
        
        # 初始化AI分析器
        with st.spinner("🤖 正在初始化AI分析器..."):
            analyzer = AIAnalyzer(provider=selected_provider)
        
        # 创建进度条
        progress_bar = st.progress(0)
        status_text = st.empty()
        results_data = []
        
        # 批量分析
        def update_progress(current, total, company_name):
            progress = current / total
            progress_bar.progress(progress)
            status_text.text(f"正在分析: {company_name} ({current}/{total})")
        
        with st.spinner("🔍 正在进行AI分析..."):
            try:
                # 转换数据格式
                companies_data = df.to_dict('records')
                
                # 批量分析
                results = analyzer.batch_analyze_companies(
                    companies_data, 
                    target_profile, 
                    callback=update_progress
                )
                
                # 清空进度显示
                progress_bar.empty()
                status_text.empty()
                
                # 显示结果
                st.success("🎉 AI分析完成！")
                
                # 转换结果为DataFrame
                results_df = pd.DataFrame(results)
                
                # 保存结果
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"output/scored/ai_analysis_{selected_file}_{timestamp}.csv"
                os.makedirs("output/scored", exist_ok=True)
                results_df.to_csv(output_file, index=False, encoding='utf-8-sig')
                
                st.info(f"📄 分析结果已保存至: {output_file}")
                
                # 显示统计概览
                st.subheader("📈 分析概览")
                
                col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
                
                with col_stats1:
                    avg_score = results_df['final_score'].mean()
                    st.metric("平均得分", f"{avg_score:.1f}", help="所有公司的平均AI评分")
                
                with col_stats2:
                    high_score_count = len(results_df[results_df['final_score'] >= 70])
                    st.metric("高分客户", f"{high_score_count} 家", help="得分≥70的优质客户数量")
                
                with col_stats3:
                    max_score = results_df['final_score'].max()
                    st.metric("最高得分", f"{max_score:.1f}", help="单个客户的最高评分")
                
                with col_stats4:
                    confidence_high = len(results_df[results_df.get('confidence_level', 'medium') == 'high'])
                    st.metric("高置信度", f"{confidence_high} 家", help="AI分析置信度高的客户数量")
                
                # 得分分布图
                st.subheader("📊 得分分布分析")
                
                fig_dist = px.histogram(
                    results_df,
                    x='final_score',
                    nbins=20,
                    title="客户得分分布",
                    labels={'final_score': '综合得分', 'count': '客户数量'}
                )
                fig_dist.update_layout(showlegend=False)
                st.plotly_chart(fig_dist, use_container_width=True)
                
                # 维度雷达图（选择前5名客户）
                if 'dimension_scores' in results_df.columns:
                    st.subheader("🎯 TOP5客户维度分析")
                    
                    top5 = results_df.nlargest(5, 'final_score')
                    
                    # 解析维度得分
                    radar_data = []
                    dimensions = ['行业匹配度', '商业规模', '决策者可达性', '增长潜力']
                    
                    for _, row in top5.iterrows():
                        try:
                            if isinstance(row['dimension_scores'], str):
                                scores = json.loads(row['dimension_scores'])
                            else:
                                scores = row['dimension_scores']
                            
                            radar_data.append({
                                'company': row['company_name'][:20] + "..." if len(row['company_name']) > 20 else row['company_name'],
                                'industry_match': scores.get('industry_match', 0),
                                'business_scale': scores.get('business_scale', 0),
                                'decision_accessibility': scores.get('decision_accessibility', 0),
                                'growth_potential': scores.get('growth_potential', 0)
                            })
                        except:
                            continue
                    
                    if radar_data:
                        # 创建雷达图
                        fig_radar = go.Figure()
                        
                        for data in radar_data:
                            fig_radar.add_trace(go.Scatterpolar(
                                r=[data['industry_match'], data['business_scale'], 
                                   data['decision_accessibility'], data['growth_potential']],
                                theta=['行业匹配度', '商业规模', '决策者可达性', '增长潜力'],
                                fill='toself',
                                name=data['company']
                            ))
                        
                        fig_radar.update_layout(
                            polar=dict(
                                radialaxis=dict(
                                    visible=True,
                                    range=[0, 100]
                                )),
                            showlegend=True,
                            title="TOP5客户四维分析对比"
                        )
                        
                        st.plotly_chart(fig_radar, use_container_width=True)
                
                # 详细结果表格
                st.subheader("📋 详细分析结果")
                
                # 创建显示用的DataFrame
                display_df = results_df[['company_name', 'final_score', 'analysis_summary', 'tags']].copy()
                display_df['final_score'] = display_df['final_score'].round(1)
                display_df.columns = ['公司名称', '综合得分', '分析摘要', '智能标签']
                
                # 按得分排序
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
                
                display_df['状态'] = display_df['综合得分'].apply(score_color)
                display_df = display_df[['状态', '公司名称', '综合得分', '分析摘要', '智能标签']]
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "综合得分": st.column_config.ProgressColumn(
                            "综合得分",
                            help="AI评估的综合得分",
                            min_value=0,
                            max_value=100,
                            format="%.1f"
                        ),
                        "分析摘要": st.column_config.TextColumn(
                            "分析摘要",
                            width="large"
                        ),
                        "智能标签": st.column_config.TextColumn(
                            "智能标签", 
                            width="medium"
                        )
                    }
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
                        file_name=f"ai_analysis_results_{timestamp}.csv",
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
                        file_name=f"ai_analysis_results_{timestamp}.json",
                        mime="application/json"
                    )
                
            except Exception as e:
                st.error(f"AI分析过程中出错: {e}")
                st.exception(e)
        
    else:
        with results_container:
            st.info("👈 请在左侧配置分析参数，然后点击开始AI分析按钮")
            
            # 显示功能介绍
            st.markdown("""
            ### 🚀 AI分析功能亮点
            
            **🎯 四维智能评分体系：**
            - **行业匹配度** (40% 权重) - AI评估业务契合度
            - **商业规模** (25% 权重) - 智能分析购买力和规模  
            - **决策者可达性** (20% 权重) - 关键人员接触难易度
            - **增长潜力** (15% 权重) - 未来合作机会预测
            
            **🧠 深度AI洞察：**
            - 个性化分析摘要
            - 关键商业洞察  
            - 风险因素识别
            - 合作机会发现
            - 行动建议生成
            
            **📊 可视化分析报告：**
            - 得分分布统计
            - 维度雷达图对比
            - 智能标签分类
            - 交互式数据表格
            """)

# 侧边栏附加信息
st.sidebar.markdown("---")
st.sidebar.subheader("💡 使用提示")
st.sidebar.markdown("""
**最佳实践：**
1. 详细描述目标客户画像
2. 选择合适的AI模型
3. 关注高置信度结果
4. 结合人工判断做决策

**评分说明：**
- 🟢 80+ 分：优质客户
- 🟡 60-79 分：潜力客户  
- 🟠 40-59 分：一般客户
- 🔴 <40 分：低匹配度
""")

st.sidebar.markdown("---")
st.sidebar.info("💰 **提示**: AI分析会消耗LLM API调用额度，建议合理使用。")