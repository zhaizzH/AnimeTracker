package top.zhaizz.admin.constant;

import java.util.Set;

/**
 * 番剧导入模式常量，与 Python agent 侧 import_runner 保持一致
 */
public final class ImportConstants {
    /**
     * 禁止实例化仅提供静态操作的工具类
     */
    private ImportConstants() {}

    /** 完整导入模式标识 */
    public static final String MODE_FULL = "full";
    /** 按季度导入模式标识 */
    public static final String MODE_SEASON = "season";
    /** 近期条目导入模式标识 */
    public static final String MODE_RECENT = "recent";
    /** 按起始时间导入模式标识 */
    public static final String MODE_SINCE = "since";

    /** 允许使用的导入模式集合 */
    public static final Set<String> MODES = Set.of(MODE_FULL, MODE_SEASON, MODE_RECENT, MODE_SINCE);
}
