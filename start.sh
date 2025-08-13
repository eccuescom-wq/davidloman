#!/usr/bin/env bash
set -e
if command -v python >/dev/null 2>&1; then PY=python; elif command -v python3 >/dev/null 2>&1; then PY=python3; else echo "No python found"; exit 127; fi
exec "$PY" bot_webhook.py
