"""Verification script to test LLM connectivity (ZAI/GLM).

Usage:
    cd ai_hunter/backend
    python scripts/test_llm_connection.py
"""

import asyncio
import logging
import os
import sys

# Add the backend directory to sys.path so we can import tools and config
sys.path.append(os.getcwd())

from config.settings import get_settings
from tools.llm_client import LLMTool

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def test_connection():
    settings = get_settings()
    
    print("\n" + "="*50)
    print(" LLM CONNECTIVITY TEST - ZAI/GLM")
    print("="*50)
    
    # 1. Check Configuration
    print(f"\n[1] Checking Configuration:")
    print(f"    - Default Model:   {settings.llm_model}")
    print(f"    - Reasoning Model: {settings.reasoning_model}")
    print(f"    - ZAI Key:        {'SET (starts with ' + settings.zai_api_key[:5] + '...)' if settings.zai_api_key else 'NOT SET'}")
    
    async def try_call(model: str, base_url: str, label: str):
        print(f"\n[Testing] {label}")
        print(f"    - Model: {model}")
        print(f"    - Base:  {base_url}")
        try:
            # Clear prev env
            for k in ["OPENAI_API_BASE", "OPENAI_API_KEY", "ZAI_API_KEY", "ZHIPUAI_API_KEY"]:
                if k in os.environ: del os.environ[k]

            # Set env
            if model.startswith("openai/"):
                os.environ["OPENAI_API_BASE"] = base_url
                os.environ["OPENAI_API_KEY"] = settings.zai_api_key
            else:
                # Native litellm provider
                os.environ["ZAI_API_KEY"] = settings.zai_api_key
            
            from litellm import acompletion
            print(f"    Calling...")
            response = await acompletion(
                model=model,
                messages=[{"role": "user", "content": "Say 'ZAI OK'"}],
                max_tokens=20,
                temperature=0.1
            )
            
            msg = response.choices[0].message
            print(f"    SUCCESS! Response: {msg.content.strip() if msg.content else 'NO CONTENT'}")
            return True
        except Exception as e:
            print(f"    FAILED: {type(e).__name__}: {str(e)}")
            return False

    combinations = [
        ("zai/glm-4-flash", "N/A", "Native LiteLLM (zai/prefix)"),
        ("openai/glm-4-flash", "https://open.bigmodel.cn/api/paas/v4/", "OpenAI Compatible (openai/prefix)"),
        ("openai/glm-5", "https://open.bigmodel.cn/api/paas/v4/", "OpenAI Compatible GLM-5"),
    ]

    results = []
    for model, base, label in combinations:
        success = await try_call(model, base, label)
        results.append(success)
        if success:
            print(f"\n    >>> WORKING CONFIG: {label} <<<")

    print("\n" + "="*50)
    if any(results):
        print(" AT LEAST ONE CONNECTION WAS SUCCESSFUL.")
    else:
        print(" ALL TESTS FAILED.")
    print("="*50 + "\n")

if __name__ == "__main__":
    import litellm
    litellm.suppress_debug_info = True
    asyncio.run(test_connection())
