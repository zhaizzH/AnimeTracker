package top.zhaizz.admin.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.admin.service.AdminSubjectService;
import top.zhaizz.common.constant.OperationLogConstants;
import top.zhaizz.common.log.OperationLog;
import top.zhaizz.common.result.Result;
import top.zhaizz.pojo.dto.subject.SubjectCreateDTO;
import top.zhaizz.pojo.dto.subject.SubjectUpdateDTO;
import top.zhaizz.pojo.vo.subject.SubjectDetailVO;

/**
 * 番剧管理控制器
 */
@RestController
@RequestMapping("/api/admin/subjects")
@RequiredArgsConstructor
@Validated
public class AdminSubjectController {

    private final AdminSubjectService adminSubjectService;

    /**
     * 创建新番剧，管理后台新建表单提交时触发
     */
    @OperationLog(action = OperationLogConstants.ACTION_SUBJECT_CREATE, module = OperationLogConstants.MODULE_SUBJECT)
    @PostMapping
    public Result<SubjectDetailVO> createSubject(@Valid @RequestBody SubjectCreateDTO request) {
        return Result.success(adminSubjectService.createSubject(request));
    }

    /**
     * 更新指定番剧的信息，管理后台编辑表单提交时触发
     */
    @OperationLog(action = OperationLogConstants.ACTION_SUBJECT_UPDATE, module = OperationLogConstants.MODULE_SUBJECT)
    @PostMapping("/{id}/update")
    public Result<SubjectDetailVO> updateSubject(
            @PathVariable Long id,
            @Valid @RequestBody SubjectUpdateDTO request) {
        return Result.success(adminSubjectService.updateSubject(id, request));
    }

    /**
     * 删除指定番剧，管理后台删除操作确认时触发
     */
    @OperationLog(action = OperationLogConstants.ACTION_SUBJECT_DELETE, module = OperationLogConstants.MODULE_SUBJECT)
    @PostMapping("/{id}/remove")
    public Result<Void> deleteSubject(@PathVariable Long id) {
        adminSubjectService.deleteSubject(id);
        return Result.success();
    }
}
