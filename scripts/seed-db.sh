#!/bin/bash
# ===================================================================
# AnimeTracker — 数据库初始化脚本
# 创建数据库并执行 init.sql，插入种子数据
# ===================================================================
set -euo pipefail

echo "=== AnimeTracker 数据库初始化 ==="

# 从环境变量或默认值读取
MYSQL_HOST="${MYSQL_HOST:-localhost}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_USER="${MYSQL_USER:-root}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-root}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SQL_FILE="$SCRIPT_DIR/../backend/data/schema/init.sql"

if [ ! -f "$SQL_FILE" ]; then
    echo "  ✗ 找不到 SQL 文件: $SQL_FILE"
    exit 1
fi

echo ">>> 连接数据库: $MYSQL_HOST:$MYSQL_PORT"
echo ">>> 执行: $SQL_FILE"

mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" \
      -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" \
      < "$SQL_FILE"

echo ""
echo "=== 数据库初始化完成 ==="
