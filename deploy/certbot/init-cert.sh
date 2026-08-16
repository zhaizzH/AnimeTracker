#!/bin/sh
set -eu

# Let's Encrypt 证书申请/续期(webroot 方式)。nginx 容器自行周期性 reload 共享证书卷。
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

[ -f "$live_dir/fullchain.pem" ]
