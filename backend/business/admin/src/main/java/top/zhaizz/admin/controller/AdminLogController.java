package top.zhaizz.admin.controller;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.RequiredArgsConstructor;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import top.zhaizz.admin.service.AdminLogService;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.common.result.Result;
import top.zhaizz.pojo.vo.OperationLogVO;

import java.time.LocalDate;

/**
 * 日志查询控制器
 */
@RestController
@RequestMapping("/api/admin/logs")
@RequiredArgsConstructor
@Validated
public class AdminLogController {

    private final AdminLogService adminLogService;

    /**
     * 分页查询操作/登录日志
     */
    @GetMapping
    public Result<PageResult<OperationLogVO>> listLogs(
            @RequestParam(required = false) String action,
            @RequestParam(required = false) String module,
            @RequestParam(required = false) String username,
            @RequestParam(required = false) Long userId,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate start,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate end,
            @RequestParam(defaultValue = "1") @Min(1) int page,
            @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size) {
        return Result.success(adminLogService.listLogs(action, module, username, userId, start, end, page, size));
    }
}
