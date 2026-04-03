#!/bin/bash
set -e

# django-pg-set full test matrix runner
# Runs all 30 combinations via Docker Compose

PG_VERSIONS="14 15 16 17 18"
DJANGO_VERSIONS="4.2 5.2 6.0"
BACKENDS="psycopg2 psycopg3"

PASS=0
FAIL=0
RESULTS=""

total=0
for _ in $PG_VERSIONS; do for _ in $DJANGO_VERSIONS; do for _ in $BACKENDS; do total=$((total + 1)); done; done; done

current=0

for pg in $PG_VERSIONS; do
    for django in $DJANGO_VERSIONS; do
        for backend in $BACKENDS; do
            current=$((current + 1))
            combo="PG ${pg} / Django ${django} / ${backend}"
            echo ""
            echo "[$current/$total] Testing: $combo"
            echo "==========================================="

            if PG_VERSION="$pg" DJANGO_VERSION="$django" BACKEND="$backend" \
                docker compose up --build --abort-on-container-exit --quiet-pull 2>&1; then
                RESULTS="${RESULTS}\n  PASS  ${combo}"
                PASS=$((PASS + 1))
            else
                RESULTS="${RESULTS}\n  FAIL  ${combo}"
                FAIL=$((FAIL + 1))
            fi

            docker compose down -v --remove-orphans 2>/dev/null || true
        done
    done
done

echo ""
echo ""
echo "==========================================="
echo "  TEST MATRIX RESULTS"
echo "==========================================="
echo -e "$RESULTS"
echo ""
echo "==========================================="
echo "  PASS: $PASS  FAIL: $FAIL  TOTAL: $total"
echo "==========================================="

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
