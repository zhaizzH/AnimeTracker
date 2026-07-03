#!/bin/bash
# ===================================================================
# AnimeTracker — 生产环境启动脚本
# 启动 Spring Boot API、AI Agent、前端开发服务器
# ===================================================================
set -euo pipefail

echo "=== AnimeTracker 启动脚本 ==="

# --- 加载环境变量 ---
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# --- 1. 启动 Spring Boot API ---
echo ""
echo ">>> [1/3] 启动 Spring Boot API (端口 8080)..."
cd "$PROJECT_DIR/backend/api"
JAVA_JAR=$(ls target/animetracker-api-*.jar 2>/dev/null | head -1)
if [ -z "$JAVA_JAR" ]; then
    echo "  ⚠ JAR 未找到，请先运行 build.sh"
else
    java -jar "$JAVA_JAR" \
        --spring.profiles.active=prod &
    echo "  ✓ API 已启动 (PID: $!)"
fi

# --- 2. 启动 AI Agent ---
echo ""
echo ">>> [2/3] 启动 AI Agent (端口 8090)..."
cd "$PROJECT_DIR/backend/ai"
uvicorn main:app --host 0.0.0.0 --port 8090 --reload &
echo "  ✓ AI Agent 已启动 (PID: $!)"

# --- 3. 启动前端开发服务器 ---
echo ""
echo ">>> [3/3] 启动前端开发服务器 (端口 5173)..."
cd "$PROJECT_DIR/frontend"
npm run dev &
echo "  ✓ 前端已启动 (PID: $!)"

echo ""
echo "=== 所有服务已启动 ==="
echo "Frontend:  http://localhost:5173"
echo "API:       http://localhost:8080"
echo "AI Agent:  http://localhost:8090"
echo "API Docs:  http://localhost:8080/doc.html"
