#!/usr/bin/env bash
# =====================================================================
# 可恢复备份脚本
# MySQL 一致性转储(--single-transaction) + MinIO 对象镜像(mc mirror),
# 生成校验和,保留 7 份每日 + 4 份每周(周日或 --weekly 时归档一份)。
# 写入前验证解析后的绝对路径位于仓库之外。
#
# 用法:  deploy/scripts/backup.sh [--weekly]
# 前置:  生产 compose 栈已启动(需要 mysql 与 minio 服务)
# =====================================================================
set -euo pipefail

COMMON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
. "$COMMON_DIR/common.sh"
cd "$REPO_ROOT"

COMPOSE="docker compose -f compose.yml -f compose.prod.yml"
WEEKLY=0
[ "${1:-}" = "--weekly" ] && WEEKLY=1

# ---- 1. 只读校验 ----
command -v docker >/dev/null 2>&1 || { echo "ERROR: 未安装 docker" >&2; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "ERROR: 未安装 docker compose v2" >&2; exit 1; }
load_env || exit 1
BACKUP_PATH="$(validate_backup_path "${BACKUP_PATH:-}")" || exit 1

[ -n "$($COMPOSE ps -q mysql)" ] || { echo "ERROR: MySQL 服务未运行" >&2; exit 1; }
[ -n "$($COMPOSE ps -q minio)" ] || { echo "ERROR: MinIO 服务未运行" >&2; exit 1; }

TS="$(date +%Y%m%d-%H%M%S)"
DEST="$BACKUP_PATH/daily/$TS"
mkdir -p "$DEST/mysql" "$DEST/minio"
echo "备份目标: $DEST"

# ---- 2. MySQL 一致性转储(密码走容器内 MYSQL_PWD,避免出现在命令行) ----
echo "转储 MySQL 数据库 $MYSQL_DATABASE ..."
$COMPOSE exec -e MYSQL_DATABASE="$MYSQL_DATABASE" -T mysql sh -c \
    'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysqldump \
        --single-transaction --quick --no-tablespaces --routines --triggers \
        --set-gtid-purged=OFF --add-drop-database --databases "$MYSQL_DATABASE" -uroot' \
    | gzip -9 > "$DEST/mysql/dump.sql.gz"
( cd "$DEST/mysql" && sha256sum dump.sql.gz > dump.sql.gz.sha256 )

# ---- 3. MinIO 对象镜像(mc mirror,与 minio 容器共享网络命名空间) ----
echo "镜像 MinIO bucket $MINIO_BUCKET ..."
MC_CID="$($COMPOSE ps -q minio)"
docker run --rm --entrypoint mc \
    --network "container:$MC_CID" \
    -v "$DEST/minio:/backup" \
    -e "MC_HOST_local=http://${MINIO_ACCESS_KEY}:${MINIO_SECRET_KEY}@127.0.0.1:9000" \
    "$MINIO_MC_IMAGE" mirror --overwrite --remove "local/$MINIO_BUCKET" /backup
( cd "$DEST/minio" && find . -type f -print0 | sort -z | xargs -0 -r sha256sum > "$DEST/minio.files.sha256" )

# ---- 4. 清单 ----
{
    echo "{"
    echo "  \"timestamp\": \"$TS\","
    echo "  \"backup_path\": \"$DEST\","
    echo "  \"mysql_database\": \"$MYSQL_DATABASE\","
    echo "  \"minio_bucket\": \"$MINIO_BUCKET\""
    echo "}"
} > "$DEST/manifest.json"

# ---- 5. 保留策略: 每日 7 份;周日或 --weekly 时归档为每周一份(硬链接,省磁盘) ----
ls -1d "$BACKUP_PATH"/daily/*/ 2>/dev/null | sort -r | tail -n +8 | xargs -r rm -rf
if [ "$WEEKLY" = 1 ] || [ "$(date +%u)" = "7" ]; then
    mkdir -p "$BACKUP_PATH/weekly"
    cp -al "$DEST" "$BACKUP_PATH/weekly/$TS"
    ls -1d "$BACKUP_PATH"/weekly/*/ 2>/dev/null | sort -r | tail -n +5 | xargs -r rm -rf
fi

echo "备份完成: $DEST"
echo "MySQL 转储: $(du -h "$DEST/mysql/dump.sql.gz" | cut -f1)"
echo "MinIO 对象: $(find "$DEST/minio" -type f | wc -l) 个文件"
