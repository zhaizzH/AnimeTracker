# AnimeTracker 后端错误拦截与代码规范

适用范围:`backend/business`(Spring Boot 3.2 多模块)。

## 一、错误拦截规范

1. **错误码 = HTTP 状态码**。业务错误码统一经 `ErrorType` 枚举 + `BizException` 抛出,禁止裸 int / 自定义错误码。
2. **抛异常**:service 层 `throw new BizException(ErrorType.X, "具体中文消息")`;需携带数据用三参构造 `BizException(ErrorType.X, "消息", data)`。
3. **响应路径**:
   - 安全层 401/403 → `SecurityConfig.writeJson`(filter 层,绕过 advice)
   - 方法级鉴权失败、业务异常、参数校验、框架异常 → `GlobalExceptionHandler`
4. **日志级别**:业务异常 `log.warn`(含 code/message);未知异常 `log.error`(全栈);参数校验失败 `log.warn`。
5. **禁止向客户端透传内部细节**:resourcePath、contentType、SQL、堆栈等一律泛化为通用中文消息。
6. **兜底映射**:DB 约束冲突(`DataIntegrityViolationException`)→ 409;方法级鉴权失败(`AccessDeniedException`)→ 403;未知异常 → 500。

## 二、注释规范

语言:**中文**。原则:**注释解释 why,不解释 what**。

| 位置 | 要求 |
|------|------|
| 类 | public / 关键类加 Javadoc,一行概述;需补一句细节时用 `<p>` |
| 方法 | public 方法加 Javadoc,一句话说明"做什么",然后依次解释各参数和返回值;controller 端点 doc 补充触发条件(如"注册后需 verify-email");需补一句细节时用 `<p>`|
| `@param` / `@return` | 仅当参数 / 返回非显然时写,不机械堆 |
| private 方法 | 逻辑非显然才加,否则不加 |
| 行内注释 | 只解释 why / 隐藏约束 / 已知坑,不解释 what |
| 常量 / 字段 | 非显然含义才加 `//`,pojo模块除外,该模块类中所有字段都需要添加注释, entity按照docs\db-schema.sql描述添加注释,vo和dto按照业务含义和docs\db-schema.sql添加注释|
| 测试类 | 可不加类 doc,测试方法名自解释即可 |

### 反例

```java
// 自解释代码加注释(what) ✗
int total = a + b; // 计算总数

// 无信息量的类注释 ✗
/** 这个类 */

// 机械堆 @param ✗
/** @param name 名字 */
```

### 正例

```java
/**
 * 统一响应体 {code, message, data}
 */
@Getter
@JsonInclude(JsonInclude.Include.NON_NULL)
public class Result<T> { ... }

// token 先算 SHA256,防止明文 token 进 Redis 键
String tokenHash = DigestUtils.sha256Hex(token);
```

## 三、错误响应结构

统一 `{code, message, data}`:

```json
{ "code": 404, "message": "接口不存在" }
```

- `code` = HTTP 状态码;`data` 仅业务异常携带(如参数校验字段错误映射),成功时 `data` 为业务数据。
