#!/usr/bin/env bash
# =====================================================================
# deploy/backup/restore 脚本测试
#   Phase 1: 不安全/过宽路径拒绝(只需 bash + coreutils,可离线运行)
#   Phase 2: 损坏备份拒绝 + 确认恢复重建一次性 MySQL/MinIO 数据(需 docker)
# 用法:  deploy/tests/test-scripts.sh
# 前置:  Phase 2 需要 compose 栈已启动(至少 mysql 与 minio 服务)
# =====================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPOSE="docker compose -f compose.yml -f compose.prod.yml"

pass=0
fail_count=0
pass() { echo "PASS: $1"; pass=$((pass + 1)); }
fail() { echo "FAIL: $1" >&2; fail_count=$((fail_count + 1)); }

# 在子 shell 中加载 common.sh 并校验路径,避免污染当前环境
# rejected 在路径被拒绝时返回 0(true),否则返回 1(false)
rejected() { ! ( source "$REPO_ROOT/deploy/scripts/common.sh" >/dev/null 2>&1
                 validate_backup_path "$1" >/dev/null 2>&1 ); }
accepted() { ( source "$REPO_ROOT/deploy/scripts/common.sh" >/dev/null 2>&1
               validate_backup_path "$1" >/dev/null 2>&1 ); }

echo "== Phase 1: 不安全/过宽路径拒绝 =="
rejected "" && pass "空路径被拒绝" || fail "空路径未被拒绝"
rejected "/" && pass "根路径 / 被拒绝" || fail "根路径未被拒绝"
rejected "/backup" && pass "根级目录被拒绝" || fail "根级目录未被拒绝"
rejected "/home" && pass "/home 被拒绝" || fail "/home 未被拒绝"
rejected "/home/me" && pass "家目录被拒绝" || fail "家目录未被拒绝"
rejected "/root" && pass "/root 被拒绝" || fail "/root 未被拒绝"
rejected "/root/backups" && pass "/root 子目录被拒绝" || fail "/root 子目录未被拒绝"
rejected "/Users/me" && pass "/Users/me 被拒绝" || fail "/Users/me 未被拒绝"
rejected "$REPO_ROOT" && pass "仓库根被拒绝" || fail "仓库根未被拒绝"
rejected "$REPO_ROOT/deploy" && pass "仓库内路径被拒绝" || fail "仓库内路径未被拒绝"

WORK="$(mktemp -d)"
accepted "$WORK/snapshot" && pass "深层临时目录被接受" || fail "深层临时目录未被接受"
accepted "/srv/animetracker-backup-test" && pass "/srv 子目录被接受" || fail "/srv 子目录未被接受"
accepted "/home/me/backups" && pass "家目录下的明确子目录被接受" || fail "家目录子目录未被接受"
rm -rf "$WORK"

echo "== Phase 2: 备份/恢复集成(需 docker compose 栈运行) =="
if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
    echo "SKIP: 需要 docker compose v2"
    echo "结果: $pass PASS, $fail_count FAIL, Phase 2 跳过"
    [ "$fail_count" = 0 ]
    exit
fi
if [ -z "$($COMPOSE ps -q mysql)" ] || [ -z "$($COMPOSE ps -q minio)" ]; then
    echo "SKIP: compose 栈未运行(需要 mysql 与 minio 服务)"
    echo "结果: $pass PASS, $fail_count FAIL, Phase 2 跳过"
    [ "$fail_count" = 0 ]
    exit
fi

# 读取真实凭据,构造一次性数据库/桶与临时 env 文件
set -a
# shellcheck disable=SC1090
. "$REPO_ROOT/.env"
set +a
MINIO_MC_IMAGE="${MINIO_MC_IMAGE:-minio/mc:RELEASE.2025-08-13T08-35-41Z}"
MC_CID="$($COMPOSE ps -q minio)"
ROOT_PW="${MYSQL_ROOT_PASSWORD:-}"
[ -n "$MC_CID" ] || { fail "无法定位 MinIO 容器"; exit 1; }

DISPOSABLE_DB="anime_tracker_restore_$$"
DISPOSABLE_BUCKET="restore-test-$$"
BACKUP_ROOT="$WORK/backup"
ENV_FILE="$WORK/test.env"
cat > "$ENV_FILE" <<EOF
MYSQL_DATABASE=$DISPOSABLE_DB
MYSQL_ROOT_PASSWORD=$ROOT_PW
MINIO_BUCKET=$DISPOSABLE_BUCKET
MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
MINIO_SECRET_KEY=${MINIO_SECRET_KEY}
BACKUP_PATH=$BACKUP_ROOT
EOF

mc_cmd() {
    docker run --rm --entrypoint mc --network "container:$MC_CID" \
        -e "MC_HOST_local=http://${MINIO_ACCESS_KEY}:${MINIO_SECRET_KEY}@127.0.0.1:9000" \
        "$MINIO_MC_IMAGE" "$@"
}
mysql_cmd() { $COMPOSE exec -e MYSQL_PWD="$ROOT_PW" -T mysql mysql -uroot "$@"; }

cleanup() {
    mc_cmd rm --recursive --force "local/$DISPOSABLE_BUCKET" >/dev/null 2>&1 || true
    mysql_cmd -e "DROP DATABASE IF EXISTS \`$DISPOSABLE_DB\`" >/dev/null 2>&1 || true
    rm -rf "$WORK"
}
trap cleanup EXIT

echo "准备一次性数据..."
mysql_cmd -e "CREATE DATABASE IF NOT EXISTS \`$DISPOSABLE_DB\` CHARACTER SET utf8mb4"
mysql_cmd "$DISPOSABLE_DB" -e "CREATE TABLE restore_marker (id INT PRIMARY KEY, note VARCHAR(100))"
mysql_cmd "$DISPOSABLE_DB" -e "INSERT INTO restore_marker VALUES (1, 'marker-$$')"
mc_cmd mb -p "local/$DISPOSABLE_BUCKET" >/dev/null
echo "object-$$" > "$WORK/marker.txt"
mc_cmd cp "$WORK/marker.txt" "local/$DISPOSABLE_BUCKET/marker.txt" >/dev/null

echo "执行备份..."
ANIMETRACKER_ENV_FILE="$ENV_FILE" "$REPO_ROOT/deploy/scripts/backup.sh" >/dev/null
DEST="$(ls -1d "$BACKUP_ROOT"/daily/*/ 2>/dev/null | sort -r | head -n1 | sed 's:/*$::')"
[ -n "$DEST" ] || fail "未生成备份目录"

echo "损坏转储应被恢复脚本拒绝..."
echo "corrupt" >> "$DEST/mysql/dump.sql.gz"
if ANIMETRACKER_ENV_FILE="$ENV_FILE" "$REPO_ROOT/deploy/scripts/restore.sh" --backup "$DEST" --yes >/dev/null 2>&1; then
    fail "损坏备份未被拒绝"
else
    pass "损坏备份被拒绝"
fi

echo "重新备份用于恢复..."
ANIMETRACKER_ENV_FILE="$ENV_FILE" "$REPO_ROOT/deploy/scripts/backup.sh" >/dev/null
DEST2="$(ls -1d "$BACKUP_ROOT"/daily/*/ 2>/dev/null | sort -r | head -n1 | sed 's:/*$::')"

echo "清空一次性数据模拟丢失..."
mysql_cmd -e "DROP DATABASE \`$DISPOSABLE_DB\`"
mc_cmd rm --recursive --force "local/$DISPOSABLE_BUCKET" >/dev/null

echo "确认恢复..."
ANIMETRACKER_ENV_FILE="$ENV_FILE" "$REPO_ROOT/deploy/scripts/restore.sh" --backup "$DEST2" --yes >/dev/null
row="$(mysql_cmd -N "$DISPOSABLE_DB" -e "SELECT COUNT(*) FROM restore_marker WHERE note='marker-$$'")"
[ "$row" = "1" ] && pass "MySQL 数据恢复成功" || fail "MySQL 数据未恢复(row=$row)"
mc_cmd stat "local/$DISPOSABLE_BUCKET/marker.txt" >/dev/null 2>&1 \
    && pass "MinIO 对象恢复成功" || fail "MinIO 对象未恢复"

echo
echo "结果: $pass PASS, $fail_count FAIL"
[ "$fail_count" = 0 ]
