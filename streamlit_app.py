"""
AI Customer Finder - Streamlit Web Application
Main entry point for the web interface
"""
import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Customer Finder",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/AI_Find_Customer',
        'Report a bug': "https://github.com/your-repo/AI_Find_Customer/issues",
        'About': "# AI Customer Finder\nOpen-source B2B customer development tool"
    }
)

# Import common components
from components.common import check_api_keys, display_api_status, display_quick_links
from components.language_manager import get_language_manager, t

# Main page
st.title(f"🤖 {t('main.title')}")
st.markdown(f"""
### {t('main.subtitle')}

{t('main.description.intro')}
- {t('main.description.search')}
- {t('main.description.contact')}
- {t('main.description.employee')}

---

### {t('main.quick_start.title')}
1. {t('main.quick_start.step1')}
2. {t('main.quick_start.step2')}
3. {t('main.quick_start.step3')}
4. {t('main.quick_start.step4')}

### {t('main.output_location.title')}
{t('main.output_location.description')}
- {t('main.output_location.company')}
- {t('main.output_location.contact')}
- {t('main.output_location.employee')}
""")

# Check API keys
api_status = check_api_keys()

if not api_status["SERPER_API_KEY"]:
    st.error(t('main.api_config.missing_key'))
    
    col_config1, col_config2 = st.columns(2)
    
    with col_config1:
        st.info(t('main.api_config.recommended'))
        if st.button(t('main.api_config.goto_settings'), type="primary"):
            st.switch_page("pages/6_⚙️_System_Settings.py")
    
    with col_config2:
        with st.expander(t('main.api_config.manual_config')):
            st.markdown("""
            1. Create a `.env` file in the project root directory
            2. Add your API keys:
            ```
            SERPER_API_KEY=your_serper_api_key_here
            LLM_PROVIDER=openai  # or anthropic, google, huoshan
            OPENAI_API_KEY=your_openai_key_here  # if using OpenAI
            ```
            3. Restart the application
            """)
    st.stop()

# Display configuration status in sidebar
display_api_status()

# Display quick links
display_quick_links()

# Feature cards
st.markdown("---")
st.subheader(f"🚀 {t('main.features.title')}")

col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

with col1:
    st.markdown(f"""
    ### {t('main.features.company_search.title')}
    {t('main.features.company_search.description')}
    
    [{t('main.features.company_search.link')}](/Company_Search)
    """)
    
    st.markdown(f"""
    ### {t('main.features.ai_search.title')}
    {t('main.features.ai_search.description')}
    
    [{t('main.features.ai_search.link')}](/Intelligent_Search)
    """)

with col2:
    st.markdown(f"""
    ### {t('main.features.contact_extraction.title')}
    {t('main.features.contact_extraction.description')}
    
    [{t('main.features.contact_extraction.link')}](/Contact_Extraction)
    """)

with col3:
    st.markdown(f"""
    ### {t('main.features.employee_search.title')}
    {t('main.features.employee_search.description')}
    
    [{t('main.features.employee_search.link')}](/Employee_Search)
    """)

with col4:
    st.markdown(f"""
    ### {t('main.features.system_settings.title')}
    {t('main.features.system_settings.description')}
    
    [{t('main.features.system_settings.link')}](/System_Settings)
    """)
    
    st.markdown(f"""
    ### {t('main.features.ai_dashboard.title')}
    {t('main.features.ai_dashboard.description')}
    
    [{t('main.features.ai_dashboard.link')}](/AI_Analytics_Dashboard)
    """)

# Statistics section
st.markdown("---")
st.subheader(f"📊 {t('main.usage_stats.title')}")

# Check for existing output files
output_dir = "output"
stats = {}

if os.path.exists(output_dir):
    # Count files in each subdirectory
    for subdir in ["company", "contact", "employee"]:
        subdir_path = os.path.join(output_dir, subdir)
        if os.path.exists(subdir_path):
            csv_files = len([f for f in os.listdir(subdir_path) if f.endswith('.csv')])
            stats[subdir] = csv_files

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(t('main.usage_stats.company_files'), stats.get("company", 0))
    
    with col2:
        st.metric(t('main.usage_stats.contact_files'), stats.get("contact", 0))
    
    with col3:
        st.metric(t('main.usage_stats.employee_files'), stats.get("employee", 0))
else:
    st.info(t('main.usage_stats.no_files'))

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray;">
    <small>
    AI Customer Finder v1.0 | 
    <a href="https://github.com/your-repo/AI_Find_Customer">GitHub</a> | 
    <a href="https://github.com/your-repo/AI_Find_Customer/wiki">Documentation</a>
    </small>
</div>
""", unsafe_allow_html=True)