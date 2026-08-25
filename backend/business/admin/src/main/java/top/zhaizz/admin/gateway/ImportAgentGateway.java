package top.zhaizz.admin.gateway;

import top.zhaizz.pojo.dto.imprt.ImportRunDTO;

/** 触发 Python Agent 导入任务的外部端口。 */
public interface ImportAgentGateway {
    void runImport(String authorization, ImportRunDTO request);
}
