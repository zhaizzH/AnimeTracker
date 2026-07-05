package top.zhaizz.animetracker.subject.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import top.zhaizz.animetracker.common.ApiResponse;
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
    public ApiResponse<Void> runImport() {  // TODO 待接入python功能
        importService.runImport();
        return ApiResponse.success();
    }

    /**
     * 获取番剧导入状态
     */
    @GetMapping("/status")
    public ApiResponse<ImportStatusVO> getImportStatus() {
        return ApiResponse.success(importService.getImportStatus());
    }
}
