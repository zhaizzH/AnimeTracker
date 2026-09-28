package top.zhaizz.pojo.dto.imprt;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

/**
 * 番剧导入触发参数（包名 imprt：import 为 Java 关键字不可作包名）
 */
public class ImportRunDTO {
    /**
     * 导入模式: full / season / recent / since
     */
    @NotBlank(message = "导入模式不能为空")
    @Pattern(regexp = "full|season|recent|since", message = "导入模式仅允许: full/season/recent/since")
    private String mode; // 导入模式: full / season / recent / since
    /**
     * 季度标识（season 模式必填），如 "2026-summer"
     */
    private String key; // 季度标识（season 模式必填），如 "2026-summer"
    /**
     * 起始日期（since 模式必填），如 "2026-01-01"
     */
    private String since; // 起始日期（since 模式必填），如 "2026-01-01"
    /**
     * 并发线程数，为空使用 Python 侧默认值
     */
    private Integer workers; // 并发线程数，为空使用 Python 侧默认值

    /** 创建待填充导入参数的空请求对象 */
    public ImportRunDTO() {
    }

    /**
     * 获取导入模式
     * @return 导入模式，取值限定 full / season / recent / since；未提供时为 {@code null}，必填
     */
    public String getMode() {
        return this.mode;
    }

    /**
     * 获取季度标识
     * @return 形如 {@code 2026-summer} 的季度标识；未提供时为 {@code null}，仅 season 模式下必填
     */
    public String getKey() {
        return this.key;
    }

    /**
     * 获取起始日期
     * @return 形如 {@code 2026-01-01} 的起始日期文本；未提供时为 {@code null}，仅 since 模式下必填
     */
    public String getSince() {
        return this.since;
    }

    /**
     * 获取并发线程数
     * @return 请求的并发线程数；为 {@code null} 时由 Python 侧使用默认值
     */
    public Integer getWorkers() {
        return this.workers;
    }

    /**
     * 替换导入模式
     * @param mode 导入模式，取值限定 full / season / recent / since；可为 {@code null}，但校验要求其非空
     */
    public void setMode(final String mode) {
        this.mode = mode;
    }

    /**
     * 替换季度标识
     * @param key 形如 {@code 2026-summer} 的季度标识；可为 {@code null}，仅 season 模式下必填
     */
    public void setKey(final String key) {
        this.key = key;
    }

    /**
     * 替换起始日期
     * @param since 形如 {@code 2026-01-01} 的起始日期文本；可为 {@code null}，仅 since 模式下必填
     */
    public void setSince(final String since) {
        this.since = since;
    }

    /**
     * 替换并发线程数
     * @param workers 请求的并发线程数；可为 {@code null} 表示使用 Python 侧默认值
     */
    public void setWorkers(final Integer workers) {
        this.workers = workers;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof ImportRunDTO)) return false;
        final ImportRunDTO other = (ImportRunDTO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisWorkers = this.getWorkers();
        final Object otherWorkers = other.getWorkers();
        if (thisWorkers == null ? otherWorkers != null : !thisWorkers.equals(otherWorkers)) return false;
        final Object thisMode = this.getMode();
        final Object otherMode = other.getMode();
        if (thisMode == null ? otherMode != null : !thisMode.equals(otherMode)) return false;
        final Object thisKey = this.getKey();
        final Object otherKey = other.getKey();
        if (thisKey == null ? otherKey != null : !thisKey.equals(otherKey)) return false;
        final Object thisSince = this.getSince();
        final Object otherSince = other.getSince();
        if (thisSince == null ? otherSince != null : !thisSince.equals(otherSince)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof ImportRunDTO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashWorkers = this.getWorkers();
        result = result * PRIME + (hashWorkers == null ? 43 : hashWorkers.hashCode());
        final Object hashMode = this.getMode();
        result = result * PRIME + (hashMode == null ? 43 : hashMode.hashCode());
        final Object hashKey = this.getKey();
        result = result * PRIME + (hashKey == null ? 43 : hashKey.hashCode());
        final Object hashSince = this.getSince();
        result = result * PRIME + (hashSince == null ? 43 : hashSince.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "ImportRunDTO(mode=" + this.getMode() + ", key=" + this.getKey() + ", since=" + this.getSince() + ", workers=" + this.getWorkers() + ")";
    }
}
