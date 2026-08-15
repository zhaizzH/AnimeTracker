package top.zhaizz.common.constant;

/**
 * 操作日志注解常量（module/action 与管理端日志筛选一致，改前端筛选需同步）
 */
public final class OperationLogConstants {
    private OperationLogConstants() {}

    public static final String MODULE_AUTH = "AUTH";
    public static final String MODULE_SUBJECT = "SUBJECT";
    public static final String MODULE_ADMIN = "ADMIN";
    public static final String MODULE_IMPORT = "IMPORT";
    public static final String MODULE_AGENT = "AGENT";
    public static final String MODULE_USER = "USER";
    public static final String MODULE_FILE = "FILE";

    public static final String ACTION_REGISTER = "REGISTER";
    public static final String ACTION_VERIFY_EMAIL = "VERIFY_EMAIL";
    public static final String ACTION_LOGIN = "LOGIN";
    public static final String ACTION_RESET_PASSWORD = "RESET_PASSWORD";
    public static final String ACTION_LOGOUT = "LOGOUT";
    public static final String ACTION_SUBJECT_CREATE = "SUBJECT_CREATE";
    public static final String ACTION_SUBJECT_UPDATE = "SUBJECT_UPDATE";
    public static final String ACTION_SUBJECT_DELETE = "SUBJECT_DELETE";
    public static final String ACTION_ROLE_CHANGE = "ROLE_CHANGE";
    public static final String ACTION_IMPORT_RUN = "IMPORT_RUN";
    public static final String ACTION_PROMPT_UPDATE = "PROMPT_UPDATE";
    public static final String ACTION_PROMPT_RESET = "PROMPT_RESET";
    public static final String ACTION_CONFIG_UPDATE = "CONFIG_UPDATE";
    public static final String ACTION_PASSWORD_CHANGE = "PASSWORD_CHANGE";
    public static final String ACTION_FILE_UPLOAD = "FILE_UPLOAD";
}
