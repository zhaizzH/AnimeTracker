package top.zhaizz.client.archfixture;
import top.zhaizz.agent.service.AgentService;
import top.zhaizz.log.mapper.OperationLogMapper;
import top.zhaizz.infrastructure.storage.minio.MinioImageStorageGateway;
/** 故意违规的客户端依赖，用于证明架构门禁能发现非法引用 */
public class ForbiddenCapabilities {
    /** 用户模块不允许直接访问的 Agent 服务 */
    AgentService agent;
    /** 只能由日志模块访问的内部 Mapper */
    OperationLogMapper mapper;
    /** 业务方应通过公开接口使用的供应商实现 */
    MinioImageStorageGateway vendor;
}
