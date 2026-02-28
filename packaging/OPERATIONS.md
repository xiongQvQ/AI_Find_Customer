# AI Hunter — 完整操作流程

## 目录
1. [开发环境运行](#1-开发环境运行)
2. [License Server 部署](#2-license-server-部署)
3. [生成 License Key](#3-生成-license-key)
4. [打包桌面应用](#4-打包桌面应用)
5. [测试](#5-测试)
6. [用户安装体验](#6-用户安装体验)
7. [运维操作](#7-运维操作)

---

## 1. 开发环境运行

```bash
# 后端
cd ai_hunter/backend
pip install -r requirements.txt
uvicorn api.app:app --reload --port 8000

# 前端（另一个终端）
cd ai_hunter/frontend
npm install
npm run dev   # http://localhost:5173
```

> 开发时 `.env` 在 `ai_hunter/backend/.env`，**不需要** license 验证（只要 `license_server_url` 能访问到服务器）。

---

## 2. License Server 部署

### 2.1 首次部署（VPS）

```bash
cd ai_hunter/license-server
cp .env.example .env
```

编辑 `.env`：

```bash
# 生成安全密钥
openssl rand -hex 32   # 用于 JWT_SECRET
openssl rand -hex 32   # 用于 ADMIN_API_KEY（不同的值）
```

```ini
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@db:5432/license_db
JWT_SECRET=<上面生成的第1个hex>
ADMIN_API_KEY=<上面生成的第2个hex>
TOKEN_TTL_DAYS=7
APP_VERSION=1.0.0
```

```bash
docker-compose up -d

# 验证服务正常
curl https://your-server/health
# → {"status": "ok", "service": "ai-hunter-license"}
```

### 2.2 更新部署

```bash
docker-compose pull
docker-compose up -d --force-recreate
```

---

## 3. 生成 License Key

### 3.1 创建单个 Key

```bash
curl -X POST https://your-server/api/v1/admin/keys \
  -H "X-Admin-Key: YOUR_ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_email": "user@example.com",
    "customer_name": "张三",
    "plan": "personal",
    "max_devices": 1,
    "expires_at": "2027-01-01T00:00:00Z"
  }'
```

返回：
```json
{
  "key": "AIHNT-AB3CD-EF7GH-JK2MN-PQ8RS",
  "customer_email": "user@example.com",
  "plan": "personal",
  "max_devices": 1,
  "expires_at": "2027-01-01T00:00:00Z"
}
```

### 3.2 plan 类型

| plan | 说明 | 建议 max_devices |
|------|------|-----------------|
| `personal` | 个人版 | 1 |
| `team` | 团队版 | 3 |
| `enterprise` | 企业版 | 10 |

### 3.3 查看所有 Key

```bash
curl https://your-server/api/v1/admin/keys \
  -H "X-Admin-Key: YOUR_ADMIN_API_KEY"
```

### 3.4 禁用 Key（退款 / 违规）

```bash
curl -X PATCH https://your-server/api/v1/admin/keys/AIHNT-AB3CD-EF7GH-JK2MN-PQ8RS \
  -H "X-Admin-Key: YOUR_ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

### 3.5 查看某 Key 的设备激活情况

```bash
curl https://your-server/api/v1/admin/keys/AIHNT-AB3CD-EF7GH-JK2MN-PQ8RS/activations \
  -H "X-Admin-Key: YOUR_ADMIN_API_KEY"
```

---

## 4. 打包桌面应用

### 前置条件

```bash
# macOS
brew install python@3.11
pip3 install pyinstaller pyarmor cython cryptography

# 图标（可选，没有也能构建）
# 将 icon.icns 放到 ai_hunter/packaging/assets/icon.icns
```

### 4.1 Step A — 构建 Python 后端

```bash
cd ai_hunter
./packaging/build_backend.sh mac    # macOS
./packaging/build_backend.sh win    # Windows（需在 Windows 上运行）
```

脚本完成后验证：

```bash
./packaging/dist/AIHunter/AIHunter
# 应该启动 uvicorn，端口 8000
curl http://127.0.0.1:8000/health   # → {"status":"ok"}
^C  # 确认后停止
```

### 4.2 Step B — 配置 backend URL

确认 `ai_hunter/backend/license/validator.py` 中的 server_url 指向你的真实服务器：

```bash
grep license_server_url ai_hunter/backend/config/settings.py
# license_server_url: str = "https://license.aihunter.app"
```

如果域名不同，修改该默认值后重新执行 Step A。

### 4.3 Step C — 构建 Tauri 桌面安装包

```bash
cd ai_hunter/packaging/tauri
npm install

# 开发预览（不打包）
npm run tauri dev

# 正式打包
npm run tauri build
```

输出位置：

| 平台 | 文件 |
|------|------|
| macOS | `src-tauri/target/release/bundle/dmg/AIHunter_x.x.x_aarch64.dmg` |
| Windows | `src-tauri/target/release/bundle/nsis/AIHunter_x.x.x_x64-setup.exe` |

### 4.4 版本号更新

需要同步修改以下两处：

```bash
# ai_hunter/packaging/tauri/tauri.conf.json
"version": "1.0.1"

# ai_hunter/packaging/tauri/src-tauri/Cargo.toml
version = "1.0.1"
```

---

## 5. 测试

### 5.1 运行全部测试

```bash
cd ai_hunter/backend
python -m pytest tests/ --ignore=tests/test_e2e.py -q
# 预期：651 passed
```

### 5.2 只测试 license 模块

```bash
python -m pytest tests/test_license/ -v
# 预期：76 passed
```

### 5.3 测试 license server（本地 docker）

```bash
cd ai_hunter/license-server
docker-compose up -d

# 创建测试 key
curl -X POST http://localhost:8001/api/v1/admin/keys \
  -H "X-Admin-Key: change-me-admin-key" \
  -H "Content-Type: application/json" \
  -d '{"customer_email":"test@test.com","customer_name":"Test","plan":"personal","max_devices":1}'

# 激活（模拟客户端）
curl -X POST http://localhost:8001/api/v1/license/activate \
  -H "Content-Type: application/json" \
  -d '{"license_key":"AIHNT-xxxxx-xxxxx-xxxxx-xxxxx","machine_id":"testmachineid12345678901234"}'
```

---

## 6. 用户安装体验

```
1. 用户下载 AIHunter.dmg（macOS）或 AIHunter-setup.exe（Windows）
2. 安装 → 双击图标启动
3. Tauri shell 启动，Python 后端在后台静默运行（~3-5秒）
4. 窗口出现后自动检查 license：

   ┌─ 已激活 ────────────────────────────────────┐
   │  直接进入主界面                              │
   └──────────────────────────────────────────────┘

   ┌─ 未激活（首次运行）─────────────────────────┐
   │  全屏激活页：输入 AIHNT-XXXXX-... key        │
   │  → 点击激活 → 成功后进入主界面               │
   └──────────────────────────────────────────────┘

5. 首次使用：进入 Settings 配置 LLM 和 Search API Keys
6. 关闭窗口 → 最小化到系统托盘（进程继续运行）
7. 托盘右键 → Quit 彻底退出
```

### 用户数据存储位置

| 平台 | 路径 |
|------|------|
| macOS | `~/Library/Application Support/AIHunter/` |
| Windows | `%APPDATA%\AIHunter\` |
| Linux | `~/.config/AIHunter/` |

该目录包含：
- `.env` — API keys 配置
- `.aihunter_license` — 加密 license token（AES-256，机器ID绑定）
- `hunt_sessions.db` — LangGraph checkpoint SQLite DB
- `data/hunts/` — Hunt 结果 JSON 文件
- `uploads/` — 用户上传文件

> **升级应用不会丢失以上数据**（数据在用户目录，不在 app bundle 内）

---

## 7. 运维操作

### 7.1 用户换机器（设备转移）

```
方法 A（推荐）：用户在旧机器的 Settings → License → 点击「注销此设备」
              然后在新机器重新激活同一个 key

方法 B（管理员）：
```

```bash
# 撤销指定设备激活
curl -X DELETE "https://your-server/api/v1/admin/keys/AIHNT-xxxxx/activations/{activation_id}" \
  -H "X-Admin-Key: YOUR_ADMIN_API_KEY"
```

### 7.2 查看用量 / 激活状态

```bash
curl https://your-server/api/v1/admin/keys \
  -H "X-Admin-Key: YOUR_ADMIN_API_KEY" | python3 -m json.tool
```

### 7.3 License Server 日志

```bash
docker-compose logs -f license-server
```

### 7.4 数据库备份

```bash
docker exec aihunter-db pg_dump -U postgres license_db > backup_$(date +%Y%m%d).sql
```

### 7.5 常见问题排查

| 现象 | 原因 | 解决 |
|------|------|------|
| 激活提示「Cannot reach license server」| 网络/防火墙 | 检查用户网络，确认 `https://license.aihunter.app` 可访问 |
| 激活提示「Device limit reached」 | 已达设备上限 | 管理员撤销旧设备，或用户在旧机器注销 |
| 激活提示「License key not found」 | Key 输入错误 | 让用户复制粘贴，注意 O/0 I/1 混淆（已在生成时过滤） |
| 应用启动后白屏超过 30 秒 | Python 后端启动失败 | 检查 macOS Gatekeeper 是否拦截，查看 Console.app 日志 |
| 设置保存后 API key 不生效 | 需要重新发起一次 Hunt | 正常现象，settings 保存后立即生效 |
