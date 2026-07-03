#!/bin/bash
# ===================================================================
# AnimeTracker — 构建脚本
# 构建 Spring Boot API、安装前端依赖、验证 AI Agent 环境
# ===================================================================
set -euo pipefail

echo "=== AnimeTracker 构建脚本 ==="

# --- 1. 构建 Java API ---
echo ""
echo ">>> [1/3] 构建 Spring Boot API..."
cd "$(dirname "$0")/../backend/api"
mvn clean package -DskipTests
echo "  ✓ API 构建完成"

# --- 2. 安装前端依赖 ---
echo ""
echo ">>> [2/3] 安装前端依赖..."
cd "$(dirname "$0")/../frontend"
npm install
echo "  ✓ 前端依赖安装完成"

# --- 3. 验证 AI Agent 环境 ---
echo ""
echo ">>> [3/3] 验证 AI Agent 环境..."
cd "$(dirname "$0")/../backend/ai"
python -c "import fastapi; print('  ✓ FastAPI:', fastapi.__version__)" 2>/dev/null \
    || echo "  ⚠ FastAPI 未安装，请执行: pip install -r requirements.txt"

echo ""
echo "=== 构建完成 ==="
