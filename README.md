# opdm_fastapi_template

> OPDM monorepo 下新后端服务的**生产就绪脚手架**。

## 项目定位

本仓库是 monorepo 内所有 OPDM FastAPI 后端服务的种子工程。模板**只携带通用基础能力，不携带任何业务能力**：

- ✅ 通用响应包装 / 通用查询框架 / 通用 CRUD 基类
- ✅ 业务异常体系 + SQLAlchemy IntegrityError 友好解析
- ✅ 业务级 Redis 单例（带降级）
- ✅ Alembic 异步迁移
- ✅ gunicorn 生产部署镜像 + bridge 网络编排
- ❌ 不包含：车间隔离、EAV、SN 流水号、Excel 导入导出、变更日志、Dashboard、业务路由示例

业务方 clone 本模板后，按需在 `app/api/`、`app/services/`、`app/repositories/`、`app/models/`、`app/schemas/` 下扩展业务模块即可。

## 快速开始

### 1. 占位符替换

模板内的占位符（`{SERVICE_NAME}` / `{SERVICE_PORT}` / `{SERVICE_WORKERS}` / `<...>` 等）需在首次构建前替换。

```bash
# 进入 monorepo 根目录
cd <monorepo-root>

# 把模板目录重命名为你的服务目录（如 order_service）
mv opdm_fastapi_template <SERVICE_DIR>

cd <SERVICE_DIR>

# 替换 pyproject.toml / Dockerfile / docker-compose.yml 中的占位符
sed -i 's/{SERVICE_NAME}/order_service/g' pyproject.toml
sed -i 's/<SERVICE_DIR>/order_service/g' Dockerfile docker-compose.yml
sed -i 's/<SERVICE_NAME>/order_service/g' docker-compose.yml
sed -i 's/<SERVICE_PORT>/8007/g' docker-compose.yml
```

或使用 `scripts/rename_to_service.sh`（见脚本顶部说明）。

### 2. 配置 .env

```bash
cp .env.example .env
# 编辑 .env，替换所有 <...> 占位符为实际值
```

### 3. 安装依赖（开发者本地）

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[prod,dev]"
```

### 4. 数据库迁移

```bash
# 生成首版迁移（需先在 app/models/__init__.py 中 import 所有业务 Model）
alembic revision --autogenerate -m "init"
alembic upgrade head
```

### 5. 本地启动（开发者 sanity check）

```bash
APP_ENV=development uvicorn app.main:app --port 8000 --reload
```

访问 http://localhost:8000/docs 查看 Swagger。

### 6. 生产部署

```bash
docker network create opdm-net          # 仅首次需要
docker compose build
docker compose up -d
```

宿主机 nginx 反向代理 `443/80 → 127.0.0.1:${SERVICE_PORT}` 即可对外暴露。

## 占位符替换清单

| 占位符 | 出现位置 | 替换示例 |
|---|---|---|
| `{SERVICE_NAME}` | `pyproject.toml`、`app/config.py` | `order_service` |
| `{SERVICE_PORT}` | `app/config.py` | `8007` |
| `{SERVICE_WORKERS}` | `app/config.py` | `2` |
| `{SERVICE_TOKEN}` | `app/config.py`、`.env` | `secrets.token_urlsafe(32)` 输出 |
| `{JWT_SECRET_KEY}` | `app/config.py`、`.env` | `uuid.uuid4().hex` 输出 |
| `{AUTH_SERVICE_HOST}` | `app/config.py`、`.env` | `auth.opdm.local` |
| `<SERVICE_DIR>` | `Dockerfile`、`docker-compose.yml` | 实际服务目录名 |
| `<SERVICE_NAME>` | `docker-compose.yml` | 实际服务名 |
| `<SERVICE_PORT>` | `docker-compose.yml` | 实际服务端口 |
| `<DB_CONNECTION_STRING>` | `.env` | `sqlite+aiosqlite:///./data/app.db` 或 SQL Server 串 |
| `<SERVICE_TOKEN>` | `.env` | 同上 |
| `<JWT_SECRET_KEY>` | `.env` | 同上 |
| `<AUTH_SERVICE_HOST>` | `.env` | 同上 |

## 目录结构

```
<SERVICE_DIR>/
├── .env.example              # 参数化环境变量模板
├── .gitignore                # 防 .env / db 误提交
├── alembic/                  # 数据库迁移
│   ├── env.py                # 异步迁移环境
│   └── versions/             # 迁移脚本（首次需生成）
├── alembic.ini
├── CLAUDE.md                 # 12 条编码规范
├── Dockerfile                # 生产模式（gunicorn + 烤入镜像）
├── docker-compose.yml        # 生产模式（bridge + nginx 反代）
├── pyproject.toml            # 依赖 + ruff 配置
├── README.md                 # 本文件
├── app/
│   ├── api/                  # 路由层（默认空架子）
│   ├── core/                 # 异常 / Integrity / Redis / 依赖注入
│   ├── database/             # 异步引擎与会话
│   ├── models/               # SQLModel 数据模型
│   ├── repositories/         # 数据仓储层（含 CrudRepo 基类）
│   ├── schemas/              # Pydantic Schema（ApiResponse / ListQuery / CRUD 基类）
│   ├── services/             # 业务逻辑层（含 CrudService 基类）
│   ├── config.py             # Settings（pydantic-settings）
│   └── main.py               # FastAPI 工厂 + 生命周期 + 异常处理
├── scripts/                  # 运维脚本（如 rename_to_service.sh）
└── temp/                     # 工作区文档（不入镜像）
```

## 禁止事项

- ❌ **禁止将真实 `.env` 提交到仓库**（`.gitignore` 已屏蔽）
- ❌ 禁止提交 `dbhub.toml`、`*.db`、`data/`、`*.sqlite3`
- ❌ 禁止在 `app/api/__init__.py` 默认 router 下硬编码业务 prefix
- ❌ 禁止在 `app/services/` 中直接调用 SQLAlchemy / 数据库 API
- ❌ 禁止在 `app/repositories/` 中调用其他 Repo 或外部 HTTP 客户端
- ❌ 禁止在模板中新增业务专属能力（车间隔离 / EAV / SN / Excel 等）

## 模板能力速查

### 响应包装

```python
from app.schemas.response import ApiResponse

@app.get("/users/{id}", response_model=ApiResponse[UserRead])
async def get_user(id: int) -> ApiResponse[UserRead]:
    user = ...
    return ApiResponse[UserRead].ok(data=user)
```

### 通用列表查询

```python
from app.schemas.query import ListQuery, SortSpec, FilterOperation, FieldCondition, ConditionGroup

class UserListQuery(ListQuery):
    pass

@app.post("/users/list", response_model=ApiResponse[PaginatedResponse[UserRead]])
async def list_users(query: UserListQuery) -> ApiResponse[PaginatedResponse[UserRead]]:
    rows, total = await service.list_paginated(query)
    return ApiResponse[PaginatedResponse[UserRead]].ok(
        data=PaginatedResponse[UserRead](items=rows, total=total),
    )
```

### 业务异常

```python
from app.core.exceptions import NotFoundError, ConflictError

user = await repo.get_by_id(uid)
if user is None:
    raise NotFoundError(f"用户 #{uid} 不存在")
```

### IntegrityError 友好消息

```python
# 业务启动时注册表-列到友好消息的映射
from app.core.integrity import register_constraint_message

register_constraint_message("tb_user", "username", "用户名已存在")
register_constraint_message("tb_user", "email", "邮箱已被注册")
```

## 参考

- 模板抽取源：`D:\project\opdm\opdm_label_server`
- 详细升级计划：`temp/plans/2026-07-07_template_upgrade.md`