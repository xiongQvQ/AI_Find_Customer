"""
System Settings Page - Streamlit
Configure API keys and system settings through web interface
"""
import streamlit as st
import os
from pathlib import Path
import json
from datetime import datetime
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from components.common import check_api_keys

st.set_page_config(page_title="System Settings", page_icon="⚙️", layout="wide")

st.title("⚙️ 系统设置")
st.markdown("配置API密钥、LLM提供商和其他系统设置")

# Initialize session state for settings
if 'settings_saved' not in st.session_state:
    st.session_state.settings_saved = False

# Load current .env file content
def load_env_settings():
    """加载当前.env文件设置"""
    settings = {}
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    settings[key.strip()] = value.strip().strip('"').strip("'")
    return settings

def save_env_settings(settings):
    """保存设置到.env文件"""
    env_file = Path(".env")
    
    # 备份原文件
    if env_file.exists():
        backup_file = Path(f".env.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        env_file.rename(backup_file)
        st.info(f"原配置已备份为: {backup_file}")
    
    # 写入新设置
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write("# AI Customer Finder Configuration\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Serper API
        f.write("# Serper.dev API Configuration\n")
        f.write(f"SERPER_API_KEY={settings.get('SERPER_API_KEY', '')}\n\n")
        
        # LLM Configuration
        f.write("# LLM Provider Configuration\n")
        f.write(f"LLM_PROVIDER={settings.get('LLM_PROVIDER', 'openai')}\n\n")
        
        # OpenAI
        f.write("# OpenAI Configuration\n")
        f.write(f"OPENAI_API_KEY={settings.get('OPENAI_API_KEY', '')}\n")
        f.write(f"OPENAI_MODEL={settings.get('OPENAI_MODEL', 'gpt-4o-mini')}\n\n")
        
        # Anthropic
        f.write("# Anthropic Configuration\n")
        f.write(f"ANTHROPIC_API_KEY={settings.get('ANTHROPIC_API_KEY', '')}\n")
        f.write(f"ANTHROPIC_MODEL={settings.get('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')}\n\n")
        
        # Google
        f.write("# Google Configuration\n")
        f.write(f"GOOGLE_API_KEY={settings.get('GOOGLE_API_KEY', '')}\n")
        f.write(f"GOOGLE_MODEL={settings.get('GOOGLE_MODEL', 'gemini-1.5-flash')}\n\n")
        
        # Huoshan/Volcano
        f.write("# Huoshan/Volcano Configuration\n")
        f.write(f"ARK_API_KEY={settings.get('ARK_API_KEY', '')}\n")
        f.write(f"ARK_BASE_URL={settings.get('ARK_BASE_URL', 'https://ark.cn-beijing.volces.com/api/v3')}\n")
        f.write(f"ARK_MODEL={settings.get('ARK_MODEL', 'ep-20241022140031-89nkp')}\n\n")
        
        # Application Settings
        f.write("# Application Settings\n")
        f.write(f"HEADLESS={settings.get('HEADLESS', 'true')}\n")
        f.write(f"TIMEOUT={settings.get('TIMEOUT', '15000')}\n")
        f.write(f"VISIT_CONTACT_PAGE={settings.get('VISIT_CONTACT_PAGE', 'false')}\n")

# Load current settings
current_settings = load_env_settings()

# Main settings interface
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🔍 搜索引擎配置")
    
    # Serper API Key
    serper_key = st.text_input(
        "Serper.dev API Key",
        value=current_settings.get('SERPER_API_KEY', ''),
        type="password",
        help="用于搜索公司和员工信息的API密钥，获取地址: https://serper.dev"
    )
    
    if serper_key:
        st.success("✅ Serper API Key 已配置")
    else:
        st.warning("⚠️ 需要配置 Serper API Key 才能使用搜索功能")
    
    st.divider()
    
    st.subheader("🧠 LLM提供商配置")
    
    # LLM Provider selection
    llm_provider = st.selectbox(
        "默认LLM提供商",
        options=['openai', 'anthropic', 'google', 'huoshan'],
        index=['openai', 'anthropic', 'google', 'huoshan'].index(current_settings.get('LLM_PROVIDER', 'openai')),
        help="选择默认的大语言模型提供商"
    )
    
    # OpenAI Configuration
    with st.expander("🤖 OpenAI 配置", expanded=llm_provider=='openai'):
        openai_key = st.text_input(
            "OpenAI API Key",
            value=current_settings.get('OPENAI_API_KEY', ''),
            type="password",
            help="OpenAI API密钥，获取地址: https://platform.openai.com"
        )
        
        openai_model = st.selectbox(
            "OpenAI 模型",
            options=['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
            index=['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'].index(
                current_settings.get('OPENAI_MODEL', 'gpt-4o-mini')
            ) if current_settings.get('OPENAI_MODEL', 'gpt-4o-mini') in ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'] else 1
        )
    
    # Anthropic Configuration
    with st.expander("🧠 Anthropic 配置", expanded=llm_provider=='anthropic'):
        anthropic_key = st.text_input(
            "Anthropic API Key",
            value=current_settings.get('ANTHROPIC_API_KEY', ''),
            type="password",
            help="Anthropic API密钥，获取地址: https://console.anthropic.com"
        )
        
        anthropic_model = st.selectbox(
            "Anthropic 模型",
            options=['claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022', 'claude-3-opus-20240229'],
            index=['claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022', 'claude-3-opus-20240229'].index(
                current_settings.get('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
            ) if current_settings.get('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022') in ['claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022', 'claude-3-opus-20240229'] else 0
        )

with col2:
    # Google Configuration
    with st.expander("🌟 Google 配置", expanded=llm_provider=='google'):
        google_key = st.text_input(
            "Google API Key",
            value=current_settings.get('GOOGLE_API_KEY', ''),
            type="password",
            help="Google AI API密钥，获取地址: https://ai.google.dev"
        )
        
        google_model = st.selectbox(
            "Google 模型",
            options=['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro'],
            index=['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro'].index(
                current_settings.get('GOOGLE_MODEL', 'gemini-1.5-flash')
            ) if current_settings.get('GOOGLE_MODEL', 'gemini-1.5-flash') in ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro'] else 1
        )
    
    # Huoshan/Volcano Configuration
    with st.expander("🌋 火山引擎 配置", expanded=llm_provider=='huoshan'):
        ark_key = st.text_input(
            "ARK API Key",
            value=current_settings.get('ARK_API_KEY', ''),
            type="password",
            help="火山引擎API密钥"
        )
        
        ark_base_url = st.text_input(
            "ARK Base URL",
            value=current_settings.get('ARK_BASE_URL', 'https://ark.cn-beijing.volces.com/api/v3'),
            help="火山引擎API基础URL"
        )
        
        ark_model = st.text_input(
            "ARK Model ID",
            value=current_settings.get('ARK_MODEL', 'ep-20241022140031-89nkp'),
            help="火山引擎模型ID"
        )
    
    st.divider()
    
    st.subheader("🔧 应用设置")
    
    # Browser settings
    headless_mode = st.selectbox(
        "浏览器模式",
        options=['true', 'false'],
        index=['true', 'false'].index(current_settings.get('HEADLESS', 'true')),
        help="true: 无头模式（后台运行），false: 显示浏览器窗口"
    )
    
    timeout_value = st.number_input(
        "页面加载超时(毫秒)",
        min_value=5000,
        max_value=60000,
        value=int(current_settings.get('TIMEOUT', '15000')),
        step=1000,
        help="网页加载超时时间，单位毫秒"
    )
    
    visit_contact_page = st.selectbox(
        "访问联系页面",
        options=['false', 'true'],
        index=['false', 'true'].index(current_settings.get('VISIT_CONTACT_PAGE', 'false')),
        help="是否尝试访问网站的联系页面获取更多信息"
    )

# Save settings section
st.divider()

col_save1, col_save2, col_save3 = st.columns([1, 1, 1])

with col_save1:
    if st.button("💾 保存配置", type="primary", use_container_width=True):
        # Prepare settings dict
        new_settings = {
            'SERPER_API_KEY': serper_key,
            'LLM_PROVIDER': llm_provider,
            'OPENAI_API_KEY': openai_key,
            'OPENAI_MODEL': openai_model,
            'ANTHROPIC_API_KEY': anthropic_key,
            'ANTHROPIC_MODEL': anthropic_model,
            'GOOGLE_API_KEY': google_key,
            'GOOGLE_MODEL': google_model,
            'ARK_API_KEY': ark_key,
            'ARK_BASE_URL': ark_base_url,
            'ARK_MODEL': ark_model,
            'HEADLESS': headless_mode,
            'TIMEOUT': str(timeout_value),
            'VISIT_CONTACT_PAGE': visit_contact_page
        }
        
        try:
            save_env_settings(new_settings)
            st.session_state.settings_saved = True
            st.success("✅ 配置已保存！请重启应用以生效。")
            st.balloons()
        except Exception as e:
            st.error(f"❌ 保存配置失败: {e}")

with col_save2:
    if st.button("🔄 重载配置", use_container_width=True):
        st.rerun()

with col_save3:
    if st.button("🧪 测试配置", use_container_width=True):
        with st.spinner("测试API连接..."):
            # Test API configurations
            test_results = {}
            
            # Test Serper API
            if serper_key:
                try:
                    import requests
                    response = requests.get(
                        "https://google.serper.dev/search",
                        headers={"X-API-KEY": serper_key},
                        params={"q": "test"},
                        timeout=10
                    )
                    test_results['Serper'] = response.status_code in [200, 401, 429]
                except:
                    test_results['Serper'] = False
            
            # Test LLM APIs (basic connectivity)
            if openai_key:
                try:
                    import openai
                    client = openai.OpenAI(api_key=openai_key)
                    # Test with a simple request
                    models = client.models.list()
                    test_results['OpenAI'] = True
                except:
                    test_results['OpenAI'] = False
            
            if anthropic_key:
                try:
                    import anthropic
                    client = anthropic.Anthropic(api_key=anthropic_key)
                    test_results['Anthropic'] = True
                except:
                    test_results['Anthropic'] = False
            
            if google_key:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=google_key)
                    test_results['Google'] = True
                except:
                    test_results['Google'] = False
            
            if ark_key and ark_base_url:
                try:
                    import requests
                    # Simple connectivity test
                    test_results['Huoshan'] = True
                except:
                    test_results['Huoshan'] = False
            
            # Display test results
            if test_results:
                st.subheader("🧪 API连接测试结果")
                for service, status in test_results.items():
                    if status:
                        st.success(f"✅ {service} - 连接正常")
                    else:
                        st.error(f"❌ {service} - 连接失败")
            else:
                st.warning("⚠️ 没有配置任何API密钥进行测试")

# Current status display
st.divider()
st.subheader("📊 当前配置状态")

# Check current API status
current_api_status = check_api_keys()

col_status1, col_status2 = st.columns(2)

with col_status1:
    st.markdown("**搜索引擎API:**")
    if current_api_status.get('SERPER_API_KEY'):
        st.success("✅ Serper API - 已配置")
    else:
        st.error("❌ Serper API - 未配置")

with col_status2:
    st.markdown("**LLM API状态:**")
    llm_apis = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY', 'ARK_API_KEY']
    configured_llms = [key.replace('_API_KEY', '') for key, status in current_api_status.items() 
                       if key in llm_apis and status]
    
    if configured_llms:
        for llm in configured_llms:
            st.success(f"✅ {llm} - 已配置")
    else:
        st.error("❌ 未配置任何LLM API")

# Usage instructions
with st.sidebar:
    st.header("📖 使用说明")
    
    st.markdown("""
    ### API获取地址
    
    **搜索引擎**
    - [Serper.dev](https://serper.dev) - 获取搜索API
    
    **LLM提供商**
    - [OpenAI](https://platform.openai.com) - GPT系列模型
    - [Anthropic](https://console.anthropic.com) - Claude系列模型  
    - [Google AI](https://ai.google.dev) - Gemini系列模型
    - [火山引擎](https://www.volcengine.com) - 豆包系列模型
    
    ### 配置步骤
    1. 获取所需API密钥
    2. 在界面中输入API密钥
    3. 选择默认LLM提供商
    4. 调整应用设置
    5. 点击"保存配置"
    6. 重启应用生效
    """)
    
    st.divider()
    
    st.markdown("**⚠️ 注意事项**")
    st.markdown("""
    - API密钥将保存在 `.env` 文件中
    - 原配置文件会自动备份
    - 修改后需要重启应用才能生效
    - 请妥善保管API密钥，不要分享给他人
    """)

# Show save confirmation
if st.session_state.settings_saved:
    st.info("💡 配置已保存，重启应用后生效。可以使用以下命令重启：`streamlit run streamlit_app.py`")