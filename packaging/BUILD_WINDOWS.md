# Windows EXE Build Guide — AI Hunter

## Prerequisites (install once on Windows machine)

1. **Python 3.10** (must match macOS build — same CPython minor version)
   - Download: https://www.python.org/downloads/release/python-31011/
   - Install to `C:\Python310\`, tick "Add to PATH"
   - Verify: `python --version` → `Python 3.10.x`

2. **Rust + Cargo**
   - Download: https://rustup.rs/
   - Verify: `rustc --version`, `cargo --version`

3. **cargo-tauri** (native CLI, avoids napi Node.js wrapper bug)
   ```
   cargo install tauri-cli --version "^2" --locked
   ```

4. **Visual Studio Build Tools** (required by Cython + Rust)
   - Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Select: "Desktop development with C++"

5. **NSIS** (installer generator, required by Tauri for EXE)
   - Download: https://nsis.sourceforge.io/Download
   - Install to default path (`C:\Program Files (x86)\NSIS`)

6. **Node.js 18+** (for frontend build)
   - Download: https://nodejs.org/

7. **Git for Windows** (provides Git Bash to run the .sh script)
   - Download: https://git-scm.com/download/win

---

## Step 1 — Clone / sync the repo

```bash
git clone <repo-url>
cd b2binsights/ai_hunter
```

---

## Step 2 — Build Python backend (Cython .pyd + PyInstaller)

Open **Git Bash** and run:

```bash
cd packaging
bash build_backend.sh win
```

This will:
- Create `.venv_build/` with clean Python 3.10 venv
- Compile all business code to `.pyd` native binaries via Cython
- Stage binaries into `dist/staging/`
- Package with PyInstaller → `dist/AIHunter/AIHunter.exe`

Expected output:
```
agents/: 7 binaries
api/: 5 binaries
...
Total .pyd binaries: 50
```

---

## Step 3 — Build frontend

```bash
cd frontend
npm install
npm run build
# Output: frontend/dist/
```

---

## Step 4 — Build Tauri EXE installer

**IMPORTANT: run from `src-tauri/` directory**, not the parent `tauri/`.

```bash
cd packaging/tauri/src-tauri
cargo tauri build --bundles nsis --config "{\"build\":{\"beforeBuildCommand\":\"\"}}"
```

Output:
```
packaging/tauri/target/release/bundle/nsis/AI Hunter_1.0.0_x64-setup.exe
```

---

## Encryption verification (before shipping)

Run in Git Bash after Step 2:

```bash
python -c "
import os, glob
dist = 'dist/AIHunter/_internal'
for pkg in ['agents','api','config','graph','tools','observability','license']:
    d = os.path.join(dist, pkg)
    pyds = glob.glob(os.path.join(d, '*.pyd'))
    pys  = [f for f in glob.glob(os.path.join(d,'*.py')) if '__init__' not in f]
    print(f'{pkg}/: {len(pyds)} .pyd  {len(pys)} raw .py')
"
```

Expected: all packages have `0 raw .py`.

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `cl.exe not found` | Install VS Build Tools, restart Git Bash |
| `error: Microsoft Visual C++ 14.0 is required` | Same as above |
| `ModuleNotFoundError: No module named 'xyz'` | Add `--hidden-import xyz` to build_backend.sh |
| `No package info in the config file` | Make sure you run `cargo tauri build` from `src-tauri/`, not `tauri/` |
| NSIS not found during Tauri build | Install NSIS and ensure it's in PATH |
| `.pyd` files not in bundle | Verify Step 2 produced `dist/staging/agents/*.pyd` etc. |

---

## File locations

| Artifact | Path |
|----------|------|
| Windows EXE installer | `packaging/tauri/target/release/bundle/nsis/AI Hunter_1.0.0_x64-setup.exe` |
| Python backend bundle | `packaging/dist/AIHunter/` |
| macOS DMG | `packaging/tauri/target/release/bundle/dmg/AI Hunter_1.0.0_aarch64.dmg` |
