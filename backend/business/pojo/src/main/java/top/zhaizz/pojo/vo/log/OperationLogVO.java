package top.zhaizz.pojo.vo.log;

import java.time.LocalDateTime;

/**
 * 操作日志 VO
 */
public class OperationLogVO {

    /** 日志ID */
    private Long id;
    /** 用户ID（匿名失败登录为NULL） */
    private Long userId;
    /** 用户名/邮箱快照 */
    private String username;
    /** 动作 */
    private String action;
    /** 模块 */
    private String module;
    /** HTTP 方法 */
    private String method;
    /** 请求路径 */
    private String path;
    /** 历史请求参数字段，当前采集器不填充 */
    private String params;
    /** 客户端 IP */
    private String ip;
    /** 客户端代理标识；当前采集器不填充，保留历史字段 */
    private String userAgent;
    /** 0=成功, 1=失败 */
    private Integer status;
    /** 失败原因 */
    private String errorMsg;
    /** 耗时(毫秒) */
    private Long durationMs;
    /** 创建时间 */
    private LocalDateTime createdAt;

    /** 创建字段均为默认值的空日志对象 */
    public OperationLogVO() {
    }

    /**
     * 获取日志ID
     * @return 操作日志主键；未提供时为 {@code null}
     */
    public Long getId() {
        return this.id;
    }

    /**
     * 获取用户ID
     * @return 操作者用户ID；匿名失败登录时为 {@code null}
     */
    public Long getUserId() {
        return this.userId;
    }

    /**
     * 获取用户名/邮箱快照
     * @return 操作时的用户名或邮箱快照；未提供时为 {@code null}
     */
    public String getUsername() {
        return this.username;
    }

    /**
     * 获取动作
     * @return 操作动作标识；未提供时为 {@code null}
     */
    public String getAction() {
        return this.action;
    }

    /**
     * 获取模块
     * @return 操作所属业务模块；未提供时为 {@code null}
     */
    public String getModule() {
        return this.module;
    }

    /**
     * 获取 HTTP 方法
     * @return 请求的 HTTP 方法；未提供时为 {@code null}
     */
    public String getMethod() {
        return this.method;
    }

    /**
     * 获取请求路径
     * @return 请求的 URL 路径；未提供时为 {@code null}
     */
    public String getPath() {
        return this.path;
    }

    /**
     * 获取请求参数
     * @return 历史请求参数字段，当前采集器不填充；未提供时为 {@code null}
     */
    public String getParams() {
        return this.params;
    }

    /**
     * 获取客户端 IP
     * @return 发起请求的客户端 IP；未提供时为 {@code null}
     */
    public String getIp() {
        return this.ip;
    }

    /**
     * 获取客户端代理标识
     * @return 客户端 User-Agent；当前采集器不填充，未提供时为 {@code null}
     */
    public String getUserAgent() {
        return this.userAgent;
    }

    /**
     * 获取状态
     * @return 0=成功, 1=失败；未提供时为 {@code null}
     */
    public Integer getStatus() {
        return this.status;
    }

    /**
     * 获取失败原因
     * @return 操作失败时的错误描述；成功时为 {@code null}
     */
    public String getErrorMsg() {
        return this.errorMsg;
    }

    /**
     * 获取耗时
     * @return 操作耗时（毫秒）；未提供时为 {@code null}
     */
    public Long getDurationMs() {
        return this.durationMs;
    }

    /**
     * 获取创建时间
     * @return 日志记录创建时间；未提供时为 {@code null}
     */
    public LocalDateTime getCreatedAt() {
        return this.createdAt;
    }

    /**
     * 替换日志ID
     * @param id 操作日志主键，可为 {@code null}
     */
    public void setId(final Long id) {
        this.id = id;
    }

    /**
     * 替换用户ID
     * @param userId 操作者用户ID，匿名失败登录时为 {@code null}
     */
    public void setUserId(final Long userId) {
        this.userId = userId;
    }

    /**
     * 替换用户名/邮箱快照
     * @param username 操作时的用户名或邮箱快照，可为 {@code null}
     */
    public void setUsername(final String username) {
        this.username = username;
    }

    /**
     * 替换动作
     * @param action 操作动作标识，可为 {@code null}
     */
    public void setAction(final String action) {
        this.action = action;
    }

    /**
     * 替换模块
     * @param module 操作所属业务模块，可为 {@code null}
     */
    public void setModule(final String module) {
        this.module = module;
    }

    /**
     * 替换 HTTP 方法
     * @param method 请求的 HTTP 方法，可为 {@code null}
     */
    public void setMethod(final String method) {
        this.method = method;
    }

    /**
     * 替换请求路径
     * @param path 请求的 URL 路径，可为 {@code null}
     */
    public void setPath(final String path) {
        this.path = path;
    }

    /**
     * 替换请求参数
     * @param params 历史请求参数字段，当前采集器不填充，可为 {@code null}
     */
    public void setParams(final String params) {
        this.params = params;
    }

    /**
     * 替换客户端 IP
     * @param ip 发起请求的客户端 IP，可为 {@code null}
     */
    public void setIp(final String ip) {
        this.ip = ip;
    }

    /**
     * 替换客户端代理标识
     * @param userAgent 客户端 User-Agent，当前采集器不填充，可为 {@code null}
     */
    public void setUserAgent(final String userAgent) {
        this.userAgent = userAgent;
    }

    /**
     * 替换状态
     * @param status 0=成功, 1=失败，可为 {@code null}
     */
    public void setStatus(final Integer status) {
        this.status = status;
    }

    /**
     * 替换失败原因
     * @param errorMsg 操作失败时的错误描述，可为 {@code null}
     */
    public void setErrorMsg(final String errorMsg) {
        this.errorMsg = errorMsg;
    }

    /**
     * 替换耗时
     * @param durationMs 操作耗时（毫秒），可为 {@code null}
     */
    public void setDurationMs(final Long durationMs) {
        this.durationMs = durationMs;
    }

    /**
     * 替换创建时间
     * @param createdAt 日志记录创建时间，可为 {@code null}
     */
    public void setCreatedAt(final LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof OperationLogVO)) return false;
        final OperationLogVO other = (OperationLogVO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisId = this.getId();
        final Object otherId = other.getId();
        if (thisId == null ? otherId != null : !thisId.equals(otherId)) return false;
        final Object thisUserId = this.getUserId();
        final Object otherUserId = other.getUserId();
        if (thisUserId == null ? otherUserId != null : !thisUserId.equals(otherUserId)) return false;
        final Object thisStatus = this.getStatus();
        final Object otherStatus = other.getStatus();
        if (thisStatus == null ? otherStatus != null : !thisStatus.equals(otherStatus)) return false;
        final Object thisDurationMs = this.getDurationMs();
        final Object otherDurationMs = other.getDurationMs();
        if (thisDurationMs == null ? otherDurationMs != null : !thisDurationMs.equals(otherDurationMs)) return false;
        final Object thisUsername = this.getUsername();
        final Object otherUsername = other.getUsername();
        if (thisUsername == null ? otherUsername != null : !thisUsername.equals(otherUsername)) return false;
        final Object thisAction = this.getAction();
        final Object otherAction = other.getAction();
        if (thisAction == null ? otherAction != null : !thisAction.equals(otherAction)) return false;
        final Object thisModule = this.getModule();
        final Object otherModule = other.getModule();
        if (thisModule == null ? otherModule != null : !thisModule.equals(otherModule)) return false;
        final Object thisMethod = this.getMethod();
        final Object otherMethod = other.getMethod();
        if (thisMethod == null ? otherMethod != null : !thisMethod.equals(otherMethod)) return false;
        final Object thisPath = this.getPath();
        final Object otherPath = other.getPath();
        if (thisPath == null ? otherPath != null : !thisPath.equals(otherPath)) return false;
        final Object thisParams = this.getParams();
        final Object otherParams = other.getParams();
        if (thisParams == null ? otherParams != null : !thisParams.equals(otherParams)) return false;
        final Object thisIp = this.getIp();
        final Object otherIp = other.getIp();
        if (thisIp == null ? otherIp != null : !thisIp.equals(otherIp)) return false;
        final Object thisUserAgent = this.getUserAgent();
        final Object otherUserAgent = other.getUserAgent();
        if (thisUserAgent == null ? otherUserAgent != null : !thisUserAgent.equals(otherUserAgent)) return false;
        final Object thisErrorMsg = this.getErrorMsg();
        final Object otherErrorMsg = other.getErrorMsg();
        if (thisErrorMsg == null ? otherErrorMsg != null : !thisErrorMsg.equals(otherErrorMsg)) return false;
        final Object thisCreatedAt = this.getCreatedAt();
        final Object otherCreatedAt = other.getCreatedAt();
        if (thisCreatedAt == null ? otherCreatedAt != null : !thisCreatedAt.equals(otherCreatedAt)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof OperationLogVO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashId = this.getId();
        result = result * PRIME + (hashId == null ? 43 : hashId.hashCode());
        final Object hashUserId = this.getUserId();
        result = result * PRIME + (hashUserId == null ? 43 : hashUserId.hashCode());
        final Object hashStatus = this.getStatus();
        result = result * PRIME + (hashStatus == null ? 43 : hashStatus.hashCode());
        final Object hashDurationMs = this.getDurationMs();
        result = result * PRIME + (hashDurationMs == null ? 43 : hashDurationMs.hashCode());
        final Object hashUsername = this.getUsername();
        result = result * PRIME + (hashUsername == null ? 43 : hashUsername.hashCode());
        final Object hashAction = this.getAction();
        result = result * PRIME + (hashAction == null ? 43 : hashAction.hashCode());
        final Object hashModule = this.getModule();
        result = result * PRIME + (hashModule == null ? 43 : hashModule.hashCode());
        final Object hashMethod = this.getMethod();
        result = result * PRIME + (hashMethod == null ? 43 : hashMethod.hashCode());
        final Object hashPath = this.getPath();
        result = result * PRIME + (hashPath == null ? 43 : hashPath.hashCode());
        final Object hashParams = this.getParams();
        result = result * PRIME + (hashParams == null ? 43 : hashParams.hashCode());
        final Object hashIp = this.getIp();
        result = result * PRIME + (hashIp == null ? 43 : hashIp.hashCode());
        final Object hashUserAgent = this.getUserAgent();
        result = result * PRIME + (hashUserAgent == null ? 43 : hashUserAgent.hashCode());
        final Object hashErrorMsg = this.getErrorMsg();
        result = result * PRIME + (hashErrorMsg == null ? 43 : hashErrorMsg.hashCode());
        final Object hashCreatedAt = this.getCreatedAt();
        result = result * PRIME + (hashCreatedAt == null ? 43 : hashCreatedAt.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "OperationLogVO(id=" + this.getId() + ", userId=" + this.getUserId() + ", username=" + this.getUsername() + ", action=" + this.getAction() + ", module=" + this.getModule() + ", method=" + this.getMethod() + ", path=" + this.getPath() + ", params=" + this.getParams() + ", ip=" + this.getIp() + ", userAgent=" + this.getUserAgent() + ", status=" + this.getStatus() + ", errorMsg=" + this.getErrorMsg() + ", durationMs=" + this.getDurationMs() + ", createdAt=" + this.getCreatedAt() + ")";
    }
}
