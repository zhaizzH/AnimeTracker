package top.zhaizz.agent.gateway;

import top.zhaizz.pojo.dto.imprt.ImportRunDTO;

/** 触发 Python Agent 导入任务的外部端口 */
public interface ImportAgentGateway {
    /**
     * 触发一次导入任务
     *
     * @param authorization 当前请求的授权头，可为空或空字符串，此时不追加授权头
     * @param request 已由业务层校验的非空导入参数
     * @throws top.zhaizz.common.exception.BizException 上游 409 为 CONFLICT，其他 4xx 为 BAD_REQUEST；
     *         上游 5xx 或连接失败为 INTERNAL_ERROR，异常消息不透传上游响应正文
     */
    void runImport(String authorization, ImportRunDTO request);
}
