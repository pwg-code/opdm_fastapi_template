# AGENTS.md


## 目录结构

```

```

## 架构与编码规范

**分层**（CLAUDE.md 编码规范，已核对源码后修正为实际目录名）：
- 严格分层：`api/ → services/ → reps/（仓库层）→ models/`，禁止跨层调用（如 api 直接调 repository）或反向调用（如 repository 依赖 service）。注意目录名是 **`app/reps`**，不是 `repositories`。
- `schemas/` 定义接口层数据结构（Pydantic DTO），`models/` 定义数据库映射（SQLModel），两层独立；Service 只返回 Schema，禁止返回 Model 对象给路由层。
- 基础设施（DB 会话、Redis、auth）通过 `core/dependencies.py` 注入，禁止在 Service 中直接 `import` 或自行创建连接；**Service 层不得操作数据库，所有 DB 访问都在仓库层**。
- Repository 仅封装数据库查询，禁止包含业务判断或调用其他 Repository；所有业务规则、跨表操作、外部调用编排都在 Service 层。

**类型与 Pydantic v2**：
- 所有函数/方法必须标注参数与返回值类型，禁止省略。
- 禁用 `Any`、裸 `dict` / `list`（无泛型）等无法推断具体结构的类型；类型不确定时用具体类型或 `object` + `isinstance` 守卫。所有结构化数据必须定义对应的 Schema（Pydantic Model / dataclass / TypedDict）。
- 使用 Python 3.12+ 语法：`A | B`（代替 `Union`）、`list[int]`（代替 `List[int]`）；可能返回空值的函数必须标注 `| None`。
- 单函数体不超过 50 行，复杂逻辑拆分为带类型注解的子函数；生成代码时先输出数据模型定义，再输出业务逻辑。
- 禁止手动逐字段映射：用 `model_validate()`（ORM 对象加 `from_attributes=True`）代替 `_to_response()` 和 `Schema(**obj)`；用 `model_dump(exclude=.../exclude_unset=True)` 代替手写字典；字段定义只出现在 Schema 一处。响应体 Schema 有默认值，请求体 Schema 保持必填。
- 新增代码必须通过 pyright 静态检查。

## 数据库

- 异步 SQLAlchemy；开发默认 SQLite（`./data/opdm_iot.db`，见 `DB_CONNECTION_STRING`）；生产为 SQL Server（aioodbc，ODBC Driver 18）。
- SQLite 下启动时自动建表（`app/database/session.py` 的 `init_db`）。
- SQLModel 元数据都在 `app/models/config_domain.py` — 当前所有表都在这里（仅配置域，无产品表）。`docs/配置域数据库设计方案.md` 为权威设计文档。
- 统一错误响应：`core/exceptions.py` 覆盖 opdm_lib 默认 handler，统一返回 `{"code", "message", "data"}`；优先使用 `NotFoundError` / `ConflictError` / `BadRequestError` / `ExternalServiceError`（均继承 `BusinessError`），不要直接抛 HTTPException。

## 认证（opdm_lib）

- Auth / `BusinessError` 均**从 `opdm_lib` 再导出**（兄弟仓库 `../opdm_lib`，src 布局，通过 `[tool.uv.sources]` 以 editable 安装）。若某个符号找不到，很可能在 `opdm_lib/auth/__init__.py` — 应改那个仓库，而不是本仓库。
- 运行时认证（JWT + Redis 权限缓存）需要在启动时调用 `init_auth(...)`（secret_key、redis_url、reloader_base_url、reloader_service_token）— **目前 `app/main.py` 尚未接线**。接线前不要依赖 `RequirePermission` 等在运行时真正生效；`/health` 刻意不需要认证。

## 相关仓库

- `opdm_lib`（`../opdm_lib`）— 共享认证 / 异常代码。

