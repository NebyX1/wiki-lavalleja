#!/bin/sh
set -e

echo "Setting up Prometheus multiprocess directory at $PROMETHEUS_MULTIPROC_DIR"
rm -rf "$PROMETHEUS_MULTIPROC_DIR"
mkdir -p "$PROMETHEUS_MULTIPROC_DIR"

echo "Running database migrations..."
if ! flask db upgrade; then
    echo "FATAL: Database migration failed. The application will not start."
    echo "To recover: inspect the migration error, fix the issue, and restart."
    exit 1
fi

echo "Starting Gunicorn..."
exec gunicorn -c /app/gunicorn.conf.py "wsgi:app"