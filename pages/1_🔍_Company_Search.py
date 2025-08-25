"""
Company Search Page - Streamlit
Search for companies by industry, region, or custom queries with integrated AI analysis
"""
import streamlit as st
import pandas as pd
import os
import json
import sys
from pathlib import Path
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.company_search import CompanySearcher
from components.common import (
    display_api_status, 
    show_usage_tips, 
    create_download_buttons,
    display_metrics,
    format_dataframe_columns,
    check_api_keys
)
from integration_guide import AIAnalyzerManager

st.set_page_config(page_title="Company Search", page_icon="🔍", layout="wide")

st.title("🔍 Smart Company Search")
st.markdown("Search for target companies by industry, region, or custom queries")

# Initialize searcher
# Temporarily disable cache to ensure new code is loaded
# @st.cache_resource
def get_searcher():
    try:
        return CompanySearcher()
    except ValueError as e:
        st.error(f"Error initializing searcher: {str(e)}")
        return None

searcher = get_searcher()

if not searcher:
    st.error("Cannot initialize company searcher. Please check your API configuration.")
    st.stop()

# Search form
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Search Criteria")
    
    # Search mode selection
    search_mode = st.radio(
        "Search Mode",
        ["General Search", "LinkedIn Company Search", "Custom Query"],
        help="Choose different search modes"
    )
    
    # Input fields based on mode
    if search_mode == "Custom Query":
        custom_query = st.text_area(
            "Custom Search Query",
            placeholder="Enter complete search query, e.g.: renewable energy companies California",
            height=100
        )
        industry = None
        region = None
    else:
        custom_query = None
        industry = st.text_input(
            "Industry Keywords",
            placeholder="e.g.: solar energy, software, manufacturing"
        )
        
        region = st.text_input(
            "Region/Location",
            placeholder="e.g.: California, New York, London"
        )
        
        keywords = st.text_input(
            "Additional Keywords (Optional)",
            placeholder="Separate multiple keywords with commas",
            help="Add extra search keywords to refine results"
        )
    
    # Advanced options
    with st.expander("Advanced Options"):
        gl = st.selectbox(
            "Target Market",
            options=["us", "uk", "cn", "de", "fr", "jp", "au", "ca", "in", "br"],
            index=0,
            help="Select geographic preference for search"
        )
        
        num_results = st.slider(
            "Number of Results",
            min_value=10,
            max_value=100,
            value=30,
            step=10,
            help="Number of search results to return"
        )
    
    # Search button
    search_button = st.button("🚀 Start Search", type="primary", use_container_width=True)

# Results display area
with col2:
    st.subheader("Search Results")
    
    if search_button:
        # Validate input
        if search_mode == "Custom Query" and not custom_query:
            st.error("Please enter a custom query")
        elif search_mode != "Custom Query" and not industry and not region:
            st.error("Please enter at least industry or region")
        else:
            # Execute search
            with st.spinner("Searching for companies..."):
                # Prepare parameters
                search_params = {
                    "search_mode": "linkedin" if search_mode == "LinkedIn Company Search" else "general",
                    "gl": gl,
                    "num_results": num_results
                }
                
                if search_mode == "Custom Query":
                    search_params["custom_query"] = custom_query
                else:
                    search_params["industry"] = industry
                    search_params["region"] = region
                    if 'keywords' in locals() and keywords:
                        search_params["keywords"] = [k.strip() for k in keywords.split(",")]
                
                # Execute search
                result = searcher.search_companies(**search_params)
                
                if result["success"]:
                    companies = result["data"]
                    
                    if companies:
                        st.success(f"✅ Found {len(companies)} companies!")
                        
                        # Convert to DataFrame and save to session state
                        df = pd.DataFrame(companies)
                        st.session_state['search_results'] = df
                        st.session_state['search_params'] = search_params
                        
                        # Display statistics
                        metrics = {
                            "Total Companies": len(companies),
                            "Unique Domains": df['domain'].dropna().nunique() if 'domain' in df else 0,
                            "LinkedIn Profiles": df['linkedin'].notna().sum() if 'linkedin' in df else 0
                        }
                        display_metrics(metrics)
                        
                        # Display data table
                        st.dataframe(
                            df,
                            use_container_width=True,
                            height=400,
                            column_config=format_dataframe_columns(df),
                            hide_index=True
                        )
                        
                        # Download options
                        st.divider()
                        st.subheader("📥 Download Results")
                        
                        filename_prefix = f"companies_{search_mode.lower().replace(' ', '_')}_{gl}"
                        create_download_buttons(df, filename_prefix, "both")
                        
                        # Show save location
                        if result.get("output_file"):
                            st.info(f"💾 Results saved to: `{result['output_file']}`")
                    else:
                        st.warning("No companies found matching your criteria")
                        if 'search_results' in st.session_state:
                            del st.session_state['search_results']
                else:
                    st.error(f"❌ Search failed: {result['error']}")
                    if 'search_results' in st.session_state:
                        del st.session_state['search_results']

# AI Analysis Section - Show only if there are search results
if 'search_results' in st.session_state:
    st.divider()
    st.header("🤖 AI智能分析")
    st.markdown("对搜索结果进行AI深度分析，评估客户匹配度和商业价值")
    
    # Check API configuration
    api_status = check_api_keys()
    llm_available = any([
        api_status.get('OPENAI_API_KEY', False),
        api_status.get('ANTHROPIC_API_KEY', False), 
        api_status.get('GOOGLE_API_KEY', False),
        api_status.get('ARK_API_KEY', False)
    ])
    
    if not llm_available:
        st.warning("""
        ⚠️ **需要配置LLM API才能使用AI分析功能**
        
        请在 `.env` 文件中配置以下任一API：
        - OpenAI API Key / Anthropic API Key / Google API Key / Huoshan API Key
        """)
    else:
        # AI Analysis Configuration
        col_ai1, col_ai2 = st.columns([1, 2])
        
        with col_ai1:
            st.subheader("🎯 分析配置")
            
            # Target customer profile input
            target_profile = st.text_area(
                "目标客户画像",
                value="""我们的目标客户是从事可再生能源业务的大中型企业，特别是：
- 太阳能设备制造商和分销商
- 清洁能源项目开发商
- 电池储能系统供应商
- 具有国际业务的企业
- 年营收1000万美元以上的公司""",
                height=150,
                help="请详细描述您的理想客户特征，AI将基于此进行匹配分析"
            )
            
            # LLM provider selection
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
            
            # Analysis button
            analyze_button = st.button(
                "🚀 开始AI分析",
                type="primary",
                use_container_width=True
            )
        
        with col_ai2:
            st.subheader("📊 AI分析结果")
            
            if analyze_button:
                if not target_profile.strip():
                    st.error("请输入目标客户画像描述")
                else:
                    # Get search results from session state
                    df = st.session_state['search_results'].copy()
                    search_params = st.session_state.get('search_params', {})
                    
                    st.success(f"✅ 准备分析 {len(df)} 家公司")
                    
                    # Initialize AI analyzer with optimized version
                    with st.spinner("🤖 正在初始化AI分析器..."):
                        try:
                            analyzer = AIAnalyzerManager(
                                provider=selected_provider,
                                use_optimized=True,
                                max_concurrent=6,
                                enable_cache=True
                            )
                            
                            # Show analyzer info
                            analyzer_info = analyzer.get_analyzer_info()
                            if analyzer_info['type'] == 'optimized':
                                st.info("⚡ 使用优化版AI分析器，性能提升5-10倍")
                            
                        except Exception as e:
                            st.error(f"初始化AI分析器失败: {e}")
                            st.stop()
                    
                    # Create progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Progress callback function
                    def update_progress(current, total, company_name):
                        progress = current / total
                        progress_bar.progress(progress)
                        status_text.text(f"正在分析: {company_name} ({current}/{total})")
                    
                    # Execute AI analysis
                    with st.spinner("🔍 正在进行AI分析..."):
                        try:
                            # Convert DataFrame to list of dicts
                            companies_data = df.to_dict('records')
                            
                            # Batch analyze companies
                            results = analyzer.batch_analyze_companies(
                                companies_data, 
                                target_profile, 
                                callback=update_progress
                            )
                            
                            # Clear progress display
                            progress_bar.empty()
                            status_text.empty()
                            
                            # Display results
                            st.success("🎉 AI分析完成！")
                            
                            # Convert results to DataFrame
                            results_df = pd.DataFrame(results)
                            
                            # Show performance stats if available
                            if hasattr(analyzer, 'get_performance_stats'):
                                stats = analyzer.get_performance_stats()
                                if stats:
                                    with st.expander("📈 性能统计", expanded=False):
                                        st.json(stats)
                            
                            # Save results
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            search_type = search_params.get('search_mode', 'general')
                            industry = search_params.get('industry', 'unknown')
                            region = search_params.get('region', 'unknown')
                            
                            output_dir = Path("output/scored")
                            output_dir.mkdir(exist_ok=True)
                            
                            output_file = output_dir / f"ai_analysis_{search_type}_{industry}_{region}_{timestamp}.csv"
                            results_df.to_csv(output_file, index=False, encoding='utf-8-sig')
                            
                            st.info(f"📄 分析结果已保存至: {output_file}")
                            
                            # Display analysis statistics
                            st.subheader("📈 分析概览")
                            
                            col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
                            
                            with col_stats1:
                                avg_score = results_df['final_score'].mean()
                                st.metric("平均得分", f"{avg_score:.1f}")
                            
                            with col_stats2:
                                high_potential = len(results_df[results_df['final_score'] >= 70])
                                st.metric("高潜力客户", f"{high_potential} 家")
                            
                            with col_stats3:
                                medium_potential = len(results_df[(results_df['final_score'] >= 50) & (results_df['final_score'] < 70)])
                                st.metric("中等潜力", f"{medium_potential} 家")
                            
                            with col_stats4:
                                total_analyzed = len(results_df)
                                st.metric("总分析数量", f"{total_analyzed} 家")
                            
                            # Display results table
                            st.subheader("📋 详细分析结果")
                            
                            # Sort by final score
                            results_df_sorted = results_df.sort_values('final_score', ascending=False)
                            
                            # Display interactive table
                            st.dataframe(
                                results_df_sorted,
                                use_container_width=True,
                                height=400,
                                column_config={
                                    "final_score": st.column_config.NumberColumn(
                                        "最终得分",
                                        min_value=0,
                                        max_value=100,
                                        format="%.1f"
                                    ),
                                    "industry_match": st.column_config.NumberColumn(
                                        "行业匹配",
                                        min_value=0,
                                        max_value=100,
                                        format="%.1f"
                                    ),
                                    "business_scale": st.column_config.NumberColumn(
                                        "商业规模",
                                        min_value=0,
                                        max_value=100,
                                        format="%.1f"
                                    )
                                },
                                hide_index=True
                            )
                            
                            # Visualization
                            st.subheader("📊 分析可视化")
                            
                            col_viz1, col_viz2 = st.columns(2)
                            
                            with col_viz1:
                                # Score distribution histogram
                                fig_hist = px.histogram(
                                    results_df, 
                                    x='final_score', 
                                    nbins=10,
                                    title='客户得分分布',
                                    labels={'final_score': '最终得分', 'count': '客户数量'}
                                )
                                st.plotly_chart(fig_hist, use_container_width=True)
                            
                            with col_viz2:
                                # Top companies bar chart
                                top_companies = results_df_sorted.head(10)
                                fig_bar = px.bar(
                                    top_companies,
                                    y='company_name',
                                    x='final_score',
                                    orientation='h',
                                    title='Top 10 高分客户',
                                    labels={'final_score': '最终得分', 'company_name': '公司名称'}
                                )
                                fig_bar.update_layout(height=400)
                                st.plotly_chart(fig_bar, use_container_width=True)
                            
                            # Download analysis results
                            st.subheader("📥 下载分析结果")
                            
                            # Create download buttons for analysis results
                            import json as json_lib
                            csv_data = results_df_sorted.to_csv(index=False, encoding='utf-8-sig')
                            json_data = json_lib.dumps(results_df_sorted.to_dict('records'), ensure_ascii=False, indent=2)
                            
                            col_dl1, col_dl2 = st.columns(2)
                            
                            with col_dl1:
                                st.download_button(
                                    label="📄 下载CSV格式",
                                    data=csv_data,
                                    file_name=f"ai_analysis_results_{timestamp}.csv",
                                    mime="text/csv"
                                )
                            
                            with col_dl2:
                                st.download_button(
                                    label="📄 下载JSON格式",
                                    data=json_data,
                                    file_name=f"ai_analysis_results_{timestamp}.json",
                                    mime="application/json"
                                )
                        
                        except Exception as e:
                            st.error(f"❌ AI分析失败: {e}")
                            import traceback
                            st.error(f"错误详情: {traceback.format_exc()}")
                            
                            # Clear progress display on error
                            progress_bar.empty()
                            status_text.empty()

# Sidebar content
with st.sidebar:
    # API status
    display_api_status()
    
    # Usage tips
    show_usage_tips("company_search")
    
    # Recent searches (if output directory exists)
    st.divider()
    st.header("📁 Recent Searches")
    
    company_dir = os.path.join("output", "company")
    if os.path.exists(company_dir):
        csv_files = [f for f in os.listdir(company_dir) if f.endswith('.csv')]
        csv_files.sort(key=lambda x: os.path.getmtime(os.path.join(company_dir, x)), reverse=True)
        
        if csv_files:
            recent_files = csv_files[:5]  # Show last 5 files
            for file in recent_files:
                file_path = os.path.join(company_dir, file)
                file_size = os.path.getsize(file_path) / 1024  # Convert to KB
                st.markdown(f"📄 {file[:30]}... ({file_size:.1f} KB)")
        else:
            st.info("No search results yet")