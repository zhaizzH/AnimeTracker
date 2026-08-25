package top.zhaizz.app.architecture;

import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.core.importer.ImportOption;
import org.junit.jupiter.api.Test;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;

class ArchitectureBoundaryTest {

    private static final JavaClasses CLASSES = new ClassFileImporter()
            .withImportOption(new ImportOption.DoNotIncludeTests())
            .importPackages("top.zhaizz");

    @Test
    void controllersDoNotReachPersistenceImplementationsOrRuntimeAdapters() {
        noClasses().that().resideInAPackage("..controller..")
                .should().dependOnClassesThat().resideInAnyPackage(
                        "..mapper..",
                        "..service.impl..",
                        "top.zhaizz.app.infrastructure..")
                .check(CLASSES);
    }

    @Test
    void servicesDoNotDependOnControllersOrRuntimeAdapters() {
        noClasses().that().resideInAPackage("..service..")
                .should().dependOnClassesThat().resideInAnyPackage(
                        "..controller..",
                        "top.zhaizz.app.infrastructure..")
                .check(CLASSES);
    }

    @Test
    void businessModulesDoNotDependOnEachOther() {
        noClasses().that().resideInAPackage("top.zhaizz.admin..")
                .should().dependOnClassesThat().resideInAnyPackage(
                        "top.zhaizz.client..", "top.zhaizz.agent..")
                .check(CLASSES);
        noClasses().that().resideInAPackage("top.zhaizz.client..")
                .should().dependOnClassesThat().resideInAnyPackage(
                        "top.zhaizz.admin..", "top.zhaizz.agent..")
                .check(CLASSES);
        noClasses().that().resideInAPackage("top.zhaizz.agent..")
                .should().dependOnClassesThat().resideInAnyPackage(
                        "top.zhaizz.admin..", "top.zhaizz.client..")
                .check(CLASSES);
    }

    @Test
    void commonDoesNotDependOnApplicationOrBusinessModules() {
        noClasses().that().resideInAPackage("top.zhaizz.common..")
                .should().dependOnClassesThat().resideInAnyPackage(
                        "top.zhaizz.app..",
                        "top.zhaizz.admin..",
                        "top.zhaizz.client..",
                        "top.zhaizz.agent..")
                .check(CLASSES);
    }
}
