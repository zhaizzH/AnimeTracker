package top.zhaizz.pojo.vo.collection;

import com.fasterxml.jackson.annotation.JsonInclude;

/**
 * 想看加入结果（幂等）：state=ADDED 表示新增成功；state=ALREADY_COLLECTED 表示已存在收藏，不覆盖
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public class WishlistAddResultVO {

    /** 加入状态：ADDED 为新增，ALREADY_COLLECTED 为已有收藏 */
    private String state;
    /** ALREADY_COLLECTED 时返回已存在收藏类型（1-5） */
    private Integer existingType;

    /** 创建字段均为默认值的空结果对象 */
    public WishlistAddResultVO() {
    }

    /**
     * 创建携带全部字段的加入结果
     * @param state 加入状态，可为 {@code null}
     * @param existingType 已存在收藏类型（1-5），可为 {@code null}
     */
    public WishlistAddResultVO(final String state, final Integer existingType) {
        this.state = state;
        this.existingType = existingType;
    }

    /**
     * 创建表示收藏已新增的结果对象
     *
     * @return 状态为 ADDED 且未设置已有收藏类型的结果
     */
    public static WishlistAddResultVO added() {
        return WishlistAddResultVO.builder().state("ADDED").build();
    }

    /**
     * 创建表示收藏已存在并携带原收藏类型的结果对象
     *
     * @param existingType 已有收藏类型，原样保存
     * @return 状态为 ALREADY_COLLECTED 并携带原收藏类型的结果
     */
    public static WishlistAddResultVO alreadyCollected(Integer existingType) {
        return WishlistAddResultVO.builder()
                .state("ALREADY_COLLECTED")
                .existingType(existingType)
                .build();
    }

    /**
     * 创建构建器，用于链式组装加入结果
     * @return 空的加入结果构建器
     */
    public static WishlistAddResultVOBuilder builder() {
        return new WishlistAddResultVOBuilder();
    }

    /**
     * 获取加入状态
     * @return ADDED 或 ALREADY_COLLECTED；未提供时为 {@code null}
     */
    public String getState() {
        return this.state;
    }

    /**
     * 获取已存在收藏类型
     * @return 已存在收藏的收藏类型（1-5）；非 ALREADY_COLLECTED 时为 {@code null}，序列化时因 NON_NULL 不输出
     */
    public Integer getExistingType() {
        return this.existingType;
    }

    /**
     * 替换加入状态
     * @param state 加入状态，可为 {@code null}
     */
    public void setState(final String state) {
        this.state = state;
    }

    /**
     * 替换已存在收藏类型
     * @param existingType 已存在收藏的收藏类型（1-5），可为 {@code null}
     */
    public void setExistingType(final Integer existingType) {
        this.existingType = existingType;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof WishlistAddResultVO)) return false;
        final WishlistAddResultVO other = (WishlistAddResultVO) o;
        if (!other.canEqual((Object) this)) return false;
        final Object thisExistingType = this.getExistingType();
        final Object otherExistingType = other.getExistingType();
        if (thisExistingType == null ? otherExistingType != null : !thisExistingType.equals(otherExistingType)) return false;
        final Object thisState = this.getState();
        final Object otherState = other.getState();
        if (thisState == null ? otherState != null : !thisState.equals(otherState)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof WishlistAddResultVO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final Object hashExistingType = this.getExistingType();
        result = result * PRIME + (hashExistingType == null ? 43 : hashExistingType.hashCode());
        final Object hashState = this.getState();
        result = result * PRIME + (hashState == null ? 43 : hashState.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "WishlistAddResultVO(state=" + this.getState() + ", existingType=" + this.getExistingType() + ")";
    }

    /**
     * {@code WishlistAddResultVO} 的链式构建器
     *
     * <p>全部字段均无默认值，未显式设置的字段保持 {@code null}
     */
    public static class WishlistAddResultVOBuilder {
        /** 加入状态 */
        private String state;
        /** ALREADY_COLLECTED 时返回已存在收藏类型（1-5） */
        private Integer existingType;

        /**
         * 创建空构建器，全部字段保持未设置状态
         */
        WishlistAddResultVOBuilder() {
        }

        /**
         * 设置加入状态，覆盖此前取值
         * @param state 加入状态，可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public WishlistAddResultVO.WishlistAddResultVOBuilder state(final String state) {
            this.state = state;
            return this;
        }

        /**
         * 设置已存在收藏类型，覆盖此前取值
         * @param existingType 已存在收藏的收藏类型（1-5），可为 {@code null}
         * @return {@code this}，用于链式调用
         */
        public WishlistAddResultVO.WishlistAddResultVOBuilder existingType(final Integer existingType) {
            this.existingType = existingType;
            return this;
        }

        /**
         * 构建加入结果
         * @return 携带当前构建器取值的加入结果
         */
        public WishlistAddResultVO build() {
            return new WishlistAddResultVO(this.state, this.existingType);
        }

        /**
         * 返回包含构建器当前取值的字符串表示
         * @return 字段名与取值的文本
         */
        @Override
        public String toString() {
            return "WishlistAddResultVO.WishlistAddResultVOBuilder(state=" + this.state + ", existingType=" + this.existingType + ")";
        }
    }
}
