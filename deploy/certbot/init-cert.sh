#!/bin/sh
set -eu

# Let's Encrypt 证书申请/续期(webroot 方式),成功后向 nginx 平滑 reload。
# 由 compose 以循环方式调用(每次间隔 12h);DOMAIN/CERT_EMAIL 由 compose 注入。
# 首次启动依赖: nginx 容器已由 bootstrap.sh 生成占位证书并监听 80 提供 webroot。

: "${DOMAIN:?DOMAIN 未设置,请在 .env 中配置域名}"
: "${CERT_EMAIL:?CERT_EMAIL 未设置,请在 .env 中配置邮箱}"

webroot="/var/www/certbot"
live_dir="/etc/letsencrypt/live/$DOMAIN"

certbot certonly \
    --webroot -w "$webroot" \
    -d "$DOMAIN" \
    --email "$CERT_EMAIL" \
    --agree-tos \
    --no-eff-email \
    --keep-until-expiring \
    --non-interactive \
    --expand

# 证书就绪后向 nginx 容器发送 SIGHUP(经只读 docker socket),让 nginx 立即
# 换用新证书。socket 不可用时静默跳过——nginx 下次重启/轮询仍会生效。
if [ -f "$live_dir/fullchain.pem" ]; then
    python3 - <<'PY' || true
import json, os, socket
from urllib.parse import quote

sock = "/var/run/docker.sock"
if not os.path.exists(sock):
    raise SystemExit(0)

def call(method, path):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(sock)
    s.sendall(f"{method} {path} HTTP/1.1\r\nHost: docker\r\nConnection: close\r\n\r\n".encode())
    buf = b""
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        buf += chunk
    s.close()
    return buf

def body(resp):
    _, _, payload = resp.partition(b"\r\n\r\n")
    if not payload:
        return []
    try:
        return json.loads(payload.decode("utf-8", "replace"))
    except ValueError:
        return []

filters = quote(json.dumps({"name": ["nginx"]}, separators=(",", ":")))
for c in body(call("GET", f"/containers/json?filters={filters}")):
    call("POST", f"/containers/{c['Id']}/kill?signal=SIGHUP")
PY
fi
