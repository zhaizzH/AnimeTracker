#!/usr/bin/env bash
# =====================================================================
# 受保护的恢复脚本
# 打印目标环境、备份时间、校验和与将被覆盖的数据,要求交互确认或 --yes。
# 在任何服务停止之前先校验产物存在且校验和匹配,拒绝缺失/损坏的备份。
#
# 用法:  deploy/scripts/restore.sh [--backup <目录>] [--yes]
#   --backup  指定备份目录(默认取 daily/ 下最新一份)
#   --yes     跳过交互确认(用于脚本/演练)
# =====================================================================
set -euo pipefail

COMMON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
. "$COMMON_DIR/common.sh"
cd "$REPO_ROOT"

COMPOSE="docker compose -f compose.yml -f compose.prod.yml"
BACKUP_SELECT=""
YES=0
while [ $# -gt 0 ]; do
    case "$1" in
        --backup) BACKUP_SELECT="${2:-}"; shift 2 ;;
        --yes) YES=1; shift ;;
        *) echo "ERROR: 未知参数: $1" >&2; exit 1 ;;
    esac
done

# ---- 1. 只读校验 ----
command -v docker >/dev/null 2>&1 || { echo "ERROR: 未安装 docker" >&2; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "ERROR: 未安装 docker compose v2" >&2; exit 1; }
load_env || exit 1
BACKUP_PATH="$(validate_backup_path "${BACKUP_PATH:-}")" || exit 1

[ -n "$($COMPOSE ps -q mysql)" ] || { echo "ERROR: MySQL 服务未运行" >&2; exit 1; }
[ -n "$($COMPOSE ps -q minio)" ] || { echo "ERROR: MinIO 服务未运行" >&2; exit 1; }

# ---- 2. 定位备份目录(默认最新一份 daily) ----
if [ -n "$BACKUP_SELECT" ]; then
    DEST="$(resolve_abs "$BACKUP_SELECT")"
else
    DEST="$(ls -1d "$BACKUP_PATH"/daily/*/ 2>/dev/null | sort -r | head -n1 | sed 's:/*$::')"
fi
[ -n "$DEST" ] && [ -d "$DEST" ] || { echo "ERROR: 备份目录不存在: ${DEST:-<无可用备份>}" >&2; exit 1; }

# ---- 3. 校验产物与校验和(在任何服务停止之前) ----
[ -f "$DEST/mysql/dump.sql.gz" ] || { echo "ERROR: 缺少 MySQL 转储 $DEST/mysql/dump.sql.gz" >&2; exit 1; }
[ -f "$DEST/mysql/dump.sql.gz.sha256" ] || { echo "ERROR: 缺少 MySQL 校验和文件" >&2; exit 1; }
gzip -t "$DEST/mysql/dump.sql.gz" || { echo "ERROR: MySQL 转储损坏(gzip 校验失败)" >&2; exit 1; }
( cd "$DEST/mysql" && sha256sum -c dump.sql.gz.sha256 ) >/dev/null 2>&1 \
    || { echo "ERROR: MySQL 转储校验和不符" >&2; exit 1; }

[ -d "$DEST/minio" ] || { echo "ERROR: 缺少 MinIO 镜像目录 $DEST/minio" >&2; exit 1; }
[ -f "$DEST/minio.files.sha256" ] || { echo "ERROR: 缺少 MinIO 校验和文件" >&2; exit 1; }
( cd "$DEST/minio" && sha256sum -c "$DEST/minio.files.sha256" ) >/dev/null 2>&1 \
    || { echo "ERROR: MinIO 镜像校验和不符" >&2; exit 1; }

echo "=========================================================="
echo "环境      : compose 项目 $(docker compose -f compose.yml -f compose.prod.yml config --project-name)"
echo "MySQL 库  : $MYSQL_DATABASE"
echo "MinIO 桶  : $MINIO_BUCKET"
echo "备份时间  : $(basename "$DEST")"
echo "备份目录  : $DEST"
echo "将覆盖数据:"
echo "  - MySQL 数据库 $MYSQL_DATABASE(现有数据将被替换)"
echo "  - MinIO 桶 $MINIO_BUCKET(对象将按备份镜像覆盖)"
echo "=========================================================="

# ---- 4. 确认 ----
if [ "$YES" != 1 ]; then
    read -r -p "输入 yes 确认恢复: " ans
    [ "$ans" = "yes" ] || { echo "已取消恢复"; exit 1; }
fi

# ---- 5. 停止业务写入方,防止恢复期间产生脏写 ----
echo "停止 business / agent ..."
$COMPOSE stop business agent

# ---- 6. 恢复 MySQL(转储含 CREATE DATABASE + USE,直接灌入) ----
echo "恢复 MySQL 数据库 $MYSQL_DATABASE ..."
gunzip -c "$DEST/mysql/dump.sql.gz" \
    | $COMPOSE exec -T mysql sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot'

# ---- 7. 恢复 MinIO 对象 ----
echo "恢复 MinIO 桶 $MINIO_BUCKET ..."
MC_CID="$($COMPOSE ps -q minio)"
docker run --rm --entrypoint mc \
    --network "container:$MC_CID" \
    -v "$DEST/minio:/backup" \
    -e "MC_HOST_local=http://${MINIO_ACCESS_KEY}:${MINIO_SECRET_KEY}@127.0.0.1:9000" \
    "$MINIO_MC_IMAGE" mirror --overwrite --remove /backup "local/$MINIO_BUCKET"

# ---- 8. 重启业务(up -d:不存在则创建,已停止则启动) ----
echo "启动 business / agent ..."
$COMPOSE up -d business agent

echo "恢复完成: $DEST"
