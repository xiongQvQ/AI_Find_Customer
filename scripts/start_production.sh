#!/bin/bash
# 生产环境启动脚本
# 生成时间: 20250825_003242

cd "/Users/xiongbojian/learn/AI_Find_Customer"

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 设置环境变量
export PYTHONPATH="${PYTHONPATH}:/Users/xiongbojian/learn/AI_Find_Customer"
export ENVIRONMENT=production

# 启动Streamlit应用
echo "启动AI客户发现系统..."
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true

echo "系统已启动，访问 http://localhost:8501"
