#!/usr/bin/env bash
# V9's tests/test_api.py points NEXUS_DB at a temp database at import time, which leaks into other files in one pytest session.
# Running each file in its own process avoids that (pre-existing isolation issue, not a regression).
cd "$(dirname "$0")/../backend" || exit 1
rc=0; for f in tests/test_*.py; do python3 -m pytest "$f" -q 2>&1 | tail -1 | sed "s|^|$f: |"; python3 -m pytest "$f" -q >/dev/null 2>&1 || rc=1; done; exit $rc
