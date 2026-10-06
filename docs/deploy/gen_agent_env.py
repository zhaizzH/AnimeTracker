"""在服务器上生成 agent 生产配置 /opt/animetracker/agent.env。

用法（在服务器执行，密钥经环境变量传入，不落盘、不入库）：

    JWT_SECRET=$(openssl rand -base64 48) \
    DEEPSEEK_API_KEY=... DASHSCOPE_API_KEY=... BANGUMI_ACCESS_TOKEN=... \
    MYSQL_PASSWORD=... REDIS_PASSWORD=... MINIO_SECRET_KEY=... \
    python3 gen_agent_env.py

以 .env.example 为模板逐行覆写需要改的键，保留其余默认值。
"""

import os
import pathlib
import re
import sys

SRC = pathlib.Path("/opt/animetracker/src/AnimeTracker/backend/agent/.env.example")
DST = pathlib.Path("/opt/animetracker/agent.env")

PUBLIC_HOST = os.environ.get("PUBLIC_HOST", "104.208.115.195")

# 密钥一律从环境变量取，禁止写死在源码里（否则 GitHub push protection 会拦，
# 且密钥进了 git 历史就等同泄露）。
REQUIRED = (
    "JWT_SECRET",
    "DEEPSEEK_API_KEY",
    "DASHSCOPE_API_KEY",
    "BANGUMI_ACCESS_TOKEN",
    "MYSQL_PASSWORD",
    "REDIS_PASSWORD",
    "MINIO_SECRET_KEY",
)
missing = [name for name in REQUIRED if not os.environ.get(name)]
if missing:
    sys.exit(f"缺少必填环境变量: {', '.join(missing)}")

override = {
    "LLM_PROVIDER": os.environ.get("LLM_PROVIDER", "deepseek"),
    "DEEPSEEK_API_KEY": os.environ["DEEPSEEK_API_KEY"],
    "DASHSCOPE_API_KEY": os.environ["DASHSCOPE_API_KEY"],
    "BANGUMI_ACCESS_TOKEN": os.environ["BANGUMI_ACCESS_TOKEN"],
    "AGENT_HOST": "127.0.0.1",
    "BACKEND_BASE_URL": "http://127.0.0.1:8080",
    "BUSINESS_BASE_URL": "http://127.0.0.1:8080",
    "JWT_SECRET": os.environ["JWT_SECRET"],
    "REDIS_URL": f"redis://:{os.environ['REDIS_PASSWORD']}@127.0.0.1:6379/1",
    "CORS_ORIGINS": f'["http://{PUBLIC_HOST}","http://{PUBLIC_HOST}:8081"]',
    "DB_HOST": "127.0.0.1",
    "DB_PASSWORD": os.environ["MYSQL_PASSWORD"],
    "MINIO_ENDPOINT": "127.0.0.1:9000",
    "MINIO_ACCESS_KEY": os.environ.get("MINIO_ACCESS_KEY", "root"),
    "MINIO_SECRET_KEY": os.environ["MINIO_SECRET_KEY"],
    "RAG_ENABLED": os.environ.get("RAG_ENABLED", "true"),
    "ANIMETRACKER_LOG": "",
}

lines, seen = [], set()
for line in SRC.read_text(encoding="utf-8").splitlines():
    match = re.match(r"^([A-Z_][A-Z0-9_]*)=", line)
    if match:
        key = match.group(1)
        seen.add(key)
        if key in override:
            lines.append(f"{key}={override[key]}")
            continue
    lines.append(line)

# 模板里没有、但生产必须补的键
for key, value in override.items():
    if key not in seen:
        lines.append(f"{key}={value}")

DST.write_text("\n".join(lines) + "\n", encoding="utf-8")
DST.chmod(0o600)
print(f"已写入 {DST}（{len(lines)} 行，权限 600）")
