package top.zhaizz.app.architecture;

import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.core.importer.ImportOption;
import com.tngtech.archunit.lang.ArchRule;
import org.junit.jupiter.api.Test;
import top.zhaizz.client.archfixture.AllowedCapabilities;
import top.zhaizz.client.archfixture.ForbiddenCapabilities;
import top.zhaizz.common.archfixture.ForbiddenPojo;
import java.util.Map;
import java.util.Set;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;
import static org.assertj.core.api.Assertions.assertThat;

/** 对生产字节码执行完整模块依赖上限及内部实现访问约束。 */
class ArchitectureBoundaryTest {
    /** 规范允许的跨模块直接依赖；模块内部依赖始终允许。 */
    private static final Map<String, Set<String>> ALLOWED = Map.of(
            "common", Set.of(),
            "pojo", Set.of("common"),
            "infrastructure", Set.of("common", "pojo"),
            "auth", Set.of("infrastructure", "common", "pojo"),
            "log", Set.of("auth", "infrastructure", "common", "pojo"),
            "agent", Set.of("log", "auth", "infrastructure", "common", "pojo"),
            "client", Set.of("auth", "log", "infrastructure", "common", "pojo"),
            "admin", Set.of("agent", "auth", "log", "infrastructure", "common", "pojo"),
            "app", Set.of("admin", "client", "agent", "log", "auth", "infrastructure", "common", "pojo"));
    /** 排除测试夹具，避免把故意违规的测试类当作生产依赖。 */
    private static final JavaClasses PRODUCTION = new ClassFileImporter()
            .withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS).importPackages("top.zhaizz");

    /** 验证 common 仅承载已批准的结果、分页与错误定义，禁止悄然恢复技术实现。 */
    @Test
    void commonContainsOnlyFoundationDefinitions() {
        assertThat(PRODUCTION.stream().filter(c -> c.getPackageName().startsWith("top.zhaizz.common."))
                .map(c -> c.getName()).toList()).containsExactlyInAnyOrder(
                        "top.zhaizz.common.result.Result", "top.zhaizz.common.result.PageResult",
                        "top.zhaizz.common.exception.BizException", "top.zhaizz.common.constant.ErrorType");
    }
    /** 验证全部九模块遵守允许依赖矩阵，包括 common 不依赖 pojo、client 不依赖 agent。 */
    @Test
    void allModulesRespectDependencyMatrix() {
        ALLOWED.keySet().stream().filter(m -> !m.equals("app"))
                .forEach(m -> dependencyRule(m).check(PRODUCTION));
    }

    /** 验证跨模块不能直接访问 Mapper、服务实现或供应商适配器，app 装配除外。 */
    @Test
    void internalImplementationsStayInsideTheirModule() {
        ALLOWED.keySet().stream().filter(m -> !m.equals("app"))
                .forEach(m -> internalRule(m).check(PRODUCTION));
    }

    /** 验证故意加入的 client 到 agent、common 到 pojo 引用会被门禁拒绝。 */
    @Test
    void matrixRejectsPreviouslyUncoveredEdges() {
        JavaClasses illegal = new ClassFileImporter().importClasses(ForbiddenCapabilities.class, ForbiddenPojo.class);
        assertThat(dependencyRule("client").evaluate(illegal).hasViolation()).isTrue();
        assertThat(dependencyRule("common").evaluate(illegal).hasViolation()).isTrue();
    }

    /** 验证内部日志 Mapper 和 MinIO 实现访问被拒绝，公开能力调用被允许。 */
    @Test
    void internalRulesRejectAdaptersButAcceptPublicCapabilities() {
        JavaClasses illegal = new ClassFileImporter().importClasses(ForbiddenCapabilities.class);
        assertThat(internalRule("log").evaluate(illegal).hasViolation()).isTrue();
        assertThat(internalRule("infrastructure").evaluate(illegal).hasViolation()).isTrue();
        JavaClasses legal = new ClassFileImporter().importClasses(AllowedCapabilities.class);
        assertThat(dependencyRule("client").evaluate(legal).hasViolation()).isFalse();
        assertThat(internalRule("infrastructure").evaluate(legal).hasViolation()).isFalse();
    }

    /**
     * 为模块生成跨模块禁止依赖规则。
     * @param module 允许矩阵中的模块名
     * @return 禁止访问矩阵以外项目模块的规则
     */
    private static ArchRule dependencyRule(String module) {
        String[] forbidden = ALLOWED.keySet().stream()
                .filter(target -> !target.equals(module) && !ALLOWED.get(module).contains(target))
                .map(target -> "top.zhaizz." + target + "..").toArray(String[]::new);
        return noClasses().that().resideInAPackage("top.zhaizz." + module + "..")
                .should().dependOnClassesThat().resideInAnyPackage(forbidden).allowEmptyShould(true);
    }

    /**
     * 保护模块的持久化和供应商实现，允许 app 显式装配。
     * @param module 被保护模块
     * @return 拒绝其他模块越过公开入口的规则
     */
    private static ArchRule internalRule(String module) {
        String prefix = "top.zhaizz." + module;
        return noClasses().that().resideOutsideOfPackages(prefix + "..", "top.zhaizz.app..")
                .should().dependOnClassesThat().resideInAnyPackage(
                        prefix + ".mapper..", prefix + ".service.impl..",
                        prefix + ".storage.minio..", prefix + ".email.resend..").allowEmptyShould(true);
    }
}
