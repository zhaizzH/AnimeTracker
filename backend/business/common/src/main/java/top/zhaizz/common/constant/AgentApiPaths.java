package top.zhaizz.common.constant;

/**
 * 上游 Python agent 服务路由（单一来源）。
 * 漂移不在此检测——Python 侧改路由需与这里同步，否则运行时 404。
 */
public final class AgentApiPaths {
    private AgentApiPaths() {}

    public static final String ADMIN_PROMPTS = "/api/admin/agent/prompts";
    public static final String ADMIN_CONFIG = "/api/admin/agent/config";
    public static final String ADMIN_CHAT_STREAM = "/api/admin/agent/chat/stream";
    public static final String ADMIN_CHAT_SESSIONS = "/api/admin/agent/chat/sessions";
    public static final String ADMIN_IMPORT_RUN = "/api/admin/agent/import/run";

    public static final String CLIENT_HEALTH = "/api/client/agent/health";
    public static final String CLIENT_STREAM = "/api/client/agent/stream";
    public static final String CLIENT_SESSIONS = "/api/client/agent/sessions";
}
