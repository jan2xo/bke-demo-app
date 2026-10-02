#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "macOS packaging must run on macOS" >&2
  exit 1
fi

python - <<'PY'
import json
from pathlib import Path
from bke_demo_app.version import APP_VERSION

manifest = json.loads(Path("bke.manifest.json").read_text(encoding="utf-8"))
if manifest["version"] != APP_VERSION:
    raise SystemExit(f"manifest version {manifest['version']} != app version {APP_VERSION}")
if manifest["platform"] != "macos":
    raise SystemExit("macOS package requires manifest platform=macos")
if manifest["entryPoint"] != "BKE Demo App":
    raise SystemExit("macOS package requires manifest entryPoint='BKE Demo App'")
PY

rm -rf build dist

pyinstaller \
  --clean \
  --noconfirm \
  --windowed \
  --onedir \
  --name "BKE Demo App" \
  --paths src \
  packaging/macos/entry.py

cp bke.manifest.json "dist/BKE Demo App/bke.manifest.json"

echo "Built: $ROOT/dist/BKE Demo App"
