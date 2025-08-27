# 🚀 AI客户发现工具 - 启动脚本使用指南

## 📋 脚本说明

本项目提供了3个便捷的Shell脚本来管理前后端服务：

### 1. 启动脚本 (`start.sh`)
- **功能**: 同时启动FastAPI后端和Vue前端服务
- **端口**: 后端8000，前端3000
- **日志**: 自动保存到 `logs/` 目录

### 2. 停止脚本 (`stop.sh`) 
- **功能**: 停止所有前后端服务
- **清理**: 自动清理进程ID文件和残留进程

### 3. 状态检查 (`status.sh`)
- **功能**: 检查服务运行状态、端口占用、日志文件等
- **监控**: 显示系统资源使用和环境配置

## 🎯 使用方法

### 启动服务
```bash
./start.sh
```

### 停止服务  
```bash
./stop.sh
```

### 查看状态
```bash
./status.sh
```

### 查看日志
```bash
# 后端日志
tail -f logs/backend.log

# 前端日志  
tail -f logs/frontend.log
```

## 📍 访问地址

启动成功后，可以通过以下地址访问：

- **前端应用**: http://localhost:3000
- **后端API**: http://localhost:8000  
- **API文档**: http://localhost:8000/docs

## 🔧 环境要求

### 必需依赖
- Python 3.8+
- Node.js 16+
- npm

### 环境配置
确保 `.env` 文件包含必要的配置：
```bash
SERPER_API_KEY=your_serper_api_key
LLM_PROVIDER=your_llm_provider
# 其他LLM配置...
```

## 📊 状态说明

### 服务状态
- ✅ 绿色：服务正常运行
- ❌ 红色：服务未运行
- ⚠️ 黄色：服务异常或配置问题

### 端口检查
脚本会自动检查端口占用情况：
- 8000：后端服务端口
- 3000/3001/3002：前端服务端口（自动选择可用端口）

## 🛠 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 查找占用进程
   lsof -i :8000
   # 终止进程
   kill -9 <PID>
   ```

2. **依赖缺失**
   ```bash
   # 安装Python依赖
   pip install -r requirements.txt
   
   # 安装Node.js依赖
   cd vue_app && npm install
   ```

3. **权限问题**
   ```bash
   # 给脚本添加执行权限
   chmod +x start.sh stop.sh status.sh
   ```

4. **服务启动失败**
   ```bash
   # 查看详细日志
   cat logs/backend.log
   cat logs/frontend.log
   ```

### 手动启动（备选方案）

如果脚本无法正常工作，可以手动启动：

```bash
# 启动后端
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 启动前端
cd vue_app && npm run dev
```

## 📝 注意事项

1. **首次运行前**请确保已安装所有依赖
2. **配置环境变量**在 `.env` 文件中设置API密钥
3. **检查防火墙**确保8000和3000端口可访问
4. **日志监控**定期清理日志文件避免磁盘空间不足

## 🎉 使用技巧

- 使用 `./status.sh` 随时检查服务状态
- 日志文件保存在 `logs/` 目录，便于问题排查
- 脚本支持进程ID管理，确保干净的启动和停止
- 自动检测可用端口，避免端口冲突

---

**🌟 现在可以使用 `./start.sh` 一键启动您的AI客户发现工具！**