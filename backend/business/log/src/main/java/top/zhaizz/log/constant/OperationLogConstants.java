package top.zhaizz.log.constant;

/**
 * 操作日志注解常量（module/action 与管理端日志筛选一致，改前端筛选需同步）。
 */
public final class OperationLogConstants {
    /** 禁止实例化操作日志协议常量。 */
    private OperationLogConstants() {}

    /** 日志模块筛选编码：{@code AUTH}，与前端筛选保持一致。 */
    public static final String MODULE_AUTH = "AUTH";
    /** 日志模块筛选编码：{@code SUBJECT}，与前端筛选保持一致。 */
    public static final String MODULE_SUBJECT = "SUBJECT";
    /** 日志模块筛选编码：{@code ADMIN}，与前端筛选保持一致。 */
    public static final String MODULE_ADMIN = "ADMIN";
    /** 日志模块筛选编码：{@code IMPORT}，与前端筛选保持一致。 */
    public static final String MODULE_IMPORT = "IMPORT";
    /** 日志模块筛选编码：{@code AGENT}，与前端筛选保持一致。 */
    public static final String MODULE_AGENT = "AGENT";
    /** 日志模块筛选编码：{@code USER}，与前端筛选保持一致。 */
    public static final String MODULE_USER = "USER";
    /** 日志模块筛选编码：{@code FILE}，与前端筛选保持一致。 */
    public static final String MODULE_FILE = "FILE";

    /** 操作动作筛选编码：{@code REGISTER}，与前端筛选保持一致。 */
    public static final String ACTION_REGISTER = "REGISTER";
    /** 操作动作筛选编码：{@code VERIFY_EMAIL}，与前端筛选保持一致。 */
    public static final String ACTION_VERIFY_EMAIL = "VERIFY_EMAIL";
    /** 操作动作筛选编码：{@code LOGIN}，与前端筛选保持一致。 */
    public static final String ACTION_LOGIN = "LOGIN";
    /** 操作动作筛选编码：{@code RESET_PASSWORD}，与前端筛选保持一致。 */
    public static final String ACTION_RESET_PASSWORD = "RESET_PASSWORD";
    /** 操作动作筛选编码：{@code LOGOUT}，与前端筛选保持一致。 */
    public static final String ACTION_LOGOUT = "LOGOUT";
    /** 操作动作筛选编码：{@code SUBJECT_CREATE}，与前端筛选保持一致。 */
    public static final String ACTION_SUBJECT_CREATE = "SUBJECT_CREATE";
    /** 操作动作筛选编码：{@code SUBJECT_UPDATE}，与前端筛选保持一致。 */
    public static final String ACTION_SUBJECT_UPDATE = "SUBJECT_UPDATE";
    /** 操作动作筛选编码：{@code SUBJECT_DELETE}，与前端筛选保持一致。 */
    public static final String ACTION_SUBJECT_DELETE = "SUBJECT_DELETE";
    /** 操作动作筛选编码：{@code ROLE_CHANGE}，与前端筛选保持一致。 */
    public static final String ACTION_ROLE_CHANGE = "ROLE_CHANGE";
    /** 操作动作筛选编码：{@code IMPORT_RUN}，与前端筛选保持一致。 */
    public static final String ACTION_IMPORT_RUN = "IMPORT_RUN";
    /** 操作动作筛选编码：{@code PROMPT_UPDATE}，与前端筛选保持一致。 */
    public static final String ACTION_PROMPT_UPDATE = "PROMPT_UPDATE";
    /** 操作动作筛选编码：{@code PROMPT_RESET}，与前端筛选保持一致。 */
    public static final String ACTION_PROMPT_RESET = "PROMPT_RESET";
    /** 操作动作筛选编码：{@code CONFIG_UPDATE}，与前端筛选保持一致。 */
    public static final String ACTION_CONFIG_UPDATE = "CONFIG_UPDATE";
    /** 操作动作筛选编码：{@code PASSWORD_CHANGE}，与前端筛选保持一致。 */
    public static final String ACTION_PASSWORD_CHANGE = "PASSWORD_CHANGE";
    /** 操作动作筛选编码：{@code FILE_UPLOAD}，与前端筛选保持一致。 */
    public static final String ACTION_FILE_UPLOAD = "FILE_UPLOAD";
}
