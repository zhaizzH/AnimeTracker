package top.zhaizz.admin.service;

import top.zhaizz.common.result.PageResult;
import top.zhaizz.pojo.dto.imprt.ImportRecordQueryDTO;
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
     * @throws top.zhaizz.common.exception.BizException 模式无效或缺少模式必需参数时为 BAD_REQUEST；运行中冲突为 CONFLICT，上游连接或服务器失败为 INTERNAL_ERROR
     */
    void runImport(String authorization, ImportRunDTO request);

    /**
     * 获取导入状态（直接查库，不经过 Python agent）
     * @return 导入计数与最近 10 条记录；无完成记录时最近完成时间为空
     */
    ImportStatusVO getImportStatus();

    /**
     * 分页查询导入记录（直接查库，不经过 Python agent）
     *
     * @param request 分页与状态过滤参数
     * @return 按启动时间降序排列的导入记录分页
     */
    PageResult<ImportRecordVO> getImportRecords(ImportRecordQueryDTO request);
}
