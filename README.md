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
