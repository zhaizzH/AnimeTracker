package top.zhaizz.admin.service;

import top.zhaizz.pojo.vo.ImportStatusVO;

/**
 * 番剧导入服务接口
 */
public interface ImportService {
    /**
     * 触发番剧导入
     */
    void runImport();
    /**
     * 获取导入状态
     */
    ImportStatusVO getImportStatus();
}
