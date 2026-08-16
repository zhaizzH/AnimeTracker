#!/bin/sh
set -eu

# 演示数据写入入口（仅 tools profile 下由 docker compose 显式调用）。
# 守卫：非空业务库默认拒绝写入；只有 ALLOW_DEMO_SEED=true 才允许覆盖。
# 依赖：业务库已由 Flyway 建表；DEMO_USER_PASSWORD 提供明文密码，哈希运行时生成。

mysql_demo() {
  mysql -h"${MYSQL_HOST:-localhost}" -P"${MYSQL_PORT:-3306}" \
        -u"${MYSQL_USER:-root}" -p"${MYSQL_PASSWORD:?MYSQL_PASSWORD 未设置}" \
        "${MYSQL_DATABASE:-anime_tracker}" "$@"
}

if [ -z "${DEMO_USER_PASSWORD:-}" ]; then
  echo "错误: DEMO_USER_PASSWORD 未设置，无法生成演示用户密码哈希" >&2
  exit 1
fi

count="$(mysql_demo --batch --skip-column-names -e 'SELECT COUNT(*) FROM subject')"
if [ "$count" != "0" ] && [ "${ALLOW_DEMO_SEED:-}" != "true" ]; then
  echo "拒绝写入非空数据库: subject 表现有 $count 条数据；如需覆盖请设置 ALLOW_DEMO_SEED=true" >&2
  exit 1
fi

hash="$(python -c 'import os, bcrypt; print(bcrypt.hashpw(os.environ["DEMO_USER_PASSWORD"].encode(), bcrypt.gensalt(10)).decode())')"

sed "s|__DEMO_USER_PASSWORD_HASH__|$hash|g" /seed.sql | mysql_demo
echo "演示数据写入完成"
