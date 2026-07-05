package top.zhaizz.animetracker.subject.controller;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.animetracker.common.ApiResponse;
import top.zhaizz.animetracker.common.PageResult;
import top.zhaizz.animetracker.subject.service.TagService;
import top.zhaizz.animetracker.subject.vo.SubjectListVO;
import top.zhaizz.animetracker.subject.vo.TagVO;

import java.util.List;

/**
 * 用户标签控制器
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
    public ApiResponse<List<TagVO>> listTags() {
        return ApiResponse.success(tagService.listTags());
    }

    /**
     * 获取标签下的番剧列表
     */
    @GetMapping("/{tag}/subjects")
    public ApiResponse<PageResult<SubjectListVO>> listSubjectsByTag(
            @PathVariable String tag,
            @RequestParam(defaultValue = "1") @Min(1) int page,
            @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size) {
        return ApiResponse.success(tagService.listSubjectsByTag(tag, page, size));
    }
}
