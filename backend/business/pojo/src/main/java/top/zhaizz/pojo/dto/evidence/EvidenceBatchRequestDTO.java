package top.zhaizz.pojo.dto.evidence;

import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.List;

/**
 * 批量证据回查请求
 */
public class EvidenceBatchRequestDTO {
    /**
     * 待回查条目 ID，必填且最多 50 个，元素不得为空
     */
    @NotEmpty(message = "条目 ID 不能为空")
    @Size(max = 50, message = "条目 ID 最多 50 个")
    private List<@NotNull(message = "条目 ID 不能为空") Long> subjectIds;

    /** 创建待填充条目 ID 的空请求对象 */
    public EvidenceBatchRequestDTO() {
    }

    /**
     * 获取待回查条目 ID 列表
     * @return 待回查条目 ID 列表；未提供时为 {@code null}，必填、元素非空且最多 50 个
     */
    public List<@NotNull(message = "条目 ID 不能为空") Long> getSubjectIds() {
        return this.subjectIds;
    }

    /**
     * 替换待回查条目 ID 列表
     * @param subjectIds 待回查条目 ID 列表；可为 {@code null}，非空时元素不得为空且最多 50 个
     */
    public void setSubjectIds(final List<@NotNull(message = "条目 ID 不能为空") Long> subjectIds) {
        this.subjectIds = subjectIds;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof EvidenceBatchRequestDTO)) return false;
        final EvidenceBatchRequestDTO other = (EvidenceBatchRequestDTO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisSubjectIds = this.getSubjectIds();
        final Object otherSubjectIds = other.getSubjectIds();
        if (thisSubjectIds == null ? otherSubjectIds != null : !thisSubjectIds.equals(otherSubjectIds)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof EvidenceBatchRequestDTO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashSubjectIds = this.getSubjectIds();
        result = result * PRIME + (hashSubjectIds == null ? 43 : hashSubjectIds.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "EvidenceBatchRequestDTO(subjectIds=" + this.getSubjectIds() + ")";
    }
}
