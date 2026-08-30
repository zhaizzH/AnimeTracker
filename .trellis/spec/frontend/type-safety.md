# 类型安全规范

## 类型所有权

- 跨应用/跨页面 API 类型集中在 `packages/shared/src/types/index.ts`。
- 仅组件内部使用的 props、表单和视图状态留在组件附近。
- shared API 函数声明精确输入/输出泛型，调用方不重复写响应结构。
- Java `Long` 业务 ID 在前端现有契约中使用 `string`，避免超过安全整数。
- 状态/角色/收藏类型使用联合类型，例如 `UserRole`、`CollectionType`。

## HTTP 边界

- `http.ts` 将 `ApiResult<T>` 解包为 `T`；普通 API 函数不要再次访问 `.data`。
- 上传使用 `postForm`，普通 JSON 使用 `get/post`；SSE 单独走 `streamSse`。
- 未知 JSON 先用 `unknown` 或最小接口收窄；避免 `any`。
- 类型断言只允许在 Axios/SSE 等边界，收窄后不要向组件继续传播 `Record<string, unknown>`。
- 当前没有 Zod 等运行时 schema；服务端字段变化必须靠端到端核对与测试补足。

## 跨层同步

改字段时同时检查：

1. Java DTO/VO 或 Python Pydantic schema。
2. `docs/spec/openapi.yaml`。
3. shared types 与 API 函数。
4. Query key、表单初值和渲染分支。
5. 相关 Vitest/pytest 用例。

## 禁止做法

- 用非空断言掩盖实际可缺失的 API 字段。
- 将 `unknown` 直接强转成完整领域对象。
- 同一响应在 client/admin 分别定义两套近似类型。
- 用 `number` 接收可能超过 JS 安全范围的数据库 ID。
