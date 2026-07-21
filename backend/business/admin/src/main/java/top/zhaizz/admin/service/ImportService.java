package top.zhaizz.admin.service;

import top.zhaizz.pojo.vo.ImportStatusVO;

public interface ImportService {
    void runImport();
    ImportStatusVO getImportStatus();
}
