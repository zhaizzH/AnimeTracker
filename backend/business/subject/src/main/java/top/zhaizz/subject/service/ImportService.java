package top.zhaizz.subject.service;

import top.zhaizz.pojo.vo.ImportStatusVO;

/**
 * 数据导入服务接口
 */
public interface ImportService {

    /** 触发数据导入 */
    void runImport();

    /** 获取导入状态 */
    ImportStatusVO getImportStatus();
}
