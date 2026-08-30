#!/bin/bash
set -u
cd "$(dirname "$0")"

PY="$(command -v python3 || true)"
if [ -z "$PY" ]; then
 echo "Python 3 پیدا نشد."
 read -n 1 -s -r -p "Press any key to close..."
 exit 1
fi

if [ ! -d ".venv" ]; then
 echo "Creating local virtual environment..."
 "$PY" -m venv .venv || exit 1
fi
source .venv/bin/activate

STAMP=".venv/.abc_requirements_installed"
REQ_HASH="$(shasum -a 256 requirements.txt | awk '{print $1}')"
OLD_HASH="$(cat "$STAMP" 2>/dev/null || true)"
if [ "$REQ_HASH" != "$OLD_HASH" ]; then
 echo "Installing/updating demo dependencies..."
 python -m pip install --upgrade pip >/dev/null
 python -m pip install -r requirements.txt || {
   echo "Dependency installation failed. Internet access may be required the first time."
   read -n 1 -s -r -p "Press any key to close..."
   exit 1
 }
 echo "$REQ_HASH" > "$STAMP"
fi

REQUESTED="${ABC_DEMO_PORT:-8775}"
PORT="$(python - "$REQUESTED" <<'PY'
import socket,sys
r=int(sys.argv[1])
def free(p):
  s=socket.socket()
  try:s.bind(("127.0.0.1",p));return True
  except OSError:return False
  finally:s.close()
if free(r):print(r)
else:
  for p in range(8776,8899):
    if free(p):print(p);break
PY
)"
URL="http://127.0.0.1:${PORT}"
LOG="/tmp/abc_demo_02_${PORT}.log"
echo "Starting ABC.DEMO.02 at $URL"
python -m uvicorn server.app:app --host 127.0.0.1 --port "$PORT" >"$LOG" 2>&1 &
PID=$!
cleanup(){ kill "$PID" >/dev/null 2>&1 || true; }
trap cleanup EXIT INT TERM

READY=0
for _ in {1..60}; do
 if ! kill -0 "$PID" >/dev/null 2>&1; then
  echo "Server failed:"; cat "$LOG"; read -n 1 -s -r -p "Press any key..."; exit 1
 fi
 if curl -fsS "$URL/api/health" >/dev/null 2>&1; then READY=1; break; fi
 sleep .2
done
if [ "$READY" -ne 1 ]; then echo "Server did not become ready."; cat "$LOG"; exit 1; fi

open "$URL"
echo ""
echo "ABC.DEMO.02 is running: $URL"
if [ -f ".env.local" ]; then echo "LIVE provider config: local .env.local found"; else echo "Mode: Showcase fallback (run SET_OPENAI_KEY.command for live generation)"; fi
echo "Press Ctrl+C to stop."
wait "$PID"
