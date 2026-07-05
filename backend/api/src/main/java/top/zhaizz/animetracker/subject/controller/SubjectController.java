package top.zhaizz.animetracker.subject.controller;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Pattern;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.animetracker.common.ApiResponse;
import top.zhaizz.animetracker.common.BizException;
import top.zhaizz.animetracker.common.ErrorType;
import top.zhaizz.animetracker.common.PageResult;
import top.zhaizz.animetracker.subject.service.EpisodeService;
import top.zhaizz.animetracker.subject.service.SubjectService;
import top.zhaizz.animetracker.subject.vo.EpisodeVO;
import top.zhaizz.animetracker.subject.vo.SubjectDetailVO;
import top.zhaizz.animetracker.subject.vo.SubjectListVO;

import java.util.List;

@RestController
@RequestMapping("/api/user/subjects")
@RequiredArgsConstructor
@Validated
public class SubjectController {

    private final SubjectService subjectService;
    private final EpisodeService episodeService;

    @GetMapping
    public ApiResponse<PageResult<SubjectListVO>> listSubjects(
            @RequestParam(defaultValue = "1") @Min(1) int page,
            @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size,
            @RequestParam(defaultValue = "score") String sort,
            @RequestParam(defaultValue = "desc") String order) {
        return ApiResponse.success(subjectService.listSubjects(page, size, sort, order));
    }

    @GetMapping("/search")
    public ApiResponse<PageResult<SubjectListVO>> searchSubjects(
            @RequestParam String q,
            @RequestParam(defaultValue = "1") @Min(1) int page,
            @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size) {
        if (q == null || q.trim().isEmpty()) {
            throw new BizException(ErrorType.BAD_REQUEST, "搜索关键词不能为空");
        }
        return ApiResponse.success(subjectService.searchSubjects(q.trim(), page, size));
    }

    @GetMapping("/season")
    public ApiResponse<PageResult<SubjectListVO>> listBySeason(
            @RequestParam @Min(1970) @Max(2100) int year,
            @RequestParam @Pattern(regexp = "spring|summer|autumn|winter",
                    message = "季度仅允许: spring/summer/autumn/winter") String quarter,
            @RequestParam(defaultValue = "1") @Min(1) int page,
            @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size) {
        return ApiResponse.success(subjectService.listBySeason(year, quarter, page, size));
    }

    @GetMapping("/{id}")
    public ApiResponse<SubjectDetailVO> getSubjectDetail(@PathVariable Long id) {
        return ApiResponse.success(subjectService.getSubjectDetail(id));
    }

    @GetMapping("/{id}/episodes")
    public ApiResponse<List<EpisodeVO>> getEpisodes(@PathVariable Long id) {
        return ApiResponse.success(episodeService.getEpisodesBySubjectId(id));
    }
}
