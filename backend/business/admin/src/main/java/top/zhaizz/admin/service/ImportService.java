package top.zhaizz.admin.service;

import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.dto.imprt.ImportRunDTO;
import top.zhaizz.pojo.vo.imprt.ImportRecordVO;
import top.zhaizz.pojo.vo.imprt.ImportStatusVO;

/**
 * 番剧导入服务接口
 */
public interface ImportService {

    /**
     * 触发番剧导入（转发至 Python Agent 导入端点）
     *
     * @param authorization 调用方 JWT（透传给 agent 做 ADMIN 校验）
     * @param request       导入参数（mode/key/since/workers）
     */
    void runImport(String authorization, ImportRunDTO request);

    /**
     * 获取导入状态（直接查库，不经过 Python agent）
     */
    ImportStatusVO getImportStatus();

    /**
     * 分页查询导入记录（直接查库，不经过 Python agent）
     *
     * @param page   页码（从 1 开始）
     * @param size   每页条数
     * @param status 可选状态过滤：RUNNING / COMPLETED / FAILED，为空表示全部
     */
    PageResult<ImportRecordVO> getImportRecords(int page, int size, String status);
}
