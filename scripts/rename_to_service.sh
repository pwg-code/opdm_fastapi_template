#!/usr/bin/env bash
# ============================================
# 模板占位符替换脚本
# ============================================
# 用法：
#   ./scripts/rename_to_service.sh <SERVICE_NAME> <SERVICE_PORT> <SERVICE_DIR>
#
# 示例：
#   ./scripts/rename_to_service.sh order_service 8007 order_service
#
# 作用：
#   把模板内的占位符（{SERVICE_NAME} / {SERVICE_PORT} / {SERVICE_WORKERS} /
#   <SERVICE_DIR> / <SERVICE_NAME> / <SERVICE_PORT>）替换为实际值。
#   必须在 .env.example 之前运行，避免误把示例 .env 替换。
# ============================================
set -euo pipefail

if [ "$#" -lt 3 ]; then
    echo "Usage: $0 <SERVICE_NAME> <SERVICE_PORT> <SERVICE_DIR>" >&2
    exit 1
fi

SERVICE_NAME="$1"
SERVICE_PORT="$2"
SERVICE_DIR="$3"
SERVICE_WORKERS="${4:-2}"

cd "$(dirname "$0")/.."
ROOT="$(pwd)"

echo "==> 替换占位符 (SERVICE_NAME=$SERVICE_NAME, SERVICE_PORT=$SERVICE_PORT, SERVICE_DIR=$SERVICE_DIR)"

# pyproject.toml
sed -i "s/{SERVICE_NAME}/$SERVICE_NAME/g" pyproject.toml

# app/config.py
sed -i "s/{SERVICE_NAME}/$SERVICE_NAME/g" app/config.py
sed -i "s/{SERVICE_PORT}/$SERVICE_PORT/g" app/config.py
sed -i "s/{SERVICE_WORKERS}/$SERVICE_WORKERS/g" app/config.py
sed -i "s/{AUTH_SERVICE_HOST}/$SERVICE_NAME-auth/g" app/config.py

# Dockerfile
sed -i "s|<SERVICE_DIR>|$SERVICE_DIR|g" Dockerfile
sed -i "s|<SERVICE_PORT>|$SERVICE_PORT|g" Dockerfile

# docker-compose.yml
sed -i "s|<SERVICE_DIR>|$SERVICE_DIR|g" docker-compose.yml
sed -i "s|<SERVICE_NAME>|$SERVICE_NAME|g" docker-compose.yml
sed -i "s|<SERVICE_PORT>|$SERVICE_PORT|g" docker-compose.yml

echo "==> 完成。请按需修改 .env.example 与 README.md 中剩余的 <...> 占位符。"