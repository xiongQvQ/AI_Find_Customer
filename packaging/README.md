# AI Hunter — Packaging & Distribution

## Architecture Overview

```text
User's Machine
├── Tauri Desktop Shell  (Rust, native .dmg / .exe installer)
│   ├── Frontend  (React/Vite static build, embedded)
│   ├── Sidecar: Python backend  (PyInstaller --onedir bundle)
│   │   ├── FastAPI server  (localhost:8000)
│   │   ├── license/  (Cython-compiled: fingerprint, token_store, validator)
│   │   └── All AI Hunter agents + tools
│   └── System tray  (Show / Hide / Quit)
│
└── User config (survives app updates, writable by user):
      macOS:   ~/Library/Application Support/AIHunter/.env
      Windows: %APPDATA%\AIHunter\.env
      Linux:   ~/.config/AIHunter/.env
               ~/.config/AIHunter/.aihunter_license  (encrypted JWT token)

Your VPS
└── License Server  (FastAPI + PostgreSQL, Docker Compose)
    ├── POST /api/v1/license/activate
    ├── POST /api/v1/license/refresh
    ├── POST /api/v1/license/deactivate
    └── /api/v1/admin/*  (key management)
```

## User Experience Flow

```text
1. User double-clicks AI Hunter icon
2. Tauri spawns Python backend sidecar (hidden window)
3. Tauri polls port 8000 — shows window when backend is ready (~3-5s)
4. Frontend checks license status:
   ├─ Valid token (offline OK up to 7 days)  →  show main app
   └─ No token / expired                     →  show License Activation screen
5. User enters AIHNT-XXXXX-... key → activates online → enters main app
6. First run: Settings page to configure LLM & Search API keys
7. Closing window minimizes to system tray (does NOT quit)
8. Quit via tray menu → gracefully kills backend → exits
```

## License Flow (Hybrid Online/Offline)

```text
App startup
  └─► Read local encrypted token (machine-ID-keyed AES-256)
        ├─ Valid + >2 days left  →  Start immediately (no network needed)
        ├─ Valid + <2 days left  →  Try refresh online → start either way
        └─ Missing / expired     →  Show activation screen
                                     └─ No network + expired → deny startup
```

## Code Protection Layers

| Layer | Tool | What it protects |
| ----- | ---- | ---------------- |
| License core | Cython → .so/.pyd | fingerprint, token_store, validator |
| Business logic | PyArmor | All other .py agent/tool files |
| Binary packing | PyInstaller --onedir | Bundles interpreter + bytecode |
| Transport | HTTPS + JWT (HS256) | License server communication |
| Token storage | AES-256 / Fernet | Local token keyed to machine ID |

## Build Steps

### 1. Deploy License Server (one-time)

```bash
cd license-server
cp .env.example .env
# Set JWT_SECRET and ADMIN_API_KEY:
#   openssl rand -hex 32
docker-compose up -d
```

### 2. Generate a License Key for a Customer

```bash
curl -X POST https://your-license-server/api/v1/admin/keys \
  -H "X-Admin-Key: YOUR_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_email": "customer@example.com",
    "customer_name": "Jane Smith",
    "plan": "personal",
    "max_devices": 1,
    "expires_at": "2026-12-31T00:00:00Z"
  }'
# → { "key": "AIHNT-XXXXX-XXXXX-XXXXX-XXXXX", ... }
```

### 3. Build the Desktop App

```bash
# Step A: Build + obfuscate Python backend
./packaging/build_backend.sh mac    # or: win
# Output: packaging/dist/AIHunter/

# Step B: Verify the bundle works standalone
./packaging/dist/AIHunter/AIHunter  # should start on port 8000

# Step C: Build the Tauri shell (embeds frontend + sidecar)
cd packaging/tauri
npm install
npm run tauri build
```

### 4. Output Installers

- **macOS**: `packaging/tauri/src-tauri/target/release/bundle/dmg/AIHunter_1.0.0_aarch64.dmg`
- **Windows**: `packaging/tauri/src-tauri/target/release/bundle/nsis/AIHunter_1.0.0_x64-setup.exe`

### 4.1 Windows "one-click" behavior (zero command line for end users)

The Windows installer is designed for a non-technical user flow:

1. Double-click `AIHunter_...-setup.exe`
2. Click through installer UI
3. Launch AI Hunter from Start Menu/Desktop

No Python, Node.js, Rust, or manual command execution is required on the end-user machine.

Important packaging notes:

- Frontend static assets are embedded in the Tauri app bundle.
- Backend (`AIHunter.exe` + `_internal/`) is bundled as Tauri resources and launched automatically by the desktop shell.
- WebView2 install mode is set to **offline installer** for Windows, so first install does not rely on downloading runtime over network.

### 4.2 Why setup.exe can be smaller than expected

`*-setup.exe` is an NSIS compressed installer, not the final installed size.
It is normal for installer size (e.g. ~80–120MB) to be significantly smaller than the installed app directory.

To validate packaging completeness, check:

- CI "Verify backend bundle" and "Smoke-test backend EXE" steps pass.
- `frontend/dist/index.html` exists before Tauri build.
- Installed app can launch on a clean Windows machine by double-clicking only.

### 5. App Icons (required before building)

Place icons in `packaging/assets/`:

- `icon.icns` — macOS
- `icon.ico`  — Windows

See `packaging/assets/README.md` for generation instructions.

## Updating the App

The Tauri updater plugin checks `https://releases.aihunter.app` on startup.
Users see a dialog and can update without re-entering their license key
(token is stored in user app-data, not inside the app bundle).
