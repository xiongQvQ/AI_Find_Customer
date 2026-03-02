"""
Common UI components for Streamlit app
"""
import streamlit as st
import os
from typing import Dict, List, Optional

def check_api_keys() -> Dict[str, bool]:
    """
    Check if required API keys are configured
    Returns a dict with key status
    """
    api_status = {
        "SERPER_API_KEY": bool(os.getenv("SERPER_API_KEY")),
        "LLM_PROVIDER": os.getenv("LLM_PROVIDER", "none") != "none"
    }
    
    # Check specific LLM provider keys
    llm_provider = os.getenv("LLM_PROVIDER", "none").lower()
    if llm_provider == "openai":
        api_status["OPENAI_API_KEY"] = bool(os.getenv("OPENAI_API_KEY"))
    elif llm_provider == "anthropic":
        api_status["ANTHROPIC_API_KEY"] = bool(os.getenv("ANTHROPIC_API_KEY"))
    elif llm_provider == "google":
        api_status["GOOGLE_API_KEY"] = bool(os.getenv("GOOGLE_API_KEY"))
    elif llm_provider == "huoshan":
        api_status["ARK_API_KEY"] = bool(os.getenv("ARK_API_KEY"))
    
    return api_status

def display_api_status():
    """Display API configuration status in sidebar"""
    st.sidebar.header("⚙️ Configuration Status")
    
    api_status = check_api_keys()
    
    # Serper API status
    serper_icon = "✅" if api_status["SERPER_API_KEY"] else "❌"
    st.sidebar.write(f"Serper API: {serper_icon}")
    
    # LLM Provider status
    llm_icon = "✅" if api_status["LLM_PROVIDER"] else "⚠️"
    llm_provider = os.getenv("LLM_PROVIDER", "none")
    st.sidebar.write(f"LLM Provider: {llm_icon} {llm_provider}")
    
    # Check for missing required keys
    if not api_status["SERPER_API_KEY"]:
        st.sidebar.error("Missing SERPER_API_KEY!")
        st.sidebar.info("Please configure it in .env file")
        return False
    
    return True

def display_quick_links():
    """Display quick links in sidebar"""
    st.sidebar.divider()
    st.sidebar.header("🔗 Quick Links")
    
    # Create clickable links to output directories
    output_dir = os.path.join(os.getcwd(), "output")
    if os.path.exists(output_dir):
        st.sidebar.markdown(f"📁 [Output Directory]({output_dir})")
    
    st.sidebar.markdown("""
    - 📚 [GitHub Repository](https://github.com/xiongQvQ/AI_Find_Customer)
    - � [B2BInsights.io - AI B2B Intelligence](https://b2binsights.io)
    - 🐛 [Report Issues](https://github.com/xiongQvQ/AI_Find_Customer/issues)
    """)

def show_usage_tips(page_type: str):
    """Show usage tips based on page type"""
    tips = {
        "company_search": {
            "title": "📖 Search Tips",
            "content": """
            ### Search Tips
            
            **Industry Keywords**
            - ✅ Use specific terms: "solar panel manufacturing"
            - ❌ Avoid generic terms: "energy"
            
            **Region Selection**
            - ✅ Country/State/City: "California", "London"
            - ✅ Areas: "Silicon Valley", "Bay Area"
            
            **Combine Criteria**
            - Use multiple conditions for precise results
            """
        },
        "contact_extraction": {
            "title": "📖 Extraction Tips",
            "content": """
            ### Extraction Tips
            
            **Input Methods**
            - Single URL for quick extraction
            - CSV file for batch processing
            - Use results from Company Search
            
            **Best Practices**
            - Enable contact page crawling for better results
            - Use LLM for improved accuracy
            - Check output/contact/ for results
            """
        },
        "employee_search": {
            "title": "📖 Search Tips",
            "content": """
            ### Employee Search Tips
            
            **Position Keywords**
            - Be specific: "Sales Director", "CEO"
            - Use common titles: "Manager", "VP"
            
            **Location Filters**
            - Add location for better targeting
            - Use country for broader search
            
            **LinkedIn Focus**
            - Results primarily from LinkedIn
            - Professional profiles only
            """
        }
    }
    
    if page_type in tips:
        with st.sidebar:
            st.header(tips[page_type]["title"])
            st.markdown(tips[page_type]["content"])

def create_download_buttons(data, filename_prefix: str, data_type: str = "csv"):
    """Create download buttons for data export"""
    col1, col2 = st.columns(2)
    
    with col1:
        if data_type == "csv" or data_type == "both":
            import pandas as pd
            if isinstance(data, pd.DataFrame):
                csv_data = data.to_csv(index=False)
            else:
                df = pd.DataFrame(data)
                csv_data = df.to_csv(index=False)
            
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"{filename_prefix}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col2:
        if data_type == "json" or data_type == "both":
            import json
            if isinstance(data, str):
                json_data = data
            else:
                json_data = json.dumps(data if isinstance(data, list) else data.to_dict('records'), 
                                      ensure_ascii=False, indent=2)
            
            st.download_button(
                label="📥 Download JSON",
                data=json_data,
                file_name=f"{filename_prefix}.json",
                mime="application/json",
                use_container_width=True
            )

def display_metrics(metrics: Dict[str, any]):
    """Display metrics in columns"""
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics.items()):
        with col:
            st.metric(label, value)

def format_dataframe_columns(df, column_configs: Optional[Dict] = None):
    """Format dataframe columns for better display"""
    if column_configs is None:
        column_configs = {}
    
    # Common column configurations
    default_configs = {
        "url": st.column_config.LinkColumn("Website"),
        "linkedin": st.column_config.LinkColumn("LinkedIn"),
        "email": st.column_config.TextColumn("Email", width="medium"),
        "phone": st.column_config.TextColumn("Phone", width="small"),
        "name": st.column_config.TextColumn("Name", width="medium"),
        "company_name": st.column_config.TextColumn("Company", width="medium"),
        "description": st.column_config.TextColumn("Description", width="large"),
    }
    
    # Merge with custom configs
    final_configs = {**default_configs, **column_configs}
    
    # Filter to only include columns that exist in dataframe
    existing_configs = {k: v for k, v in final_configs.items() if k in df.columns}
    
    return existing_configs