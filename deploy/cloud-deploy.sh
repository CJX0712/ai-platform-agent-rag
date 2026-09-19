#!/usr/bin/env bash
# 云服部署脚本（FRP / SSH 场景）。作者：晨星
#
# 用法：
#   SSH_HOST=43.161.233.163 SSH_USER=root SSH_PORT=22 ./deploy/cloud-deploy.sh
#
# 说明：在目标机器上构建镜像并以 compose 启动；若目标机已通过 FRP 暴露端口，
# 公网可直接访问 http://<公网IP>:<远端映射端口>/health

set -euo pipefail

SSH_HOST="${SSH_HOST:-43.161.233.163}"
SSH_USER="${SSH_USER:-root}"
SSH_PORT="${SSH_PORT:-22}"
REMOTE_DIR="${REMOTE_DIR:-/opt/ai-platform-agent-rag}"
LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "[1/4] 同步代码到 ${SSH_USER}@${SSH_HOST}:${REMOTE_DIR}"
ssh -p "${SSH_PORT}" "${SSH_USER}@${SSH_HOST}" "mkdir -p ${REMOTE_DIR}"
rsync -avz --delete \
  --exclude '.venv' --exclude 'data' --exclude '.git' --exclude '__pycache__' \
  -e "ssh -p ${SSH_PORT}" \
  "${LOCAL_DIR}/" "${SSH_USER}@${SSH_HOST}:${REMOTE_DIR}/"

echo "[2/4] 准备配置文件"
ssh -p "${SSH_PORT}" "${SSH_USER}@${SSH_HOST}" \
  "cd ${REMOTE_DIR} && [ -f .env ] || cp deploy/.env.example .env && mkdir -p data"

echo "[3/4] 构建并启动（含健康检查）"
ssh -p "${SSH_PORT}" "${SSH_USER}@${SSH_HOST}" \
  "cd ${REMOTE_DIR} && docker compose -f deploy/docker-compose.yml up -d --build"

echo "[4/4] 验证 health 端点"
ssh -p "${SSH_PORT}" "${SSH_USER}@${SSH_HOST}" \
  "sleep 8 && curl -fsS http://127.0.0.1:8000/health"

echo "部署完成"
