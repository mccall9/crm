#!/usr/bin/env bash

set -euo pipefail

DB_HOST="${DB_HOST:-${MYSQLHOST:-}}"
DB_PORT="${DB_PORT:-${MYSQLPORT:-3306}}"
DB_ROOT_PASSWORD="${DB_ROOT_PASSWORD:-${MYSQL_ROOT_PASSWORD:-${MYSQLPASSWORD:-}}}"
REDIS_HOST="${REDIS_HOST:-${REDISHOST:-}}"
REDIS_PORT="${REDIS_PORT:-${REDISPORT:-6379}}"

: "${DB_HOST:?DB_HOST or MYSQLHOST is required}"
: "${DB_ROOT_PASSWORD:?DB_ROOT_PASSWORD or MYSQL_ROOT_PASSWORD is required}"
: "${REDIS_HOST:?REDIS_HOST or REDISHOST is required}"
: "${ADMIN_PASSWORD:?ADMIN_PASSWORD is required}"
: "${SITE_NAME:?SITE_NAME is required}"
: "${PORT:?PORT is required}"

BENCH_DIR="${BENCH_DIR:-/workspace/frappe-bench}"
APP_SOURCE="${APP_SOURCE:-/workspace}"
FRAPPE_BRANCH="${FRAPPE_BRANCH:-version-15}"

if [ ! -d "${BENCH_DIR}/apps/frappe" ]; then
  bench init \
    --skip-redis-config-generation \
    --version "${FRAPPE_BRANCH}" \
    "${BENCH_DIR}"
fi

cd "${BENCH_DIR}"

bench set-mariadb-host "${DB_HOST}"
bench set-redis-cache-host "redis://${REDIS_HOST}:${REDIS_PORT}"
bench set-redis-queue-host "redis://${REDIS_HOST}:${REDIS_PORT}"
bench set-redis-socketio-host "redis://${REDIS_HOST}:${REDIS_PORT}"

if [ ! -d "${BENCH_DIR}/apps/crm" ]; then
  bench get-app crm "${APP_SOURCE}"
fi

if [ ! -f "${BENCH_DIR}/sites/${SITE_NAME}/site_config.json" ]; then
  bench new-site "${SITE_NAME}" --force --mariadb-root-password "${DB_ROOT_PASSWORD}" --admin-password "${ADMIN_PASSWORD}" --db-host "${DB_HOST}" --db-port "${DB_PORT}" --no-mariadb-socket

  bench --site "${SITE_NAME}" install-app crm
  bench --site "${SITE_NAME}" set-config developer_mode 0
  bench --site "${SITE_NAME}" set-config mute_emails 1
  bench --site "${SITE_NAME}" clear-cache
fi

bench use "${SITE_NAME}"
exec bench serve --port "${PORT}" --host 0.0.0.0 --noreload
