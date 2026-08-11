package top.zhaizz.admin.constant;

import java.util.Set;

/**
 * 番剧导入模式常量，与 Python agent 侧 import_runner 保持一致
 */
public final class ImportConstants {
    private ImportConstants() {}

    public static final String MODE_FULL = "full";
    public static final String MODE_SEASON = "season";
    public static final String MODE_RECENT = "recent";
    public static final String MODE_SINCE = "since";

    public static final Set<String> MODES = Set.of(MODE_FULL, MODE_SEASON, MODE_RECENT, MODE_SINCE);
}
