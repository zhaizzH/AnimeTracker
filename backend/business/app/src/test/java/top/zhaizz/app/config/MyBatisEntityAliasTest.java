package top.zhaizz.app.config;

import org.apache.ibatis.type.TypeAliasRegistry;
import org.junit.jupiter.api.Test;

import top.zhaizz.pojo.entity.Character;

import static org.assertj.core.api.Assertions.assertThat;

/** MyBatis 实体别名冲突回归测试 */
class MyBatisEntityAliasTest {

    /** 验证业务 Character 别名不会覆盖 Java 内置别名 */
    @Test
    void scansBangumiCharacterWithoutCollidingWithJavaLangCharacter() {
        TypeAliasRegistry registry = new TypeAliasRegistry();

        // This is the same registration path MyBatis uses for each scanned entity.
        // Registering the class without the explicit alias would collide with the
        // built-in java.lang.Character alias.
        registry.registerAlias(Character.class);

        assertThat(registry.resolveAlias("BangumiCharacter")).isSameAs(Character.class);
        assertThat(registry.resolveAlias("Character")).isSameAs(java.lang.Character.class);
    }
}
