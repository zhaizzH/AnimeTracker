package top.zhaizz.animetracker.subject.service;

import top.zhaizz.animetracker.subject.vo.ImportStatusVO;

public interface ImportService {

    /** 触发数据导入 */
    void runImport();

    /** 获取导入状态 */
    ImportStatusVO getImportStatus();
}
