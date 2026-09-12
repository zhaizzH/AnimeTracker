# 技术设计

## 1. Business 信封与收藏状态

在 backend/agent/app/adapters/business_http.py 统一识别 {code,message,data}。存在 data 键时返回其值；成功信封缺少 data 时返回 None；普通字典保持原样。扩展 BusinessGateway 的可空返回类型，并让 wishlist 状态检查只在明确的集合对象存在时判定为已收集。

## 2. Business SSE 错误语义

用户端和管理员端 SSE 控制器都不在调用上游前获取 PrintWriter 或提交 SSE 响应；仅在收到首行成功数据时初始化 writer。这样 AgentServiceImpl 抛出的上游 4xx 仍由全局异常处理器转换为标准错误响应，成功流的换行和 UTF-8 保持不变。

## 3. 流式聚合与持久化

stream_agent_events 使用单一聚合缓冲区。正常 token 和 fallback 都先追加再发送；结束时将同一缓冲区传给保存回调。保存异常记录结构化日志并发出失败状态/遥测字段，随后仍发送结束事件，避免客户端永久等待。

## 4. Runtime 与意图路由

把过时的能力测试改写为当前 entry -> gateway/admin graph 契约。reasoning 分片只去除整段空白，不去除词间空格。确认解析先处理完整短语，再应用否定词规则。对“推荐/添加到愿望单”等明确动作保留确定性路由；普通搜索继续走搜索节点。

## 5. RAG 证据与结构化过滤

推荐工具新增可选的年份、季度、评分、播出状态等字段并原样传给 use case。subject compact 输出 airDate 和基于未来剧集的显式状态；无法判断时输出 UNKNOWN。RAG 不可用返回 {available:false, reason:...} 结构，正常无结果仍返回空列表。实体名称解析暂不注入：当前 Business 没有权威名称查询接口，运行时保持 fail-closed 并把不可用原因传递给调用方。

## 6. 前端停止操作

复用 useAgentChat 已有的 stop，在 AgentConversation 流式期间将发送按钮切换为停止按钮；停止后恢复输入态，不改变已完成消息。

## 兼容与回滚

所有改动局限于 Agent 适配器、流式控制器、RAG 契约、runtime 路由和聊天组件；旧请求字段、SSE 事件名及正常响应保持兼容。若上游 Business 版本暂不支持结构化过滤，字段为空时走原有查询路径即可单独回滚该分支。
