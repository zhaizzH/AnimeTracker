package top.zhaizz.app.architecture;

import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.core.importer.ImportOption;
import com.tngtech.archunit.lang.ArchRule;
import org.junit.jupiter.api.Test;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;

class ArchitectureBoundaryTest {

    @Test
    void lowerModulesDoNotDependOnApplicationCompositionRoot() {
        ArchRule rule = noClasses()
                .that().resideInAnyPackage(
                        "top.zhaizz.pojo..",
                        "top.zhaizz.common..",
                        "top.zhaizz.client..",
                        "top.zhaizz.admin..",
                        "top.zhaizz.agent..")
                .should().dependOnClassesThat().resideInAnyPackage("top.zhaizz.app..");

        rule.check(new ClassFileImporter()
                .withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS)
                .importPackages("top.zhaizz"));
    }
}
