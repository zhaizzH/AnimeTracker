package top.zhaizz.common.result;

import java.util.List;

/**
 * 统一分页格式 {content, total, page, size}
 *
 * @param <T> 承载的数据类型
 */
@Getter
@Setter
public class PageResult<T> {

    /** 当前页记录列表 */
    private List<T> content;
    /** 符合条件的记录总数 */
    private long total;
    /** 分页页码 */
    private int page;
    /** 单页返回数量 */
    private int size;

    /** 创建空分页结果 */
    public PageResult() {}

    /**
     * 创建分页结果
     *
     * @param content 当前页记录，可为空；保存传入列表引用
     * @param total 符合查询条件的总记录数
     * @param page 调用方提供的页码，原样保存且不校验
     * @param size 调用方请求的每页记录数
     */
    public PageResult(List<T> content, long total, int page, int size) {
        this.content = content;
        this.total = total;
        this.page = page;
        this.size = size;
    }

    /**
     * 创建分页结果
     *
     * @param <T> 承载的数据类型
     * @param content 当前页记录，可为空；保存传入列表引用
     * @param total 符合查询条件的总记录数
     * @param page 调用方提供的页码，原样保存且不校验
     * @param size 调用方请求的每页记录数
     * @return 包含传入列表引用与分页元数据的新结果
     */
    public static <T> PageResult<T> of(List<T> content, long total, int page, int size) {
        return new PageResult<>(content, total, page, size);
    }

    /**
     * 获取当前页记录列表
     * @return 当前页记录；未分页查询命中数据时为 {@code null}
     */
    public List<T> getContent() {
        return this.content;
    }

    /**
     * 获取符合条件的记录总数
     * @return 忽略分页的匹配记录总数
     */
    public long getTotal() {
        return this.total;
    }

    /**
     * 获取分页页码
     * @return 调用方请求的页码，原样返回且不校验
     */
    public int getPage() {
        return this.page;
    }

    /**
     * 获取单页返回数量
     * @return 调用方请求的每页记录数
     */
    public int getSize() {
        return this.size;
    }

    /**
     * 替换当前页记录列表
     * @param content 新的当前页记录，可为 {@code null}；保存传入列表引用
     */
    public void setContent(final List<T> content) {
        this.content = content;
    }

    /**
     * 替换符合条件的记录总数
     * @param total 忽略分页的匹配记录总数
     */
    public void setTotal(final long total) {
        this.total = total;
    }

    /**
     * 替换分页页码
     * @param page 新的页码，不做校验
     */
    public void setPage(final int page) {
        this.page = page;
    }

    /**
     * 替换单页返回数量
     * @param size 新的每页记录数
     */
    public void setSize(final int size) {
        this.size = size;
    }
}
