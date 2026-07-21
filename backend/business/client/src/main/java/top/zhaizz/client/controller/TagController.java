package top.zhaizz.client.controller;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.client.service.TagService;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.common.result.Result;
import top.zhaizz.pojo.vo.SubjectListVO;
import top.zhaizz.pojo.vo.TagVO;

import java.util.List;

/**
 * 标签控制器
 */
@RestController
@RequestMapping("/api/user/tags")
@RequiredArgsConstructor
@Validated
public class TagController {

    private final TagService tagService;

    /**
     * 获取标签列表
     */
    @GetMapping
    public Result<List<TagVO>> listTags() {
        return Result.success(tagService.listTags());
    }

    /**
     * 获取标签下的番剧列表
     */
    @GetMapping("/{tag}/subjects")
    public Result<PageResult<SubjectListVO>> listSubjectsByTag(
            @PathVariable String tag,
            @RequestParam(defaultValue = "1") @Min(1) int page,
            @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size) {
        return Result.success(tagService.listSubjectsByTag(tag, page, size));
    }
}
