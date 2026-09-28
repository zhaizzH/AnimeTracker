package top.zhaizz.pojo.vo.subject;

/**
 * 热门榜条目
 */
public class HotSubjectVO {
    /** 条目ID */
    private Long id;                // 条目ID
    /** 日文/英文名 */
    private String name;            // 日文/英文名
    /** 中文名 */
    private String nameCn;          // 中文名
    /** 封面图URL */
    private String image;           // 封面图URL
    /** 收藏数 */
    private long collectionCount;   // 收藏数

    /** 创建字段均为默认值的空热门榜条目 */
    public HotSubjectVO() {
    }

    /**
     * 获取条目ID
     * @return 条目主键；未提供时为 {@code null}
     */
    public Long getId() {
        return this.id;
    }

    /**
     * 获取日文/英文名
     * @return 原始语言名称；未提供时为 {@code null}
     */
    public String getName() {
        return this.name;
    }

    /**
     * 获取中文名
     * @return 中文名称，可能为空；未提供时为 {@code null}
     */
    public String getNameCn() {
        return this.nameCn;
    }

    /**
     * 获取封面图URL
     * @return 封面图地址；未提供时为 {@code null}
     */
    public String getImage() {
        return this.image;
    }

    /**
     * 获取收藏数
     * @return 收藏人数，未设置时默认为 {@code 0}
     */
    public long getCollectionCount() {
        return this.collectionCount;
    }

    /**
     * 替换条目ID
     * @param id 条目主键，可为 {@code null}
     */
    public void setId(final Long id) {
        this.id = id;
    }

    /**
     * 替换日文/英文名
     * @param name 原始语言名称，可为 {@code null}
     */
    public void setName(final String name) {
        this.name = name;
    }

    /**
     * 替换中文名
     * @param nameCn 中文名称，可为 {@code null}
     */
    public void setNameCn(final String nameCn) {
        this.nameCn = nameCn;
    }

    /**
     * 替换封面图URL
     * @param image 封面图地址，可为 {@code null}
     */
    public void setImage(final String image) {
        this.image = image;
    }

    /**
     * 替换收藏数
     * @param collectionCount 收藏人数，取值为基本类型 long
     */
    public void setCollectionCount(final long collectionCount) {
        this.collectionCount = collectionCount;
    }

    /**
     * 判断与另一对象是否相等，比较本类全部字段
     * @param o 待比较的对象
     * @return 类型与全部字段均相等时为 {@code true}
     */
    @Override
    public boolean equals(final Object o) {
        if (o == this) return true;
        if (!(o instanceof HotSubjectVO)) return false;
        final HotSubjectVO other = (HotSubjectVO) o;
        if (!other.canEqual((Object) this)) return false;
        if (this.getCollectionCount() != other.getCollectionCount()) return false;
        final Object thisId = this.getId();
        final Object otherId = other.getId();
        if (thisId == null ? otherId != null : !thisId.equals(otherId)) return false;
        final Object thisName = this.getName();
        final Object otherName = other.getName();
        if (thisName == null ? otherName != null : !thisName.equals(otherName)) return false;
        final Object thisNameCn = this.getNameCn();
        final Object otherNameCn = other.getNameCn();
        if (thisNameCn == null ? otherNameCn != null : !thisNameCn.equals(otherNameCn)) return false;
        final Object thisImage = this.getImage();
        final Object otherImage = other.getImage();
        if (thisImage == null ? otherImage != null : !thisImage.equals(otherImage)) return false;
        return true;
    }

    /**
     * 判断另一对象是否可参与相等比较
     * @param other 待比较的对象
     * @return 与当前类型兼容时为 {@code true}
     */
    protected boolean canEqual(final Object other) {
        return other instanceof HotSubjectVO;
    }

    /**
     * 基于本类全部字段计算哈希值
     * @return 与 {@link #equals(Object)} 一致的哈希值
     */
    @Override
    public int hashCode() {
        final int PRIME = 59;
        int result = 1;
        final long hashCollectionCount = this.getCollectionCount();
        result = result * PRIME + (int) (hashCollectionCount >>> 32 ^ hashCollectionCount);
        final Object hashId = this.getId();
        result = result * PRIME + (hashId == null ? 43 : hashId.hashCode());
        final Object hashName = this.getName();
        result = result * PRIME + (hashName == null ? 43 : hashName.hashCode());
        final Object hashNameCn = this.getNameCn();
        result = result * PRIME + (hashNameCn == null ? 43 : hashNameCn.hashCode());
        final Object hashImage = this.getImage();
        result = result * PRIME + (hashImage == null ? 43 : hashImage.hashCode());
        return result;
    }

    /**
     * 返回包含本类全部字段的字符串表示
     * @return 字段名与取值的文本
     */
    @Override
    public String toString() {
        return "HotSubjectVO(id=" + this.getId() + ", name=" + this.getName() + ", nameCn=" + this.getNameCn() + ", image=" + this.getImage() + ", collectionCount=" + this.getCollectionCount() + ")";
    }
}
