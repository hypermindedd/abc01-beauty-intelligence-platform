#!/bin/bash
set -e
cd "$(dirname "$0")"
PY="$(command -v python3 || true)"
if [ -z "$PY" ]; then echo "Python 3 پیدا نشد."; exit 1; fi
if [ ! -d ".venv" ]; then "$PY" -m venv .venv; fi
source .venv/bin/activate
python -m pip install -r requirements.txt >/dev/null
export PYTHONPATH="$(pwd)"
python tests/test_integrity.py
python tests/test_preview_quarantine.py
python tests/smoke_e2e.py
echo ""
echo "ALL v0.3.0 TESTS PASS."
read -n 1 -s -r -p "Press any key to close..."
