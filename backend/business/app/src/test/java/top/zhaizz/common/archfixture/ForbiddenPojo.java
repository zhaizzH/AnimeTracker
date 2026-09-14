package top.zhaizz.common.archfixture;
import top.zhaizz.pojo.entity.User;
/** 故意引入 pojo 的 common 夹具，用于验证基础模块无项目依赖。 */
public class ForbiddenPojo {
    /** common 不能持有的业务实体类型。 */
    User user;
}
