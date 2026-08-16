#!/usr/bin/env bash
# =====================================================================
# 生产部署脚本(安全优先)
# 先校验 Docker / Compose / .env / 备份路径 / 必需密钥 / LLM Key,
# 全部通过后才执行 git pull --ff-only + compose pull + up -d + ps。
# 不包含任何破坏性步骤。
#
# 用法:  deploy/scripts/deploy.sh
# 前置:  在仓库根目录,已配置 .env(可参考 .env.example)
# =====================================================================
set -euo pipefail

COMMON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
. "$COMMON_DIR/common.sh"
cd "$REPO_ROOT"

COMPOSE="docker compose -f compose.yml -f compose.prod.yml"

# ---- 1. 只读校验,任何一项不满足都不做任何变更 ----
command -v docker >/dev/null 2>&1 || { echo "ERROR: 未安装 docker" >&2; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "ERROR: 未安装 docker compose v2" >&2; exit 1; }
[ -f .env ] || { echo "ERROR: 缺少 .env,请复制 .env.example 并填写" >&2; exit 1; }
load_env || exit 1

validate_backup_path "${BACKUP_PATH:-}" >/dev/null || exit 1

# compose config --quiet 会校验 compose.*.yml 中所有 ${VAR:?} 必需变量
echo "校验 compose 配置与必需密钥..."
$COMPOSE config --quiet || { echo "ERROR: compose 配置校验失败,请检查 .env 中的必需密钥" >&2; exit 1; }

# 至少配置一个 LLM Key(DeepSeek 优先,DashScope 兜底)
if [ -z "${DEEPSEEK_API_KEY:-}" ] && [ -z "${DASHSCOPE_API_KEY:-}" ]; then
    echo "ERROR: 至少需要配置一个 LLM Key(DEEPSEEK_API_KEY 或 DASHSCOPE_API_KEY)" >&2
    exit 1
fi

echo "== 校验通过,开始发布 =="

# ---- 2. 发布(仅向前快进,保留本地意外改动不被覆盖) ----
git pull --ff-only
$COMPOSE pull
$COMPOSE up -d

# ---- 3. 打印健康状态 ----
$COMPOSE ps
