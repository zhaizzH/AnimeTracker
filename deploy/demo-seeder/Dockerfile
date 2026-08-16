FROM python:3.12-slim

# 守卫查询与数据导入需要 mysql 客户端；bcrypt 用于容器启动时生成演示密码哈希
RUN apt-get update \
    && apt-get install -y --no-install-recommends default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir bcrypt

COPY seed.sql /seed.sql
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
