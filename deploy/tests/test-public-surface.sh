#!/bin/sh
set -eu

# 验证生产公网暴露面(需已启动: docker compose -f compose.yml -f compose.prod.yml up -d)。
#  1) 仅 nginx 把 80/443 映射到宿主机
#  2) 静态面: 客户端 / 与管理端 /admin/ 正常返回
#  3) /api 通过 nginx 可达
#  4) 内部端点(Swagger/Actuator/MinIO)对公网不可达
#  5) SSE 代理关闭缓冲并设长读超时(配置级)
# 用法: ./deploy/tests/test-public-surface.sh [BASE_URL]

BASE_URL="${1:-https://${DOMAIN:-localhost}}"
COMPOSE="docker compose -f compose.yml -f compose.prod.yml"

fail=0
warn=0

code_of() { # code_of <url> -> HTTP 状态码(000 表示连接失败)
    curl -s -k -o /dev/null -w '%{http_code}' --max-time 15 "$1" 2>/dev/null || echo "000"
}

echo "== 1) 仅 nginx 发布 80/443 =="
published="$($COMPOSE ps -a --format '{{.Ports}}' \
    | tr ',' '\n' \
    | sed 's/^[[:space:]]*//' \
    | cut -d'>' -f1 \
    | awk -F: '{print $NF}' \
    | grep -E '^[0-9]+$' \
    | sort -un \
    | tr '\n' ' ' | sed 's/ $//')"
echo "  已发布宿主机端口: [${published}]"
if [ -z "$published" ]; then
    echo "FAIL: 未发现任何发布端口"; fail=$((fail+1))
else
    ok=1
    for p in $published; do
        case "$p" in
            80|443) ;;
            *) ok=0; echo "  非法发布端口: $p";;
        esac
    done
    [ "$ok" = 1 ] && echo "PASS: 仅 80/443 被映射" || { echo "FAIL: 存在非 80/443 映射"; fail=$((fail+1)); }
fi

echo "== 2) 静态面: 客户端 / 与管理端 /admin/ =="
for entry in "/:客户端" "/admin/:管理端"; do
    path="${entry%%:*}"; name="${entry##*:}"
    code="$(code_of "$BASE_URL$path")"
    if [ "$code" = "200" ]; then
        echo "PASS: $name $path -> 200"
    else
        echo "FAIL: $name $path -> $code"; fail=$((fail+1))
    fi
done

echo "== 3) /api 经 nginx 可达 =="
code="$(code_of "$BASE_URL/api/client/agent/health")"
case "$code" in
    000) echo "FAIL: /api 连接失败"; fail=$((fail+1));;
    200) echo "PASS: /api/client/agent/health -> 200";;
    *)   echo "WARN: /api 可达但返回 $code(受鉴权保护)"; warn=$((warn+1));;
esac

echo "== 4) 内部端点公网不可达 =="
for path in /actuator /actuator/health /actuator/health/liveness \
            /minio /minio/login /doc.html /swagger-ui/index.html /v3/api-docs; do
    code="$(code_of "$BASE_URL$path")"
    if [ "$code" = "000" ]; then
        echo "FAIL: $path 连接失败"; fail=$((fail+1))
    elif [ "$code" = "404" ] || [ "$code" = "403" ]; then
        echo "PASS: $path -> $code"
    else
        echo "FAIL: $path -> $code,内部端点不应对外可达"; fail=$((fail+1))
    fi
done

echo "== 5) SSE 代理不缓冲(配置级) =="
sse_conf="$($COMPOSE exec -T nginx sh -c 'nginx -T 2>/dev/null' 2>/dev/null || true)"
if printf '%s' "$sse_conf" | grep -q 'proxy_buffering[[:space:]]*off' \
   && printf '%s' "$sse_conf" | grep -q 'proxy_read_timeout[[:space:]]*600s'; then
    echo "PASS: 检测到 proxy_buffering off 与 proxy_read_timeout 600s"
else
    echo "FAIL: 未检测到 SSE 不缓冲配置"; fail=$((fail+1))
fi

echo
echo "结果: $((fail)) FAIL, $((warn)) WARN"
[ "$fail" = 0 ] || exit 1
