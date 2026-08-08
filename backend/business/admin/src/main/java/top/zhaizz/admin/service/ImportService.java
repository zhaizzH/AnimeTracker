package top.zhaizz.admin.service;

import top.zhaizz.pojo.vo.ImportStatusVO;

/**
 * 番剧导入服务接口
 */
public interface ImportService {

    /**
     * 触发番剧导入（转发至 Python Agent 导入端点）
     *
     * @param authorization 调用方 JWT（透传给 agent 做 ADMIN 校验）
     * @param mode          导入模式：full / season / recent / since
     * @param key           季度标识（season 模式必填），如 "2026-summer"
     * @param since         起始日期（since 模式必填），如 "2026-01-01"
     * @param workers       并发线程数，为空使用 Python 侧默认值
     */
    void runImport(String authorization, String mode, String key, String since, Integer workers);

    /**
     * 获取导入状态
     */
    ImportStatusVO getImportStatus();
}
