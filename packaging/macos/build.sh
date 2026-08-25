#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "macOS packaging must run on macOS" >&2
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"

PYTHONPATH=src "$PYTHON_BIN" - <<'PY'
import json
from pathlib import Path
from bke_demo_app.version import APP_VERSION

manifest = json.loads(Path("bke.manifest.json").read_text(encoding="utf-8"))
if manifest["version"] != APP_VERSION:
    raise SystemExit(f"manifest version {manifest['version']} != app version {APP_VERSION}")
if manifest["platform"] != "macos":
    raise SystemExit("macOS package requires manifest platform=macos")
if manifest["entryPoint"] != "BKE Institution Suite":
    raise SystemExit("macOS package requires manifest entryPoint='BKE Institution Suite'")
PY

if ! "$PYTHON_BIN" -c 'import PyInstaller' >/dev/null 2>&1; then
  echo "PyInstaller is required. Install it with: $PYTHON_BIN -m pip install pyinstaller" >&2
  exit 1
fi

rm -rf build dist

"$PYTHON_BIN" -m PyInstaller \
  --clean \
  --noconfirm \
  --windowed \
  --onedir \
  --name "BKE Institution Suite" \
  --paths src \
  packaging/macos/entry.py

cp bke.manifest.json "dist/BKE Institution Suite/bke.manifest.json"

echo "Built: $ROOT/dist/BKE Institution Suite"
