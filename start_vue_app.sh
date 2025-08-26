#!/bin/bash
# AI Customer Finder - Vue.js + FastAPI 启动脚本

set -e

echo "🚀 Starting AI Customer Finder (Vue.js + FastAPI)"
echo "================================================"

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js first."
    exit 1
fi

# 检查Python
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python first."
    exit 1
fi

# 停止现有的Streamlit进程
echo "🛑 Stopping existing Streamlit processes..."
pkill -f streamlit || true

# 安装前端依赖
echo "📦 Installing frontend dependencies..."
cd vue_app
if [ ! -d "node_modules" ]; then
    npm install
fi

# 启动FastAPI后端
echo "🔧 Starting FastAPI backend..."
cd ../fastapi_backend

# 安装后端依赖
pip install -r requirements.txt

# 启动后端服务（后台运行）
python main.py &
BACKEND_PID=$!

# 等待后端启动
echo "⏳ Waiting for backend to start..."
sleep 5

# 启动Vue前端
echo "🎨 Starting Vue.js frontend..."
cd ../vue_app
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Application started successfully!"
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# 等待用户中断
trap 'echo "🛑 Stopping services..."; kill $BACKEND_PID $FRONTEND_PID; exit 0' INT
wait