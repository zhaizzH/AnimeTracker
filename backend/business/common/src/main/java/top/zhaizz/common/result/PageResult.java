package top.zhaizz.common.result;

import lombok.Getter;
import lombok.Setter;

import java.util.List;

/**
 * 统一分页格式 {content, total, page, size}。
 *
 * @param <T> 承载的数据类型
 */
@Getter
@Setter
public class PageResult<T> {

    /** 当前页记录列表。 */
    private List<T> content;
    /** 符合条件的记录总数。 */
    private long total;
    /** 分页页码。 */
    private int page;
    /** 单页返回数量。 */
    private int size;

    /** 创建空分页结果。 */
    public PageResult() {}

    /**
     * 创建分页结果。
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
     * 创建分页结果。
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
}
