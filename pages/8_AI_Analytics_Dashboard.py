#!/usr/bin/env python3
"""
AI分析仪表板 - 智能搜索结果的可视化分析
提供深度的数据洞察和趋势分析
"""

import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os
import glob
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from components.common import check_api_keys, display_api_status
from components.language_manager import get_language_manager, t

# 页面配置
st.set_page_config(
    page_title=t('ai_dashboard.title'),
    page_icon="📊", 
    layout="wide"
)

# 自定义CSS
st.markdown("""
<style>
.metric-container {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 0.5rem;
    text-align: center;
    margin: 0.5rem 0;
}
.insight-box {
    background-color: #e3f2fd;
    padding: 1rem;
    border-left: 4px solid #2196f3;
    margin: 1rem 0;
    border-radius: 0.25rem;
}
.recommendation-box {
    background-color: #e8f5e8;
    padding: 1rem;
    border-left: 4px solid #4caf50;
    margin: 1rem 0;
    border-radius: 0.25rem;
}
</style>
""", unsafe_allow_html=True)

def load_search_results():
    """加载搜索结果数据"""
    output_dir = Path("output")
    results_data = []
    
    # 加载简化版搜索结果
    simplified_pattern = output_dir / "*simplified_results.json"
    for file_path in glob.glob(str(simplified_pattern)):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('success') and data.get('final_recommendations'):
                    data['file_path'] = file_path
                    data['search_type'] = 'intelligent'
                    results_data.append(data)
        except Exception as e:
            st.warning(f"无法加载文件 {file_path}: {e}")
    
    # 加载传统搜索结果（如果需要的话）
    # 这里可以添加加载其他格式搜索结果的代码
    
    return results_data

def analyze_search_trends(results_data):
    """分析搜索趋势"""
    if not results_data:
        return None
    
    trend_data = []
    for result in results_data:
        execution_summary = result.get('execution_summary', {})
        recommendations = result.get('final_recommendations', [])
        
        # 提取搜索时间
        timestamp_str = result.get('timestamp', '')
        try:
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                # 从文件路径提取时间戳
                file_path = result.get('file_path', '')
                if 'search_' in file_path:
                    ts_part = file_path.split('search_')[1].split('_')[0]
                    timestamp = datetime.fromtimestamp(int(ts_part))
                else:
                    timestamp = datetime.now()
        except:
            timestamp = datetime.now()
        
        trend_data.append({
            'timestamp': timestamp,
            'company_count': len(recommendations),
            'execution_time': execution_summary.get('total_time', 0),
            'avg_score': sum(c.get('overall_score', 0) for c in recommendations) / len(recommendations) if recommendations else 0,
            'search_id': result.get('search_id', 'unknown')
        })
    
    return pd.DataFrame(trend_data)

def create_score_distribution_chart(results_data):
    """创建评分分布图表"""
    all_scores = []
    all_tiers = []
    
    for result in results_data:
        recommendations = result.get('final_recommendations', [])
        for company in recommendations:
            all_scores.append(company.get('overall_score', 0))
            all_tiers.append(company.get('score_tier', 'unknown'))
    
    if not all_scores:
        return None, None
    
    # 评分分布直方图
    fig_hist = px.histogram(
        x=all_scores,
        nbins=20,
        title="公司评分分布",
        labels={'x': '评分', 'y': '公司数量'},
        color_discrete_sequence=['#1f77b4']
    )
    fig_hist.update_layout(showlegend=False)
    
    # 等级分布饼图
    tier_counts = pd.Series(all_tiers).value_counts()
    fig_pie = px.pie(
        values=tier_counts.values,
        names=tier_counts.index,
        title="质量等级分布",
        color_discrete_map={
            'excellent': '#28a745',
            'very_good': '#17a2b8', 
            'good': '#ffc107',
            'acceptable': '#6c757d'
        }
    )
    
    return fig_hist, fig_pie

def create_performance_metrics_chart(trend_df):
    """创建性能指标图表"""
    if trend_df.empty:
        return None
    
    # 创建子图
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('搜索效率趋势', '结果质量趋势', '搜索量趋势', '执行时间分布'),
        specs=[[{"secondary_y": True}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # 搜索效率 (执行时间 vs 结果数量)
    fig.add_trace(
        go.Scatter(
            x=trend_df['timestamp'],
            y=trend_df['execution_time'],
            mode='lines+markers',
            name='执行时间(秒)',
            line=dict(color='#ff7f0e')
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=trend_df['timestamp'],
            y=trend_df['company_count'],
            mode='lines+markers',
            name='找到公司数',
            line=dict(color='#1f77b4'),
            yaxis='y2'
        ),
        row=1, col=1
    )
    
    # 结果质量趋势
    fig.add_trace(
        go.Scatter(
            x=trend_df['timestamp'],
            y=trend_df['avg_score'],
            mode='lines+markers',
            name='平均评分',
            line=dict(color='#2ca02c')
        ),
        row=1, col=2
    )
    
    # 搜索量趋势
    daily_searches = trend_df.groupby(trend_df['timestamp'].dt.date).size().reset_index()
    daily_searches.columns = ['date', 'count']
    
    fig.add_trace(
        go.Bar(
            x=daily_searches['date'],
            y=daily_searches['count'],
            name='每日搜索次数',
            marker_color='#d62728'
        ),
        row=2, col=1
    )
    
    # 执行时间分布
    fig.add_trace(
        go.Histogram(
            x=trend_df['execution_time'],
            nbinsx=10,
            name='执行时间分布',
            marker_color='#9467bd'
        ),
        row=2, col=2
    )
    
    fig.update_layout(
        height=800,
        showlegend=False,
        title_text="AI智能搜索性能分析"
    )
    
    return fig

def generate_insights(results_data, trend_df):
    """生成AI洞察"""
    insights = []
    
    if not results_data:
        return ["暂无数据可供分析"]
    
    # 基础统计
    total_searches = len(results_data)
    total_companies = sum(len(r.get('final_recommendations', [])) for r in results_data)
    avg_companies_per_search = total_companies / total_searches if total_searches > 0 else 0
    
    insights.append(f"📊 已执行 {total_searches} 次智能搜索，累计发现 {total_companies} 家潜在客户")
    insights.append(f"⚡ 平均每次搜索找到 {avg_companies_per_search:.1f} 家公司")
    
    # 性能分析
    if not trend_df.empty:
        avg_exec_time = trend_df['execution_time'].mean()
        avg_score = trend_df['avg_score'].mean()
        
        insights.append(f"🚀 平均搜索执行时间: {avg_exec_time:.1f}秒")
        insights.append(f"🎯 平均公司评分: {avg_score:.1f}分")
        
        # 效率分析
        if avg_exec_time < 60:
            insights.append("✅ 搜索效率优秀，响应时间在理想范围内")
        elif avg_exec_time < 120:
            insights.append("⚠️ 搜索效率良好，考虑优化以提升用户体验")
        else:
            insights.append("⚠️ 搜索执行时间较长，建议优化多智能体协作流程")
    
    # 质量分析
    all_scores = []
    excellent_count = 0
    
    for result in results_data:
        recommendations = result.get('final_recommendations', [])
        for company in recommendations:
            score = company.get('overall_score', 0)
            all_scores.append(score)
            if company.get('score_tier') == 'excellent':
                excellent_count += 1
    
    if all_scores:
        high_quality_ratio = len([s for s in all_scores if s >= 8]) / len(all_scores)
        excellent_ratio = excellent_count / len(all_scores)
        
        if excellent_ratio > 0.3:
            insights.append(f"🏆 发现高质量客户比例很高 ({excellent_ratio:.1%})，搜索策略效果优秀")
        elif high_quality_ratio > 0.5:
            insights.append(f"✨ 高评分客户占比 {high_quality_ratio:.1%}，整体搜索质量良好")
        else:
            insights.append("💡 建议优化搜索关键词或筛选条件以提高匹配质量")
    
    return insights

def generate_recommendations(results_data, trend_df):
    """生成改进建议"""
    recommendations = []
    
    if not results_data:
        return ["开始使用AI智能搜索以获取改进建议"]
    
    # 基于搜索频率的建议
    total_searches = len(results_data)
    if total_searches < 5:
        recommendations.append("🔥 建议多尝试不同类型的搜索需求，以充分体验AI智能搜索的能力")
    
    # 基于执行时间的建议
    if not trend_df.empty:
        avg_exec_time = trend_df['execution_time'].mean()
        if avg_exec_time > 90:
            recommendations.append("⚡ 考虑在网络条件良好时进行搜索，或优化API调用超时设置")
    
    # 基于结果质量的建议
    all_scores = []
    for result in results_data:
        recommendations_list = result.get('final_recommendations', [])
        all_scores.extend([c.get('overall_score', 0) for c in recommendations_list])
    
    if all_scores:
        avg_score = sum(all_scores) / len(all_scores)
        if avg_score < 7:
            recommendations.append("🎯 尝试使用更具体的需求描述，包含详细的产品规格、价格范围和地理位置")
            recommendations.append("💡 在需求描述中加入行业关键词和技术要求，有助于提高匹配精度")
    
    # 通用建议
    recommendations.extend([
        "📝 保存高质量的搜索结果，建立潜在客户数据库",
        "🔄 定期重新搜索以发现新的潜在客户",
        "📊 关注评分维度，重点联系匹配度高的公司",
        "🤝 结合联系信息提取功能，建立完整的客户档案"
    ])
    
    return recommendations[:5]  # 限制建议数量

def main():
    """主界面"""
    st.title(f"📊 {t('ai_dashboard.title')}")
    st.markdown(t('ai_dashboard.subtitle'))
    
    # 检查API状态
    display_api_status()
    
    # 加载数据
    with st.spinner("正在加载搜索结果数据..."):
        results_data = load_search_results()
        trend_df = analyze_search_trends(results_data) if results_data else pd.DataFrame()
    
    if not results_data:
        st.warning("📝 暂无AI智能搜索结果数据")
        st.info("💡 请先使用 **AI智能搜索** 功能进行搜索，然后回到此页面查看分析结果")
        
        if st.button("🔍 前往AI智能搜索"):
            st.switch_page("pages/7_🔍_Intelligent_Search.py")
        
        st.stop()
    
    # 概览指标
    st.markdown("## 📈 核心指标概览")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_searches = len(results_data)
    total_companies = sum(len(r.get('final_recommendations', [])) for r in results_data)
    avg_exec_time = trend_df['execution_time'].mean() if not trend_df.empty else 0
    avg_score = trend_df['avg_score'].mean() if not trend_df.empty else 0
    
    with col1:
        st.metric("搜索次数", total_searches, help="总的AI智能搜索执行次数")
    
    with col2:
        st.metric("发现公司", total_companies, help="累计发现的潜在客户公司数量")
    
    with col3:
        st.metric("平均执行时间", f"{avg_exec_time:.1f}秒", help="AI智能体协作的平均用时")
    
    with col4:
        st.metric("平均评分", f"{avg_score:.1f}分", help="AI评分的平均水平")
    
    # 标签页
    tab1, tab2, tab3, tab4 = st.tabs(["📊 数据可视化", "🔍 深度分析", "💡 AI洞察", "📈 趋势预测"])
    
    with tab1:
        data_visualization_tab(results_data, trend_df)
    
    with tab2:
        deep_analysis_tab(results_data, trend_df)
    
    with tab3:
        ai_insights_tab(results_data, trend_df)
    
    with tab4:
        trend_prediction_tab(results_data, trend_df)

def data_visualization_tab(results_data, trend_df):
    """数据可视化标签页"""
    st.markdown("### 📊 搜索结果可视化分析")
    
    # 评分分布图表
    fig_hist, fig_pie = create_score_distribution_chart(results_data)
    
    if fig_hist and fig_pie:
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            st.plotly_chart(fig_pie, use_container_width=True)
    
    # 性能指标图表
    if not trend_df.empty:
        fig_perf = create_performance_metrics_chart(trend_df)
        if fig_perf:
            st.plotly_chart(fig_perf, use_container_width=True)

def deep_analysis_tab(results_data, trend_df):
    """深度分析标签页"""
    st.markdown("### 🔍 深度数据分析")
    
    if trend_df.empty:
        st.info("数据不足，无法进行深度分析")
        return
    
    # 详细统计表
    st.markdown("#### 📋 搜索记录详细统计")
    
    analysis_df = trend_df.copy()
    analysis_df['search_date'] = analysis_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
    analysis_df['efficiency_score'] = (analysis_df['company_count'] / analysis_df['execution_time'] * 10).round(2)
    
    display_df = analysis_df[['search_date', 'company_count', 'execution_time', 'avg_score', 'efficiency_score']]
    display_df.columns = ['搜索时间', '找到公司数', '执行时间(秒)', '平均评分', '效率评分']
    
    st.dataframe(display_df, use_container_width=True)
    
    # 相关性分析
    st.markdown("#### 🔗 指标相关性分析")
    
    corr_matrix = trend_df[['company_count', 'execution_time', 'avg_score']].corr()
    
    fig_heatmap = px.imshow(
        corr_matrix,
        text_auto=True,
        aspect="auto",
        title="性能指标相关性热力图",
        color_continuous_scale='RdBu_r'
    )
    
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # 异常值检测
    st.markdown("#### ⚠️ 异常搜索检测")
    
    # 检测执行时间异常
    q75, q25 = trend_df['execution_time'].quantile([0.75, 0.25])
    iqr = q75 - q25
    outlier_threshold = q75 + 1.5 * iqr
    
    outliers = trend_df[trend_df['execution_time'] > outlier_threshold]
    
    if not outliers.empty:
        st.warning(f"检测到 {len(outliers)} 次执行时间异常的搜索")
        st.dataframe(
            outliers[['timestamp', 'execution_time', 'company_count']].rename(columns={
                'timestamp': '时间',
                'execution_time': '执行时间(秒)',
                'company_count': '公司数量'
            })
        )
    else:
        st.success("✅ 所有搜索的执行时间都在正常范围内")

def ai_insights_tab(results_data, trend_df):
    """AI洞察标签页"""
    st.markdown("### 💡 AI智能洞察")
    
    # 生成洞察
    insights = generate_insights(results_data, trend_df)
    recommendations = generate_recommendations(results_data, trend_df)
    
    # 显示洞察
    st.markdown("#### 🔍 数据洞察")
    for insight in insights:
        st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)
    
    # 显示建议
    st.markdown("#### 🎯 优化建议")
    for recommendation in recommendations:
        st.markdown(f'<div class="recommendation-box">{recommendation}</div>', unsafe_allow_html=True)
    
    # 成功案例分析
    if results_data:
        st.markdown("#### 🏆 最佳搜索案例")
        
        best_searches = []
        for result in results_data:
            recommendations_list = result.get('final_recommendations', [])
            if recommendations_list:
                excellent_count = sum(1 for c in recommendations_list if c.get('score_tier') == 'excellent')
                excellent_ratio = excellent_count / len(recommendations_list)
                
                best_searches.append({
                    'search_id': result.get('search_id', 'unknown'),
                    'company_count': len(recommendations_list),
                    'excellent_ratio': excellent_ratio,
                    'avg_score': sum(c.get('overall_score', 0) for c in recommendations_list) / len(recommendations_list),
                    'execution_time': result.get('execution_summary', {}).get('total_time', 0)
                })
        
        if best_searches:
            # 找出最佳搜索
            best_search = max(best_searches, key=lambda x: (x['excellent_ratio'], x['avg_score']))
            
            st.success(f"""
            🎉 **最佳搜索案例**: {best_search['search_id']}
            - 找到公司: {best_search['company_count']} 家
            - 优秀公司比例: {best_search['excellent_ratio']:.1%}
            - 平均评分: {best_search['avg_score']:.1f}分
            - 执行时间: {best_search['execution_time']:.1f}秒
            """)

def trend_prediction_tab(results_data, trend_df):
    """趋势预测标签页"""
    st.markdown("### 📈 趋势预测与建议")
    
    if trend_df.empty or len(trend_df) < 3:
        st.info("数据点不足，无法进行趋势预测。请多进行几次搜索后再查看此功能。")
        return
    
    # 简单的趋势分析
    st.markdown("#### 📊 性能趋势分析")
    
    # 计算趋势
    recent_searches = trend_df.tail(3)
    older_searches = trend_df.head(max(1, len(trend_df) - 3))
    
    recent_avg_time = recent_searches['execution_time'].mean()
    older_avg_time = older_searches['execution_time'].mean()
    
    recent_avg_score = recent_searches['avg_score'].mean()
    older_avg_score = older_searches['avg_score'].mean()
    
    # 效率趋势
    if recent_avg_time < older_avg_time:
        efficiency_trend = "📈 搜索效率正在提升"
        efficiency_color = "green"
    elif recent_avg_time > older_avg_time:
        efficiency_trend = "📉 搜索效率有所下降"
        efficiency_color = "orange"
    else:
        efficiency_trend = "➡️ 搜索效率保持稳定"
        efficiency_color = "blue"
    
    # 质量趋势
    if recent_avg_score > older_avg_score:
        quality_trend = "📈 搜索质量正在提升"
        quality_color = "green"
    elif recent_avg_score < older_avg_score:
        quality_trend = "📉 搜索质量有所下降"
        quality_color = "orange"
    else:
        quality_trend = "➡️ 搜索质量保持稳定"
        quality_color = "blue"
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**执行效率趋势**: :{efficiency_color}[{efficiency_trend}]")
        st.metric(
            "最近3次平均执行时间", 
            f"{recent_avg_time:.1f}秒",
            delta=f"{recent_avg_time - older_avg_time:.1f}秒"
        )
    
    with col2:
        st.markdown(f"**结果质量趋势**: :{quality_color}[{quality_trend}]")
        st.metric(
            "最近3次平均评分",
            f"{recent_avg_score:.1f}分", 
            delta=f"{recent_avg_score - older_avg_score:.1f}分"
        )
    
    # 使用建议
    st.markdown("#### 💡 基于趋势的使用建议")
    
    suggestions = []
    
    if recent_avg_time > 90:
        suggestions.append("⚡ 建议在网络环境良好时进行搜索，或考虑分时段使用")
    
    if recent_avg_score < 7:
        suggestions.append("🎯 尝试更精确的需求描述，包含具体的技术规格和地理位置")
    
    if len(trend_df) > 5 and trend_df['company_count'].std() > 5:
        suggestions.append("📊 搜索结果数量波动较大，建议标准化搜索关键词")
    
    suggestions.append("🔄 建议定期搜索以发现市场新变化")
    suggestions.append("📈 持续使用可以帮助AI更好地理解您的需求偏好")
    
    for suggestion in suggestions:
        st.info(suggestion)
    
    # 预测下次搜索表现
    st.markdown("#### 🔮 下次搜索表现预测")
    
    predicted_time = recent_avg_time
    predicted_score = recent_avg_score
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("预测执行时间", f"{predicted_time:.1f}秒")
    
    with col2:
        st.metric("预测平均评分", f"{predicted_score:.1f}分")
    
    with col3:
        confidence = min(90, len(trend_df) * 15)  # 基于历史数据量的置信度
        st.metric("预测置信度", f"{confidence}%")

if __name__ == "__main__":
    main()