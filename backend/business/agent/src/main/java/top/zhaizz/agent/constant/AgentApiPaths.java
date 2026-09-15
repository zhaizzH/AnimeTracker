package top.zhaizz.agent.constant;

/** Python Agent HTTP 路由常量 */
public final class AgentApiPaths {
    /**
     * 禁止实例化仅包含 Agent 路由常量的工具类
     */
    private AgentApiPaths() {
    }

    /** 管理端提示词列表 */
    public static final String ADMIN_PROMPTS = "/api/admin/agent/prompts";
    /** 管理端模型配置 */
    public static final String ADMIN_CONFIG = "/api/admin/agent/config";
    /** 管理端流式对话 */
    public static final String ADMIN_CHAT_STREAM = "/api/admin/agent/chat/stream";
    /** 管理端会话 */
    public static final String ADMIN_CHAT_SESSIONS = "/api/admin/agent/chat/sessions";
    /** 管理端导入任务 */
    public static final String ADMIN_IMPORT_RUN = "/api/admin/agent/import/run";
    /** 客户端健康检查 */
    public static final String CLIENT_HEALTH = "/api/client/agent/health";
    /** 客户端流式对话 */
    public static final String CLIENT_STREAM = "/api/client/agent/stream";
    /** 客户端会话 */
    public static final String CLIENT_SESSIONS = "/api/client/agent/sessions";
}
