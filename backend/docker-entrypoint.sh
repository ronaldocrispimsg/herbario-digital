#!/bin/sh
set -eu

python wait_for_db.py
alembic upgrade head
python seed.py

exec uvicorn app.main:app --host "${APP_HOST:-0.0.0.0}" --port "${APP_PORT:-8000}"
