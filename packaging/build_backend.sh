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
    print(f"    Compiling {len(rel_files)} .py files with Cython...")

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

    # Also compile any pre-generated .c files that have no .py counterpart
    # (e.g. license/ modules whose .py source is not committed to git).
    from setuptools import Extension
    import glob as _glob
    c_only_exts = []
    for c_file in _glob.glob(os.path.join(backend_root, '**', '*.c'), recursive=True):
        if '__pycache__' in c_file or 'build' + os.sep in c_file:
            continue
        rel_c = os.path.relpath(c_file, backend_root)
        # Derive dotted module name: license/validator.c -> license.validator
        parts = Path(rel_c).with_suffix('').parts
        mod_name = '.'.join(parts)
        # Skip if a .py version is already being compiled by Cython
        py_counterpart = os.path.splitext(c_file)[0] + '.py'
        if os.path.exists(py_counterpart):
            continue
        # Skip setup files
        if Path(c_file).stem in ('setup_cython', 'setup'):
            continue
        print(f"    Compiling pre-generated .c: {rel_c} -> {mod_name}")
        c_only_exts.append(Extension(mod_name, sources=[rel_c]))

    all_extensions = extensions + c_only_exts

    from setuptools import setup
    # Patch sys.argv so setuptools runs build_ext --inplace
    sys.argv = ["setup.py", "build_ext", "--inplace", "--build-temp", build_tmp]
    setup(name="aihunter_cython", packages=[], ext_modules=all_extensions)
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

    # Ensure top-level __init__.py exists — Python requires it to recognise
    # the directory as a package. Create an empty stub if the source has none.
    init_dst = Path(dst) / "__init__.py"
    if not init_dst.exists():
        init_dst.touch()

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

# ── Step 3.5: Register staging dir in site-packages so PyInstaller finds .pyd ──
# PyInstaller analysis actually imports modules; it can only find our Cython
# .pyd files if the staging dir is on sys.path. A .pth file in site-packages
# is the cleanest way to add it without touching the source tree.
echo ""
echo "==> [3.5/4] Registering staging dir with Python site-packages..."
REGISTER_SCRIPT="$BUILD_TMP/register_staging.py"
if [ "$PLATFORM" = "win" ] && command -v cygpath &>/dev/null; then
    REGISTER_SCRIPT_PY="$(cygpath -w "$REGISTER_SCRIPT")"
else
    REGISTER_SCRIPT_PY="$REGISTER_SCRIPT"
fi
cat > "$REGISTER_SCRIPT" << 'PYEOF5'
import site, sys, os
staging = sys.argv[1]
# Find the first writable site-packages dir
sp = None
for d in site.getsitepackages():
    if os.path.isdir(d) and os.access(d, os.W_OK):
        sp = d
        break
if not sp:
    print(f"ERROR: no writable site-packages found in {site.getsitepackages()}", file=sys.stderr)
    sys.exit(1)
pth = os.path.join(sp, "aihunter_staging.pth")
with open(pth, "w") as f:
    f.write(staging + "\n")
print(f"    Wrote {pth}")
print(f"    Contents: {staging}")
# Verify Python can now import from staging — abort if it fails so we catch
# missing .pyd files at build time rather than at smoke-test time.
sys.path.insert(0, staging)
try:
    import importlib, importlib.util
    # List all .pyd/.so files found under staging for diagnostics
    import glob
    ext = ".pyd" if sys.platform == "win32" else ".so"
    found = sorted(glob.glob(os.path.join(staging, "**", "*" + ext), recursive=True))
    print(f"    Staging {ext} inventory ({len(found)} files):")
    for f in found:
        print(f"      {f}")
    import license
    print(f"    import license: OK  ({license.__file__})")
    import license.settings_store
    print(f"    import license.settings_store: OK  ({license.settings_store.__file__})")
    import license.validator
    print(f"    import license.validator: OK")
except ImportError as e:
    print(f"ERROR: import check failed: {e}", file=sys.stderr)
    print(f"  staging dir: {staging}", file=sys.stderr)
    print(f"  sys.path: {sys.path[:5]}", file=sys.stderr)
    sys.exit(1)
PYEOF5
$PYTHON_CMD "$REGISTER_SCRIPT_PY" "$STAGING_DIR_PY"

# ── Step 4: Package with PyInstaller (Python-driven, no shell quoting) ────────
echo ""
echo "==> [4/4] Packaging with PyInstaller..."

# Determine icon path
ICON_FILE=""
if [ "$PLATFORM" = "mac" ]; then
    ICON_FILE="$ASSETS_DIR/icon.icns"
else
    ICON_FILE="$ASSETS_DIR/icon.ico"
fi

# Write a Python runner script — avoids ALL shell quoting / Windows path issues
PYI_RUNNER="$BUILD_TMP/run_pyinstaller.py"
if [ "$PLATFORM" = "win" ] && command -v cygpath &>/dev/null; then
    PYI_RUNNER_PY="$(cygpath -w "$PYI_RUNNER")"
else
    PYI_RUNNER_PY="$PYI_RUNNER"
fi

cat > "$PYI_RUNNER" << 'PYEOF4'
import glob, os, sys
from pathlib import Path

staging   = sys.argv[1]   # staging dir
dist_dir  = sys.argv[2]   # output distpath
platform  = sys.argv[3]   # 'win' | 'mac' | 'linux'
icon_file = sys.argv[4]   # path to icon or ''

os.chdir(staging)

ext = ".pyd" if platform == "win" else ".so"

# Verify .pyd/.so files exist
binaries = glob.glob(os.path.join(staging, '**', '*' + ext), recursive=True)
print(f"    Found {len(binaries)} {ext} files in staging:")
for b in sorted(binaries):
    print(f"      {b}")
if not binaries:
    print("ERROR: No compiled binaries found in staging — Cython build failed!", file=sys.stderr)
    sys.exit(1)

sep = ";" if platform == "win" else ":"

# Build args list
args = [
    "main.py",
    "--name", "AIHunter",
    "--onedir",
    "--noconfirm",
    "--paths", staging,
    "--add-data", os.path.join(staging, "prompts") + sep + "prompts",
    "--distpath", dist_dir,
]

if platform == "win":
    args.append("--noconsole")

if icon_file and os.path.exists(icon_file):
    args += ["--icon", icon_file]

# Our custom .pyd/.so extension modules are now on sys.path via the .pth file
# written to site-packages in step 3.5. PyInstaller will find and bundle them
# automatically during analysis — no --add-binary needed.

# Hidden imports for our packages (needed for module discovery)
OUR_HIDDEN = [
    "api.app", "api.routes", "api.settings_routes", "api.hunt_store", "api.sse",
    "config.settings",
    "agents.insight_agent", "agents.keyword_gen_agent", "agents.search_agent",
    "agents.lead_extract_agent", "agents.email_craft_agent", "agents.parse_description_agent",
    "graph.builder", "graph.state", "graph.checkpointer", "graph.evaluate",
    "license", "license.validator", "license.fingerprint",
    "license.token_store", "license.settings_store",
    "tools.registry", "tools.llm_client", "tools.llm_output",
    "tools.email_finder", "tools.email_verifier", "tools.google_search",
    "tools.tavily_search", "tools.web_search", "tools.jina_reader",
    "tools.pdf_parser", "tools.docx_parser", "tools.excel_parser",
    "tools.platform_registry", "tools.react_runner", "tools.contact_extractor",
    "tools.company_website_finder", "tools.url_filter", "tools.ocr",
    "tools.amap_search", "tools.baidu_search", "tools.brave_search",
    "tools.google_maps_search",
    "observability.setup", "observability.cost_tracker",
    "models",
    "uvicorn.logging", "uvicorn.loops", "uvicorn.loops.auto",
    "uvicorn.protocols", "uvicorn.protocols.http", "uvicorn.protocols.http.auto",
    "uvicorn.lifespan", "uvicorn.lifespan.on",
    "cryptography", "cryptography.fernet", "cryptography.hazmat",
    "cryptography.hazmat.primitives", "cryptography.hazmat.backends",
    "httpx", "pydantic_settings",
    "multipart", "multipart.multiparser", "multipart.decoders",
    "sse_starlette",
    "jose", "jose.jwt", "jose.exceptions",
    "docx", "docx.oxml.ns",
    "tavily", "anyio", "sniffio", "h11", "click", "aiosqlite",
]
for imp in OUR_HIDDEN:
    args += ["--hidden-import", imp]

# collect-all for third-party packages with dynamic imports
COLLECT_ALL = [
    "cryptography", "litellm", "langchain_core", "langgraph", "langfuse",
    "pymupdf4llm", "pymupdf", "pandas", "tenacity", "httpx",
    "pydantic", "pydantic_settings", "multipart", "sse_starlette",
    "jose", "openpyxl", "docx", "starlette", "tavily", "anyio", "aiosqlite",
]
if platform != "win":
    COLLECT_ALL.append("uvloop")
for pkg in COLLECT_ALL:
    args += ["--collect-all", pkg]

EXCLUDE = [
    "litellm.proxy.guardrails", "litellm.proxy.tests",
    "litellm.tests", "litellm.proxy.example_config_yaml",
]
for ex in EXCLUDE:
    args += ["--exclude-module", ex]

print(f"    Running PyInstaller with {len(args)} args")
print(f"    First 10: {args[:10]}")

import PyInstaller.__main__
PyInstaller.__main__.run(args)
PYEOF4

$PYTHON_CMD "$PYI_RUNNER_PY" "$STAGING_DIR_PY" "$DIST_DIR_PY" "$PLATFORM" "$ICON_FILE"

# Cleanup temp build dir
rm -rf "$BUILD_TMP"

# Remove deeply nested test/example dirs from third-party packages that breach
# Windows NSIS MAX_PATH (260 char) limit. None of these are needed at runtime.
BUNDLE_INTERNAL="$DIST_DIR/AIHunter/_internal"
if [ -d "$BUNDLE_INTERNAL" ]; then
    echo "==> Pruning deep-path dirs from bundle (Windows MAX_PATH safety)..."
    # litellm: proxy server, tests, optional API modules not used by this app
    rm -rf "$BUNDLE_INTERNAL/litellm/proxy" 2>/dev/null || true
    rm -rf "$BUNDLE_INTERNAL/litellm/tests" 2>/dev/null || true
    rm -rf "$BUNDLE_INTERNAL/litellm/fine_tuning" 2>/dev/null || true
    rm -rf "$BUNDLE_INTERNAL/litellm/realtime_api" 2>/dev/null || true
    # langfuse: cookbooks and integration tests
    rm -rf "$BUNDLE_INTERNAL/langfuse/cookbooks" 2>/dev/null || true
    rm -rf "$BUNDLE_INTERNAL/langfuse/tests" 2>/dev/null || true
    # langchain_core: test suites
    rm -rf "$BUNDLE_INTERNAL/langchain_core/tests" 2>/dev/null || true
    # langgraph: tests
    rm -rf "$BUNDLE_INTERNAL/langgraph/tests" 2>/dev/null || true
    echo "    Done. Bundle size after prune:"
    du -sh "$BUNDLE_INTERNAL" 2>/dev/null || true
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
