#!/bin/sh
set -e

echo "Running migrations..."
python -m alembic upgrade head

if [ "${RUN_DEMO_SEED:-false}" = "true" ]; then
  echo "RUN_DEMO_SEED=true detected. Running demo seed..."
  python scripts/dev_seed.py
else
  echo "RUN_DEMO_SEED is not true. Skipping demo seed."
fi

echo "Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
