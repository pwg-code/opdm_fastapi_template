# ============================================
# OPDM FastAPI 服务 - Dockerfile
# 生产环境镜像 - Python 3.13 + SQL Server ODBC
# ============================================

# ============================================
# 阶段 1: 基础镜像 - 安装系统依赖和 ODBC 驱动
# ============================================
FROM python:3.13-slim as base

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

# ============================================
# 阶段 2: 依赖安装阶段
# ============================================
FROM base as dependencies

WORKDIR /app

# 复制本地私有依赖包（整个 opdm_lib 项目，src 布局会自动安装所有子包）
COPY opdm_lib /app/local_deps/opdm_lib

# 安装项目依赖（注意：Dockerfile context 需指向 monorepo 根目录）
COPY <your-service-dir>/pyproject.toml .
RUN pip install --upgrade pip && \
    pip install /app/local_deps/opdm_lib && \
    pip install -e ".[prod]" && \
    pip install watchfiles

# ============================================
# 阶段 3: 生产环境镜像
# ============================================
FROM base as production

RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/app /app/data && \
    chown -R appuser:appuser /app

COPY --from=dependencies /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

WORKDIR /app

# 注意：应用代码通过 volume 挂载，不打包进镜像（支持热重载）

USER appuser

ARG SERVICE_PORT=8000
EXPOSE ${SERVICE_PORT}

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${SERVICE_PORT:-8000}/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${SERVICE_PORT:-8000} --reload --reload-dir /app/app"]
