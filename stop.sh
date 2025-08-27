#!/bin/bash

# AI客户发现工具停止脚本
# 停止FastAPI后端和Vue前端服务

echo "🛑 停止AI客户发现工具..."
echo "=================================="

# 读取进程ID
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "🌐 停止后端服务 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        sleep 2
        if kill -0 $BACKEND_PID 2>/dev/null; then
            echo "⚠️  强制停止后端服务..."
            kill -9 $BACKEND_PID
        fi
        echo "✅ 后端服务已停止"
    else
        echo "ℹ️  后端服务未运行"
    fi
    rm -f .backend.pid
else
    echo "ℹ️  未找到后端进程ID文件"
fi

if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "🎨 停止前端服务 (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        sleep 2
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            echo "⚠️  强制停止前端服务..."
            kill -9 $FRONTEND_PID
        fi
        echo "✅ 前端服务已停止"
    else
        echo "ℹ️  前端服务未运行"
    fi
    rm -f .frontend.pid
else
    echo "ℹ️  未找到前端进程ID文件"
fi

# 清理其他可能的进程
echo "🧹 清理残留进程..."
pkill -f "uvicorn api.main:app" 2>/dev/null || true
pkill -f "vite.*vue_app" 2>/dev/null || true

echo ""
echo "✅ 停止完成!"
echo "=================================="
echo "所有服务已停止"