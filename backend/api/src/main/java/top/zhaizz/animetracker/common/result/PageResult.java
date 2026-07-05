package top.zhaizz.animetracker.common;

import lombok.Getter;
import lombok.Setter;

import java.util.List;

/**
 * 统一分页格式 {content, total, page, size}
 */
@Getter
@Setter
public class PageResult<T> {

    private List<T> content;
    private long total;
    private int page;
    private int size;

    public PageResult() {}

    public PageResult(List<T> content, long total, int page, int size) {
        this.content = content;
        this.total = total;
        this.page = page;
        this.size = size;
    }

    /**
     * 创建分页结果（基于 MyBatis-Plus Page）
     */
    public static <T> PageResult<T> of(List<T> content, long total, int page, int size) {
        return new PageResult<>(content, total, page, size);
    }

    /**
     * 创建空分页结果
     */
    public static <T> PageResult<T> empty(int page, int size) {
        return new PageResult<>(List.of(), 0, page, size);
    }
}
