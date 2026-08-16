#!/bin/sh
set -eu

# nginx 首次启动引导:
# certbot 尚未签发真实证书时,生成 30 天自签占位证书,使 443 立即可用;
# certbot 通过 webroot 拿到真实证书后 SIGHUP reload,占位证书随即被替换。
# 仅首次引导需要;证书已存在(占位或真实)时直接启动 nginx。

live_dir="/etc/letsencrypt/live/${DOMAIN:?DOMAIN 未设置,请在 .env 中配置域名}"

if [ ! -f "$live_dir/fullchain.pem" ]; then
    mkdir -p "$live_dir"
    openssl req -x509 -nodes -newkey rsa:2048 -days 30 \
        -keyout "$live_dir/privkey.pem" \
        -out "$live_dir/fullchain.pem" \
        -subj "/CN=${DOMAIN}"
fi

exec nginx -g "daemon off;"
