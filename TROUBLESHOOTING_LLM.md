# LLM评估问题排查指南

## 问题描述
- AI评估显示"基础评估（无LLM可用）"
- 所有公司评分固定为75.0
- 前端显示空白

## 已实施的修复

### 1. 环境变量加载优化
- 在 `robust_llm_client.py` 和 `llm_client.py` 中添加了 `load_dotenv()`
- 在 Streamlit 页面最顶部优先加载环境变量

### 2. 延迟初始化修复
- 实现了 `LazyNodeProxy` 延迟加载机制
- 确保节点在环境变量加载后才初始化
- 避免了模块级别的过早初始化问题

### 3. 错误修复
- 修复了 `CLIENT_AVAILABLE` 未定义的错误

## 验证步骤

### 1. 测试LLM是否正常工作
```bash
python test_minimal_llm.py
```

预期输出：
- ✅ LLM Response: OK
- ✅ Evaluation result: score=XX, reason=中文评估原因

### 2. 清理Streamlit缓存
```bash
python clear_streamlit_cache.py
```

### 3. 重启Streamlit应用
```bash
# 停止当前运行的Streamlit（Ctrl+C）
# 然后重新启动
streamlit run streamlit_app.py
```

### 4. 测试搜索功能
1. 访问"🔍 Intelligent Search (LangGraph)"页面
2. 输入查询，如"深圳人工智能公司"
3. 点击搜索

## 检查点

### 环境变量检查
确保 `.env` 文件包含：
```
LLM_PROVIDER=huoshan
ARK_API_KEY=你的API密钥
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ARK_MODEL=你的模型ID
```

### 日志检查
查看搜索时的控制台输出，应该看到：
- "鲁棒性LLM客户端初始化成功"
- "内部LLM客户端状态: provider=huoshan, available=True"

### 结果检查
成功的AI评估应该显示：
- `ai_score`: 不同的分数（不是固定的75.0）
- `ai_reason`: 详细的中文评估原因（不是"基础评估（无LLM可用）"）

## 如果问题仍然存在

1. **检查Python导入顺序**
   - 确保没有在环境变量加载前导入LangGraph模块
   
2. **检查Streamlit版本**
   ```bash
   pip show streamlit
   ```
   
3. **完全重启**
   - 关闭所有Python进程
   - 删除 `__pycache__` 目录
   - 重新启动Streamlit

4. **运行直接测试**
   ```bash
   python test_langgraph_direct.py
   ```

## 调试信息收集

如果问题持续，请收集以下信息：
1. `test_minimal_llm.py` 的完整输出
2. Streamlit启动时的控制台输出
3. 搜索时的控制台错误信息
4. 最新的搜索结果JSON文件内容