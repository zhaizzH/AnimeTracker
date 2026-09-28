package top.zhaizz.pojo.dto.evidence;

import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;
import java.util.List;

/**
 * 按实体批量扩展至安全动画条目的请求
 * <p>
 * ids 始终是本地数据库主键；人物声优（ACTOR）同样使用 person.id，
 * 仅关系路径不同
 */
public class EvidenceEntityBatchRequestDTO {
    /**
     * 待解析实体的类型
     */
    @NotNull(message = "实体类型不能为空")
    private EvidenceEntityType entityType;
    /**
     * 待解析的本地主键，必填且最多 50 个，每个 ID 必须为正数
     */
    @NotEmpty(message = "实体 ID 不能为空")
    @Size(max = 50, message = "实体 ID 最多 50 个")
    private List<@NotNull(message = "实体 ID 不能为空") @Positive(message = "实体 ID 必须为正数") Long> ids;

    /** 创建待填充字段的空请求对象 */
    public EvidenceEntityBatchRequestDTO() {
    }

    /**
     * 创建携带全部字段的批量扩展请求
     * @param entityType 待解析实体的类型，不可为 {@code null}
     * @param ids 待解析的本地主键列表，可为 {@code null}，非空时元素非空且为正数、最多 50 个
     */
    public EvidenceEntityBatchRequestDTO(final EvidenceEntityType entityType, final List<@NotNull(message = "实体 ID 不能为空") @Positive(message = "实体 ID 必须为正数") Long> ids) {
        this.entityType = entityType;
        this.ids = ids;
    }

    /**
     * 获取待解析实体的类型
     * @return 待解析实体的类型；为 {@code null} 时校验失败
     */
    public EvidenceEntityType getEntityType() {
        return this.entityType;
    }

    /**
     * 获取待解析的本地主键列表
     * @return 待解析的本地数据库主键列表；未提供时为 {@code null}，必填、元素非空且为正数、最多 50 个
     */
    public List<@NotNull(message = "实体 ID 不能为空") @Positive(message = "实体 ID 必须为正数") Long> getIds() {
        return this.ids;
    }

    /**
     * 替换待解析实体的类型
     * @param entityType 待解析实体的类型；不可为 {@code null}
     */
    public void setEntityType(final EvidenceEntityType entityType) {
        this.entityType = entityType;
    }

    /**
     * 替换待解析的本地主键列表
     * @param ids 待解析的本地数据库主键列表；可为 {@code null}，非空时元素非空且为正数、最多 50 个
     */
    public void setIds(final List<@NotNull(message = "实体 ID 不能为空") @Positive(message = "实体 ID 必须为正数") Long> ids) {
        this.ids = ids;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof EvidenceEntityBatchRequestDTO)) return false;
        final EvidenceEntityBatchRequestDTO other = (EvidenceEntityBatchRequestDTO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisEntityType = this.getEntityType();
        final Object otherEntityType = other.getEntityType();
        if (thisEntityType == null ? otherEntityType != null : !thisEntityType.equals(otherEntityType)) return false;
        final Object thisIds = this.getIds();
        final Object otherIds = other.getIds();
        if (thisIds == null ? otherIds != null : !thisIds.equals(otherIds)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof EvidenceEntityBatchRequestDTO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashEntityType = this.getEntityType();
        result = result * PRIME + (hashEntityType == null ? 43 : hashEntityType.hashCode());
        final Object hashIds = this.getIds();
        result = result * PRIME + (hashIds == null ? 43 : hashIds.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "EvidenceEntityBatchRequestDTO(entityType=" + this.getEntityType() + ", ids=" + this.getIds() + ")";
    }
}
