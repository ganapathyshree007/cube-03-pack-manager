#!/bin/sh
# Production entrypoint: fix DATABASE_URL scheme, run migrations, then start the app.
# This runs as the non-privileged 'pack' user; the Render DB user has sufficient
# privileges to CREATE TABLE, enable RLS, and FORCE RLS on its own tables.
set -e

# Render Managed PostgreSQL provides the URL as:
#   postgresql://user:pass@host/db?sslmode=require
# SQLAlchemy with the psycopg (v3) driver requires:
#   postgresql+psycopg://user:pass@host/db?sslmode=require
#
# Translate in-place if the scheme does not already include the driver prefix.
if [ -n "$DATABASE_URL" ]; then
    case "$DATABASE_URL" in
        postgresql+psycopg://*)
            # Already correct — nothing to do.
            ;;
        postgresql://*)
            DATABASE_URL="postgresql+psycopg://${DATABASE_URL#postgresql://}"
            export DATABASE_URL
            ;;
        postgres://*)
            # Some providers emit "postgres://" (non-standard).
            DATABASE_URL="postgresql+psycopg://${DATABASE_URL#postgres://}"
            export DATABASE_URL
            ;;
    esac
fi

# Run Alembic migrations before starting the server.
# alembic.ini is at /app/alembic.ini (copied in the Dockerfile).
# env.py uses DATABASE_URL (via Settings) when MIGRATION_DATABASE_URL is unset.
echo "Running database migrations..."
alembic upgrade head
echo "Migrations complete."

# Hand off to the main server process.
exec uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8000}" --no-proxy-headers
