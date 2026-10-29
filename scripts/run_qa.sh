#!/usr/bin/env bash
# Starts the 2 backends + 2 Vite servers, runs scripts/qa_browser.py, then stops everything.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
export NEXUS_WRITE_TOKEN=local-test
PIDS=()
(cd backend && python3 -m uvicorn app.main:app --port 8000 >/tmp/be0.log 2>&1) & PIDS+=($!)
(cd backend && NEXUS_AUTH_ENABLED=1 NEXUS_AUTH_SECRET=qa-secret NEXUS_USERS='exec:Demo-pass-1:viewer;root:Admin-pass-1:admin' python3 -m uvicorn app.main:app --port 8001 >/tmp/be1.log 2>&1) & PIDS+=($!)
(cd frontend && npx vite --port 5173 --strictPort >/tmp/fe0.log 2>&1) & PIDS+=($!)
(cd frontend && NEXUS_API=http://127.0.0.1:8001 npx vite --port 5174 --strictPort >/tmp/fe1.log 2>&1) & PIDS+=($!)
for u in 8000/api/auth/status 8001/api/auth/status 5173/ 5174/; do
  for i in $(seq 1 40); do curl -sf "localhost:$u" >/dev/null 2>&1 && break; sleep 0.5; done
done
python3 scripts/qa_browser.py; RC=$?
kill "${PIDS[@]}" 2>/dev/null; pkill -f "vite --port 517" 2>/dev/null; pkill -f "uvicorn app.main:app --port 800" 2>/dev/null
exit $RC
