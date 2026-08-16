# ===================================================================
# AnimeTracker Agent — Python FastAPI
# 运行时: python 3.12 slim, 非 root
# 说明: resources/ 目录(托管提示词)必须保留,见 app/utils/prompt_utils.py
# ===================================================================
FROM python:3.12-slim

# tzdata 保证日志时间正确;libpq 兼容层无需要求最小镜像
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r app && useradd -r -g app -d /app app

WORKDIR /app

# 先装依赖,利用 pip 层缓存
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 业务代码(含 resources/ 提示词)
COPY . .

USER app
EXPOSE 8090

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8090/api/client/agent/health', timeout=3).close()"]

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8090"]
