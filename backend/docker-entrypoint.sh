#!/bin/sh
set -eu

python wait_for_db.py
python seed.py

exec uvicorn main:app --host "${APP_HOST:-0.0.0.0}" --port "${APP_PORT:-8000}"
