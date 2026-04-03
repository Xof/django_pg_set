#!/bin/bash
set -e

DJANGO_VERSION="${DJANGO_VERSION:-5.2}"
BACKEND="${BACKEND:-psycopg3}"

echo "=== django-pg-set test runner ==="
echo "Django: ${DJANGO_VERSION}"
echo "Backend: ${BACKEND}"
echo "================================="

# Install the requested Django version
uv pip install "django==${DJANGO_VERSION}.*"

# Install the requested backend
if [ "$BACKEND" = "psycopg2" ]; then
    uv pip install psycopg2-binary
    # Remove psycopg3 if installed
    uv pip uninstall psycopg psycopg-binary 2>/dev/null || true
elif [ "$BACKEND" = "psycopg3" ]; then
    uv pip install "psycopg[binary]"
    # Remove psycopg2 if installed
    uv pip uninstall psycopg2-binary 2>/dev/null || true
else
    echo "ERROR: BACKEND must be 'psycopg2' or 'psycopg3', got '${BACKEND}'"
    exit 1
fi

echo ""
echo "Installed versions:"
uv pip show django | grep Version
if [ "$BACKEND" = "psycopg2" ]; then
    uv pip show psycopg2-binary | grep Version
else
    uv pip show psycopg | grep Version
fi
echo ""

# Execute the command passed to the container (default: uv run pytest -v)
exec "$@"
