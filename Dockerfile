# ============================================
# OPDM FastAPI 服务 — 生产模式 Dockerfile
# ============================================
# 构建上下文：monorepo 根目录
# 构建命令：  docker build -f <SERVICE_DIR>/Dockerfile -t <SERVICE_NAME>:latest .
# 占位符（首次构建前替换）：
#   <SERVICE_DIR>     — 本服务在 monorepo 下的目录名（如 opdm_label_server）
#   <SERVICE_NAME>    — 服务名（与 .env 中 SERVICE_NAME 一致）
#   <SERVICE_PORT>    — 服务监听端口（与 .env 中 SERVICE_PORT 一致）
# ============================================

# ──────────────────────────────────────────────
# 阶段 1：基础镜像 — 安装系统依赖与 ODBC 驱动
# ──────────────────────────────────────────────
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Shanghai

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        curl \
        gnupg \
        unixodbc-dev \
        tzdata \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* \
    && curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl https://packages.microsoft.com/config/debian/12/prod.list | tee /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
        msodbcsql18 \
        mssql-tools18 \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

ENV PATH="/opt/mssql-tools18/bin:${PATH}"

# ──────────────────────────────────────────────
# 阶段 2：依赖安装
# ──────────────────────────────────────────────
FROM base AS dependencies

WORKDIR /app

# 复制本地私有依赖（整个 opdm_lib 项目，src 布局自动安装所有子包）
COPY opdm_lib /app/local_deps/opdm_lib

# 安装项目依赖
COPY <SERVICE_DIR>/pyproject.toml .
RUN pip install --upgrade pip \
    && pip install /app/local_deps/opdm_lib \
    && pip install --no-deps . \
    && pip install ".[prod]"

# ──────────────────────────────────────────────
# 阶段 3：生产镜像 — 烤入应用代码
# ──────────────────────────────────────────────
FROM base AS production

RUN useradd -m -u 1000 appuser \
    && mkdir -p /app/app /app/data \
    && chown -R appuser:appuser /app

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