# OPDM FastAPI 服务 — 编码规范

> 本规范适用于 monorepo 下所有使用本模板的服务。

---

### 编码规范

**所有代码必须通过 Type Hints**

1. **强制类型注解**：所有函数/方法必须标注参数与返回值类型，禁止省略。
2. **禁用 Any 与模糊类型**：严禁使用 `Any`、`dict`、`list`（无泛型）等无法推断具体结构的类型。类型不确定时用具体类型或 `object` + `isinstance` 守卫。任何结构化数据必须定义对应的 Schema（Pydantic Model / dataclass / TypedDict），确保每个字段类型可静态推断，杜绝数据模糊。
3. **现代语法**：必须使用 Python 3.12+ 语法（用 `A | B` 代替 `Union`，用 `list[int]` 代替 `List[int]`）。
4. **必须定义 Schema**：所有跨层传递的数据（请求体、响应体、Service 返回值、Repository 输出）必须定义明确的 Schema 类，禁止使用裸 `dict` 或 `Any` 传递结构化数据。Schema 是类型的唯一真相来源，没有 Schema 就没有该数据结构。
5. **显式 None**：可能返回空值的函数，必须标注 `| None`，禁止隐式返回空。
6. **单一职责**：单函数体代码不超过 50 行，复杂逻辑必须拆分为带类型注解的子函数。
7. **先结构后逻辑**：生成代码时，必须先输出数据模型定义，再输出业务逻辑代码。

**分层规范**

8. **严格分层调用**：`api/ → services/ → repositories/ → models/`，禁止跨层调用（如 api 直接调用 repository）或反向调用（如 repository 依赖 service）。
9. **schemas 隔离**：`schemas/` 定义接口层数据结构，`models/` 定义数据库映射，两层各自独立，禁止 Service 返回 Model 对象给路由层，必须转换为 Schema。
10. **依赖注入而非导入**：基础设施（DB 会话、Redis、外部客户端）通过 `core/deps.py` 注入，禁止在 Service 中直接 `import` 或自行创建连接。
11. **Repository 只做数据访问**：Repository 仅封装数据库查询逻辑，禁止包含业务判断或调用其他 Repository。
12. **Service 承载业务逻辑**：所有业务规则、跨表操作、外部调用编排均在 Service 层完成，路由层和 Repository 层不得包含业务逻辑。 **服务层不应直接操作数据库，所有对数据库的操作始终放在仓储层**

### Pydantic v2 原生方法规范

**禁止手动逐字段映射**，必须使用 `model_validate()`（ORM 对象加 `from_attributes=True`）替代 `_to_response()` 和 `Schema(**obj)`，用 `model_dump(exclude=.../exclude_unset=True)` 替代手写字典和 getattr 循环，响应体 Schema 应有默认值而请求体保持必填，字段定义只出现在 Schema 一处。