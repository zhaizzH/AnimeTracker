package top.zhaizz.client.controller;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.client.service.TagService;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.common.result.Result;
import top.zhaizz.pojo.vo.subject.SubjectListVO;
import top.zhaizz.pojo.vo.tag.TagVO;

import java.util.List;

/**
 * 标签控制器
 */
@RestController
@RequestMapping("/api/client/tags")
@Validated
public class TagController {
    /**
     * 标签查询服务
     */
    private final TagService tagService;

    /**
     * 注入标签查询服务
     * @param tagService 提供标签列表与标签下条目分页的服务，由 Spring 容器提供
     */
    public TagController(final TagService tagService) {
        this.tagService = tagService;
    }

    /**
     * 获取标签列表
     * @return 统一成功响应，其数据为：按使用次数降序排列的标签
     */
    @GetMapping
    public Result<List<TagVO>> listTags() {
        return Result.success(tagService.listTags());
    }

    /**
     * 获取标签下的番剧列表
     * @param tag 标签名称
     * @param page 分页页码，从 1 开始
     * @param size 每页记录数
     * @return 统一成功响应，其数据为：匹配标签的条目分页
     */
    @GetMapping("/{tag}/subjects")
    public Result<PageResult<SubjectListVO>> listSubjectsByTag(
            @PathVariable String tag,
            @RequestParam(defaultValue = "1") @Min(1) int page,
            @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size) {
        return Result.success(tagService.listSubjectsByTag(tag, page, size));
    }
}
