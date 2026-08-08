package top.zhaizz.admin.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.admin.service.ImportService;
import top.zhaizz.common.log.OperationLog;
import top.zhaizz.common.result.Result;
import top.zhaizz.pojo.vo.ImportStatusVO;

/**
 * 番剧导入控制器
 */
@RestController
@RequestMapping("/api/admin/import")
@RequiredArgsConstructor
public class ImportController {

    private final ImportService importService;

    /**
     * 运行番剧导入，供管理后台手动触发数据同步
     *
     * @param mode    导入模式：full / season / recent / since
     * @param key     季度标识（season 模式必填），如 "2026-summer"
     * @param since   起始日期（since 模式必填），如 "2026-01-01"
     * @param workers 并发线程数，为空使用 Python 侧默认值
     */
    @OperationLog(action = "IMPORT_RUN", module = "IMPORT")
    @PostMapping("/run")
    public Result<Void> runImport(@RequestHeader(value = "Authorization", required = false) String auth,
                                  @RequestParam String mode,
                                  @RequestParam(required = false) String key,
                                  @RequestParam(required = false) String since,
                                  @RequestParam(required = false) Integer workers) {
        importService.runImport(auth, mode, key, since, workers);
        return Result.success();
    }

    /**
     * 获取番剧导入状态，供管理后台导入进度轮询触发
     */
    @GetMapping("/status")
    public Result<ImportStatusVO> getImportStatus() {
        return Result.success(importService.getImportStatus());
    }
}
