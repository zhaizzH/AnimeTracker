#!/bin/bash
# ===================================================================
# AnimeTracker 一键更新脚本
# 用法: sudo ./update.sh            （以 root 运行）
# 功能: git pull → 后端构建重启 → Agent 重启 → 前端构建 → 验证
# ===================================================================
set -e
set -o pipefail

if [ "$(id -u)" != "0" ]; then
    echo "❌ 请用 root 运行: sudo ./update.sh"
    exit 1
fi

PROJECT_DIR="/home/zhaizz/projects/AnimeTracker"
LOG_FILE="/tmp/animetracker-update.log"
START_TIME=$(date '+%Y-%m-%d %H:%M:%S')

echo "==========================================" | tee "$LOG_FILE"
echo " AnimeTracker 更新开始: $START_TIME" | tee -a "$LOG_FILE"
echo "==========================================" | tee -a "$LOG_FILE"

cd "$PROJECT_DIR"

# ---------- 1. 拉取代码 ----------
echo "" | tee -a "$LOG_FILE"
echo "▶ [1/6] 拉取最新代码..." | tee -a "$LOG_FILE"
sudo -u zhaizz git checkout -- frontend/client/package-lock.json frontend/admin/package-lock.json 2>/dev/null || true
for i in 1 2 3; do
    if sudo -u zhaizz git pull origin main 2>&1 | tee -a "$LOG_FILE"; then
        break
    fi
    echo "   (网络重试 $i/3)..." | tee -a "$LOG_FILE"
    sleep 5
done

# ---------- 2. 后端构建 ----------
echo "" | tee -a "$LOG_FILE"
echo "▶ [2/6] 构建后端 (Maven)..." | tee -a "$LOG_FILE"
cd backend/business
sudo -u zhaizz mvn clean install -DskipTests -q 2>&1 | tail -20 | tee -a "$LOG_FILE"
cd "$PROJECT_DIR"

# ---------- 3. 后端重启 ----------
echo "" | tee -a "$LOG_FILE"
echo "▶ [3/6] 重启业务后端..." | tee -a "$LOG_FILE"
systemctl restart animetracker-business
echo "   ✓ animetracker-business 已重启" | tee -a "$LOG_FILE"

# ---------- 4. Agent 依赖 + 重启 ----------
echo "" | tee -a "$LOG_FILE"
echo "▶ [4/6] 更新 Agent 依赖并重启..." | tee -a "$LOG_FILE"
cd backend/agent
sudo -u zhaizz ./venv/bin/pip install -q -r requirements.txt 2>&1 | tail -5 | tee -a "$LOG_FILE" || echo "   (依赖无变化，跳过)" | tee -a "$LOG_FILE"
systemctl restart animetracker-agent
echo "   ✓ animetracker-agent 已重启" | tee -a "$LOG_FILE"
cd "$PROJECT_DIR"

# ---------- 5. 前端构建 ----------
echo "" | tee -a "$LOG_FILE"
echo "▶ [5/6] 构建前端 (client + admin)..." | tee -a "$LOG_FILE"
for fe in client admin; do
    echo "   - $fe ..." | tee -a "$LOG_FILE"
    cd "frontend/$fe"
    # 修复构建缓存文件属主（历史遗留的 root 文件会导致 EACCES）
    chown -R zhaizz:zhaizz . 2>/dev/null || true
    sudo -u zhaizz npm install --no-audit --no-fund 2>&1 | tail -2 | tee -a "$LOG_FILE"
    sudo -u zhaizz npm run build 2>&1 | tail -5 | tee -a "$LOG_FILE"
    cd "$PROJECT_DIR"
done
echo "   ✓ 前端构建完成（nginx 直接读 dist，无需重启）" | tee -a "$LOG_FILE"

# ---------- 6. 等待后端就绪 + 验证 ----------
echo "" | tee -a "$LOG_FILE"
echo "▶ [6/6] 等待后端就绪并验证..." | tee -a "$LOG_FILE"
for i in $(seq 1 30); do
    code=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/api/client/me 2>/dev/null || echo "000")
    if [ "$code" != "000" ] && [ "$code" != "502" ] && [ "$code" != "503" ]; then
        break
    fi
    sleep 2
done

B_HTTP=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/api/client/me 2>/dev/null)
A_HTTP=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8090/api/client/agent/health 2>/dev/null)
C_HTTP=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:80/ 2>/dev/null)
D_HTTP=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:81/ 2>/dev/null)

echo "" | tee -a "$LOG_FILE"
echo "=========== 验证结果 ===========" | tee -a "$LOG_FILE"
echo "  业务后端 8080 : HTTP $B_HTTP (期望 401)" | tee -a "$LOG_FILE"
echo "  Agent 8090    : HTTP $A_HTTP (期望 200)" | tee -a "$LOG_FILE"
echo "  用户端 80     : HTTP $C_HTTP (期望 200)" | tee -a "$LOG_FILE"
echo "  管理端 81     : HTTP $D_HTTP (期望 200)" | tee -a "$LOG_FILE"
echo "================================" | tee -a "$LOG_FILE"

if [ "$C_HTTP" = "200" ] && [ "$D_HTTP" = "200" ] && [ "$A_HTTP" != "000" ]; then
    echo "✅ 更新完成！日志: $LOG_FILE" | tee -a "$LOG_FILE"
else
    echo "⚠️  部分服务异常，请查看日志: $LOG_FILE" | tee -a "$LOG_FILE"
    echo "    journalctl -u animetracker-business -n 50" | tee -a "$LOG_FILE"
    exit 1
fi
