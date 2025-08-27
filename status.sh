#!/bin/bash

# AI客户发现工具状态检查脚本
# 检查FastAPI后端和Vue前端服务状态

echo "📊 AI客户发现工具状态检查"
echo "=================================="

# 检查端口占用
check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        local pid=$(lsof -Pi :$port -sTCP:LISTEN -t)
        echo "✅ $service: 运行中 (端口 $port, PID: $pid)"
        return 0
    else
        echo "❌ $service: 未运行 (端口 $port)"
        return 1
    fi
}

# 检查后端服务
echo "🌐 后端服务状态:"
check_port 8000 "FastAPI后端"
if [ $? -eq 0 ]; then
    echo "   📍 API地址: http://localhost:8000"
    echo "   📚 API文档: http://localhost:8000/docs"
    
    # 测试API健康检查
    if command -v curl &> /dev/null; then
        if curl -s http://localhost:8000/health >/dev/null 2>&1; then
            echo "   💚 健康检查: 通过"
        else
            echo "   💛 健康检查: API可能未完全就绪"
        fi
    fi
else
    if [ -f ".backend.pid" ]; then
        echo "   ⚠️  清理残留PID文件"
        rm -f .backend.pid
    fi
fi

echo ""

# 检查前端服务
echo "🎨 前端服务状态:"
if check_port 3000 "Vue前端"; then
    echo "   📍 前端地址: http://localhost:3000"
else
    # 尝试其他常见端口
    if check_port 3001 "Vue前端"; then
        echo "   📍 前端地址: http://localhost:3001"
    elif check_port 3002 "Vue前端"; then
        echo "   📍 前端地址: http://localhost:3002"
    else
        if [ -f ".frontend.pid" ]; then
            echo "   ⚠️  清理残留PID文件"
            rm -f .frontend.pid
        fi
    fi
fi

echo ""

# 检查日志文件
echo "📋 日志文件状态:"
if [ -f "logs/backend.log" ]; then
    backend_log_size=$(wc -l < logs/backend.log 2>/dev/null || echo "0")
    echo "✅ 后端日志: logs/backend.log ($backend_log_size 行)"
else
    echo "❌ 后端日志: 不存在"
fi

if [ -f "logs/frontend.log" ]; then
    frontend_log_size=$(wc -l < logs/frontend.log 2>/dev/null || echo "0")
    echo "✅ 前端日志: logs/frontend.log ($frontend_log_size 行)"
else
    echo "❌ 前端日志: 不存在"
fi

echo ""

# 检查环境配置
echo "⚙️  环境配置:"
if [ -f ".env" ]; then
    echo "✅ 环境配置: .env 文件存在"
    # 检查关键配置项（不显示具体值）
    if grep -q "SERPER_API_KEY" .env 2>/dev/null; then
        echo "   🔑 Serper API密钥: 已配置"
    else
        echo "   ⚠️  Serper API密钥: 未配置"
    fi
    
    if grep -q "LLM_PROVIDER" .env 2>/dev/null; then
        llm_provider=$(grep "LLM_PROVIDER" .env | cut -d'=' -f2 | tr -d '"')
        echo "   🧠 LLM提供商: $llm_provider"
    fi
else
    echo "❌ 环境配置: .env 文件不存在"
fi

echo ""

# 系统资源使用情况
echo "💻 系统资源:"
if command -v python &> /dev/null; then
    python_version=$(python --version 2>&1)
    echo "✅ Python: $python_version"
else
    echo "❌ Python: 未安装"
fi

if command -v node &> /dev/null; then
    node_version=$(node --version 2>/dev/null)
    npm_version=$(npm --version 2>/dev/null)
    echo "✅ Node.js: $node_version, npm: $npm_version"
else
    echo "❌ Node.js: 未安装"
fi

echo ""
echo "=================================="

# 总结状态
backend_running=$(lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 && echo "1" || echo "0")
frontend_running=$(lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1 || lsof -Pi :3001 -sTCP:LISTEN -t >/dev/null 2>&1 || lsof -Pi :3002 -sTCP:LISTEN -t >/dev/null 2>&1 && echo "1" || echo "0")

if [ "$backend_running" = "1" ] && [ "$frontend_running" = "1" ]; then
    echo "🎉 状态: 所有服务正常运行"
elif [ "$backend_running" = "1" ]; then
    echo "⚠️  状态: 仅后端服务运行，前端需要启动"
elif [ "$frontend_running" = "1" ]; then
    echo "⚠️  状态: 仅前端服务运行，后端需要启动"
else
    echo "🛑 状态: 所有服务已停止"
    echo "💡 使用 ./start.sh 启动服务"
fi