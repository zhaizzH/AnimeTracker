package top.zhaizz.admin.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.admin.service.ImportService;
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

    // TODO 待接入python功能
    /**
     * 运行番剧导入
     */
    @PostMapping("/run")
    public Result<Void> runImport() {
        importService.runImport();
        return Result.success();
    }

    // TODO 待接入python功能
    /**
     * 获取番剧导入状态
     */
    @GetMapping("/status")
    public Result<ImportStatusVO> getImportStatus() {
        return Result.success(importService.getImportStatus());
    }
}
