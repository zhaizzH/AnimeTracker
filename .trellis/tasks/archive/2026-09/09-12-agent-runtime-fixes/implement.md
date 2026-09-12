# 实施清单

1. [x] 修复 Business envelope 解包、wishlist 状态判断，并补充适配器/收藏回归测试。
2. [x] 调整 Business 用户端和管理员端 SSE writer 生命周期和上游 4xx 映射，增加 Java 控制器/服务测试。
3. [x] 修复流式 fallback 聚合、保存失败可观测性，补充 Python streaming 测试。
4. [x] 更新失效 capability 测试，修复 reasoning 空格、确认短语与显式动作路由。
5. [x] 扩展 RAG 推荐过滤、compact 的 airDate/状态和不可用原因，确认实体查询器因缺少 Business 权威接口而暂缓，并补测。
6. [x] 接入前端已有 stop，更新组件测试和类型检查。
7. [x] 运行 Python pytest、Business Maven、三套前端 typecheck/Vitest；修复新增回归。
8. [x] 完成只读健康检查；复用本轮已有真实对话报告作为回放基线，未新增写入或模型消耗。

范围说明：F08 的“实体名称查询器注入”依赖尚不存在的 Business 名称搜索接口，本任务只完成不可用状态的结构化返回，不声称名称解析已修复。
