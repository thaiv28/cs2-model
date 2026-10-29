#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p db
rm -f db/cs2.db
for script in scripts/[0-9][0-9][0-9]_*; do
    case "$script" in
        *.sql) uv run --no-sync python - "$script" <<'PY'
from pathlib import Path
import sqlite3
import sys
with sqlite3.connect('db/cs2.db') as conn:
    conn.executescript(Path(sys.argv[1]).read_text())
PY
            ;;
        *.py) uv run --no-sync python "$script" ;;
    esac
done
