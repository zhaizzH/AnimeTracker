package top.zhaizz.animetracker.subject.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.animetracker.common.result.Result;
import top.zhaizz.animetracker.common.dto.SubjectCreateDTO;
import top.zhaizz.animetracker.common.dto.SubjectUpdateDTO;
import top.zhaizz.animetracker.subject.service.SubjectService;
import top.zhaizz.animetracker.common.vo.SubjectDetailVO;

/**
 * 番剧管理控制器
 */
@RestController
@RequestMapping("/api/admin/subjects")
@RequiredArgsConstructor
@Validated
public class AdminController {

    private final SubjectService subjectService;

    /**
     * 创建新番剧
     */
    @PostMapping
    public Result<SubjectDetailVO> createSubject(@Valid @RequestBody SubjectCreateDTO request) {
        return Result.success(subjectService.createSubject(request));
    }

    /**
     * 更新指定番剧的信息
     */
    @PutMapping("/{id}")
    public Result<SubjectDetailVO> updateSubject(
            @PathVariable Long id,
            @Valid @RequestBody SubjectUpdateDTO request) {
        return Result.success(subjectService.updateSubject(id, request));
    }

    /**
     * 删除指定番剧
     */
    @DeleteMapping("/{id}")
    public Result<Void> deleteSubject(@PathVariable Long id) {
        subjectService.deleteSubject(id);
        return Result.success();
    }
}
