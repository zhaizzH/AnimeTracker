#!/usr/bin/env bash
# =====================================================================
# 部署/备份/恢复脚本公共函数与路径校验
# 被 deploy/scripts/*.sh 以 source 方式加载,自身不直接执行。
# =====================================================================

# 仓库根目录 = 本文件所在目录的上一级(scripts/.. 为 deploy,再上级为仓库根)
COMMON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$COMMON_DIR/../.." && pwd)"

fail() {
    echo "ERROR: $*" >&2
    return 1
}

resolve_abs() {
    if command -v realpath >/dev/null 2>&1; then
        realpath -m "$1"
    elif command -v python3 >/dev/null 2>&1; then
        python3 -c "import os,sys; print(os.path.abspath(sys.argv[1]))" "$1"
    else
        echo "$1"
    fi
}

# 加载环境变量。可用 ANIMETRACKER_ENV_FILE 覆盖(测试注入用),默认仓库根 .env
load_env() {
    local env_file="${ANIMETRACKER_ENV_FILE:-$REPO_ROOT/.env}"
    [ -f "$env_file" ] || { echo "ERROR: 未找到环境文件 $env_file" >&2; return 1; }
    set -a
    # shellcheck disable=SC1090
    . "$env_file"
    set +a
}

# 校验备份目标绝对路径安全:
#   - 非空、解析后为绝对路径
#   - 不在仓库根内,也不是仓库根本身
#   - 不是危险/过宽路径: 根目录、家目录自身、根级目录(/ 的子目录)
# 通过返回 0,否则返回 1 并输出原因。
validate_backup_path() {
    local path="${1:-}" target parent repo
    [ -n "$path" ] || { echo "ERROR: 未设置备份路径 BACKUP_PATH" >&2; return 1; }
    target="$(resolve_abs "$path")"
    case "$target" in
        /*) ;;
        *) echo "ERROR: 备份路径必须为绝对路径: $path" >&2; return 1 ;;
    esac
    repo="$(resolve_abs "$REPO_ROOT")"
    case "$target" in
        "$repo"|"$repo"/*) echo "ERROR: 备份路径不得位于仓库内: $target" >&2; return 1 ;;
    esac
    parent="$(dirname "$target")"
    case "$parent" in
        /|/home|/Users|/root)
            echo "ERROR: 备份路径过宽,请使用明确的子目录(如 /srv/backups/animetracker): $target" >&2
            return 1 ;;
    esac
    echo "$target"
}
