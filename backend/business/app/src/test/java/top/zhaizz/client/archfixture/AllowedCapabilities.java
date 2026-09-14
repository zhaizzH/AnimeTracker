package top.zhaizz.client.archfixture;
import top.zhaizz.infrastructure.storage.ImageStorageGateway;
/** 用户模块通过公开技术接口访问基础设施的合法夹具。 */
public class AllowedCapabilities {
    /** 允许客户端使用的图片存储公开接口。 */
    ImageStorageGateway storage;
}
