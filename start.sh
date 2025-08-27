#!/bin/bash

# AI客户发现工具启动脚本
# 同时启动FastAPI后端和Vue前端服务

echo "🚀 启动AI客户发现工具..."
echo "=================================="

# 检查是否在正确的目录
if [ ! -f "api/main.py" ] || [ ! -d "vue_app" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "❌ 错误: Python未安装或不在PATH中"
    exit 1
fi

# 检查Node.js环境
if ! command -v npm &> /dev/null; then
    echo "❌ 错误: Node.js/npm未安装或不在PATH中"
    exit 1
fi

# 创建日志目录
mkdir -p logs

echo "🔧 检查后端依赖..."
# 检查后端依赖
if [ ! -f "requirements.txt" ]; then
    echo "⚠️  警告: requirements.txt不存在"
else
    echo "✅ 后端依赖文件存在"
fi

echo "🔧 检查前端依赖..."
# 检查前端依赖
if [ ! -d "vue_app/node_modules" ]; then
    echo "📦 安装前端依赖..."
    cd vue_app && npm install
    if [ $? -ne 0 ]; then
        echo "❌ 前端依赖安装失败"
        exit 1
    fi
    cd ..
else
    echo "✅ 前端依赖已存在"
fi

# 检查端口占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  警告: 端口 $port 已被占用"
        return 1
    else
        echo "✅ 端口 $port 可用"
        return 0
    fi
}

echo "🔍 检查端口状态..."
check_port 8000  # 后端端口
check_port 3000  # 前端端口

# 启动后端服务
echo ""
echo "🌐 启动后端服务 (FastAPI)..."
echo "后端地址: http://localhost:8000"
nohup python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "后端进程 PID: $BACKEND_PID"

# 等待后端启动
echo "⏳ 等待后端启动..."
sleep 3

# 检查后端是否启动成功
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo "✅ 后端启动成功"
else
    echo "❌ 后端启动失败，请检查 logs/backend.log"
    exit 1
fi

# 启动前端服务
echo ""
echo "🎨 启动前端服务 (Vue)..."
echo "前端地址: http://localhost:3000"
cd vue_app
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "前端进程 PID: $FRONTEND_PID"

# 等待前端启动
echo "⏳ 等待前端启动..."
sleep 5

# 检查前端是否启动成功
if kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "✅ 前端启动成功"
else
    echo "❌ 前端启动失败，请检查 logs/frontend.log"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# 保存进程ID到文件
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

echo ""
echo "🎉 启动完成!"
echo "=================================="
echo "📍 访问地址:"
echo "   前端: http://localhost:3000"
echo "   后端API: http://localhost:8000"
echo "   API文档: http://localhost:8000/docs"
echo ""
echo "📋 管理命令:"
echo "   查看状态: ./status.sh"
echo "   停止服务: ./stop.sh"
echo "   查看日志: tail -f logs/backend.log 或 tail -f logs/frontend.log"
echo ""
echo "🔧 进程信息:"
echo "   后端PID: $BACKEND_PID"
echo "   前端PID: $FRONTEND_PID"
echo ""
echo "✨ AI客户发现工具已就绪，开始您的智能客户搜索之旅！"