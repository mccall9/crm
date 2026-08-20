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
APP_SOURCE="${APP_SOURCE:-/workspace/crm}"
FRAPPE_BRANCH="${FRAPPE_BRANCH:-version-16}"
PYTHON_BIN="${PYTHON_BIN:-/home/frappe/.pyenv/versions/${PYTHON_VERSION:-3.14.2}/bin/python3}"

if [ ! -x "${PYTHON_BIN}" ]; then
  printf 'Required Python interpreter not found: %s\n' "${PYTHON_BIN}" >&2
  exit 1
fi

wait_for_tcp() {
  local host="$1"
  local port="$2"
  local label="$3"
  local attempts=60

  printf 'Waiting for %s service\n' "$label"
  until (exec 3<>"/dev/tcp/${host}/${port}") 2>/dev/null; do
    attempts=$((attempts - 1))
    if [ "$attempts" -le 0 ]; then
      printf 'Timed out waiting for %s service\n' "$label" >&2
      return 1
    fi
    sleep 2
  done
  printf '%s service is reachable\n' "$label"
}

wait_for_tcp "$DB_HOST" "$DB_PORT" "MariaDB"
wait_for_tcp "$REDIS_HOST" "$REDIS_PORT" "Redis"

if [ -x "${BENCH_DIR}/env/bin/python" ]; then
  BENCH_PYTHON_VERSION="$(${BENCH_DIR}/env/bin/python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  if [ "${BENCH_PYTHON_VERSION}" != "3.14" ]; then
    rm -rf "${BENCH_DIR}"
  fi
fi

if [ ! -d "${BENCH_DIR}/apps/frappe" ]; then
  bench init \
    --python "${PYTHON_BIN}" \
    --skip-assets \
    --skip-redis-config-generation \
    --version "${FRAPPE_BRANCH}" \
    "${BENCH_DIR}"
fi

cd "${BENCH_DIR}"

# Frappe v16's special DocType JSON files omit `istable`, while meta.py
# accesses it directly during first-site installation. Keep the bootstrap
# compatible and idempotent without changing the CRM source tree.
FRAPPE_META="${BENCH_DIR}/apps/frappe/frappe/model/meta.py"
if [ -f "${FRAPPE_META}" ]; then
  sed -i 's/self\\.istable/getattr(self, "istable", False)/g' "${FRAPPE_META}"
fi

# Keep the global app registry aligned with the app names in this repository.
# This also removes stale entries such as the former `frappecrm` name.
printf '%s\n' frappe crm > "${BENCH_DIR}/sites/apps.txt"

bench set-mariadb-host "${DB_HOST}"
bench set-redis-cache-host "redis://${REDIS_HOST}:${REDIS_PORT}"
bench set-redis-queue-host "redis://${REDIS_HOST}:${REDIS_PORT}"
bench set-redis-socketio-host "redis://${REDIS_HOST}:${REDIS_PORT}"

rm -rf "${BENCH_DIR}/apps/crm"
cp -a "${APP_SOURCE}" "${BENCH_DIR}/apps/crm"

bench pip install --quiet -e "${BENCH_DIR}/apps/crm"

if [ ! -f "${BENCH_DIR}/sites/${SITE_NAME}/site_config.json" ]; then
  bench new-site "${SITE_NAME}" \
    --force \
    --mariadb-root-password "${DB_ROOT_PASSWORD}" \
    --admin-password "${ADMIN_PASSWORD}" \
    --db-host "${DB_HOST}" \
    --db-port "${DB_PORT}" \
    --no-mariadb-socket
fi

if ! bench --site "${SITE_NAME}" list-apps | awk '{print $1}' | grep -qx "crm"; then
  bench --site "${SITE_NAME}" install-app crm
fi

bench --site "${SITE_NAME}" set-config developer_mode 0
bench --site "${SITE_NAME}" set-config mute_emails 1
bench --site "${SITE_NAME}" migrate
bench --site "${SITE_NAME}" clear-cache

bench use "${SITE_NAME}"
exec bench serve --host 0.0.0.0 --port "${PORT}" --noreload
