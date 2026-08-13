package top.zhaizz.admin.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import top.zhaizz.admin.service.AdminLogService;
import top.zhaizz.common.result.PageResult;
import top.zhaizz.common.result.Result;
import top.zhaizz.pojo.dto.log.LogQueryDTO;
import top.zhaizz.pojo.vo.LogVO;

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
     * 分页查询操作/登录日志并返回当前筛选条件的全量聚合统计，管理后台日志页筛选查询时触发
     */
    @GetMapping
    public Result<PageResult<LogVO>> listLogs(@Valid LogQueryDTO request) {
        return Result.success(adminLogService.listLogs(request));
    }
}
