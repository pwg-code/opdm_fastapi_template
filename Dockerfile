# ============================================
# OPDM FastAPI 服务 — 生产模式 Dockerfile
# ============================================
# 构建上下文：monorepo 根目录
# 构建命令：  docker build -f <SERVICE_DIR>/Dockerfile -t <SERVICE_NAME>:latest .
# 前置条件：需先构建 opdm-base 公共基础镜像（见 docker-base/README.md）：
#   docker build -t opdm-base:py3.12-odbc18 docker-base/
# 占位符（首次构建前替换）：
#   <SERVICE_DIR>     — 本服务在 monorepo 下的目录名（如 opdm_label_server）
#   <SERVICE_NAME>    — 服务名（与 .env 中 SERVICE_NAME 一致）
#   <SERVICE_PORT>    — 服务监听端口（与 .env 中 SERVICE_PORT 一致）
# ============================================

# ──────────────────────────────────────────────
# 阶段 1：基础镜像 — 复用 monorepo 公共基础镜像
# ──────────────────────────────────────────────
# 基础镜像：python:3.12-slim + gcc/g++ + MS ODBC Driver 18（源码与构建说明见 docker-base/README.md）
ARG BASE_IMAGE=opdm-base:py3.12-odbc18
FROM ${BASE_IMAGE} AS base

# ──────────────────────────────────────────────
# 阶段 2：依赖安装
# ──────────────────────────────────────────────
FROM base AS dependencies

WORKDIR /app

# 复制本地私有依赖（路径须与 uv.lock 记录的 ../opdm_lib 相对路径一致）
COPY opdm_lib /app/opdm_lib

# 复制依赖清单（uv.lock 锁定全部第三方依赖版本，重建镜像不再隐性升级）
COPY <SERVICE_DIR>/pyproject.toml <SERVICE_DIR>/uv.lock ./<SERVICE_DIR>/
RUN pip install --upgrade pip uv \
    && cd /app/<SERVICE_DIR> \
    && UV_PROJECT_ENVIRONMENT=/usr/local UV_PYTHON_DOWNLOADS=never uv sync \
       --locked --no-dev --extra prod --no-editable --no-install-project
# --locked            lock 与 pyproject 不一致时构建失败，防止漏跑 uv lock 的静默漂移
# --no-dev            跳过 dev 依赖
# --extra prod        安装生产 extra（ODBC 等）
# --no-editable       opdm_lib 以常规方式装入 site-packages（生产阶段无需源码）
# --no-install-project 项目包由生产阶段 COPY 烤入，此处只装第三方依赖

# ──────────────────────────────────────────────
# 阶段 3：生产镜像 — 烤入应用代码
# ──────────────────────────────────────────────
FROM base AS production

RUN id -u appuser &>/dev/null || useradd -m -u 1000 -o appuser \
    && mkdir -p /app/app /app/data /app/scripts \
    && chown appuser:appuser /app

COPY --from=dependencies /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

WORKDIR /app

# 烤入应用代码（构建上下文为 monorepo 根目录；改代码需重建镜像）
COPY --chown=appuser:appuser <SERVICE_DIR>/app /app/app

USER appuser

ARG SERVICE_PORT=8000
EXPOSE ${SERVICE_PORT}

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${SERVICE_PORT:-8000}/health || exit 1

# 生产模式 gunicorn 启动（无 --reload；worker 数与超时由环境变量控制）
CMD ["sh", "-c", "gunicorn app.main:app \
    --bind 0.0.0.0:${SERVICE_PORT:-8000} \
    --workers ${SERVICE_WORKERS:-2} \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 300 \
    --log-level ${LOG_LEVEL:-info}"]