#!/usr/bin/env bash
# =====================================================================
# demo-seeder 集成测试：空库写入 / 非空库拒绝 / ALLOW_DEMO_SEED=true 幂等覆盖
# 前置：docker 可用（一次性 MySQL 与 seeder 均在容器内运行，宿主机无需 mysql 客户端）
# 用法：deploy/tests/test-demo-seeder.sh
# =====================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SEEDER_DIR="$SCRIPT_DIR/../demo-seeder"
BASELINE_SQL="${BASELINE_SQL:-$SCRIPT_DIR/../../docs/database/db-schema.sql}"
IMAGE="${IMAGE:-animetracker-demo-seeder:test}"
DB_NAME="demo_seeder_$$"
ROOT_PW="seeder_test_pw"

command -v docker >/dev/null 2>&1 || { echo "FAIL: 需要 docker" >&2; exit 1; }
[ -f "$BASELINE_SQL" ] || { echo "FAIL: 未找到建表脚本 $BASELINE_SQL" >&2; exit 1; }

pass() { echo "PASS: $1"; }
fail() { echo "FAIL: $1" >&2; exit 1; }

echo "构建 seeder 镜像..."
docker build -q -t "$IMAGE" "$SEEDER_DIR" >/dev/null

echo "启动一次性 MySQL..."
MYSQL_CID="$(docker run -d --rm -e MYSQL_ROOT_PASSWORD="$ROOT_PW" -e MYSQL_DATABASE="$DB_NAME" mysql:8)"
trap 'docker rm -f "$MYSQL_CID" >/dev/null 2>&1 || true' EXIT

for _ in $(seq 1 60); do
  docker exec "$MYSQL_CID" mysqladmin ping -uroot -p"$ROOT_PW" --silent >/dev/null 2>&1 && break
  sleep 2
done
docker exec "$MYSQL_CID" mysqladmin ping -uroot -p"$ROOT_PW" --silent >/dev/null 2>&1 || fail "MySQL 未在超时时间内就绪"

echo "应用项目级 db-schema.sql 建表..."
docker exec -i "$MYSQL_CID" mysql -uroot -p"$ROOT_PW" "$DB_NAME" < "$BASELINE_SQL"

run_seeder() {
  docker run --rm --network "container:$MYSQL_CID" \
    -e MYSQL_HOST=127.0.0.1 -e MYSQL_PORT=3306 \
    -e MYSQL_USER=root -e MYSQL_PASSWORD="$ROOT_PW" \
    -e MYSQL_DATABASE="$DB_NAME" \
    -e DEMO_USER_PASSWORD="${1:?}" \
    -e ALLOW_DEMO_SEED="${2:-}" \
    "$IMAGE"
}

echo "场景1: 空库应成功写入..."
run_seeder "demo-pass-1" "" || fail "空库写入失败"
count="$(docker exec "$MYSQL_CID" mysql -uroot -p"$ROOT_PW" -N -e "SELECT COUNT(*) FROM \`$DB_NAME\`.subject")"
[ "$count" = "5" ] || fail "期望 5 条番剧，实际 $count"
pass "空库写入成功（subject=$count）"

echo "场景2: 非空库未授权应拒绝..."
if run_seeder "demo-pass-2" "" >/dev/null 2>&1; then
  fail "非空库未被拒绝"
fi
pass "非空库正确拒绝"

echo "场景3: ALLOW_DEMO_SEED=true 应幂等覆盖成功..."
run_seeder "demo-pass-3" "true" || fail "显式覆盖失败"
pass "显式覆盖成功"

echo "全部场景通过"
