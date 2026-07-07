package top.zhaizz.animetracker.subject.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.animetracker.common.result.Result;
import top.zhaizz.animetracker.subject.service.ImportService;
import top.zhaizz.animetracker.common.vo.ImportStatusVO;

/**
 * 番剧导入控制器
 */
@RestController
@RequestMapping("/api/admin/import")
@RequiredArgsConstructor
public class ImportController {

    private final ImportService importService;

    /**
     * 运行番剧导入
     */
    @PostMapping("/run")
    public Result<Void> runImport() {  // TODO 待接入python功能
        importService.runImport();
        return Result.success();
    }

    /**
     * 获取番剧导入状态
     */
    @GetMapping("/status")
    public Result<ImportStatusVO> getImportStatus() {
        return Result.success(importService.getImportStatus());
    }
}
