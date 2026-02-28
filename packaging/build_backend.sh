#!/usr/bin/env bash
# ============================================================
# AI Hunter — Backend Build Script
#
# Protection strategy:
#   ALL Python business code is compiled with Cython to native
#   binaries (.so on macOS/Linux, .pyd on Windows).  The original
#   .py source files are NEVER deleted — compilation happens in a
#   temporary staging directory, then the compiled binaries are
#   copied into a clean staging tree that PyInstaller packages.
#
#   Result: the distributed bundle contains ZERO readable .py
#   source files for our own code.
#
# Usage:
#   ./packaging/build_backend.sh [mac|win] [--no-venv]
#
#   --no-venv   Use the currently active Python (must already be
#               activated) instead of creating .venv_build
#
# Cross-platform:
#   Run on macOS  → produces .so  (arm64/x86_64)
#   Run on Windows → produces .pyd (win_amd64)
#   Each platform must build its own binary — no cross-compilation.
#
# Output (for Tauri to embed):
#   packaging/dist/AIHunter/           ← onedir bundle
#   packaging/dist/AIHunter/AIHunter   ← executable (AIHunter.exe on win)
# ============================================================
set -euo pipefail

PLATFORM="${1:-mac}"
USE_VENV=true
for arg in "$@"; do
    [ "$arg" = "--no-venv" ] && USE_VENV=false
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/../backend" && pwd)"
DIST_DIR="$SCRIPT_DIR/dist"
ASSETS_DIR="$SCRIPT_DIR/assets"
VENV_DIR="$SCRIPT_DIR/.venv_build"
# Staging dir: compiled .so/.pyd + non-Python assets, NO .py source
STAGING_DIR="$DIST_DIR/staging"

# Platform-specific helpers
if [ "$PLATFORM" = "win" ]; then
    PYTHON_CMD="python"
    PIP_CMD="pip"
    VENV_ACTIVATE="$VENV_DIR/Scripts/activate"
    PATH_SEP=";"
else
    PYTHON_CMD="python3"
    PIP_CMD="pip"
    VENV_ACTIVATE="$VENV_DIR/bin/activate"
    PATH_SEP=":"
fi

# On Windows/Git Bash, shell paths are Unix-style (/d/a/...) but Python needs
# native Windows paths (D:\a\...). Convert all dir vars used in Python calls.
# cygpath is provided by Git for Windows and GitHub Actions windows runners.
if [ "$PLATFORM" = "win" ] && command -v cygpath &>/dev/null; then
    BACKEND_DIR_PY="$(cygpath -w "$BACKEND_DIR")"
    STAGING_DIR_PY="$(cygpath -w "$STAGING_DIR")"
    DIST_DIR_PY="$(cygpath -w "$DIST_DIR")"
else
    BACKEND_DIR_PY="$BACKEND_DIR"
    STAGING_DIR_PY="$STAGING_DIR"
    DIST_DIR_PY="$DIST_DIR"
fi

echo "==> Building AI Hunter backend for: $PLATFORM"
echo "    Backend  : $BACKEND_DIR"
echo "    Staging  : $STAGING_DIR"
echo "    Output   : $DIST_DIR/AIHunter/"

# ── Step 0: venv setup ────────────────────────────────────────────────────────
if [ "$USE_VENV" = true ]; then
    echo ""
    echo "==> [0/4] Setting up clean build venv..."
    if [ ! -d "$VENV_DIR" ]; then
        if [ "$PLATFORM" = "win" ]; then
            PYTHON_BIN="python"
        else
            PYTHON_BIN="/opt/homebrew/bin/python3.12"
            [ -x "$PYTHON_BIN" ] || PYTHON_BIN="python3"
        fi
        "$PYTHON_BIN" -m venv "$VENV_DIR"
        echo "    Created: $VENV_DIR"
    else
        echo "    Reusing: $VENV_DIR"
    fi
    # shellcheck disable=SC1090
    source "$VENV_ACTIVATE"
    $PIP_CMD install --upgrade pip --quiet
    $PIP_CMD install cython pyinstaller -r "$BACKEND_DIR/requirements.txt" --quiet
    echo "    Python: $($PYTHON_CMD --version)  at $(which $PYTHON_CMD)"
else
    echo ""
    echo "==> [0/4] Using active Python: $($PYTHON_CMD --version) at $(which $PYTHON_CMD)"
    $PIP_CMD install cython pyinstaller --quiet
fi

# ── Step 1: Collect .py files to compile ─────────────────────────────────────
echo ""
echo "==> [1/4] Collecting Python source files..."

# Collect all .py files that belong to OUR code (not third-party, not tests).
# main.py is excluded — it's the PyInstaller entry point and must remain .py.
COMPILE_FILES_RAW=()
while IFS= read -r -d '' f; do
    COMPILE_FILES_RAW+=("$f")
done < <(find "$BACKEND_DIR" -name "*.py" \
    -not -path "*/__pycache__/*" \
    -not -path "*/tests/*" \
    -not -path "*/build/*" \
    -not -path "*/scripts/*" \
    -not -path "*/prompts/*" \
    -not -name "main.py" \
    -not -name "setup_cython.py" \
    -not -name "routes.py" \
    -print0)
# api/routes.py is excluded from Cython: FastAPI dependency injection pattern
# is not compatible with Cython's static analysis. It contains no business
# logic (only routing/endpoint declarations) so .pyc protection is sufficient.

# On Windows/Git Bash, convert all collected paths to native Windows format
# so that Python's open(), os.path.relpath(), etc. work correctly.
COMPILE_FILES=()
if [ "$PLATFORM" = "win" ] && command -v cygpath &>/dev/null; then
    for f in "${COMPILE_FILES_RAW[@]}"; do
        COMPILE_FILES+=("$(cygpath -w "$f")")
    done
else
    COMPILE_FILES=("${COMPILE_FILES_RAW[@]}")
fi

echo "    Files to compile: ${#COMPILE_FILES[@]}"

# ── Step 2: Compile with Cython into a temp build dir ────────────────────────
echo ""
echo "==> [2/4] Compiling to native binaries with Cython (source is NOT deleted)..."

BUILD_TMP="$DIST_DIR/_cython_build_tmp"
rm -rf "$BUILD_TMP"
mkdir -p "$BUILD_TMP"

# Convert BUILD_TMP to Windows-native path for Python (cygpath already available from above check)
if [ "$PLATFORM" = "win" ] && command -v cygpath &>/dev/null; then
    BUILD_TMP_PY="$(cygpath -w "$BUILD_TMP")"
else
    BUILD_TMP_PY="$BUILD_TMP"
fi

# Write a proper setup.py in the backend dir (with __main__ guard to avoid
# multiprocessing spawn issues). Pass file list via a JSON sidecar file.
FILES_JSON="$BUILD_TMP/files.json"
# Build the Python-compatible path by joining BUILD_TMP_PY with the filename
if [ "$PLATFORM" = "win" ] && command -v cygpath &>/dev/null; then
    FILES_JSON_PY="$(cygpath -w "$BUILD_TMP/files.json")"
else
    FILES_JSON_PY="$BUILD_TMP/files.json"
fi
$PYTHON_CMD -c "import json,sys; json.dump(sys.argv[1:-1], open(sys.argv[-1],'w'))" "${COMPILE_FILES[@]}" "$FILES_JSON_PY"

SETUP_PY="$BUILD_TMP/cython_setup.py"
if [ "$PLATFORM" = "win" ] && command -v cygpath &>/dev/null; then
    SETUP_PY_PY="$(cygpath -w "$SETUP_PY")"
else
    SETUP_PY_PY="$SETUP_PY"
fi
cat > "$SETUP_PY" << 'PYEOF'
from __future__ import annotations
import sys, os, json
from pathlib import Path

def main():
    files_json = sys.argv[1]
    build_tmp  = sys.argv[2]

    with open(files_json) as f:
        src_files = json.load(f)

    # Detect backend root (parent of agents/, api/, etc.)
    backend_root = None
    for fpath in src_files:
        p = Path(fpath)
        for i, part in enumerate(p.parts):
            if part in ('agents','api','config','graph','tools','observability','license'):
                backend_root = str(Path(*p.parts[:i]))
                break
        if backend_root:
            break
    if not backend_root:
        backend_root = str(Path(os.path.commonpath(src_files)))

    print(f"    Backend root : {backend_root}")
    os.chdir(backend_root)

    rel_files = [os.path.relpath(f, backend_root) for f in src_files]
    print(f"    Compiling {len(rel_files)} files with Cython...")

    from Cython.Compiler import Options
    Options.annotate = False

    from Cython.Build import cythonize
    extensions = cythonize(
        rel_files,
        compiler_directives={"language_level": "3", "embedsignature": False},
        annotate=False,
        nthreads=0,   # 0 = no worker processes, fully serial
        quiet=True,
    )

    from setuptools import setup
    # Patch sys.argv so setuptools runs build_ext --inplace
    sys.argv = ["setup.py", "build_ext", "--inplace", "--build-temp", build_tmp]
    setup(name="aihunter_cython", packages=[], ext_modules=extensions)
    print("    Compilation complete.")

if __name__ == "__main__":
    main()
PYEOF

$PYTHON_CMD "$SETUP_PY_PY" "$FILES_JSON_PY" "$BUILD_TMP_PY" 2>&1 | grep -v "^$" | grep -v "^Compiling " | grep -v "^copying "

echo "    Cython compilation done."

# Count produced .so/.pyd files
# setuptools build_ext --inplace puts binaries in build/lib.*/ relative to backend_root (BACKEND_DIR)
EXT_SUFFIX=".so"
[ "$PLATFORM" = "win" ] && EXT_SUFFIX=".pyd"
# Write a temp script to avoid all shell quoting / backslash issues with Windows paths
COUNT_SCRIPT="$BUILD_TMP/count_binaries.py"
cat > "$COUNT_SCRIPT" << PYEOF3
import glob, os, sys
from pathlib import Path
backend = sys.argv[1]
ext_suffix = sys.argv[2]
# Search both in-place (backend/**) AND build/lib.*/ (where setuptools --inplace actually writes)
build_dirs = glob.glob(os.path.join(backend, 'build', 'lib.*'))
search_roots = [backend] + build_dirs
print(f"    [count] backend={backend}", file=sys.stderr)
print(f"    [count] build_dirs={build_dirs}", file=sys.stderr)
files = []
for root in search_roots:
    found = [f for f in glob.glob(os.path.join(root, '**', '*' + ext_suffix), recursive=True)
             if '__pycache__' not in f]
    files += found
# Deduplicate by relative path to avoid double-counting
seen = set()
unique = []
for f in files:
    key = Path(f).name
    if key not in seen:
        seen.add(key)
        unique.append(f)
print(len(unique))
PYEOF3
if [ "$PLATFORM" = "win" ] && command -v cygpath &>/dev/null; then
    COUNT_SCRIPT_PY="$(cygpath -w "$COUNT_SCRIPT")"
else
    COUNT_SCRIPT_PY="$COUNT_SCRIPT"
fi
SO_COUNT=$($PYTHON_CMD "$COUNT_SCRIPT_PY" "$BACKEND_DIR_PY" "$EXT_SUFFIX")
echo "    Native binaries created: $SO_COUNT"
[ "$SO_COUNT" -lt 10 ] && echo "ERROR: Too few binaries — compilation failed!" >&2 && exit 1

# ── Step 3: Build staging dir (binaries + assets, NO .py source) ─────────────
echo ""
echo "==> [3/4] Building clean staging directory (binaries only, no source)..."

rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"

# Copy main.py (entry point, must stay .py — contains no business logic)
cp "$BACKEND_DIR/main.py" "$STAGING_DIR/main.py"

# Write staging script to a file so paths are passed via sys.argv (not embedded
# as Python string literals), avoiding Windows backslash escape issues (\a, \b, \p…)
STAGING_SCRIPT="$BUILD_TMP/do_staging.py"
cat > "$STAGING_SCRIPT" << 'PYEOF'
import os, sys, shutil, glob
from pathlib import Path

backend_dir = sys.argv[1]
staging_dir = sys.argv[2]
platform    = sys.argv[3]

# Copy prompts directory
src_prompts = os.path.join(backend_dir, "prompts")
dst_prompts = os.path.join(staging_dir, "prompts")
if os.path.isdir(src_prompts):
    shutil.copytree(src_prompts, dst_prompts, dirs_exist_ok=True)

# Find the build/lib.* directory where setuptools put the .so/.pyd files
build_dirs = glob.glob(os.path.join(backend_dir, "build", "lib.*"))
if not build_dirs:
    print("ERROR: build/lib.* not found after Cython compilation!", file=sys.stderr)
    sys.exit(1)
build_lib = build_dirs[0]
print(f"    Compiled binaries dir: {build_lib}")

ext = ".so" if platform != "win" else ".pyd"

for pkg in ["agents", "api", "config", "graph", "tools", "observability", "license"]:
    dst = os.path.join(staging_dir, pkg)
    os.makedirs(dst, exist_ok=True)

    # Copy compiled .so/.pyd from build/lib.*/<pkg>/
    build_pkg = os.path.join(build_lib, pkg)
    so_count = 0
    if os.path.isdir(build_pkg):
        for f in Path(build_pkg).rglob(f"*{ext}"):
            shutil.copy2(str(f), dst)
            so_count += 1

    # Also pick up .so/.pyd already compiled in-place in the source dir
    src_pkg = os.path.join(backend_dir, pkg)
    if os.path.isdir(src_pkg):
        for f in Path(src_pkg).rglob(f"*{ext}"):
            dest = os.path.join(dst, os.path.basename(f))
            if not os.path.exists(dest):
                shutil.copy2(str(f), dest)
                so_count += 1

    # Copy __init__.py stubs from source (package markers only)
    if os.path.isdir(src_pkg):
        for f in Path(src_pkg).rglob("__init__.py"):
            rel = f.relative_to(src_pkg)
            dest_dir = Path(dst) / rel.parent
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(f), str(dest_dir / f.name))

    print(f"    {pkg}/: {so_count} binaries")

# api/routes.py excluded from Cython — copy as .py (compiled to .pyc in PYZ)
routes_src = os.path.join(backend_dir, "api", "routes.py")
if os.path.exists(routes_src):
    shutil.copy2(routes_src, os.path.join(staging_dir, "api", "routes.py"))
    print("    api/routes.py: copied as .py (will be .pyc in PYZ)")

# models.so from build dir root
for f in Path(build_lib).glob(f"models*{ext}"):
    shutil.copy2(str(f), staging_dir)
    print(f"    models: copied {f.name}")

print("    Staging complete.")
PYEOF

if [ "$PLATFORM" = "win" ] && command -v cygpath &>/dev/null; then
    STAGING_SCRIPT_PY="$(cygpath -w "$STAGING_SCRIPT")"
else
    STAGING_SCRIPT_PY="$STAGING_SCRIPT"
fi
$PYTHON_CMD "$STAGING_SCRIPT_PY" "$BACKEND_DIR_PY" "$STAGING_DIR_PY" "$PLATFORM"

echo "    Staging complete."

# ── Step 4: Package with PyInstaller from staging dir ────────────────────────
echo ""
echo "==> [4/4] Packaging with PyInstaller..."

ICON_OPT=""
if [ "$PLATFORM" = "mac" ]; then
    ICON_FILE="$ASSETS_DIR/icon.icns"
    [ -f "$ICON_FILE" ] && ICON_OPT="--icon=$ICON_FILE"
else
    ICON_FILE="$ASSETS_DIR/icon.ico"
    [ -f "$ICON_FILE" ] && ICON_OPT="--icon=$ICON_FILE"
fi

cd "$STAGING_DIR"

# Build --add-binary flags file for every .so/.pyd in staging
# Written to a file to avoid shell arg-length limits and path-with-spaces issues
ADD_BINARY_FLAGFILE="$BUILD_TMP/add_binary_flags.txt"
# Write a small Python script to avoid any shell variable expansion conflicts
ADD_BINARY_SCRIPT="$BUILD_TMP/gen_flags.py"
if [ "$PLATFORM" = "win" ] && command -v cygpath &>/dev/null; then
    ADD_BINARY_FLAGFILE_PY="$(cygpath -w "$ADD_BINARY_FLAGFILE")"
    ADD_BINARY_SCRIPT_PY="$(cygpath -w "$ADD_BINARY_SCRIPT")"
else
    ADD_BINARY_FLAGFILE_PY="$ADD_BINARY_FLAGFILE"
    ADD_BINARY_SCRIPT_PY="$ADD_BINARY_SCRIPT"
fi
cat > "$ADD_BINARY_SCRIPT" << PYEOF2
import os, glob, sys
staging   = sys.argv[1]
ext_      = sys.argv[2]   # .so or .pyd
sep       = sys.argv[3]   # : or ;
out_file  = sys.argv[4]
lines = []
for f in glob.glob(os.path.join(staging, '**', '*' + ext_), recursive=True):
    rel_dir = os.path.relpath(os.path.dirname(f), staging)
    lines.append('--add-binary=' + f + sep + rel_dir)
with open(out_file, 'wb') as fp:
    fp.write('\n'.join(lines).encode())
print('    Generated ' + str(len(lines)) + ' --add-binary flags')
PYEOF2

EXT_BIN=".so"
[ "$PLATFORM" = "win" ] && EXT_BIN=".pyd"
$PYTHON_CMD "$ADD_BINARY_SCRIPT_PY" "$STAGING_DIR_PY" "$EXT_BIN" "$PATH_SEP" "$ADD_BINARY_FLAGFILE_PY"

pyinstaller \
    --name "AIHunter" \
    --onedir \
    --noconfirm \
    --paths "$STAGING_DIR_PY" \
    --add-data "${STAGING_DIR_PY}/prompts${PATH_SEP}prompts" \
    $(tr -d '\r' < "$ADD_BINARY_FLAGFILE" | tr '\n' ' ') \
    --hidden-import "api.app" \
    --hidden-import "api.routes" \
    --hidden-import "api.settings_routes" \
    --hidden-import "api.hunt_store" \
    --hidden-import "api.sse" \
    --hidden-import "config.settings" \
    --hidden-import "agents.insight_agent" \
    --hidden-import "agents.keyword_gen_agent" \
    --hidden-import "agents.search_agent" \
    --hidden-import "agents.lead_extract_agent" \
    --hidden-import "agents.email_craft_agent" \
    --hidden-import "agents.parse_description_agent" \
    --hidden-import "graph.builder" \
    --hidden-import "graph.state" \
    --hidden-import "graph.checkpointer" \
    --hidden-import "graph.evaluate" \
    --hidden-import "tools.registry" \
    --hidden-import "tools.llm_client" \
    --hidden-import "tools.llm_output" \
    --hidden-import "tools.email_finder" \
    --hidden-import "tools.email_verifier" \
    --hidden-import "tools.google_search" \
    --hidden-import "tools.tavily_search" \
    --hidden-import "tools.web_search" \
    --hidden-import "tools.jina_reader" \
    --hidden-import "tools.pdf_parser" \
    --hidden-import "tools.docx_parser" \
    --hidden-import "tools.excel_parser" \
    --hidden-import "tools.platform_registry" \
    --hidden-import "tools.react_runner" \
    --hidden-import "tools.contact_extractor" \
    --hidden-import "tools.company_website_finder" \
    --hidden-import "tools.url_filter" \
    --hidden-import "tools.ocr" \
    --hidden-import "tools.amap_search" \
    --hidden-import "tools.baidu_search" \
    --hidden-import "tools.brave_search" \
    --hidden-import "tools.google_maps_search" \
    --hidden-import "observability.setup" \
    --hidden-import "observability.cost_tracker" \
    --hidden-import "models" \
    --hidden-import "uvicorn.logging" \
    --hidden-import "uvicorn.loops" \
    --hidden-import "uvicorn.loops.auto" \
    --hidden-import "uvicorn.protocols" \
    --hidden-import "uvicorn.protocols.http" \
    --hidden-import "uvicorn.protocols.http.auto" \
    --hidden-import "uvicorn.lifespan" \
    --hidden-import "uvicorn.lifespan.on" \
    --hidden-import "cryptography" \
    --hidden-import "cryptography.fernet" \
    --hidden-import "cryptography.hazmat" \
    --hidden-import "cryptography.hazmat.primitives" \
    --hidden-import "cryptography.hazmat.backends" \
    --collect-all "cryptography" \
    --hidden-import "httpx" \
    --collect-all "litellm" \
    --exclude-module "litellm.proxy.guardrails" \
    --exclude-module "litellm.proxy.tests" \
    --exclude-module "litellm.tests" \
    --exclude-module "litellm.proxy.example_config_yaml" \
    --collect-all "langchain_core" \
    --collect-all "langgraph" \
    --collect-all "langfuse" \
    --collect-all "pymupdf4llm" \
    --collect-all "pymupdf" \
    --collect-all "pandas" \
    --collect-all "tenacity" \
    --collect-all "httpx" \
    $([ "$PLATFORM" != "win" ] && echo "--collect-all uvloop") \
    --collect-all "pydantic" \
    --collect-all "pydantic_settings" \
    --hidden-import "pydantic_settings" \
    --collect-all "multipart" \
    --hidden-import "multipart" \
    --hidden-import "python_multipart" \
    --collect-all "sse_starlette" \
    --hidden-import "sse_starlette" \
    --collect-all "jose" \
    --hidden-import "jose" \
    --collect-all "openpyxl" \
    --collect-all "docx" \
    --hidden-import "docx" \
    --collect-all "starlette" \
    --distpath "$DIST_DIR_PY" \
    $ICON_OPT \
    main.py

# Cleanup temp build dir
rm -rf "$BUILD_TMP"

# Remove litellm proxy server and test dirs — they contain deeply nested paths
# that breach Windows NSIS MAX_PATH (260 char) limit during installer creation.
# The app uses litellm as an LLM client only; the proxy server is never needed.
if [ -d "$DIST_DIR/AIHunter/_internal/litellm" ]; then
    echo "==> Pruning litellm proxy/tests (long-path risk on Windows)..."
    rm -rf "$DIST_DIR/AIHunter/_internal/litellm/proxy" 2>/dev/null || true
    rm -rf "$DIST_DIR/AIHunter/_internal/litellm/tests" 2>/dev/null || true
    rm -rf "$DIST_DIR/AIHunter/_internal/litellm/fine_tuning" 2>/dev/null || true
    rm -rf "$DIST_DIR/AIHunter/_internal/litellm/realtime_api" 2>/dev/null || true
    echo "    Done."
fi

echo ""
echo "==> Build complete!"
echo "    Bundle: $DIST_DIR/AIHunter/"
du -sh "$DIST_DIR/AIHunter/" 2>/dev/null || true
echo ""
echo "    Protection summary:"
echo "      agents/ api/ graph/ tools/ config/ observability/ license/ models"
echo "      → ALL compiled to .so (macOS) / .pyd (Windows) native binaries"
echo "      → ZERO readable .py source in the distributed bundle"
echo "      → main.py: entry point only (uvicorn launcher, no logic)"
echo "      → prompts/: text templates (data, not code)"
echo ""
echo "    Next: cd packaging/tauri/src-tauri && ../node_modules/.bin/tauri build"
