"""
Employee Search Page - Streamlit
Search for employees and decision makers in companies with integrated AI analysis
"""
import streamlit as st
import pandas as pd
import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

from components.common import (
    display_api_status,
    show_usage_tips,
    create_download_buttons,
    display_metrics,
    check_api_keys
)

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from integration_guide import EmployeeAIAnalyzerManager

st.set_page_config(page_title="Employee Search", page_icon="👥", layout="wide")

st.title("👥 Employee & Decision Maker Search")
st.markdown("Find key employees and decision makers in target companies")

# Import refactored employee search module
try:
    from core.employee_search import EmployeeSearcher
    search_available = True
except ImportError as e:
    st.error(f"Error importing employee search module: {str(e)}")
    search_available = False

# Main content
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Search Criteria")
    
    # Input method
    input_method = st.radio(
        "Input Method",
        ["Single Company", "Company List (CSV)"],
        help="Choose how to specify target companies"
    )
    
    if input_method == "Single Company":
        company_name = st.text_input(
            "Company Name",
            placeholder="e.g., Tesla, Microsoft, Apple",
            help="Enter the name of the company"
        )
        
    else:
        # CSV file selection from company search results
        company_dir = os.path.join("output", "company")
        if os.path.exists(company_dir):
            csv_files = [f for f in os.listdir(company_dir) if f.endswith('.csv')]
            if csv_files:
                selected_file = st.selectbox(
                    "Select Company List",
                    options=csv_files,
                    help="Choose from previous company search results"
                )
                
                # Preview selected file
                if selected_file:
                    file_path = os.path.join(company_dir, selected_file)
                    df_preview = pd.read_csv(file_path)
                    st.info(f"Selected file contains {len(df_preview)} companies")
                    
                    # Select company name column
                    name_columns = df_preview.columns.tolist()
                    company_column = st.selectbox(
                        "Company Name Column",
                        options=name_columns,
                        index=name_columns.index("name") if "name" in name_columns else 0
                    )
            else:
                st.warning("No company files found. Please run a company search first.")
                selected_file = None
        else:
            st.warning("No company directory found.")
            selected_file = None
    
    # Position/Title search
    position = st.text_input(
        "Position/Title",
        placeholder="e.g., CEO, Sales Director, Marketing Manager",
        help="Specify the job title or position to search for"
    )
    
    # Location filters
    with st.expander("Location Filters (Optional)"):
        location = st.text_input(
            "City/State",
            placeholder="e.g., San Francisco, California",
            help="Filter by location"
        )
        
        country = st.text_input(
            "Country",
            placeholder="e.g., United States, UK",
            help="Filter by country"
        )
    
    # Advanced options
    with st.expander("Advanced Options"):
        gl = st.selectbox(
            "Search Region",
            options=["us", "uk", "cn", "de", "fr", "jp", "au", "ca", "in", "br"],
            index=0,
            help="Geographic region for search"
        )
        
        num_results = st.slider(
            "Results per Company",
            min_value=5,
            max_value=50,
            value=20,
            step=5,
            help="Number of employee results per company"
        )
    
    # Search button
    search_button = st.button("🔍 Search Employees", type="primary", use_container_width=True)

# Results area
with col2:
    st.subheader("Search Results")
    
    if search_button and search_available:
        # Validate input
        companies_to_search = []
        
        if input_method == "Single Company":
            if company_name and position:
                companies_to_search = [company_name]
            else:
                st.error("Please enter both company name and position")
                
        else:
            if selected_file and position:
                file_path = os.path.join(company_dir, selected_file)
                df_companies = pd.read_csv(file_path)
                if 'company_column' in locals():
                    companies_to_search = df_companies[company_column].dropna().tolist()
                    # Limit for demo
                    if len(companies_to_search) > 5:
                        st.warning(f"Demo mode: Searching first 5 companies only")
                        companies_to_search = companies_to_search[:5]
                else:
                    st.error("Please select a company name column")
            else:
                st.error("Please select a file and enter a position")
        
        if companies_to_search:
            # Initialize search
            with st.spinner(f"Searching for {position} in {len(companies_to_search)} companies..."):
                try:
                    # Create searcher instance
                    searcher = EmployeeSearcher()
                    
                    # Progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    all_employees = []
                    
                    # Search each company
                    for i, company in enumerate(companies_to_search):
                        # Update progress
                        progress = (i + 1) / len(companies_to_search)
                        progress_bar.progress(progress)
                        status_text.text(f"Searching {company}...")
                        
                        # Perform search
                        result = searcher.search_employees(
                            company_name=company,
                            position=position,
                            location=location if 'location' in locals() and location else None,
                            country=country if 'country' in locals() and country else None,
                            gl=gl,
                            num_results=num_results
                        )
                        
                        if result['success'] and result['data']:
                            all_employees.extend(result['data'])
                    
                    # Clear progress
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Display results
                    if all_employees:
                        st.success(f"✅ Found {len(all_employees)} employees!")
                        
                        # Convert to DataFrame and save to session state
                        df_results = pd.DataFrame(all_employees)
                        st.session_state['employee_search_results'] = df_results
                        st.session_state['employee_search_params'] = {
                            'position': position,
                            'companies': companies_to_search,
                            'location': location if 'location' in locals() else None,
                            'country': country if 'country' in locals() else None
                        }
                        
                        # Display metrics
                        metrics = {
                            "Total Profiles": len(all_employees),
                            "Companies": df_results['company'].nunique() if 'company' in df_results else 0,
                            "With Email": df_results['email'].notna().sum() if 'email' in df_results else 0,
                            "LinkedIn Profiles": df_results['linkedin_url'].notna().sum() if 'linkedin_url' in df_results else 0
                        }
                        display_metrics(metrics)
                        
                        # Display table
                        display_columns = ['name', 'title', 'company', 'linkedin_url', 'email', 'description']
                        display_df = df_results[[col for col in display_columns if col in df_results.columns]]
                        
                        st.dataframe(
                            display_df,
                            use_container_width=True,
                            height=400,
                            column_config={
                                "linkedin_url": st.column_config.LinkColumn("LinkedIn"),
                                "name": st.column_config.TextColumn("Name", width="medium"),
                                "title": st.column_config.TextColumn("Title", width="medium"),
                                "company": st.column_config.TextColumn("Company", width="medium"),
                            },
                            hide_index=True
                        )
                        
                        # Download options
                        st.divider()
                        st.subheader("📥 Download Results")
                        
                        # Generate timestamp for filename
                        timestamp = int(time.time())
                        filename_prefix = f"employees_{position.replace(' ', '_')}_{gl}_{timestamp}"
                        create_download_buttons(df_results, filename_prefix, "both")
                        
                        # Save info - Note: output_file may not be available in batch search
                        st.info(f"💾 Results available for download")
                        
                    else:
                        if 'employee_search_results' in st.session_state:
                            del st.session_state['employee_search_results']
                        st.warning(f"No employees found with position '{position}' in the specified companies")
                        
                except Exception as e:
                    st.error(f"Search error: {str(e)}")
                    progress_bar.empty()
                    status_text.empty()
                    if 'employee_search_results' in st.session_state:
                        del st.session_state['employee_search_results']

# Employee AI Analysis Section - Show only if there are employee search results
if 'employee_search_results' in st.session_state:
    st.divider()
    st.header("🤖 员工AI智能分析")
    st.markdown("对搜索到的员工进行AI深度分析，评估决策者价值和联系优先级")
    
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
        # Employee AI Analysis Configuration
        col_emp_ai1, col_emp_ai2 = st.columns([1, 2])
        
        with col_emp_ai1:
            st.subheader("🎯 分析配置")
            
            # Business context input
            business_context = st.text_area(
                "业务背景",
                value="""我们是一家可再生能源解决方案提供商，主要业务包括：
- 太阳能发电系统设计与安装
- 储能系统集成服务
- 清洁能源项目开发

目标联系人：决策者、采购负责人、技术负责人""",
                height=150,
                help="请详细描述您的业务背景，AI将基于此评估员工联系价值"
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
            
            # Analysis mode
            analysis_mode = st.radio(
                "分析模式",
                ["个体分析", "团队分析"],
                help="个体分析：逐个分析每位员工；团队分析：按公司分析团队结构"
            )
            
            # Analysis button
            employee_analyze_button = st.button(
                "🚀 开始员工AI分析",
                type="primary",
                use_container_width=True
            )
        
        with col_emp_ai2:
            st.subheader("📊 员工AI分析结果")
            
            if employee_analyze_button:
                if not business_context.strip():
                    st.error("请输入业务背景描述")
                else:
                    # Get employee search results from session state
                    df_employees = st.session_state['employee_search_results'].copy()
                    search_params = st.session_state.get('employee_search_params', {})
                    
                    st.success(f"✅ 准备分析 {len(df_employees)} 位员工")
                    
                    # Initialize Employee AI analyzer with optimized version
                    with st.spinner("🤖 正在初始化员工AI分析器..."):
                        try:
                            employee_analyzer = EmployeeAIAnalyzerManager(
                                provider=selected_provider,
                                use_optimized=True,
                                max_concurrent=6,
                                enable_cache=True
                            )
                            
                            st.info("⚡ 使用优化版员工AI分析器，性能提升5-10倍")
                            
                        except Exception as e:
                            st.error(f"初始化员工AI分析器失败: {e}")
                            st.stop()
                    
                    # Create progress tracking
                    emp_progress_bar = st.progress(0)
                    emp_status_text = st.empty()
                    
                    # Progress callback function
                    def update_employee_progress(current, total, employee_name):
                        progress = current / total
                        emp_progress_bar.progress(progress)
                        emp_status_text.text(f"正在分析: {employee_name} ({current}/{total})")
                    
                    # Execute Employee AI analysis
                    with st.spinner("🔍 正在进行员工AI分析..."):
                        try:
                            # Convert DataFrame to list of dicts
                            employees_data = df_employees.to_dict('records')
                            
                            # Batch analyze employees
                            emp_results = employee_analyzer.batch_analyze_employees(
                                employees_data, 
                                business_context, 
                                callback=update_employee_progress
                            )
                            
                            # Clear progress display
                            emp_progress_bar.empty()
                            emp_status_text.empty()
                            
                            # Display results
                            st.success("🎉 员工AI分析完成！")
                            
                            # Convert results to DataFrame
                            emp_results_df = pd.DataFrame(emp_results)
                            
                            # Show performance stats if available
                            if hasattr(employee_analyzer, 'get_performance_stats'):
                                emp_stats = employee_analyzer.get_performance_stats()
                                if emp_stats:
                                    with st.expander("📈 性能统计", expanded=False):
                                        st.json(emp_stats)
                            
                            # Save results
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            position = search_params.get('position', 'unknown')
                            
                            output_dir = Path("output/employee")
                            output_dir.mkdir(exist_ok=True)
                            
                            output_file = output_dir / f"employee_ai_analysis_{position.replace(' ', '_')}_{analysis_mode}_{timestamp}.csv"
                            emp_results_df.to_csv(output_file, index=False, encoding='utf-8-sig')
                            
                            st.info(f"📄 员工分析结果已保存至: {output_file}")
                            
                            # Display analysis statistics
                            st.subheader("📈 员工分析概览")
                            
                            col_emp_stats1, col_emp_stats2, col_emp_stats3, col_emp_stats4 = st.columns(4)
                            
                            with col_emp_stats1:
                                avg_score = emp_results_df['final_score'].mean()
                                st.metric("平均得分", f"{avg_score:.1f}")
                            
                            with col_emp_stats2:
                                high_priority = len(emp_results_df[emp_results_df['priority_level'].isin(['P0 - 极高优先级', 'P1 - 高优先级'])])
                                st.metric("高优先级联系人", f"{high_priority} 位")
                            
                            with col_emp_stats3:
                                decision_makers = len(emp_results_df[emp_results_df['final_score'] >= 70])
                                st.metric("潜在决策者", f"{decision_makers} 位")
                            
                            with col_emp_stats4:
                                total_analyzed = len(emp_results_df)
                                st.metric("总分析数量", f"{total_analyzed} 位")
                            
                            # Display results table
                            st.subheader("📋 详细员工分析结果")
                            
                            # Sort by final score
                            emp_results_sorted = emp_results_df.sort_values('final_score', ascending=False)
                            
                            # Display interactive table
                            st.dataframe(
                                emp_results_sorted,
                                use_container_width=True,
                                height=400,
                                column_config={
                                    "final_score": st.column_config.NumberColumn(
                                        "最终得分",
                                        min_value=0,
                                        max_value=100,
                                        format="%.1f"
                                    ),
                                    "decision_power": st.column_config.NumberColumn(
                                        "决策力",
                                        min_value=0,
                                        max_value=100,
                                        format="%.1f"
                                    ),
                                    "accessibility": st.column_config.NumberColumn(
                                        "可接触性",
                                        min_value=0,
                                        max_value=100,
                                        format="%.1f"
                                    ),
                                    "priority_level": st.column_config.TextColumn(
                                        "优先级",
                                        width="medium"
                                    )
                                },
                                hide_index=True
                            )
                            
                            # Visualization
                            st.subheader("📊 员工分析可视化")
                            
                            col_emp_viz1, col_emp_viz2 = st.columns(2)
                            
                            with col_emp_viz1:
                                # Score distribution histogram
                                fig_emp_hist = px.histogram(
                                    emp_results_df, 
                                    x='final_score', 
                                    nbins=10,
                                    title='员工得分分布',
                                    labels={'final_score': '最终得分', 'count': '员工数量'}
                                )
                                st.plotly_chart(fig_emp_hist, use_container_width=True)
                            
                            with col_emp_viz2:
                                # Priority level pie chart
                                priority_counts = emp_results_df['priority_level'].value_counts()
                                fig_emp_pie = px.pie(
                                    values=priority_counts.values,
                                    names=priority_counts.index,
                                    title='员工优先级分布'
                                )
                                st.plotly_chart(fig_emp_pie, use_container_width=True)
                            
                            # Download analysis results
                            st.subheader("📥 下载员工分析结果")
                            
                            # Create download buttons for analysis results
                            import json as json_lib
                            emp_csv_data = emp_results_sorted.to_csv(index=False, encoding='utf-8-sig')
                            emp_json_data = json_lib.dumps(emp_results_sorted.to_dict('records'), ensure_ascii=False, indent=2)
                            
                            col_emp_dl1, col_emp_dl2 = st.columns(2)
                            
                            with col_emp_dl1:
                                st.download_button(
                                    label="📄 下载CSV格式",
                                    data=emp_csv_data,
                                    file_name=f"employee_analysis_results_{timestamp}.csv",
                                    mime="text/csv"
                                )
                            
                            with col_emp_dl2:
                                st.download_button(
                                    label="📄 下载JSON格式",
                                    data=emp_json_data,
                                    file_name=f"employee_analysis_results_{timestamp}.json",
                                    mime="application/json"
                                )
                        
                        except Exception as e:
                            st.error(f"❌ 员工AI分析失败: {e}")
                            import traceback
                            st.error(f"错误详情: {traceback.format_exc()}")
                            
                            # Clear progress display on error
                            emp_progress_bar.empty()
                            emp_status_text.empty()

# Sidebar
with st.sidebar:
    # API status
    display_api_status()
    
    # Usage tips
    show_usage_tips("employee_search")
    
    # Recent searches
    st.divider()
    st.header("📁 Recent Searches")
    
    employee_dir = os.path.join("output", "employee")
    if os.path.exists(employee_dir):
        csv_files = [f for f in os.listdir(employee_dir) if f.endswith('.csv')]
        csv_files.sort(key=lambda x: os.path.getmtime(os.path.join(employee_dir, x)), reverse=True)
        
        if csv_files:
            recent_files = csv_files[:5]
            for file in recent_files:
                file_path = os.path.join(employee_dir, file)
                file_size = os.path.getsize(file_path) / 1024
                st.markdown(f"📄 {file[:30]}... ({file_size:.1f} KB)")
        else:
            st.info("No search results yet")