package top.zhaizz.animetracker.subject.controller;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Pattern;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.animetracker.common.result.Result;
import top.zhaizz.animetracker.common.exception.BizException;
import top.zhaizz.animetracker.common.ErrorType;
import top.zhaizz.animetracker.common.result.PageResult;
import top.zhaizz.animetracker.subject.service.EpisodeService;
import top.zhaizz.animetracker.subject.service.SubjectService;
import top.zhaizz.animetracker.common.vo.EpisodeVO;
import top.zhaizz.animetracker.common.vo.SubjectDetailVO;
import top.zhaizz.animetracker.common.vo.SubjectListVO;

import java.util.List;

/**
 * 番剧控制器
 */
@RestController
@RequestMapping("/api/user/subjects")
@RequiredArgsConstructor
@Validated
public class SubjectController {

    private final SubjectService subjectService;
    private final EpisodeService episodeService;

    /**
     * 获取用户番剧列表
     */
    @GetMapping
    public Result<PageResult<SubjectListVO>> listSubjects(
            @RequestParam(defaultValue = "1") @Min(1) int page,
            @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size,
            @RequestParam(defaultValue = "score") String sort,
            @RequestParam(defaultValue = "desc") String order) {
        return Result.success(subjectService.listSubjects(page, size, sort, order));
    }

    /**
     * 用户搜索番剧
     */
    @GetMapping("/search")
    public Result<PageResult<SubjectListVO>> searchSubjects(
            @RequestParam String q,
            @RequestParam(defaultValue = "1") @Min(1) int page,
            @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size) {
        if (q == null || q.trim().isEmpty()) {
            throw new BizException(ErrorType.BAD_REQUEST, "搜索关键词不能为空");
        }
        return Result.success(subjectService.searchSubjects(q.trim(), page, size));
    }

    /**
     * 按季度筛选用户番剧
     */
    @GetMapping("/season")
    public Result<PageResult<SubjectListVO>> listBySeason(
            @RequestParam @Min(1970) @Max(2100) int year,
            @RequestParam @Pattern(regexp = "spring|summer|autumn|winter",
                    message = "季度仅允许: spring/summer/autumn/winter") String quarter,
            @RequestParam(defaultValue = "1") @Min(1) int page,
            @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size) {
        return Result.success(subjectService.listBySeason(year, quarter, page, size));
    }

    /**
     * 获取用户番剧详情
     */
    @GetMapping("/{id}")
    public Result<SubjectDetailVO> getSubjectDetail(@PathVariable Long id) {
        return Result.success(subjectService.getSubjectDetail(id));
    }

    /**
     * 获取用户番剧剧剧集列表
     */
    @GetMapping("/{id}/episodes")
    public Result<List<EpisodeVO>> getEpisodes(@PathVariable Long id) {
        return Result.success(episodeService.getEpisodesBySubjectId(id));
    }
}
