package top.zhaizz.admin.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.admin.service.AdminSubjectService;
import top.zhaizz.common.result.Result;
import top.zhaizz.pojo.dto.SubjectCreateDTO;
import top.zhaizz.pojo.dto.SubjectUpdateDTO;
import top.zhaizz.pojo.vo.SubjectDetailVO;

/**
 * 番剧管理控制器
 */
@RestController
@RequestMapping("/api/admin/subjects")
@RequiredArgsConstructor
@Validated
public class AdminController {

    private final AdminSubjectService adminSubjectService;

    /**
     * 创建新番剧
     */
    @PostMapping
    public Result<SubjectDetailVO> createSubject(@Valid @RequestBody SubjectCreateDTO request) {
        return Result.success(adminSubjectService.createSubject(request));
    }

    /**
     * 更新指定番剧的信息
     */
    @PutMapping("/{id}")
    public Result<SubjectDetailVO> updateSubject(
            @PathVariable Long id,
            @Valid @RequestBody SubjectUpdateDTO request) {
        return Result.success(adminSubjectService.updateSubject(id, request));
    }

    /**
     * 删除指定番剧
     */
    @DeleteMapping("/{id}")
    public Result<Void> deleteSubject(@PathVariable Long id) {
        adminSubjectService.deleteSubject(id);
        return Result.success();
    }
}
