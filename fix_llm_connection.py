#!/usr/bin/env python3
"""
LLM连接问题快速修复脚本
诊断并修复LLM连接问题
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

def main():
    print("🔧 LLM连接问题快速修复脚本")
    print("=" * 50)
    
    # 加载环境变量
    load_dotenv()
    
    print("1. 检查环境变量配置...")
    
    # 检查关键配置
    config_status = {
        "SERPER_API_KEY": os.getenv("SERPER_API_KEY"),
        "LLM_PROVIDER": os.getenv("LLM_PROVIDER"),
        "ARK_API_KEY": os.getenv("ARK_API_KEY"),
        "ARK_BASE_URL": os.getenv("ARK_BASE_URL"),
        "ARK_MODEL": os.getenv("ARK_MODEL"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY")
    }
    
    for key, value in config_status.items():
        status = "✅ 已设置" if value else "❌ 未设置"
        if value and len(str(value)) > 20:
            display_value = f"{str(value)[:10]}...{str(value)[-4:]}"
        else:
            display_value = value if value else "未设置"
        print(f"   {key}: {status} ({display_value})")
    
    print("\n2. 测试LLM连接...")
    
    # 测试Huoshan API
    if config_status["ARK_API_KEY"] and config_status["ARK_BASE_URL"]:
        print("   测试火山引擎(Huoshan) API...")
        try:
            import requests
            
            headers = {
                "Authorization": f"Bearer {config_status['ARK_API_KEY']}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": config_status["ARK_MODEL"] or "doubao-seed-1-6-250615",
                "messages": [{"role": "user", "content": "测试"}],
                "max_tokens": 10
            }
            
            response = requests.post(
                f"{config_status['ARK_BASE_URL']}/chat/completions",
                json=data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("   ✅ 火山引擎API连接正常")
            else:
                print(f"   ⚠️ 火山引擎API返回错误: {response.status_code}")
                print(f"   响应: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ 火山引擎API测试失败: {e}")
    else:
        print("   ❌ 火山引擎配置不完整")
    
    print("\n3. 生成修复建议...")
    
    suggestions = []
    
    # 检查基本配置
    if not config_status["SERPER_API_KEY"]:
        suggestions.append("🔑 设置SERPER_API_KEY (必需)")
    
    if config_status["LLM_PROVIDER"] == "huoshan":
        if not all([config_status["ARK_API_KEY"], config_status["ARK_BASE_URL"], config_status["ARK_MODEL"]]):
            suggestions.append("🔧 完善火山引擎配置 (ARK_API_KEY, ARK_BASE_URL, ARK_MODEL)")
    
    # 建议添加备用LLM
    if not config_status["OPENAI_API_KEY"]:
        suggestions.append("🛡️ 添加OpenAI API密钥作为备用")
    
    # 输出建议
    if suggestions:
        print("   修复建议:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. {suggestion}")
    else:
        print("   ✅ 配置看起来正常")
    
    print("\n4. 应用自动修复...")
    
    # 创建增强的环境变量加载
    env_fix_code = '''
# 在应用启动时添加以下代码确保环境变量正确加载
import os
from dotenv import load_dotenv
from pathlib import Path

def ensure_env_loaded():
    """确保环境变量正确加载"""
    # 加载.env文件
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)
    
    # 验证关键变量
    required_vars = ["SERPER_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️ 缺少环境变量: {', '.join(missing_vars)}")
        return False
    
    return True

# 调用检查
if not ensure_env_loaded():
    print("❌ 环境变量加载失败，请检查.env文件")
'''
    
    # 写入修复代码文件
    fix_code_path = Path(__file__).parent / "env_fix_helper.py"
    with open(fix_code_path, 'w', encoding='utf-8') as f:
        f.write(env_fix_code)
    
    print(f"   ✅ 创建了环境变量修复助手: {fix_code_path}")
    
    print("\n5. 创建LLM连接测试工具...")
    
    # 测试LLM连接的简单脚本
    test_script_content = '''#!/usr/bin/env python3
"""简单的LLM连接测试脚本"""

import os
from dotenv import load_dotenv
load_dotenv()

def test_huoshan_llm():
    """测试火山引擎LLM"""
    try:
        import requests
        
        api_key = os.getenv("ARK_API_KEY")
        base_url = os.getenv("ARK_BASE_URL")
        model = os.getenv("ARK_MODEL")
        
        if not all([api_key, base_url, model]):
            return False, "配置不完整"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 20
        }
        
        response = requests.post(
            f"{base_url}/chat/completions",
            json=data,
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            return True, "连接成功"
        else:
            return False, f"HTTP {response.status_code}: {response.text[:100]}"
            
    except Exception as e:
        return False, f"错误: {e}"

if __name__ == "__main__":
    success, message = test_huoshan_llm()
    print(f"🧪 LLM连接测试: {'✅ 成功' if success else '❌ 失败'}")
    print(f"   详情: {message}")
'''
    
    test_script_path = Path(__file__).parent / "test_llm_connection.py"
    with open(test_script_path, 'w', encoding='utf-8') as f:
        f.write(test_script_content)
    
    os.chmod(test_script_path, 0o755)  # 添加执行权限
    print(f"   ✅ 创建了LLM连接测试脚本: {test_script_path}")
    
    print("\n6. 总结和后续步骤...")
    
    print("   ✅ 快速修复完成!")
    print("   \n   后续步骤:")
    print("   1. 运行测试脚本: python test_llm_connection.py")
    print("   2. 如果仍有问题，检查网络连接和防火墙")
    print("   3. 考虑添加OpenAI API密钥作为备用")
    print("   4. 重启Streamlit应用: streamlit run pages/7_🔍_Intelligent_Search_LangGraph.py")
    
    print(f"\n   📊 当前LLM提供商: {config_status['LLM_PROVIDER'] or '未设置'}")
    print(f"   🔑 API密钥状态: {'火山引擎已配置' if config_status['ARK_API_KEY'] else '未配置'}")

if __name__ == "__main__":
    main()