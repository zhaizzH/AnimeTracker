package top.zhaizz.app.config;

import org.apache.ibatis.type.TypeAliasRegistry;
import org.junit.jupiter.api.Test;

import top.zhaizz.pojo.entity.Character;

import static org.assertj.core.api.Assertions.assertThat;

class MyBatisEntityAliasTest {

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
