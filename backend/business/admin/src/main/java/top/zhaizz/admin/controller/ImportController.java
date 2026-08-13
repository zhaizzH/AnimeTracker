package top.zhaizz.admin.controller;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.admin.service.ImportService;
import top.zhaizz.common.constant.OperationLogConstants;
import top.zhaizz.common.log.OperationLog;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.common.result.Result;
import top.zhaizz.pojo.dto.imprt.ImportRunDTO;
import top.zhaizz.pojo.vo.imprt.ImportRecordVO;
import top.zhaizz.pojo.vo.imprt.ImportStatusVO;

/**
 * 番剧导入控制器
 */
@RestController
@RequestMapping("/api/admin/import")
@RequiredArgsConstructor
@Validated
public class ImportController {

    private final ImportService importService;

    /**
     * 运行番剧导入，供管理后台手动触发数据同步
     *
     * @param authorization 调用方 JWT（透传给 agent 做 ADMIN 校验）
     * @param request       导入参数（mode/key/since/workers，query 串绑定）
     */
    @OperationLog(action = OperationLogConstants.ACTION_IMPORT_RUN, module = OperationLogConstants.MODULE_IMPORT)
    @PostMapping("/run")
    public Result<Void> runImport(@RequestHeader(value = "Authorization", required = false) String authorization,
                                  @Valid ImportRunDTO request) {
        importService.runImport(authorization, request);
        return Result.success();
    }

    /**
     * 获取番剧导入状态，供管理后台导入进度轮询触发
     */
    @GetMapping("/status")
    public Result<ImportStatusVO> getImportStatus() {
        return Result.success(importService.getImportStatus());
    }

    /**
     * 分页查询导入记录，供管理后台导入历史表格展示全部记录
     */
    @GetMapping("/records")
    public Result<PageResult<ImportRecordVO>> getImportRecords(
            @RequestParam(defaultValue = "1") @Min(1) int page,
            @RequestParam(defaultValue = "10") @Min(1) @Max(1000) int size,
            @RequestParam(required = false) String status) {
        return Result.success(importService.getImportRecords(page, size, status));
    }
}
