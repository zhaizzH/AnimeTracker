package top.zhaizz.pojo.dto.log;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import org.springframework.format.annotation.DateTimeFormat;
import java.time.LocalDate;

/**
 * 日志查询参数
 */
public class LogQueryDTO {
    /**
     * 动作
     */
    private String action; // 动作
    /**
     * 模块
     */
    private String module; // 模块
    /**
     * 用户名/邮箱快照
     */
    private String username; // 用户名/邮箱快照
    /**
     * 用户ID
     */
    private Long userId; // 用户ID
    /**
     * 状态: 0=成功, 1=失败
     */
    private Integer status; // 状态: 0=成功, 1=失败
    /**
     * 开始日期(含)
     */
    @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
    private LocalDate start; // 开始日期(含)
    /**
     * 结束日期(含)
     */
    @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
    private LocalDate end; // 结束日期(含)
    /**
     * 页码
     */
    @Min(value = 1, message = "页码不能小于1")
    private int page = 1; // 页码
    /**
     * 每页条数
     */
    @Min(value = 1, message = "每页条数不能小于1")
    @Max(value = 100, message = "每页条数不能超过100")
    private int size = 20; // 每页条数

    /** 创建使用默认分页参数的空查询对象 */
    public LogQueryDTO() {
    }

    /**
     * 获取动作
     * @return 操作动作过滤值；为 {@code null} 时不过滤动作
     */
    public String getAction() {
        return this.action;
    }

    /**
     * 获取模块
     * @return 所属模块过滤值；为 {@code null} 时不过滤模块
     */
    public String getModule() {
        return this.module;
    }

    /**
     * 获取用户名/邮箱快照
     * @return 操作时记录的用户名或邮箱快照；为 {@code null} 时不过滤用户
     */
    public String getUsername() {
        return this.username;
    }

    /**
     * 获取用户ID
     * @return 操作用户的 ID；为 {@code null} 时不过滤用户 ID
     */
    public Long getUserId() {
        return this.userId;
    }

    /**
     * 获取操作状态
     * @return 状态过滤值，0=成功、1=失败；为 {@code null} 时不过滤状态
     */
    public Integer getStatus() {
        return this.status;
    }

    /**
     * 获取开始日期
     * @return 查询起始日期（含当天），按 ISO 日期绑定；为 {@code null} 时不限制下界
     */
    public LocalDate getStart() {
        return this.start;
    }

    /**
     * 获取结束日期
     * @return 查询结束日期（含当天），按 ISO 日期绑定；为 {@code null} 时不限制上界
     */
    public LocalDate getEnd() {
        return this.end;
    }

    /**
     * 获取页码
     * @return 当前页码，默认 1，取值不得小于 1
     */
    public int getPage() {
        return this.page;
    }

    /**
     * 获取每页条数
     * @return 单页记录数，默认 20，取值需在 1~100 之间
     */
    public int getSize() {
        return this.size;
    }

    /**
     * 替换动作
     * @param action 操作动作过滤值；可为 {@code null} 表示不过滤动作
     */
    public void setAction(final String action) {
        this.action = action;
    }

    /**
     * 替换模块
     * @param module 所属模块过滤值；可为 {@code null} 表示不过滤模块
     */
    public void setModule(final String module) {
        this.module = module;
    }

    /**
     * 替换用户名/邮箱快照
     * @param username 操作时记录的用户名或邮箱快照；可为 {@code null} 表示不过滤用户
     */
    public void setUsername(final String username) {
        this.username = username;
    }

    /**
     * 替换用户ID
     * @param userId 操作用户的 ID；可为 {@code null} 表示不过滤用户 ID
     */
    public void setUserId(final Long userId) {
        this.userId = userId;
    }

    /**
     * 替换操作状态
     * @param status 状态过滤值，0=成功、1=失败；可为 {@code null} 表示不过滤状态
     */
    public void setStatus(final Integer status) {
        this.status = status;
    }

    /**
     * 替换开始日期
     * @param start 查询起始日期（含当天），按 ISO 日期绑定；可为 {@code null} 表示不限制下界
     */
    public void setStart(final LocalDate start) {
        this.start = start;
    }

    /**
     * 替换结束日期
     * @param end 查询结束日期（含当天），按 ISO 日期绑定；可为 {@code null} 表示不限制上界
     */
    public void setEnd(final LocalDate end) {
        this.end = end;
    }

    /**
     * 替换页码
     * @param page 新的页码，从 1 开始，不得小于 1
     */
    public void setPage(final int page) {
        this.page = page;
    }

    /**
     * 替换每页条数
     * @param size 新的单页记录数，需在 1~100 之间
     */
    public void setSize(final int size) {
        this.size = size;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof LogQueryDTO)) return false;
        final LogQueryDTO other = (LogQueryDTO) o;
        if (!other.canEqual((Object) this)) return false;
        if (this.getPage() != other.getPage()) return false;
        if (this.getSize() != other.getSize()) return false;
        final Object thisUserId = this.getUserId();
        final Object otherUserId = other.getUserId();
        if (thisUserId == null ? otherUserId != null : !thisUserId.equals(otherUserId)) return false;
        final Object thisStatus = this.getStatus();
        final Object otherStatus = other.getStatus();
        if (thisStatus == null ? otherStatus != null : !thisStatus.equals(otherStatus)) return false;
        final Object thisAction = this.getAction();
        final Object otherAction = other.getAction();
        if (thisAction == null ? otherAction != null : !thisAction.equals(otherAction)) return false;
        final Object thisModule = this.getModule();
        final Object otherModule = other.getModule();
        if (thisModule == null ? otherModule != null : !thisModule.equals(otherModule)) return false;
        final Object thisUsername = this.getUsername();
        final Object otherUsername = other.getUsername();
        if (thisUsername == null ? otherUsername != null : !thisUsername.equals(otherUsername)) return false;
        final Object thisStart = this.getStart();
        final Object otherStart = other.getStart();
        if (thisStart == null ? otherStart != null : !thisStart.equals(otherStart)) return false;
        final Object thisEnd = this.getEnd();
        final Object otherEnd = other.getEnd();
        if (thisEnd == null ? otherEnd != null : !thisEnd.equals(otherEnd)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof LogQueryDTO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        result = result * PRIME + this.getPage();
        result = result * PRIME + this.getSize();
        final Object hashUserId = this.getUserId();
        result = result * PRIME + (hashUserId == null ? 43 : hashUserId.hashCode());
        final Object hashStatus = this.getStatus();
        result = result * PRIME + (hashStatus == null ? 43 : hashStatus.hashCode());
        final Object hashAction = this.getAction();
        result = result * PRIME + (hashAction == null ? 43 : hashAction.hashCode());
        final Object hashModule = this.getModule();
        result = result * PRIME + (hashModule == null ? 43 : hashModule.hashCode());
        final Object hashUsername = this.getUsername();
        result = result * PRIME + (hashUsername == null ? 43 : hashUsername.hashCode());
        final Object hashStart = this.getStart();
        result = result * PRIME + (hashStart == null ? 43 : hashStart.hashCode());
        final Object hashEnd = this.getEnd();
        result = result * PRIME + (hashEnd == null ? 43 : hashEnd.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "LogQueryDTO(action=" + this.getAction() + ", module=" + this.getModule() + ", username=" + this.getUsername() + ", userId=" + this.getUserId() + ", status=" + this.getStatus() + ", start=" + this.getStart() + ", end=" + this.getEnd() + ", page=" + this.getPage() + ", size=" + this.getSize() + ")";
    }
}
