package top.zhaizz.client.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.client.service.ClientSubjectService;
import top.zhaizz.client.service.EpisodeService;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.common.result.Result;
import top.zhaizz.common.util.SecurityUtil;
import top.zhaizz.pojo.dto.subject.ScheduleQueryDTO;
import top.zhaizz.pojo.dto.subject.SeasonQueryDTO;
import top.zhaizz.pojo.dto.subject.SubjectBatchRequestDTO;
import top.zhaizz.pojo.dto.subject.SubjectListQueryDTO;
import top.zhaizz.pojo.dto.subject.SubjectSearchQueryDTO;
import top.zhaizz.pojo.dto.subject.LexicalSearchRequestDTO;
import top.zhaizz.pojo.vo.subject.EpisodeVO;
import top.zhaizz.pojo.vo.subject.SubjectDetailVO;
import top.zhaizz.pojo.vo.subject.SubjectBatchResultVO;
import top.zhaizz.pojo.vo.subject.SubjectListVO;
import top.zhaizz.pojo.vo.subject.LexicalSearchResultVO;

import java.util.List;

/**
 * 番剧控制器
 */
@RestController
@RequestMapping("/api/client/subjects")
@RequiredArgsConstructor
public class SubjectController {

    private final ClientSubjectService clientSubjectService;
    private final EpisodeService episodeService;

    /**
     * 获取番剧列表
     */
    @GetMapping
    public Result<PageResult<SubjectListVO>> listSubjects(@Valid SubjectListQueryDTO request) {
        return Result.success(clientSubjectService.listSubjects(request));
    }

    /**
     * 搜索番剧
     */
    @GetMapping("/search")
    public Result<PageResult<SubjectListVO>> searchSubjects(@Valid SubjectSearchQueryDTO request) {
        return Result.success(clientSubjectService.searchSubjects(request));
    }

    /**
     * 面向 Agent 的受控词法召回；请求只包含结构化字段和普通搜索词，
     * 不接受 MATCH/SQL 表达式。详细证据必须继续调用 evidence/batch。
     */
    @PostMapping("/lexical-search")
    public Result<LexicalSearchResultVO> lexicalSearch(
            @Valid @RequestBody LexicalSearchRequestDTO request) {
        return Result.success(clientSubjectService.lexicalSearch(request));
    }

    /**
     * 按季度筛选用户番剧
     */
    @GetMapping("/season")
    public Result<PageResult<SubjectListVO>> listBySeason(@Valid SeasonQueryDTO request) {
        return Result.success(clientSubjectService.listBySeason(request));
    }

    /**
     * 每周追番列表
     */
    @GetMapping("/schedule")
    public Result<PageResult<SubjectListVO>> listSchedule(@Valid ScheduleQueryDTO request) {
        return Result.success(clientSubjectService.listSchedule(request));
    }

    /**
     * 批量回查候选条目的权威可见状态。
     */
    @PostMapping("/batch")
    public Result<SubjectBatchResultVO> batchSubjects(@Valid @RequestBody SubjectBatchRequestDTO request) {
        return Result.success(clientSubjectService.batch(
                request.getSubjectIds(), request.isExcludeCollected(), SecurityUtil.getCurrentUserIdQuietly()));
    }

    /**
     * 获取番剧详情
     */
    @GetMapping("/{id}")
    public Result<SubjectDetailVO> getSubjectDetail(@PathVariable Long id) {
        return Result.success(clientSubjectService.getSubjectDetail(id));
    }

    /**
     * 获取库中实际存在的番剧年份列表
     */
    @GetMapping("/years")
    public Result<List<Integer>> listYears() {
        return Result.success(clientSubjectService.listYears());
    }

    /**
     * 获取番剧剧集列表
     */
    @GetMapping("/{id}/episodes")
    public Result<List<EpisodeVO>> getEpisodes(@PathVariable Long id) {
        return Result.success(episodeService.getEpisodesBySubjectId(id));
    }
}
